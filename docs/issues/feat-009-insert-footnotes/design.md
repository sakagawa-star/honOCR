# feat-009 機能設計書: MinerU 出力から欠落する脚注（訳注）の Markdown 挿入

- 案件: `docs/issues/feat-009-insert-footnotes/`
- 作成日: 2026-08-25
- 準拠基準: `docs/DESIGN_STANDARD.md`
- 用語は `requirements.md` の用語定義に従う

## 1. 対応要求マッピング

| 要求 ID | 設計セクション |
|---|---|
| FR-001 脚注挿入 CLI | §4.1, §4.5, §6, §7 |
| FR-002 脚注の組み立て | §4.2 |
| FR-003 挿入位置と挿入形式 | §4.3, §4.4 |
| FR-004 冪等性 | §4.4 |
| FR-005 アンカーなしページの扱い | §4.4, §8 |
| FR-006 ocr_dir.py への組み込み | §5 |
| FR-007 既存データへの適用 | §9 |
| FR-008 自動テスト | §10 |

## 2. システム構成

```
scripts/
├── insert_footnotes.py   # 新規: 脚注挿入 CLI（本案件の主対象）
├── normalize_punct.py    # 既存: write_text_atomic を import して再利用（変更しない）
└── ocr_dir.py            # 変更: HTML表変換の直後に脚注挿入ステップを追加
tests/
├── test_insert_footnotes.py  # 新規
└── test_ocr_dir.py           # 変更: 脚注挿入ステップのテストを追加
```

依存方向: `insert_footnotes.py` → `normalize_punct.py`（`write_text_atomic` のみ）および `html_table_to_md.py`（`convert_table` のみ。table アンカーの生成に使う）。`ocr_dir.py` → `insert_footnotes.py`（subprocess 起動。import しない。html_table_to_md.py と同方式）。循環依存なし。

## 3. 技術スタック

- Python 3.12（uv 管理）。使用するのは標準ライブラリ（argparse, json, re, sys, collections, pathlib）と `normalize_punct.write_text_atomic`・`html_table_to_md.convert_table` のみ。新規ライブラリ追加なし（`docs/TECH_STACK.md` の更新不要）
- テストは pytest（導入済み）

## 4. insert_footnotes.py の詳細設計

### 4.1 データフロー

- 入力 1: Markdown ファイル → `str`（`path.read_bytes().decode("utf-8")` で読む。html_table_to_md.py と同方式）
- 入力 2: content_list JSON → `list[dict]`。各ブロックの参照キー: `type: str`、`page_idx: int`、`text: str`（欠落あり得る）、`img_path: str`（image/chart/table のみ）、`bbox: list[int]`（`[x0, y0, x1, y1]`、0–1000 正規化、欠落あり得る）
- 出力: 挿入後の Markdown `str` → `outdir/<md と同じベース名>` に `normalize_punct.write_text_atomic(text, output_path, overwrite)` で書き込む
- 中間データ:
  - `located: dict[int, tuple[int, int]]` — ブロックインデックス → md 内の (開始位置, 終了位置)
  - `page_last_end: dict[int, int]` — page_idx → そのページで発見できたブロックの md 内終了位置の最大値
  - `notes_by_page: dict[int, list[str]]` — page_idx → 組み立て済み脚注のリスト

### 4.2 脚注の組み立て（`assemble_notes`）

モジュール定数:

```python
NUM_PREFIX_RE = re.compile(r"^(?:\d+|[⁰¹²³⁴⁵⁶⁷⁸⁹]+)\s")
WS_RE = re.compile(r"\s+")
```

手順（1 ページ分の脚注ブロックリスト → 組み立て済み脚注リスト）:

1. 各ブロックの `text` を取り出し（`block.get("text") or ""`）、`strip()` し、内部の改行を含む連続空白はそのまま保持した上で改行文字 `"\n"` のみ半角スペース 1 個に置換する
2. テキストが空文字列のブロックを除外する
3. 浮遊断片除去: 各ブロックのテキストから `WS_RE` で全空白を除去した文字列を作り、自分以外のブロックの空白除去文字列の部分文字列（`in` 演算、かつ両者が非同一文字列）であるブロックを除外する。同一の空白除去文字列を持つブロックが複数ある場合（完全重複）はどちらも除外されないため、後段の冪等性チェック（§4.4）で 2 個目以降が同文挿入されることを防ぐ目的で、完全重複は最初の 1 個だけ残す
4. 残ったブロックを `(bbox[1], bbox[0])` の昇順で安定ソートする。`bbox` が list でない・要素数 4 未満・欠落の場合は `[0, 0, 0, 0]` として扱う
5. 先頭から走査し、`NUM_PREFIX_RE` にマッチするテキストは新しい組み立て済み脚注として開始、マッチしないテキストは直前の組み立て済み脚注の末尾に `" "`（半角スペース 1 個）を挟んで連結する。まだ 1 個も脚注がない状態でマッチしないテキストが来た場合は、それ自身を新しい組み立て済み脚注とする（前ページからの続き）

### 4.3 アンカー探索（`locate_blocks`）

```
cursor = 0
for i, block in enumerate(content_list):
    type に応じて検索文字列の候補リスト needles を決める:
        text / ref_text / equation → [block.get("text")]
        image / chart              → [block.get("img_path")]
        table → 次の3候補をこの順で（None/空は除く）:
            (a) (block.get("table_body") or "").strip()   # HTML表が未変換の md に一致
            (b) html_table_to_md.convert_table((a)) の戻り値 (lines, reason) で
                reason が None のとき "\n".join(lines)     # feat-008 変換後の md に一致
            (c) block.get("img_path")
        上記以外（header, page_number, footer, page_footnote 等）→ 対象外（continue）
    needles を順に試す:
        pos = md.find(needle, cursor)
        pos >= 0 の最初の needle を採用
    どの候補も発見できない → continue（このブロックは発見不能。エラーにしない）
    located[i] = (pos, pos + len(needle))
    cursor = pos + len(needle)
```

- カーソルを単調増加させることで、同じ語句が複数回現れる md でも読み順の対応を保つ
- table の 3 候補の根拠（final/chap01 実測）: feat-008 変換後の md では `img_path`・`table_body` とも一致せず、`convert_table` 再生成のパイプテーブル文字列（行を `"\n"` 連結）のみが一致する（表 2 件とも確認）。未変換 md（feat-008 適用前の run 出力）では md 中の 1 行 HTML `<table>` が `table_body` と一致する。変換スキップされた複雑な表は md に HTML のまま残るため (a) で一致する
- `page_last_end[p]` = そのページ（`page_idx == p`）の `located` 済みブロックの終了位置の最大値

### 4.4 挿入（`insert_notes`）

```
inserted = 0; skipped = 0; warnings = []
inserts = []  # (挿入点, 挿入文字列)
for p in sorted(notes_by_page):
    notes = notes_by_page[p]
    if p not in page_last_end:
        skipped += len(notes)
        warnings.append(f"{md_name}: page {p}: no anchor; {len(notes)} note(s) skipped")
        continue
    ins = md.find("\n\n", page_last_end[p]);  ins < 0 なら ins = len(md)
    chunk = ""
    for t in notes:
        if ("> " + t) in md: skipped += 1; continue   # 冪等性（警告なし）
        chunk += "\n\n> " + t; inserted += 1
    if chunk: inserts.append((ins, chunk))
for pos, chunk in sorted(inserts, key=lambda x: -x[0]):   # 挿入点の降順
    md = md[:pos] + chunk + md[pos:]
```

- 同一ページの複数脚注は 1 個の `chunk` にまとめて 1 回で挿入するため、ページ内の順序は保たれる（挿入点が同一の複数挿入による順序逆転を防ぐ。プロトタイプで実際に発生した不具合の対策）
- 挿入点はアンカー段落の末尾（`"\n\n"` の直前）なので、既存テキストはバイト単位で無変更のまま、段落間に blockquote 段落が増える

### 4.5 CLI（`parse_args` / `main`）

```python
def parse_args(argv: list[str] | None = None) -> argparse.Namespace
    # 位置引数 md: Path / 位置引数 content_list: Path
    # -o/--outdir: Path 必須 / --overwrite: store_true
def main(argv: list[str] | None = None) -> int
```

