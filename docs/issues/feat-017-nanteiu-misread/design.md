# feat-017 機能設計書: 確率統計 4章の誤読「なんという → なんていう」9件の修正

対象案件: `docs/issues/feat-017-nanteiu-misread/`
要求仕様書: 同フォルダの `requirements.md`
調査記録: 同フォルダの `README.md`

## 1. 対応要求マッピング

| 要求 | 設計箇所 |
|---|---|
| FR-001 修正定義ファイルへの修正の定義 | §4（4ファイルの全文）・§5（一意性の確認） |
| FR-002 「なんという」の誤読の訂正 | §4（`old` / `new` の設計）・§7 手順1 |
| FR-003 既存成果物への適用と final 再構築 | §6（適用手順）・§7（確認手順） |
| FR-004 影響範囲の限定 | §3（変更しないもの）・§6 手順A（不変対象マニフェストの記録）・§7 手順3 |

## 2. システム構成

本案件は**リポジトリ内のコードを変更しない**。既存スクリプトを引数を変えて実行するのみである。

```
{BASE2} = /home/sakagawa/work/確率統計
NN ∈ {01, 03, 06, 08}
{NORM}(NN)  = {BASE2}/ocr/mineru-full/chapNN/run-01-normalized
{FINAL}(NN) = {BASE2}/ocr/final/chapNN
{FIXES}(NN) = {BASE2}/ocr/fixes/chapNN.json   ← 本案件で作成/追記（リポジトリ外）

  {NORM}(NN)/chapNN_gray300.md ──┐
                                 ├─→ apply_fixes.py ──→ {NORM}(NN)/chapNN_gray300.md（インプレース更新）
  {FIXES}(NN) ───────────────────┘

  {NORM}(NN)/（md + content_list.json + images/）
        └─→ build_final.py ──→ {FINAL}(NN)/（再構築・3種類の機械検証）
```

4章とも `run-01` のみが存在する（2026-08-31 実測: 各章の `{BASE2}/ocr/mineru-full/chapNN/` の
内容は `run-01` / `run-01-normalized` / `run-01.log` の3つ）。
実装時に `ls {BASE2}/ocr/mineru-full/chapNN/` を実行し、`run-01-normalized` が存在すること、
およびそれが最大の run 番号であることを章ごとに確認する。異なっていた場合は中断して報告する。

**章ごとに「適用 → final 再構築 → 確認」を完結させる**（chap01 → chap03 → chap06 → chap08 の順）。
ある章で異常が起きたら、以降の章に進まずに中断する（FR-004 非機能要求「独立性」）。

## 3. 変更しないもの（FR-004）

| 対象 | 理由 |
|---|---|
| `scripts/` 配下のすべてのファイル | 本案件はデータ側の修正のみで実現できる |
| `tests/test_*.py`（テストコード） | コード変更がないため、テストの追加・変更も生じない。ただし `tests/results/feat-017_test_result.txt` は検証記録として**新規作成する**（CLAUDE.md「テスト」のルール。§7 手順4） |
| 各章の `chapNN_gray300_content_list.json` | `apply_fixes.py` は md のみを対象とする（feat-010 の設計）。§8 の非対称性 |
| 各章の `{NORM}/images/`・`{FINAL}/images/` | 画像は本案件の対象外。`build_final.py` がコピーするのみ |
| `{BASE2}/ocr/fixes/chap06.json` の既存 fix `chap06-001` | feat-013 で作成・適用済み。本案件では追記のみを行う |
| `{BASE2}/ocr/fixes/` の他5ファイル（chap02・04・05・07・09） | 本案件の対象外 |
| 確率統計の対象外6章（chap00・02・04・05・07・09）の成果物 | 「なんという」の残存は 0 件（chap02 は feat-015 で修正済み）。案件 README.md §5 |
| PRML（`{BASE}`）の成果物 | 「なんという」は 0 件（案件 README.md §5） |
| `{BASE2}/ocr/mineru-full/chapNN/run-01/`（MinerU 生出力） | 読み取りも変更もしない |

## 4. 修正定義ファイルの内容（FR-001・FR-002）

以下の4ファイルを作成／更新する。**JSON はすべて UTF-8・インデント2スペースとする**
（既存ファイルの書式に合わせる）。

### 4.1 `{BASE2}/ocr/fixes/chap01.json`（新規作成）

```json
{
  "fixes": [
    {
      "id": "chap01-001",
      "reason": "p? の Q&A コラム見出し ? 1.5（原本 page-06_1L.tif）で、原本の「なんていう」が「なんという」と誤読されていた（原本 TIF 目視確認済み）。chap01 の md に「なんという」は1件しかないが、再 OCR 時の取り違えを防ぐため直後の「大風呂敷」まで含めて一意にしている",
      "old": "なんという大風呂敷",
      "new": "なんていう大風呂敷"
    }
  ]
}
```

### 4.2 `{BASE2}/ocr/fixes/chap03.json`（新規作成）

