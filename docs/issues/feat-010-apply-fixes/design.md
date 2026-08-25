# feat-010 機能設計書: 手動修正の永続化 — 修正定義ファイルの機械適用

- 案件: `docs/issues/feat-010-apply-fixes/`
- 作成日: 2026-08-25
- 準拠基準: `docs/DESIGN_STANDARD.md`
- 用語は `requirements.md` の用語定義に従う

## 1. 対応要求マッピング

| 要求 ID | 設計セクション |
|---|---|
| FR-001 修正適用 CLI | §4.1, §4.4, §6, §7 |
| FR-002 定義ファイルの書式と検証 | §4.2 |
| FR-003 適用規則 | §4.3 |
| FR-004 ocr_dir.py への組み込み | §5 |
| FR-005 テンプレートと使い方の文書 | §9 |
| FR-006 初期修正定義の作成 | §10 |
| FR-007 既存データへの適用 | §11 |
| FR-008 自動テスト | §12 |

## 2. システム構成

```
honOCR/（リポジトリ。公開可能な内容のみ）
├── scripts/
│   ├── apply_fixes.py    # 新規: 修正適用 CLI
│   ├── normalize_punct.py  # 既存: write_text_atomic を import（変更しない）
│   └── ocr_dir.py        # 変更: --fixes-dir オプションと修正適用ステップを追加
├── fixes/
│   ├── template.json     # 新規: 書式テンプレート（架空の文字列のみ）
│   └── README.md         # 新規: 書式仕様・適用規則・運用方法
└── tests/
    ├── test_apply_fixes.py  # 新規
    └── test_ocr_dir.py      # 変更: 修正適用ステップのテストを追加

{BASE}/ocr/fixes/（リポジトリ外。git 管理しない）
├── chap01.json           # 実体の修正定義（書籍本文の文字列を含む）
├── chap02.json
└── chap05.json
```

依存方向: `apply_fixes.py` → `normalize_punct.py`（`write_text_atomic` のみ）。`ocr_dir.py` → `apply_fixes.py`（subprocess 起動。import しない）。循環依存なし。

## 3. 技術スタック

- Python 3.12（uv 管理）。標準ライブラリ（argparse, json, sys, pathlib）＋ `normalize_punct.write_text_atomic` のみ。新規ライブラリ追加なし（`docs/TECH_STACK.md` の更新不要）

## 4. apply_fixes.py の詳細設計

### 4.1 データフロー

- 入力 1: Markdown → `str`（`path.read_bytes().decode("utf-8")`）
- 入力 2: 修正定義 JSON → `dict`。スキーマ:

```json
{
  "fixes": [
    {
      "id": "eq-tag-example",
      "reason": "修正の理由（人間向けメモ）",
      "old": "修正前の完全一致文字列（非空）",
      "new": "修正後の文字列（非空。削除だけの修正は前後の残す文字列を含めて表現する）"
    }
  ]
}
```

- 出力: 適用後の Markdown `str` → `outdir/<md と同じベース名>` に `write_text_atomic` で書き込む（エラー時は書かない）

### 4.2 定義ファイルの検証（`validate_fixes`）

`json.loads` 成功後、次を順に検査し、違反は `"{fixes名}: {内容}"` 形式のエラーメッセージとして収集する（全件検査してからまとめて報告する）:

1. トップレベルが dict で `"fixes"` キーを持つ
2. `fixes` が list
3. 各要素が dict で、`id` / `reason` / `old` / `new` の 4 キーをすべて持ち、4 つとも str 型
4. `id` が非空、ファイル内で一意
5. `old` が非空
6. `new` が非空
7. `old != new`

エラーが 1 件以上あれば標準エラーに全件出力して終了コード 1（出力ファイルは書かない）。

### 4.3 適用（`apply_fixes`）

