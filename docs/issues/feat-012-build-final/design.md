# feat-012 機能設計書: final ディレクトリ構築の自動化

対象要求仕様書: `docs/issues/feat-012-build-final/requirements.md`

## 1. 対応要求マッピング

| 要求ID | 設計セクション |
|---|---|
| FR-001 final 構築 CLI の新設 | §4.2, §4.3, §4.7 |
| FR-002 入力検証とエラー処理 | §4.4 |
| FR-003 構築後の機械検証 | §4.5 |
| FR-004 図が 0 件の章の扱い | §4.3, §4.5, §4.6 |
| FR-005 `ocr_dir.py` への組み込み | §5 |
| FR-006 冪等性 | §4.3（孤児削除）, §4.6 |
| FR-007 既存データとの整合 | §9 |
| FR-008 自動テスト | §10 |

## 2. システム構成

```
scripts/
├── build_final.py        # 新規: 正規化済みディレクトリ → final ディレクトリの集約と検証
├── colorize_images.py    # 変更なし（ocr_dir.py から呼ばれる側）
└── ocr_dir.py            # 変更: --final の追加、カラー再切出と final 構築の呼び出し
tests/
├── test_build_final.py   # 新規
└── test_ocr_dir.py       # 変更: テスト追加
```

新規に作成するファイルは `scripts/build_final.py`・`tests/test_build_final.py`・
テスト結果ファイル `tests/results/feat-012_test_result.txt` の3点。

依存関係（呼び出し方向。循環なし）:

- `ocr_dir.py` → `colorize_images.py`（`subprocess`。新規）
- `ocr_dir.py` → `build_final.py`（`subprocess`。新規）
- `build_final.py` → `normalize_punct.py`（`import`。`write_text_atomic` は使わないが、
  原子的コピーの実装方針を揃えるため §4.3 の `copy_atomic` を `build_final.py` 内に置く。
  **import はしない**）

`build_final.py` は他スクリプトを import しない自己完結モジュールとする。

## 3. 技術スタック

- Python 3.12.3（既存）
- 標準ライブラリのみ（`argparse` / `json` / `os` / `re` / `shutil` / `sys` / `tempfile` / `pathlib`）
- 新規ライブラリの追加はなし（`docs/TECH_STACK.md` の更新は不要）

## 4. `build_final.py` の詳細設計

### 4.1 モジュール定数

```python
CONTENT_LIST_SUFFIX: str = "_content_list.json"
IMAGES_DIRNAME: str = "images"
IMAGE_REF_RE: re.Pattern[str] = re.compile(r"images/[^\s)\"'<>]+")
```

`IMAGE_REF_RE` は Markdown 中の `![](images/xxxx.jpg)` や
`<img src="images/xxxx.jpg">` の両方から参照パスを拾うためのもので、
`images/` に続く「空白・`)`・引用符・不等号以外の文字列」を1件とみなす。

### 4.2 データフロー

入力:

| データ | 型・形式 | 値域・制約 |
|---|---|---|
| `normalized_dir` | `Path` | 既存のディレクトリ。直下に `*_content_list.json` がちょうど1個 |
| `outdir` | `Path` | final の出力先。存在しなければ作成する |
| `overwrite` | `bool` | 既定 `False` |

中間データ:

| データ | 型 | 内容 |
|---|---|---|
| `base` | `str` | ベース名（例: `chap07_gray300`） |
| `md_src` | `Path` | `normalized_dir / f"{base}.md"` |
| `cl_src` | `Path` | `normalized_dir / f"{base}{CONTENT_LIST_SUFFIX}"` |
| `images_src` | `Path` | `normalized_dir / IMAGES_DIRNAME`（存在しないことがある） |
| `src_names` | `set[str]` | `images_src` 直下のファイル名集合（`images_src` が無ければ空集合） |

出力:

| データ | 内容 |
|---|---|
| `outdir / f"{base}.md"` | `md_src` のバイト同一コピー |
| `outdir / f"{base}{CONTENT_LIST_SUFFIX}"` | `cl_src` のバイト同一コピー |
| `outdir / IMAGES_DIRNAME / *` | `images_src` 直下の全ファイルのバイト同一コピー |
| 終了コード | 0 = 成功、1 = 検証エラーまたは構築エラー、2 = argparse のエラー |

