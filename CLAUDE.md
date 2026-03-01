# META FIT - Virtual Try-On Project

## Project Overview
META FITは、AIを活用したバーチャル試着システムです。
ユーザーが全身写真をアップロードすると、任意の衣服を着た姿をリアルに生成します。

## Goal
**完璧な仮想試着** - どのような体型の人も、どのようなポーズでも、自由自在にフィットした仮想試着を実現する。

## Tech Stack
- **試着エンジン**: Gemini Nano Banana (新規) / PASTA-GAN++ (旧)
- **身体分析**: ポーズ推定 (OpenPose)、身体セグメンテーション (Graphonomy)
- **NN基盤**: PyTorch, CUDA, StyleGAN2
- **画像処理**: OpenCV, Pillow, NumPy, scikit-image
- **Webプロトタイプ**: TensorFlow.js, Three.js
- **インフラ**: Docker (PyTorch 1.7.1 + CUDA 11.0)

## Repository
- **GitHub (primary)**: https://github.com/matu79go/metafit
- **Bitbucket (legacy)**: https://bitbucket.org/suzukiy/meta_fit/src/main/
- **ベースブランチ**: `custom_training` (fixing_openpose の修正取り込み済み)

## Project Rules

### 開発ルール
1. すべての試行錯誤は `docs/` フォルダにドキュメントとして残す
2. 作業管理は `TODO.md` で行う
3. 技術ブログとしてまとめられるよう、経緯を詳細に記録する
4. コードの変更理由と結果を必ず記録する

### ドキュメント構成
- `docs/` - 技術ドキュメント、試行錯誤の記録
- `TODO.md` - 作業管理・タスク管理
- `CLAUDE.md` - プロジェクトルール（このファイル）

### コーディング規約
- Python コードは PEP 8 準拠
- 型ヒントを使用する
- **ソースコード内のコメントは英語で書く** (公開リポジトリのため)
- ドキュメント (docs/, TODO.md) は日本語OK
- Git コミットメッセージは英語

### ブランチ戦略
- `main` - 安定版
- `custom_training` - 現在のベースブランチ
- `develop` - 開発ブランチ
- `feature/*` - 機能開発
- `experiment/*` - 実験・検証

## Project Structure
```
meta_fit/
├── test.py                  # Main inference entry point
├── configs/test_config.yaml # Test configuration
├── src/                     # Core source (pose, parsing, preprocessing)
│   ├── generate_keypoints.py
│   ├── graphonomy/          # Body part segmentation (DeepLab + GCN)
│   ├── preprocess.py        # Image resize/crop (512x320)
│   └── utils.py             # Image/pose utilities
├── training/                # Model training (StyleGAN2-based)
│   ├── networks.py          # Generator/Discriminator
│   ├── dataset.py           # Uviton dataset loader
│   └── training_loop_fullbody.py
├── custom/                  # Custom training code
├── torch_utils/             # PyTorch CUDA operations
├── dnnlib/                  # Model loading utilities
├── docker/Dockerfile        # Container definition
├── docs/                    # Technical documentation
└── .claude/skills/          # Claude Code skills
```

## Key References
- プロジェクトサイト: https://suzuki-shoten.dev/projects/metafit/
- 旧実装: PF-AFN (2D), PIFu (3D), PASTA-GAN++
- 新実装: Gemini Nano Banana ベース
