# feat-023 機能設計書: Q&A コラム見出しの意味に影響する数式記号の欠落2件の修正

対象案件: `docs/issues/feat-023-qa-heading-math-semantics/`
要求仕様書: 同フォルダの `requirements.md`
調査記録: 同フォルダの `README.md`

## 1. 対応要求マッピング

| 要求 | 設計箇所 |
|---|---|
| FR-001 修正定義ファイルへの追記（4件） | §4（追記内容）・§5（一意性の確認）・§6 手順1 |
| FR-002 対象2行を原本の数式表記と一致させる | §4.2（4件の `old`/`new`）・§7 手順1 |
| FR-003 既存成果物への適用と final 再構築 | §6（適用手順）・§7（確認手順） |
| FR-004 影響範囲の限定 | §3（変更しないもの）・§6 手順A（不変対象マニフェスト）・§7 手順3 |
| FR-005 後続案件案 F への引き渡し | §11（BACKLOG・CHANGELOG への記載）・§12 |

## 2. システム構成

本案件は**リポジトリ内のコードを変更しない**。既存スクリプトを引数を変えて実行するのみである。

```
{BASE2} = /home/sakagawa/work/確率統計
対象2章 NN ∈ {06, 08}

{NORM_NN}  = {BASE2}/ocr/mineru-full/chapNN/run-01-normalized
{FINAL_NN} = {BASE2}/ocr/final/chapNN
{FIXES_NN} = {BASE2}/ocr/fixes/chapNN.json   ← 本案件で各2件追記（リポジトリ外・作成済み）

  {NORM_NN}/chapNN_gray300.md ──┐
                                ├─→ apply_fixes.py ──→ {NORM_NN}/chapNN_gray300.md（インプレース更新）
  {FIXES_NN} ───────────────────┘

  {NORM_NN}/（md + content_list.json + images/）
        └─→ build_final.py ──→ {FINAL_NN}/（再構築・3種類の機械検証）
```

### 2.1 `{NORM_NN}` の確認

**chap06・chap08 はいずれも `run-01` のみが存在する**（2026-09-06 実測。各章の
`{BASE2}/ocr/mineru-full/chapNN/` の内容は `run-01` / `run-01-normalized` / `run-01.log` の3つ）。

**feat-020 で chap07 だけ `run-02` があり final のコピー元が `run-02-normalized` だった事例がある**
（`docs/PROJECT_KNOWLEDGE.md` 記載）。本案件の対象2章は該当しないが、実装時に必ず
`ls {BASE2}/ocr/mineru-full/chapNN/` を実行して `run-01-normalized` が唯一かつ最大の run 番号で
あることを確認する。異なっていた場合は中断して報告する。手順0 の `md_identical` 検査でも検出できる。

### 2.2 処理の単位と順序

**章単位で「直前確認（手順0-B）→ 追記 → 適用 → final 再構築」を完結させ、2章を次の順に処理する。**

```
chap06 → chap08
```

（手順A の不変対象マニフェストと手順0 の事前確認は、2章の処理を始める前に**一度だけ**行う。）

- 章の処理が失敗した場合、**その章のみを退避から復元し、後続の章には進まず中断して報告する**
  （§6「失敗時の復元」）。既に完了した章はそのままでよい
- 順序に技術的な依存はない（章間に干渉がないことは §5.4 で示す）。再現性のために章番号順に固定する

## 3. 変更しないもの（FR-004）

| 対象 | 理由 |
|---|---|
| `scripts/` 配下のすべてのファイル | 本案件はデータ側の修正のみで実現できる |
| `tests/test_*.py`（テストコード） | コード変更がないため。ただし `tests/results/feat-023_test_result.txt` は検証記録として**新規作成する**（§7 手順4） |
| **`CLAUDE.md`** | update-003 の非対称ルール。本案件の知見は `docs/PROJECT_KNOWLEDGE.md` に追記する（§11） |
| 各 `{NORM_NN}/chapNN_gray300_content_list.json` | `apply_fixes.py` は md のみを対象とする（feat-010 の設計）。§8 の非対称性 |
| 各 `{NORM_NN}/images/`・`{FINAL_NN}/images/` | 画像は対象外（chap06 = 19 / chap08 = 43 ファイル） |
| 既存の fix 計10件（chap06-001〜007・chap08-001〜003） | 先行案件で作成・適用済み。本案件では追記のみ |
| `{BASE2}/ocr/fixes/` の他8ファイル（chap00・01・02・03・04・05・07・09） | 本案件の対象外 |
| 確率統計の非対象8章の成果物 | 同上 |
| PRML（`{BASE}`）の成果物 | 本案件は確率統計のみを対象とする |
| **対象2行以外の行** | 変更は chap06 253 行と chap08 285 行の2行のみ（FR-004 基準8） |
| **対象2行以外の `D4` 16件** | 後続案件案 F に残す（FR-005・§12） |
| **`docs/issues/feat-021-qa-heading-source-collation/collation_summary.md`** | feat-021 の成果物であり、確定した突合結果の記録である（FR-005 基準3） |
| **見出し記号（`## ? 6.3` / `## ? 8.3`）** | feat-020 で確定済み。`old`/`new` に含めない（ADR-3） |

## 4. 修正定義ファイルへの追記内容（FR-001）

### 4.1 追記の方法と追記前の状態

**既存 JSON を読み込み、`fixes` 配列の末尾に新規 fix を `append` して書き戻す。**
既存要素（4キー）を1文字も変更してはならない。

追記の**前**に、対象ファイルが下表の状態であることを SHA-256 と fix 一覧で確認する。
**異なっていた場合は上書きせず中断して報告する。**

| ファイル | 追記前の SHA-256（2026-09-06 実測） | 既存 fix 数 | 既存 ID |
|---|---|---|---|
| `chap06.json` | `3383cf6e22cc8666fa6cfd1090661572d57d039aeae4ed6098802f053a8e777b` | 7 | `chap06-001`〜`007` |
| `chap08.json` | `8f838fcd311fd7b47e9ab32fa88dfb28c97b54f1e1f8f27807c07c9155b75e89` | 3 | `chap08-001`〜`003` |

追記後の `fixes` 配列の要素数は chap06 = **9**、chap08 = **5** になる。

**既存 fix の内容は本書に転記しない**（複数行文字列と 64 桁の画像ハッシュを含むため、転記は
誤りを持ち込む risk がある）。上表の SHA-256 の一致をもって確認とする（feat-022 ADR-5・feat-020 ADR-6 と同じ判断）。

書式は `fixes/template.json`・`fixes/README.md` に従う（キーは `id` / `reason` / `old` / `new` の
4つ、すべて文字列。JSON はインデント2・`ensure_ascii=False`・末尾改行ありで書き出す）。

**JSON 内でのバックスラッシュのエスケープに注意する。** 本案件の `new` は LaTeX を含むため、
JSON 文字列としては `\\theta` / `\\hat{\\theta}` / `\\boldsymbol` のように書く（読み込んだ Python
文字列としては `\theta` / `\hat{\theta}` / `\boldsymbol` になる）。**追記後に必ず読み込み直して、
Python 文字列が §4.2 の表と一致することを確認する**（§6 手順1）。

### 4.2 新規 fix（4件）