### 4.3 処理ロジック（`main`）

1. 引数を解析する。
2. `find_pair(normalized_dir)` でベース名と 2 つの入力パスを決める（§4.4）。
   例外が返れば標準エラーへ出力して終了コード 1 を返す。
3. `validate_inputs(normalized_dir, md_src, cl_src, outdir, overwrite)` を呼ぶ（§4.4）。エラーが 1 件でもあれば、
   全件を標準エラーへ出力して終了コード 1 を返す（**この時点まで出力先に一切書かない**）。
4. `outdir` と `outdir / IMAGES_DIRNAME` を `mkdir(parents=True, exist_ok=True)` で作成する。
5. `copy_atomic(md_src, outdir / md_src.name)` と
   `copy_atomic(cl_src, outdir / cl_src.name)` を実行する。
6. 画像をコピーする:
   1. `src_names` の各ファイルについて `copy_atomic(images_src / name, outdir / IMAGES_DIRNAME / name)`
   2. **孤児削除**（FR-006 基準3）: `outdir / IMAGES_DIRNAME` 直下のファイルのうち
      `src_names` に含まれないものを `unlink()` する。
      ディレクトリが含まれる場合は削除せず、標準エラーへ
      `unexpected directory in images: {パス}` を出力して終了コード 1 を返す
7. `verify(...)` を実行する（§4.5）。エラーが 1 件でもあれば全件を標準エラーへ出力し、
   **出力ファイルは削除せずに**終了コード 1 を返す（FR-003 基準4）。
8. 標準出力へ 2 行を出力し、終了コード 0 を返す:
   ```
   {base}: md=1 content_list=1 images={len(src_names)}
   total: 1 built
   ```

**例外処理**: 手順 4〜7 の全体を `try` で囲み、`OSError` を捕捉したら
`print(f"build failed: {exc}", file=sys.stderr)` を出力して終了コード 1 を返す
（Python のトレースバックを出さない。要求仕様書 FR-001 基準7）。
既に書き出したファイルは削除しない（検証不合格時と同じ扱い）。
検証で防いでいる事象（§4.4 の検証 7・8）以外の I/O エラー（権限不足・ディスク不足・
実行中に入力が消される等）がここに落ちる。

```python
def copy_atomic(src: Path, dst: Path) -> None:
    """バイト同一のコピーを原子的に行う。

    同一ディレクトリの一時ファイルへ書き、fsync 後に os.replace で確定する
    （feat-002 write_pdf_atomic・feat-004 write_text_atomic と同じ方式。
    ただしテキストではなくバイト列を扱うため shutil.copyfileobj を用いる）。
    失敗時は一時ファイルを削除して例外を送出する。
    """
```

`copy_atomic` は `overwrite` の区別を持たない（既存ファイルの有無は §4.4 で検証済みであり、
ここでは常に `os.replace` で確定する）。

### 4.4 入力検証（`find_pair` と `validate_inputs`）

```python
def find_pair(normalized_dir: Path) -> tuple[str, Path, Path]:
    """(ベース名, md パス, content_list パス) を返す。

    決定不能な場合は ValueError を送出する。
    """
```

- `normalized_dir` がディレクトリでなければ
  `ValueError(f"not a directory: {normalized_dir}")`
- `sorted(normalized_dir.glob(f"*{CONTENT_LIST_SUFFIX}"))` の件数が
  - 0 件: `ValueError(f"content list not found in {normalized_dir}")`
  - 2 件以上: `ValueError(f"multiple content lists in {normalized_dir}: {件数}")`
- ベース名は `content_list.name` から末尾の `CONTENT_LIST_SUFFIX` を除いた文字列
- md は `normalized_dir / f"{base}.md"`。存在しなければ
  `ValueError(f"md not found: {md}")`

```python
def validate_inputs(
    normalized_dir: Path,
    md: Path,
    content_list: Path,
    outdir: Path,
    overwrite: bool,
) -> list[str]:
    """検証を行い、エラーメッセージのリストを返す（空 = 合格）。

    normalized_dir は検証6（重なり検査）と検証7（images の種別）に用いる。
    """
```

検証項目（すべて実施し、エラーを積み上げて返す）:

| # | 条件 | エラーメッセージ |
|---|---|---|
| 1 | `md.stat().st_size == 0` | `empty file: {md}` |
| 2 | `content_list.stat().st_size == 0` | `empty file: {content_list}` |
| 3 | content_list が UTF-8 の JSON として読めない | `content list unreadable: {content_list} ({例外})` |
| 4 | content_list が JSON 配列でない | `content list is not an array: {content_list}` |
| 5 | `overwrite` が False で、出力先の md・content_list・`images/` 直下のいずれかが既存 | `output exists: {パス} (use --overwrite)`（既存のものすべてを列挙する） |
| 6 | 出力先が入力ディレクトリと重なる（§4.4.1） | `outdir overlaps normalized_dir: {outdir}` |
| 7 | `normalized_dir / IMAGES_DIRNAME` が存在するがディレクトリでない | `images is not a directory: {パス}` |
| 8 | `outdir / IMAGES_DIRNAME` が存在するがディレクトリでない | `output images is not a directory: {パス}` |
| 9 | `outdir` が存在し、かつ `outdir.is_symlink()` が真 | `outdir must not be a symlink: {outdir}` |
| 10 | `outdir / IMAGES_DIRNAME` が存在し、かつ `is_symlink()` が真 | `output images must not be a symlink: {パス}` |

検証 6〜10 は `overwrite` の値によらず常に実施する。

検証 9・10 の理由: `is_dir()` はシンボリックリンクの先を辿るため、リンクであっても真になる。
その状態でコピー・孤児削除を行うと、final の外にある実体を書き換え・削除しうる
（要求仕様書 §4 の「シンボリックリンク・ハードリンクを使わない」に反する）。
判定は `Path.is_symlink()`（`lstat` ベースでリンク自身を見る）で行い、
実ディレクトリのみを許可する。コピー元側（`normalized_dir` と `images_src`）は
読み取りしか行わないため、この検査の対象外とする。

#### 4.4.1 出力先と入力ディレクトリの重なり検査（検証 6）

`Path.resolve()` で実体パスに正規化してから、次のいずれかに当たる場合をエラーとする。

```python
nd = normalized_dir.resolve()
od = outdir.resolve()           # outdir は未作成でもよい（resolve は strict=False が既定）
overlap = (od == nd) or (nd in od.parents) or (od in nd.parents)
```

- `od == nd`: 出力先がコピー元そのもの
- `nd in od.parents`: 出力先がコピー元の配下（コピー元ディレクトリに書き込むことになる）
- `od in nd.parents`: コピー元が出力先の配下（孤児削除がコピー元を巻き込む恐れがある）

`--overwrite` の有無によらず終了コード 1 で拒否する（要求仕様書 FR-002 基準6）。
シンボリックリンク経由で同じ実体を指す場合も `resolve()` により検出できる。

### 4.5 構築後の検証（`verify`）

```python
def verify(
    md_src: Path, cl_src: Path, outdir: Path, base: str, src_names: set[str]
) -> list[str]:
    """FR-003 の3項目を検証し、エラーメッセージのリストを返す（空 = 合格）。"""
```

1. **バイト同一**（FR-003 基準1）
   - `md_src.read_bytes() != (outdir / md_src.name).read_bytes()` なら
     `byte mismatch: {outdir / md_src.name}`
   - content_list についても同様
2. **md の画像参照の解決**（FR-003 基準2）
   - `refs = {Path(m).name for m in IMAGE_REF_RE.findall(md_text)}`
     （`md_text` は final 側 md を UTF-8 で読んだもの）
   - `missing = refs - actual_names`（`actual_names` = `outdir/images` 直下のファイル名集合）
   - `missing` が空でなければ
     `missing images referenced by md: {sorted(missing) の先頭5件}{" ..." if 5件超}`
3. **`img_path` 集合の一致**（FR-003 基準3）
   - final 側 content_list を読み、`img_path` キーを持つ要素の
     `Path(block["img_path"]).name` のユニーク集合を `expected` とする
   - `expected != actual_names` なら、差分を両方向で示す:
     - `images missing (in content_list, not in images/): {sorted(expected - actual_names)}`
     - `images extra (in images/, not in content_list): {sorted(actual_names - expected)}`
     - それぞれ空でない側のみ出力する
   - `img_path` が文字列でない要素は無視する（MinerU スキーマ外のデータに落ちないため）

