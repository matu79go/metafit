# Vertex AI Virtual Try-On vs Nano Banana 比較レポート

> 調査日: 2026-03-09

## 目的

Nano Banana (Gemini API) と Vertex AI Virtual Try-On (`virtual-try-on-001`) の2つのアプローチを同一画像セットで比較し、最適な構成を検討する。

## テスト環境

| 項目 | Nano Banana | Vertex AI VTO |
|------|-------------|---------------|
| **モデル** | `gemini-3-pro-image-preview` | `virtual-try-on-001` |
| **API** | Gemini Developer API | Vertex AI Prediction API (REST) |
| **認証** | API Key | GCP サービスアカウント |
| **リージョン** | - | us-central1 |
| **GCPプロジェクト** | 不要 | `metafit-489710` |

### セットアップ経緯

- gcloud CLI (v468.0.0) が古く `gcloud auth application-default login` でスコープエラーが発生
- `gcloud components update` は2時間以上フリーズして失敗
- **サービスアカウント方式に切り替え**て解決:
  - GCP Console でサービスアカウント `metafit-vto` を作成
  - `Vertex AI ユーザー` ロールを付与
  - JSON キーファイルをダウンロードして認証
- REST API で直接呼び出す方式を採用（`google-genai` SDK の `predict()` はバージョン非互換あり）

## テスト結果

### Test 1: clothing モード（商品画像 → 人物に着せる）

- **人物**: woman_standing3.jpg
- **衣服**: tshirt_black.png（黒Tシャツ商品画像）
- **結果**: 両方とも成功

| 項目 | Nano Banana | Vertex AI VTO |
|------|-------------|---------------|
| 衣服の着せ替え | ○ 正しく黒Tに着替え | ○ 正しく黒Tに着替え |
| 顔の保持 | ○ | ○ |
| ポーズ保持 | ○ | ○ |

→ clothing モードは VTO の本来の用途であり、両方とも良好な結果。

### Test 2: transfer モード（人物→人物の着せ替え）⭐ 重要発見

- **ターゲット**: woman_dance4.jpg（ダンスポーズの女性、タンクトップ着用）
- **ソース**: woman_standing5.jpg（立ちポーズの女性、Tシャツ着用）
- **タスク**: ソースの服をターゲットに着せ替え
- **結果**: 興味深い差異が発生

| 項目 | Nano Banana | Vertex AI VTO |
|------|-------------|---------------|
| **服のデザイン抽出** | ◎ ソースの服を正しく抽出・着せ替え | △ ターゲットの元の服（タンクトップ）に引っ張られた |
| **靴の着せ替え** | × 靴は着せ替えできず | ◎ 白い靴を正しく着せ替え |
| **ポーズ保持** | ○ ダンスポーズ維持 | ○ ダンスポーズ維持 |
| **顔の保持** | ○ | ○ |

#### 分析

**Nano Banana の強み:**
- プロンプトで「ソースの服を抽出してターゲットに着せろ」と指示できるため、人→人の着せ替え（transfer）が正確
- 柔軟性が高い

**Nano Banana の弱み:**
- 靴の着せ替えまでは対応しきれない（プロンプトの限界）

**Vertex AI VTO の強み:**
- 靴を含むアイテム単位の着せ替えが得意（専用モデルの強み）
- 商品画像（フラットレイ）からの着せ替えが本領

**Vertex AI VTO の弱み:**
- 人物画像から服だけを抽出するのは苦手（商品画像前提の設計）
- ターゲットの元の服に引っ張られる傾向

### Test 3: transfer モード - ふくよかな体型 + 露出の多い衣服 ⭐ 重要発見

- **ターゲット**: 159cm_woman_f.jpg（ふくよかな体型の女性）
- **ソース**: woman_dance3.jpg（ダンスポーズ、露出度の高い衣服）
- **タスク**: ソースの服をターゲットに着せ替え
- **結果**: Nano Banana が IMAGE_SAFETY フィルターでブロック

| 項目 | Nano Banana | Vertex AI VTO |
|------|-------------|---------------|
| **結果** | × IMAGE_SAFETY でブロック | ○ 成功 |
| **体型保持** | - | ○ ふくよかな体型を維持 |
| **服の着せ替え** | - | ○ |

#### 分析

- **Nano Banana** は汎用画像生成モデルのため、露出度の高い衣服の生成が SAFETY フィルターに抵触する
- **Vertex AI VTO** は試着専用モデルなので、「衣服の着せ替え」という文脈を理解しており、フィルターが適切に緩和されている
- これは実用上の大きな差異。水着・スポーツウェア・ドレスなど肌の露出がある衣服はファッション業界で一般的であり、VTO の優位性が明確

