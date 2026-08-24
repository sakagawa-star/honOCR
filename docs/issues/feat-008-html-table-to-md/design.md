# feat-008 機能設計書: MinerU 出力の HTML 表を Markdown パイプテーブルに変換

## 1. 対応要求マッピング

| 要求ID | 設計セクション |
|---|---|
| FR-001 HTML 表変換スクリプト | §4.1 |
| FR-002 入力検証とエラー処理 | §4.2 |
| FR-003 ocr_dir.py への組み込み | §4.3 |
| FR-004 自動テスト | §4.4 |
| FR-005 既存の最終成果物への適用と normalized md の復旧 | §4.5 |

用語は `requirements.md` §2 に従う。

## 2. システム構成

```
scripts/
├── html_table_to_md.py   # 新規: HTML 表 → パイプテーブル変換 CLI（FR-001, FR-002）
├── normalize_punct.py    # 既存: validate_inputs / write_text_atomic を import して再利用
└── ocr_dir.py            # 変更: 機械確認合格後に html_table_to_md.py を subprocess 実行（FR-003）
tests/
├── test_html_table_to_md.py  # 新規（FR-004）
├── test_ocr_dir.py           # 追記（FR-004）
└── results/feat-008_test_result.txt
```

依存関係: `html_table_to_md.py` → `normalize_punct.py`（関数 import）。`ocr_dir.py` → `html_table_to_md.py`（subprocess、既存の `normalize_punct.py` 呼び出しと同方式）。循環なし。`html_table_to_md.py` を `uv run python scripts/html_table_to_md.py` で実行した場合、`sys.path[0]` がスクリプトのディレクトリになるため `import normalize_punct` は追加設定なしで解決する（テストは既存テストと同じく `sys.path.insert(0, scripts)` を行う）。

## 3. 技術スタック

- Python 3.12.3 / uv（`docs/TECH_STACK.md` と同一）
- 標準ライブラリのみ: `argparse`, `re`, `html`（`html.unescape` のみ使用）, `sys`, `pathlib`
- pytest 9.1.1（既存 dev 依存）。ライブラリの追加・変更はなく `docs/TECH_STACK.md` の更新は不要

## 4. 各機能の詳細設計

### 4.1 HTML 表変換スクリプト（FR-001）

#### CLI 仕様

```
uv run python scripts/html_table_to_md.py FILE [FILE ...] -o OUTDIR [--overwrite]
```

| 引数 | 型 | 必須 | 意味 |
|---|---|---|---|
| `FILE` | Path（1 個以上） | 必須 | 入力 Markdown（UTF-8） |
| `-o` / `--outdir` | Path | 必須 | 出力ディレクトリ（入力と同じベース名で書き出す。存在しなければ作成） |
| `--overwrite` | flag | 任意 | 出力先の同名ファイルが既存でも上書きする（既定は拒否）。入力と同じディレクトリを `-o` に指定すればインプレース変換になる |

終了コード: 0 = 全ファイル書き出し成功（スキップの有無は問わない）、1 = 入力検証エラーまたは書き込み失敗。`normalize_punct.py` と同一。

標準出力（ファイルごとに 1 行、最後に合計 1 行。書式は固定。§4.3 で ocr_dir.py がパースする）:

```
chap01_gray300.md: 2 converted, 0 skipped
total: 2 converted, 0 skipped in 1 files
```

標準エラー（スキップした表ごとに 1 行）: `{ベース名}:{行番号(1 始まり)}: skipped ({理由})`。理由は §4.1「処理ロジック — `convert_table`」の理由文字列。

#### データフロー

- 入力: Markdown テキスト（`str`。`Path.read_bytes().decode("utf-8")` で読み込む。`Path.read_text` は `\r\n` / `\r` を `\n` に変換するため使わない。行分割は `text.split("\n")` のみで行い（`splitlines` は `\x0c` 等でも分割するため使わない）、各要素の末尾の `\r` は改行の一部として保持する）
- 中間: 表行ごとに `list[list[str]]`（行 × 列のセルテキスト）
- 出力: 変換済みテキスト（`str`。`"\n".join(out)` で再結合するため、表行以外の行は改行コードを含めてバイト不変）。変換された表行はパイプテーブル（各行末は元の表行と同じ `\r` の有無。元の表行がファイル末尾で改行なしの場合は最終行のみ改行なし）に置換される

