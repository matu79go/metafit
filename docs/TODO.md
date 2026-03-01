# META FIT - TODO

## Phase 0: プロジェクトセットアップ
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

## Phase 1: Nano Banana 基盤構築 + ライセンスクリーン化
- [ ] Nano Banana の API 調査・セットアップ
- [ ] 基本的な仮想試着プロンプトの設計
- [ ] 簡易テスト（シンプルな写真での試着）
- [ ] **全コンポーネントを商用利用可能ライセンス (Apache 2.0 / MIT) に置き換え**
  - [ ] OpenPose → MediaPipe Pose (Apache 2.0) に置き換え
  - [ ] PASTA-GAN++ / StyleGAN2 → Nano Banana API に置き換え
  - [ ] Graphonomy (MIT) → そのまま利用OK
  - [ ] 不要になった非商用コンポーネント (torch_utils/, dnnlib/, training/) を除去
- [ ] 旧システム (PASTA-GAN++) との比較検証
- [ ] 精度評価基準の策定

### Phase 1 完了時の目標パイプライン
```
写真 → MediaPipe Pose (Apache 2.0)  → 体型・ポーズ情報抽出
     → Graphonomy (MIT)              → 部位セグメンテーション
     → Nano Banana API               → 試着画像生成
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
*最終更新: 2026-03-01*
