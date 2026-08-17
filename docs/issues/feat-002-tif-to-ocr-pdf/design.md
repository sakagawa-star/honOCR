# feat-002 機能設計書: TIF → OCR用可逆PDF生成スクリプト

## 1. 対応要求マッピング

対象: `docs/issues/feat-002-tif-to-ocr-pdf/requirements.md`

| 要求ID | 設計セクション |
|---|---|
| FR-001 | §4.1 |
| FR-002 | §4.2 |
| FR-003 | §4.3 |
| FR-004 | §4.4 |

## 2. システム構成

### 追加・変更ファイル

| ファイル | 種別 | 担当内容 |
|---|---|---|
| `scripts/make_ocr_pdf.py` | 新規 | 変換スクリプト本体（CLI） |
| `tests/test_make_ocr_pdf.py` | 新規 | 自動テスト（§4.4） |
| `pyproject.toml` | 変更 | 依存追加（§6 に差分を記載） |
| `uv.lock` | 自動更新 | `uv sync` による更新 |
| `tests/results/feat-002_test_result.txt` | 新規 | テスト実行結果の保存先 |
| `docs/TECH_STACK.md` | 変更 | 導入ライブラリの反映（§11。完了ステップ8で Claude Code 本体が実施） |

### モジュール構成と依存

- `scripts/make_ocr_pdf.py`（単一モジュール）→ `PIL.Image`（読込・変換）、`img2pdf`（PDF 生成）、`argparse` / `pathlib` / `sys` / `io`（標準ライブラリ）
- `tests/test_make_ocr_pdf.py` → `scripts/make_ocr_pdf.py`（sys.path 追加で import する。§4.4）、`PIL.Image`（合成 TIF 生成）、`pypdf`（PDF 検証）
- 循環依存: なし

### ディレクトリ構成（実施後の追加分）

```
honOCR/
├── scripts/
│   └── make_ocr_pdf.py     # 新規
└── tests/
    ├── test_env.py         # 既存（feat-001）
    ├── test_make_ocr_pdf.py  # 新規
    └── results/
        └── feat-002_test_result.txt  # 新規
```

## 3. 技術スタック

- **言語**: Python 3.12（feat-001 で構築済みの uv 環境を使う）
- **追加ライブラリ**:
  - `img2pdf==0.6.3`（新規）— PNG を再圧縮せず PDF に格納する（可逆性の保証）。Pillow の PDF 保存機能を使わない理由は §9 ADR-2
  - `pillow==12.3.0`（明示化）— TIF 読込・グレースケール変換・1/2縮小。現行 uv.lock の解決版と同一
  - `pypdf==6.16.1`（dev、明示化）— テストでのページ数・フィルタ・寸法の検証。現行 uv.lock の解決版と同一

## 4. 各機能の詳細設計

### 4.1 CLI による PDF 生成（FR-001）

#### CLI 仕様

```
uv run python scripts/make_ocr_pdf.py TIF [TIF ...] -o OUTPUT.pdf [--overwrite]
```

| 引数 | 型 | 必須 | 意味 |
|---|---|---|---|
| `tifs`（位置引数、`nargs="+"`） | パス1個以上 | 必須 | 入力 TIF。**このページ順で PDF に格納する**（スクリプト内で並べ替えない。シェルのグロブ展開が辞書順を与える） |
| `-o` / `--output` | パス | 必須 | 出力 PDF パス |
| `--overwrite` | フラグ | 任意 | 出力パスが既存でも上書きする（既定は拒否） |

縮小率（1/2）と出力 DPI（300）は本ツールの仕様として定数で持つ（`REDUCE_FACTOR = 2`、`OUT_DPI = 300`）。CLI 引数にしない（§9 ADR-5）。

#### データフロー

```
TIF (mode "1"/"L"/"RGB", 3683×5806, 600dpi)
  → PIL.Image.open
  → convert("L")           # 8-bit グレースケール化（mode "L" はそのまま）
  → reduce(2)              # 2×2平均で1/2縮小 → 1842×2903（端数は切り上げ）
  → PNG bytes (dpi=(300, 300) を埋め込み)   # 中間データ、メモリ上のみ
  → img2pdf.convert([PNG bytes, ...])       # 全ページ分をまとめて1つのPDFに
  → 出力パスへ書き込み
```