```
applied = 0; skipped = 0; errors = []
for fix in fixes:                      # 記載順の逐次適用。md は置換のたびに更新される
    n_old = md.count(fix.old)
    if n_old == 1:
        md = md.replace(fix.old, fix.new, 1); applied += 1
    elif n_old == 0:
        n_new = md.count(fix.new)
        if n_new == 1:
            skipped += 1               # 適用済みとみなす（冪等）
        elif n_new == 0:
            errors.append(f"{id}: old not found (old[:40]={...!r})")
        else:  # n_new >= 2
            errors.append(f"{id}: ambiguous - new found {n_new} times")
    else:  # n_old >= 2
        errors.append(f"{id}: old is not unique ({n_old} occurrences)")
if not errors:                         # 最終不変条件（FR-003 規則 6）
    for fix in fixes:
        if md.count(fix.old) != 0:
            errors.append(f"{id}: final invariant violated - old still present")
        if md.count(fix.new) != 1:
            errors.append(f"{id}: final invariant violated - new count is {n}")
if errors: 標準エラーに全件出力して終了コード 1（出力ファイルは書かない）
```

- 判定は常に「それ以前の修正を反映した md」に対して行う（FR-003）
- `new` は検証（§4.2）で非空が保証されるため、適用済み判定は常に `count(new) == 1` の厳密判定で行える（削除だけの修正が「最初から成功扱い」になる抜け道はない）
- エラー検査（規則 3〜5）は全 fix 分を収集してからまとめて報告する（1 件目で止めない。修正定義のメンテナンス性のため）
- **最終不変条件**の狙い: 規則 1〜5 だけでは「old が new の部分文字列である修正」（適用後も old が残り、再実行で二重適用される）や「後続 fix が先行 fix の new を書き換える修正」（再実行で先行 fix がエラーになる）を防げない。出力直前に全 fix の `count(old) == 0` かつ `count(new) == 1` を最終 md に対して検査することで、再実行が必ず「0 applied・全件 skipped・md 不変」になる定義だけを受け入れる。violate する修正は old / new の抜粋範囲（前後文脈）を広げて一意化・分離する運用とする（fixes/README.md にも記載する）

### 4.4 CLI（`parse_args` / `main`）

```python
def parse_args(argv: list[str] | None = None) -> argparse.Namespace
    # 位置引数 md: Path / 位置引数 fixes: Path
    # -o/--outdir: Path 必須 / --overwrite: store_true
def main(argv: list[str] | None = None) -> int
```

main の手順:

1. md 読み込み。失敗（不存在・デコード不能）→ 標準エラー、return 1
2. 定義ファイル読み込み＋ `validate_fixes`。失敗 → 標準エラー、return 1
3. `apply_fixes`。エラーあり → 標準エラー、return 1
4. `outdir.mkdir(parents=True, exist_ok=True)` 後、`write_text_atomic(result, outdir / md.name, overwrite)`。例外 → 標準エラー、return 1
5. 標準出力に以下の 2 行を出して return 0:

```
{md名}: {applied} applied, {skipped} skipped
total: {applied} applied, {skipped} skipped
```

（入力は 1 ファイルだが、ocr_dir.py の解析対象を `total:` 行に統一するため 2 行構成。feat-008/009 と同形式）

## 5. ocr_dir.py の変更

1. `parse_args` にオプション追加: `--fixes-dir`（`type=Path`、`default=None`、help「修正定義ファイルのディレクトリ（{name}.json を探す。省略時は修正適用を行わない）」）
2. `DirResult` にフィールド追加: `fixes_applied: int = 0`、`fixes_skipped: int = 0`
3. 関数 `parse_fixes_summary(stdout: str) -> tuple[int, int] | None` を追加: 正規表現 `r"^total: (\d+) applied, (\d+) skipped$"`（`re.MULTILINE`）
4. 関数 `apply_fixes(normalized_md: Path, fixes_file: Path, normalized_dir: Path) -> tuple[list[str], int, int]` を追加: `insert_footnotes`（feat-009 のラッパ）と同構造。コマンドは

   ```python
   [sys.executable, str(SCRIPTS_DIR / "apply_fixes.py"),
    str(normalized_md), str(fixes_file),
    "-o", str(normalized_dir), "--overwrite"]
   ```

   非 0 終了 → `["修正適用失敗: {stderr}"]`。サマリ解析不能 → `["修正適用失敗: summary parse failed: {stdout}"]`。stderr に内容があればそのまま標準エラーへ転記