以下の4つのオブジェクトを、それぞれ対応するファイルの `fixes` 配列の末尾に追加する。
**`old` / `new` の値は Python 文字列として示す**（JSON に書くときはバックスラッシュを二重にする）。

#### `chap06-008`（chap06 6.3・「種目 θ」の数式マークアップ）

| キー | 値 |
|---|---|
| `old` | `あらゆる種目 θ で` |
| `new` | `あらゆる種目 $\theta$ で` |
| `reason` | Q&A コラム見出し「? 6.3」（原本 page-07_1L.tif）の質問文で、原本は数式組版の `$\theta$` だが md では平文の `θ` になっていた（原本 TIF 目視確認済み・feat-021 の突合および本案件での再確認）。同じ行の `chap06-009`（推定量のハット）を復元すると同一文に平文の θ と数式の $\hat{\theta}$ が混在するため、本件も併せて数式にする（2026-09-06 ユーザー決定）。直前の「あらゆる種目 」と直後の「 で」を含めて一意にしている（feat-023） |

#### `chap06-009`（chap06 6.3・**推定量のハットの復元**）

| キー | 値 |
|---|---|
| `old` | `の推定量 θ を探さない` |
| `new` | `の推定量 $\hat{\theta}$ を探さない` |
| `reason` | Q&A コラム見出し「? 6.3」（原本 page-07_1L.tif）の質問文で、原本は推定量を表すハット付きの `$\hat{\theta}$` だが md では素の `θ` になっており、**ハットが失われて θ（真のパラメータ）と θ̂（その推定量）の区別が消えていた**（原本 TIF 目視確認済み・feat-021 の突合および本案件での再確認）。chap06 は `\hat{\theta}` を24箇所で使っており、本見出しだけが失われていた。「推定量 θ」は chap06 に1件しかないが、再 OCR 時の取り違えを防ぐため直前の「の」と直後の「 を探さない」まで含めて一意にしている（feat-023） |

#### `chap08-004`（chap08 8.3・「第 i」の数式マークアップ）

| キー | 値 |
|---|---|
| `old` | `第 i 主成分が $z_` |
| `new` | `第 $i$ 主成分が $z_` |
| `reason` | Q&A コラム見出し「? 8.3」（原本 page-06_2R.tif）の質問文で、原本は数式組版の `$i$` だが md では平文の `i` になっていた（原本 TIF 目視確認済み・feat-021 の突合および本案件での再確認）。同じ行の `chap08-005`（太字ベクトル）と併せて行全体を原本に一致させる（2026-09-06 ユーザー決定）。**「第 i 主成分」は chap08 に6件あるため**、直後の「が $z_」まで含めて一意にしている（feat-023） |

#### `chap08-005`（chap08 8.3・**太字ベクトル記法の復元**）

| キー | 値 |
|---|---|
| `old` | `$z_{i}=q_{i}\cdot x$` |
| `new` | `$z_{i}=\boldsymbol{q}_{i}\cdot\boldsymbol{x}$` |
| `reason` | Q&A コラム見出し「? 8.3」（原本 page-06_2R.tif）の質問文で、原本は `$z_{i}=\boldsymbol{q}_{i}\cdot\boldsymbol{x}$` と `q_i`・`x` が太字（ベクトル）だが md では素の記号になっており、**ベクトルとスカラーの区別が消えていた**（原本 TIF 目視確認済み・feat-021 の突合および本案件での再確認）。`z_i = q_i · x` は「ベクトル q_i とベクトル x の内積がスカラー z_i」という式であり、太字の有無で意味が変わる。chap08 は `\boldsymbol` を122箇所で使っており、本見出しだけが失われていた。数式全体（`$…$` 込み）を old にすることで一意になる（feat-023） |

### 4.3 適用前後の md の該当行（実測・2026-09-06）

| 章 | 行 | 適用前（現状） |
|---|---|---|
| chap06 | 253 | `## ? 6.3 あらゆる種目 θ ですべてのライバルを凌駕する全種目征覇なスーパーチャンピオンの推定量 θ を探さないといけないわけですか。がんばって探してみますね。` |
| chap08 | 285 | `## ? 8.3 第 i 主成分が $z_{i}=q_{i}\cdot x$ で求められるのはなぜ？` |

| 章 | 行 | 適用後（期待。**FR-002 基準1・2 の完全一致の対象**） |
|---|---|---|
| chap06 | 253 | `## ? 6.3 あらゆる種目 $\theta$ ですべてのライバルを凌駕する全種目征覇なスーパーチャンピオンの推定量 $\hat{\theta}$ を探さないといけないわけですか。がんばって探してみますね。` |
| chap08 | 285 | `## ? 8.3 第 $i$ 主成分が $z_{i}=\boldsymbol{q}_{i}\cdot\boldsymbol{x}$ で求められるのはなぜ？` |

**見出し記号（`## ? 6.3` / `## ? 8.3`）は変わらない**（feat-020 で確定済み。ADR-3）。

### 4.4 原本の確認（2026-09-06 実施）

feat-021 の突合記録（`{BASE2}/ocr/collation/feat-021_qa_headings.md`。リポジトリ外）に加え、
**本案件として `scripts/crop_blocks.py` で原本 TIF から切り出して独立に再確認した**。

| 章 | content_list の index | `type` / `text_level` | `page_idx` | 原本 TIF | 確認した内容 |
|---|---|---|---|---|---|
| chap06 | 136 | `text` / 2 | 11 | `page-07_1L.tif` | 1つめの θ は素、**2つめの θ にはハットが付いている**（θ̂） |
| chap08 | 150 | `text` / 2 | 10 | `page-06_2R.tif` | `z_i` と添字 `i` は細字イタリック、**`q_i` と `x` は太字イタリック**（ベクトル） |

確認の手順（再実行可能）:

```bash
uv run python scripts/crop_blocks.py \
  /home/sakagawa/work/確率統計/ocr/final/chap06/chap06_gray300_content_list.json \
  /home/sakagawa/work/確率統計/dewarping/chap06/out \
  -o "$SCRATCH/crops/chap06" --index 136 --margin 12 --max-width 1700
```

（chap08 は index 150。）**実装フェーズでの再実行は必須としない。**

### 4.5 `old` / `new` の設計

- `old` は「対象の記号 ＋ 一意性が確保できる最小限の文脈」とする。文脈を長くするほど
  再 OCR 時に文面が変わって `old` が一致しなくなる（feat-019 ADR-2・feat-022 §4.5 と同じ判断）
- **`chap08-004` のみ文脈が必須**である。「第 i 主成分」は chap08 に **6件**あるため、
  直後の「が $z_」まで含めて一意化した。他の3件は誤りの箇所自体が章内で一意だが、
  再 OCR 耐性のために短い文脈を付けている
- **見出し記号（`##`・`?`・番号）を `old` / `new` に含めない**（ADR-3）
- **1行につき2件の fix に分ける**（1行を丸ごと置換する1件にしない）。理由は ADR-2

## 5. 一意性の確認（FR-001 受け入れ基準 5・6）

`apply_fixes.py` は適用後に**全 fix について `count(old) == 0` かつ `count(new) == 1`** を検査し、
1つでも破れていればエラー終了して出力を書かない（最終不変条件。feat-010 FR-003 規則6）。
そのため `old` の一意性だけでなく、**適用後に `new` がちょうど1件になることも事前に数える**
（`docs/PROJECT_KNOWLEDGE.md` の規定）。

