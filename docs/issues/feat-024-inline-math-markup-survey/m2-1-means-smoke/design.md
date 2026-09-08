# feat-024 M2-1 機能設計書: 新規手段の単体疎通（段2）

- **案件 / マイルストーン**: feat-024 / **M2-1**（`../roadmap.md` §5 の**段2**）
- **作成日**: 2026-09-07
- **準拠**: `docs/DESIGN_STANDARD.md`
- **上位文書**: `../roadmap.md`（第3版）／`requirements.md`（本マイルストーンの要求）
- **判定の閾値**: `../roadmap.md` §6 の**段2 の想定値と外れの幅**（本書に再掲しない）

**本書だけを読んで、判断なしに実装・実行できることを目的とする。**
**`../roadmap.md` §5 の「決める項」が無しの段であるため、疎通以上の作業を設計しない。**

---

## 1.1 対応要求マッピング

| 要求 ID | 設計セクション |
|---|---|
| FR-M2-1-001（層別標本抽出の疎通） | §4（`sample_candidates.py` の仕様）・§7 手順1・§8 |
| FR-M2-1-002（`--input-sample` の疎通） | §5（既存スクリプトの実行）・§7 手順2 |
| FR-M2-1-003（推定の疎通） | §6（`estimate_rates.py` の仕様）・§7 手順3 |
| NFR-M2-1-001（決定性） | §4.6・§6.6・§7 手順4 |
| NFR-M2-1-003（既存データの不変） | §2「入力（読み取りのみ）」・§9 |
| NFR-M2-1-004（書籍本文の非混入） | §3（出力先の表） |

## 1.2 システム構成

### 新設するもの（いずれも**本マイルストーンフォルダ配下**。ADR-M2-1-1）

| ファイル | 役割 |
|---|---|
| `docs/issues/feat-024-inline-math-markup-survey/m2-1-means-smoke/sample_candidates.py` | 候補 TSV から層・件数・シードを指定して無作為抽出し、標本 TSV を出す CLI |
| `docs/issues/feat-024-inline-math-markup-survey/m2-1-means-smoke/estimate_rates.py` | 層ごとの計数（`N`, `k`, `n'`）から `p̂`・Wilson 区間・推定件数を算出する CLI |
| `docs/issues/feat-024-inline-math-markup-survey/m2-1-means-smoke/smoke_counts.tsv` | 推定スクリプトの疎通入力（**合成値**。書籍本文を含まない） |
| `docs/issues/feat-024-inline-math-markup-survey/m2-1-means-smoke/experiment_log.md` | 予測と実測の記録（§8 の構成） |

### 変更しないもの

- `docs/issues/feat-024-inline-math-markup-survey/m2-population-check/locate_candidates.py`（**既存。改変禁止**）
- `scripts/` 配下と `tests/` 配下のすべて

### 入力（すべて読み取りのみ。`{BASE2}` = `../survey_notes.md` §2 の定義）

| パス | 内容 |
|---|---|
| `{BASE2}/ocr/collation/feat-024_candidates.tsv` | 段1（M1）の候補 TSV（7 列・4,782 行＋ヘッダ） |
| `{BASE2}/ocr/final/chapNN/chapNN_gray300.md` | 成果物 md（全10章。`locate_candidates.py` が読む） |
| `{BASE2}/ocr/final/chapNN/chapNN_gray300_content_list.json` | content_list（全10章。同上） |

### 依存関係

```
sample_candidates.py  ──(標本 TSV)──▶  locate_candidates.py --input-sample  ──(逆引き結果 TSV)──▶ （段4 で使う）
estimate_rates.py     ◀──(計数 TSV)──  smoke_counts.tsv（合成値。段5 では段4 の判定から作る）
```

3 つのスクリプトは互いを import しない（それぞれ独立した CLI）。

## 1.3 技術スタック

- **言語**: Python 3.12（`requires-python = ">=3.12"`。`docs/TECH_STACK.md`）
- **実行**: `uv run python <パス> ...`
- **ライブラリ**: **標準ライブラリのみ**（`argparse`・`csv`・`math`・`os`・`random`・`sys`・`tempfile`・`pathlib`）。
  新規ライブラリを追加しない（`requirements.md` 制約1。`docs/TECH_STACK.md` の更新は不要）