### Test 4-7: clothing モード（商品画像 → 人物）詳細比較 ⭐ VTO の本領

著作権フリーの商品画像（Unsplash）を用いて clothing モードを詳細比較。

#### Test 4: 女性 + 赤ドレス ⭐ 差が顕著

- **人物**: woman_standing4.jpg
- **衣服**: red_dress.jpg（赤いキャミドレス、Unsplash）

| 項目 | Nano Banana | Vertex AI VTO |
|------|-------------|---------------|
| **色の再現** | × 赤→ピンク寄りに変色 | ◎ 正確な赤色 |
| **デザインの忠実度** | × ロングプリーツドレスに改変 | ◎ 商品画像の丈感・形状を再現 |
| **ポーズ保持** | ○ | ○ |

→ **Vertex VTO が明確に勝利**。Nano Banana は服のデザインを「解釈」して大きく変えてしまった。

#### Test 5: 女性 + ストライプシャツ

- **人物**: woman_standing5.jpg
- **衣服**: striped_shirt.jpg（柄物シャツ、Unsplash）
- **結果**: 両方成功。ほぼ互角。VTO の方がポーズ・体型保持が若干良い。

#### Test 6: 男性 + パーカー

- **人物**: man_standing.jpg
- **衣服**: hoodie.jpg（グレーパーカー、Unsplash）
- **結果**: 両方成功。ほぼ互角。VTO の方が背景保持が良い。

#### Test 7: 男性 + スーツ

- **人物**: man_standing2.jpg
- **衣服**: suit_blazer.jpg（紺スーツ、Unsplash）
- **結果**: 両方成功。ほぼ互角。

#### clothing モード総括

| パターン | Nano Banana | Vertex AI VTO |
|---------|-------------|---------------|
| **特徴的なデザイン（ドレス等）** | △ デザインを改変する傾向 | ◎ 忠実に再現 |
| **シンプルな衣服（シャツ等）** | ○ | ○ |
| **背景保持** | △ 若干変化あり | ○ |

→ 商品画像からの着せ替え（EC サイト用途）では **Vertex VTO が安定して優位**。

## PASTA-GAN++ との3者比較 ⭐ ブログ用ハイライト

旧実装 PASTA-GAN++ が苦手としていたケース（ふくよかな体型、ボーダー柄）で、3世代のモデルを比較。
PASTA-GAN++ は過去のテスト結果画像（`20260301bak/`）を使用。

### Test 8: ふくよかな男性 + ボーダーセーター（5枚並び）

- **ターゲット**: man110.jpg（ふくよかな体型の男性、下着姿）
- **ソース**: man11.jpg（ボーダーセーターの細身男性）
- **比較画像**: `20260309_195013_man110_man11.png`

| 項目 | PASTA-GAN++ | Nano Banana | Vertex AI VTO |
|------|-------------|-------------|---------------|
| **ボーダー柄の再現** | ○ 再現できている | ◎ きれいに再現 | - |
| **体型保持** | △ 若干スリム化 | ◎ ふくよかな体型を維持 | - |
| **ショーツの着せ替え** | ○ | ○ | - |
| **顔の品質** | △ やや劣化 | ◎ | - |
| **服の着せ替え成功** | ○ | ◎ | **× 失敗（服が着せ替わっていない）** |

#### Vertex VTO 失敗の分析

- HTTP エラーは発生せず、画像は生成されている（198KB）
- しかし**服が着せ替わっておらず、ターゲットのほぼ元の姿のまま**
- **原因: VTO は商品画像（白背景フラットレイ）前提**であり、人物画像から服だけを抽出する能力がない
- man11（ボーダーセーターの男性）を「商品画像」として認識できなかった
- → **Vertex VTO は transfer モード（人→人）に対応不可**であることが確定

### Test 9: ふくよかな女性 + スリムモデルの服

- **ターゲット**: woman_chihi.jpg（ふくよかな体型の女性）
- **ソース**: savel_model.jpg（オレンジタンクトップ+ベージュショーツのスリムモデル）
- **比較画像**: `20260309_195129_woman_chihi_savel_model.png`

| 項目 | PASTA-GAN++ | Nano Banana | Vertex AI VTO |
|------|-------------|-------------|---------------|
| **服の着せ替え** | ○ できている | ◎ | × SAFETY ブロック |
| **体型保持** | **× スリムに変わっている** | △ やや変化 | - |
| **顔の品質** | △ 劣化 | ○ | - |

#### 分析

