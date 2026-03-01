"""
META FIT - Virtual Try-On Test with Nano Banana Pro (Gemini 3 Pro Image)

Usage:
    # Mode 1: clothing item image + person = try-on
    python try_on_test.py --person <person> --clothing <clothing>

    # Mode 2: model wearing clothes + target person = target wearing those clothes
    python try_on_test.py --mode transfer --source <dressed_model> --person <target_person>

    # With preprocessing (MediaPipe face mask + pose detection)
    python try_on_test.py --mode transfer --source <model> --person <target> --preprocess
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# Output directory for results
OUTPUT_DIR = Path("test_results/nano_banana")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Model configuration
MODEL_ID = "gemini-3-pro-image-preview"

# Prompt: clothing item + person
PROMPT_CLOTHING = """You are a virtual try-on system.
Image 1: A target person photo.
Image 2: A clothing product image (flat lay or on hanger).

Generate a photo-realistic image of the target person wearing this clothing item.

CRITICAL RULES:
- The person's face MUST remain EXACTLY identical - same facial features, expression, age, skin texture
- Do NOT regenerate or modify the face in any way
- Preserve the exact same body shape, proportions, and pose
- Preserve the same background
- Fit the clothing naturally with realistic draping and shadows
- Keep hair, accessories, and all non-clothing elements unchanged
- Output the FULL BODY image at the same framing as the input
"""

# Prompt: transfer clothes from one model to another
PROMPT_TRANSFER = """You are a virtual try-on system.
Image 1: A target person (the person who should wear the clothes).
Image 2: A source model wearing specific clothing.

Your task: Generate an image of the TARGET PERSON (Image 1) wearing the EXACT SAME CLOTHING from the source model (Image 2).