- **選定理由**: 抽出は `random.Random(seed).sample`、区間は `math.sqrt` のみで足りるため

## 2. 入出力ファイルの一覧

| パス | 内容 | リポジトリに置くか |
|---|---|---|
| `{BASE2}/ocr/collation/feat-024_m2-1_smoke_sample.tsv` | FR-M2-1-001 の標本 TSV（**候補の文脈を含む**） | **しない**（リポジトリ外。`../roadmap.md` 前提12-b） |
| `{BASE2}/ocr/collation/feat-024_m2-1_smoke_located.tsv` | FR-M2-1-002 の逆引き結果 TSV（**同上**） | **しない** |
| `m2-1-means-smoke/smoke_counts.tsv` | FR-M2-1-003 の入力（合成値） | **する** |
| `m2-1-means-smoke/smoke_estimate.tsv` | FR-M2-1-003 の推定結果 | **する** |

## 3. 共通仕様

### 3.1 TSV の形式

- 区切りはタブ、改行は `\n`、文字コードは UTF-8（BOM なし）、**1 行目はヘッダ**
- 値にタブ・改行を含めない（候補 TSV は段1 が保証している）

### 3.2 出力の原子性

出力は**同一ディレクトリの一時ファイルに書き、`os.replace` で置換する**
（`scripts/scan_plain_math.py` の `write_tsv_atomic` と同じ方式）。

```python
# 意図の伝達のための例。そのままコピーして使うものではない
fd, tmp_name = tempfile.mkstemp(dir=out.parent, prefix=f".{out.name}.", suffix=".tmp")
with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
    f.write(content)
os.replace(tmp_name, out)
```

失敗時は一時ファイルを削除して例外を送出する。

### 3.3 共通の終了コード

| コード | 意味 |
|---|---|
| 0 | 成功（出力を書いた） |
| 1 | 入力・引数のエラー、または書き込み失敗（**出力を作らない**） |

エラーは標準エラー出力に 1 行で出す（形式は各節に示す）。

---

## 4. `sample_candidates.py` の仕様（FR-M2-1-001）

### 4.1 インターフェース

```
uv run python docs/issues/feat-024-inline-math-markup-survey/m2-1-means-smoke/sample_candidates.py \
  --candidates <候補 TSV のパス> \
  --kind {G,L,C} \
  --size <正の整数> \
  --seed <整数> \
  -o <出力 TSV のパス> \
  [--overwrite]
```

| 引数 | 型 | 必須 | 既定値 | 説明 |
|---|---|---|---|---|
| `--candidates` | `Path` | 必須 | なし | 候補 TSV のパス |
| `--kind` | `str` | 必須 | なし | 層。`argparse` の `choices=["G", "L", "C"]` |
| `--size` | `int` | 必須 | なし | 抽出件数 |
| `--seed` | `int` | 必須 | なし | 乱数シード |
| `-o` / `--out` | `Path` | 必須 | なし | 出力 TSV のパス |
| `--overwrite` | フラグ | 任意 | `False` | 出力先が既存でも上書きする |

公開関数のシグネチャ:

```python
def load_candidates_tsv(path: Path) -> list[dict]: ...      # 7 列を読み、line/offset を int 化する
def select_population(rows: list[dict], kind: str) -> list[dict]: ...
def sample_rows(population: list[dict], size: int, seed: int) -> list[dict]: ...
def write_tsv_atomic(rows: list[dict], out: Path) -> None: ...
def parse_args(argv: list[str] | None = None) -> argparse.Namespace: ...
def main(argv: list[str] | None = None) -> int: ...
```

### 4.2 データフロー

| 段階 | 型・形式・値域 |
|---|---|
| 入力 | TSV。列は `chapter`（`chap00`〜`chap09`）・`line`（1 以上の整数）・`offset`（0 以上の整数）・`kind`（`G`/`L`/`C`）・`location`（`body`/`footnote`/`table`）・`symbol`（1 文字以上の文字列）・`context`（文字列） |
| 中間 | 母集団 = `location != "table"` かつ `kind == 指定の層` の行の一覧 |
| 出力 | 入力と**同じ 7 列**の TSV（ヘッダ `chapter\tline\toffset\tkind\tlocation\tsymbol\tcontext`）。行は `(chapter, offset)` の昇順 |

### 4.3 処理ロジック