- 中間 PNG は `io.BytesIO` 上で生成し、ファイルには書かない
- ページの物理寸法は PNG の dpi メタデータ（300dpi）から img2pdf が決定する: 1842px / 300dpi × 72 = 442.08pt、2903px / 300dpi × 72 = 696.72pt

#### 処理ロジック

1. 引数解析（argparse）
2. 検証フェーズ（§4.3。**1件でも不合格なら変換を開始しない**）
3. 変換フェーズ: 入力順に各 TIF を PNG bytes へ変換し、リストに蓄積する。1ページ処理するごとに標準出力へ進捗を1行出す（§8）
4. `img2pdf.convert()` で PDF bytes を生成する
5. 原子的書き込み（`write_pdf_atomic`。§7）:
   1. 出力パスの親ディレクトリを `Path.mkdir(parents=True, exist_ok=True)` で作成する
   2. 親ディレクトリ内に一時ファイルを作成し（`tempfile.NamedTemporaryFile(dir=親, suffix=".tmp", delete=False)`）、PDF bytes を書き込み、`flush()` と `os.fsync()` を行う
   3. 確定方法を `--overwrite` で分岐する:
      - `--overwrite` なし: `os.link(一時ファイル, 出力パス)` で確定する（出力パスが既存なら `FileExistsError` になる no-clobber 動作。検証フェーズ通過後に他プロセスが同名ファイルを作った競合でも上書きしない）。成功したら一時ファイルを `os.unlink` で削除する
      - `--overwrite` あり: `os.replace(一時ファイル, 出力パス)` で置換する（同一ディレクトリ内のため原子的）
   4. 手順 2〜3 で例外が発生した場合（`FileExistsError` を含む）、一時ファイルを削除してから標準エラーへメッセージ（`FileExistsError` の場合は §4.3 の「出力パス既存」と同じメッセージ）を出力し、終了コード 1 で終了する（既存の出力ファイルは変更されない）
6. 終了コード 0 で終了する

ループ終了条件: 入力ファイルリストの末尾まで（リストは有限）。

メモリ見積り: 84ページ時、PNG bytes 合計はおおよそ 300〜500MB（1ページ 4〜6MB）で、本環境の RAM 31GB に対して問題ない。ストリーミング書き込みは実装しない（§9 ADR-6）。

### 4.2 変換仕様（FR-002）

- グレースケール化: `Image.convert("L")`（Pillow の ITU-R 601-2 係数）。mode `"1"` と `"RGB"` は `"L"` へ変換、`"L"` はそのまま
- 縮小: `Image.reduce(2)`。2×2 画素の算術平均。3683（奇数）→ 1842（端の1列は1×2平均。Pillow の reduce の仕様どおり）、5806 → 2903
- PNG 保存: `img.save(buf, format="PNG", dpi=(300, 300))`。PNG は常に可逆
- PDF 格納: img2pdf は PNG の画像データを Flate のまま格納する（JPEG 化しない）

### 4.3 入力検証とエラー処理（FR-003）

検証フェーズ（変換開始前に全件を検査し、不合格を**すべて**列挙してから終了する）:

| 検査 | 不合格条件 | 動作 |
|---|---|---|
| 出力パス既存 | `--overwrite` なしで出力パスにファイルが存在 | 標準エラーへ `output exists: {path} (use --overwrite)` を出力し終了コード 1。既存ファイルは変更しない |
| 入力存在 | 入力パスが存在しない、またはファイルでない | 標準エラーへ `not found: {path}` を出力（該当全件）し終了コード 1 |
| 画像モード・デコード可否 | `with Image.open(path) as im:` で開き、mode が `"1"` / `"L"` / `"RGB"` 以外、または `im.load()`（全画素の実デコード）が失敗 | mode 不正は標準エラーへ `unsupported image: {path} (mode={mode})`、open / `load()` 失敗は `unreadable image: {path}` を出力（該当全件）し終了コード 1。`Image.open` はヘッダ識別のみで画素デコードを遅延するため、壊れた TIF を変換開始前に検出する目的で検証フェーズ内で必ず `load()` まで行う |