#### 処理ロジック

**`convert_table(table_html: str) -> tuple[list[str], str | None]`** — 1 個の HTML 表文字列（表行の `strip()` 結果）をパイプテーブル行のリストに変換する。引数名を `html` にしてはならない（標準ライブラリモジュール `html` を関数内で隠蔽し `html.unescape` が `AttributeError` になるため。Sonnet 実装時検出 2026-08-24）。戻り値は `(lines, None)`（成功。`lines` は改行を含まない行のリスト）または `([], reason)`（スキップ。`reason` は下記の理由文字列）。

1. `re.split(r"(</?(?:table|thead|tbody|tr|td|th)\b[^>]*>)", table_html, flags=re.IGNORECASE)` で表タグとテキストに分割する（奇数インデックスが表タグ、偶数インデックスがテキスト）。表タグ以外の `<`（数式中の不等号、未知タグ）はテキスト側に残る
2. 状態: `rows: list[list[str]] = []`、`current_row: list[str] | None = None`、`cell: list[str] | None = None`（セル内テキストの断片リスト。`None` = セル外）
3. 各表タグ断片について `re.fullmatch(r"<(/?)([A-Za-z]+)([^>]*)>", tag)` を適用する（手順 1 の分割規則により必ずマッチする）
   - `group(3).strip() != ""`（属性あり。`colspan` `rowspan` `style` を含む）→ `([], "attribute on <名前>")`（名前は小文字）
   - タグ名を小文字にして判定。`table` `thead` `tbody` は無視（開閉とも何もしない）。`tr` 開始 → `current_row = []`、`tr` 終了 → `rows.append(current_row)`; `current_row = None`。`td` / `th` 開始 → `cell = []`、終了 → セルテキスト `s = html.unescape("".join(cell)).strip()` を求め、`re.search(r"</?[A-Za-z]+(\s[^<>]*)?>", s)` にマッチする（表タグ以外の HTML タグ形式。`<br>` `<b>` `<sup>` `<span class="x">` を含む）→ `([], "unsupported tag in cell")`、マッチしなければ `current_row.append(s)`; `cell = None`
   - `td` / `th` 開始時に `current_row is None`、または `tr` 終了時に `current_row is None`、または `td` / `th` 終了時に `cell is None` → `([], "malformed structure")`
4. 各テキスト断片について: `cell is not None` なら `cell.append(text)`。`cell is None` かつ `text.strip() != ""` → `([], "text outside cell")`
5. 分割の走査終了後、`current_row is not None` または `cell is not None` → `([], "malformed structure")`
6. `len(rows) == 0` → `([], "no rows")`。列数 `n = len(rows[0])`。`n == 0` → `([], "no columns")`。いずれかの行で `len(row) != n` → `([], "ragged rows")`
7. いずれかのセルに `|` が含まれる → `([], "pipe in cell")`
8. 出力行を組み立てる: 各行を `"| " + " | ".join(cells) + " |"` とする（空セルは空文字列のまま。例: `|  | $M = 0$ |`）。1 行目 = `rows[0]`、2 行目 = `"|" + " --- |" * n`、3 行目以降 = `rows[1:]`。`(lines, None)` を返す

`$a<b$` のようにセル内に表タグ以外の `<` がある場合、手順 1 の分割ではテキスト側に残るため、セルテキスト `$a<b$` としてそのまま保持される（数式中の不等号を含む表も変換できる）。`$a<b$ と $c>d$` のように `<` と `>` が同一セルにある場合も、手順 3 の HTML タグ形式（タグ名の直後は空白か `>` のみ）には一致しないため保持される。

**`convert_text(text: str, name: str) -> tuple[str, int, int, list[str]]`** — Markdown 全文を変換する。戻り値は `(変換後テキスト, 変換件数, スキップ件数, 警告メッセージのリスト)`。

