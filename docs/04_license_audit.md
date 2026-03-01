# ライセンス調査報告

> 調査日: 2026-03-01

## 概要

本プロジェクトは複数のオープンソースプロジェクトを統合して構築されている。
商用利用を視野に入れる場合、各コンポーネントのライセンスを正確に把握する必要がある。

## 調査結果

### 非商用ライセンス（商用利用不可）

| プロジェクト | ライセンス | 該当ファイル | 商用ライセンス |
|------------|-----------|-------------|-------------|
| **StyleGAN2 (NVIDIA)** | NVIDIA Source Code License-NC | `torch_utils/`, `dnnlib/`, `training/networks.py`, `training/augment.py` | NVIDIA Research に問い合わせ |
| **PASTA-GAN++** | 非商用研究限定（README記載） | メインモデル全体 | 著者に問い合わせ |
| **OpenPose (CMU)** | CMU Academic Non-Commercial | `src/keypoints_model.py`, `src/body.py`, `src/generate_keypoints.py` | CMU FlintBox 経由（約$25,000/年） |
| **PF-AFN** | 非商用研究限定（README記載） | `20260301bak/` のみ | 著者に問い合わせ |
| **FlowNet2 (Freiburg)** | Research-Only | `20260301bak/` のみ | 著者の同意が必要 |

### 商用利用可能なライセンス

| プロジェクト | ライセンス | 該当ファイル | 条件 |
|------------|-----------|-------------|------|
| **Graphonomy** | MIT | `src/graphonomy/` | 著作権表示の維持 |
| **SyncBatchNorm** | MIT | `sync_batchnorm/` | 著作権表示の維持 |
| **PIFu** | MIT | `20260301bak/` のみ | 著作権表示の維持 |
| **FlowNet2-PyTorch (NVIDIA)** | Apache 2.0 | `20260301bak/` のみ | ライセンス・著作権表示、特許付与あり |
| **PyTorch** | BSD | フレームワーク依存 | 著作権表示の維持 |
| **OpenCV** | Apache 2.0 | 依存ライブラリ | ライセンス表示 |

## 重要な判断基準：パイプライン利用もライセンス対象

**非商用ライセンスのソフトウェアは、パイプラインの一部として使う場合も商用利用に該当する。**

### 例

```
パターンA（問題なし）:
  写真 → Nano Banana API → 試着画像
  → Nano Banana のライセンスのみ適用

パターンB（NG: OpenPose の商用利用に該当）:
  写真 → OpenPose（キーポイント検出） → Nano Banana → 試着画像
  → OpenPose の非商用ライセンスに違反

パターンC（NG: StyleGAN2 の商用利用に該当）:
  写真 → PASTA-GAN++/StyleGAN2 ベースの推論 → 試着画像
  → NVIDIA / PASTA-GAN++ の非商用ライセンスに違反
```

**中間処理であっても、商用プロダクトの一部として使用すれば非商用ライセンスに違反する。**

## Nano Banana 移行時の方針

### 置き換えが必要なコンポーネント

| 現行コンポーネント | 機能 | 商用利用可能な代替候補 |
|------------------|------|---------------------|
| **OpenPose** | ポーズ検出 (18点) | MediaPipe Pose (Apache 2.0), MoveNet (Apache 2.0), YOLOv8-pose (AGPL/商用) |
| **PASTA-GAN++** | 衣服生成 | Nano Banana で代替（本プロジェクトの目的） |
| **StyleGAN2** | ジェネレーター基盤 | Nano Banana で代替 |

### そのまま使えるコンポーネント

| コンポーネント | 機能 | ライセンス |
|-------------|------|-----------|
| **Graphonomy** | 人体セグメンテーション | MIT |
| **SyncBatchNorm** | バッチ正規化 | MIT |
| **OpenCV** | 画像処理全般 | Apache 2.0 |

### ポーズ検出の代替候補詳細

1. **MediaPipe Pose (Google)** - Apache 2.0
   - 33点のランドマーク検出
   - リアルタイム対応
   - 商用利用完全OK
   - Python / JavaScript / C++ 対応

2. **MoveNet (Google)** - Apache 2.0
   - TensorFlow Hub で公開
   - Lightning / Thunder の2モデル
   - 17点検出
   - 商用利用完全OK

3. **YOLOv8-Pose (Ultralytics)** - AGPL-3.0 / 商用ライセンス
   - 高精度なポーズ検出
   - 商用利用には Ultralytics の商用ライセンスが必要
   - ただしAGPLより安価な選択肢

## 推奨アクション

1. [x] 公開リポジトリの README に非商用研究目的である旨を明記
2. [ ] 各OSSの著作権表記が既存コードで維持されていることを確認
3. [ ] Nano Banana 移行時に OpenPose を MediaPipe Pose に置き換え
4. [ ] 移行完了後、非商用コンポーネント (torch_utils/, dnnlib/ 等) を除去
5. [ ] 最終的に全コンポーネントのライセンスが商用利用可能であることを確認
6. [ ] LICENSE ファイルを作成し、使用OSSの帰属を記載

---
*このドキュメントは法的助言ではありません。商用化の際は知的財産の専門家に相談してください。*