```json
{
  "fixes": [
    {
      "id": "chap03-001",
      "reason": "本文（原本 page-15_1L.tif）で、原本の「等しいなんていう勘違い」が「なんという」と誤読されていた（原本 TIF 目視確認済み）。chap03 には「なんという」が3件あるため、直前の「等しい」と直後の「勘違い」を含めて一意にしている",
      "old": "等しいなんという勘違い",
      "new": "等しいなんていう勘違い"
    },
    {
      "id": "chap03-002",
      "reason": "図 3.15 のキャプション（原本 page-19_1L.tif）で、原本の「なんていうことはない」が「なんということはない」と誤読されていた（原本 TIF 目視確認済み）。図は「合計そのものは 3.5n に収束せず、収束するのは 合計/n である」ことを示しており、原本の否定の意味（そのようなことは起きない）と整合する。図 3.16 のキャプションが同一の言い回しであるため、直前の「3.5n に近づいていく、」まで含めて一意にしている",
      "old": "3.5n に近づいていく、なんということはない",
      "new": "3.5n に近づいていく、なんていうことはない"
    },
    {
      "id": "chap03-003",
      "reason": "図 3.16 のキャプション（原本 page-19_2R.tif）で、原本の「なんていうことはない」が「なんということはない」と誤読されていた（原本 TIF 目視確認済み）。理由は chap03-002 と同じ。図 3.15 のキャプションと区別するため、直前の「n/2 に近づいていく、」まで含めて一意にしている",
      "old": "n/2 に近づいていく、なんということはない",
      "new": "n/2 に近づいていく、なんていうことはない"
    }
  ]
}
```

### 4.3 `{BASE2}/ocr/fixes/chap06.json`（既存ファイルへの追記）

既存の `chap06-001` は1文字も変更しない。追記後のファイル全体は次のとおりになる。

```json
{
  "fixes": [
    {
      "id": "chap06-001",
      "reason": "p12 の式番号「……（イ）」の「イ」が部首「亻」として認識された（原本 TIF 目視確認済み）。`(\\text {イ})` は同章に別の式番号として1件存在するため、`\\dots \\dots` まで含めて一意にしている",
      "old": "\\dots \\dots (\\text {亻})",
      "new": "\\dots \\dots (\\text {イ})"
    },
    {
      "id": "chap06-002",
      "reason": "本文（原本 page-10_1L.tif）で、原本の「事前分布なんていう恣意的なもの」が「なんという」と誤読されていた（原本 TIF 目視確認済み）。chap06 には「なんという」が4件あるため、直前の「事前分布」と直後の「恣意的な」を含めて一意にしている",
      "old": "事前分布なんという恣意的な",
      "new": "事前分布なんていう恣意的な"
    },
    {
      "id": "chap06-003",
      "reason": "本文（原本 page-11_1L.tif）で、原本の「だから H0 だなんていう説は受け入れ難い」が「なんという」と誤読されていた（原本 TIF 目視確認済み）。直後の引用ブロック（chap06-004）が同一の言い回しであるため、後続の「」と訴える」まで含めて一意にしている",
      "old": "だなんという説は受け入れ難い」と訴える",
      "new": "だなんていう説は受け入れ難い」と訴える"
    },
    {
      "id": "chap06-004",
      "reason": "引用ブロック（原本 page-11_1L.tif）で、原本の「だから H0 だなんていう説は受け入れ難い。」が「なんという」と誤読されていた（原本 TIF 目視確認済み）。直前の本文（chap06-003）と区別するため、末尾の句点「。」まで含めて一意にしている（chap06-003 は「」と訴える」が続き、chap06-005 は「」。」が続くため、句点が直接続くのは本件のみ）",
      "old": "だなんという説は受け入れ難い。",
      "new": "だなんていう説は受け入れ難い。"
    },
    {
      "id": "chap06-005",
      "reason": "本文（原本 page-12_1L.tif）で、原本の「だから期待値が 7 だなんていう説は受け入れ難い」が「なんという」と誤読されていた（原本 TIF 目視確認済み）。chap06-003・004 と区別するため、直前の「期待値が7だ」を含めて一意にしている",
      "old": "期待値が7だなんという説",
      "new": "期待値が7だなんていう説"
    }
  ]
}
```

**注意**: 上の `chap06-001` は 2026-08-31 時点の既存ファイルの内容を**そのまま転記した**ものである。
実装時は既存の `chap06-001` を1文字も変更してはならない（`id` / `reason` / `old` / `new` の
4キーすべてを既存の値のまま残す）。実装は「既存 JSON を読み込み、`fixes` 配列の末尾に
4件を `append` して書き戻す」方法で行い、既存要素を書き換えないこと。

### 4.4 `{BASE2}/ocr/fixes/chap08.json`（新規作成）

