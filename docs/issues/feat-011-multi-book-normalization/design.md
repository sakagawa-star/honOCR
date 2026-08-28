# feat-011 機能設計書: 他書籍対応のための正規化・脚注処理の一般化

対象要求仕様書: `docs/issues/feat-011-multi-book-normalization/requirements.md`
調査記録（実測データの根拠）: `docs/issues/feat-011-multi-book-normalization/README.md`

## 1. 対応要求マッピング

| 要求ID | 設計セクション |
|---|---|
| FR-001 句読点スタイルの選択 | §4.1, §4.2, §4.6 |
| FR-002 中国語字の字形正規化 | §4.1, §4.2, §4.6 |
| FR-003 JIS 外漢字の残存警告 | §4.3, §4.6, §8 |
| FR-004 `ocr_dir.py` への伝播と機械確認の連動 | §5 |
| FR-005 脚注プレフィックスの `*N` 対応 | §6.1 |
| FR-006 断片判定の比較正規化 | §6.2 |
| FR-007 既存データに対する回帰の非破壊 | §9 |
| FR-008 自動テスト | §10 |

## 2. システム構成

変更するファイルは 3 本のスクリプトと 3 本のテストのみ。新規に作成するファイルは
テスト結果ファイル `tests/results/feat-011_test_result.txt`（§10）だけであり、
`scripts/` 配下・`tests/` 配下に新しいモジュールやテストファイルは追加しない。

```
scripts/
├── normalize_punct.py    # 変更: 句読点スタイル・字形正規化・JIS外警告
├── insert_footnotes.py   # 変更: プレフィックス正規表現・比較キー
└── ocr_dir.py            # 変更: --punct-style 伝播・check_normalized 連動
tests/
├── test_normalize_punct.py   # 変更: テスト追加
├── test_insert_footnotes.py  # 変更: テスト追加
└── test_ocr_dir.py           # 変更: テスト追加
```

依存関係（呼び出し方向。循環なし）:

- `ocr_dir.py` → `normalize_punct.py`（**新規に `import` する**。定数・置換表の参照のため）
- `ocr_dir.py` → 各スクリプト（従来どおり `subprocess` で実行）
- `insert_footnotes.py` → `normalize_punct.py`（既存。`write_text_atomic` の再利用）
- `insert_footnotes.py` → `html_table_to_md.py`（既存）

`ocr_dir.py` は先頭に `SCRIPTS_DIR` を持ち、自身が `scripts/` 直下にあるため、
`insert_footnotes.py` と同じ形式（`import normalize_punct`）で import できる。

## 3. 技術スタック

- Python 3.12.3（既存）
- 標準ライブラリのみ（`argparse` / `re` / `json` / `pathlib`）。
  JIS X 0208 の判定には Python 同梱の `shift_jis` コーデックを用い、外部辞書は使わない
- 新規ライブラリの追加はなし（`docs/TECH_STACK.md` の更新は不要）

## 4. `normalize_punct.py` の詳細設計

### 4.1 モジュール定数（既存 `REPLACEMENTS` を置き換える）

```python
PUNCT_STYLES: tuple[str, ...] = ("comma", "touten")
DEFAULT_PUNCT_STYLE: str = "comma"

PUNCT_REPLACEMENTS: dict[str, dict[str, str]] = {
    "comma": {"、": "，", "。": "．"},
    "touten": {},
}

CJK_REPLACEMENTS: dict[str, str] = {
    "值": "値",
    "变": "変",
    "单": "単",
    "对": "対",
    "图": "図",
    "换": "換",
    "徵": "徴",
    "樣": "様",
}
```

既存のモジュール定数 `REPLACEMENTS` と `TRANSLATION_TABLE` は**削除する**。
（`REPLACEMENTS` を参照している箇所は `ocr_dir.py` 内の同名の別定義のみであり、
それも §5.1 で削除する。`tests/` からの参照はない。）

### 4.2 置換表の生成と適用