2026-09-06 に各 `{NORM_NN}/chapNN_gray300.md`（= 対応する `{FINAL_NN}` の md とバイト同一）で実測した。

### 5.1 新規4件（章内での出現回数）

| fix | 文字列 | 適用前 | 適用後（実測） |
|---|---|---|---|
| `chap06-008` | `old` = `あらゆる種目 θ で` | **1** | 0 |
| `chap06-008` | `new` = `あらゆる種目 $\theta$ で` | **0** | **1** |
| `chap06-009` | `old` = `の推定量 θ を探さない` | **1** | 0 |
| `chap06-009` | `new` = `の推定量 $\hat{\theta}$ を探さない` | **0** | **1** |
| `chap08-004` | `old` = `第 i 主成分が $z_` | **1** | 0 |
| `chap08-004` | `new` = `第 $i$ 主成分が $z_` | **0** | **1** |
| `chap08-005` | `old` = `$z_{i}=q_{i}\cdot x$` | **1** | 0 |
| `chap08-005` | `new` = `$z_{i}=\boldsymbol{q}_{i}\cdot\boldsymbol{x}$` | **0** | **1** |

### 5.2 既存10件（追記後も最終不変条件を満たすこと）

新規 fix を適用した後の md に対し、当該章の**全 fix**（既存 ＋ 新規）について
`count(old) == 0` かつ `count(new) == 1` を検算した結果、**違反は2章とも0件**であった（2026-09-06 実測）。

| 章 | 検査した fix 数（既存 ＋ 新規） | 最終不変条件の違反 |
|---|---|---|
| chap06 | 7 + 2 = 9 | **なし** |
| chap08 | 3 + 2 = 5 | **なし** |

### 5.3 干渉が起きないことの根拠（章内・同一行）

**本案件は1行に2件の fix を当てるため、同一行内での干渉を特に確認した。**

- **chap06**: `chap06-008` の `old`（`あらゆる種目 θ で`）と `chap06-009` の `old`
  （`の推定量 θ を探さない`）は、同じ行の**異なる位置**にあり文字列として重ならない。
  互いの `new` にも含まれない。したがって適用順に依存しない
- **chap08**: `chap08-004` の `old`（`第 i 主成分が $z_`）は `chap08-005` の `old`
  （`$z_{i}=q_{i}\cdot x$`）と **`$z_` の3文字が隣接するが重複しない**
  （`chap08-004` は `$z_` までで終わり、`chap08-005` は `$z_{i}=…` から始まる）。
  **どちらを先に適用しても、他方の `old` は影響を受けない**:
  - `chap08-004` を先に適用 → 行は `第 $i$ 主成分が $z_{i}=q_{i}\cdot x$ …` になり、
    `chap08-005` の `old` はそのまま残る
  - `chap08-005` を先に適用 → 行は `第 i 主成分が $z_{i}=\boldsymbol{q}_{i}\cdot\boldsymbol{x}$ …` になり、
    `chap08-004` の `old`（`第 i 主成分が $z_`）はそのまま残る
- 新規4件の `old` / `new` は、当該章の既存 fix の `old` / `new` と文字列として重ならない
- 上記はすべて §5.1・§5.2 の実測（全 fix が適用後 `count(old) == 0` かつ `count(new) == 1`）で確認済みである

**`apply_fixes.py` は修正定義ファイルの記載順に逐次適用する**（`scripts/apply_fixes.py` の
`apply_fixes()` を確認）。本案件では `chap06-008` → `chap06-009`、`chap08-004` → `chap08-005` の順に
記載するが、上記のとおり順序に依存しない。

### 5.4 干渉が起きないことの根拠（章間）

`apply_fixes.py` は **md 1ファイルと修正定義ファイル1件**を受け取り、そのファイル内でのみ
`str.count()` / `str.replace()` を行う（feat-010 の設計）。したがって章をまたぐ干渉は原理的に起きない。

### 5.5 適用による文字数・行数の変化（実測）

| 章 | 新規 fix | 文字数（前 → 後） | 内訳 | 行数（前 → 後） |
|---|---|---|---|---|
| chap06 | 2 | 36399 → **36419**（+20） | `θ` → `$\theta$`（+7）、`θ` → `$\hat{\theta}$`（+13） | 833 → **833** |
| chap08 | 2 | 67202 → **67229**（+27） | `i` → `$i$`（+2）、`q_{i}`→`\boldsymbol{q}_{i}`・`x`→`\boldsymbol{x}`（+25） | 1566 → **1566** |

## 6. 適用手順（FR-003）

### 作業用ディレクトリ `{SCRATCH}` の定義

本書で `{SCRATCH}` と書いた箇所は、**Claude Code のセッション用スクラッチパッド**
（`/tmp/claude-1000/-home-sakagawa-git-honOCR/{session-id}/scratchpad/feat023/`）を指す。
成果物ディレクトリ（`{BASE2}` 配下）とリポジトリの**外**であり、実装の冒頭で作成する。

```bash
SCRATCH=/tmp/claude-1000/-home-sakagawa-git-honOCR/{session-id}/scratchpad/feat023
mkdir -p "$SCRATCH"
```

**本書のシェルコマンド中では `{SCRATCH}` ではなくシェル変数 `"$SCRATCH"` の形で書いてある。
`{SCRATCH}` は本文の説明でのみ用いる記法であり、コマンドにそのまま貼り付けてはならない。**

**MinerU（`ocr_dir.py`）と `normalize_punct.py` は実行しない。**

### 手順A: 不変対象マニフェストの記録（最初に一度だけ）

FR-004 基準3・4・5 の対象のうち、**`git` 管理外のため `git status` では変更を検出できない
ファイル群**について、SHA-256 のマニフェストを記録する。対象は次の**641ファイル**である。

- `{BASE2}/ocr/fixes/` の他8ファイル（`chap00`・`chap01`・`chap02`・`chap03`・`chap04`・
  `chap05`・`chap07`・`chap09` の各 `.json`）… 8ファイル
- 確率統計の非対象8章（chap00・01・02・03・04・05・07・09）の `final/chapNN/` 配下の全通常ファイル（再帰）
- PRML（`{BASE}`）の `ocr/final/chap00〜07/` 配下の全通常ファイル（再帰）

```bash
uv run python -c "
import hashlib
from pathlib import Path
B2 = Path('/home/sakagawa/work/確率統計/ocr')
B1 = Path('/home/sakagawa/work/Pattern_Recognition_and_Machine_Learning/ocr')
OTHERS = ['00','01','02','03','04','05','07','09']
paths = [B2/'fixes'/f'chap{n}.json' for n in OTHERS]
for n in OTHERS:
    paths += [p for p in (B2/'final'/f'chap{n}').rglob('*') if p.is_file()]
for d in sorted((B1/'final').iterdir()):
    if d.is_dir():
        paths += [p for p in d.rglob('*') if p.is_file()]
lines = [f'{p}\t{hashlib.sha256(p.read_bytes()).hexdigest()}' for p in sorted(paths)]
manifest = chr(10).join(lines) + chr(10)
print(manifest, end='')
print('files =', len(lines))
print('AGGREGATE', hashlib.sha256(manifest.encode()).hexdigest())
" | tee "$SCRATCH/invariant_manifest_before.txt"
```