1. `lines = text.split("\n")`（ファイル末尾が `\n` なら最後の要素は `""`。各要素は改行 `\n` を含まず、CRLF ファイルでは末尾に `\r` を持つ）。出力行リスト `out: list[str] = []`
2. 各行 `line`（インデックス `i`、行番号 `i + 1`）について:
   - `body = line.rstrip("\r")`、`cr = line[len(body):]`（`""` または `"\r"`）、`stripped = body.strip()`。`stripped.startswith("<table") and stripped.endswith("</table>")` なら表行
   - 表行なら `convert_table(stripped)` を呼ぶ。スキップなら `out.append(line)`、スキップ件数 +1、警告 `f"{name}:{i + 1}: skipped ({reason})"` を追加。成功なら (a) `out` が空でなく `out[-1].strip() != ""` のとき `out.append(cr)` を挿入（空行）、(b) 各パイプテーブル行 `l` について `out.append(l + cr)`、(c) 次の行 `lines[i + 1]` が存在しその `strip() != ""` のとき `out.append(cr)` を挿入、変換件数 +1
   - 表行でなく `"<table" in line` の場合（複数行にまたがる HTML 表）: `out.append(line)`、スキップ件数 +1、警告 `f"{name}:{i + 1}: skipped (multi-line table)"`。以降の行は通常行として扱う（`</table>` の探索はしない）
   - それ以外: `out.append(line)`
3. `"\n".join(out)` を返す（表行以外の要素は無改変で再結合されるため、LF / CRLF / 末尾改行の有無がバイト単位で保存される）

**`main(argv) -> int`** — `normalize_punct.main` と同じ構造。`validate_inputs` → 各ファイルを `convert_text` → `write_text_atomic` → 標準出力に件数。警告は `write_text_atomic` の前に標準エラーへ出力する。書き込み失敗（例外）は `str(exc)` を標準エラーに出力して 1 を返す。

#### 境界条件

- 表行 0 件のファイル: 内容不変（バイト同一）で出力し `0 converted, 0 skipped`
- 空ファイル: 空ファイルを出力し `0 converted, 0 skipped`
- 表が 1 行（ヘッダ行のみ）: パイプテーブル 2 行（ヘッダ + 区切り）を出力する
- ファイル末尾の表行に改行がない: パイプテーブルの最終行も改行なし
- CRLF ファイル: 表行以外はバイト不変。パイプテーブルの各行末も `\r\n`
- 表行の前後に空行がある（MinerU 出力の通常形）: 空行の挿入は行わない（前後の行はバイト不変）

### 4.2 入力検証とエラー処理（FR-002）

`normalize_punct.validate_inputs(files, outdir, overwrite)` と `normalize_punct.write_text_atomic(text, output, overwrite)` をそのまま使う（feat-004 design.md §4.2 と同一の検証: 存在確認・UTF-8 デコード・ベース名重複・出力既存。`validate_inputs` 内の `read_text` は UTF-8 判定にのみ使われ、本文の読み込みは §4.1 のとおり `read_bytes().decode("utf-8")` で別途行う）。インプレース変換（入力 = 出力パス、`--overwrite` 指定）は `write_text_atomic` が一時ファイル → `os.replace` で確定するため、入力の読み込み（変換前に完了している）と競合しない。

想定エラーと処理（すべて標準エラーにメッセージ、終了コード 1）:

| エラー | 検出 | 処理 |
|---|---|---|
| 入力ファイルなし | `validate_inputs` | 変換開始前に終了 |
| UTF-8 でない | `validate_inputs` | 変換開始前に終了 |
| ベース名重複 | `validate_inputs` | 変換開始前に終了 |
| 出力既存（`--overwrite` なし） | `validate_inputs` | 変換開始前に終了、既存ファイル不変 |
| 書き込み失敗（権限・ディスク） | `write_text_atomic` の例外 | 一時ファイル削除後に終了。処理済みの先行ファイルは残す |

### 4.3 ocr_dir.py への組み込み（FR-003）

変更箇所は `process_dir` の末尾（`machine_errors` 判定の後、`完了: PASS` 出力の前）、新規 helper 2 関数、`DirResult`、サマリ出力の 4 点。