```python
def build_replacements(punct_style: str = DEFAULT_PUNCT_STYLE) -> dict[str, str]:
    """句読点置換（スタイル依存）と字形置換（常時）を合成した置換表を返す。"""
```

- 処理: `PUNCT_REPLACEMENTS[punct_style] | CJK_REPLACEMENTS` を返す
- `punct_style` が `PUNCT_STYLES` に無い場合は `KeyError` を送出する
  （CLI 経由では argparse の `choices` で弾かれるため到達しない。ライブラリ誤用の検出用）
- キーの重複はない（句読点 2 字と漢字 8 字で交差しない）

```python
def normalize_text(
    text: str, punct_style: str = DEFAULT_PUNCT_STYLE
) -> tuple[str, int]:
    """置換後テキストと置換件数を返す。"""
```

- 処理:
  1. `replacements = build_replacements(punct_style)`
  2. `count = sum(text.count(src) for src in replacements)`
  3. `normalized = text.translate(str.maketrans(replacements))`
  4. `(normalized, count)` を返す
- すべて 1 文字 → 1 文字の置換であるため、`len(normalized) == len(text)` が常に成り立つ
- 第 2 引数のデフォルト値により、既存の呼び出し `normalize_text(text)` は
  「comma スタイル ＋ 字形正規化」となる

### 4.3 JIS 外漢字の検出（FR-003）

```python
CJK_RE: re.Pattern[str] = re.compile(r"[一-鿿]")
CONTEXT_CHARS: int = 25


def is_jis_x0208(ch: str) -> bool:
    """文字が JIS X 0208 で表現できるかを返す。"""
```

- 処理: `ch.encode("shift_jis")` を試み、成功で `True`、`UnicodeEncodeError` で `False`
- コーデックは `shift_jis` を使う（`cp932` は NEC/IBM 拡張を含むため使わない）

```python
def find_non_jis_kanji(text: str) -> dict[str, tuple[int, str]]:
    """JIS 外漢字 -> (出現件数, 最初の出現箇所の文脈) を返す。"""
```

- 処理:
  1. `chars = set(CJK_RE.findall(text))`（ユニーク化してから判定する。
     文字ごとに `encode` を呼ぶ回数を字種数に抑えるため）
  2. 各 `ch` について `is_jis_x0208(ch)` が `False` のものだけを対象にする
  3. 件数は `text.count(ch)`
  4. 文脈は `pos = text.find(ch)` として
     `text[max(0, pos - CONTEXT_CHARS):pos + CONTEXT_CHARS + 1]` を取り、
     改行（`\n`）と復帰（`\r`）を半角空白 1 文字に置換する
  5. 戻り値の辞書はそのまま返す（順序付けは呼び出し側で行う）

```python
def format_non_jis_warning(name: str, found: dict[str, tuple[int, str]]) -> list[str]:
    """警告行のリストを返す（found が空なら空リスト）。"""
```

- 出力書式（FR-003）:
  - 1 行目: `{name}: JIS外漢字 {字種数} 種 {総件数} 件`
  - 2 行目以降: `sorted(found)` の順（コードポイント昇順・決定的）に
    `  '{ch}' x{件数}: ...{文脈}...`

### 4.4 エラーハンドリング

本案件で新規に増えるエラーはない。既存の `validate_inputs`（not found / not utf-8 /
duplicate basename / output exists）と終了コードの規約（0 = 正常、1 = 検証エラー）は変更しない。

- `--punct-style` の不正値: argparse の `choices` により終了コード 2 で abort（argparse の標準動作）
- JIS 外漢字の検出: 警告のみ。終了コードを変えない（FR-003 受け入れ基準 2）
- `encode("shift_jis")` は `UnicodeEncodeError` 以外の例外を送出しない（サロゲートは
  正規表現 `[一-鿿]` に一致しないため入力に現れない）

### 4.5 境界条件