```json
{
  "fixes": [
    {
      "id": "chap08-001",
      "reason": "本文（原本 page-07_1L.tif から page-07_2R.tif に続く段落）で、原本の「なんていう雑な扱い」が「なんという」と誤読されていた（原本 TIF 目視確認済み）。chap08 の md に「なんという」は1件しかないが、再 OCR 時の取り違えを防ぐため直後の「雑な扱い」まで含めて一意にしている",
      "old": "なんという雑な扱い",
      "new": "なんていう雑な扱い"
    }
  ]
}
```

### 4.5 `old` / `new` の設計方針

- 誤読は9件とも「なんという」→「なんていう」の**1文字の置換**である。`old` を
  「なんという」だけにすると、同一章に複数ある場合に一意にならず、また `new`
  （「なんていう」）が適用後に複数件になって最終不変条件に違反する。
  そのため**すべての fix で最小限の文脈を付けて一意化する**
- 文脈は一意性が確保できる最小限にとどめる。文脈を長くするほど再 OCR 時に文面が変わって
  `old` が一致しなくなる可能性が上がる（feat-015 ADR-3・feat-016 ADR-3 と同じ判断）
- chap01・chap08 は章内に1件しかないため文脈なしでも一意だが、**直後の語を1語含める**
  （§5 の実測で `new` の一意性も確認済み）。再 OCR で別の箇所に「なんという」が現れた場合に
  誤った箇所へ適用されるのを防ぐためである
- 数式（`$H_{0}$` 等）を `old` に含めない。再 OCR で数式の空白や記法が1文字でも変われば
  `old` が一致しなくなるため（feat-015 ADR-3 と同じ判断）。chap06-003・004 は
  `$H_{0}$ だ` の直後から始めるのではなく、`だなんという説は…` として数式を避けている

## 5. 一意性の確認（FR-001 受け入れ基準 5・6）

`apply_fixes.py` は、適用後に**全 fix について `count(old) == 0` かつ `count(new) == 1`** を
検査し、1つでも破れていればエラー終了して出力を書かない（最終不変条件。feat-010 FR-003 規則6）。
そのため `old` の一意性だけでなく、**適用後に `new` がちょうど1件になることも事前に数える**
（CLAUDE.md の運用ルール。feat-013 でこれを怠って実装が1度中断した）。

2026-08-31 に各章の `{FINAL}(NN)/chapNN_gray300.md`（= `{NORM}(NN)` の md とバイト同一）で
実測した。**全 fix を章内で逐次適用したうえで**最終不変条件を検査している。

| 章 | fix | `count(old)` 適用前 | `count(new)` 適用前 | `count(old)` 適用後 | `count(new)` 適用後 |
|---|---|---|---|---|---|
| chap01 | `chap01-001` | 1 | 0 | 0 | 1 |
| chap03 | `chap03-001` | 1 | 0 | 0 | 1 |
| chap03 | `chap03-002` | 1 | 0 | 0 | 1 |
| chap03 | `chap03-003` | 1 | 0 | 0 | 1 |
| chap06 | `chap06-002` | 1 | 0 | 0 | 1 |
| chap06 | `chap06-003` | 1 | 0 | 0 | 1 |
| chap06 | `chap06-004` | 1 | 0 | 0 | 1 |
| chap06 | `chap06-005` | 1 | 0 | 0 | 1 |
| chap08 | `chap08-001` | 1 | 0 | 0 | 1 |

**全 fix が `count(old) == 1` かつ `count(new) == 0`（適用前）、`count(old) == 0` かつ
`count(new) == 1`（適用後）を満たす。**

既存の `chap06-001` についても、追記後の最終不変条件を満たす。

| fix | 文字列 | 適用前 | 適用後（予測） |
|---|---|---|---|
| `chap06-001` | `old` = `\dots \dots (\text {亻})` | 0 | 0 |
| `chap06-001` | `new` = `\dots \dots (\text {イ})` | 1 | 1 |

`chap06-001` は feat-013 で適用済みのため `count(old) == 0` / `count(new) == 1` であり、
`apply_fixes.py` の規則2により **skipped** として扱われ、最終不変条件も満たす。
新規4件の `old` / `new` は `chap06-001` の `old` / `new` と文字列として重ならないため、
逐次適用の順序による干渉は生じない。

### 5.1 干渉が起きないことの根拠（chap06 の4件）

chap06-003（`だなんという説は受け入れ難い」と訴える`）と chap06-004
（`だなんという説は受け入れ難い。`）は先頭部分が共通するが、**どちらも他方の部分文字列ではない**
（一方は `」と訴える` が、他方は `。` が続く）。したがって適用順に依存しない。

chap06-005 の適用後の文字列は `期待値が7だなんていう説は受け入れ難い」。` であり、
chap06-004 の `new`（`だなんていう説は受け入れ難い。`）とは `」` の有無で異なるため、
chap06-004 の `count(new)` を 2 にしてしまうことはない（§5 の実測で確認済み）。

## 6. 適用手順（FR-003）