1. `DirResult` にフィールド `tables: int = 0`、`tables_skipped: int = 0` を追加する（末尾に既定値付きで追加。既存の `_fail` 呼び出しは変更不要）
2. **`parse_table_summary(stdout: str) -> tuple[int, int] | None`**（新規関数。テスト対象）: `re.search(r"^total: (\d+) converted, (\d+) skipped in \d+ files$", stdout, re.MULTILINE)` でマッチした 2 整数を返す。マッチしない場合は `None` を返す
3. **`convert_tables(normalized_md: Path, normalized_dir: Path) -> tuple[list[str], int, int]`**（新規関数。テスト対象。戻り値は `(エラーメッセージのリスト, 変換件数, スキップ件数)`。エラーリストが空 = 成功）:
   ```
   cmd = [sys.executable, str(SCRIPTS_DIR / "html_table_to_md.py"),
          str(normalized_md), "-o", str(normalized_dir), "--overwrite"]
   proc = subprocess.run(cmd, capture_output=True, text=True)
   ```
   - `proc.returncode != 0` → `([f"HTML表変換失敗: {proc.stderr.strip()}"], 0, 0)`
   - `proc.returncode == 0` かつ `parse_table_summary(proc.stdout) is None` → `([f"HTML表変換失敗: summary parse failed: {proc.stdout.strip()}"], 0, 0)`
   - それ以外 → `proc.stderr.strip()` が空でなければその内容を標準エラーにそのまま出力し（スキップ警告。FAIL にはしない）、`([], tables, tables_skipped)` を返す
4. `process_dir` で `machine_errors` が空のとき（= `if machine_errors: return _fail(...)` の直後）、`print(f"[{name}] HTML表変換中...")` の後に `table_errors, tables, tables_skipped = convert_tables(normalized_md, normalized_dir)` を呼ぶ。`table_errors` が空でなければ `_fail(name, table_errors, start, pages=page_count, blocks=blocks, replaced_md=replaced_md, replaced_json=replaced_json)` を返す。空なら成功時の `DirResult` に `tables=tables, tables_skipped=tables_skipped` を渡す
5. `main` のサマリ PASS 行を `f"{r.name}: PASS pages={r.pages} blocks={r.blocks} replaced={r.replaced_md}+{r.replaced_json} tables={r.tables}+{r.tables_skipped}skipped ({minutes}分{seconds}秒)"` に変更する

変換は正規化済み md（`normalized_md`）のみに適用する。`normalized_content_list` は無改変。機械確認（`check_normalized`）は変換前に完了しているため、変換によって「正規化前後のコードポイント比較」が崩れることはない。

### 4.4 自動テスト（FR-004）

`tests/test_html_table_to_md.py`（新規。既存テストと同じく `sys.path.insert(0, scripts)` 後に `import html_table_to_md`）:

| テスト | 内容 |
|---|---|
| `test_convert_table_simple` | `<table><tr><td>a</td><td>b</td></tr><tr><td>1</td><td>2</td></tr></table>` → `["| a | b |", "| --- | --- |", "| 1 | 2 |"]`, reason None |
| `test_convert_table_math_and_empty` | `<table><tr><td></td><td> $M = 0$ </td></tr><tr><td> $w_{0}^{*}$ </td><td>0.19</td></tr></table>` → 1 行目 `|  | $M = 0$ |`、3 行目 `| $w_{0}^{*}$ | 0.19 |` |
| `test_convert_table_th_thead_tbody` | `th` `thead` `tbody` を含む表が変換される |
| `test_convert_table_entities` | `&lt;` `&amp;` がセルで `<` `&` に復元される |
| `test_convert_table_ragged` | 列数不一致 → `([], "ragged rows")` |
| `test_convert_table_attribute` | `<td colspan="2">` → reason が `attribute on <td>` |
| `test_convert_table_unsupported_tag` | `<td>a<br>b</td>` → reason が `unsupported tag in cell` |
| `test_convert_table_pipe` | セルに `|` → `([], "pipe in cell")` |
| `test_convert_table_lt_in_math` | `<td>$a<b$</td><td>$c>d$</td>` → reason None、セルが `$a<b$`・`$c>d$` のまま保持される |
| `test_convert_table_text_outside_cell` | `<table><tr>x<td>a</td></tr></table>` → `([], "text outside cell")` |
| `test_convert_table_no_rows` | `<table></table>` → `([], "no rows")` |
| `test_convert_text_replaces_line` | 空行・表行・空行・本文 のテキストで、表行のみパイプテーブルに置換され他はバイト不変、件数 (1, 0) |
| `test_convert_text_inserts_blank_lines` | 本文・表行・本文（空行なし）で、表の前後に空行が挿入される |
| `test_convert_text_skip_keeps_line` | 単純表でない表行が不変で残り、警告に行番号と理由が含まれ、件数 (0, 1) |
| `test_convert_text_multiline_table` | `<table>` と `</table>` が別行 → 不変・警告 `multi-line table` |
| `test_convert_text_no_tables` | 表なし → バイト同一、(0, 0) |
| `test_convert_text_eof_without_newline` | 末尾改行なしの表行 → 出力最終行も改行なし |
| `test_convert_text_crlf_no_tables` | CRLF・表なし → バイト同一 |
| `test_convert_text_crlf_with_table` | CRLF・表あり → 表行以外バイト不変、パイプテーブル各行末が `\r\n` |
| `test_cli_writes_output` | `main([src, "-o", outdir])` が 0 を返し出力に `| --- |` 行がある。入力不変 |
| `test_cli_inplace_overwrite` | `-o` に入力ディレクトリ、`--overwrite` で 0、入力が変換済みになる |
| `test_cli_output_exists_without_overwrite` | 既存出力 → 1、既存ファイル不変 |
| `test_cli_missing_input` | → 1 |

