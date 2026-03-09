"""Compare Nano Banana vs Vertex AI Virtual Try-On side by side.

Usage:
    # Run comparison on a single pair
    python compare_vto.py --person test_data/person/woman1.jpg --clothing test_data/clothing/tshirt_black.png

    # Run comparison on all predefined test cases
    python compare_vto.py --all

    # Transfer mode: person-to-person (source's clothes -> target person)
    python compare_vto.py --mode transfer --person test_data/person/woman_dance4.jpg --source test_data/person/woman_standing5.jpg

    # Nano Banana only (skip Vertex VTO)
    python compare_vto.py --person <img> --clothing <img> --nano-only

    # Vertex VTO only (skip Nano Banana)
    python compare_vto.py --person <img> --clothing <img> --vertex-only
"""

import argparse
import base64
import json
import os
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

load_dotenv()

# --- Config ---
OUTPUT_DIR = Path("test_results/comparison")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Vertex AI config - set via environment variables or .env
VERTEX_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
VERTEX_LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
VERTEX_MODEL = "virtual-try-on-001"
VERTEX_CREDENTIALS = Path(
    os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "configs/service-account.json")
)

# Nano Banana config
NANO_MODEL = "gemini-3-pro-image-preview"

# Test cases: (person_image, clothing_image, description)
TEST_CASES = [
    ("test_data/person/woman_standing3.jpg", "test_data/clothing/tshirt_black.png", "Woman + Black T-shirt"),
    ("test_data/person/woman_standing4.jpg", "test_data/clothing/tshirt_black.png", "Woman2 + Black T-shirt"),
    ("test_data/person/woman_standing5.jpg", "test_data/clothing/sckirt.png", "Woman3 + Skirt"),
    ("test_data/person/man_standing.jpg", "test_data/clothing/tshirt_black.png", "Man + Black T-shirt"),
    ("test_data/person/man_standing2.jpg", "test_data/clothing/tshirt_black.png", "Man2 + Black T-shirt"),
    ("test_data/person/178cm_man_front.png", "test_data/clothing/tshirt_black.png", "178cm Man + Black T-shirt"),
    ("test_data/person/160cm_woman.png", "test_data/clothing/sckirt.png", "160cm Woman + Skirt"),
    ("test_data/person/woman_dance1.jpg", "test_data/clothing/tshirt_black.png", "Dance pose + Black T-shirt"),
]


# --- Vertex AI Virtual Try-On ---

def get_vertex_token() -> str:
    """Get access token from service account."""
    if not VERTEX_PROJECT or not VERTEX_CREDENTIALS.exists():
        raise RuntimeError(
            "Vertex AI not configured. Set GOOGLE_CLOUD_PROJECT and "
            "GOOGLE_APPLICATION_CREDENTIALS in .env"
        )
    from google.oauth2 import service_account
    import google.auth.transport.requests

    credentials = service_account.Credentials.from_service_account_file(
        str(VERTEX_CREDENTIALS),
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    credentials.refresh(google.auth.transport.requests.Request())
    return credentials.token


def run_vertex_vto(person_path: str, clothing_path: str) -> Image.Image | None:
    """Run Vertex AI Virtual Try-On and return PIL Image."""
    import io

    person_b64 = base64.b64encode(Path(person_path).read_bytes()).decode()
    clothing_b64 = base64.b64encode(Path(clothing_path).read_bytes()).decode()

    token = get_vertex_token()
    endpoint = (
        f"https://{VERTEX_LOCATION}-aiplatform.googleapis.com/v1/"
        f"projects/{VERTEX_PROJECT}/locations/{VERTEX_LOCATION}/"
        f"publishers/google/models/{VERTEX_MODEL}:predict"
    )

    body = {
        "instances": [{
            "personImage": {"image": {"bytesBase64Encoded": person_b64}},
            "productImages": [{"image": {"bytesBase64Encoded": clothing_b64}}],
        }],
        "parameters": {"sampleCount": 1},
    }

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"  [Vertex VTO] HTTP {e.code}: {e.read().decode()[:200]}")
        return None

    predictions = result.get("predictions", [])
    if predictions:
        img_b64 = predictions[0].get("bytesBase64Encoded", "")
        if img_b64:
            return Image.open(io.BytesIO(base64.b64decode(img_b64)))
    return None