5. `process_dir` 内、脚注挿入（feat-009 ステップ）成功の直後に追加:

   ```
   fixes_applied = 0; fixes_skipped = 0
   if args.fixes_dir is not None:
       fixes_file = args.fixes_dir / f"{name}.json"
       if fixes_file.is_file():
           print(f"[{name}] 修正適用中...")
           fx_errors, fixes_applied, fixes_skipped = apply_fixes(
               normalized_md, fixes_file, normalized_dir)
           fx_errors が非空 → _fail(...)（脚注挿入失敗時と同じ引数構成）
       # ファイルがなければ何もしない（メッセージも出さない）
   ```

6. 成功時の `DirResult` に `fixes_applied` / `fixes_skipped` を設定し、`main` の PASS 行の `footnotes=...` の直後に `fixes={r.fixes_applied}+{r.fixes_skipped}skipped ` を追加（`--fixes-dir` 未指定でも 0+0 で常に表示する）

## 6. ファイル・ディレクトリ設計

- 修正定義ファイルの実体: `{BASE}/ocr/fixes/{name}.json`（name は ocr_dir.py の name 決定規則と同じ。chap01 等）。リポジトリには置かない
- リポジトリ側: `fixes/template.json`・`fixes/README.md`（§9）
- 出力ファイル名: 入力 md と同じベース名を `-o` のディレクトリ直下に書く（既存スクリプトと同じ規約）
- 文字コード: 定義ファイル・md とも UTF-8

## 7. インターフェース定義

`scripts/apply_fixes.py` の公開関数（テストから import して使う）:

```python
def validate_fixes(data: object, fixes_name: str) -> list[str]
    # 戻り値: エラーメッセージのリスト（空 = 合格）
def apply_fixes(md: str, fixes: list[dict], fixes_name: str) -> tuple[str, int, int, list[str]]
    # 戻り値: (適用後md, applied, skipped, errors)。errors 非空のとき適用後mdは使用しない
def parse_args(argv: list[str] | None = None) -> argparse.Namespace
def main(argv: list[str] | None = None) -> int
```

- 責務: `apply_fixes` が適用規則の全体を担い、`main` は入出力（ファイル・引数・サマリ表示）のみを担う
- 型ヒントを全シグネチャに付ける（コーディング規約）

## 8. エラーハンドリング・ログ設計

| 事象 | 検出 | 処理 | 出力（標準エラー） |
|---|---|---|---|
| md 不存在・非 UTF-8 | 読み込み時の例外 | return 1 | 例外メッセージを含む 1 行 |
| 定義ファイル不存在・JSON 不正 | 読み込み時の例外 | return 1 | 例外メッセージを含む 1 行 |
| 定義ファイルのスキーマ違反 | `validate_fixes` | return 1（出力を書かない） | 違反全件を 1 行ずつ |
| old が見つからず new も見つからない | `apply_fixes` 規則 3 | return 1（出力を書かない） | `{id}: old not found …` |
| old が見つからず new が 2 回以上出現 | `apply_fixes` 規則 4 | return 1（出力を書かない） | `{id}: ambiguous - new found …` |
| old が 2 回以上出現 | `apply_fixes` 規則 5 | return 1（出力を書かない） | `{id}: old is not unique …` |
| 最終不変条件 violate（old 残存 / new 出現数 ≠ 1） | `apply_fixes` 規則 6（出力前検査） | return 1（出力を書かない） | `{id}: final invariant violated …` |
| 適用済み（冪等） | 規則 2 | skipped に数え正常継続 | なし |
| 出力先既存かつ `--overwrite` なし | `write_text_atomic` の拒否 | return 1 | 例外メッセージ |

