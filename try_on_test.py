"""
META FIT - Virtual Try-On Test with Nano Banana Pro (Gemini 3 Pro Image)

Usage:
    # Mode 1: clothing item image + person = try-on
    python try_on_test.py --person <person> --clothing <clothing>

    # Mode 2: model wearing clothes + target person = target wearing those clothes
    python try_on_test.py --mode transfer --source <dressed_model> --person <target_person>
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
) -> None:
    """Run virtual try-on with Nano Banana Pro."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not set in .env")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    print(f"Model: {MODEL_ID}")
    print(f"Mode: {mode}")
    print(f"Person: {person_path}")
    print(f"Clothing/Source: {clothing_path}")
    print("Generating try-on image...")

    person_part = load_image_as_part(person_path)
    clothing_part = load_image_as_part(clothing_path)

    response = client.models.generate_content(
        model=MODEL_ID,
        contents=[
            prompt,
            person_part,
            clothing_part,
        ],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )

    result_path = save_result(response, person_path, clothing_path, mode)

    if result_path:
        print(f"\nTry-on complete! Result: {result_path}")
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
    args = parser.parse_args()

    if args.mode == "clothing":
        clothing = args.clothing or "test_data/clothing/tshirt_black.png"
        run_tryon(args.person, clothing, PROMPT_CLOTHING, "clothing")
    elif args.mode == "transfer":
        if not args.source:
            print("Error: --source is required for transfer mode")
            sys.exit(1)
        run_tryon(args.person, args.source, PROMPT_TRANSFER, "transfer")


if __name__ == "__main__":
    main()
