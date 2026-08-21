# feat-007 機能設計書: 図画像のカラー再切出スクリプト（colorize_images.py）

## 1. 対応要求マッピング

対象: `docs/issues/feat-007-colorize-images/requirements.md`

| 要求ID | 設計セクション |
|---|---|
| FR-001 | §4.1 |
| FR-002 | §4.2 |
| FR-003 | §4.3 |

## 2. システム構成

| ファイル | 種別 | 担当内容 |
|---|---|---|
| `scripts/colorize_images.py` | 新規 | カラー再切出 CLI（単一モジュール） |
| `tests/test_colorize_images.py` | 新規 | 自動テスト（§4.3） |
| `tests/results/feat-007_test_result.txt` | 新規 | テスト結果の保存先 |

`pyproject.toml` の変更なし（pillow は既存依存）。既存スクリプトの改変なし・import なし。

## 3. 技術スタック

- Python 3.12 標準ライブラリ（`argparse` / `pathlib` / `sys` / `json`）＋ pillow（TIF 読み込み・切り出し・JPEG 保存）

## 4. 各機能の詳細設計

### 定数

```python
TIF_PATTERNS = ("page-*_1L.tif", "page-*_2R.tif")  # feat-006 ocr_dir.py と同一（TIF 列の規則）
BBOX_SCALE = 1000       # bbox の正規化スケール
JPEG_QUALITY = 95
DEFAULT_SCALE = 1 / 3   # 出力縮小率の既定（600dpi → 200dpi 相当。旧 MinerU 生成画像と同等の表示サイズ。丸めで数 px の差は許容）
```

### 4.1 カラー再切出（FR-001）

#### CLI 仕様

```
uv run python scripts/colorize_images.py CONTENT_LIST TIF_DIR -o OUTDIR [--overwrite]
```

| 引数 | 型 | 必須 | 意味 |
|---|---|---|---|
| `content_list`（位置引数） | パス | 必須 | content_list の JSON |
| `tif_dir`（位置引数） | パス | 必須 | 原本 TIF のディレクトリ |
| `-o` / `--outdir` | パス | 必須 | 出力ディレクトリ（存在しなければ `parents=True` で作成） |
| `--overwrite` | フラグ | 任意 | 出力先の同名ファイルが既存でも上書きする（既定は拒否） |
| `--scale` | float | 任意 | 出力の縮小率（既定 `DEFAULT_SCALE` = 1/3）。`1.0` で原寸。`0` 以下は検証フェーズでエラー（終了コード 1） |

#### 処理フロー（`main`）

```
1. 引数解析
2. content_list 読み込み（JSON 配列）。図ブロック = img_path キーを持つ要素を抽出
3. TIF 列 = TIF_PATTERNS で列挙し辞書順 sort
4. 検証フェーズ（§4.2。`args.scale` を含めて全件検査してから終了。1件でも不合格なら切り出しを開始しない）
5. 図ブロックごとに切り出し（同一 img_path のベース名は初出のみ処理）:
   a. tif = TIF列[page_idx] を開く
   b. px = (x0/1000*W, y0/1000*H, x1/1000*W, y1/1000*H) を round で整数化し、
      [0, W]×[0, H] にクランプ
   c. img = tif.crop(px)。scale ≠ 1.0 なら Image.LANCZOS で (max(1, round(幅×scale)), max(1, round(高さ×scale))) に縮小
   d. img.convert("RGB") を OUTDIR/<img_path のベース名> に JPEG quality=95 で保存
6. サマリを標準出力へ表示: "blocks={図ブロック数} unique={生成ファイル数} outdir={OUTDIR}"、終了コード 0
```

- 同じ TIF を複数ブロックが参照する場合に備え、開いた TIF は page_idx をキーにキャッシュしてよい（機能要件ではなく実装効率。任意）
- 白紙 TIF（1-bit）も `convert("RGB")` で処理できるため特別扱いしない（実際には白紙上に図ブロックは出現しない想定）

### 4.2 入力検証とエラー処理（FR-002）

検証フェーズ（全件検査してから終了。エラーはすべて標準エラーへ、終了コード 1）:

| 検査 | 不合格条件 |
|---|---|
| content_list | パスが存在しない・ファイルでない・JSON として読めない・配列でない |
| TIF ディレクトリ | 存在しない・TIF 列が 0 件 |
| 各図ブロックの page_idx | 整数でない・`0 <= page_idx < len(TIF列)` の範囲外 |
| 各図ブロックの bbox | 欠落・長さ4でない・数値でない・`x0 >= x1` または `y0 >= y1`・値が 0–1000 の範囲外 |
| 出力先の既存 | `--overwrite` なしで OUTDIR に同名ファイルが存在（該当全件を報告） |
| `--scale` | 値が 0 以下・NaN・inf のいずれか |