- **PASTA-GAN++ の最大の問題点が可視化された**: ふくよかな体型がスリムに変わってしまう。訓練データに少ない体型で結果が劣化する GAN の根本的限界
- **Nano Banana** はプロンプトで体型保持を指示できるため大幅に改善
- **Vertex VTO** は SAFETY フィルターでブロック。ソース画像の露出度が原因（男性の下着姿 man110 はスルーされたが、女性のタンクトップでブロック。フィルター基準にばらつきあり）

### 3者比較の総括

| 観点 | PASTA-GAN++ (旧) | Nano Banana (現) | Vertex AI VTO |
|------|-------------------|-------------------|---------------|
| **体型保持（ふくよか）** | × スリム化する | ◎ | ○（clothingモード時） |
| **ボーダー柄の再現** | ○ | ◎ | -（transfer不可） |
| **顔の品質** | △ | ◎ | ◎ |
| **transfer モード** | ○ | ◎ | × 対応不可 |
| **SAFETY フィルター** | なし（ローカル実行） | △（露出でブロック） | △（基準にばらつき） |
| **処理環境** | GPU + Docker 必須 | API Key のみ | GCP 必要 |

→ **PASTA-GAN++ → Nano Banana で劇的に改善**。特に体型多様性と顔品質で世代差が明確。

## 比較まとめ

| 観点 | Nano Banana | Vertex AI VTO | 勝者 |
|------|-------------|---------------|------|
| **clothing モード（商品→人物）** | △〜○ | ◎ | **Vertex AI VTO** |
| **transfer モード（人→人）** | ◎ | × 対応不可 | **Nano Banana** |
| **靴の着せ替え** | × | ◎ | Vertex AI VTO |
| **服デザインの忠実度（clothing）** | △（改変傾向あり） | ◎ | **Vertex AI VTO** |
| **服デザインの抽出（transfer）** | ◎ | × | **Nano Banana** |
| **露出の多い衣服** | × SAFETYブロック | △（基準にばらつき） | 条件次第 |
| **体型多様性** | ◎ | ○ | Nano Banana |
| **セットアップの容易さ** | ◎（API Key のみ） | △（GCP 必要） | Nano Banana |
| **コスト** | 無料枠大 | ~$0.02-0.04/枚 | Nano Banana |
| **柔軟性** | ◎（プロンプトで制御） | △（専用用途のみ） | Nano Banana |

## 結論と次のステップ

### 現時点の結論

1. **PASTA-GAN++ → Nano Banana で世代的な飛躍**。体型保持・顔品質・柄の再現すべてで改善
2. **用途で使い分けが最適**:
   - **clothing モード（EC サイト向け）** → Vertex AI VTO が優位（忠実度・安定性）
   - **transfer モード（人→人の着せ替え）** → Nano Banana が唯一の選択肢（VTO は対応不可）
3. **SAFETY フィルターは両方に課題あり**: Nano Banana は露出でブロック、VTO は基準にばらつき
4. **ハイブリッド戦略が最適**: 用途に応じてエンジンを切り替え、互いの弱点を補完

### Test 10-12: ふくよかな女性(159cm_woman_f) での3者比較 ⭐ ブログ用ハイライト

PASTA-GAN++ が苦手としていた「ふくよかな体型 × 様々な衣服」のケースで3世代を比較。

#### Test 10: 花柄シャツ + デニム（Desigual）

- **ターゲット**: 159cm_woman_f.jpg（ふくよかな体型）
- **ソース**: desigual_flower.jpg（複雑な花柄シャツ+ロールアップデニム）
- **比較画像**: `20260309_200441_159cm_woman_f_desigual_flower.png`

| 項目 | PASTA-GAN++ | Nano Banana | Vertex AI VTO |
|------|-------------|-------------|---------------|
| **花柄の再現** | × 服がぐちゃぐちゃ | ◎ きれいに再現 | ○ |
| **体型保持** | × スリム化 | ◎ ふくよか維持 | △ ソースのポーズに引っ張られる |
| **デニムの再現** | × | ◎ | ○ |

#### Test 11: グレースウェット + 黒パンツ（H&M）

- **ターゲット**: 159cm_woman_f.jpg
- **ソース**: hm_grey_sweat.jpg（グレースウェット+黒カーゴパンツ）
- **比較画像**: `20260309_200525_159cm_woman_f_hm_grey_sweat.png`

| 項目 | PASTA-GAN++ | Nano Banana | Vertex AI VTO |
|------|-------------|-------------|---------------|
| **服の再現** | × 服がぐちゃぐちゃ | ◎ | ○ |
| **体型保持** | × スリム化 | ◎ ふくよか維持 | △ ソースのポーズに引っ張られる |

