# Nano Banana 調査レポート

> 調査日: 2026-03-01

## 重要な発見

Google には **2つのアプローチ** がある：

1. **Nano Banana (Gemini Image API)** - 汎用画像生成・編集モデル
2. **Vertex AI Virtual Try-On API** - **仮想試着専用モデル**

## 1. Nano Banana モデルファミリー

### モデル一覧

| モデル | モデルID | 特徴 |
|--------|---------|------|
| **Nano Banana 2** | `gemini-3.1-flash-image-preview` | 最新・高速・Pro品質をFlash速度で (2026/02/26発表) |
| **Nano Banana Pro** | `gemini-3-pro-image-preview` | プロ向け・最高品質 |
| **Nano Banana** | `gemini-2.5-flash-image` | 初代モデル |

### 主要機能
- テキスト→画像生成
- **画像+テキスト→画像編集**（既存画像の変換が可能）
- マルチターン会話形式での繰り返し編集
- Web検索連携による正確な描写

### 仕様
- 解像度: 512px、1K、2K、4K
- アスペクト比: 14種類対応 (1:1, 16:9, 3:2, 4:5 等)
- 参考画像: 最大14枚入力可能
- SynthID透かし付与

### API 使用例 (Python)
```python
from google import genai
client = genai.Client()

# テキストのみから画像生成
response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=["Generate an image of ..."],
)

# 既存画像を編集（仮想試着への応用）
response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[person_image, clothing_image, "この人にこの服を着せてください"],
)
```

### 仮想試着への適用
- 人物画像 + 衣服画像 + プロンプトで試着画像を生成可能
- 既に開発者がReact + Gemini APIで仮想試着アプリを実装した実績あり
  - GitHub: https://github.com/oyeolamilekan/gemini-ai-tryon (MIT License)
  - Next.js + TypeScript + @google/genai SDK
  - `/api/tryon` エンドポイントで人物画像と衣服画像を受け取り合成

## 2. Vertex AI Virtual Try-On API（専用モデル）

### 概要
Google が提供する **仮想試着専用API**。人物画像と衣服画像を入力すると、その人がその服を着た画像を生成する。

### モデル
- `virtual-try-on-001`

### エンドポイント
```
POST https://LOCATION-aiplatform.googleapis.com/v1/projects/PROJECT_ID/locations/LOCATION/publishers/google/models/virtual-try-on-001:predict
```

### 入力
- **personImage**: 人物画像 (Base64 or GCS URI)
- **productImages**: 衣服画像の配列 (Base64 or GCS URI)

### パラメータ

| パラメータ | 型 | 説明 | デフォルト |
|---------|------|------|---------|
| `sampleCount` | int | 生成画像数 (1〜4) | 1 |
| `baseSteps` | int | 品質制御（大きいほど高品質） | 32 |
| `addWatermark` | bool | 透かし追加 | true |
| `seed` | uint32 | ランダムシード | - |
| `personGeneration` | string | `dont_allow` / `allow_adult` / `allow_all` | allow_adult |

### Python SDK
```python
# pip install --upgrade google-genai
from google import genai

# 環境変数の設定
# GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, GOOGLE_GENAI_USE_VERTEXAI=True

client = genai.Client()
response = client.models.predict(
    model="virtual-try-on-001",
    instances=[{
        "personImage": {"bytesBase64Encoded": person_b64},
        "productImages": [{"bytesBase64Encoded": clothing_b64}]
    }],
    parameters={"sampleCount": 4}
)
```

### 対応衣服
- トップス (Tシャツ、ブラウス等)
- ボトムス (パンツ、スカート等)
- ワンピース (ドレス等)
- 靴 (最新版で品質向上)

### 特徴
- 体型保持（body shape preservation）
- 商品忠実度（product fidelity）
- レイテンシ改善

### セットアップ要件
- Google Cloud プロジェクト（課金有効）
- Vertex AI API 有効化
- IAM ロール設定
- gcloud CLI 認証

### Colab ノートブック
https://colab.sandbox.google.com/github/GoogleCloudPlatform/generative-ai/blob/main/vision/getting-started/virtual_try_on.ipynb

## 3. 比較: どちらを使うべきか？

| 項目 | Nano Banana (Gemini API) | Vertex AI Virtual Try-On |
|------|-------------------------|------------------------|
| **目的** | 汎用画像生成・編集 | 仮想試着専用 |
| **入力** | 画像+テキストプロンプト | 人物画像+衣服画像 |
| **精度** | プロンプト依存 | 試着に最適化済み |
| **体型保持** | プロンプトで指示 | モデルに組み込み |
| **衣服忠実度** | プロンプト依存 | 専用最適化済み |
| **柔軟性** | 高い（何でもできる） | 試着に特化 |
| **セットアップ** | API Key のみ | GCP プロジェクト必要 |
| **コスト** | Gemini API 料金 | Vertex AI 料金 |

### 推奨アプローチ

**ハイブリッド戦略**:
1. **Vertex AI Virtual Try-On** をベースに使用（試着精度が高い）
2. **Nano Banana** で後処理・調整（柔軟な編集が可能）
3. **MediaPipe Pose** で前処理（体型情報の抽出、ライセンスクリーン）

```
写真 → MediaPipe Pose (Apache 2.0)  → 体型・ポーズ情報
     → Vertex AI Virtual Try-On      → 基本試着画像生成
     → Nano Banana (後処理)           → 品質向上・調整
```

## 4. ライセンス・利用規約

- Gemini API: Google の利用規約に準拠、商用利用可能
- Vertex AI: Google Cloud の利用規約、商用利用可能
- 生成画像には SynthID 透かしが含まれる
- 権利侵害コンテンツの生成は禁止

## 5. 次のステップ

1. [ ] Google AI Studio で API Key を取得
2. [ ] Nano Banana で簡易テスト（人物+衣服のプロンプト）
3. [ ] GCP プロジェクトセットアップ（Vertex AI Virtual Try-On用）
4. [ ] Virtual Try-On API で専用モデルテスト
5. [ ] 両方の結果を比較し、最適なパイプラインを決定
6. [ ] Colab ノートブックで動作確認

## 参考リンク

- [Nano Banana 画像生成ドキュメント](https://ai.google.dev/gemini-api/docs/image-generation)
- [Nano Banana 2 発表ブログ](https://blog.google/innovation-and-ai/technology/ai/nano-banana-2/)
- [Vertex AI Virtual Try-On API リファレンス](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/model-reference/virtual-try-on-api)
- [Virtual Try-On 使い方ガイド](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/image/generate-virtual-try-on-images)
- [Gemini AI Try-On (OSS実装例)](https://github.com/oyeolamilekan/gemini-ai-tryon)
- [Virtual Try-On Colab](https://colab.sandbox.google.com/github/GoogleCloudPlatform/generative-ai/blob/main/vision/getting-started/virtual_try_on.ipynb)

---
*このドキュメントは開発の進行に合わせて随時更新されます*