検証はすべて **final 側の出力ファイル**を読んで行う（コピーが正しく行われたかを確かめるため、
メモリ上のデータではなく書き出した結果を読む）。

### 4.6 境界条件

| 入力 | 振る舞い |
|---|---|
| `images_src` が存在しない | `src_names` は空集合。`outdir/images` を空ディレクトリとして作成し、検証3 は「空集合 = 空集合」で合格（図 0 件の章。FR-004） |
| `images_src` は存在するが空 | 上と同じ |
| content_list に図ブロックが 0 件で `images/` に画像がある | 検証3 の `images extra` で不合格 |
| md に画像参照が 0 件で `images/` に画像がある | 検証2 は合格（`refs` が空集合）。検証3 で content_list との一致が確かめられる（PRML chap01 等、content_list からのみ参照される画像が正常に存在するため。feat-005 work_log の実績） |
| `outdir` が `normalized_dir` と同一パス、またはどちらかが他方の配下 | §4.4 検証6 でエラー（`--overwrite` の有無によらず終了コード 1）。コピー元を書き換える・孤児削除がコピー元に及ぶ事故を防ぐ |
| `normalized_dir / images` が通常ファイル | §4.4 検証7 でエラー（列挙時の `NotADirectoryError` を書き込み前に防ぐ） |
| `outdir / images` が通常ファイル | §4.4 検証8 でエラー（`mkdir` の例外を書き込み前に防ぐ） |
| `images_src` 直下にサブディレクトリがある | コピー対象は直下のファイルのみ。サブディレクトリは無視する（MinerU は images 直下にのみ出力する） |
| `outdir/images` 直下にサブディレクトリがある | §4.3 手順 6-2 でエラー（`unexpected directory in images`） |

### 4.7 CLI（`parse_args`）

```python
parser = argparse.ArgumentParser(
    description="final ディレクトリ構築スクリプト（正規化済み出力を final へ集約し検証する）"
)
parser.add_argument(
    "normalized_dir",
    type=Path,
    help="正規化済みディレクトリ（run-NN-normalized。md・content_list・images/ を含む）",
)
parser.add_argument(
    "-o", "--outdir", type=Path, required=True,
    help="final の出力先ディレクトリ（例: {root}/final/chapNN）",
)
parser.add_argument(
    "--overwrite", action="store_true",
    help="出力先の同名ファイルが既存でも上書きする（既定は拒否）",
)
```

## 5. `ocr_dir.py` の変更

### 5.1 変更点一覧

| 箇所 | 変更内容 |
|---|---|
| `DirResult` | フィールド `images: int = 0` を追加（既存フィールドの後ろ） |
| 新設関数 | `parse_colorize_summary` / `colorize_images` / `parse_final_summary` / `build_final`（§5.2） |
| `process_dir` | 修正適用の後に `--final` 指定時の 2 ステップを追加（§5.3） |
| `parse_args` | `--final` を追加（§5.4） |
| `main` の PASS サマリ | `images={r.images}` を `fixes=…` の後ろに追加 |

### 5.2 新設関数

既存の `convert_tables` / `insert_footnotes` / `apply_fixes` と同じ構造にする
（`subprocess.run(capture_output=True, text=True)` → 非0終了ならエラー → サマリ行を正規表現で解析 →
解析不能ならエラー → stderr を素通し）。

```python
def parse_colorize_summary(stdout: str) -> tuple[int, int] | None:
    """colorize_images.py の出力から (blocks, unique) を読み取る。"""
```
- 正規表現: `^blocks=(\d+) unique=(\d+) outdir=.+$`（`re.MULTILINE`）

```python
def colorize_images(
    normalized_content_list: Path, tif_dir: Path, images_dir: Path
) -> tuple[list[str], int]:
    """正規化済み content_list の図ブロックを原本 TIF からカラー再切出する。

    戻り値は (エラーメッセージのリスト, 生成枚数)。
    """
```
- コマンド: `[sys.executable, str(SCRIPTS_DIR / "colorize_images.py"), str(normalized_content_list), str(tif_dir), "-o", str(images_dir), "--overwrite"]`
- 失敗時のメッセージ: `カラー再切出失敗: {proc.stderr.strip()}`
- サマリ解析不能時: `カラー再切出失敗: summary parse failed: {proc.stdout.strip()}`
- 戻り値の枚数は `unique`（重複 `img_path` を除いた実生成数）