# --- Nano Banana ---

def run_nano_banana(person_path: str, clothing_path: str, mode: str = "clothing") -> Image.Image | None:
    """Run Nano Banana Pro try-on and return PIL Image."""
    import io
    from google import genai
    from google.genai import types

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("  [Nano Banana] GEMINI_API_KEY not set")
        return None

    client = genai.Client(api_key=api_key)

    if mode == "transfer":
        prompt = """You are a virtual try-on system.
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
    else:
        prompt = """You are a virtual try-on system.
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

    person_bytes = Path(person_path).read_bytes()
    clothing_bytes = Path(clothing_path).read_bytes()

    person_mime = "image/png" if person_path.endswith(".png") else "image/jpeg"
    clothing_mime = "image/png" if clothing_path.endswith(".png") else "image/jpeg"

    person_part = types.Part.from_bytes(data=person_bytes, mime_type=person_mime)
    clothing_part = types.Part.from_bytes(data=clothing_bytes, mime_type=clothing_mime)

    try:
        response = client.models.generate_content(
            model=NANO_MODEL,
            contents=[prompt, person_part, clothing_part],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )
    except Exception as e:
        print(f"  [Nano Banana] Error: {e}")
        return None

    try:
        if not response.candidates or not response.candidates[0].content.parts:
            reason = getattr(response.candidates[0], "finish_reason", "unknown") if response.candidates else "no candidates"
            print(f"  [Nano Banana] No content returned (reason: {reason})")
            return None
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                return Image.open(io.BytesIO(part.inline_data.data))
    except (AttributeError, TypeError) as e:
        print(f"  [Nano Banana] Response parse error: {e}")
    return None


# --- Comparison image ---