ログレベル制御は行わない（既存スクリプトと同様、print / stderr のみ）。

### 境界条件

- `fixes` が空リスト → 0 applied / 0 skipped で正常終了（md は無変更の内容で書き出す）
- md が空文字列 → 全 fix が規則 3（old 0 回・new 0 回）でエラーになる
- old が md 全文と一致 → 1 回出現として通常適用
- 適用エラーと検証エラーの混在はない（検証エラー時は適用に進まない）

## 9. fixes/template.json と fixes/README.md（リポジトリ側）

`fixes/template.json`（この内容そのままをファイルにする。架空の文字列のみ）:

```json
{
  "fixes": [
    {
      "id": "example-001",
      "reason": "誤認識の訂正の例（このファイルは書式サンプル。実体は {BASE}/ocr/fixes/ に置く）",
      "old": "ここに修正前の文字列（md 内にちょうど1回出現すること。空は不可）",
      "new": "ここに修正後の文字列（空は不可。削除だけの修正は前後の残す文字列を含めて書く）"
    }
  ]
}
```

`fixes/README.md` に記載する内容（見出しと要点。文面は実装時に整える）:

1. 目的: OCR 誤りの手動修正を定義ファイルとして分離し、再OCR後も 1 コマンドで復元する
2. 実体の置き場所: `{BASE}/ocr/fixes/{name}.json`。**書籍本文の文字列を含むためリポジトリにはコミットしない**（このディレクトリにはテンプレートと本 README のみ置く）
3. 書式: template.json 参照。必須キー（id / reason / old / new）と型
4. 適用規則: requirements.md FR-003 の規則 1〜5 を転記
5. 実行方法: `uv run python scripts/apply_fixes.py <md> {BASE}/ocr/fixes/<name>.json -o <出力先> --overwrite`、および `ocr_dir.py --fixes-dir {BASE}/ocr/fixes` での一括適用
6. 注意: old は「正規化・表変換・脚注挿入がすべて済んだ md」の文字列として書く。エラーで止まったら OCR 出力が変わったサインなので、old を新しい md に合わせて更新する。最終不変条件エラー（old が new の部分文字列になっている等）が出たら、old / new の抜粋範囲（前後文脈）を広げて一意化する

## 10. 初期修正定義の作成手順（実装時に実施）

書籍本文の文字列を含むため、**old / new の具体文字列は本設計書には書かない**。次の手順で機械的に作成する:

1. 対象 5 件（案件 README の調査記録の表）について、現行 `{BASE}/ocr/final/{chap}/{chap}_gray300.md` から該当式ブロック（および直後の迷子番号の独立段落）を含む連続領域を正確に抜粋して `old` とする。抜粋範囲は「変更対象の式ブロック先頭の `$$` から迷子番号段落の末尾まで」とし、md 内で一意になることを `count == 1` で確認する
2. `new` は `old` に対して次の変更のみを加えた文字列とする:
   - 誤結合型（chap01 の (1.25)/(1.26)、chap05 の (5.98)〜(5.100)）: 各式ブロックの `\tag{}` を原本どおりの番号に付け替え・付与し、迷子番号の独立段落（前後の空行区切りを含む）を除去する
   - 統合型（chap02 の (2.218)/(2.219)、chap05 の (5.106)/(5.107)・(5.159)/(5.160)）: `\begin{array}...\end{array}` を独立した `$$ … $$` ブロックに分割し、それぞれに原本どおりの `\tag{}` を付け、迷子番号の独立段落を除去する。分割時に除去してよいのは array の**構文要素のみ**: `\begin{array}{…}`・`\end{array}`・alignment marker `&`・行区切り `\\`。数式トークン自体は変更しない（実測: chap02 の対象は `{r l}` 環境で `&` 2 個・行区切り 1 個、chap05 の 2 件は `{l}` 環境で `&` なし・行区切り 2 個 / 1 個。行とタグの対応は原本スキャンで確認して決める）