変換フェーズ以降の想定エラー:

| エラー | 検出方法 | 処理 |
|---|---|---|
| img2pdf の変換失敗 | 例外 | 標準エラーへ例外メッセージを出力し終了コード 1（出力ファイルは書き込まれない） |
| 出力書き込み失敗（ディスク不足を含む） | OSError | 標準エラーへ例外メッセージを出力し、一時ファイルを削除して終了コード 1（§4.1 手順5。既存の出力ファイルは不変・一時ファイルの残骸なし） |

リトライは実装しない（手動再実行で回復できるため）。

#### 境界条件

- 入力1件 → 1ページの PDF
- 白紙ページ（1-bit G4、916B）→ 全白のグレースケールページとして格納される（Flate で数 KB）
- 入力0件 → argparse（`nargs="+"`）がエラーを出し終了コード 2（argparse の既定動作のまま）
- 奇数辺 → `reduce(2)` の仕様で切り上げ（3683 → 1842）

### 4.4 自動テスト（FR-004）

`tests/test_make_ocr_pdf.py` に以下を実装する。`scripts/` は import パスに含まれないため、テストファイル冒頭で `sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))` を行い `import make_ocr_pdf` する。

フィクスチャ（`tmp_path` に Pillow で生成する合成 TIF）:

- `rgb.tif`: mode "RGB"、100×160px、`compression="tiff_lzw"`、dpi=(600, 600)
- `blank.tif`: mode "1"、60×80px、`compression="group4"`
- `rgba.tif`: mode "RGBA"、20×20px（未対応モードの代表）
- `broken.tif`: `rgb.tif` のバイト列を先頭 60% で切り詰めて別名保存したファイル（壊れた TIF の代表）

| テスト関数名 | 内容（assert する条件） |
|---|---|
| `test_convert_page_rgb` | `rgb.tif` の変換結果 PNG を Pillow で開くと mode "L"・サイズ 50×80・dpi (300, 300)（判定は各値 ±0.01 の許容誤差。PNG の解像度は整数の pixels/m で格納されるため、300dpi は往復変換で 299.9994 になる） |
| `test_convert_page_bilevel` | `blank.tif` の変換結果 PNG が mode "L"・サイズ 30×40 |
| `test_cli_creates_pdf` | `rgb.tif` と `blank.tif` の2件で main() を実行 → 戻り値 0、pypdf で開いてページ数 2、第1ページの画像 XObject の Filter に FlateDecode が含まれ DCTDecode が含まれない、第1ページの MediaBox 幅 = 50/300×72 = 12.0pt（±0.5pt） |
| `test_cli_missing_input` | 存在しないパスを指定 → main() 戻り値 1、出力 PDF が生成されない |
| `test_cli_unsupported_mode` | `rgba.tif` を指定 → main() 戻り値 1、出力 PDF が生成されない |
| `test_cli_refuses_overwrite` | 出力パスに既存ファイルを置いて `--overwrite` なし → 戻り値 1、既存ファイルの内容が不変 |
| `test_cli_overwrite_flag` | 同条件で `--overwrite` あり → 戻り値 0、PDF が生成される |
| `test_cli_truncated_tif` | `broken.tif` を指定 → 戻り値 1、出力 PDF が生成されない（変換開始前の検証フェーズで検出） |
| `test_write_atomic_no_clobber_race` | 出力パスに既存ファイルを置き、`write_pdf_atomic(pdf_bytes, output, overwrite=False)` を直接呼ぶ → `FileExistsError` が送出され、既存ファイルの内容が不変、ディレクトリに `.tmp` ファイルが残っていない（検証フェーズ後に出力が作られた競合と同じ経路の検証） |
| `test_write_atomic_failure_cleanup` | monkeypatch で `os.replace` を `OSError` 送出に差し替え、既存の出力ファイルに対し `write_pdf_atomic(pdf_bytes, output, overwrite=True)` を直接呼ぶ → `OSError` が送出され、既存ファイルの内容が不変、ディレクトリに `.tmp` ファイルが残っていない（実際の書き込み確定段階の失敗を検証） |