| 入力 | 振る舞い |
|---|---|
| 空ファイル | 置換 0 件・警告なしで出力（空ファイルを書き出す）。既存動作と同一 |
| 置換対象を含まない | 出力は入力とバイト単位で一致し、集計は `0 replaced` |
| JIS 外漢字が 0 件 | 標準エラーへ何も出力しない |
| 同じ JIS 外漢字が複数回 | 1 字種として 1 行にまとめ、件数を合算し、文脈は最初の 1 件のみ |
| 文脈がファイル先頭・末尾に接する | `max(0, ...)` とスライスの上限クリップにより短い文脈を出力する（エラーにしない） |
| `touten` スタイルで「、」「。」を含む | 句読点は置換されず、字形置換のみが行われる |

### 4.6 CLI（`parse_args` / `main`）

`parse_args` に次の引数を追加する（他の引数・`description` は変更しない）。

```python
parser.add_argument(
    "--punct-style",
    choices=PUNCT_STYLES,
    default=DEFAULT_PUNCT_STYLE,
    help="句読点スタイル（comma: 、。→，．に置換 / touten: 句読点を置換しない。既定 comma）",
)
```

`main` の処理順序（変更点は 3 と 5 のみ）:

1. 引数解析
2. `validate_inputs`（変更なし）
3. ファイルごとに `normalize_text(text, args.punct_style)` を呼ぶ
4. `write_text_atomic` で出力（変更なし）
5. **正規化後テキスト**に対して `find_non_jis_kanji` → `format_non_jis_warning` を実行し、
   各行を `print(..., file=sys.stderr)` で出力する
6. 集計行 `{file_path.name}: {count} replaced` を標準出力へ（既存書式）
7. 合計行 `total: {total} replaced in {len(files)} files` を標準出力へ（既存書式）

標準出力（6・7）の書式は変更しない。`ocr_dir.py` はこの書式を解析しないが、
ユーザーが目視で追う情報であるため維持する。

## 5. `ocr_dir.py` の変更

### 5.1 変更点一覧

| 箇所 | 変更内容 |
|---|---|
| import 節 | `import normalize_punct` を追加（`import pypdf` の下に置く） |
| モジュール定数 | `REPLACEMENTS: dict[str, str] = {"、": "，", "。": "．"}` を**削除**する |
| `check_normalized` | 第 3 引数 `punct_style` を追加（§5.2） |
| `process_dir` | 正規化コマンドへ `--punct-style` を付与、`check_normalized` へスタイルを渡す、replaced 集計を置換表ベースに変更（§5.3） |
| `parse_args` | `--punct-style` を追加（§5.4） |

### 5.2 `check_normalized` の連動（FR-004）

```python
def check_normalized(
    src: Path,
    dst: Path,
    punct_style: str = normalize_punct.DEFAULT_PUNCT_STYLE,
) -> list[str]:
```

処理（既存の枠組みを保ち、`allowed` と残存検査だけを置換表から導出する）:

1. `dst` が存在しなければ `[f"normalized output missing: {dst}"]` を返す（既存）
2. `a = src.read_text()`, `b = dst.read_text()`
3. 長さ不一致なら `[f"length mismatch: {src} ({len(a)}) vs {dst} ({len(b)})"]` を返す（既存）
4. `replacements = normalize_punct.build_replacements(punct_style)`
5. `allowed = set(replacements.items())`
6. `bad_diff = sum(1 for x, y in zip(a, b) if x != y and (x, y) not in allowed)`
   → 1 以上なら `f"disallowed diff: {bad_diff} positions in {dst}"` を追加（既存書式）
7. `residual = sum(b.count(src_ch) for src_ch in replacements)`
   → 1 以上なら `f"residual source chars: {residual} in {dst}"` を追加
   （**メッセージ文言を変更する**。残存対象が句読点だけでなく中国語字も含むため。
   既存テストはメッセージ文字列を検証していないため影響しない）
8. エラーリストを返す

この設計により、スタイルごとの判定は自動的に次のようになる。