CRITICAL RULES:
- The target person's face MUST remain EXACTLY identical - same facial features, expression, age, skin texture
- Do NOT regenerate or modify the face in any way
- Use the target person's body shape and pose
- Extract only the clothing design, color, pattern, and style from Image 2
- Fit that clothing naturally onto the target person's body
- Keep the target person's background
- Output the FULL BODY image at the same framing as Image 1
"""


def preprocess_images(
    person_path: str, clothing_path: str, mode: str,
) -> tuple[str, str, str, str | None]:
    """Apply MediaPipe preprocessing: face detection + pose landmarks.

    Returns (person_path, clothing_path, extra_prompt, face_crop_path).
    face_crop_path is a cropped face image to send as additional reference.

    Requires: pip install mediapipe opencv-contrib-python
    """
    try:
        import mediapipe as mp
        from mediapipe.tasks.python import BaseOptions
        from mediapipe.tasks.python.vision import (
            FaceLandmarker,
            FaceLandmarkerOptions,
            PoseLandmarker,
            PoseLandmarkerOptions,
            PoseLandmark,
        )
    except ImportError:
        print("Error: mediapipe is required for --preprocess")
        print("Install with: pip install mediapipe")
        sys.exit(1)

    import cv2

    img = cv2.imread(person_path)
    if img is None:
        print(f"[preprocess] Warning: Could not read {person_path}")
        return person_path, clothing_path, "", None
    h, w = img.shape[:2]

    # MediaPipe tasks API requires mediapipe.Image
    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=cv2.cvtColor(img, cv2.COLOR_BGR2RGB),
    )

    model_dir = Path("models")
    face_info = ""
    face_crop_path = None

    # --- FaceLandmarker: detect face region ---
    face_model = model_dir / "face_landmarker.task"
    if face_model.exists():
        print("[preprocess] Running FaceLandmarker...")
        face_options = FaceLandmarkerOptions(
            base_options=BaseOptions(
                model_asset_path=str(face_model),
            ),
            num_faces=1,
        )
        with FaceLandmarker.create_from_options(face_options) as landmarker:
            result = landmarker.detect(mp_image)

        if result.face_landmarks:
            landmarks = result.face_landmarks[0]
            xs = [lm.x for lm in landmarks]
            ys = [lm.y for lm in landmarks]
            face_x1, face_x2 = min(xs), max(xs)
            face_y1, face_y2 = min(ys), max(ys)
            face_w = face_x2 - face_x1
            face_h = face_y2 - face_y1
            face_cx = (face_x1 + face_x2) / 2
            face_cy = (face_y1 + face_y2) / 2

            face_info = (
                f"Face region (normalized 0-1): "
                f"center=({face_cx:.3f},{face_cy:.3f}), "
                f"bbox=({face_x1:.3f},{face_y1:.3f})"
                f"-({face_x2:.3f},{face_y2:.3f}), "
                f"size={face_w:.3f}x{face_h:.3f}"
            )
            print(f"[preprocess] {face_info}")

            # Crop face with margin for reference image
            margin = 0.4
            cx1 = max(0, int((face_x1 - face_w * margin) * w))
            cx2 = min(w, int((face_x2 + face_w * margin) * w))
            cy1 = max(0, int((face_y1 - face_h * margin) * h))
            cy2 = min(h, int((face_y2 + face_h * margin) * h))
            face_crop = img[cy1:cy2, cx1:cx2]

            face_crop_path = str(
                OUTPUT_DIR / f"_face_crop_{Path(person_path).stem}.png"
            )
            cv2.imwrite(face_crop_path, face_crop)
            print(f"[preprocess] Face crop saved: {face_crop_path}")
        else:
            print("[preprocess] Warning: No face detected")
    else:
        print(f"[preprocess] Warning: {face_model} not found, skipping face")

    # --- PoseLandmarker: extract landmarks ---
    pose_model = model_dir / "pose_landmarker_heavy.task"
    pose_info = ""
    if pose_model.exists():
        print("[preprocess] Running PoseLandmarker...")
        pose_options = PoseLandmarkerOptions(
            base_options=BaseOptions(
                model_asset_path=str(pose_model),
            ),
            num_poses=1,
        )
        with PoseLandmarker.create_from_options(pose_options) as landmarker:
            result = landmarker.detect(mp_image)

        if result.pose_landmarks:
            lm = result.pose_landmarks[0]
            PL = PoseLandmark

            nose = lm[PL.NOSE]
            l_sh = lm[PL.LEFT_SHOULDER]
            r_sh = lm[PL.RIGHT_SHOULDER]
            l_el = lm[PL.LEFT_ELBOW]
            r_el = lm[PL.RIGHT_ELBOW]
            l_wr = lm[PL.LEFT_WRIST]
            r_wr = lm[PL.RIGHT_WRIST]
            l_hp = lm[PL.LEFT_HIP]
            r_hp = lm[PL.RIGHT_HIP]
            l_kn = lm[PL.LEFT_KNEE]
            r_kn = lm[PL.RIGHT_KNEE]
            l_an = lm[PL.LEFT_ANKLE]
            r_an = lm[PL.RIGHT_ANKLE]

            shoulder_w = abs(l_sh.x - r_sh.x)
            hip_w = abs(l_hp.x - r_hp.x)
            torso_h = abs(
                (l_sh.y + r_sh.y) / 2 - (l_hp.y + r_hp.y) / 2
            )

            pose_info = (
                f"Pose landmarks (normalized 0-1): "
                f"nose=({nose.x:.3f},{nose.y:.3f}), "
                f"L_shoulder=({l_sh.x:.3f},{l_sh.y:.3f}), "
                f"R_shoulder=({r_sh.x:.3f},{r_sh.y:.3f}), "
                f"L_elbow=({l_el.x:.3f},{l_el.y:.3f}), "
                f"R_elbow=({r_el.x:.3f},{r_el.y:.3f}), "
                f"L_wrist=({l_wr.x:.3f},{l_wr.y:.3f}), "
                f"R_wrist=({r_wr.x:.3f},{r_wr.y:.3f}), "
                f"L_hip=({l_hp.x:.3f},{l_hp.y:.3f}), "
                f"R_hip=({r_hp.x:.3f},{r_hp.y:.3f}), "
                f"L_knee=({l_kn.x:.3f},{l_kn.y:.3f}), "
                f"R_knee=({r_kn.x:.3f},{r_kn.y:.3f}), "
                f"L_ankle=({l_an.x:.3f},{l_an.y:.3f}), "
                f"R_ankle=({r_an.x:.3f},{r_an.y:.3f}). "
                f"Proportions: shoulder_width={shoulder_w:.3f}, "
                f"hip_width={hip_w:.3f}, torso_height={torso_h:.3f}, "
                f"shoulder/hip_ratio={shoulder_w / hip_w:.2f}"
            )
            print(f"[preprocess] Pose: shoulder_w={shoulder_w:.3f}, "
                  f"hip_w={hip_w:.3f}, torso_h={torso_h:.3f}")
        else:
            print("[preprocess] Warning: No pose detected")
    else:
        print(f"[preprocess] Warning: {pose_model} not found, skipping pose")

    # Build extra prompt with preprocessing data
    extra_prompt = ""
    if face_info or pose_info:
        extra_prompt = (
            "\n\nPREPROCESSING DATA (MediaPipe analysis of target person):\n"
        )
        if face_info:
            extra_prompt += f"{face_info}\n"
        if pose_info:
            extra_prompt += f"{pose_info}\n"
        if face_crop_path:
            extra_prompt += (
                "\nImage 3 is a close-up crop of the target person's face. "
                "You MUST reproduce this face EXACTLY - every facial feature, "
                "skin texture, facial hair, and expression must be "
                "pixel-perfect identical.\n"
            )
        extra_prompt += (
            "Use the pose landmarks to maintain the exact body position.\n"
        )

    return person_path, clothing_path, extra_prompt, face_crop_path


def postprocess_face_restore(
    original_path: str, generated_path: str,
) -> str | None:
    """Restore the original face onto the generated try-on image.

    Uses MediaPipe FaceLandmarker to detect face regions in both images,
    then composites the original face onto the generated image with
    feathered blending for natural edges.

    Returns the path to the face-restored image, or None on failure.
    """
    try:
        import mediapipe as mp
        from mediapipe.tasks.python import BaseOptions
        from mediapipe.tasks.python.vision import (
            FaceLandmarker,
            FaceLandmarkerOptions,
        )
    except ImportError:
        print("[postprocess] mediapipe not available, skipping face restore")
        return None

    import cv2
    import numpy as np

    face_model = Path("models/face_landmarker.task")
    if not face_model.exists():
        print("[postprocess] face_landmarker.task not found, skipping")
        return None

    orig_img = cv2.imread(original_path)
    gen_img = cv2.imread(generated_path)
    if orig_img is None or gen_img is None:
        print("[postprocess] Could not read images, skipping")
        return None

    orig_h, orig_w = orig_img.shape[:2]
    gen_h, gen_w = gen_img.shape[:2]

    # Resize generated image to match original dimensions to avoid
    # upscaling the small original face into a large generated image.
    if (gen_w, gen_h) != (orig_w, orig_h):
        print(f"[postprocess] Resizing generated {gen_w}x{gen_h} "
              f"-> {orig_w}x{orig_h}")
        gen_img = cv2.resize(
            gen_img, (orig_w, orig_h), interpolation=cv2.INTER_LANCZOS4,
        )

    # Detect face in both images
    face_options = FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(face_model)),
        num_faces=1,
    )

    def detect_face_bbox(img):
        """Detect face and return (x1, y1, x2, y2) in pixel coordinates."""
        h, w = img.shape[:2]
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=cv2.cvtColor(img, cv2.COLOR_BGR2RGB),
        )
        with FaceLandmarker.create_from_options(face_options) as landmarker:
            result = landmarker.detect(mp_image)
        if not result.face_landmarks:
            return None
        landmarks = result.face_landmarks[0]
        xs = [lm.x for lm in landmarks]
        ys = [lm.y for lm in landmarks]
        # Add margin around face landmarks
        face_w = max(xs) - min(xs)
        face_h = max(ys) - min(ys)
        margin_x = face_w * 0.15
        margin_y = face_h * 0.15
        x1 = max(0, int((min(xs) - margin_x) * w))
        x2 = min(w, int((max(xs) + margin_x) * w))
        y1 = max(0, int((min(ys) - margin_y) * h))
        y2 = min(h, int((max(ys) + margin_y) * h))
        return x1, y1, x2, y2

    print("[postprocess] Detecting face in original image...")
    orig_bbox = detect_face_bbox(orig_img)
    if orig_bbox is None:
        print("[postprocess] No face found in original, skipping")
        return None

    print("[postprocess] Detecting face in generated image...")
    gen_bbox = detect_face_bbox(gen_img)
    if gen_bbox is None:
        print("[postprocess] No face found in generated, skipping")
        return None

    ox1, oy1, ox2, oy2 = orig_bbox
    gx1, gy1, gx2, gy2 = gen_bbox

    print(f"[postprocess] Original face: ({ox1},{oy1})-({ox2},{oy2})")
    print(f"[postprocess] Generated face: ({gx1},{gy1})-({gx2},{gy2})")

    # Crop original face and resize to match generated face region
    orig_face = orig_img[oy1:oy2, ox1:ox2]
    gen_face_w = gx2 - gx1
    gen_face_h = gy2 - gy1
    orig_face_resized = cv2.resize(
        orig_face, (gen_face_w, gen_face_h), interpolation=cv2.INTER_LANCZOS4,
    )

    # Color correction: match original face color to generated image skin tone.
    # Convert to LAB, match mean/std of L/A/B channels in the face region.
    gen_face_crop = gen_img[gy1:gy2, gx1:gx2]
    orig_lab = cv2.cvtColor(orig_face_resized, cv2.COLOR_BGR2LAB).astype(
        np.float32,
    )
    gen_lab = cv2.cvtColor(gen_face_crop, cv2.COLOR_BGR2LAB).astype(
        np.float32,
    )
    for ch in range(3):
        o_mean, o_std = orig_lab[:, :, ch].mean(), orig_lab[:, :, ch].std()
        g_mean, g_std = gen_lab[:, :, ch].mean(), gen_lab[:, :, ch].std()
        if o_std > 0:
            orig_lab[:, :, ch] = (
                (orig_lab[:, :, ch] - o_mean) * (g_std / o_std) + g_mean
            )
    orig_lab = np.clip(orig_lab, 0, 255)
    orig_face_corrected = cv2.cvtColor(
        orig_lab.astype(np.uint8), cv2.COLOR_LAB2BGR,
    )
    print("[postprocess] Color correction applied (LAB channel matching)")

    # Create elliptical feather mask for smooth blending
    mask = np.zeros((gen_face_h, gen_face_w), dtype=np.float32)
    center = (gen_face_w // 2, gen_face_h // 2)
    axes = (int(gen_face_w * 0.45), int(gen_face_h * 0.45))
    cv2.ellipse(mask, center, axes, 0, 0, 360, 1.0, -1)

    # Gaussian blur for feathering
    feather_size = max(gen_face_w, gen_face_h) // 3
    feather_size = feather_size + 1 if feather_size % 2 == 0 else feather_size
    feather_size = max(feather_size, 3)
    mask = cv2.GaussianBlur(mask, (feather_size, feather_size), 0)

    # Expand mask to 3 channels
    mask_3ch = np.stack([mask] * 3, axis=-1)

    # Blend: result = corrected_face * mask + gen_face * (1 - mask)
    result = gen_img.copy()
    gen_region = result[gy1:gy2, gx1:gx2].astype(np.float32)
    orig_region = orig_face_corrected.astype(np.float32)
    blended = orig_region * mask_3ch + gen_region * (1.0 - mask_3ch)
    result[gy1:gy2, gx1:gx2] = blended.astype(np.uint8)

    # Save result
    gen_path = Path(generated_path)
    restored_path = str(
        gen_path.parent / f"{gen_path.stem}_face_restored{gen_path.suffix}"
    )
    cv2.imwrite(restored_path, result)
    print(f"[postprocess] Face restored: {restored_path}")
    return restored_path


def load_image_as_part(image_path: str) -> types.Part:
    """Load an image file and return as a Gemini API Part."""
    path = Path(image_path)
    if not path.exists():
        print(f"Error: Image not found: {image_path}")
        sys.exit(1)

    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    mime_type = mime_map.get(path.suffix.lower(), "image/png")

    with open(path, "rb") as f:
        image_bytes = f.read()

    return types.Part.from_bytes(data=image_bytes, mime_type=mime_type)


def save_result(
    response, person_path: str, clothing_path: str, mode: str,
) -> str | None:
    """Extract and save the generated image from the response."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    person_name = Path(person_path).stem
    clothing_name = Path(clothing_path).stem

    for i, part in enumerate(response.candidates[0].content.parts):
        if part.inline_data is not None:
            ext = "png" if "png" in part.inline_data.mime_type else "jpg"
            filename = f"{timestamp}_{mode}_{person_name}_{clothing_name}_{i}.{ext}"
            output_path = OUTPUT_DIR / filename

            with open(output_path, "wb") as f:
                f.write(part.inline_data.data)

            print(f"Saved: {output_path}")
            return str(output_path)
        elif part.text:
            print(f"Model response text: {part.text}")

    return None