**MinerU（`ocr_dir.py`）と `normalize_punct.py` は実行しない。**
各章の `{NORM}` は feat-013 の再適用（2026-08-28）で字形正規化済みの状態にあり、
本案件は置換表を変更しないため、再正規化しても結果は変わらない。

以下を **chap01 → chap03 → chap06 → chap08 の順に、章ごとに手順0〜3 を完結させて**実行する。
ただし手順A は全章共通で、最初に1回だけ実行する。

### 手順A: 不変対象マニフェストの記録（全章共通・最初に1回だけ）

FR-004 基準3・4・5 の対象のうち、**`git` 管理外のため `git status` では変更を検出できない
ファイル群**について、SHA-256 のマニフェストを記録する。対象は次の**541ファイル**である。
**`images/` を含む配下のすべての通常ファイルを再帰的に対象とする**（`.md` / `.json` だけでは
図画像の変更を検出できないため）。

- `{BASE2}/ocr/fixes/` の他5ファイル（`chap02.json`・`chap04.json`・`chap05.json`・
  `chap07.json`・`chap09.json`）… 5ファイル
- 確率統計の対象外6章（chap00・02・04・05・07・09）の `final/chapNN/` 配下の全通常ファイル（再帰）
- PRML（`{BASE}` = `/home/sakagawa/work/Pattern_Recognition_and_Machine_Learning`）の
  `ocr/final/chap00〜07/` 配下の全通常ファイル（再帰）

```bash
uv run python -c "
import hashlib
from pathlib import Path
B2 = Path('/home/sakagawa/work/確率統計/ocr')
B1 = Path('/home/sakagawa/work/Pattern_Recognition_and_Machine_Learning/ocr')
paths = [B2/'fixes'/f'{n}.json' for n in ['chap02','chap04','chap05','chap07','chap09']]
for n in ['chap00','chap02','chap04','chap05','chap07','chap09']:
    paths += [p for p in (B2/'final'/n).rglob('*') if p.is_file()]
for d in sorted((B1/'final').iterdir()):
    if d.is_dir():
        paths += [p for p in d.rglob('*') if p.is_file()]
lines = [f'{p}\t{hashlib.sha256(p.read_bytes()).hexdigest()}' for p in sorted(paths)]
manifest = chr(10).join(lines) + chr(10)
print(manifest, end='')
print('files =', len(lines))
print('AGGREGATE', hashlib.sha256(manifest.encode()).hexdigest())
" | tee /tmp/.../invariant_manifest_before.txt
```

`print(manifest, end='')` により、**個別のパスと SHA-256 の一覧も標準出力に出す**。
`tee` でファイルに保存されるため、不一致時に行単位で比較して変更ファイルを特定できる。

期待値（2026-08-31 実測）:

- `files = 541`
- `AGGREGATE = 1fa3f0ca33d3f103f095cb9a20b64bd40e27775e616e7d1502ed1a227286ac72`

**この2値が期待と異なる場合は、その場で回避策を取らず中断して報告する**
（対象外のデータが既に変更されている、またはファイル構成が変わっていることを意味する）。
出力はスクラッチパッド等（成果物ディレクトリの外）に保存し、§7 手順3 で再実行して照合する。

### 手順0: 事前確認（章ごとに、実行前に必ず行う）

```bash
ls /home/sakagawa/work/確率統計/ocr/mineru-full/chapNN/

uv run python -c "
import hashlib
from pathlib import Path
ch = 'chapNN'
norm = Path(f'/home/sakagawa/work/確率統計/ocr/mineru-full/{ch}/run-01-normalized')
fin  = Path(f'/home/sakagawa/work/確率統計/ocr/final/{ch}')
md_n, md_f = norm/f'{ch}_gray300.md', fin/f'{ch}_gray300.md'
cl_n, cl_f = norm/f'{ch}_gray300_content_list.json', fin/f'{ch}_gray300_content_list.json'
t = md_n.read_text(encoding='utf-8')
print('md bytes identical:', md_n.read_bytes() == md_f.read_bytes())
print('chars', len(t), 'lines', len(t.split(chr(10))))
print('なんという', t.count('なんという'), 'なんていう', t.count('なんていう'))
h = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
print('content_list sha256 NORM ', h(cl_n))
print('content_list sha256 FINAL', h(cl_f))
print('images', len(list((fin/'images').iterdir())))
"
```

期待値（2026-08-31 実測）:

| 章 | chars | lines | なんという | なんていう | images | content_list SHA-256 |
|---|---|---|---|---|---|---|
| chap01 | 24856 | 586 | 1 | 0 | 27 | `bd53e369c349f2754e110642d8801577f5dd320c2b04d06303899ede243bc92a` |
| chap03 | 54009 | 1462 | 3 | 0 | 66 | `d269034e9b54fd993a3d4f9e092421a3b7974d3441519eb389678055e5103220` |
| chap06 | 36479 | 835 | 4 | 0 | 19 | `f41ce4ca1b838792ede2a985ac08466fb5fdcc6ccc1704d02355ce903bd99860` |
| chap08 | 67199 | 1566 | 1 | 0 | 43 | `7febf605cd86d279257d4d6c519bf626cf028d06c4147ac0703a391a61c83426` |