3. 番号の正しさは原本 TIF の該当領域（README 記載の page_idx・content_list インデックスから特定）を切り出して目視確認する
4. `id` は `eq-1.25-1.26` のように修正対象の式番号で命名し、`reason` に誤りの型（誤結合/統合）と原本確認済みである旨を書く
5. ファイルは `{BASE}/ocr/fixes/chap01.json`（1 fix）・`chap02.json`（1 fix）・`chap05.json`（3 fixes）として保存する

## 11. 既存データへの適用手順（実装時に実施し、結果を報告する）

対象: chap01・chap02・chap05 × final / run-01-normalized 両系統。

1. 適用前検証: 対象 3 章で final md と run-01-normalized md が `cmp` 一致することを確認。不一致なら**中断して報告**
2. 対象 3 章の content_list.json（両系統 6 ファイル）の sha256 を記録
3. 各章の final に適用: `uv run python scripts/apply_fixes.py {BASE}/ocr/final/{chap}/{chap}_gray300.md {BASE}/ocr/fixes/{chap}.json -o {BASE}/ocr/final/{chap} --overwrite`
4. run-01-normalized にも同様に適用
5. 適用後検証（すべて満たすこと。満たさない場合は中断して報告）:
   - applied 件数: chap01 = 1、chap02 = 1、chap05 = 3（両系統で同数、skipped = 0）
   - 対象 3 章で final md と run-01-normalized md が `cmp` 一致
   - content_list.json の sha256 が適用前と一致
   - 全 8 章の final md に対し「独立段落の迷子番号」検査（正規表現 `^\((1\.26|2\.219|5\.100|5\.107|5\.160)\)$` に一致する行）が 0 件
   - `\tag{1.25}` `\tag{1.26}` `\tag{2.219}` `\tag{5.100}` `\tag{5.107}` `\tag{5.160}` がそれぞれ該当章の md に 1 回ずつ出現
   - 冪等性: final chap01 に再実行して 0 applied / 1 skipped・md 不変（スクラッチパッド上で確認し、実データは変更しない）

## 12. テスト設計（tests/test_apply_fixes.py）

合成データ（**架空の文字列のみ**。書籍本文を使わない）で以下を検証する。参考: `tests/test_insert_footnotes.py`・`tests/test_html_table_to_md.py`（CLI・原子的書き込み・overwrite の検証パターン）。

| # | ケース | 検証内容 |
|---|---|---|
| 1 | 通常適用 | old 1 回出現 → 置換され applied=1。他の部分は無変更 |
| 2 | 複数修正の逐次適用 | fix1 の置換結果に fix2 が一致するケースで記載順に適用される |
| 3 | 適用済みスキップ | old 0 回・new 1 回以上 → skipped、md 不変 |
| 4 | 適用済み曖昧エラー | old 0 回・new 2 回出現 → exit 1、出力ファイルが作られない |
| 5 | old 不在エラー | old 0 回・new 0 回 → exit 1、出力ファイルが作られない |
| 6 | old 非一意エラー | old 2 回出現 → exit 1、出力ファイルが作られない |
| 7 | エラー全件収集 | 不正 fix が 2 件あるとき標準エラーに 2 件とも出る |
| 8 | 冪等性 | 出力に再実行すると 0 applied・全件 skipped・md バイト不変 |
| 9 | スキーマ検証 | 必須キー欠落・id 重複・old 空・new 空・old==new の各不正で exit 1 |
| 10 | 空 fixes | `{"fixes": []}` で 0/0 正常終了 |
| 11 | CLI: overwrite 拒否 | 出力先既存・`--overwrite` なしで exit 1、既存ファイル不変 |
| 12 | CLI: サマリ形式 | stdout が `{名}: N applied, M skipped` と `total: …` の 2 行 |
| 13 | CLI: 不正 JSON | exit 1、stderr にメッセージ |
| 14 | テンプレート検証 | リポジトリの `fixes/template.json` が `validate_fixes` を通る |
| 15 | 最終不変条件: old ⊂ new | old が new の部分文字列である fix → 適用後も old が残るため exit 1、出力ファイルが作られない |
| 16 | 最終不変条件: fix 間干渉 | 後続 fix が先行 fix の new を書き換えて `count(new) == 0` になる → exit 1、出力ファイルが作られない |