期待値（2026-09-06 実測）:

- `files = 641`
- `AGGREGATE = 82797d011e9bf26172ee4e0f3749096ba6a4b1d88a0ff2011d6402657356e420`

**この2値が期待と異なる場合は、その場で回避策を取らず中断して報告する。**

### 手順0: 事前確認（2章の処理を開始する前に**一度だけ**行う）

```bash
uv run python -c "
import hashlib, json
from pathlib import Path
B2 = Path('/home/sakagawa/work/確率統計')
EXP = {
 'chap06': dict(chars=36399, lines=833, images=19, nfix=7, ln=253,
   cl='f41ce4ca1b838792ede2a985ac08466fb5fdcc6ccc1704d02355ce903bd99860',
   fx='3383cf6e22cc8666fa6cfd1090661572d57d039aeae4ed6098802f053a8e777b',
   olds=['あらゆる種目 θ で', 'の推定量 θ を探さない'],
   news=['あらゆる種目 \$\\\\theta\$ で', 'の推定量 \$\\\\hat{\\\\theta}\$ を探さない']),
 'chap08': dict(chars=67202, lines=1566, images=43, nfix=3, ln=285,
   cl='7febf605cd86d279257d4d6c519bf626cf028d06c4147ac0703a391a61c83426',
   fx='8f838fcd311fd7b47e9ab32fa88dfb28c97b54f1e1f8f27807c07c9155b75e89',
   olds=['第 i 主成分が \$z_', '\$z_{i}=q_{i}\\\\cdot x\$'],
   news=['第 \$i\$ 主成分が \$z_', '\$z_{i}=\\\\boldsymbol{q}_{i}\\\\cdot\\\\boldsymbol{x}\$']),
}
h = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
ok = True
for ch, e in EXP.items():
    norm = B2/f'ocr/mineru-full/{ch}/run-01-normalized'
    fin  = B2/f'ocr/final/{ch}'
    mdn, mdf = norm/f'{ch}_gray300.md', fin/f'{ch}_gray300.md'
    cln, clf = norm/f'{ch}_gray300_content_list.json', fin/f'{ch}_gray300_content_list.json'
    fx = B2/f'ocr/fixes/{ch}.json'
    t = mdn.read_text(encoding='utf-8')
    r = dict(md_identical=mdn.read_bytes()==mdf.read_bytes(), chars=len(t),
             lines=len(t.split(chr(10))), images=len(list((fin/'images').iterdir())),
             olds=[t.count(o) for o in e['olds']], news=[t.count(n) for n in e['news']],
             nfix=len(json.loads(fx.read_text(encoding='utf-8'))['fixes']))
    good = (r['md_identical'] and r['chars']==e['chars'] and r['lines']==e['lines']
            and r['images']==e['images'] and r['nfix']==e['nfix']
            and r['olds']==[1,1] and r['news']==[0,0]
            and h(cln)==e['cl'] and h(clf)==e['cl'] and h(fx)==e['fx'])
    ok = ok and good
    print(ch, 'OK' if good else 'MISMATCH', r)
print('ALL_OK' if ok else 'ABORT')
"
```

期待値: 2章とも `OK` で、最終行が `ALL_OK`。内訳は次のとおり。

| 章 | `md_identical` | `chars` | `lines` | `olds` | `news` | `images` | `nfix` |
|---|---|---|---|---|---|---|---|
| chap06 | `True` | 36399 | 833 | `[1, 1]` | `[0, 0]` | 19 | 7 |
| chap08 | `True` | 67202 | 1566 | `[1, 1]` | `[0, 0]` | 43 | 3 |

**本スクリプトは2章とも未適用であることを前提とするため、2章の処理を開始する前に一度だけ
実行する。** 章ごとの確認は手順0-B を使う。

あわせて run の構成を確認する（§2.1）。

```bash
for ch in chap06 chap08; do echo "== $ch"; ls "/home/sakagawa/work/確率統計/ocr/mineru-full/$ch/"; done
```

- 2章とも `run-01` / `run-01-normalized` / `run-01.log` の3つだけであること
- **件数はすべて Python の `str.count()` で数える。`grep -c` を使わない**

いずれかが期待と異なる場合は、その場で回避策を取らず**中断して報告する**。

また、更新前の md・`{FINAL_NN}` 全体・修正定義ファイルを `{SCRATCH}` に退避する。

```bash
B2=/home/sakagawa/work/確率統計
for ch in chap06 chap08; do
  cp "$B2/ocr/mineru-full/$ch/run-01-normalized/${ch}_gray300.md" "$SCRATCH/${ch}_gray300.md.before"
  cp -a "$B2/ocr/final/$ch" "$SCRATCH/final_${ch}.before"
  cp "$B2/ocr/fixes/${ch}.json" "$SCRATCH/${ch}.json.before"
done

# 退避の成功確認（md・final・修正定義ファイルの3点すべてを検査する）
for ch in chap06 chap08; do
  cmp "$B2/ocr/mineru-full/$ch/run-01-normalized/${ch}_gray300.md" "$SCRATCH/${ch}_gray300.md.before" || { echo "BACKUP_NG_MD $ch"; continue; }
  diff -r "$B2/ocr/final/$ch" "$SCRATCH/final_${ch}.before" || { echo "BACKUP_NG_FINAL $ch"; continue; }
  cmp "$B2/ocr/fixes/${ch}.json" "$SCRATCH/${ch}.json.before" || { echo "BACKUP_NG_FIXES $ch"; continue; }
  echo "BACKUP_OK $ch"
done
```

- **2章とも `BACKUP_OK {章名}` が出ること。** `BACKUP_NG_*` が1つでも出たら手順1 に進まない
- 本案件では**両章とも修正定義ファイルが既存**である（feat-020 の chap00 のような新規作成はない）。
  したがって**復元時にファイルを削除する場面は存在しない**

**退避に失敗した場合は手順1 に進まず中断して報告する。**

### 手順0-B: 章ごとの直前確認（各章の手順1 の直前に行う）

手順0 のスクリプトの `EXP` から**当該章の1エントリだけ**を残したものを実行し、`OK` であることを
確認してから手順1 に進む。`MISMATCH` の場合はその章の手順1 に進まず**中断して報告する**。
**手順0 を2章分まとめて再実行してはならない**（処理済みの章が `MISMATCH` になるため）。

### 手順1: 修正定義ファイルへの追記

§4.2 の内容で2ファイルを更新する。**§2.2 の順序で1章ずつ処理する**
（手順0-B → 手順1 → 手順2 → 手順3 を章ごとに完結させる）。

- 既存 JSON を読み込み、`fixes` 配列の末尾に新規2件を `append` して書き戻す。
  追記前に §4.1 の SHA-256 と既存 ID を照合し、**異なっていた場合は上書きせず中断して報告する**
