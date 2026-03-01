# META FIT - TODO

## Phase 1: Nano Banana 試着テスト

### Step 1: Nano Banana Pro (Gemini 3 Pro) で試着テスト ← 今ここ
- [x] Nano Banana 調査 (docs/05_nano_banana_research.md)
- [ ] Google AI Studio で API Key 取得
- [ ] Nano Banana Pro (`gemini-3-pro-image-preview`) で簡易試着テスト
- [ ] プロンプト設計・試行錯誤（人物画像+衣服画像→試着画像）
- [ ] 結果の品質評価（体型保持、衣服忠実度、自然さ）
- [ ] 複数パターンテスト（体型・ポーズ・衣服種類の組み合わせ）

### Step 2: Vertex AI Virtual Try-On で比較テスト
- [ ] GCP プロジェクトセットアップ
- [ ] Vertex AI API 有効化
- [ ] Virtual Try-On (`virtual-try-on-001`) で同じ画像セットをテスト
- [ ] Nano Banana Pro との結果比較
- [ ] コスト・精度・速度の総合評価
- [ ] 最適なモデル（or ハイブリッド構成）を決定

### Step 3: ライセンスクリーン化
- [ ] **全コンポーネントを商用利用可能ライセンス (Apache 2.0 / MIT) に置き換え**
  - [ ] OpenPose → MediaPipe Pose (Apache 2.0) に置き換え
  - [ ] PASTA-GAN++ / StyleGAN2 → Nano Banana or VTO に置き換え
  - [ ] Graphonomy (MIT) → そのまま利用OK
  - [ ] 不要になった非商用コンポーネント (torch_utils/, dnnlib/, training/) を除去
- [ ] 精度評価基準の策定

### Phase 1 完了時の目標パイプライン
```
写真 → MediaPipe Pose (Apache 2.0)  → 体型・ポーズ情報抽出
     → Graphonomy (MIT)              → 部位セグメンテーション
     → Nano Banana or VTO            → 試着画像生成
```
※ 全ステップが商用利用可能なライセンスで構成されること

## Phase 2: 精度向上
- [ ] 多様な体型への対応
- [ ] 多様なポーズへの対応
- [ ] 衣服テクスチャ・パターンの忠実度向上
- [ ] フィッティング精度の改善
- [ ] エッジケースの特定と対応

## Phase 3: 統合・最適化
- [ ] Web フロントエンド構築
- [ ] 処理速度の最適化
- [ ] ユーザーテスト
- [ ] 技術ブログ記事の完成
- [ ] LICENSE ファイル作成（使用OSSの帰属を記載）

---

## 完了済み

### Phase 0: プロジェクトセットアップ
- [x] 旧プロジェクトの調査・把握
- [x] プロジェクトサイト (suzuki-shoten.dev) の内容確認
- [x] 20260301bak のソース解析
- [x] CLAUDE.md 作成
- [x] docs/ フォルダ作成
- [x] TODO.md 作成
- [x] Bitbucket からソースコード取得
- [x] GitHub リポジトリ作成・移行
- [x] 有用な Claude skills のインストール
- [x] プロジェクト履歴のドキュメント化
- [x] ライセンス調査 (docs/04_license_audit.md)

---
*最終更新: 2026-03-01*