```python
def parse_final_summary(stdout: str) -> bool:
    """build_final.py の出力に `total: 1 built` があるかを返す。"""
```
- 正規表現: `^total: 1 built$`（`re.MULTILINE`）

```python
def build_final(normalized_dir: Path, final_dir: Path) -> list[str]:
    """正規化済みディレクトリから final ディレクトリを構築する。

    戻り値はエラーメッセージのリスト（空 = 成功）。
    """
```
- コマンド: `[sys.executable, str(SCRIPTS_DIR / "build_final.py"), str(normalized_dir), "-o", str(final_dir), "--overwrite"]`
- 失敗時のメッセージ: `final 構築失敗: {proc.stderr.strip()}`
- サマリ解析不能時: `final 構築失敗: summary parse failed: {proc.stdout.strip()}`

### 5.3 `process_dir` の変更

修正適用ブロック（`if args.fixes_dir is not None:` の全体）の**直後**、
`elapsed = time.monotonic() - start` の**直前**に、次を挿入する。

```python
images = 0
if args.final:
    print(f"[{name}] カラー再切出中...")
    images_dir = normalized_dir / "images"
    cz_errors, images = colorize_images(normalized_content_list, d, images_dir)
    if cz_errors:
        return _fail(name, cz_errors, start, pages=page_count, blocks=blocks,
                     replaced_md=replaced_md, replaced_json=replaced_json)

    print(f"[{name}] final 構築中...")
    final_dir = root / "final" / name
    bf_errors = build_final(normalized_dir, final_dir)
    if bf_errors:
        return _fail(name, bf_errors, start, pages=page_count, blocks=blocks,
                     replaced_md=replaced_md, replaced_json=replaced_json)
```

- カラー再切出の入力 content_list は**正規化済みの方**（`normalized_content_list`）を使う。
  `bbox`・`page_idx`・`img_path` は正規化・表変換・脚注挿入・修正適用のいずれでも
  改変されないため、生出力と同じ結果になる（feat-008/009/010 の「content_list 無改変」の設計による）
- カラー再切出の TIF ディレクトリは入力ディレクトリ `d` を使う
- 返り値の `images` は成功時の `DirResult(images=images)` に渡す（`_fail` 側には渡さない。
  失敗時の `DirResult.images` は既定値 0 のままとする）
- **章単位構築**（FR-005 基準4）: 各章の `process_dir` が独立して final を作るため、
  後続の章が FAIL しても既に構築された final はそのまま残る。追加の制御は不要である

### 5.4 `parse_args` の追加引数

```python
parser.add_argument(
    "--final",
    action="store_true",
    help="カラー再切出と final ディレクトリ構築（{root}/final/{name}/）を行う（既定は行わない）",
)
```

### 5.5 PASS サマリ行

```python
f"{r.name}: PASS pages={r.pages} blocks={r.blocks} "
f"replaced={r.replaced_md}+{r.replaced_json} "
f"tables={r.tables}+{r.tables_skipped}skipped "
f"footnotes={r.footnotes}+{r.footnotes_skipped}skipped "
f"fixes={r.fixes_applied}+{r.fixes_skipped}skipped "
f"images={r.images} "
f"({minutes}分{seconds}秒)"
```

`--final` を指定しない実行では `images=0` と表示される。

## 6. ファイル・ディレクトリ設計

```
{root}/
├── pdf/
├── mineru-full/{name}/
│   ├── run-NN/…/hybrid_auto/     # MinerU 生出力（images/ を含む。触らない）
│   ├── run-NN-normalized/
│   │   ├── {base}.md
│   │   ├── {base}_content_list.json
│   │   └── images/               # 新規: カラー再切出の出力（--final 指定時）
│   └── run-NN.log
└── final/{name}/                 # 新規: --final 指定時に構築
    ├── {base}.md
    ├── {base}_content_list.json
    └── images/
```

`{base}` = `{name}_gray300`。この配置は feat-005 で構築された PRML の final と同一である。

## 7. インターフェース定義