- **追記後に必ずファイルを読み込み直し、新規 fix の `old` / `new` が Python 文字列として
  §4.2 の表と一致することを確認する**（JSON のバックスラッシュのエスケープ誤りを検出するため。§4.1）

  ```bash
  uv run python -c "
  import json, sys
  ch = sys.argv[1]; scratch = sys.argv[2]
  EXP = {
   'chap06': [('chap06-008', 'あらゆる種目 θ で', 'あらゆる種目 \$\\\\theta\$ で'),
              ('chap06-009', 'の推定量 θ を探さない', 'の推定量 \$\\\\hat{\\\\theta}\$ を探さない')],
   'chap08': [('chap08-004', '第 i 主成分が \$z_', '第 \$i\$ 主成分が \$z_'),
              ('chap08-005', '\$z_{i}=q_{i}\\\\cdot x\$', '\$z_{i}=\\\\boldsymbol{q}_{i}\\\\cdot\\\\boldsymbol{x}\$')],
  }[ch]
  n_before = {'chap06': 7, 'chap08': 3}[ch]
  before = json.load(open(f'{scratch}/{ch}.json.before', encoding='utf-8'))['fixes']
  after  = json.load(open(f'/home/sakagawa/work/確率統計/ocr/fixes/{ch}.json', encoding='utf-8'))['fixes']
  assert len(before) == n_before and len(after) == n_before + 2, (len(before), len(after))
  assert after[:n_before] == before, 'EXISTING FIXES CHANGED'
  for i, (fid, old, new) in enumerate(EXP):
      f = after[n_before + i]
      assert f['id'] == fid, (f['id'], fid)
      assert f['old'] == old, ('OLD MISMATCH', f['old'], old)
      assert f['new'] == new, ('NEW MISMATCH', f['new'], new)
  print(ch, 'APPEND_OK', [f['id'] for f in after[n_before:]])
  " chap06 "$SCRATCH"
  ```

  （chap08 も同様に引数を変えて実行する。）
- あわせて JSON として妥当であること、`fixes` 配列の要素数が chap06 = 9 / chap08 = 5 であることを確認する

### 手順2: 修正の適用（章ごと）

```bash
B2=/home/sakagawa/work/確率統計
ch=chap06   # 次に chap08
uv run python scripts/apply_fixes.py \
  "$B2/ocr/mineru-full/$ch/run-01-normalized/${ch}_gray300.md" \
  "$B2/ocr/fixes/${ch}.json" \
  -o "$B2/ocr/mineru-full/$ch/run-01-normalized" --overwrite
```

- 期待: 終了コード 0、標準出力の `applied` / `skipped` が次のとおり

  | 章 | applied | skipped |
  |---|---|---|
  | chap06 | 2 | 7 |
  | chap08 | 2 | 3 |

- **`applied` / `skipped` が表と異なる場合は、終了コードが 0 でも次の手順に進まず、
  「失敗時の復元」に従って当該章を復元してから中断・報告する**

### 手順3: final の再構築（章ごと）

```bash
B2=/home/sakagawa/work/確率統計
ch=chap06   # 次に chap08
uv run python scripts/build_final.py \
  "$B2/ocr/mineru-full/$ch/run-01-normalized" -o "$B2/ocr/final/$ch" --overwrite
```

- 期待: 終了コード 0（3種類の機械検証がすべて合格）

### 失敗時の復元（手順1〜手順3 に共通）

**本手順は、本案件が既にファイルを書き換えた後に失敗したときにのみ実行する。**

**書き込み前の不一致では復元してはならない。** 復元は退避時点の内容で上書きする操作であり、
本案件が書いていないファイルに対して行うと、**退避後に他の作業が加えた変更を消してしまう**。

本案件が書き込むファイルは、章ごとに次の順序で増えていく。

| 段階 | この時点までに本案件が書き換えたファイル |
|---|---|
| 手順0-B の実行中・手順1 の照合中（追記前） | **なし** |
| 手順1 の追記後 | 修正定義ファイル（`{FIXES_NN}`）のみ |
| 手順2 の後 | `{FIXES_NN}` ＋ `{NORM_NN}` の md |
| 手順3 の後 | `{FIXES_NN}` ＋ `{NORM_NN}` の md ＋ `{FINAL_NN}` |

| 失敗した箇所 | 条件 | 復元対象 |
|---|---|---|
| 手順0-B | 当該章が `MISMATCH` | **復元しない**（中断して報告するのみ） |
| 手順1（追記**前**） | §4.1 の SHA-256 の不一致・既存 ID の不一致 | **復元しない**（中断して報告するのみ） |
| 手順1（追記**後**） | JSON 不正・要素数の不一致・`EXISTING FIXES CHANGED`・`OLD MISMATCH` / `NEW MISMATCH` | **`{FIXES_NN}` のみ** |
| 手順2 | `apply_fixes.py` の終了コードが 0 以外、または `applied` / `skipped` が表と異なる | **`{FIXES_NN}` と `{NORM_NN}` の md** |
| 手順3 | `build_final.py` の終了コードが 0 以外 | **`{FIXES_NN}`・`{NORM_NN}` の md・`{FINAL_NN}` の3点** |

**復元対象を広げてはならない。** 判断できない場合は、**何も戻さずに中断して報告する**。

**手順3 で失敗した場合に復元が必須である理由**: `build_final.py` は**ファイル単位では原子的**
（`copy_atomic` による一時ファイル＋`os.replace`）だが、**ディレクトリ全体としては原子的ではない**
（md → content_list.json → images/ の順に上書きし、孤児画像を削除したうえで最後に3検証を行う）。
そのため **`{FINAL_NN}` が新旧混在の部分更新状態で残りうる**。

対応（**失敗した章についてのみ、上表の「復元対象」に含まれるものだけ**）:

1. **その場で再実行やリトライをしない**
2. （手順3 で失敗した場合のみ）`{FINAL_NN}` を退避から復元する

   ```bash
   B2=/home/sakagawa/work/確率統計
   ch=chap06   # 失敗した章
   rm -rf "$B2/ocr/final/$ch"
   cp -a "$SCRATCH/final_${ch}.before" "$B2/ocr/final/$ch"
   diff -r "$SCRATCH/final_${ch}.before" "$B2/ocr/final/$ch" && echo RESTORED
   ```

3. （手順2 または手順3 で失敗した場合のみ）`{NORM_NN}` の md を退避から復元する

   ```bash
   cp "$SCRATCH/${ch}_gray300.md.before" \
      "$B2/ocr/mineru-full/$ch/run-01-normalized/${ch}_gray300.md"
   ```

4. （手順1 の追記後・手順2・手順3 のいずれかで失敗した場合）修正定義ファイルを復元する。
   **本案件では両章とも退避が存在するため、ファイルを削除する場面はない。**
   退避が見つからない場合は退避の取り漏らしであり、**何も消さず中断して報告する**

   ```bash
   if [ -f "$SCRATCH/${ch}.json.before" ]; then
     cp "$SCRATCH/${ch}.json.before" "$B2/ocr/fixes/${ch}.json"
   else
     echo "RESTORE_ABORT $ch: 退避 ${ch}.json.before が存在しない。削除せず中断する"
     exit 1
   fi
   ```

5. 復元後、**手順0-B**（当該章のみ）を実行し `OK` になることを確認する。
   手順2 または手順3 で失敗した場合は、あわせて `{NORM_NN}` と `{FINAL_NN}` が
   **再びバイト同一**であることを確認する

   ```bash
   cmp "$B2/ocr/mineru-full/$ch/run-01-normalized/${ch}_gray300.md" \
       "$B2/ocr/final/$ch/${ch}_gray300.md" && echo NORM_FINAL_IDENTICAL
   ```