切り出しフェーズのエラー（TIF が開けない・保存失敗）: 該当ファイルと例外メッセージを標準エラーへ出力し、終了コード 1（部分出力が残ることは許容し、メッセージで明示する）。

境界条件:

- 図ブロック 0 件 → `"blocks=0 unique=0"` を表示して終了コード 0（FR-001 基準4）
- bbox がページ境界と接する（0 や 1000）→ クランプにより正常処理

### 4.3 自動テスト（FR-003）

`tests/test_colorize_images.py`。`sys.path` への `scripts/` 追加は既存テストと同じ方式。フィクスチャは `tmp_path` に生成する（例: 100×160px の RGB 画像を `page-01_1L.tif`・`page-01_2R.tif` として保存し、対応する content_list JSON を書く）。

| テスト関数名 | 内容（assert する条件） |
|---|---|
| `test_crop_color_and_size` | `--scale 1.0` 指定。bbox=[100,125,600,875] → 出力が RGB・(50,120)px（100×160 の TIF に対し round((600-100)/1000*100)=50 等）で、元画像の該当領域と**許容誤差付きで**一致（JPEG は非可逆のため完全一致は要求しない。各画素の平均絶対誤差 ≤ 3 を合格とする） |
| `test_scale_default` | `--scale` 未指定（既定 1/3）。crop が (60,120)px 相当の bbox → 出力 (20,40)px |
| `test_scale_custom` | `--scale 0.5`。同 bbox → 出力 (30,60)px |
| `test_scale_invalid` | `--scale 0` → 終了コード 1・出力なし |
| `test_bbox_clamp` | bbox=[0,0,1000,1000] → TIF 全面。境界でエラーにならない |
| `test_duplicate_img_path` | 同じ img_path を持つブロック2件 → 出力1ファイル・unique=1 |
| `test_no_image_blocks` | 図ブロック 0 件の content_list → 終了コード 0・"blocks=0" |
| `test_missing_content_list` | 不存在パス → 終了コード 1 |
| `test_invalid_json` | JSON でないファイル → 終了コード 1 |
| `test_empty_tif_dir` | TIF 0 件のディレクトリ → 終了コード 1 |
| `test_page_idx_out_of_range` | page_idx = len(TIF列) → 終了コード 1・出力なし |
| `test_bad_bbox` | bbox 長さ3 / x0>=x1 / 値が1001 の3系 → いずれも終了コード 1・出力なし |
| `test_refuses_overwrite` | 出力先に既存ファイル・`--overwrite` なし → 終了コード 1・既存不変 |
| `test_overwrite_flag` | 同条件で `--overwrite` → 終了コード 0・上書きされる |
| `test_inputs_unchanged` | 実行後、TIF・content_list の内容が実行前と同一 |

実行手順: `uv run pytest -v > tests/results/feat-007_test_result.txt 2>&1` → 全件 PASS（既存41件＋本案件15件 = 56件）を確認する。

## 5. 状態遷移

該当なし。

## 6. ファイル・ディレクトリ設計

- 出力先は呼び出し側が指定する。**推奨運用**（本案件の動作確認と今後の標準）: `{ROOT}/mineru-full/<name>/run-NN-normalized/images/` に出力する。md と同じディレクトリに `images/` が置かれるため、VS Code プレビューで図がカラー表示され、feat-005 §4.4 の final 構築時にも「正規化済みディレクトリ一式」をコピーすれば揃う
- feat-005 の final 構築（未実施）では、images のコピー元を「`run-NN-normalized/images/`（本スクリプトの出力）」とする。**feat-005 の requirements.md FR-004（入力・受け入れ基準）と design.md §4.4（前提条件・コピー表）は本案件で修正済み**（2026-08-18。final 構築の前提に「各章でカラー再切出済み（`img_path` ユニーク数 = images/ ファイル数）」を追加）。feat-005 側の Codex セッションで差分再レビューを行う

## 7. インターフェース定義

`scripts/colorize_images.py` 内（すべて型ヒント付き）:

| 関数 | シグネチャ | 責務 |
|---|---|---|
| `load_image_blocks` | `(content_list: Path) -> list[dict]` | JSON 読み込みと図ブロック（img_path 保持要素）の抽出 |
| `list_tifs` | `(d: Path) -> list[Path]` | TIF 列の辞書順列挙（TIF_PATTERNS） |
| `validate` | `(blocks: list[dict], tifs: list[Path], outdir: Path, overwrite: bool, scale: float) -> list[str]` | §4.2 の検証（`--scale` の検証を含む）。エラーメッセージのリストを返す（空 = 合格） |
| `bbox_to_pixels` | `(bbox: list[float], size: tuple[int, int]) -> tuple[int, int, int, int]` | 0–1000 正規化 → ピクセル座標（round＋クランプ） |
| `colorize` | `(blocks: list[dict], tifs: list[Path], outdir: Path, scale: float = DEFAULT_SCALE) -> int` | 切り出し・縮小・保存。生成ファイル数を返す |
| `parse_args` | `(argv: list[str] \| None = None) -> argparse.Namespace` | CLI 引数の解析 |
| `main` | `(argv: list[str] \| None = None) -> int` | 全体制御。終了コードを返す |

## 8. ログ・デバッグ設計

- logging モジュールは使わない（既存スクリプトと同じ方針）。進捗・サマリは標準出力、エラーは標準エラー

## 9. 設計判断の記録（ADR）

| # | 採用 | 却下と理由 |
|---|---|---|
| 1 | 原本 TIF からの再切出（テキスト不変） | カラー PDF での MinerU 再実行 — 確認済みテキストが再生成され確認をやり直しになる。ユーザーが案A を選択（2026-08-18） |
| 2 | 対象は content_list の `img_path` 保持ブロック全件（image/chart/table） | md 参照分のみ — content_list（final に含める成果物）も img_path を参照しており、両方の参照を満たすには全件が必要。`images/` 内の非参照157ファイルは対象外（どこからも参照されない中間生成物） |
| 3 | 出力ファイル名は img_path のベース名と同一 | 新名称＋md 書き換え — 確認済み md・content_list への変更は避ける。同名差し替えなら参照がそのまま生きる |
| 4 | 既定で 1/3 に縮小して保存（`--scale` で変更可）、JPEG quality 95 | 600dpi 原寸既定 — 手動テストで「図が大きすぎる」と指摘（investigation.md イテレーション1。md はピクセル原寸で表示されるため）。1/3 で旧 MinerU 画像と同等の表示サイズ（丸めで数 px、各辺 1% 以内の差を許容）になる。md の `<img width>` 書き換えで見かけだけ変える案 — 確認済み md への変更と書き換えロジックが必要になり不採用（investigation.md §1.2b）。原寸が必要なら `--scale 1.0`。PNG — 容量過大のため不採用 |
| 5 | bbox 異常・page_idx 範囲外は全体を終了コード 1 で失敗させる | 該当ブロックのスキップ続行 — 座標系の前提（0–1000 正規化）が崩れている兆候であり、静かに欠けた出力を作るより失敗が安全 |
| 6 | TIF 列の規則は feat-006 と同一の固定2パターン（オプションなし） | `--glob` の提供 — page_idx との対応は feat-005/006 の列挙規則で検証済み。規則を変えられると対応が壊れる |

## 10. 実装・検証の実施方法

- 手順: Codex レビュー収束 → 人レビュー承認 → 実装（**Sonnet サブエージェント委任**: スクリプト＋テスト＋テスト実行）→ 動作確認 → 完了処理
- 動作確認（実装後、Claude Code 本体が実施。GPU 不要）: 処理済みの各章（chap00〜03）について `uv run python scripts/colorize_images.py {ROOT}/mineru-full/chapNN/run-01-normalized/chapNN_gray300_content_list.json {BASE}/chapNN/out -o {ROOT}/mineru-full/chapNN/run-01-normalized/images --overwrite` を実行する（**`--overwrite` 必須** — イテレーション1以前の原寸画像が既に存在するため）。各章で「ブロック数 = 生成数・終了コード 0」と、サンプル画像（README の検証で使った写真ブロック）が「カラーかつ出力サイズ = round(600dpi 切出サイズ × 1/3)（サンプルでは 630×944）で、旧グレー画像（631×946）との差が各辺 1% 以内」であることを確認する。結果は本案件 README に追記する
- 手動テスト（ステップ7）: ユーザーが VS Code プレビューで chap01 の md を開き、図が**カラーで表示され、かつ旧グレー画像と同等の表示サイズ**であることを確認する

## 11. 完了処理でのドキュメント更新

- `docs/TECH_STACK.md`: 変更なし（ライブラリ追加がない）
- `CLAUDE.md`: ディレクトリ構成に `scripts/colorize_images.py`・`tests/test_colorize_images.py` を追記する。「ドメイン知識」に bbox の座標系（0–1000 正規化）とカラー再切出コマンドの1行例を追記する
- feat-005 requirements.md FR-004 / design.md §4.4: images のコピー元変更とカラー再切出の前提条件追加は反映済み（§6 のとおり）。完了処理での追加作業はなし
- `docs/BACKLOG.md` / `docs/CHANGELOG.md`: 完了時に更新