実行手順:

1. `uv run pytest -v > tests/results/feat-002_test_result.txt 2>&1`
2. 終了コード 0 を確認する。結果ファイルに `16 passed`（feat-001 の6件＋本案件の10件）が含まれることを確認する

## 5. 状態遷移

該当なし（GUI・ステートフル処理はない）。

## 6. ファイル・ディレクトリ設計

- スクリプト配置: `scripts/make_ocr_pdf.py`（snake_case。CLAUDE.md「コーディング規約」）
- 出力 PDF のパス・ファイル名は利用者が CLI で指定する（本スクリプトは命名規則を強制しない）
- `pyproject.toml` の差分（この2箇所のみ変更する）:

```toml
dependencies = [
    "mineru[core]==3.4.4",
    "torch==2.13.0",
    "torchvision==0.28.0",
    "img2pdf==0.6.3",
    "pillow==12.3.0",
]

[dependency-groups]
dev = [
    "pytest==9.1.1",
    "pypdf==6.16.1",
]
```

- 変更後に `uv sync` を実行する（img2pdf のみ新規取得。pillow / pypdf はロック済み版と同一のため環境の実体は変わらない）

## 7. インターフェース定義

`scripts/make_ocr_pdf.py` 内（すべて型ヒント付き）:

| 関数 | シグネチャ | 責務 |
|---|---|---|
| `convert_tif_to_png` | `(tif_path: Path) -> bytes` | 1ファイルをグレースケール・1/2縮小の PNG bytes に変換する |
| `validate_inputs` | `(tifs: list[Path], output: Path, overwrite: bool) -> list[str]` | §4.3 の検証（`im.load()` による実デコード確認を含む）を行い、エラーメッセージのリストを返す（空 = 合格） |
| `build_pdf` | `(pages: list[bytes]) -> bytes` | PNG bytes のリストから PDF bytes を生成する |
| `write_pdf_atomic` | `(pdf_bytes: bytes, output: Path, overwrite: bool) -> None` | §4.1 手順5 の原子的書き込み。一時ファイル → fsync → 確定（`overwrite=False`: `os.link` による no-clobber / `overwrite=True`: `os.replace`）。失敗時（出力既存の `FileExistsError` を含む）は一時ファイルを削除して例外を送出する |
| `parse_args` | `(argv: list[str] | None = None) -> argparse.Namespace` | CLI 引数の解析 |
| `main` | `(argv: list[str] | None = None) -> int` | 全体制御。終了コードを返す。`if __name__ == "__main__": sys.exit(main())` |

定数: `REDUCE_FACTOR: int = 2`、`OUT_DPI: int = 300`、`SUPPORTED_MODES: frozenset[str] = frozenset({"1", "L", "RGB"})`

## 8. ログ・デバッグ設計

- logging モジュールは使わない（単機能 CLI のため。§9 ADR-7）
- 進捗: 標準出力へ1ページ1行 `"[{n}/{total}] {filename} -> {width}x{height}"`（n は1始まり）
- 完了: 標準出力へ `"wrote {output} ({pages} pages, {size_mb:.1f} MB)"`
- エラー: 標準エラーへ §4.3 のメッセージ

## 9. 設計判断の記録（ADR）