1. `parse_args` で引数を解析する
2. `--candidates` が存在するファイルでなければエラー `candidates tsv not found: <path>` を出して 1 を返す
3. 出力先の親ディレクトリが存在しなければエラー `output dir not found: <dir>` を出して 1 を返す
4. 出力先が存在し `--overwrite` が無ければエラー `output exists (use --overwrite): <path>` を出して 1 を返す
5. 候補 TSV を読む。読めなければエラー `candidates tsv unreadable: <path> (<例外>)` を出して 1 を返す
6. 母集団を作る: `location != "table"` かつ `kind == args.kind` の行だけを残す
7. 母集団を `(chapter, offset)` の昇順に**並べ替える**（入力順に依存しない正準順序にするため）
8. `--size` が母集団の件数を超えるならエラー `size <n> exceeds population size <m> for kind <K>` を出して 1 を返す
9. `rng = random.Random(args.seed)` を作り、`rng.sample(母集団, args.size)` で抽出する
10. 抽出結果を `(chapter, offset)` の昇順に並べ替える
11. §3.2 の方式で TSV を書く。書けなければエラー `write failed: <path> (<例外>)` を出して 1 を返す
12. §4.5 のサマリを標準エラー出力に出し、0 を返す

**分岐はここに挙げたものがすべてである。ループは母集団の構築と出力の整形だけで、終了条件は行数である。**

### 4.4 エラーハンドリングと境界条件

| 事象 | 検出方法 | 動作 |
|---|---|---|
| 候補 TSV が無い | `Path.is_file()` | エラー出力（§4.3 手順2）・終了コード 1 |
| 候補 TSV が読めない・列が欠ける | `OSError` / `UnicodeDecodeError` / `csv.Error` / `KeyError` / `ValueError` | エラー出力（同 手順5）・終了コード 1 |
| 出力先の親ディレクトリが無い | `Path.is_dir()` | エラー出力（同 手順3）・終了コード 1 |
| 出力先が既存で `--overwrite` 無し | `Path.exists()` | エラー出力（同 手順4）・終了コード 1 |
| `--size` が母集団超過 | 件数比較 | エラー出力（同 手順8）・終了コード 1（**出力を作らない**。FR-M2-1-001 受け入れ基準5） |
| `--size` が 0 以下 | `argparse` の後に検査 | エラー `size must be positive: <n>`・終了コード 1 |
| 母集団が 0 件 | 件数比較（手順8 に含まれる） | 同上のエラー・終了コード 1 |

### 4.5 標準エラーへのサマリ

```
sampled: kind=<K> size=<n> population=<m> seed=<s>
```

### 4.6 決定性（NFR-M2-1-001）

- 母集団を `(chapter, offset)` で並べ替えてから `random.Random(seed).sample` を呼ぶため、
  入力ファイルの行順に依存しない
- 同じ引数での再実行は**バイト一致**する（§7 手順4 で確認する）

---

## 5. `locate_candidates.py --input-sample` の実行（FR-M2-1-002）

**既存スクリプトを変更しない。** 実行するだけである。

```
uv run python docs/issues/feat-024-inline-math-markup-survey/m2-population-check/locate_candidates.py \
  --candidates <候補 TSV のパス> \
  --final-root {BASE2}/ocr/final \
  --input-sample <標本 TSV のパス> \
  -o <出力 TSV のパス> \
  [--overwrite]
```

- `--candidates` には**母集団全体の候補 TSV** を渡す（章内候補列の構築に使うため。`--input-sample` と併用する）
- `--sample-size` / `--seed` は指定しない（`--input-sample` と排他）
- 出力 TSV の列（11 列）: `chapter`・`line`・`offset`・`kind`・`location`・`symbol`・`context`・`stage`・`block_index`・`page_idx`・`reason`
- `stage` の値域: `block` / `page` / `none`。特定できない `block_index`・`page_idx` は `-1`
- **確認1（入力の引き継ぎ。FR-M2-1-002 受け入れ基準2）**: 出力のデータ行の**先頭 7 列**が、入力した標本 TSV のデータ行と**完全に一致**すること（タブ区切りの文字列として比較する）
- **確認2（既存スクリプトの不変。同 受け入れ基準5）**: 実行後に `git diff -- docs/issues/feat-024-inline-math-markup-survey/m2-population-check/locate_candidates.py` が空であること

---

## 6. `estimate_rates.py` の仕様（FR-M2-1-003）