`tests/test_ocr_dir.py` に追記:

| テスト | 内容 |
|---|---|
| `test_parse_table_summary` | `"x.md: 2 converted, 1 skipped\ntotal: 2 converted, 1 skipped in 1 files\n"` → `(2, 1)` |
| `test_parse_table_summary_no_match` | `""` → `None` |
| `test_convert_tables_success` | `monkeypatch.setattr(ocr_dir.subprocess, "run", stub)` で returncode 0・stdout に合計行（2, 0）・stderr 空 を返す stub → `([], 2, 0)`。stub が受け取った `cmd` に `html_table_to_md.py`・`--overwrite`・md パスが含まれる |
| `test_convert_tables_nonzero_fail` | returncode 1・stderr `"boom"` → エラー 1 件（`HTML表変換失敗: boom`） |
| `test_convert_tables_summary_missing_fail` | returncode 0・stdout `""` → エラー 1 件（`summary parse failed` を含む） |
| `test_convert_tables_warning_passes` | returncode 0・合計行（1, 1）・stderr `"x.md:3: skipped (ragged rows)"` → `([], 1, 1)`、`capsys` の err にその警告が含まれる |

「機械確認が合格したディレクトリでのみ変換する」は `process_dir` 内の呼び出し位置（`if machine_errors: return _fail(...)` の後）で構造的に保証する（`process_dir` の end-to-end テストは MinerU 実行を伴うため既存どおり行わない）。

実行: `uv run pytest -v > tests/results/feat-008_test_result.txt 2>&1`（全件 PASS。既存 56 件 + 新規 29 件 = 85 件）。

### 4.5 既存の最終成果物への適用と normalized md の復旧（FR-005）

実装完了後、Sonnet サブエージェントが次の順で実行し、結果を報告する（すべて `uv run` 経由、パスは `{BASE}` 展開済みの絶対パスで指定）。

**実施状況（2026-08-24）**: 手順 1〜2 と手順 3 (a)(b)(d) は初回実装時に完了済み（chap01 = 2 converted / chap06 = 1 converted、スキップ 0、`<table` 行 0、sha256 不変）。手順 3 (c) で run-01-normalized 側の損傷（案件 README「実装中の発見」）が発覚したため、以降は手順 3.5（復旧）を追加した本改訂版に従って再開する。

1. 適用前の記録: 4 ファイルの `<table` を含む行数（`grep -c "<table"`。期待: chap01 = 2、chap06 = 1）と、`final/chap01/`・`final/chap06/` の content_list.json と `images/` 全ファイルの `sha256sum` を記録する
2. 変換（各ファイルをインプレース）:
   ```
   uv run python scripts/html_table_to_md.py {BASE}/ocr/final/chap01/chap01_gray300.md -o {BASE}/ocr/final/chap01 --overwrite
   uv run python scripts/html_table_to_md.py {BASE}/ocr/final/chap06/chap06_gray300.md -o {BASE}/ocr/final/chap06 --overwrite
   uv run python scripts/html_table_to_md.py {BASE}/ocr/mineru-full/chap01/run-01-normalized/chap01_gray300.md -o {BASE}/ocr/mineru-full/chap01/run-01-normalized --overwrite
   uv run python scripts/html_table_to_md.py {BASE}/ocr/mineru-full/chap06/run-01-normalized/chap06_gray300.md -o {BASE}/ocr/mineru-full/chap06/run-01-normalized --overwrite
   ```
   期待出力: chap01 = `2 converted, 0 skipped`、chap06 = `1 converted, 0 skipped`、終了コード 0、標準エラー出力なし