あわせて次を確認する。

- `run-01-normalized` が存在し、それが最大の run 番号であること
- `md bytes identical` が `True` であること（`{NORM}` と `{FINAL}` の md がバイト同一。
  差分があれば未反映の変更が存在する）
- `content_list sha256` の NORM と FINAL が互いに一致し、かつ上表の値であること。
  この値は §7 手順3 で `content_list.json` が変更されていないことを検証するために使う
  （FR-003 基準7）
- **件数はすべて Python の `str.count()` による出現回数で数える**。`grep -c` は
  マッチした「行数」を返すため、`apply_fixes.py` の不変条件（`str.count()` ベース）と
  数え方が一致しない。本書のすべての件数確認で `grep -c` を使ってはならない

いずれかが期待と異なる場合は、その場で回避策を取らず**中断して報告する**。

また、更新前の md を作業用にコピーしておく（成果物ディレクトリの**外**、
スクラッチパッド等に置く。§7 手順2 の `diff` で使う）。

### 手順1: 修正定義ファイルの作成／追記

§4 の内容で `{BASE2}/ocr/fixes/chapNN.json` を作成または更新する。

- chap01・chap03・chap08 は**新規作成**（既存ファイルは存在しない。存在した場合は
  上書きせず**中断して報告する**）
- chap06 は**既存ファイルへの追記**。既存 JSON を読み込んで `fixes` 配列の末尾に4件を
  `append` して書き戻す方法で行い、既存の `chap06-001` の4キーを1文字も変更しないこと。
  既存ファイルの `chap06-001` の `old` が `\dots \dots (\text {亻})`、`new` が
  `\dots \dots (\text {イ})` と異なっていた場合は、上書きせず**中断して報告する**
- 作成／追記後に `uv run python -c "import json; json.load(open(...))"` で JSON として
  妥当なことと、`fixes` 配列の要素数が §4 のとおり（chap01 = 1、chap03 = 3、chap06 = 5、
  chap08 = 1）であることを確認する

### 手順2: 修正の適用（章ごと）

```bash
uv run python scripts/apply_fixes.py \
  /home/sakagawa/work/確率統計/ocr/mineru-full/chapNN/run-01-normalized/chapNN_gray300.md \
  /home/sakagawa/work/確率統計/ocr/fixes/chapNN.json \
  -o /home/sakagawa/work/確率統計/ocr/mineru-full/chapNN/run-01-normalized --overwrite
```

- 出力先を入力と同じディレクトリにし、`--overwrite` でインプレース更新する
  （feat-013 ADR-4・feat-015 と同じ）
- 期待（終了コード 0）:

  | 章 | 標準出力 |
  |---|---|
  | chap01 | `chap01_gray300.md: 1 applied, 0 skipped` / `total: 1 applied, 0 skipped` |
  | chap03 | `chap03_gray300.md: 3 applied, 0 skipped` / `total: 3 applied, 0 skipped` |
  | chap06 | `chap06_gray300.md: 4 applied, 1 skipped` / `total: 4 applied, 1 skipped` |
  | chap08 | `chap08_gray300.md: 1 applied, 0 skipped` / `total: 1 applied, 0 skipped` |

### 手順3: final の再構築（章ごと）

```bash
uv run python scripts/build_final.py \
  /home/sakagawa/work/確率統計/ocr/mineru-full/chapNN/run-01-normalized \
  -o /home/sakagawa/work/確率統計/ocr/final/chapNN --overwrite
```

- 期待: 終了コード 0（バイト同一・画像参照・`img_path` 集合一致の3検証がすべて合格）

## 7. 確認手順（FR-002〜FR-004 の受け入れ基準）

### 手順1: 修正内容の確認（章ごと）

手順0 と同じ数え方（`str.count()` による出現回数）で、`{NORM}` と `{FINAL}` の
両方の md を確認する。

```bash
uv run python -c "
ch = 'chapNN'
for label, path in [
    ('NORM',  f'/home/sakagawa/work/確率統計/ocr/mineru-full/{ch}/run-01-normalized/{ch}_gray300.md'),
    ('FINAL', f'/home/sakagawa/work/確率統計/ocr/final/{ch}/{ch}_gray300.md'),
]:
    t = open(path, encoding='utf-8').read()
    print(label, 'なんという', t.count('なんという'), 'なんていう', t.count('なんていう'),
          'chars', len(t), 'lines', len(t.split(chr(10))))
"
```

期待値（`{NORM}` / `{FINAL}` とも同じ）:

| 章 | なんという | なんていう | chars | lines | 対応する受け入れ基準 |
|---|---|---|---|---|---|
| chap01 | 0 | 1 | 24856 | 586 | FR-002 基準1・2、FR-003 基準3 |
| chap03 | 0 | 3 | 54009 | 1462 | 同上 |
| chap06 | 0 | 4 | 36479 | 835 | 同上 |
| chap08 | 0 | 1 | 67199 | 1566 | 同上 |