### 6.1 インターフェース

```
uv run python docs/issues/feat-024-inline-math-markup-survey/m2-1-means-smoke/estimate_rates.py \
  --counts <計数 TSV のパス> \
  -o <出力 TSV のパス> \
  [--overwrite]
```

```python
def load_counts_tsv(path: Path) -> list[dict]: ...
def wilson_interval(k: int, n_eff: int, population: int) -> tuple[float, float, float]: ...  # (p_hat, ci_lo, ci_hi)
def write_tsv_atomic(rows: list[dict], out: Path) -> None: ...
def parse_args(argv: list[str] | None = None) -> argparse.Namespace: ...
def main(argv: list[str] | None = None) -> int: ...
```

### 6.2 入力の形式

ヘッダ `layer\tpopulation\tk\tn_eff`。1 行が 1 層。

| 列 | 型 | 値域 |
|---|---|---|
| `layer` | `str` | 任意の識別子（段5 では `G` / `L` / `C`） |
| `population` | `int` | 2 以上（有限母集団修正の分母 `N − 1` が正である必要があるため） |
| `k` | `int` | `0 ≤ k ≤ n_eff` |
| `n_eff` | `int` | `1 ≤ n_eff ≤ population` |

### 6.3 算出の式（`../survey_notes.md` §9.1）

`z = 1.959964`（定数。95%）とし、`p̂ = k / n'` として次を計算する。

```
center = (p̂ + z²/(2n')) / (1 + z²/n')
half   = z/(1 + z²/n') × sqrt( p̂(1−p̂)/n' + z²/(4n'²) )
fpc    = sqrt( (N − n') / (N − 1) )
half   ← half × fpc
ci_lo  = max(0.0, center − half)
ci_hi  = min(1.0, center + half)
est_count = N × p̂
est_lo    = N × ci_lo
est_hi    = N × ci_hi
```

**Wald 法は使わない**（`../survey_notes.md` §9.1）。

### 6.4 出力の形式

ヘッダ `layer\tpopulation\tk\tn_eff\tp_hat\tci_lo\tci_hi\test_count\test_lo\test_hi`。

| 列 | 書式 |
|---|---|
| `layer`・`population`・`k`・`n_eff` | 入力のまま |
| `p_hat`・`ci_lo`・`ci_hi` | 小数**12 桁**固定（`f"{v:.12f}"`） |
| `est_count`・`est_lo`・`est_hi` | 小数**6 桁**固定（`f"{v:.6f}"`） |

行の順序は入力の順序を保つ。

### 6.5 エラーハンドリングと境界条件

| 事象 | 動作 |
|---|---|
| 計数 TSV が無い | エラー `counts tsv not found: <path>`・終了コード 1 |
| 計数 TSV が読めない・列が欠ける | エラー `counts tsv unreadable: <path> (<例外>)`・終了コード 1 |
| 出力先の親が無い / 既存で `--overwrite` 無し | §3.3 と同じ形式のエラー・終了コード 1 |
| `n_eff < 1` | エラー `invalid row (n_eff must be >= 1): layer=<L>`・終了コード 1（**出力を作らない**） |
| `k < 0` または `k > n_eff` | エラー `invalid row (require 0 <= k <= n_eff): layer=<L>`・終了コード 1 |
| `n_eff > population` または `population < 2` | エラー `invalid row (require 2 <= population and n_eff <= population): layer=<L>`・終了コード 1 |
| 入力が 0 行（ヘッダのみ） | エラー `counts tsv has no data row: <path>`・終了コード 1 |

**検査はすべての行について書き込み前に行う**（1 行でも不正なら出力を作らない）。

### 6.6 疎通に使う入力と、照合する手計算値

`smoke_counts.tsv`（本マイルストーンフォルダに置く。**合成値**）:

```
layer	population	k	n_eff
G	291	1	2
```

この入力に対する**手計算値**（`z = 1.959964`、§6.3 の式に代入した値。IEEE 754 倍精度）:

| 列 | 値 |
|---|---|
| `p_hat` | `0.500000000000` |
| `ci_lo` | `0.095230892469` |
| `ci_hi` | `0.904769107531` |
| `est_count` | `145.500000` |
| `est_lo` | `27.712190` |
| `est_hi` | `263.287810` |

