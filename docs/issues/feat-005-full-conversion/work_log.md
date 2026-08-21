# feat-005 作業記録（work_log）

design.md の手順に従い、手順ごとに追記する（上書きしない）。

## §4.1 入力PDF の生成（2026-08-18）

### 事前確認

- 空き容量: 93GB（≥ 20GB 合格）
- `du -sb ~/.cache` 実行前値: **53,086,712,269 bytes**（§4.2 受け入れ基準4の基準値）
- 実行前照合（ファイル数）: chap00: 20 / chap01: 84 / chap02: 70 / chap03: 44 / chap04: 48 / chap05: 70 / chap06: 36 / chap07: 24 — **すべて設計の P と一致（合格）**

### 生成結果（受け入れ基準1・2: 合格）

| 対象 | 所要 | サイズ | pdfinfo ページ数 | 判定 |
|---|---|---|---|---|
| chap00 | 3秒 | 8,077,676 | 20 | ✓ |
| chap01 | 22秒 | 65,340,958 | 84 | ✓ |
| chap02 | 19秒 | 55,260,264 | 70 | ✓ |
| chap03 | 12秒 | 36,626,610 | 44 | ✓ |
| chap04 | 13秒 | 40,660,164 | 48 | ✓ |
| chap05 | 21秒 | 59,482,035 | 70 | ✓ |
| chap06 | 9秒 | 22,695,327 | 36 | ✓ |
| chap07 | 6秒 | 19,242,189 | 24 | ✓ |

出力先: `{ROOT}/pdf/chapNN_gray300.pdf`。全8件終了コード 0。FR-001 合格。

## §4.2 / §4.3 chap00（run-01、2026-08-18）

### §4.2 完了確認（合格）

- 終了コード 0。`chap00_gray300.md` 19,462 bytes（>0 ✓）
- page_idx 検査: blocks=66、出現ページ15、missing={0,4,8,10,18} = 白紙位置と完全一致、extra なし → **PASS**
- 生出力 16MB。独立数式 0 件（前付けのため妥当。参考記録）

### §4.3 正規化＋機械確認（合格）

- 置換: md 52 + json 52 = 104箇所。終了コード 0
- 機械確認: md（len=9,323・許可置換52・不許可0・残存0）PASS / json（len=21,722・許可置換52・不許可0・残存0）PASS
- 出力先: `{ROOT}/mineru-full/chap00/run-01-normalized/`

## §4.2 / §4.3 chap01（run-01、2026-08-18）

### §4.2 完了確認（合格）

- 終了コード 0。`chap01_gray300.md` 206,704 bytes（>0 ✓）
- page_idx 検査: blocks=847、出現ページ79、missing={0,4,8,10,18} = 白紙位置と完全一致、extra なし → **PASS**
- 生出力 133MB。独立数式 157 件（feat-003 run-02 の実測 157 件と一致。参考記録）

### §4.3 正規化＋機械確認（結果は追記欄参照）
- 置換: md 256 + json 267 = 523箇所。終了コード 0
- 機械確認: md（len=103,566・許可置換256・不許可0・残存0）PASS / json（len=268,175・許可置換267・不許可0・残存0）PASS
- 出力先: `{ROOT}/mineru-full/chap01/run-01-normalized/`

## §4.2 / §4.3 chap02（run-01、2026-08-18）

### §4.2 完了確認（合格）

- 終了コード 0。`chap02_gray300.md` 198,762 bytes（>0 ✓）
- page_idx 検査: blocks=1016、出現ページ70/70、missing なし（白紙なしと整合）、extra なし → **PASS**
- 生出力 115MB。独立数式 300 件（参考記録）

### §4.3 正規化＋機械確認（合格）

- 置換: md 245 + json 245 = 490箇所。終了コード 0
- 機械確認: md（len=116,995・許可置換245・不許可0・残存0）PASS / json（len=316,393・許可置換245・不許可0・残存0）PASS
- 出力先: `{ROOT}/mineru-full/chap02/run-01-normalized/`

## 一時停止（2026-08-18）

- ユーザー指示により chap02 完了時点で一時停止。chap03〜07 は未着手、final（§4.4）は未構築（全8件合格が前提のため）
- 再開時は chap03 の §4.2（`{ROOT}/mineru-full/chap03/run-01`）から

## §4.2 / §4.3 chap03（run-01、2026-08-18。feat-006 の ocr_dir.py で実行）

- feat-006 の動作確認を兼ねて `uv run python scripts/ocr_dir.py {BASE}/chap03/out -o {ROOT} --overwrite-pdf` で一括実行（PDF は manifest なしのため作り直し。以後 manifest 付き）
- 結果: **PASS** pages=44 blocks=505 replaced=165+165（md 165 + json 165 = 330箇所）、所要 4分35秒、終了コード 0
- スクリプト内機械確認（ページ数・page_idx（missing ⊆ 白紙{0}）・コードポイント比較・残存0）すべて合格。出力レイアウトは feat-005 §6 と一致（`mineru-full/chap03/run-01`・`run-01.log`・`run-01-normalized`）
- 残り: chap04〜07（ユーザーが ocr_dir.py で実行可能）。final（§4.4）は全8件合格後

## カラー再切出（feat-007、2026-08-18）

- 処理済み4章に `colorize_images.py` を適用: chap00 = 3 / chap01 = 55 / chap02 = 55 / chap03 = 36 ブロック（いずれも unique 一致・終了コード 0）
- 出力先: 各章の `run-01-normalized/images/`。§4.4 前提条件のカラー再切出は chap04〜07 の OCR 完了後に同様に実施する

## §4.2 / §4.3 chap04〜07（run-01、2026-08-21。ocr_dir.py で一括実行）

- `uv run python scripts/ocr_dir.py {BASE}/chap0{4..7}/out -o {ROOT} --overwrite-pdf` を実行。全4章 **PASS**:
  - chap04: pages=48 blocks=628 replaced=149+149（4分53秒）
  - chap05: pages=70 blocks=876 replaced=387+387（6分15秒）
  - chap06: pages=36 blocks=466 replaced=52+56（3分6秒）
  - chap07: pages=24 blocks=316 replaced=7+7（2分10秒）
- スクリプト内機械確認（ページ数・page_idx（白紙位置整合）・コードポイント比較・残存0）すべて合格
- FR-002 基準4（モデル追加DLなし）: `du -sb ~/.cache` = 53,076,947,755（基準 53,086,712,269 から微減。差分 < 100MB 合格）
- カラー再切出（feat-007）: chap04 = 27 / chap05 = 41 / chap06 = 25 / chap07 = 0（図なし。設計上の正常ケース）。全件終了コード 0

## §4.4 final ディレクトリ構築（2026-08-21）

- 前提条件確認: 全8章 §4.3 合格＋カラー再切出完了（img_path ユニーク数 = images ファイル数、全章一致）✓
- `{ROOT}/final/chapNN/`（NN=00〜07）を構築。機械確認 **PASS**:
  - 全8章 × 3項目の存在 ✓ / md・content_list 計16ファイルのバイト同一（cmp）✓
  - md 参照画像 ⊆ images ✓（chap01: 53/55、chap02: 54/55、chap06: 24/25 — 差分は content_list のみ参照の画像で、基準4により images に収録済み）
  - content_list の img_path ユニーク集合 = images ファイル集合（FR-004 基準4）✓ 全8章
  - chap07 は図 0 件のため空 images/ を作成（境界条件どおり）
- 回帰テスト: 56件全 PASS（`tests/results/feat-005_test_result.txt`）