**文字数・行数は適用前と同一である**（「と」→「て」は 1 文字 → 1 文字であり、改行の増減もない）。

### 手順2: 差分が該当箇所のみであることの確認（章ごと）

手順0 で退避した適用前の md と、適用後の md の `diff` を取る。

```bash
diff /tmp/.../chapNN_gray300.md.before \
     /home/sakagawa/work/確率統計/ocr/final/chapNN/chapNN_gray300.md
```

期待される差分ハンク数は chap01 = 1、chap03 = 3、chap06 = 4、chap08 = 1 であり、
**いずれも「なんという」→「なんていう」の1文字のみの変更**である（FR-003 基準4）。
他の変更があってはならない。

差分行が案件 README.md §2 の表に挙げた行（chap01: 204、chap03: 966・1263・1274、
chap06: 523・567・571・627、chap08: 366）に対応していることを確認する。

### 手順3: 非影響の確認（FR-004）

**4章すべての適用が終わった後**に、次を実行する。

```bash
git status --short
```

**この確認は実装（CLAUDE.md 機能追加フローのステップ6）の時点で行う。**
`docs/CHANGELOG.md` の更新と `docs/BACKLOG.md` のステータス Closed 化は
完了処理（ステップ8）で Claude Code 本体が行うため、**この時点ではまだ変更されていない**。

期待される変更は次の3件のみである。それ以外（`scripts/`・`tests/test_*.py`・
`docs/CHANGELOG.md`・`CLAUDE.md`・ルートの `README.md`）に変更があってはならない。

| パス | 状態 | 理由 |
|---|---|---|
| `docs/issues/feat-017-nanteiu-misread/` | `??`（未追跡） | 案件ドキュメント。起票時（ステップ1〜3）に作成済み |
| `docs/BACKLOG.md` | `M` | 起票時に feat-017 の行（ステータス `Open`）を追加済み |
| `tests/results/feat-017_test_result.txt` | `??`（未追跡） | 手順4 で新規作成する |

完了処理（ステップ8）の後は、上記に加えて `docs/CHANGELOG.md` が `M` になり、
`docs/BACKLOG.md` のステータスが `Closed` に変わる。これは想定どおりの変更であり、
本手順の検証対象ではない。

確率統計 final 全10章の「なんという」の残存件数を、出現回数で確認する。

```bash
uv run python -c "
from pathlib import Path
root = Path('/home/sakagawa/work/確率統計/ocr/final')
for f in sorted(root.glob('chap*/*')):
    if f.suffix in ('.md', '.json'):
        n = f.read_text(encoding='utf-8').count('なんという')
        if n:
            print(f, n)
"
```

期待される出力は次の **5 行**である（content_list 側のみ。**md は1件も出力されない**）。

| ファイル | 期待件数 | 備考 |
|---|---|---|
| `chap01/chap01_gray300_content_list.json` | 1 | **本案件で修正しない**（§8 の非対称性） |
| `chap02/chap02_gray300_content_list.json` | 1 | 同上（feat-015 で md のみ修正済み） |
| `chap03/chap03_gray300_content_list.json` | 3 | 同上 |
| `chap06/chap06_gray300_content_list.json` | 4 | 同上 |
| `chap08/chap08_gray300_content_list.json` | 1 | 同上 |

**`*.md` が1件も出力されない**ことが、本案件の修正が全件効いた証拠である（FR-002 基準4）。

さらに章ごとに次を確認する。

- `{FINAL}(NN)/images/` のファイル数が手順0 と同じであること
  （chap01 = 27、chap03 = 66、chap06 = 19、chap08 = 43）
- `{NORM}(NN)` と `{FINAL}(NN)` の `chapNN_gray300_content_list.json` が
  **バイト単位で変更されていない**こと（FR-003 基準7）。`git` 管理外のため、
  手順0 で記録した SHA-256（§6 手順0 の表の値）と照合して検証する。
  mtime とサイズの比較では、同サイズの変更や mtime の復元を検出できないため用いない
最後に、**§6 手順A のコマンドを再実行**し、`git` 管理外の不変対象が変更されていないことを
検証する（FR-004 基準3・4・5）。

- 出力先を `invariant_manifest_after.txt` に変えて実行し、
  `files = 541` かつ `AGGREGATE = 1fa3f0ca33d3f103f095cb9a20b64bd40e27775e616e7d1502ed1a227286ac72`
  であること（手順A で記録した値と同一）
- あわせて `diff /tmp/.../invariant_manifest_before.txt /tmp/.../invariant_manifest_after.txt` が
  **無出力**であること
- 一致しない場合は、上記 `diff` の出力から**どのファイルが変わったかを特定し、中断して報告する**

この検証により、`git status` では検出できない次の3種類の非影響が確認できる。