（中間値: `center = 0.5`、`fpc = 0.998274373175`、`half = 0.404769107531`）

**`n_eff = 2` を選んだ理由**: `n_eff = 1` では `fpc = sqrt(290/290) = 1` となり有限母集団修正が検算されないため。
`p̂ = 0.5` は Wilson 区間が最も広くなる点であり、桁落ちの影響を受けにくい。

---

## 7. 実行手順（3 手段の単体疎通）

`{BASE2}` = `/home/sakagawa/work/確率統計`（`../survey_notes.md` §2）。
`{REPO}` = 本リポジトリのルート。**作業ディレクトリは `{REPO}`** とする。

**手順1（FR-M2-1-001）**

```
uv run python docs/issues/feat-024-inline-math-markup-survey/m2-1-means-smoke/sample_candidates.py \
  --candidates "{BASE2}/ocr/collation/feat-024_candidates.tsv" \
  --kind G --size 1 --seed 20260907 \
  -o "{BASE2}/ocr/collation/feat-024_m2-1_smoke_sample.tsv"
```

確認: 出力が 2 行（ヘッダ＋データ 1 行）であること。データ行の `kind` が `G`、`location` が `table` でないこと。
`(chapter, offset)` の組で候補 TSV に同じ 7 列の行が存在すること。

**手順2（FR-M2-1-002）**

```
uv run python docs/issues/feat-024-inline-math-markup-survey/m2-population-check/locate_candidates.py \
  --candidates "{BASE2}/ocr/collation/feat-024_candidates.tsv" \
  --final-root "{BASE2}/ocr/final" \
  --input-sample "{BASE2}/ocr/collation/feat-024_m2-1_smoke_sample.tsv" \
  -o "{BASE2}/ocr/collation/feat-024_m2-1_smoke_located.tsv"
```

確認: 出力が 2 行で、11 列。
**出力データ行の先頭 7 列が、手順1 の標本 TSV のデータ行と完全に一致**すること
（例: `cut -f1-7` の結果どうしを `diff` して無出力であること）。
`stage` が `block` / `page` / `none` のいずれか。`stage` が `block` または `page` なら `page_idx >= 0`。
`git diff -- docs/issues/feat-024-inline-math-markup-survey/m2-population-check/locate_candidates.py` が空。

**手順3（FR-M2-1-003）**

```
uv run python docs/issues/feat-024-inline-math-markup-survey/m2-1-means-smoke/estimate_rates.py \
  --counts docs/issues/feat-024-inline-math-markup-survey/m2-1-means-smoke/smoke_counts.tsv \
  -o docs/issues/feat-024-inline-math-markup-survey/m2-1-means-smoke/smoke_estimate.tsv
```

確認: 出力が 2 行で、6 つの算出値が §6.6 の手計算値と一致すること（一致の幅は `../roadmap.md` §6）。

**手順4（NFR-M2-1-001。3 手段の再現性）**

手順1〜3 をそれぞれ**別のパスに出力して再実行**し、`diff` が無出力であることを確認する
（出力先に `.rerun` を付けたパスを使い、確認後に再実行分のファイルを削除する）。

**手順5（境界条件の確認。FR-M2-1-001 受け入れ基準5・FR-M2-1-003 受け入れ基準3）**

1. `--kind G --size 999999` で `sample_candidates.py` を実行し、終了コードが 1 で出力が作られないこと
2. `estimate_rates.py` の**不正な入力 3 通り**について、終了コードが 1 で出力が作られないこと。
   いずれも `layer	population	k	n_eff` のヘッダと 1 行だけを書いた一時ファイルを `/tmp/claude-1000/` 配下に作って与え、確認後に削除する
   - `X	291	3	2`（`k > n_eff`）
   - `X	291	0	0`（`n_eff < 1`）
   - `X	291	1	292`（`n_eff > population`）

## 7.1 テスト

- **自動テスト**: 本マイルストーンで新設するのは案件固有の実験コードであり、`tests/` にテストを追加しない（ADR-M2-1-1）
- **回帰の確認**: `uv run pytest -v` を**全件実行**し、出力をそのまま
  `tests/results/feat-024_test_result.txt` に保存する（マイルストーンごとに上書きする。`CLAUDE.md`「テスト」）。
  既存の 260 件がすべて成功することを確認する