| # | 採用 | 却下と理由 |
|---|---|---|
| 1 | 縮小は `Image.reduce(2)`（2×2平均） | `resize(LANCZOS)` — 2:1 の整数比縮小では面積平均が情報保存的で決定的。リンギングも生じない |
| 2 | PNG + img2pdf で PDF 化 | Pillow の `save("out.pdf")` — Pillow の PDF エンコード仕様（モードごとの圧縮方式）に依存し可逆性の保証が不明瞭。img2pdf は可逆格納が仕様として明確 |
| 3 | 章対応表を持たない（入力ファイル指定で章を表現） | スクリプト内の章マッピング — 原本TIF 84件と既存閲覧用PDF 81ページが一致せず、対応はデータ側の知識。スクリプトは汎用の変換器に徹する |
| 4 | 出力既存時は拒否、`--overwrite` で明示上書き | 無条件上書き — 生成済み OCR用PDF の誤消去を防ぐ |
| 5 | 縮小率・出力 DPI は定数（CLI 引数にしない) | `--out-dpi` 引数 — 本プロジェクトの入力は 600dpi 原稿に固定であり、可変にすると検証条件（FR-002 の受け入れ基準）が発散する。変更が必要になったら案件として扱う |
| 6 | 全ページをメモリ上で構築し、一時ファイル経由で原子的に確定（`overwrite=False` は `os.link` の no-clobber、`overwrite=True` は `os.replace`） | ストリーミング書き込み・最終パスへの直接書き込み・存在再確認後の `os.replace` — 途中失敗（ディスク不足を含む）で不完全な PDF が残る、`--overwrite` 時に既存 PDF が破損する、確認と置換の間の競合で意図せず上書きする、のそれぞれを防ぐ（Codex レビュー codex-01 指摘1・codex-02 指摘1 への対応）。`os.link` は一時ファイルと同一ディレクトリ内のため同一ファイルシステムが保証される。84ページ・500MB 以下は RAM 31GB で問題ない |
| 9 | 検証フェーズで `im.load()` による全画素デコードまで実施 | `Image.open` のみ — open はヘッダ識別中心で画素デコードが遅延されるため、壊れた TIF が検証を通過してしまう（Codex レビュー codex-01 指摘2 への対応） |
| 7 | print / stderr のみ（logging 不使用） | logging モジュール — 単機能 CLI にはレベル制御の需要がなく、pytest での出力検証も単純になる |
| 8 | pillow / pypdf を現行ロック版で明示固定 | 未記載のまま推移的依存に任せる — テスト・スクリプトが直接 import するライブラリはバージョンを宣言する（feat-001 の Codex レビュー指摘の再発防止） |

## 10. 実装・検証の実施方法

- 実装は CLAUDE.md「実装の実行方法（Sonnetサブエージェント）」に従い Sonnet サブエージェントに委任する
- 実装（`uv sync` による img2pdf 取得を含む）は、Codex レビュー収束後の人レビュー承認を得てから開始する
- 検証:
  1. `uv sync` → `uv run python -c "import img2pdf; print(img2pdf.__version__)"` が `0.6.3` を出力
  2. §4.4 のテスト全件実行と結果保存（`16 passed`）
  3. 実データ確認（a): 白紙ページ1件を含む原本TIF 4件（`page-01_1L.tif page-01_2R.tif page-02_1L.tif page-02_2R.tif`）を `/home/sakagawa/work/Pattern_Recognition_and_Machine_Learning/chap01/out/ocr/sample4.pdf` に変換し、`pdfimages -list` で FR-002 の受け入れ基準（gray / 8-bit / enc≠jpeg / 300ppi）と4ページであることを確認する（出力先ディレクトリ `ocr/` は新規作成）
  4. 実データ確認（b): 原本TIF 全84件（シェルのグロブ `page-*.tif` の辞書順）を `/home/sakagawa/work/Pattern_Recognition_and_Machine_Learning/chap01/out/ocr/all-pages.pdf` に変換し、84ページ・処理時間 10 分以内・ファイルサイズ 1GB 以下を確認・記録する
- 実データ確認で生成した PDF は削除せず残す（フェーズ3の MinerU 試行で利用できる）

## 11. 完了処理でのドキュメント更新（`docs/TECH_STACK.md`）

完了ステップ8で Claude Code 本体（サブエージェントではない）が「ライブラリ一覧」の表に次の3行を追加する:

| ライブラリ | バージョン | 用途 | 選定理由 |
|---|---|---|---|
| img2pdf | 0.6.3 | OCR用PDF生成（可逆格納） | PNG を再圧縮せず Flate のまま PDF に格納できる |
| pillow | 12.3.0 | TIF 読込・グレースケール化・1/2縮小 | mineru の推移的依存と同一版を明示固定 |
| pypdf | 6.16.1 | テストでの PDF 検証（dev 依存） | mineru の推移的依存と同一版を明示固定 |

「環境構築手順」「実行環境」の節は変更しない。