| 対象 | 対応する受け入れ基準 |
|---|---|
| 確率統計の対象外6章（chap00・02・04・05・07・09）の成果物 | FR-004 基準3 |
| 既存の修正定義ファイル5件（chap02・04・05・07・09） | FR-004 基準4 |
| PRML（`{BASE}`）の成果物 | FR-004 基準5 |

### 手順4: 自動テストの全件実行（FR-004 基準6）

```bash
uv run pytest -v > tests/results/feat-017_test_result.txt 2>&1
```

- コード変更がないため、feat-015 完了時点（**216 passed**）と同じくすべて成功することを確認する
- 上記コマンドは出力を `tests/results/feat-017_test_result.txt` に**保存しながら**実行する
  （CLAUDE.md「テスト」のルール: テストコマンドの出力をそのまま保存する）。
  保存後、ファイルの末尾で全件成功（`failed` が 0 件）であることを確認する

## 8. md と content_list.json の非対称性（既知事項）

`apply_fixes.py` は md のみを対象とし、`content_list.json` を変更しない（feat-010 の設計）。
そのため最終的な状態は次のようになる。

| ファイル | 当該箇所の状態 | 理由 |
|---|---|---|
| `final/chapNN/chapNN_gray300.md` | 「なんていう」（正しい） | `apply_fixes.py` の適用対象 |
| `final/chapNN/chapNN_gray300_content_list.json` | 「なんという」（誤りのまま） | `apply_fixes.py` の対象外 |

これは feat-013 §6.1・feat-015 design.md §8・feat-016 §8 で許容済みの既存ポリシーであり、
本案件では変更しない。LLM に読ませる主成果物は md であり、`content_list.json` の主用途は
`page_idx` による原本ページとの対応付けと図ブロックの座標参照である（feat-005 ADR-7）ため、
実用上の影響はない。また `build_final.py` の検証はコピー元と final のバイト同一性・
画像参照の整合を見るものであり、md と json の間の本文の一致は検査しないため、検証にも影響しない。

## 9. エラーハンドリングと境界条件

| 事象 | 挙動 | 対応 |
|---|---|---|
| `old` が md に存在しない（0件）かつ `new` が1件 | `apply_fixes.py` は `skipped` として扱い終了コード 0・内容不変 | 冪等性の担保。手順2 を2回実行しても安全 |
| `old` が2件以上 | `apply_fixes.py` がエラー終了（出力なし） | 中断して報告する（想定外。文面が変わっている） |
| `old` も `new` も0件 | `apply_fixes.py` がエラー終了（出力なし） | 中断して報告する |
| 適用後に `new` が2件以上 | 最終不変条件違反でエラー終了（出力なし） | 中断して報告する（§5 の実測と矛盾する） |
| 既存の `chap06-001` が最終不変条件に違反 | 同上 | 中断して報告する（feat-013 の適用状態が変わっている） |
| `chapNN.json` が JSON として不正 | `apply_fixes.py` が読み込み時にエラー終了 | 定義内容を見直す（手順1 の JSON 妥当性確認で事前に検出する） |
| chap01・chap03・chap08 の fixes ファイルが既に存在する | — | 上書きせず**中断して報告する**（手順1） |
| `build_final.py` の3検証のいずれかが不合格 | 終了コード 1 | 中断して報告する |
| 出力先が入力と同一・入れ子、またはシンボリックリンク | `build_final.py` が書き込み前に拒否 | 本案件のパス指定では発生しない（`{NORM}` と `{FINAL}` は別ツリー） |
| ある章で異常が起きた | — | **以降の章に進まず中断して報告する**。完了済みの章の final は正しい状態で残る（§2） |

## 10. 実装の担当と進め方

CLAUDE.md「実装の実行方法（Sonnetサブエージェント）」に従い、**Agent ツールで model: sonnet を
指定したサブエージェントに委任する**。委任時に渡す情報は次のとおり。

1. 必読ドキュメントと順序: `CLAUDE.md` → 本案件の `README.md` → `requirements.md` →
   本 `design.md` → `fixes/README.md`・`fixes/template.json` →
   `scripts/apply_fixes.py`・`scripts/build_final.py`
2. 厳密準拠（本書に書かれていない独自判断・改善・リファクタは禁止。**コードは1行も変更しない**）
3. 想定外事象（§9 の「中断して報告する」に該当する事象を含む）が起きたら回避策を実装せず
   直ちに中断し、何が起きたか・どこまで完了したかを報告して終了する
4. 検証まで実施（§6 の手順A・手順0〜3 と §7 の手順1〜4、
   `tests/results/feat-017_test_result.txt` への保存）
5. 禁止事項: git commit / push、`docs/BACKLOG.md` / `docs/CHANGELOG.md` / `CLAUDE.md` /
   `README.md` の更新（完了処理で Claude Code 本体が行う）
6. 報告形式: 変更ファイル一覧、テスト結果サマリ、§7 の確認結果、想定外事象の有無

## 11. ドキュメントの更新（完了処理で Claude Code 本体が実施する）