3. 適用後の確認: (a) 4 ファイルの `<table` 行数が 0、(b) `| --- |` を含む行数が chap01 = 2、chap06 = 1、(d) 手順 1 の `sha256sum` が不変、(e) `diff` で変更行が表行とその置換行のみであること（`diff <(git 管理外のため適用前コピー) 適用後` を使う。適用前に手順 1 で 4 ファイルをスクラッチディレクトリにコピーしておく）。※旧 (c)（final と normalized の cmp）は手順 3.5 の後に (f) として行う
3.5. run-01-normalized の md 復旧（損傷 2 件。final が正であることは案件 README の調査で確認済み）:
   ```
   cp {BASE}/ocr/final/chap06/chap06_gray300.md {BASE}/ocr/mineru-full/chap06/run-01-normalized/chap06_gray300.md
   cp {BASE}/ocr/final/chap07/chap07_gray300.md {BASE}/ocr/mineru-full/chap07/run-01-normalized/chap07_gray300.md
   ```
   （chap06 のコピー元は手順 2 で変換済みの final。復旧と変換適用を同時に満たす。chap07 は表 0 件のため変換不要でコピーのみ）
   検証: (f) 全8章で `cmp {BASE}/ocr/final/chapNN/chapNN_gray300.md {BASE}/ocr/mineru-full/chapNN/run-01-normalized/chapNN_gray300.md` が一致、(g) 全8章の final・run-01-normalized の md 計16ファイルで `grep -c "<table"` が 0（一致済みの他章も含めて網羅確認）、(h) 復旧した chap07 の md が生出力の正規化結果と一致（`diff <(sed 's/、/，/g; s/。/．/g' {BASE}/ocr/mineru-full/chap07/run-01/chap07_gray300/hybrid_auto/chap07_gray300.md) {BASE}/ocr/mineru-full/chap07/run-01-normalized/chap07_gray300.md` が無差分）
4. ユーザー手動テスト: VS Code で `{BASE}/ocr/final/chap01/chap01_gray300.md` をプレビューし、表 1.1 / 1.2 のセル内数式が描画されることを確認する

## 5. 状態遷移

該当なし（バッチ処理）。

## 6. ファイル・ディレクトリ設計

- 入力: 任意パスの Markdown（UTF-8）。出力: `OUTDIR/{入力のベース名}`。命名規則は `normalize_punct.py` と同一
- 設定ファイル: なし
- `ocr_dir.py` の出力レイアウト（feat-006 design.md §6）は変更なし。正規化済み md がインプレースで変換されるだけ

## 7. インターフェース定義

`scripts/html_table_to_md.py`:

```python
def convert_table(table_html: str) -> tuple[list[str], str | None]: ...
def convert_text(text: str, name: str) -> tuple[str, int, int, list[str]]: ...
def parse_args(argv: list[str] | None = None) -> argparse.Namespace: ...
def main(argv: list[str] | None = None) -> int: ...
```

`scripts/ocr_dir.py`（追加）:

```python
def parse_table_summary(stdout: str) -> tuple[int, int] | None: ...
def convert_tables(normalized_md: Path, normalized_dir: Path) -> tuple[list[str], int, int]: ...
```

`DirResult` に `tables: int = 0`、`tables_skipped: int = 0` を追加。

## 8. ログ・デバッグ設計

`logging` は使わない（既存スクリプトと同様に `print`）。標準出力 = 件数（機械可読・固定書式）、標準エラー = 警告とエラー。`ocr_dir.py` の進捗行 `[{name}] HTML表変換中...` を追加する。

## 9. 設計判断の記録（ADR）