6. 上表の復元対象をすべて戻したことを確認したうえで、**何が起きたか・どの章まで処理したか・
   どのファイルを復元したか（および復元しなかったものとその理由）を報告して中断する。
   後続の章には進まない**

## 7. 確認手順（FR-002〜FR-005 の受け入れ基準）

### 手順1: 修正内容の確認

**FR-002 基準1・2 は「行の完全一致」である。** 部分文字列の確認ではなく、行全体を比較する。

```bash
uv run python -c "
from pathlib import Path
B2 = Path('/home/sakagawa/work/確率統計')
EXP = {
 'chap06': dict(chars=36419, lines=833, ln=253, text='## ? 6.3 あらゆる種目 \$\\\\theta\$ ですべてのライバルを凌駕する全種目征覇なスーパーチャンピオンの推定量 \$\\\\hat{\\\\theta}\$ を探さないといけないわけですか。がんばって探してみますね。'),
 'chap08': dict(chars=67229, lines=1566, ln=285, text='## ? 8.3 第 \$i\$ 主成分が \$z_{i}=\\\\boldsymbol{q}_{i}\\\\cdot\\\\boldsymbol{x}\$ で求められるのはなぜ？'),
}
ok = True
for ch, e in EXP.items():
    for label, p in [('NORM',  B2/f'ocr/mineru-full/{ch}/run-01-normalized/{ch}_gray300.md'),
                     ('FINAL', B2/f'ocr/final/{ch}/{ch}_gray300.md')]:
        t = p.read_text(encoding='utf-8'); lines = t.split(chr(10))
        line = lines[e['ln']-1]
        good = (len(t)==e['chars'] and len(lines)==e['lines'] and line == e['text'])
        ok = ok and good
        print(ch, label, 'OK' if good else 'MISMATCH', 'chars', len(t), 'lines', len(lines))
        if line != e['text']:
            print('   期待:', e['text']); print('   実際:', line)
# 記号の個別確認（FR-002 基準3・4）
t6 = (B2/'ocr/final/chap06/chap06_gray300.md').read_text(encoding='utf-8').split(chr(10))[252]
t8 = (B2/'ocr/final/chap08/chap08_gray300.md').read_text(encoding='utf-8').split(chr(10))[284]
r6 = (t6.count('θ')==0, t6.count(chr(92)+'hat{'+chr(92)+'theta}')==1, t6.count('\$'+chr(92)+'theta\$')==1)
r8 = (t8.count(chr(92)+'boldsymbol{q}_{i}')==1, t8.count(chr(92)+'boldsymbol{x}')==1)
print('chap06 253行: 素のθ=0 / hat{theta}=1 / \$theta\$=1 →', r6)
print('chap08 285行: boldsymbol{q}_{i}=1 / boldsymbol{x}=1 →', r8)
ok = ok and all(r6) and all(r8)
print('ALL_OK' if ok else 'ABORT')
"
```

期待値:

| 項目 | 期待値 | 対応する受け入れ基準 |
|---|---|---|
| chap06 253 行 / chap08 285 行の**行全体の一致** | 一致（NORM / FINAL の4行すべて `OK`） | FR-002 基準1・2 |
| chap06 253 行の素の `θ` | **0** | FR-002 基準3 |
| chap06 253 行の `\hat{\theta}` / `$\theta$` | **各 1** | FR-002 基準3 |
| chap08 285 行の `\boldsymbol{q}_{i}` / `\boldsymbol{x}` | **各 1** | FR-002 基準4 |
| 文字数 | chap06 = 36419 / chap08 = 67229 | FR-003 基準3 |
| 行数 | chap06 = 833 / chap08 = 1566 | FR-003 基準3 |
| 最終行 | `ALL_OK` | — |

### 手順2: 差分が該当箇所のみであることの確認

```bash
B2=/home/sakagawa/work/確率統計
for ch in chap06 chap08; do
  echo "===== $ch"
  diff "$SCRATCH/${ch}_gray300.md.before" "$B2/ocr/final/$ch/${ch}_gray300.md"
done
```

期待される差分は**2章ともハンク1つのみ**である（FR-003 基準4。2026-09-06 実測）。

| 章 | 期待ハンク数 | 実測したハンク見出し |
|---|---|---|
| chap06 | **1** | `253c253` |
| chap08 | **1** | `285c285` |

**各章の2件の修正は同一行にあるため1ハンクに収まる。** 他の行に差分があってはならない。

### 手順3: 非影響の確認（FR-004）

```bash
git status --short
```

期待される変更は次の3件のみである（`docs/CHANGELOG.md`・`docs/PROJECT_KNOWLEDGE.md` の更新と
`docs/BACKLOG.md` のステータス Closed 化は完了処理で行うため、この時点ではまだ変更されていない）。

| パス | 状態 | 理由 |
|---|---|---|
| `docs/issues/feat-023-qa-heading-math-semantics/` | `??`（未追跡） | 案件ドキュメント |
| `docs/BACKLOG.md` | `M` | 起票時に feat-023 の行（In Progress）を追加済み |
| `tests/results/feat-023_test_result.txt` | `??`（未追跡） | 手順4 で新規作成する |

さらに次を確認する。

```bash
uv run python -c "
import hashlib
from pathlib import Path
B2 = Path('/home/sakagawa/work/確率統計')
EXP = {'chap06': ('f41ce4ca1b838792ede2a985ac08466fb5fdcc6ccc1704d02355ce903bd99860', 19),
       'chap08': ('7febf605cd86d279257d4d6c519bf626cf028d06c4147ac0703a391a61c83426', 43)}
h = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
ok = True
for ch,(sha,n) in EXP.items():
    cln = B2/f'ocr/mineru-full/{ch}/run-01-normalized/{ch}_gray300_content_list.json'
    clf = B2/f'ocr/final/{ch}/{ch}_gray300_content_list.json'
    imgs = len(list((B2/f'ocr/final/{ch}/images').iterdir()))
    good = h(cln)==sha and h(clf)==sha and imgs==n
    ok = ok and good
    print(ch, 'OK' if good else 'MISMATCH', 'images', imgs)
print('ALL_OK' if ok else 'ABORT')
"
```

- 各 `{FINAL_NN}/images/` のファイル数が変わっていないこと（chap06 = 19 / chap08 = 43。FR-003 基準6）
- 各章の `content_list.json` が `{NORM_NN}` と `{FINAL_NN}` の**両方でバイト単位で変更されていない**
  こと（FR-003 基準7）。手順0 で記録した SHA-256 と照合する

最後に、**手順A のコマンドを再実行**する（FR-004 基準3・4・5）。

- 出力先を `"$SCRATCH/invariant_manifest_after.txt"` に変え、
  `files = 641` かつ `AGGREGATE = 82797d011e9bf26172ee4e0f3749096ba6a4b1d88a0ff2011d6402657356e420` であること
- `diff "$SCRATCH/invariant_manifest_before.txt" "$SCRATCH/invariant_manifest_after.txt"` が**無出力**であること
- 一致しない場合は `diff` の出力から**どのファイルが変わったかを特定し、中断して報告する**

### 手順4: 自動テストの全件実行（FR-004 基準7）