#### Test 12: 白T + ジーンズ（男性服→女性）⭐ 最注目

- **ターゲット**: 159cm_woman_f.jpg
- **ソース**: white_tee_jeans.jpg（男性モデル、白T+ジーンズ）
- **比較画像**: `20260309_200616_159cm_woman_f_white_tee_jeans.png`

| 項目 | PASTA-GAN++ | Nano Banana | Vertex AI VTO |
|------|-------------|-------------|---------------|
| **服の再現** | × 服がぐちゃぐちゃ | ◎ | ◎ |
| **体型保持** | × スリム化 | **◎ ジーパンの足の太さが忠実に再現** | △ ソースモデルのポーズに引っ張られる |
| **異性間着せ替え** | × | ◎ 自然 | ○ |

→ **Nano Banana が最も成功**。特にジーンズが159cmのふくよかな体型に合わせて自然にフィットしており、足の太さが忠実に再現されている点が秀逸。

#### Test 10-12 総括

**PASTA-GAN++ の根本的限界**:
- 3テストすべてで服がぐちゃぐちゃ。まったく実用レベルではない
- 体型がスリム化される問題も一貫して発生
- GAN の訓練データ偏りが如実に表れている

**Nano Banana の圧勝**:
- 複雑な花柄、無地、異性間いずれも高品質に着せ替え
- **体型の忠実な再現が最大の強み**（足の太さ、腰回りなど）
- プロンプトベースの柔軟性が体型多様性に直結

**Vertex VTO の課題**:
- 服自体は着せ替えできているが、**ソースモデルのポーズに引っ張られる**傾向
- transfer モードでは Nano Banana に劣る

### 追加テスト候補

- [x] clothing モードでの詳細比較（Test 4-7）
- [x] PASTA-GAN++ との3者比較（Test 8-12）
- [ ] 男性→女性の異性間着せ替え
- [ ] アクションポーズ（走り、ストレッチ等）での比較
- [ ] 複雑なパターン・ロゴのある衣服での比較
- [ ] 処理速度の計測比較

## テストスクリプト

```bash
# 2者比較（Nano Banana vs Vertex VTO）
python compare_vto.py --mode transfer --person <ターゲット画像> --source <ソース画像>
python compare_vto.py --person <人物画像> --clothing <商品画像>

# 3者比較（PASTA-GAN++ の過去結果を含む）
python compare_vto.py --mode transfer --person <ターゲット> --source <ソース> \
  --pasta "20260301bak/Pythonコード/metafit_dev/test_results/full/<結果画像>.png"

# 結果は test_results/comparison/ に横並び比較画像として保存される
```

## 比較画像

テスト結果画像は `test_results/comparison/` に保存：
- `20260309_190204_woman_standing3_tshirt_black.png` - clothing モード比較
- `20260309_190916_woman_dance4_woman_standing5.png` - transfer モード比較 ⭐
- `20260309_191938_159cm_woman_f_woman_dance3.png` - ふくよかな体型 + 露出衣服 ⭐ SAFETYフィルター問題発見
- `20260309_193322_woman_standing4_red_dress.png` - clothing: 女性 + 赤ドレス ⭐ VTO勝利
- `20260309_193403_woman_standing5_striped_shirt.png` - clothing: 女性 + ストライプシャツ
- `20260309_193515_man_standing_hoodie.png` - clothing: 男性 + パーカー
- `20260309_193632_man_standing2_suit_blazer.png` - clothing: 男性 + スーツ
- `20260309_195013_man110_man11.png` - **3者比較**: ふくよか男性 + ボーダーセーター ⭐
- `20260309_195129_woman_chihi_savel_model.png` - **3者比較**: ふくよか女性 + タンクトップ ⭐
- `20260309_200441_159cm_woman_f_desigual_flower.png` - **3者比較**: ふくよか女性 + 花柄シャツ
- `20260309_200525_159cm_woman_f_hm_grey_sweat.png` - **3者比較**: ふくよか女性 + グレースウェット
- `20260309_200616_159cm_woman_f_white_tee_jeans.png` - **3者比較**: ふくよか女性 + 白T+ジーンズ ⭐⭐ 最注目

## 参考

- [Vertex AI Virtual Try-On ドキュメント](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/imagen/virtual-try-on-001)
- [Virtual Try-On API リファレンス](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/model-reference/virtual-try-on-api)
- [Vertex AI 料金](https://cloud.google.com/vertex-ai/generative-ai/pricing)
- [前回テスト結果](./06_tryon_test_results.md)
- [Nano Banana 調査](./05_nano_banana_research.md)

---
*このドキュメントは追加テストに応じて更新されます*