| ファイル | 更新内容 |
|---|---|
| `docs/BACKLOG.md` | feat-017 のステータスを Closed に更新する（行は起票時に追加済み） |
| `docs/CHANGELOG.md` | 完了内容を記録する |
| `CLAUDE.md` | **更新不要**。語彙単位の誤りを `apply_fixes.py` で扱うことは feat-016 で、機械的な検出手段がないことは feat-015／feat-016 で既に記載済みであり、本案件で新たに加わる知見はない。ディレクトリ構成の変更もない（リポジトリ内のファイル追加・削除がないため） |
| `README.md` | **更新不要**。コマンド・CLI オプション・入出力形式・既定値・実行環境のいずれも変わらない |
| 案件 `README.md` | ステータスを Closed に更新する |

## 12. 設計判断の記録（ADR）

### ADR-1: 「なんという → なんていう」を字形正規化テーブルに入れず、修正定義ファイルで扱う

- **決定**: `normalize_punct.py` の `CJK_REPLACEMENTS_CN` / `OLD_FORM_REPLACEMENTS` に追加せず、
  章ごとの修正定義ファイルで補正する
- **理由**:
  1. 置換表は**1文字 → 1文字**の字形対応表である。「と → て」は字形の対応関係ではなく、
     字単位の置換にすれば本文が全面的に破壊される
  2. 「なんという」という5文字の並びに限っても、「なんという大事件だ」のように
     日本語として正当な用法がある。一般規則にすると誤置換のリスクが残る
  3. feat-011 ADR-3・feat-013 ADR-2・feat-015 ADR-1・feat-016 ADR-1 で確立した方針
     （字形の1対1対応が成立しない個別誤認識は `apply_fixes.py` で扱う）と一致する
- **代替案**: 置換表に `なんという → なんていう` を追加する → 置換表の意味が
  「字形正規化」から「文字列置換」に変質し、テーブルの適用範囲（全書籍・常時適用）と
  リスクが釣り合わない。不採用

### ADR-2: 9件を1つの案件で扱い、章ごとの fix に分ける

- **決定**: 9件を feat-017 の1案件として扱い、修正定義は章ごとのファイルに分けて定義する
- **理由**:
  1. 9件はすべて同一の誤読パターン（「て」→「と」）であり、原本確認・設計・検証の観点が
     共通する。案件を9つに分けると同じ調査を9回繰り返すことになる
  2. 修正定義ファイルは章単位という既存の運用（feat-010）に従う。`apply_fixes.py` も
     `build_final.py` も章単位で動作するため、この分割が自然である
  3. 章ごとに「適用 → final 再構築」を完結させるため、ある章が失敗しても完了済みの章の
     final は正しい状態で残る（feat-012 の章単位構築の方針と同じ）
- **代替案**: 章ごとに4案件に分ける → 調査・レビュー・完了処理が4倍になり、
  「小さく作って積み重ねる」方針の趣旨（1つの機能を検証可能な単位で作る）を超えて
  細分化しすぎである。不採用

### ADR-3: 図 3.15・3.16 のキャプション2件を修正対象に含める

- **決定**: 「なんということはない」→「なんていうことはない」に修正する
- **理由**:
  1. **原本 TIF の目視確認で、原本が「なんていうことはない」であることを確認した**
     （案件 README.md §3.1）。本プロジェクトのゴールは「入力への忠実な OCR」である
  2. 図の主旨とも整合する。図 3.15 は (左) 出た目の合計、(中) 合計 − 3.5n、(右) 合計/n を
     並べ、**合計そのものは 3.5n に収束しない**ことを示している。原本の
     「合計が 3.5n に近づいていく、なんていうことはない」は否定（そのようなことは起きない）
     であり、「なんということはない」（たいしたことではない）では意味が反転する
- **代替案**: 慣用句「なんということはない」として正当な可能性があるため修正対象から外す →
  原本確認により誤読であることが確定しており、残す理由がない。不採用
- **補足**: 本件は「原本を見ずに文字列だけで判断すると誤りうる」典型例である。
  同種の誤読を今後扱う際も、**必ず原本 TIF を確認してから**修正を定義する

### ADR-4: MinerU と `normalize_punct.py` を再実行しない

- **決定**: `apply_fixes.py` と `build_final.py` のみを実行する
- **理由**: 語彙単位の誤読は OCR の認識結果に起因し、同一入力に対して同じ結果になるため、
  再実行しても再発する（CLAUDE.md ドメイン知識「OCR の個別誤り…再OCRでも再発する」）。
  `normalize_punct.py` は置換表を変更しないため結果が変わらず、冪等でもある
- **代替案**: `ocr_dir.py --punct-style touten --final --fixes-dir ...` で4章を再実行する →
  MinerU の実行時間が無駄であり、run 番号が増えて履歴が追いにくくなる。不採用
  （feat-013 ADR-3・feat-015 ADR-4・feat-016 ADR-2 と同じ判断）