```bash
uv run pytest -v > tests/results/feat-023_test_result.txt 2>&1
```

- コード変更がないため、feat-020 完了時点（**236 passed**）と同じくすべて成功することを確認する
- 出力を保存しながら実行し、保存後にファイル末尾で `failed` が 0 件であることを確認する

## 8. md と content_list.json の非対称性（既知事項）

`apply_fixes.py` は md のみを対象とし、`content_list.json` を変更しない（feat-010 の設計）。
そのため最終的な状態は次のようになる。

| ファイル | 当該箇所の状態 |
|---|---|
| `final/chapNN/chapNN_gray300.md` | 原本と一致（ハット・太字・数式マークアップあり） |
| `final/chapNN/chapNN_gray300_content_list.json` | 記号が失われたまま（2件とも） |

これは feat-013 §6.1・feat-016 §8・feat-017 §8・feat-019 §8・feat-022 §8・feat-020 §8 で
許容済みの既存ポリシーであり、本案件では変更しない。LLM に読ませる主成果物は md であり、
`content_list.json` の主用途は `page_idx` による原本ページとの対応付けと図ブロックの座標参照である
（feat-005 ADR-7）。`build_final.py` の検証はコピー元と final のバイト同一性・画像参照の整合を
見るものであり、md と json の間の本文の一致は検査しないため、検証にも影響しない。

## 9. エラーハンドリングと境界条件

| 事象 | 挙動 | 対応 |
|---|---|---|
| `old` が md に存在しない（0件）かつ `new` が1件 | `apply_fixes.py` は `skipped` として扱い終了コード 0・内容不変 | 冪等性の担保。手順2 を2回実行しても安全 |
| `old` が2件以上 | `apply_fixes.py` がエラー終了（md は書かれない） | §6「失敗時の復元」の**手順2 の行**に従い復元してから中断・報告する |
| `old` も `new` も0件 | 同上 | 同上 |
| 適用後に `new` が2件以上 | 最終不変条件違反でエラー終了（md は書かれない） | 同上（§5 の実測と矛盾する） |
| 既存 fix が最終不変条件に違反 | 同上 | 同上（先行案件の適用状態が変わっている） |
| `apply_fixes.py` の終了コードが 0 でも `applied`/`skipped` が §6 手順2 の表と異なる | md は書き換わっている | **次の手順に進まず**、§6「失敗時の復元」の**手順2 の行**に従い復元してから中断・報告する |
| **JSON のバックスラッシュのエスケープ誤り**（`\\theta` と書くべきところを `\theta` と書いた等） | JSON として不正になるか、`old`/`new` が意図と異なる文字列になる | 手順1 の `APPEND_OK` 確認（`OLD MISMATCH` / `NEW MISMATCH`）で検出する。§6「失敗時の復元」の**手順1（追記後）の行**に従い `{FIXES_NN}` のみ復元し、中断・報告する |
| 修正定義ファイルが JSON として不正 | `apply_fixes.py` が読み込み時にエラー終了 | 同上 |
| 既存ファイルの SHA-256 が §4.1 の表と異なる | — | 上書きせず**中断して報告する**。**復元しない**（書き込み前のため） |
| 手順1 の確認で `EXISTING FIXES CHANGED` が出る | — | §6「失敗時の復元」の**手順1（追記後）の行**に従い `{FIXES_NN}` のみ復元し、中断・報告する |
| `build_final.py` の3検証のいずれかが不合格、またはコピー途中で失敗 | 終了コード 1。**`{FINAL_NN}` が部分更新状態で残りうる** | §6「失敗時の復元」の**手順3 の行**に従い3点を復元し、手順0-B が `OK` になることを確認して中断・報告する。**後続の章には進まない** |
| ある章で失敗し、先行する章は成功済み | — | 失敗した章のみ復元する。成功済みの章は戻さない。どの章まで完了したかを明記して報告する |
| 手順0 が `ABORT`、または手順0-B が `ABORT` | — | 手順1 に進まず中断して報告する。**復元しない**（書き込み前のため） |
| 処理済みの章がある状態で手順0 を2章分まとめて再実行した | 処理済みの章が `MISMATCH` になり `ABORT` する | 手順0 は一度だけ実行する設計である。章ごとの確認には手順0-B を使う |
| **対象章に `run-02` 以降が存在する** | `{FINAL_NN}` のコピー元が `run-01-normalized` でない可能性がある | §2.1 のとおり中断して報告する（feat-020 の chap07 の事例）。手順0 の `md_identical` 検査でも検出できる |
| 手順0 の退避で `BACKUP_NG_*` が出る | — | 手順1 に進まず中断して報告する。**復元しない** |
| 手順A のマニフェストが期待値と異なる | — | 中断して報告する |
| 出力先が入力と同一・入れ子、またはシンボリックリンク | `build_final.py` が書き込み前に拒否 | 本案件のパス指定では発生しない |

## 10. 実装の担当と進め方

CLAUDE.md「実装の実行方法（Sonnetサブエージェント）」に従い、**Agent ツールで model: sonnet を
指定したサブエージェントに委任する**。委任時に渡す情報は次のとおり。

1. 必読ドキュメントと順序: `CLAUDE.md` → `docs/PROJECT_KNOWLEDGE.md` → 本案件の `README.md` →
   `requirements.md` → 本 `design.md` → `fixes/README.md`・`fixes/template.json` →
   `scripts/apply_fixes.py`・`scripts/build_final.py`
2. 厳密準拠（本書に書かれていない独自判断・改善・リファクタは禁止。**コードは1行も変更しない**）
3. 想定外事象（§9 の「中断して報告する」に該当する事象を含む）が起きたら回避策を実装せず
   直ちに中断し、§6「失敗時の復元」の表に従って**その段階の復元対象だけ**を戻し
   （書き込み前なら何も戻さない）、何を復元し何を復元しなかったかを明記して報告して終了する
4. 検証まで実施（§6 の手順A・手順0・手順0-B・手順1〜3 と §7 の手順1〜4、
   `tests/results/feat-023_test_result.txt` への保存）。**手順0 の退避を2章すべてについて必ず先に行う**
5. 禁止事項: git commit / push、`docs/BACKLOG.md` / `docs/CHANGELOG.md` / `CLAUDE.md` /
   `README.md`（ルート）/ `docs/PROJECT_KNOWLEDGE.md` の更新、
   **`docs/issues/feat-021-qa-heading-source-collation/` の変更**
6. 報告形式: 変更ファイル一覧、章ごとの `applied`/`skipped` と終了コード、§7 の確認結果、
   差分ハンク数、テスト結果サマリ、想定外事象の有無

## 11. ドキュメントの更新（完了処理で Claude Code 本体が実施する）