```python
# build_final.py（新規）
def find_pair(normalized_dir: Path) -> tuple[str, Path, Path]: ...
def validate_inputs(normalized_dir: Path, md: Path, content_list: Path, outdir: Path, overwrite: bool) -> list[str]: ...
def copy_atomic(src: Path, dst: Path) -> None: ...
def verify(md_src: Path, cl_src: Path, outdir: Path, base: str, src_names: set[str]) -> list[str]: ...
def parse_args(argv: list[str] | None = None) -> argparse.Namespace: ...
def main(argv: list[str] | None = None) -> int: ...

# ocr_dir.py（追加）
def parse_colorize_summary(stdout: str) -> tuple[int, int] | None: ...
def colorize_images(normalized_content_list: Path, tif_dir: Path, images_dir: Path) -> tuple[list[str], int]: ...
def parse_final_summary(stdout: str) -> bool: ...
def build_final(normalized_dir: Path, final_dir: Path) -> list[str]: ...
```

`colorize_images.py` のシグネチャは変更しない。

## 8. ログ・デバッグ設計

既存方針（`logging` を使わず `print`）を踏襲する。

| 出力先 | 内容 | 追加/既存 |
|---|---|---|
| `build_final.py` 標準出力 | `{base}: md=1 content_list=1 images={n}` / `total: 1 built` | 追加 |
| `build_final.py` 標準エラー | 検証エラー（入力・構築後とも） | 追加 |
| `ocr_dir.py` 標準出力 | `[{name}] カラー再切出中...` / `[{name}] final 構築中...` | 追加 |
| `ocr_dir.py` 標準エラー | サブプロセスの stderr の素通し | 既存方式を踏襲 |

## 9. 既存データへの適用手順（実装時に実施し、結果を報告する）

**PRML の既存 `{BASE}/ocr/final/` は変更しない。**検証は一時ディレクトリへの出力で行う
（`{BASE}` = `/home/sakagawa/work/Pattern_Recognition_and_Machine_Learning`）。

1. chap00〜07 の 8 章について次を実行する。
   ```
   uv run python scripts/build_final.py \
     {BASE}/ocr/mineru-full/chapNN/run-01-normalized -o <一時ディレクトリ>/chapNN
   ```
   期待値: 全 8 章が終了コード 0。
2. 生成物と既存 final を比較する。
   期待値（FR-007）:
   - md・content_list.json 計16ファイルが既存 final とバイト同一
   - `images/` のファイル名集合が既存 final と一致
   - 図 0 件の chap07 は空の `images/` が作られる（feat-005 work_log の実績と一致）
3. 冪等性の確認: 手順1を `--overwrite` 付きでもう一度実行し、
   出力の全ファイルが 1 回目とバイト同一であることを確認する。

なお、PRML の `run-01-normalized/` には feat-005 当時にカラー再切出した `images/` が
残っているため、手順1は `colorize_images.py` を再実行せずに検証できる。
`images/` が無い章があった場合は、その章について
`uv run python scripts/colorize_images.py {BASE}/ocr/mineru-full/chapNN/run-01-normalized/chapNN_gray300_content_list.json {BASE}/chapNN/out -o <一時ディレクトリ>/images_chapNN`
を実行して枚数を確かめ、状況を報告する（既存の `run-01-normalized/images/` は書き換えない）。

## 10. テスト設計

`uv run pytest -v` の全件 PASS を条件とし、出力を `tests/results/feat-012_test_result.txt` に保存する。
テストはすべて `tmp_path` 上に作った合成データで行い、実データを参照しない（FR-008 基準3）。

### 10.1 `tests/test_build_final.py`（新規）