main の手順:

1. md 読み込み（UTF-8）。失敗（不存在・デコード不能）→ 標準エラーにメッセージ、return 1
2. content_list 読み込み（`json.loads`）。失敗（不存在・JSON 不正）または結果が list でない → 標準エラーにメッセージ、return 1
3. `locate_blocks` → `assemble_notes`（page_idx ごと）→ `insert_notes`
4. 警告を標準エラーへ 1 行ずつ出力
5. `outdir.mkdir(parents=True, exist_ok=True)` 後、`normalize_punct.write_text_atomic(result, outdir / md.name, overwrite)`。`FileExistsError` 等の例外 → 標準エラーにメッセージ、return 1
6. 標準出力に以下の 2 行を出して return 0:

```
{md名}: {inserted} inserted, {skipped} skipped
total: {inserted} inserted, {skipped} skipped
```

（入力は 1 ファイルだが、ocr_dir.py の解析対象を `total:` 行に統一するため 2 行構成とする。html_table_to_md.py の出力形式と揃える）

## 5. ocr_dir.py の変更

### 5.1 変更点一覧

1. `DirResult` にフィールド追加: `footnotes: int = 0`、`footnotes_skipped: int = 0`
2. 関数 `parse_footnote_summary(stdout: str) -> tuple[int, int] | None` を追加: 正規表現 `r"^total: (\d+) inserted, (\d+) skipped$"`（`re.MULTILINE`）で `(inserted, skipped)` を返す。不一致なら None
3. 関数 `insert_footnotes(normalized_md: Path, normalized_content_list: Path, normalized_dir: Path) -> tuple[list[str], int, int]` を追加: `convert_tables` と同構造。コマンドは

   ```python
   [sys.executable, str(SCRIPTS_DIR / "insert_footnotes.py"),
    str(normalized_md), str(normalized_content_list),
    "-o", str(normalized_dir), "--overwrite"]
   ```

   非 0 終了 → `["脚注挿入失敗: {stderr}"]`。サマリ解析不能 → `["脚注挿入失敗: summary parse failed: {stdout}"]`。stderr に内容があれば（警告）そのまま標準エラーへ転記する（convert_tables と同じ扱い）
4. `process_dir` 内、`convert_tables` 成功の直後に追加:

   ```
   print(f"[{name}] 脚注挿入中...")
   fn_errors, footnotes, footnotes_skipped = insert_footnotes(
       normalized_md, normalized_content_list, normalized_dir)
   fn_errors が非空 → _fail(...)（convert_tables 失敗時と同じ引数構成）
   ```

5. 成功時の `DirResult` に `footnotes=footnotes, footnotes_skipped=footnotes_skipped` を追加
6. `main` の PASS 行に `footnotes={r.footnotes}+{r.footnotes_skipped}skipped ` を `tables=...` の直後に追加

### 5.2 実行順序の根拠

脚注挿入は「正規化 → 機械確認 → HTML 表変換」の後に置く。理由: (a) 挿入する脚注テキストは正規化済み content_list 由来なので句読点整合が取れる、(b) 機械確認 `check_normalized` は md の長さ一致を前提とするため、挿入（長さが変わる）はその後でなければならない、(c) table アンカーは §4.3 の 3 候補方式により変換前・変換後どちらの md でも一致が取れるため表変換との順序依存はないが、feat-008 パイプラインとの差分を最小にするため最後に置く。

## 6. ファイル・ディレクトリ設計

- 出力ファイル名: 入力 md と同じベース名を `-o` のディレクトリ直下に書く（normalize_punct.py / html_table_to_md.py と同じ規約）
- 設定ファイルなし。すべて CLI 引数
- 挿入形式（再掲・確定値): 各脚注は `"\n\n> " + 組み立て済み脚注` の 1 段落。脚注内改行なし（blockquote は常に 1 行）

## 7. インターフェース定義

`scripts/insert_footnotes.py` の公開関数（テストから import して使う）:

```python
NUM_PREFIX_RE: re.Pattern[str]
WS_RE: re.Pattern[str]

def locate_blocks(content_list: list, md: str) -> dict[int, tuple[int, int]]
def assemble_notes(blocks: list[dict]) -> list[str]
    # blocks: 同一ページの page_footnote ブロックのリスト（content_list 内の出現順）
def insert_notes(md: str, md_name: str, content_list: list) -> tuple[str, int, int, list[str]]
    # 戻り値: (挿入後md, inserted, skipped, warnings)
def parse_args(argv: list[str] | None = None) -> argparse.Namespace
def main(argv: list[str] | None = None) -> int
```

- 責務: `insert_notes` が locate → assemble → 挿入の全体を担い、`main` は入出力（ファイル・引数・サマリ表示）のみを担う
- 型ヒントを全シグネチャに付ける（コーディング規約）

## 8. エラーハンドリング・ログ設計

| 事象 | 検出 | 処理 | 出力（標準エラー） |
|---|---|---|---|
| md 不存在・非 UTF-8 | 読み込み時の例外 | return 1 | 例外メッセージを含む 1 行 |
| content_list 不存在・JSON 不正・list でない | 読み込み時の例外 / isinstance | return 1 | 例外メッセージまたは `content list is not a list: {path}` |
| 出力先既存かつ `--overwrite` なし | `write_text_atomic` の拒否 | return 1 | 例外メッセージ |
| ページにアンカーなし | `page_last_end` に page_idx なし | 該当脚注をスキップ | `{md名}: page {p}: no anchor; {k} note(s) skipped` |
| 脚注既挿入（冪等） | `"> " + t in md` | スキップ（正常系） | なし |
| ブロックの `text`/`bbox`/`img_path` 欠落 | `.get()` | §4.2/§4.3 の既定値で続行 | なし |

ログレベル制御は行わない（既存スクリプトと同様、print / stderr のみ）。

### 境界条件

- 脚注ブロック 0 件 → 挿入 0・スキップ 0 で正常終了（md は無変更の内容で書き出す）
- content_list が空リスト → 同上
- md が空文字列 → アンカーが 1 個も見つからず、全脚注が no anchor スキップになる（エラーにしない）
- 全脚注ブロックのテキストが空 → 組み立て結果 0 件 → 挿入 0
- アンカーが md 末尾の段落（後続の `"\n\n"` なし）→ md 末尾に挿入

## 9. 既存データへの適用手順（実装時に実施し、結果を報告する）

対象: NN = 00〜07 の 8 章 × 2 系統。

1. 適用前検証: 各章で `cmp {BASE}/ocr/final/chapNN/chapNN_gray300.md {BASE}/ocr/mineru-full/chapNN/run-01-normalized/chapNN_gray300.md` が一致することを確認する（feat-008 完了時点の状態）。不一致があれば**中断して報告**する
2. content_list の適用前ハッシュを記録する（`sha256sum` を final・run-01-normalized の全 16 ファイルに対して実行し保存）
3. 各章の final に適用: `uv run python scripts/insert_footnotes.py {BASE}/ocr/final/chapNN/chapNN_gray300.md {BASE}/ocr/final/chapNN/chapNN_gray300_content_list.json -o {BASE}/ocr/final/chapNN --overwrite`
4. 各章の run-01-normalized に同様に適用（md・content_list とも run-01-normalized 側のパスを使う）
5. 適用後検証（すべて満たすこと。満たさない場合は中断して報告する）:
   - 挿入件数: chap01 = 14 inserted / 1 skipped（page 83 の no anchor 警告 1 行）、chap02 = 3 / 0、chap06 = 2 / 0、他 5 章 = 0 / 0。final と run-01-normalized で同数
   - 各章で final md と run-01-normalized md が `cmp` で一致
   - 全 16 個の content_list.json の sha256 が適用前と一致
   - `grep -c "^> 4 訳注" {BASE}/ocr/final/chap01/chap01_gray300.md` が 1、`grep -c "^> 5 訳注"` が 1

## 10. テスト設計（tests/test_insert_footnotes.py）

合成データ（tmp_path 上に小さな md と content_list JSON を作る）で以下を検証する。参考にする既存テスト: `tests/test_html_table_to_md.py`（CLI・原子的書き込み・overwrite の検証パターン）。