| スタイル | 許可される差分 | 残存検査の対象 |
|---|---|---|
| `comma`（既定） | （、→，）（。→．）＋ 字形 8 ペア | 「、」「。」＋ 中国語字 8 字 |
| `touten` | 字形 8 ペアのみ | 中国語字 8 字のみ |

`touten` では「、→，」が許可差分に含まれないため、誤って句読点が置換されていれば
`disallowed diff` で FAIL する（FR-004 受け入れ基準 2）。

### 5.3 `process_dir` の変更

- 正規化の実行コマンドに `--punct-style` を追加する:

  ```python
  cmd = [
      sys.executable,
      str(SCRIPTS_DIR / "normalize_punct.py"),
      str(md_path),
      str(content_list_path),
      "-o",
      str(normalized_dir),
      "--punct-style",
      args.punct_style,
  ]
  ```

  `normalize_punct.py` の標準エラー（JIS 外漢字の警告）は現行実装では
  `subprocess.run(..., capture_output=True)` で捕捉され、`returncode == 0` のときは
  破棄されている。**`returncode == 0` の場合も `proc.stderr` が空でなければ
  `print(proc.stderr.strip(), file=sys.stderr)` で素通しする**
  （`convert_tables` / `insert_footnotes` と同じ扱い。FR-004 受け入れ基準 7）

- `check_normalized` の 2 箇所の呼び出しに `args.punct_style` を渡す

- replaced 件数の集計を置換表ベースに変更する:

  ```python
  replacements = normalize_punct.build_replacements(args.punct_style)
  ...
  replaced_md = sum(md_text.count(c) for c in replacements)
  replaced_json = sum(content_text.count(c) for c in replacements)
  ```

  （`touten` の場合、字形置換のみが計上される。PASS サマリの `replaced=` の意味は
  「正規化で置換された文字数」で一貫する）

### 5.4 `parse_args` の追加引数

```python
parser.add_argument(
    "--punct-style",
    choices=normalize_punct.PUNCT_STYLES,
    default=normalize_punct.DEFAULT_PUNCT_STYLE,
    help="句読点スタイル（comma: 、。→，．に置換 / touten: 句読点を置換しない。既定 comma）",
)
```

PASS/FAIL サマリ行の書式は変更しない（要求仕様書 §5 の出力互換制約）。

## 6. `insert_footnotes.py` の変更

### 6.1 脚注プレフィックスの認識範囲（FR-005）

既存の `NUM_PREFIX_RE` を次に置き換える。

```python
NUM_PREFIX_RE = re.compile(
    r"^(?:"
    r"\d+"                        # 例: "4 "
    r"|[⁰¹²³⁴⁵⁶⁷⁸⁹]+"            # 例: "⁴ "
    r"|\\?\*\d+"                  # 例: "*4 " / "\*4 "（Markdown エスケープ）
    r"|\$\^\{\*?\d+\}\$"          # 例: "$^{3}$ " / "$^{*4}$ "
    r")\s"
)
```

- 4 つの選択肢はいずれも直後に空白（`\s`）が続く場合にのみ一致する（既存仕様の維持）
- 3 番目の `\\?` は「バックスラッシュ 0 個または 1 個」。MinerU は Markdown 中の
  `*` を `\*` とエスケープして出力するため、両方を受ける
- 4 番目の中括弧内は「アスタリスク 0 個または 1 個 ＋ 半角数字列」に限定する。
  `$^{(p.128)}$` のような**ページ参照の上付き**に誤って一致しないようにするため
- 正規表現の交替順序は上記のとおり固定する（`\d+` が先でも、`\*4` は `\d+` に
  一致しないため結果は変わらない。可読性のため既存順を保つ）

### 6.2 断片判定の比較キー（FR-006）

既存の `WS_RE`（`\s+`）による比較キー生成を、次の関数に置き換える。

```python
KEY_STRIP_RE = re.compile(r"[\s$\\]+")


def comparison_key(text: str) -> str:
    """断片判定に用いる比較キー（空白・`$`・`\\` を除去した文字列）を返す。"""
    return KEY_STRIP_RE.sub("", text)
```