- **既存データの不変（NFR-M2-1-003）**: 本マイルストーンは `{BASE2}/ocr/collation/` にのみ書き込む。
  実行前後で `{BASE2}` の `dewarping/`・`ocr/final/`・`ocr/fixes/`・`ocr/mineru-full/` を変更しない
  （これらのディレクトリに書き込むコードを書かない）

## 8. `experiment_log.md` の構成

`CLAUDE.md`「実験・検証の進め方」に従い、**各手段の実行直前に予測を記録してから実行する**
（3 手段を一括で先に予測しない）。

```markdown
# feat-024 M2-1 実験ログ
- 判定基準: ../roadmap.md §6 の段2 の想定値と外れの幅（本ログに閾値を再掲しない）
- 手順: design.md §7

## 手段1: sample_candidates.py
### 予測（実行前に記録）  … 出力行数・kind・location・終了コードの予測と、その根拠
### 実測               … 実際の出力（**書籍本文は書かない**。行数・列の値・終了コードのみ）
### 照合               … 一致 / 乖離と、乖離の原因

## 手段2: locate_candidates.py --input-sample
（同じ 3 節）

## 手段3: estimate_rates.py
（同じ 3 節。手計算値〔design.md §6.6〕と実測の相対差を記録する）

## 判定
3 手段の疎通の可否と、../roadmap.md §6 の段2 の想定値との照合結果
```

**書籍本文（`symbol`・`context` の値）をログに書かない**（`../roadmap.md` 前提12-b）。

## 9. 中断規則（想定外事象）

次のいずれかが起きたら、**その場で回避策を実装せず直ちに中断**し、何が起きたか・どこまで完了したかを報告する
（`CLAUDE.md`「実装の実行方法」項目3）。

1. 本書のとおりに実装・実行できない（引数・入力・出力の記述が実体と合わない）
2. 既存 `locate_candidates.py` の変更が必要になった
3. `uv run pytest -v` に失敗がある
4. §6.6 の手計算値と実測が一致しない
5. `{BASE2}` の既存データ 4 ディレクトリへの書き込みが必要になった

## 10. 設計判断の記録（ADR）

### ADR-M2-1-1: 新規スクリプトの置き場は**マイルストーンフォルダ**とする

- **採用**: `m2-1-means-smoke/` 配下に置く（`tests/` にテストを追加しない）
- **却下**: `scripts/` 配下に置く（テスト付きのプロダクトコードとする）
- **理由**: `CLAUDE.md`「ドキュメント作成ルール」の判定は「その案件が終わった後も使うか」である。
  `sample_candidates.py` は feat-024 の候補 TSV の 7 列形式に、`estimate_rates.py` は本調査の層構成に依存し、
  **案件の完了後に他の入力で使う見込みがない**。既存 `locate_candidates.py` も同じ判定で
  `m2-population-check/` に置かれている（M2 の ADR-M2-2）

### ADR-M2-1-2: 抽出は**母集団を正準順序に並べ替えてから** `random.Random(seed).sample` を使う

- **採用**: `(chapter, offset)` 昇順に並べ替えてから `sample`
- **却下**: 入力ファイルの行順のまま `sample` する／`random.shuffle` を使う
- **理由**: 入力の行順に依存しない再現性を得るため（NFR-M2-1-001）。
  既存 `locate_candidates.py` の `--sample-size` も同じ方式（`population_sorted` を作ってから `rng.sample`）であり、揃える

### ADR-M2-1-3: 推定の入力を**計数 TSV**（`layer`・`population`・`k`・`n_eff`）とする

- **採用**: 層ごとの計数を 1 行に持つ TSV を入力にする
- **却下**: 段4 の判定 TSV（1 標本 1 行）を直接入力にする
- **理由**: 判定 TSV には**書籍本文が含まれる**ためリポジトリ内で扱えない（`../roadmap.md` 前提12-b）。
  計数に落とせば書籍本文を含まず、段5 でもそのまま使える。集計（判定 TSV → 計数）は段5 の設計で定める

### ADR-M2-1-4: 疎通の入力に `k=1, n'=2, N=291` を使う

- **採用**: 合成値 `k=1, n'=2, N=291`
- **却下**: 実データ（段4 の判定）を使う／`n'=1` を使う
- **理由**: 段4 は未実施であり実データが無い。`n'=1` では有限母集団修正が `1` になり検算にならない（§6.6）