| テスト名 | 対応 | 内容 |
|---|---|---|
| `test_build_copies_three_parts` | FR-001 | md・content_list・images 2枚がコピーされ、終了コード 0 |
| `test_build_byte_identical` | FR-001 | コピー先の md・content_list・画像がコピー元とバイト同一 |
| `test_build_source_unchanged` | FR-001 | 実行後もコピー元のファイルが変更されない |
| `test_build_summary_format` | FR-001 | 標準出力が `{base}: md=1 content_list=1 images=2` と `total: 1 built`（`capsys`） |
| `test_build_rejects_existing_without_overwrite` | FR-001 | 出力先に同名 md がある状態で `--overwrite` なし → 終了コード 1、出力先の内容が変わらない |
| `test_build_overwrite_replaces` | FR-001 | `--overwrite` で既存ファイルが置き換わる |
| `test_missing_normalized_dir` | FR-002 | 存在しないディレクトリ → 終了コード 1 |
| `test_no_content_list` | FR-002 | content_list が無い → 終了コード 1 |
| `test_multiple_content_lists` | FR-002 | content_list が 2 個 → 終了コード 1 |
| `test_missing_md` | FR-002 | content_list に対応する md が無い → 終了コード 1 |
| `test_empty_md` | FR-002 | md が 0 バイト → 終了コード 1 |
| `test_content_list_not_json` | FR-002 | content_list が壊れた JSON → 終了コード 1 |
| `test_content_list_not_array` | FR-002 | content_list が JSON オブジェクト → 終了コード 1 |
| `test_rejects_outdir_equal_to_source` | FR-002 | `-o` にコピー元と同じパス → 終了コード 1、コピー元のファイルが変更されない（`--overwrite` の有無の両方で検証） |
| `test_rejects_outdir_inside_source` | FR-002 | `-o` がコピー元の配下（`<src>/final`）→ 終了コード 1 |
| `test_rejects_source_inside_outdir` | FR-002 | コピー元が `-o` の配下 → 終了コード 1 |
| `test_images_src_not_a_directory` | FR-002 | コピー元の `images` が通常ファイル → 終了コード 1、出力先に書かれない |
| `test_output_images_not_a_directory` | FR-002 | 出力先の `images` が通常ファイル → 終了コード 1 |
| `test_rejects_symlinked_outdir` | FR-002 | `-o` が別ディレクトリへのシンボリックリンク → 終了コード 1、リンク先の内容が変わらない |
| `test_rejects_symlinked_output_images` | FR-002 | 出力先の `images` がシンボリックリンク → 終了コード 1、リンク先のファイルが削除されない |
| `test_verify_detects_missing_image_ref` | FR-003 | md が参照する画像が images/ に無い → 終了コード 1（`img_path` は一致させておく） |
| `test_verify_detects_img_path_mismatch` | FR-003 | content_list の `img_path` に無い画像が images/ にある → 終了コード 1 |
| `test_verify_detects_img_path_missing` | FR-003 | content_list にあるが images/ に無い → 終了コード 1 |
| `test_no_images_dir_creates_empty` | FR-004 | コピー元に images/ が無く図ブロック 0 件 → 空の images/ が作られ終了コード 0、`images=0` |
| `test_empty_images_dir_ok` | FR-004 | 空の images/ ＋図ブロック 0 件 → 終了コード 0 |
| `test_md_without_image_refs_ok` | FR-003 | md に画像参照が無くても content_list と images/ が一致すれば合格 |
| `test_idempotent_rebuild` | FR-006 | `--overwrite` で 2 回実行し、全ファイルがバイト同一 |
| `test_orphan_image_removed` | FR-006 | 出力先 images/ に余分なファイルがある状態で再構築 → 削除され検証に合格 |

### 10.2 `tests/test_ocr_dir.py`（追加）

既存のサブプロセスをモックする方式（`test_process_dir_*` 系）に合わせる。

| テスト名 | 対応 | 内容 |
|---|---|---|
| `test_parse_colorize_summary` | FR-005 | `blocks=12 unique=10 outdir=/x` → `(12, 10)`、不正文字列 → `None` |
| `test_parse_final_summary` | FR-005 | `total: 1 built` → `True`、`total: 0 built` → `False` |
| `test_process_dir_final_disabled_by_default` | FR-005 | `--final` 省略時、`colorize_images.py` と `build_final.py` が呼ばれない |
| `test_process_dir_final_invokes_both` | FR-005 | `--final` 指定時、`colorize_images.py` → `build_final.py` の順で呼ばれ、いずれも `--overwrite` 付き |
| `test_process_dir_final_output_paths` | FR-005 | `build_final.py` の出力先が `{root}/final/{name}` である |
| `test_process_dir_colorize_failure_fails_dir` | FR-005 | カラー再切出が非0終了 → その章が FAIL |
| `test_process_dir_final_failure_fails_dir` | FR-005 | final 構築が非0終了 → その章が FAIL |
| `test_summary_includes_images` | FR-005 | PASS サマリ行に `images=` が含まれる |