`assemble_notes` の変更点は次の 2 点のみ。

1. `stripped = [WS_RE.sub("", it["text"]) for it in items]` を
   `keys = [comparison_key(it["text"]) for it in items]` に変える
2. 断片判定ループの前に「**比較キーが空文字列の要素は断片判定の対象から除外する**」条件を加える

   ```python
   for i in range(n):
       if keys[i] == "":          # 追加: 空キーは他の任意文字列の部分文字列になってしまう
           continue
       for j in range(n):
           if i == j:
               continue
           if keys[i] != keys[j] and keys[i] in keys[j]:
               is_fragment[i] = True
               break
   ```

   併せて、重複除去（`seen`）でも空キーは重複扱いしない:

   ```python
   for i in range(n):
       if is_fragment[i]:
           continue
       key = keys[i]
       if key != "" and key in seen:
           continue
       if key != "":
           seen.add(key)
       kept_indices.append(i)
   ```

   理由: `"" in "abc"` は `True` であるため、比較キーから `$` を除去した結果として
   空キー（例: テキストが `$$` のみのブロック）が生じると、そのブロックが常に断片と
   判定されて消える。既存実装では空白のみのブロックが事前に `text == ""` で除外されるため
   この事象は起きなかったが、`$`・`\` を除去対象に加えることで新たに起こりうる

3. 挿入されるテキスト（`it["text"]`）は変更しない。比較キーは判定にのみ用いる
   （FR-006 受け入れ基準 2）

`WS_RE` は他で使われていないため削除する。

### 6.3 境界条件

| 入力 | 振る舞い |
|---|---|
| `page_footnote` が 0 件のページ | 従来どおり挿入なし |
| 比較キーが空になるブロック（`$$` 等） | 断片扱いにせず保持する（§6.2） |
| プレフィックスに一致しない先頭ブロック | 従来どおり単独の脚注として保持（`notes` が空の場合） |
| プレフィックスに一致しない後続ブロック | 従来どおり直前の脚注に空白 1 文字で連結 |
| 同一内容の脚注ブロックが 2 件 | 従来どおり比較キーの重複として 1 件に集約 |

## 7. インターフェース定義

変更・追加される公開関数のシグネチャ（すべてモジュールレベル関数）。

```python
# normalize_punct.py
def build_replacements(punct_style: str = DEFAULT_PUNCT_STYLE) -> dict[str, str]: ...
def normalize_text(text: str, punct_style: str = DEFAULT_PUNCT_STYLE) -> tuple[str, int]: ...
def is_jis_x0208(ch: str) -> bool: ...
def find_non_jis_kanji(text: str) -> dict[str, tuple[int, str]]: ...
def format_non_jis_warning(name: str, found: dict[str, tuple[int, str]]) -> list[str]: ...
# 変更なし: validate_inputs, write_text_atomic, parse_args, main

# insert_footnotes.py
def comparison_key(text: str) -> str: ...
# 変更なし（シグネチャ）: _needles_for_block, locate_blocks, assemble_notes,
#                        insert_notes, parse_args, main

