# META FIT - AI Virtual Try-On

> **Note: This project is for non-commercial research and educational purposes only.**
> The current codebase incorporates components under non-commercial licenses
> (NVIDIA StyleGAN2, PASTA-GAN++, OpenPose). See [docs/04_license_audit.md](docs/04_license_audit.md) for details.

AI-powered virtual try-on system that generates realistic images of clothing on a user's body from a single photo.

## Setup

### Clone repo
```
git clone https://github.com/matu79go/metafit.git
```

### Download test data and weights:
https://drive.google.com/drive/folders/17Q3TsWovNJWrC7VR389AvHVG5Mpve6sn?usp=share_link

### Build docker image:
```
make build
```

### Run docker container:
```
make run
```

### Run inference
```
python3 test.py --config configs/test_config.yaml
```

## Project Documentation
- [CLAUDE.md](CLAUDE.md) - Project rules and conventions
- [docs/TODO.md](docs/TODO.md) - Task management
- [docs/01_project_history.md](docs/01_project_history.md) - Project history
- [docs/02_architecture_overview.md](docs/02_architecture_overview.md) - Architecture overview
- [docs/03_tech_blog_draft.md](docs/03_tech_blog_draft.md) - Tech blog draft
- [docs/04_license_audit.md](docs/04_license_audit.md) - License audit

## Third-Party Licenses

This project uses the following open source software:

| Component | License | Commercial Use |
|-----------|---------|---------------|
| [StyleGAN2](https://github.com/NVlabs/stylegan2-ada-pytorch) (NVIDIA) | NVIDIA Source Code License-NC | Non-commercial only |
| [PASTA-GAN++](https://github.com/xiezhy6/PASTA-GAN) | Non-commercial research only | Non-commercial only |
| [OpenPose](https://github.com/CMU-Perceptual-Computing-Lab/openpose) (CMU) | CMU Academic Non-Commercial | Non-commercial only |
| [Graphonomy](https://github.com/Gaoyiminggithub/Graphonomy) | MIT | Allowed |
| [Synchronized-BatchNorm](https://github.com/vacancy/Synchronized-BatchNorm-PyTorch) | MIT | Allowed |
| [PyTorch](https://github.com/pytorch/pytorch) | BSD | Allowed |
| [OpenCV](https://github.com/opencv/opencv) | Apache 2.0 | Allowed |
