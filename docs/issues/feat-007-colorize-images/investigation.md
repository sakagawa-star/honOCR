# feat-007 investigation: 手動テスト差し戻しの修正計画

## イテレーション1 (2026-08-18)

### 1.1 不具合の特定

- **対応する要求ID**: FR-001（カラー再切出）。ただし図の**表示サイズ**に関する要求は requirements.md に記述がなく、要求仕様作成時のヒアリング漏れに当たる（本イテレーションで FR-001 に要求を追記する）
- **対応する設計セクション**: design.md §4.1（処理フロー手順5c）・§9 ADR-4（600dpi 原寸で切り出し）
- **現在の動作**: 原本 TIF（600dpi）から原寸で切り出すため、出力画像のピクセルサイズが旧 MinerU 生成画像（200dpi 相当）の3倍になる（実測: 631×946 → 1890×2833）。Markdown の `![](images/...)` はピクセル原寸で表示されるため、VS Code プレビューで図が従来の約3倍（体感4〜5倍）の大きさに表示される
- **期待する動作**: ユーザー報告（2026-08-18 手動テスト）:「図はカラーで表示された。しかし、前回より図の大きさが4~5倍以上になっている。図が大きすぎるので小さくしてほしい」→ 表示サイズは従来（旧グレー画像）と同等とする
- **エラーメッセージ**: なし（機能不具合ではなく表示サイズの要求未定義）

### 1.2 原因分析

- **原因箇所**: `scripts/colorize_images.py` の `colorize`（crop 後に縮小せず原寸で保存）
- **原因の説明**: design.md §9 ADR-4 で「600dpi 原寸で切り出し（縮小 — カラー化が目的であり解像度を落とす理由がない）」と判断したが、Markdown プレビューがピクセル原寸で描画するという表示側の挙動を考慮していなかった
- **根本原因 or 表面的原因**: 根本原因（表示サイズの要求が仕様に存在しなかったこと）

### 1.2b 修正方式の選定

ユーザー補足（2026-08-18）:「見かけ上の大きさを変えるのでもよい」→ 2案を比較:

- **案A（採用）: 画像を既定 1/3 に縮小して保存** — 旧グレー画像と同等のピクセルサイズ（丸めで数 px の差）になり表示も従来どおり。md・content_list は無改変のまま（確認済みテキストに手を付けない方針を維持）。実装は resize 1行＋オプション追加で、テストも単純
- **案B（不採用）: md の画像参照を `<img src="..." width="NNN">` に書き換えて表示幅だけ変える** — 600dpi の解像度を保てる利点はあるが、確認済み md の書き換えロジック（参照行の正規表現置換・width の算出）が必要になり、実装・検証が複雑化する。解像度はユーザー要求に含まれておらず（要求はカラー化と表示サイズ）、必要になれば `--scale 1.0` で原寸出力できる余地を残す

### 1.3 修正内容

- **変更対象ファイル**:
  1. `docs/issues/feat-007-colorize-images/requirements.md`: FR-001 の出力仕様に「既定で切り出し結果を 1/3 に縮小して保存（200dpi 相当。旧 MinerU 生成画像と同等の表示サイズ — 丸めにより数 px（1% 以内）の差は許容）。`--scale` オプション（0 より大きい実数）で変更可（`--scale 1.0` で原寸）」を追記。受け入れ基準2を「出力ピクセルサイズ = round(bbox 換算サイズ × scale)（最小 1px）」に変更
  2. `docs/issues/feat-007-colorize-images/design.md`: 定数に `DEFAULT_SCALE = 1 / 3` を追加。CLI 表に `--scale`（float、既定 1/3、`<= 0` は検証エラー・終了コード 1）を追加。処理フロー手順5c を「crop → `--scale` ≠ 1.0 なら `Image.LANCZOS` で round(w×scale)×round(h×scale)（最小 1px）に縮小 → RGB で JPEG q95 保存」に変更。§4.2 検証に `--scale > 0` を追加。§4.3 のテスト表を更新（下記）。§9 ADR-4 を「既定 1/3 縮小（旧 MinerU 画像と同等の表示サイズ — 丸めで数 px、各辺 1% 以内の差を許容）。原寸が必要な場合は `--scale 1.0`。却下: 原寸既定 — 手動テストで表示過大の指摘（本 investigation）」に改訂
  3. `scripts/colorize_images.py`: 上記設計どおり `--scale` を実装
  4. `tests/test_colorize_images.py`: 既存の座標・サイズ検証テスト（`test_crop_color_and_size`・`test_bbox_clamp`・`test_overwrite_flag` 等、サイズを assert するもの）は `--scale 1.0` を明示して既存の期待値を維持。追加3件 — `test_scale_default`（既定で 1/3 縮小: crop (60,120)px 相当 → 出力 (20,40)px）、`test_scale_custom`（`--scale 0.5` → (30,60)px）、`test_scale_invalid`（`--scale 0` → 終了コード 1・出力なし）
- **変更しないファイル**: `scripts/ocr_dir.py` ほか既存スクリプト（colorize は独立 CLI のため影響なし）、`normalize_punct.py`・`make_ocr_pdf.py`
- **修正コード（意図伝達用）**:
  - 修正前: `tif.crop(px).convert("RGB").save(out, quality=JPEG_QUALITY)`
  - 修正後: `img = tif.crop(px); img = img.resize((max(1, round(w*scale)), max(1, round(h*scale))), Image.LANCZOS) if scale != 1.0 else img; img.convert("RGB").save(out, quality=JPEG_QUALITY)`
- **修正が設計書に沿っているか**: 設計書自体を修正する（§2.2 に従い設計変更案を上記1・2で提示）

### 1.4 影響範囲

- **他の機能への影響**: feat-005 §4.4 の final 構築（images のコピー元は `run-NN-normalized/images/` のまま。ファイル数・ファイル名は不変のため前提条件・検証手順に変更なし）。既に生成済みの4章（chap00〜03）の images/ は修正後に `--overwrite` で再生成する
- **リグレッションリスク**: 座標変換（`bbox_to_pixels`）は変更しないため切り出し領域は不変。リスクは縮小処理の丸め（最小 1px 保証で担保）と、既存テストの期待値（`--scale 1.0` 明示で維持）に限定される

### 1.5 確認方法

- **自動テスト**: 追加3件を含む全件 PASS（既存53件＋3件 = 56件）。結果を `tests/results/feat-007_test_result.txt` に上書き保存
- **手動テスト**: 修正後に chap00〜03 の images/ を `--overwrite` で再生成し、ユーザーが VS Code プレビューで「カラーのまま・従来と同等の表示サイズ」を確認する