- **採用: 表タグ（6 種）だけを正規表現で分割し、それ以外の `<` はテキストとして保持する厳格パーサ** / 却下: `html.parser.HTMLParser`、および `<[^>]*>` を一律タグ扱いする方式。理由: 寛容なパーサは `$a<b$` の `<b` を `<b>` タグ開始として吸収し、数式を壊した表を「成功」として出力し得る。一律タグ扱いは不等号入り数式の表を変換できない（Codex 指摘・中）。本設計は表タグ以外の HTML タグ形式・属性・不正構造をすべてスキップにし、数式中の不等号は保持する（忠実性優先）
- **採用: 本文は `read_bytes().decode("utf-8")` で読み、`split("\n")` / `"\n".join` で行処理** / 却下: `read_text` + `splitlines`。理由: `read_text` は改行コードを `\n` に変換し「表行以外はバイト不変」を満たせない（Codex 指摘・高）。`splitlines` は `\x0c` 等でも分割する
- **採用: 変換スクリプトの合計行を読み取れなければ FAIL** / 却下: `(0, 0)` として続行。理由: 固定書式の機械契約が破れた状態を PASS として握りつぶさない（Codex 指摘・中）
- **採用: 単純表でないものはスキップ（元の HTML を残す）** / 却下: `colspan` 等を近似変換。理由: 近似はセル位置の意味を変える。現データは 3 件とも単純表であり近似の需要がない
- **採用: セルに `|` があればスキップ** / 却下: `\|` エスケープ。理由: `$…$` 内の `\|` は LaTeX の二重縦線コマンドとして解釈され、数式が変わる。現データに該当なし
- **採用: 1 行目をヘッダ行にする** / 却下: 空のヘッダ行を追加。理由: GFM はヘッダ行必須。MinerU の HTML は `th` を出さず先頭行が見出しかデータかを区別しないため、行を追加せず先頭行をそのまま使う（chap06 の乱数表では先頭行が太字表示になるが、セル内容は不変）
- **採用: content_list.json の `table_body` は無改変** / 却下: 併せて変換。理由: content_list は座標・画像用のデータ（`colorize_images.py` の入力）であり閲覧用ではない。MinerU のスキーマ（HTML 文字列）を維持する
- **採用: `ocr_dir.py` では機械確認の後に変換** / 却下: 正規化と同時に変換。理由: `check_normalized` は正規化前後のコードポイント一致比較であり、変換を先に行うと成立しない。変換後に再検証は不要（変換対象は表行のみ、句読点は変えない）
- **採用: `normalize_punct.py` から `validate_inputs` / `write_text_atomic` を import** / 却下: コピー。理由: 同一仕様の検証・書き込みを二重管理しない。両スクリプトは同一ディレクトリで `sys.path` 追加なしに解決する
- **採用: 既存データは final と run-01-normalized の両方に適用** / 却下: final のみ。理由: feat-005 で「final = normalized のバイト同一コピー」を構築時の機械確認としており、片方だけ変えると将来の再構築で差分の原因が追えなくなる
- **採用: 損傷した normalized md 2 件は final からのコピーで復旧** / 却下: normalize_punct.py を生出力へ再適用して再生成。理由: final が「生出力＋正規化」とバイト一致することを調査で確認済みであり、コピーが最短かつ検証容易。再生成でも結果は同一だが、final との同一性検証（手順 3.5 (f)）を別途行う以上コピーで足りる（Sonnet 実装時検出の損傷。README「実装中の発見」参照）

## 10. 実装・検証の実施方法

CLAUDE.md「実装の実行方法（Sonnetサブエージェント）」に従う。必読順: CLAUDE.md → 本案件 `requirements.md` → `design.md` → `scripts/normalize_punct.py` → `scripts/ocr_dir.py` → `tests/test_normalize_punct.py` → `tests/test_ocr_dir.py`。実装後に §4.4 のテスト全件実行と結果保存、§4.5 の手順 1〜3.5 を実施して報告する（手順 4 はユーザー）。

## 11. 完了処理でのドキュメント更新

- `CLAUDE.md`: ディレクトリ構成に `scripts/html_table_to_md.py`・`tests/test_html_table_to_md.py` を追加。ドメイン知識に「MinerU は表を 1 行の HTML `<table>` で出力し、CommonMark では HTML ブロック内の `$…$` が数式描画されない → `html_table_to_md.py` で GFM パイプテーブルに変換する（ocr_dir.py に組み込み済み）」を追記。OCR 一括実行の説明を「PDF 生成 → MinerU → 正規化 → 機械確認 → HTML 表変換」に更新
- `docs/BACKLOG.md`: feat-008 を Closed に
- `docs/CHANGELOG.md`: 完了内容を記録
- `docs/TECH_STACK.md`: 変更なし（ライブラリ追加なし）
- ルート `README.md`: 存在しないため対象外