| ファイル | 更新内容 |
|---|---|
| `docs/BACKLOG.md` | feat-023 のステータスを Closed に更新する（起票時に In Progress で追加済み）。**後続案件案 F の残件が 18 → 16 件になること**を備考に明記する（FR-005） |
| `docs/CHANGELOG.md` | 完了内容を記録する。**案 F の残件が 16 件になること**も記載する |
| `docs/PROJECT_KNOWLEDGE.md` | 「データ」節の第2の書籍の項に、**Q&A 見出しの意味に影響する数式記号の欠落2件を修正済みであること**と、**残る `D4`（数式マークアップの欠落）が16件であること**を1行追記する。**追記には案件 ID「（feat-023）」を付す**。ディレクトリ構成の変更はない |
| **`CLAUDE.md`** | **更新しない**（update-003 の非対称ルール） |
| `README.md`（ルート） | **更新不要**（コマンド・CLI オプション・入出力形式・既定値・実行環境のいずれも不変） |
| 案件 `README.md` | ステータスを Closed に更新する |
| **`docs/issues/feat-021-*/collation_summary.md`** | **更新しない**（FR-005 基準3。feat-021 の確定した突合結果の記録である） |

## 12. 後続案件への引き渡し

1. **後続案件案 F（インライン数式のマークアップ欠落）の残件は 18 → 16 件**になる。
   feat-021 の `collation_summary.md` §9.2 は「`D4` が立った全18件」と記載しているが、
   本案件で chap06 6.3 と chap08 8.3 の2件が解消する。**案 F を起票する際は件数を数え直すこと**
2. 案 **C**（約物の全角/半角ゆれ10件）・**D**（アキの脱落2件）・**E**（参照アイコン `？`→`?` 2件）は未起票
3. feat-020 で発見した chap07 7.3 の箇条書きの括弧の誤読（md `(a,b)` / 原本 `(a,b]`）も未起票
4. **本文（見出し以外）における同種の記号の欠落**は未調査である。chap06 の `\hat{\theta}` 24件・
   chap08 の `\boldsymbol` 122件は既に正しく出ているが、**見出し以外で失われている箇所がないことは
   確認していない**。案 F の調査（影響範囲の測定）に含めるべき論点である

## 13. 設計判断の記録（ADR）

### ADR-1: 本件を字形正規化テーブルに入れず、修正定義ファイルで扱う

- **決定**: `normalize_punct.py` の置換表に追加せず、`{BASE2}/ocr/fixes/chapNN.json` で補正する
- **理由**: 置換表は**1文字 → 1文字**の字形対応表である。本件は
  「`θ` → `$\hat{\theta}$`」「`q_{i}` → `\boldsymbol{q}_{i}`」のような**構造の付与**であり、
  1対1の字形対応として表現できない。加えて `θ`・`q_{i}`・`x`・`i` はいずれも正当な文字・記号であり、
  全書籍に常時適用される置換表に入れれば大量の正当な箇所を壊す
- **代替案**: 置換表に追加する → 置換表の意味が変質し、適用範囲とリスクが釣り合わない。不採用
  （feat-011 ADR-3・feat-013 ADR-2・feat-019 ADR-1・feat-022 ADR-1 と同じ判断）

### ADR-2: 1行につき2件の fix に分ける（行を丸ごと置換する1件にしない）

- **決定**: chap06 6.3 に `chap06-008`・`009` の2件、chap08 8.3 に `chap08-004`・`005` の2件を定義する
- **理由**:
  1. `old` を最小の文脈にとどめられる（行を丸ごと `old` にすると、chap06 は60文字を超える長大な
     文字列になり、**再 OCR で1文字でも変われば一致しなくなる**）
  2. 修正の意図が `reason` 単位で分離される（意味に影響する欠落と、数式マークアップの欠落を
     別の fix として記録できる。後続案件案 F との境界が明確になる）
  3. §5.3 のとおり同一行内で干渉せず、適用順にも依存しない
- **代替案**: 1行 = 1 fix にする → `old` が長大になり再 OCR 耐性が下がる。
  また2種類の修正理由が1つの `reason` に混在する。不採用

### ADR-3: `old` / `new` に見出し記号（`## ? N.M`）を含めない

- **決定**: 4件の `old` / `new` はいずれも質問文の内部だけを対象とし、行頭の `## ? 6.3` /
  `## ? 8.3` を含めない
- **理由**: 見出し体裁は feat-020 で確定した領域であり、番号や `?` を `old` に含めると
  **feat-020 の成果に依存する**ことになる。質問文の内部だけを対象にすれば、
  見出し体裁がどう変わっても本案件の修正定義は有効なまま保たれる
  （feat-022 ADR-2 が疑問符を含めなかったのと同じ考え方）
- **代替案**: 行全体を `old` にする → ADR-2 の理由に加え、feat-020 との結合度が上がる。不採用

### ADR-4: 対象2行は原本と完全に一致させる（意味に影響する記号だけを直さない）

- **決定**: ハット・太字の復元に加え、同じ行にある平文の数式（chap06 の「種目 θ」・
  chap08 の「第 i」）も `$…$` にする
- **理由**: **chap06 のハット復元には `$\hat{\theta}$` と書く必要があり、数式マークアップの付与が
  不可避**である。「意味に影響する欠落だけ」を直すと、同じ一文の中に平文の `θ` と
  数式の `$\hat{\theta}$` が混在し、かえって不自然な状態になる。対象は2行のみであり、
  行単位で原本に一致させるほうが結果を検証しやすい（FR-002 基準1・2 の「行の完全一致」）。
  2026-09-06 にユーザーが決定した
- **代替案**: 意味に影響する記号（ハット・太字）のみ復元する → 上記の混在が生じる。
  また案 F の残件が 18 件のまま変わらない代わりに、案 F が同じ2行に再度手を入れることになる。不採用
- **副作用**: 案 F の残件が 18 → 16 件になる（§12。FR-005 で引き渡す）

### ADR-5: MinerU と `normalize_punct.py` を再実行しない

- **決定**: `apply_fixes.py` と `build_final.py` のみを実行する
- **理由**: 数式記号の欠落は MinerU の認識結果に起因し、同一入力に対して同じ結果になるため
  再実行しても再発する。`normalize_punct.py` は置換表を変更しないため結果が変わらず、冪等でもある
- **代替案**: `ocr_dir.py` で2章を再実行する → MinerU の実行時間が無駄であり、run 番号が増えて
  履歴が追いにくくなる（feat-013 ADR-3・feat-022 ADR-6・feat-020 ADR-7 と同じ判断）。不採用

### ADR-6: 既存 fix を本書に転記せず、SHA-256 で照合する

- **決定**: §4.1 のとおり、既存 fix 計10件の内容を転記せず、追記前のファイルの SHA-256 と
  fix 一覧（件数・ID）を照合する
- **理由**: 既存 fix には複数行文字列と 64 桁の画像ハッシュを含むものがあり、
  転記は誤りを持ち込む risk があるうえ、一意性の担保に寄与しない。実装は
  「読み込んだ既存要素をそのまま再利用して書き出す」append 方式である
  （feat-022 ADR-5・feat-020 ADR-6 と同じ判断）
- **代替案**: 既存 JSON を全文転記する → 転記ミスの risk が高い。不採用

### ADR-7: 知見の追記先を `docs/PROJECT_KNOWLEDGE.md` とし、`CLAUDE.md` を変更しない

- **決定**: §11 の追記は `docs/PROJECT_KNOWLEDGE.md` に案件 ID 付きで行う
- **理由**: update-003 で確定した非対称ルールに従う。本件で追記するのは**データの状態の変化**であり、
  統治文書に置く内容ではない
- **代替案**: `CLAUDE.md` に追記する → update-003 で外出し済みのため参照先が存在しない。不採用