## 11. 設計判断の記録（ADR）

### ADR-1: `build_final.py` を独立 CLI にする

- 採用: 集約と検証を独立した CLI に切り出し、`ocr_dir.py` は `subprocess` で呼ぶ
- 理由: `html_table_to_md.py`（feat-008）・`insert_footnotes.py`（feat-009）・
  `apply_fixes.py`（feat-010）と同じ構造にする。MinerU を再実行せずに final だけ
  作り直したい場合（画像の切出条件を変えた、final を誤って消した等）に単体で使える
- 却下: `ocr_dir.py` 内の関数として実装する — 単体再構築ができず、テストも
  `ocr_dir.py` のモックに依存して複雑になる

### ADR-2: 章単位で final を構築する

- 採用: 1章の処理が完了するたびに、その章の final を構築する
- 却下: 全章の機械確認が合格してから一括構築する（feat-005 の方式）
- 理由: 2026-08-28 のユーザー決定。確率統計は10章あり、章を分けて実行する運用が想定される。
  ある章が FAIL しても完成した章の成果物は使えるべきである。
  feat-005 の「全章揃ってから」は初回の一括本処理で中途半端な成果物を残さないための
  制約であり、章ごとに完結する成果物の性質に由来するものではない

### ADR-3: `--final` はオプトイン（既定で無効）

- 採用: `--final` を指定したときだけカラー再切出と final 構築を行う
- 却下: 既定で有効にする — PRML の再実行など既存の呼び出しの動作が変わる。
  `--fixes-dir`（feat-010）と同じくオプトインに揃える

### ADR-4: `images/` の孤児ファイルを削除する

- 採用: 再構築時、出力先 `images/` にあってコピー元に無いファイルを削除する
- 理由: FR-003 の検証3 は `img_path` 集合と `images/` の**完全一致**を要求する。
  再 OCR で図の構成が変わった場合、古い画像が残っていると検証が通らず、
  ユーザーが手で消す必要が生じる
- 却下: 孤児を残す — 上記のとおり検証が通らなくなる。
  検証3 を「包含関係」に緩める — content_list からのみ参照される画像の欠落を
  検出できなくなる（feat-005 FR-004 基準4 で明示的に採用された検査であり、緩めない）

### ADR-5: カラー再切出は `ocr_dir.py` が呼び、`build_final.py` は呼ばない

- 採用: `build_final.py` の責務は「集約と検証」に限定し、画像生成は行わない
- 理由: `build_final.py` の入力を「正規化済みディレクトリ」1つに保てる。
  カラー再切出には原本 TIF ディレクトリが必要で、これを `build_final.py` の
  引数に加えると責務が2つになり、単体での再集約（TIF が手元にない状況）ができなくなる
- 却下: `build_final.py` が `colorize_images.py` を呼ぶ — 上記のとおり

### ADR-6: コピーは一時ファイル経由の原子的置換で行う

- 採用: `copy_atomic`（一時ファイル → fsync → `os.replace`）
- 却下: `shutil.copyfile` の直接呼び出し — 途中で失敗すると出力先に不完全な
  ファイルが残る。本プロジェクトの既存スクリプト（feat-002 `write_pdf_atomic`、
  feat-004 `write_text_atomic`）は一貫して原子的書き込みを採っており、それに揃える

### ADR-7: 出力先と入力ディレクトリの重なりを常に拒否する

- 採用: 実体パスで「同一」「一方が他方の配下」を検出し、`--overwrite` の有無によらず
  終了コード 1 で拒否する（§4.4.1）
- 理由: 出力先をコピー元（またはその配下）に指定できると、コピー元の md・content_list を
  上書きし、さらに孤児削除がコピー元の `images/` を消しうる。
  要求仕様書 §4「コピー元を変更・削除しない」を破る唯一の経路であり、入口で塞ぐ
- 却下: `--overwrite` 指定時のみ許す — 誤操作で成果物のコピー元を失う危険があり、
  許して得られる用途がない
- 却下: 検証のみ行い警告で済ませる — 破壊が起きてからでは戻せない