`tests/test_ocr_dir.py` への追加: `parse_fixes_summary` の成功/失敗、`apply_fixes` ラッパの失敗時 FAIL 化、`--fixes-dir` 未指定でステップ不実行、定義ファイルなしでスキップ（0/0）、PASS 行に `fixes=` が含まれること（既存テストのモック方式に合わせる）。

テスト実行: `uv run pytest -v` 全件。結果を `tests/results/feat-010_test_result.txt` に保存する。

## 13. 設計判断の記録（ADR）

| 判断 | 採用 | 却下案と理由 |
|---|---|---|
| 修正の表現 | old→new の完全一致文字列ペア | unified diff パッチは行番号・文脈依存で OCR 出力の変化に弱く、失敗時の診断が難しいため却下。正規表現は誤爆リスクと定義の読みにくさから却下（Won't に明記） |
| 実体の置き場所 | リポジトリ外 `{BASE}/ocr/fixes/` | リポジトリ内＋`.gitignore` は誤コミット 1 回で履歴に残り、GitHub 公開時に履歴書き換えが必要になるため却下（ユーザー合意） |
| エラー時の挙動 | 1 件でもエラーなら出力を書かない | 部分適用を許すと「どこまで適用されたか」の状態管理が必要になり、冪等性規則も複雑化するため却下 |
| old の一意性要求 | ちょうど 1 回出現のみ適用 | 複数一致の全置換は意図しない箇所の書き換えリスクがあるため却下。一意になるまで old の抜粋範囲を広げる運用とする |
| 削除修正の表現 | `new` 非空を必須とし、削除は前後の残す文字列を含む置換で表現 | `new` 空（削除専用）を許すと、old が最初から存在しない適用失敗を「適用済み」と区別できず、エラー検出という本機能の目的が崩れるため却下（Codex 指摘・中） |
| 適用済み判定 | `count(new) == 1` の厳密判定（0 と 2 以上はエラー） | `count(new) >= 1` は偶然の一致で適用失敗を隠し得るため却下（Codex 指摘・中） |
| 統合型の修正方針 | array を独立 `$$` ブロックに分割（構文要素 `\begin{array}` `\end{array}` `&` `\\` のみ除去可） | array のまま 2 個目のタグを追記する案は、CommonMark 上 1 ブロック 1 タグの MinerU 出力規約から外れ、レンダラ互換も不確実なため却下。「LaTeX 本体を一切変更しない」という当初表現は alignment marker `&` を含む実データで display math が壊れるため、構文要素の除去を明示的に許可する形に改めた（Codex 指摘・高） |
| ocr_dir 連携 | `--fixes-dir` 任意指定＋`{name}.json` 規約 | 定義ファイルパスの個別指定は複数ディレクトリ一括実行と噛み合わないため却下。未指定時に何もしないのは、修正定義を持たない利用者（公開後のクローン利用）でもパイプラインが完結するようにするため |
| 適用順序 | 脚注挿入の後（最終段） | old/new は完成状態の md の文字列として書くのが最も直感的で、前段に置くと後段処理（表変換等）が new を変えてしまい冪等性判定が壊れ得るため |

本設計書のコードスニペットは意図伝達が目的であり、そのままコピーして使うものではない。