| # | ケース | 検証内容 |
|---|---|---|
| 1 | 通常挿入 | text アンカーのページに脚注 1 件が `\n\n> …` で段落末尾に入る。既存部分は無変更 |
| 2 | 複数脚注の順序 | 同一ページ 2 件（`1 …`、`2 …`）が content 順に 1→2 で入る |
| 3 | 浮遊断片除去 | 他ブロックの部分文字列（空白差ありを含む）が除去され、1 個に組み立てられる |
| 4 | bbox 並べ替え | content_list 順が読み順と逆でも (y0, x0) 順に組み立てられる |
| 5 | 番号なし先頭ブロック | 番号プレフィックスなしのみのページで、それ自身が 1 個の脚注になる |
| 6 | 番号なし連結 | 番号あり→数式→続き の 3 ブロックが半角スペース連結で 1 個になる |
| 7 | アンカーなし | 本文が md にないページの脚注がスキップされ、警告文言が仕様どおり |
| 8 | 冪等性 | 出力に再実行すると 0 inserted・全件 skipped・md 不変 |
| 9 | 画像アンカー | ページ唯一のブロックが image（`img_path`）でも挿入できる |
| 9b | 表アンカー（未変換） | ページ最後のブロックが table で、md に 1 行 HTML `<table>` がある場合に `table_body` 一致で挿入できる |
| 9c | 表アンカー（変換後） | ページ最後のブロックが table で、md が GFM パイプテーブルに変換済みの場合に `convert_table` 再生成文字列の一致で挿入できる |
| 10 | 末尾ページ | 後続 `\n\n` がない末尾段落への挿入 |
| 11 | 脚注 0 件 | 0 inserted / 0 skipped、md 内容不変 |
| 12 | CLI: overwrite 拒否 | 出力先既存・`--overwrite` なしで exit 1、既存ファイル不変 |
| 13 | CLI: サマリ形式 | stdout が `{名}: N inserted, M skipped` と `total: …` の 2 行 |
| 14 | CLI: 不正 JSON | exit 1、stderr にメッセージ |

`tests/test_ocr_dir.py` への追加: `parse_footnote_summary` の成功/失敗、`insert_footnotes`（ocr_dir 側ラッパ）の失敗時 FAIL 化、PASS 行に `footnotes=` が含まれること（既存テストのモック方式に合わせる）。

テスト実行: `uv run pytest -v` 全件。結果を `tests/results/feat-009_test_result.txt` に保存する。

## 11. 設計判断の記録（ADR）

| 判断 | 採用 | 却下案と理由 |
|---|---|---|
| 挿入形式 | blockquote（`> …` 1 段落） | GFM 脚注記法 `[^n]` は本文側に参照アンカーが必要だが、MinerU の md 本文に上付き脚注番号は残っておらず挿入位置を機械決定できないため却下。プレーン段落は本文と区別がつかないため却下 |
| 挿入位置 | ページ末尾（アンカー段落の直後） | 文書末尾へ一括集約は脚注と本文の対応（ページ）情報が失われるため却下。md をブロックから全再生成する案は既存成果物（表変換・正規化済み）を壊すリスクが大きく却下 |
| 断片除去 | 空白除去後の部分文字列判定 | bbox の包含判定は断片 bbox が本体 bbox の外にはみ出す実例（chap01 p64 idx 568）があり不採用 |
| ページ跨ぎの脚注 | 結合しない（続きは番号なし脚注として当該ページに挿入） | 跨ぎ結合は「前ページ最後の脚注が未完である」ことの機械判定が不確実で、原本もページごとに分割印刷されているため、忠実性の観点で分割のまま挿入する |
| content_list | 無改変 | 脚注の組み立て結果を書き戻す案は MinerU スキーマからの逸脱となるため却下（feat-008 と同方針） |
| ocr_dir 連携 | subprocess 起動 | import 直呼びは html_table_to_md.py（subprocess）と方式が割れ、stdout/stderr の分離も自前実装になるため却下 |

本設計書のコードスニペットは意図伝達が目的であり、そのままコピーして使うものではない。