# ocr_dir.py
def check_normalized(
    src: Path, dst: Path, punct_style: str = normalize_punct.DEFAULT_PUNCT_STYLE
) -> list[str]: ...
# 変更なし（シグネチャ）: その他すべて
```

## 8. ログ・デバッグ設計

本プロジェクトの既存方針（`logging` を使わず `print` で標準出力／標準エラーに書く）を踏襲する。

| 出力先 | 内容 | 追加/既存 |
|---|---|---|
| 標準出力 | `{name}: {n} replaced` / `total: {n} replaced in {m} files` | 既存（書式変更なし） |
| 標準エラー | JIS 外漢字の警告（§4.3 の書式） | 追加 |
| 標準エラー | 検証エラー（not found 等） | 既存 |
| `ocr_dir.py` 標準出力 | `[{name}] 正規化中...` 等の進捗、PASS/FAIL サマリ | 既存（書式変更なし） |
| `ocr_dir.py` 標準エラー | 正規化サブプロセスの stderr（JIS 外漢字の警告を含む） | 追加（素通し） |

## 9. 既存データへの適用手順（実装時に実施し、結果を報告する）

実装完了後、次の 3 つを実行し、結果を報告に含める（**成果物は書き換えない**。
検証は一時ディレクトリへの出力で行う）。

1. **PRML final の再正規化差分（FR-007 受け入れ基準 1・2）**

   ```
   uv run python scripts/normalize_punct.py \
     {BASE}/ocr/final/chapNN/chapNN_gray300.md -o <一時ディレクトリ>
   ```
   を chap00〜07 の 8 章について、Markdown と content_list.json の両方を入力に実行し、
   入力と出力の差分位置を数える。
   期待値（2026-08-28 実測）:
   - Markdown 8 ファイル合計の差分は字形置換のみで **13 箇所**
     （`值` 3・`变` 4・`单` 2・`对` 1・`徵` 1・`樣` 2、`图` 0・`换` 0）
   - content_list.json 8 ファイル合計の差分は **23 箇所**
     （`值` 8・`变` 9・`单` 2・`对` 1・`徵` 1・`樣` 2）
   - 句読点の差分は Markdown・JSON とも 0 箇所
   - FR-003 の警告として `跺` 2 件・`濵` 1 件（2 字種 3 件）が Markdown・JSON の
     いずれについても報告される

2. **PRML final の脚注冪等性（FR-007 受け入れ基準 3）**

   ```
   uv run python scripts/insert_footnotes.py \
     {BASE}/ocr/final/chapNN/chapNN_gray300.md \
     {BASE}/ocr/final/chapNN/chapNN_gray300_content_list.json -o <一時ディレクトリ>
   ```
   を chap00〜07 について実行する。
   期待値: 全章で `0 inserted`、かつ出力が入力とバイト単位で一致する

3. **確率統計パイロット出力での改善確認（FR-005・FR-006 受け入れ基準）**

   パイロット出力
   `/home/sakagawa/work/確率統計/ocr/pilot/mineru-full/chap07/run-01/chap07_gray300/hybrid_auto/`
   の `chap07_gray300.md` と `chap07_gray300_content_list.json` に対し、
   `--punct-style touten` で正規化 → `insert_footnotes.py` を適用する。
   期待値:
   - 正規化後も「、」241 件・「。」260 件が保持される
   - 字形置換は Markdown で計 9 件（`樣` 6・`图` 1・`变` 1・`换` 1）、
     content_list.json でも計 9 件（同内訳）である（2026-08-28 実測）
   - JIS 外漢字の警告は出ない（`图`・`变`・`换` は置換済み。他に JIS 外漢字はない）
   - 脚注は p2・p4・p10 に挿入され、**p4 が 2 行の blockquote に分かれる**
   - p10 の blockquote 末尾に `[0,1) でなく (0,1]` が残らない

## 10. テスト設計（`tests/`）

`uv run pytest -v` の全件 PASS を条件とし、出力を `tests/results/feat-011_test_result.txt` に保存する。

### 10.1 `tests/test_normalize_punct.py`（追加）

**FR-003 を採用しない場合、対応欄が「FR-003」のテスト 5 件（`test_non_jis_warning_emitted`・
`test_non_jis_warning_exit_code_zero`・`test_non_jis_warning_absent_when_clean`・
`test_non_jis_warning_excludes_replaced_chars`・`test_is_jis_x0208`）は追加しない**
（要求仕様書 FR-008 受け入れ基準 2 の例外規定）。他のテストは FR-003 の採否に依存しない。

| テスト名 | 対応 | 内容 |
|---|---|---|
| `test_punct_style_default_is_comma` | FR-001 | `--punct-style` 省略で「今日は、晴れ。」→「今日は，晴れ．」 |
| `test_punct_style_touten_keeps_punctuation` | FR-001 | `--punct-style touten` で「今日は、晴れ。」が変化しない |
| `test_punct_style_invalid_value` | FR-001 | 不正値で `SystemExit` の `code == 2`（`pytest.raises`） |
| `test_cjk_normalized_in_comma_style` | FR-002 | 「二值变数・单・对・图・换・徵・樣」→「二値変数・単・対・図・換・徴・様」 |
| `test_cjk_normalized_in_touten_style` | FR-002 | `touten` でも字形置換が行われる |
| `test_replace_count_includes_cjk` | FR-002 | 集計行の件数が句読点＋字形の合計と一致する（`capsys`） |
| `test_length_preserved` | FR-002 | 置換前後で `len` が等しい |
| `test_non_jis_warning_emitted` | FR-003 | 「濵」「跺」を含む入力で標準エラーに字種数・件数・文脈が出る（`capsys`） |
| `test_non_jis_warning_exit_code_zero` | FR-003 | 警告が出ても戻り値が 0 |
| `test_non_jis_warning_absent_when_clean` | FR-003 | 日本語のみの入力で標準エラーが空 |
| `test_non_jis_warning_excludes_replaced_chars` | FR-003 | 「变」のみを含む入力で警告が出ない（置換済みのため） |
| `test_build_replacements_comma_and_touten` | FR-001/002 | `build_replacements` の戻り値のキー集合を検証 |
| `test_is_jis_x0208` | FR-003 | 「値」→ True、「值」→ False、「樣」→ True |

### 10.2 `tests/test_insert_footnotes.py`（追加）

| テスト名 | 対応 | 内容 |
|---|---|---|
| `test_assemble_asterisk_prefix_splits_notes` | FR-005 | `["\\*2 参考文献 …", "$^{3}$ ただし …"]` が 2 件の脚注になる |
| `test_assemble_asterisk_without_backslash` | FR-005 | `"*4 本文"` もプレフィックスとして認識される |
| `test_assemble_superscript_math_prefix` | FR-005 | `"$^{*4}$ 本文"` がプレフィックスとして認識される |
| `test_assemble_page_ref_superscript_not_prefix` | FR-005 | `"$^{(p.128)}$ 続き"` はプレフィックスではなく直前へ連結される |
| `test_assemble_fragment_with_math_removed` | FR-006 | 断片 `"[0,1) でなく (0,1]"` が、`$` 付きの親脚注により除去される |
| `test_assemble_keeps_original_text` | FR-006 | 挿入テキストに `$`・`\` が保持される |
| `test_assemble_empty_key_block_kept` | FR-006 | テキストが `"$$"` のブロックが断片扱いで消えない |
| `test_comparison_key` | FR-006 | `comparison_key("a $b$ \\c")` == `"abc"` |

### 10.3 `tests/test_ocr_dir.py`（追加）

| テスト名 | 対応 | 内容 |
|---|---|---|
| `test_check_normalized_touten_pass` | FR-004 | `touten` で「、」が残っていても `errors == []` |
| `test_check_normalized_touten_rejects_punct_change` | FR-004 | `touten` で「、」→「，」の差分があれば errors が非空 |
| `test_check_normalized_cjk_allowed` | FR-004 | 「变」→「変」の差分は両スタイルで許可される |
| `test_check_normalized_cjk_residual` | FR-004 | 出力に「变」が残っていれば errors が非空（両スタイル） |
| `test_process_dir_passes_punct_style` | FR-004 | サブプロセス呼び出しをモックし、`normalize_punct.py` のコマンドに `--punct-style touten` が含まれることを検証（既存のモック方式に合わせる） |
| `test_process_dir_forwards_normalize_stderr` | FR-004 | 正規化サブプロセスが stderr を返したとき、`capsys` の stderr に素通しされることを検証 |

既存テスト 143 件は改変しない（`check_normalized` の第 3 引数はデフォルト値を持つため
既存の 2 引数呼び出しはそのまま通る）。

## 11. 設計判断の記録（ADR）

### ADR-1: スタイル名を `comma` / `touten` にする

- 採用: `--punct-style {comma,touten}`
- 却下: `{to-comma,keep}` — 「keep」は「何を keep するか」が曖昧であり、
  将来 3 つ目の書籍で別のスタイルが必要になったときに命名が破綻する。
  スタイル名は「書籍が用いる句読点の字」を表す名前とする
- 却下: `--no-normalize-punct`（フラグ形式） — 「置換する/しない」の 2 値ではなく
  「書籍のスタイル」という概念にした方が、FR-004 の検査条件を導出しやすい

### ADR-2: 字形正規化を常時適用とし、無効化オプションを設けない

- 採用: `CJK_REPLACEMENTS` は句読点スタイルによらず常に適用する
- 理由: 対象 8 字種はいずれも日本語の数学書本文で正当に出現しない字であり、
  無効化する用途が存在しない。オプションを増やすと `ocr_dir.py` への伝播も増え、
  検査条件（§5.2）の組み合わせが 4 通りに増える
- 却下: `--no-cjk-normalize` を設ける — 上記のとおり用途がなく、複雑さに見合わない
- 影響: `--punct-style` を省略した既存の呼び出しでも出力が変わりうる
  （PRML final の Markdown 8 章で 13 箇所、content_list.json 8 章で 23 箇所）。
  これは要求仕様書 §4「後方互換性」に明記した意図的な差分である。
  なお `跺` 2 件・`濵` 1 件は置換表の対象外であり、この件数には含まれない
  （FR-003 の警告で報告されるのみで、出力は変わらない）

### ADR-3: 「濵→演」「跺→疎」を置換表に含めない

- 採用: 字形の 1 対 1 対応が確立している 8 字種のみを置換表に入れ、
  それ以外は FR-003 の警告で検出してユーザーが `apply_fixes.py` で対処する
- 理由: 「濵」は「濱（浜）」の異体字であり「演」ではない。「跺」は「疎」と字形の
  対応関係を持たない。これらは MinerU の個別の誤認識であり、一般規則にすると
  別の文脈で誤った置換を行う危険がある（feat-010 の「old 不在・複数一致は全件エラー」
  という安全策が働く `apply_fixes.py` の担当領域である）

### ADR-4: JIS X 0208 の判定に `shift_jis` コーデックを使う

- 採用: `str.encode("shift_jis")` の成否で判定する
- 却下: `cp932` — NEC/IBM 拡張文字を含むため、判定が緩くなる
- 却下: 常用漢字表・人名用漢字表を埋め込む — データの保守が必要になり、
  JIS 第 2 水準の漢字（本文に正当に現れうる）を誤検出する
- 限界の明示: 「樣」は JIS X 0208 に含まれるため本判定では検出できない。
  そのため実測で判明した中国語字は `CJK_REPLACEMENTS` に明示列挙する方式を採る
  （FR-003 は「置換表で直せないものを見つける補助」であり、網羅性は主張しない）

### ADR-5: `ocr_dir.py` から `normalize_punct` を import する

- 採用: 置換表と定数を `normalize_punct` に一元化し、`ocr_dir.py` は import して参照する
- 却下: `ocr_dir.py` 側にも定数を複製する（現行の `REPLACEMENTS` の形） —
  置換表が 2 箇所に分かれると、字形置換の追加時に検査条件との不整合が起きる
- 依存方向: `ocr_dir.py` → `normalize_punct.py` の単方向であり、循環しない
  （`insert_footnotes.py` → `normalize_punct.py` と同じ前例がある）

### ADR-6: 比較キーの空文字列を断片判定から除外する

- 採用: §6.2 のとおり、空キーのブロックは断片判定・重複判定の対象外とする
- 理由: `"" in "任意の文字列"` が `True` になるため、除外しないと `$$` のような
  ブロックが常に消える。挿入すべき内容が消えるより、余分に残る方が
  「入力への忠実な OCR」というプロジェクト方針に沿う