def run_tryon(
    person_path: str,
    clothing_path: str,
    prompt: str,
    mode: str,
    use_preprocess: bool = False,
) -> None:
    """Run virtual try-on with Nano Banana Pro."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not set in .env")
        sys.exit(1)

    extra_prompt = ""
    face_crop_path = None
    if use_preprocess:
        print("--- Preprocessing with MediaPipe ---")
        person_path, clothing_path, extra_prompt, face_crop_path = (
            preprocess_images(person_path, clothing_path, mode)
        )
        print("--- Preprocessing complete ---")

    client = genai.Client(api_key=api_key)

    print(f"Model: {MODEL_ID}")
    print(f"Mode: {mode}")
    print(f"Preprocess: {use_preprocess}")
    print(f"Person: {person_path}")
    print(f"Clothing/Source: {clothing_path}")
    print("Generating try-on image...")

    full_prompt = prompt + extra_prompt

    person_part = load_image_as_part(person_path)
    clothing_part = load_image_as_part(clothing_path)

    # Build contents: prompt + person + clothing [+ face crop if preprocessed]
    contents = [full_prompt, person_part, clothing_part]
    if face_crop_path:
        contents.append(load_image_as_part(face_crop_path))

    response = client.models.generate_content(
        model=MODEL_ID,
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )

    result_path = save_result(response, person_path, clothing_path, mode)

    if result_path:
        print(f"\nTry-on complete! Result: {result_path}")
        # Post-process: restore original face onto generated image
        if use_preprocess:
            print("\n--- Post-processing: Face Restore ---")
            restored = postprocess_face_restore(person_path, result_path)
            if restored:
                print(f"Face-restored result: {restored}")
    else:
        print("\nNo image generated. Check the model response above.")


def main() -> None:
    parser = argparse.ArgumentParser(description="META FIT Virtual Try-On Test")
    parser.add_argument(
        "--mode", default="clothing", choices=["clothing", "transfer"],
        help="clothing: item image + person, transfer: dressed model + target person",
    )
    parser.add_argument("--person", required=True, help="Path to target person image")
    parser.add_argument("--clothing", help="Path to clothing item image (mode=clothing)")
    parser.add_argument("--source", help="Path to source model wearing clothes (mode=transfer)")
    parser.add_argument(
        "--preprocess", action="store_true",
        help="Enable MediaPipe preprocessing (face mask + pose detection)",
    )
    args = parser.parse_args()

    if args.mode == "clothing":
        clothing = args.clothing or "test_data/clothing/tshirt_black.png"
        run_tryon(args.person, clothing, PROMPT_CLOTHING, "clothing", args.preprocess)
    elif args.mode == "transfer":
        if not args.source:
            print("Error: --source is required for transfer mode")
            sys.exit(1)
        run_tryon(args.person, args.source, PROMPT_TRANSFER, "transfer", args.preprocess)


if __name__ == "__main__":
    main()
