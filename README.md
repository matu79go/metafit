# META FIT - AI Virtual Try-On

AI-powered virtual try-on system that generates realistic images of clothing on a user's body from a single photo.

Two modern API-based engines and one legacy GAN-based engine are available.

## Important Notice

> **This repository contains components under different licenses.**
> - **PASTA-GAN++ (legacy)**: Non-commercial research and educational purposes only. See [License Notice](#license-notice) below.
> - **Nano Banana / Vertex AI VTO (current)**: Commercial use allowed under Google API terms.
>
> Please read the license section carefully before using any part of this project.

---

## Quick Start

### Option A: Nano Banana (Recommended)

The simplest and most capable option. Uses Gemini API for virtual try-on.

#### Prerequisites

```bash
pip install google-genai python-dotenv pillow
```

#### Get API Key

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Create an API key
3. Create `.env` file in the project root:

```bash
GEMINI_API_KEY=your-api-key-here
```

#### Run Try-On

```bash
# Clothing mode: product image -> person
python3 try_on_test.py --person test_data/person/woman_standing4.jpg \
                       --clothing test_data/clothing/red_dress.jpg

# Transfer mode: source person's clothes -> target person
python3 try_on_test.py --mode transfer \
                       --person test_data/person/woman_standing3.jpg \
                       --source test_data/person/woman_standing5.jpg

# With MediaPipe preprocessing (usually not needed for high-res images)
python3 try_on_test.py --mode transfer \
                       --person test_data/person/man_standing.jpg \
                       --source test_data/person/man_standing2.jpg \
                       --preprocess
```

Results are saved to `test_results/nano_banana/`.

---

### Option B: Vertex AI Virtual Try-On

Google's dedicated virtual try-on model. Best for clothing product images (flat lay / white background).

#### Prerequisites

```bash
pip install google-genai google-auth python-dotenv pillow
```

#### GCP Setup

1. **Create a GCP project** (or use an existing one) at [Google Cloud Console](https://console.cloud.google.com)

2. **Enable Vertex AI API**:
   - Go to: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com
   - Click "Enable"

3. **Create a Service Account**:
   - Go to: https://console.cloud.google.com/iam-admin/serviceaccounts
   - Click "Create Service Account"
   - Name: any name (e.g., `vto-user`)
   - Grant role: **Vertex AI User** (`roles/aiplatform.user`)

4. **Download JSON key**:
   - Click on the created service account
   - Go to "Keys" tab -> "Add Key" -> "Create new key" -> JSON
   - Save the downloaded JSON file to `configs/` directory (gitignored)

5. **Configure `.env`**:

```bash
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=configs/your-key-file.json
```

> **Note**: GCP offers $300 free credit for new accounts. Virtual Try-On costs approximately $0.02-0.04 per image.

> **Tip**: If `gcloud auth application-default login` fails with scope errors (common with older gcloud versions), the service account method above is more reliable.

#### Run Try-On

```bash
# Connection test
python3 test_vertex_vto.py

# Clothing mode (Vertex VTO's strength)
python3 test_vertex_vto.py test_data/person/woman_standing4.jpg test_data/clothing/red_dress.jpg

# Generate multiple samples (up to 4)
python3 test_vertex_vto.py test_data/person/man_standing.jpg test_data/clothing/hoodie.jpg 4
```

Results are saved to `test_results/vertex_vto/`.

---

### Option C: PASTA-GAN++ (Legacy)

> **WARNING**: This is the legacy GAN-based approach. It requires GPU (NVIDIA CUDA), Docker, and large model weights (~3GB). The results are significantly inferior to Nano Banana / Vertex VTO. Included for research comparison purposes only.

> **LICENSE**: PASTA-GAN++ and its dependencies (StyleGAN2, OpenPose) are **non-commercial research only**. Do NOT use for commercial purposes.

#### Prerequisites

- NVIDIA GPU with CUDA support
- Docker with [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
- Model weights (download from Google Drive link below)

#### Setup

1. **Download test data and model weights**:

   https://drive.google.com/drive/folders/17Q3TsWovNJWrC7VR389AvHVG5Mpve6sn?usp=share_link

   Place them so the directory structure looks like:
   ```
   metafit/
   ├── weights/
   │   ├── pasta-gan++/network-snapshot-004408.pkl
   │   ├── openpose/body_pose_model.pth
   │   └── graphonomy/inference.pth
   └── test_datas/
       └── image/  (test images, 320x512px, white background)
   ```

2. **Build Docker image**:
   ```bash
   make build
   ```

3. **Run Docker container**:
   ```bash
   make run
   ```

4. **Configure test pairs** in `test_datas/test_pairs.txt`:
   ```
   target_person.jpg source_model.jpg
   ```

5. **Run inference**:
   ```bash
   python3 test.py --config configs/test_config.yaml
   ```

   Results are saved to `test_results/full/`.

#### Test Configuration

Edit `configs/test_config.yaml`:
```yaml
dataroot: test_datas
testtxt: test_pairs.txt
network: weights/pasta-gan++/network-snapshot-004408.pkl
outdir: test_results/full
batchsize: 1
testpart: full          # full / upper / lower
use_sleeve_mask: false
```

#### Input Requirements

- Image size: **320x512 pixels** (width x height)
- Full-length photo on **white background**
- Supported parts: full body, upper body, lower body

---

## Test Data

### Person images (`test_data/person/`)

Various body types, poses, and genders for comprehensive testing. All images are from [Unsplash](https://unsplash.com) (free for commercial use, no attribution required).

### Clothing images (`test_data/clothing/`)

| File | Type | Source |
|------|------|--------|
| `tshirt_black.png` | Black T-shirt | - |
| `sckirt.png` | Skirt | - |
| `red_dress.jpg` | Red dress | [Unsplash](https://unsplash.com) |
| `denim_jacket.jpg` | Denim jacket | [Unsplash](https://unsplash.com) |
| `hoodie.jpg` | Grey hoodie | [Unsplash](https://unsplash.com) |
| `jeans.jpg` | Jeans | [Unsplash](https://unsplash.com) |
| `striped_shirt.jpg` | Striped shirt | [Unsplash](https://unsplash.com) |
| `suit_blazer.jpg` | Navy suit | [Unsplash](https://unsplash.com) |

---

## Engine Comparison

| Feature | PASTA-GAN++ (Legacy) | Nano Banana (Current) | Vertex AI VTO |
|---------|---------------------|----------------------|---------------|
| **Approach** | GAN (local GPU) | Gemini API (cloud) | Dedicated VTO model (cloud) |
| **Clothing mode** (product -> person) | N/A | Good | **Best** (faithful reproduction) |
| **Transfer mode** (person -> person) | Poor | **Best** | Not supported |
| **Body type diversity** | Poor (slim bias) | **Best** (faithful) | Good |
| **Complex patterns** | Poor | **Best** | Good |
| **Shoes** | N/A | Poor | **Best** |
| **Safety filter** | None (local) | Strict (blocks exposed clothing) | Moderate (inconsistent) |
| **Setup complexity** | High (GPU + Docker) | Low (API key only) | Medium (GCP project) |
| **Cost** | Free (local) | Free tier available | ~$0.02-0.04/image |
| **Commercial use** | **No** | Yes | Yes |

---

## License Notice

### Non-Commercial Components (PASTA-GAN++ legacy pipeline)

The following components are included for **research and educational purposes only**. They **MUST NOT** be used for commercial purposes:

| Component | License | Repository |
|-----------|---------|------------|
| [PASTA-GAN++](https://github.com/xiezhy6/PASTA-GAN) | Non-commercial research only | Try-on generation |
| [StyleGAN2](https://github.com/NVlabs/stylegan2-ada-pytorch) (NVIDIA) | NVIDIA Source Code License-NC | Generator backbone |
| [OpenPose](https://github.com/CMU-Perceptual-Computing-Lab/openpose) (CMU) | CMU Academic Non-Commercial | Pose estimation |

**Affected directories**: `torch_utils/`, `dnnlib/`, `training/`, `src/generate_keypoints.py`, `src/body.py`

> If you wish to use OpenPose commercially, a license is available through [CMU FlintBox](https://cmu.flintbox.com/technologies/b820c21d-8571-4d6a-9bc6-efce58076e3a) (~$25,000/year).

### Commercial-Friendly Components

| Component | License | Usage |
|-----------|---------|-------|
| [Graphonomy](https://github.com/Gaoyiminggithub/Graphonomy) | MIT | Body segmentation |
| [MediaPipe](https://github.com/google-ai-edge/mediapipe) | Apache 2.0 | Face/Pose detection |
| [PyTorch](https://github.com/pytorch/pytorch) | BSD | ML framework |
| [OpenCV](https://github.com/opencv/opencv) | Apache 2.0 | Image processing |
| [Pillow](https://github.com/python-pillow/Pillow) | MIT-like (HPND) | Image processing |
| Gemini API (Nano Banana) | [Google API Terms](https://ai.google.dev/gemini-api/terms) | Try-on generation |
| Vertex AI VTO | [Google Cloud Terms](https://cloud.google.com/terms) | Try-on generation |

### For Commercial Use

If you plan to use this project commercially, use **only** the Nano Banana (`try_on_test.py`) and/or Vertex AI VTO (`test_vertex_vto.py`) pipelines. These do not depend on any non-commercial components.

```
Commercial-safe pipeline:
  Photo -> Gemini API (Nano Banana) -> Try-on image     OK
  Photo -> Vertex AI VTO API        -> Try-on image     OK

NOT commercial-safe:
  Photo -> OpenPose -> PASTA-GAN++ -> Try-on image      NG
```

---

## Project Site

https://suzuki-shoten.dev/projects/metafit/
