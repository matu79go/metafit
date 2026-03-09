"""Test script for Vertex AI Virtual Try-On API."""

import json
import os
import sys
import base64
from pathlib import Path

import google.auth
import google.auth.transport.requests
from google.oauth2 import service_account

# Config
PROJECT_ID = "metafit-489710"
LOCATION = "us-central1"
MODEL = "virtual-try-on-001"
CREDENTIALS_PATH = Path(__file__).parent / "configs" / "metafit-489710-6f5da50df8f4.json"
ENDPOINT = (
    f"https://{LOCATION}-aiplatform.googleapis.com/v1/"
    f"projects/{PROJECT_ID}/locations/{LOCATION}/"
    f"publishers/google/models/{MODEL}:predict"
)


def get_access_token() -> str:
    """Get access token from service account credentials."""
    credentials = service_account.Credentials.from_service_account_file(
        str(CREDENTIALS_PATH),
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    credentials.refresh(google.auth.transport.requests.Request())
    return credentials.token


def test_connection() -> None:
    """Test basic connectivity by obtaining an access token."""
    token = get_access_token()
    print(f"Access token obtained: {token[:20]}...")
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print(f"Endpoint: {ENDPOINT}")
    print("Connection OK!")


def test_vto(person_path: str, clothing_path: str, sample_count: int = 1) -> None:
    """Test Virtual Try-On with actual images via REST API."""
    import urllib.request

    person_bytes = Path(person_path).read_bytes()
    clothing_bytes = Path(clothing_path).read_bytes()

    person_b64 = base64.b64encode(person_bytes).decode("utf-8")
    clothing_b64 = base64.b64encode(clothing_bytes).decode("utf-8")

    print(f"Person image: {person_path} ({len(person_bytes):,} bytes)")
    print(f"Clothing image: {clothing_path} ({len(clothing_bytes):,} bytes)")

    token = get_access_token()

    request_body = {
        "instances": [
            {
                "personImage": {
                    "image": {"bytesBase64Encoded": person_b64}
                },
                "productImages": [
                    {"image": {"bytesBase64Encoded": clothing_b64}}
                ],
            }
        ],
        "parameters": {
            "sampleCount": sample_count,
        },
    }

    data = json.dumps(request_body).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )

    print(f"Sending request to {MODEL} (sampleCount={sample_count})...")

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"HTTP {e.code} Error: {error_body}")
        sys.exit(1)

    predictions = result.get("predictions", [])
    print(f"Response received! Predictions: {len(predictions)}")

    # Save output
    output_dir = Path("test_results/vertex_vto")
    output_dir.mkdir(parents=True, exist_ok=True)

    person_name = Path(person_path).stem
    clothing_name = Path(clothing_path).stem

    for i, pred in enumerate(predictions):
        img_b64 = pred.get("bytesBase64Encoded", "")
        if img_b64:
            img_bytes = base64.b64decode(img_b64)
            output_path = output_dir / f"{person_name}_{clothing_name}_{i}.png"
            output_path.write_bytes(img_bytes)
            print(f"Saved: {output_path} ({len(img_bytes):,} bytes)")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        test_connection()
    elif len(sys.argv) >= 3:
        sample_count = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        test_vto(sys.argv[1], sys.argv[2], sample_count)
    else:
        print("Usage:")
        print("  python test_vertex_vto.py                                    # connection test")
        print("  python test_vertex_vto.py <person.jpg> <cloth.jpg>           # VTO test")
        print("  python test_vertex_vto.py <person.jpg> <cloth.jpg> <count>   # VTO with N samples")
