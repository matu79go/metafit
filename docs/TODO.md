# META FIT - TODO

## Phase 1: Gemini 単体での試着品質検証

### Step 1: プロンプト改善 + クリーン画像テスト ✅ 完了
- [x] テスト用のクリーンな画像を用意（測定テキスト・線なし）
- [x] 顔の同一性を保つプロンプトの試行錯誤
- [x] 構図（全身フレーミング）を維持するプロンプト改善
- [x] clothing / transfer 両モードで品質を再評価
- [x] 複数パターンテスト（体型・ポーズ・衣服種類の組み合わせ）
- [x] 「プロンプトだけでどこまで行けるか」の限界を見極める
- [x] **結論: 高解像度画像なら Gemini 単体で十分な品質**

### Step 2: MediaPipe 中間処理 → 不要と判断
- [x] MediaPipe Face Mesh + Pose の実装（`--preprocess` フラグ）
- [x] Face Restore 後処理（顔貼り戻し+色調補正）の実装
- [x] **結論: 高解像度入力なら中間処理は不要。低解像度の補助としてのみ有効**

### Step 3: Graphonomy → スキップ
- ~~Graphonomy セグメンテーション~~ → Gemini 単体で十分なため不要

### Step 4: Vertex AI Virtual Try-On との比較 (進行中)
- [x] GCP プロジェクトセットアップ (`metafit-489710`, サービスアカウント方式)
- [x] Virtual Try-On (`virtual-try-on-001`) で試着テスト成功
- [x] Nano Banana vs Vertex VTO 比較テスト実施 (docs/07_vertex_vto_comparison.md)
- [x] **重要発見: transfer モードは Nano Banana が優位（服デザイン抽出が正確）**
- [x] **重要発見: 靴の着せ替えは Vertex VTO が優位**
- [x] **重要発見: ハイブリッド戦略が最適**
- [ ] clothing モード（商品画像）での詳細比較
- [ ] 処理速度・コストの計測比較
- [ ] 最適な構成を最終決定

### Step 5: ライセンスクリーン化
- [ ] 不要になった非商用コンポーネント (torch_utils/, dnnlib/, training/) を除去
- [ ] 全コンポーネントが商用利用可能 (Apache 2.0 / MIT) であることを最終確認

### 判断基準
各ステップで以下を評価し、改善が十分なら次のステップに進まない：
- 顔の同一性 (最重要)
- 体型・ポーズの保持
- 衣服のフィット感・忠実度
- 構図の維持
- 処理時間

## Phase 2: 残課題の改善
- [ ] 手足の末端ポーズが変わる問題のプロンプト改善
- [ ] 背景がソース画像に引っ張られる問題の対応
- [ ] IMAGE_SAFETY フィルター回避（露出の多い衣服への対応策）
- [ ] 別の API 以外の方法の検討

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
- [x] docs/ フォルダ作成・TODO.md 作成
- [x] Bitbucket からソースコード取得
- [x] GitHub リポジトリ作成・移行
- [x] 有用な Claude skills のインストール
- [x] プロジェクト履歴のドキュメント化
- [x] ライセンス調査 (docs/04_license_audit.md)

### Phase 1 テスト
- [x] Nano Banana 調査 (docs/05_nano_banana_research.md)
- [x] API Key 取得・セットアップ
- [x] Nano Banana Pro で試着テスト (clothing + transfer 両モード)
- [x] 初期テスト結果記録 (docs/06_tryon_test_results.md)
- [x] 高解像度 + アクションポーズテスト（Unsplash画像、16テスト実施）
- [x] MediaPipe 中間処理の実装・検証 → 高解像度なら不要と結論
- [x] Face Restore 後処理の実装・検証
- [x] 異性間着せ替え（女性服→男性、男性スーツ→女性）テスト
- [x] **重要発見: 高解像度画像 + Gemini 単体で仮想試着は十分な品質**
- [x] **重要発見: ライセンス完全クリーンな状態で実現**
- [x] **重要発見: 中間処理（MediaPipe）は基本不要**
- [x] Vertex AI VTO セットアップ・初期比較テスト (docs/07_vertex_vto_comparison.md)
- [x] 比較テストスクリプト作成 (`compare_vto.py`)

---
*最終更新: 2026-03-09*