def create_comparison(
    person_path: str,
    clothing_path: str,
    nano_img: Image.Image | None,
    vertex_img: Image.Image | None,
    description: str,
    mode: str = "clothing",
    pasta_img: Image.Image | None = None,
) -> Path:
    """Create side-by-side comparison image."""
    # Target height for all panels
    target_h = 800
    padding = 20
    label_h = 40

    # Load input images
    person_img = Image.open(person_path)
    clothing_img = Image.open(clothing_path)

    def resize_to_height(img: Image.Image, h: int) -> Image.Image:
        ratio = h / img.height
        return img.resize((int(img.width * ratio), h), Image.LANCZOS)

    # Resize all to same height
    panels = []
    labels = []

    # Input: person (target)
    p = resize_to_height(person_img, target_h)
    panels.append(p)
    labels.append("Target Person")

    # Input: clothing or source person
    c = resize_to_height(clothing_img, target_h)
    panels.append(c)
    labels.append("Source (clothes)" if mode == "transfer" else "Clothing")

    # PASTA-GAN++ result (legacy, if provided)
    if pasta_img is not None:
        pg = resize_to_height(pasta_img, target_h)
        panels.append(pg)
        labels.append("PASTA-GAN++")

    # Nano Banana result
    if nano_img:
        n = resize_to_height(nano_img, target_h)
    else:
        n = Image.new("RGB", (int(target_h * 0.6), target_h), (128, 128, 128))
    panels.append(n)
    labels.append("Nano Banana")

    # Vertex VTO result
    if vertex_img:
        v = resize_to_height(vertex_img, target_h)
    else:
        v = Image.new("RGB", (int(target_h * 0.6), target_h), (128, 128, 128))
    panels.append(v)
    labels.append("Vertex AI VTO")

    # Calculate canvas size
    total_w = sum(p.width for p in panels) + padding * (len(panels) + 1)
    total_h = target_h + label_h + padding * 3

    canvas = Image.new("RGB", (total_w, total_h), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    # Try to load a font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except OSError:
        font = ImageFont.load_default()
        small_font = font

    # Draw title
    draw.text((padding, padding // 2), description, fill=(0, 0, 0), font=font)

    # Paste panels with labels
    x = padding
    y_img = label_h + padding * 2

    for panel, label in zip(panels, labels):
        # Label
        draw.text((x, label_h + padding // 2), label, fill=(0, 0, 0), font=small_font)
        # Image
        canvas.paste(panel, (x, y_img))
        x += panel.width + padding

    # Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    person_name = Path(person_path).stem
    clothing_name = Path(clothing_path).stem
    output_path = OUTPUT_DIR / f"{timestamp}_{person_name}_{clothing_name}.png"
    canvas.save(output_path, "PNG")
    return output_path


def run_single(person_path: str, clothing_path: str, description: str,
               mode: str = "clothing",
               nano_only: bool = False, vertex_only: bool = False,
               pasta_path: str | None = None) -> Path:
    """Run comparison for a single test case."""
    print(f"\n{'='*60}")
    print(f"Test: {description}")
    print(f"  Mode:     {mode}")
    print(f"  Person:   {person_path}")
    print(f"  {'Source' if mode == 'transfer' else 'Clothing'}: {clothing_path}")

    nano_img = None
    vertex_img = None

    if not vertex_only:
        print("  Running Nano Banana Pro...")
        nano_img = run_nano_banana(person_path, clothing_path, mode)
        print(f"  Nano Banana: {'OK' if nano_img else 'FAILED'}")

    if not nano_only:
        print("  Running Vertex AI VTO...")
        if mode == "transfer":
            print("  (Note: VTO is designed for product images, not person-to-person)")
        vertex_img = run_vertex_vto(person_path, clothing_path)
        print(f"  Vertex VTO: {'OK' if vertex_img else 'FAILED'}")

    # Load PASTA-GAN++ result if provided
    pasta_img = None
    if pasta_path and Path(pasta_path).exists():
        pasta_img = Image.open(pasta_path)
        # PASTA-GAN++ output is a 3-panel image (source, target, result)
        # Extract only the result (right third)
        w = pasta_img.width
        result_crop = pasta_img.crop((w * 2 // 3, 0, w, pasta_img.height))
        pasta_img = result_crop
        print(f"  PASTA-GAN++: loaded from {pasta_path}")

    print("  Creating comparison image...")
    output = create_comparison(person_path, clothing_path, nano_img, vertex_img, description, mode, pasta_img)
    print(f"  Saved: {output}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare Nano Banana vs Vertex AI VTO")
    parser.add_argument("--mode", default="clothing", choices=["clothing", "transfer"],
                        help="clothing: product image, transfer: person-to-person")
    parser.add_argument("--person", help="Target person image path")
    parser.add_argument("--clothing", help="Clothing product image path (mode=clothing)")
    parser.add_argument("--source", help="Source person wearing clothes (mode=transfer)")
    parser.add_argument("--all", action="store_true", help="Run all predefined test cases")
    parser.add_argument("--pasta", help="Path to PASTA-GAN++ result image (3-panel format)")
    parser.add_argument("--nano-only", action="store_true", help="Skip Vertex VTO")
    parser.add_argument("--vertex-only", action="store_true", help="Skip Nano Banana")
    args = parser.parse_args()

    if args.all:
        results = []
        for person, clothing, desc in TEST_CASES:
            if not Path(person).exists():
                print(f"Skipping (not found): {person}")
                continue
            if not Path(clothing).exists():
                print(f"Skipping (not found): {clothing}")
                continue
            out = run_single(person, clothing, desc, "clothing", args.nano_only, args.vertex_only)
            results.append(out)

        print(f"\n{'='*60}")
        print(f"All done! {len(results)} comparisons saved to {OUTPUT_DIR}/")
        for r in results:
            print(f"  {r}")

    elif args.mode == "transfer" and args.person and args.source:
        desc = f"Transfer: {Path(args.source).stem} clothes -> {Path(args.person).stem}"
        run_single(args.person, args.source, desc, "transfer", args.nano_only, args.vertex_only, args.pasta)

    elif args.person and args.clothing:
        desc = f"{Path(args.person).stem} + {Path(args.clothing).stem}"
        run_single(args.person, args.clothing, desc, "clothing", args.nano_only, args.vertex_only, args.pasta)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
