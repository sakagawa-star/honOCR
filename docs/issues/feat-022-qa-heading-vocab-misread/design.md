# feat-022 機能設計書: Q&A コラム見出しの語彙誤読4件の修正

対象案件: `docs/issues/feat-022-qa-heading-vocab-misread/`
要求仕様書: 同フォルダの `requirements.md`
調査記録: 同フォルダの `README.md`

## 1. 対応要求マッピング

| 要求 | 設計箇所 |
|---|---|
| FR-001 修正定義ファイル4件への修正追記 | §4（追記内容）・§5（一意性の確認）・§6 手順1 |
| FR-002 語彙誤読4件の訂正 | §4.5（`old` / `new` の設計）・§7 手順1 |
| FR-003 既存成果物への適用と final 再構築 | §6（適用手順）・§7（確認手順） |
| FR-004 影響範囲の限定 | §3（変更しないもの）・§6 手順A（不変対象マニフェスト）・§7 手順3 |
| FR-005 feat-020 への引き渡し事項の記録 | §3（変更しないもの）・§7 手順1（`##` を補完しないことの確認）・§11 |

## 2. システム構成

本案件は**リポジトリ内のコードを変更しない**。既存スクリプトを引数を変えて実行するのみである。

```
{BASE2} = /home/sakagawa/work/確率統計
NN ∈ {01, 02, 03, 08}（対象4章）

{NORM_NN}  = {BASE2}/ocr/mineru-full/chapNN/run-01-normalized
{FINAL_NN} = {BASE2}/ocr/final/chapNN
{FIXES_NN} = {BASE2}/ocr/fixes/chapNN.json   ← 本案件で各1件追記（リポジトリ外・作成済み）

  {NORM_NN}/chapNN_gray300.md ──┐
                                ├─→ apply_fixes.py ──→ {NORM_NN}/chapNN_gray300.md（インプレース更新）
  {FIXES_NN} ───────────────────┘

  {NORM_NN}/（md + content_list.json + images/）
        └─→ build_final.py ──→ {FINAL_NN}/（再構築・3種類の機械検証）
```

対象4章はいずれも `run-01` のみが存在する（2026-09-03 実測: 各章の
`{BASE2}/ocr/mineru-full/chapNN/` の内容は `run-01` / `run-01-normalized` / `run-01.log` の3つ）。
実装時に `ls {BASE2}/ocr/mineru-full/chapNN/` を4章とも実行し、`run-01-normalized` が存在すること、
およびそれが最大の run 番号であることを確認する。異なっていた場合は中断して報告する。

### 2.1 処理の単位と順序

**章単位で「直前確認（手順0-B）→ 追記 → 適用 → final 再構築」を完結させ、4章を次の順に処理する。**
（手順A の不変対象マニフェストと手順0 の事前確認は、4章の処理を始める前に**一度だけ**行う。）

```
chap01 → chap02 → chap03 → chap08
```

- 章の処理が1つでも失敗した場合、**その章のみを退避から復元し、後続の章には進まず中断して報告する**
  （§6「失敗時の復元」）。既に完了した章はそのままでよい（章どうしは独立しており、
  途中まで完了した状態でも各章の `{NORM_NN}` と `{FINAL_NN}` は整合している）
- 順序に技術的な依存はない（章間に干渉がないことは §5.4 で示す）。再現性のために章番号順に固定する

## 3. 変更しないもの（FR-004・FR-005）

| 対象 | 理由 |
|---|---|
| `scripts/` 配下のすべてのファイル | 本案件はデータ側の修正のみで実現できる |
| `tests/test_*.py`（テストコード） | コード変更がないため、テストの追加・変更も生じない。ただし `tests/results/feat-022_test_result.txt` は検証記録として**新規作成する**（CLAUDE.md「テスト」のルール。§7 手順4） |
| **`CLAUDE.md`** | update-003 で確定した非対称ルール（CLAUDE.md 本体の変更は update 案件のみ）。本案件の知見は `docs/PROJECT_KNOWLEDGE.md` に追記する（§11） |
| 各 `{NORM_NN}/chapNN_gray300_content_list.json` | `apply_fixes.py` は md のみを対象とする（feat-010 の設計）。§8 の非対称性 |
| 各 `{NORM_NN}/images/`・`{FINAL_NN}/images/` | 画像は本案件の対象外。`build_final.py` がコピーするのみ（chap01 = 27 / chap02 = 47 / chap03 = 66 / chap08 = 43 ファイル） |
| `{BASE2}/ocr/fixes/chapNN.json`（NN ∈ {01,02,03,08}）の既存 fix 計13件 | feat-014・015・017・019 等で作成・適用済み。本案件では追記のみを行う |
| `{BASE2}/ocr/fixes/` の他5ファイル（chap04・05・06・07・09） | 本案件の対象外 |
| 確率統計の非対象6章（chap00・04・05・06・07・09）の成果物 | 本案件の4件はいずれも対象4章にのみ存在する（案件 README.md §5） |
| PRML（`{BASE}`）の成果物 | 本案件は確率統計のみを対象とする |
| **chap08 md 520 行の行頭（`? 8.6` のまま。`## ` を補わない）** | `##` の欠落（`D2`）は **feat-020 の担当**である（FR-005 基準4） |
| **chap03 md 585 行の末尾の疑問符（半角 `?` のまま）** | 約物の全角/半角ゆれは feat-021 の後続案件案 C の対象（requirements.md §7） |
| `docs/issues/feat-020-qa-heading-not-recognized/` 配下のファイル | 本案件では feat-020 のドキュメントを変更しない（FR-005 基準3） |

## 4. 修正定義ファイルへの追記内容（FR-001）

### 4.1 追記の方法

**既存 JSON を読み込み、`fixes` 配列の末尾に新規1件を `append` して書き戻す。**
既存要素（`id` / `reason` / `old` / `new` の4キー）を1文字も変更してはならない。

追記の**前**に、対象4ファイルが下表の状態であることを SHA-256 と fix 一覧で確認する。
**異なっていた場合は上書きせず中断して報告する。**

| ファイル | 追記前の SHA-256（2026-09-03 実測） | 既存 fix 数 | 既存 ID |
|---|---|---|---|
| `chap01.json` | `25f04c94a543e7fdad6acb5895d303b077bee6ebc478cb5941d60d49143ed97a` | 2 | `chap01-001`, `chap01-002` |
| `chap02.json` | `e2d0ffbb8337343929acfa6b88fc7ba6de03ea6dfdbe8c9dc2ae229727e5a660` | 4 | `chap02-001`〜`chap02-004` |
| `chap03.json` | `c2a8942bfb2731eee62fb6f150a437f1387d9ebe635ea1ad96e9fce24643b923` | 6 | `chap03-001`〜`chap03-006` |
| `chap08.json` | `ccb8a7a48e059621d2b35e50ce1b2c45e2b75cde02fa751824259014b4c08f6b` | 1 | `chap08-001` |

追記後の `fixes` 配列の要素数は chap01 = 3 / chap02 = 5 / chap03 = 7 / chap08 = 2 になる。

**既存 fix の内容は本書に転記しない**（chap02・chap03 の `old` に 64 桁の画像ハッシュを含む
長大な文字列があり、転記は誤りを持ち込む risk がある）。上表の SHA-256 が一致することを
もって「既存が想定どおりであること」の確認とする。書き戻し後は、**既存要素が変更されて
いないこと**を「読み込んだ既存要素のオブジェクトをそのまま再利用して書き出す」実装で担保し、
§6 手順1 の確認で検算する。

書式は `fixes/template.json`・`fixes/README.md` に従う（キーは `id` / `reason` / `old` / `new` の
4つ、すべて文字列。JSON はインデント2・`ensure_ascii=False`・末尾改行ありで書き出す。
既存4ファイルと同じ体裁）。

### 4.2 新規 fix（4件）

以下の4つのオブジェクトを、それぞれ対応するファイルの `fixes` 配列の末尾に追加する。

**chap01.json に追加（`chap01-003`）**

```json
{
  "id": "chap01-003",
  "reason": "Q&A コラム見出し「? 1.8」（原本 page-08_1L.tif）の質問文で、原本の「描いたらいいんでしたっけ」が「描いたらいんでしたっけ」と誤読されていた（「い」が1文字脱落。原本 TIF 目視確認済み・feat-021 の突合および本案件での再確認）。「いんでしたっけ」は chap01 に1件しかないが、再 OCR 時の取り違えを防ぐため直前の「描いたら」まで含めて一意にしている（feat-022）",
  "old": "描いたらいんでしたっけ",
  "new": "描いたらいいんでしたっけ"
}
```

**chap02.json に追加（`chap02-005`）**

```json
{
  "id": "chap02-005",
  "reason": "Q&A コラム見出し「? 2.10」（原本 page-18_2R.tif）の質問文で、原本の「これぜんぶ覚えない」が「こぜんぶ覚えない」と誤読されていた（「れ」が1文字脱落。原本 TIF 目視確認済み・feat-021 の突合および本案件での再確認）。「こぜんぶ」は chap02 に1件しかないが、再 OCR 時の取り違えを防ぐため直後の「覚えない」まで含めて一意にしている（feat-022）",
  "old": "こぜんぶ覚えない",
  "new": "これぜんぶ覚えない"
}
```

**chap03.json に追加（`chap03-007`）**

```json
{
  "id": "chap03-007",
  "reason": "Q&A コラム見出し「? 3.5」（原本 page-10_1L.tif）の質問文で、原本の「賭けろということですよね」が「賭けるということですよね」と誤読されていた（「ろ」→「る」。原本 TIF 目視確認済み・feat-021 の突合および本案件での再確認）。chap03 には正当な「賭けるほうが」があり「賭ける」だけでは一意にならないため、直後の「ということですよね」まで含めて一意にしている。同じ行にある末尾の疑問符の全角/半角ゆれ（原本は全角「？」だが md は半角「?」）は本案件のスコープ外のため、old / new に疑問符を含めない（feat-022）",
  "old": "賭けるということですよね",
  "new": "賭けろということですよね"
}
```

**chap08.json に追加（`chap08-002`）**

```json
{
  "id": "chap08-002",
  "reason": "Q&A コラム見出し「? 8.6」（原本 page-10_2R.tif）の質問文末尾で、原本の「そういうことだろ」が「そういうことだる」と誤読されていた（「ろ」→「る」。原本 TIF 目視確認済み・feat-021 の突合および本案件での再確認）。「だる」は確率統計の全10章で1件しかないが、再 OCR 時の取り違えを防ぐため直前の「そういうこと」まで含めて一意にしている。なお同じ行には「## が無い」という別の不一致もあるが、それは feat-020 の担当であり本案件では扱わない（feat-022）",
  "old": "そういうことだる",
  "new": "そういうことだろ"
}
```

### 4.3 追記前後の md の該当行（実測・2026-09-03）

| 章 | 行 | 追記前（現状） | 適用後（期待） |
|---|---|---|---|
| chap01 | 298 | `## ?1.8 上で描いたような式の領域はどんなやり方で描いたらいんでしたっけ？` | `## ?1.8 上で描いたような式の領域はどんなやり方で描いたらいいんでしたっけ？` |
| chap02 | 1395 | `## ? 2.10 こぜんぶ覚えないといけませんか？` | `## ? 2.10 これぜんぶ覚えないといけませんか？` |
| chap03 | 585 | `## ? 3.5 ギャンブルなら期待値の高いほうに賭けるということですよね?` | `## ? 3.5 ギャンブルなら期待値の高いほうに賭けろということですよね?` |
| chap08 | 520 | `? 8.6 ツキには波が…可能性が高い。そういうことだる？` | `? 8.6 ツキには波が…可能性が高い。そういうことだろ？` |

**chap03 の末尾は半角 `?` のまま、chap08 の行頭は `? 8.6`（`##` なし）のままである**（§3）。

### 4.4 原本の確認（本案件で 2026-09-03 に実施）

feat-021 の記録に依存せず、本案件として独立に確認した（案件 README.md §3）。

| 章 | content_list の index | `page_idx` | 原本 TIF | 原本の印字 |
|---|---|---|---|---|
| chap01 | 159 | 14 | `page-08_1L.tif` | …描いたら**いい**んでしたっけ？ |
| chap02 | 648 | 35 | `page-18_2R.tif` | **これ**ぜんぶ覚えないといけませんか？ |
| chap03 | 257 | 17 | `page-10_1L.tif` | …賭け**ろ**ということですよね？ |
| chap08 | 274 | 18 | `page-10_2R.tif` | …そういうことだ**ろ**？ |

確認の手順（再実行可能）:

```bash
uv run python scripts/crop_blocks.py \
  /home/sakagawa/work/確率統計/ocr/final/chap01/chap01_gray300_content_list.json \
  /home/sakagawa/work/確率統計/dewarping/chap01/out \
  -o "$SCRATCH/crops/chap01" --index 159 --margin 20
```

（chap02 は index 648、chap03 は index 257、chap08 は index 274。`--margin 20` は
見出しの前後の行まで写して文脈を確認するための値。）

**本確認は実装フェーズでの再実行を必須としない**（起票時に実施済み）。原本と md が
本書の記載と食い違う場合にのみ再実行して確認する。

### 4.5 `old` / `new` の設計

- 4件はいずれも**1文字の挿入（chap01・chap02）または1文字の置換（chap03・chap08）**である
- `old` は「誤読された語 ＋ 一意性が確保できる最小限の文脈」とする。文脈を長くするほど
  再 OCR 時に文面が変わって `old` が一致しなくなる可能性が上がる
  （feat-015 ADR-3・feat-016 ADR-3・feat-017 §4.5・feat-019 ADR-2 と同じ判断）
- **数式・画像参照・脚注記号・疑問符を `old` / `new` に含めない**。
  数式・画像参照・脚注記号は再 OCR で記法が変わりうる。疑問符は後続案件案 C（約物の
  全角/半角ゆれ）で変更されうる（ADR-2）
- chap03 のみ、誤読語（`賭ける`）が同章に正当な用例（`賭けるほうが`）を持つため、
  文脈による一意化が**必須**である。他の3件は誤読語だけでも一意だが、
  feat-017 `chap01-001`・`chap08-001` の先例に倣い再 OCR 耐性のために短い文脈を付ける

## 5. 一意性の確認（FR-001 受け入れ基準 5・6）

`apply_fixes.py` は、適用後に**全 fix について `count(old) == 0` かつ `count(new) == 1`** を
検査し、1つでも破れていればエラー終了して出力を書かない（最終不変条件。feat-010 FR-003 規則6）。
そのため `old` の一意性だけでなく、**適用後に `new` がちょうど1件になることも事前に数える**
（`docs/PROJECT_KNOWLEDGE.md` の規定。feat-013 でこれを怠って実装が1度中断した）。

2026-09-03 に各 `{NORM_NN}/chapNN_gray300.md`（= 対応する `{FINAL_NN}` の md とバイト同一）で
実測した。**新規1件を適用したうえで、既存を含む当該章の全 fix について最終不変条件を検査**している。

### 5.1 新規4件（章内での出現回数）

| fix | 文字列 | 適用前 | 適用後（実測） |
|---|---|---|---|
| `chap01-003` | `old` = `描いたらいんでしたっけ` | **1** | 0 |
| `chap01-003` | `new` = `描いたらいいんでしたっけ` | **0** | **1** |
| `chap02-005` | `old` = `こぜんぶ覚えない` | **1** | 0 |
| `chap02-005` | `new` = `これぜんぶ覚えない` | **0** | **1** |
| `chap03-007` | `old` = `賭けるということですよね` | **1** | 0 |
| `chap03-007` | `new` = `賭けろということですよね` | **0** | **1** |
| `chap08-002` | `old` = `そういうことだる` | **1** | 0 |
| `chap08-002` | `new` = `そういうことだろ` | **0** | **1** |

### 5.2 既存13件（追記後も最終不変条件を満たすこと）

新規1件を適用した後の md に対し、当該章の**全 fix**（既存 ＋ 新規）について
`count(old) == 0` かつ `count(new) == 1` を検算した結果、**違反は4章とも0件**であった
（2026-09-03 実測）。

| 章 | 検査した fix 数（既存 ＋ 新規） | 最終不変条件の違反 |
|---|---|---|
| chap01 | 2 + 1 = 3 | **なし** |
| chap02 | 4 + 1 = 5 | **なし** |
| chap03 | 6 + 1 = 7 | **なし** |
| chap08 | 1 + 1 = 2 | **なし** |

既存 fix はいずれも適用済みのため `count(old) == 0` / `count(new) == 1` であり、
`apply_fixes.py` の規則2により **skipped** として扱われる。

### 5.3 干渉が起きないことの根拠（章内）

- 新規4件の `old`（`描いたらいんでしたっけ` / `こぜんぶ覚えない` / `賭けるということですよね` /
  `そういうことだる`）は、いずれも当該章の既存 fix の `new` に部分文字列として含まれない。
  したがって既存の適用結果を壊さない
- 新規4件の `new` は、いずれも当該章の既存 fix の `new` と文字列として重ならない。
  したがって既存の `count(new)` を 2 にしてしまうことはない
- 各章に追加する新規 fix は1件のみのため、新規どうしの適用順依存は生じない
- 上記はすべて §5.1・§5.2 の実測（全 fix が適用後 `count(old) == 0` かつ `count(new) == 1`）で
  確認済みである

### 5.4 干渉が起きないことの根拠（章間）

`apply_fixes.py` は **md 1ファイルと修正定義ファイル1件**を受け取り、そのファイル内でのみ
`str.count()` / `str.replace()` を行う（feat-010 の設計）。したがって章をまたぐ干渉は原理的に
起きない。加えて、新規4件の `old` / `new` は**確率統計の final 全10章を横断しても
それぞれ1件 / 0件**であることを実測済みである（案件 README.md §6）。

### 5.5 適用による文字数・行数の変化（実測）

| 章 | 文字数（前 → 後） | 行数（前 → 後） |
|---|---|---|
| chap01 | 24776 → **24777**（+1） | 584 → **584** |
| chap02 | 68838 → **68839**（+1） | 1859 → **1859** |
| chap03 | 53925 → **53925**（±0） | 1460 → **1460** |
| chap08 | 67199 → **67199**（±0） | 1566 → **1566** |

## 6. 適用手順（FR-003）

### 作業用ディレクトリ `{SCRATCH}` の定義

本書で `{SCRATCH}` と書いた箇所は、**Claude Code のセッション用スクラッチパッド**
（`/tmp/claude-1000/-home-sakagawa-git-honOCR/{session-id}/scratchpad/feat022/`）を指す。
成果物ディレクトリ（`{BASE2}` 配下）とリポジトリの**外**であり、実装の冒頭で作成する。

```bash
SCRATCH=/tmp/claude-1000/-home-sakagawa-git-honOCR/{session-id}/scratchpad/feat022
mkdir -p "$SCRATCH"
```

`{session-id}` は実装時のセッションのものを用いる（サブエージェントは自身に与えられた
スクラッチパッドのパスを使ってよい）。**本書のシェルコマンド中では `{SCRATCH}` ではなく
シェル変数 `"$SCRATCH"` の形で書いてある。`{SCRATCH}` は本文の説明でのみ用いる記法であり、
コマンドにそのまま貼り付けてはならない**（展開されず `{SCRATCH}` という名前のディレクトリが
作られてしまう）。**保存期間はセッション中のみ**であり、本案件の検証（§7 手順2・手順3）が
完了すれば破棄してよい。恒久的な記録は `tests/results/feat-022_test_result.txt` と
案件ドキュメントに残す。

**MinerU（`ocr_dir.py`）と `normalize_punct.py` は実行しない。**
対象4章の `{NORM_NN}` は feat-013 の再適用（2026-08-28）で字形正規化済み、feat-014 の再適用
（2026-09-02）までの各案件の修正が適用済みの状態にあり、本案件は置換表を変更しないため、
再正規化しても結果は変わらない。

### 手順A: 不変対象マニフェストの記録（最初に1回だけ）

FR-004 基準3・4・5 の対象のうち、**`git` 管理外のため `git status` では変更を検出できない
ファイル群**について、SHA-256 のマニフェストを記録する。対象は次の**513ファイル**である。
**`images/` を含む配下のすべての通常ファイルを再帰的に対象とする**（`.md` / `.json` だけでは
図画像の変更を検出できないため）。

- `{BASE2}/ocr/fixes/` の他5ファイル（`chap04`・`chap05`・`chap06`・`chap07`・`chap09` の各 `.json`）… 5ファイル
- 確率統計の非対象6章（chap00・04・05・06・07・09）の `final/chapNN/` 配下の全通常ファイル（再帰）
- PRML（`{BASE}` = `/home/sakagawa/work/Pattern_Recognition_and_Machine_Learning`）の
  `ocr/final/chap00〜07/` 配下の全通常ファイル（再帰）

**本手順は §6 冒頭の `{SCRATCH}` の定義（`mkdir -p "$SCRATCH"` まで）を実行した後に行う。**
以下のコマンドはシェル変数 `$SCRATCH` が設定されていることを前提とする。

```bash
uv run python -c "
import hashlib
from pathlib import Path
B2 = Path('/home/sakagawa/work/確率統計/ocr')
B1 = Path('/home/sakagawa/work/Pattern_Recognition_and_Machine_Learning/ocr')
paths = [B2/'fixes'/f'chap{n}.json' for n in ['04','05','06','07','09']]
for n in ['00','04','05','06','07','09']:
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

`print(manifest, end='')` により、**個別のパスと SHA-256 の一覧も標準出力に出す**。
`tee` でファイルに保存されるため、不一致時に行単位で比較して変更ファイルを特定できる。

期待値（2026-09-03 実測）:

- `files = 513`
- `AGGREGATE = 68f5af84c591ee2e657d6be3483283186d2802ec4492c35f55e624b7aa976414`

**この2値が期待と異なる場合は、その場で回避策を取らず中断して報告する**
（対象外のデータが既に変更されている、またはファイル構成が変わっていることを意味する）。
出力はスクラッチパッド等（成果物ディレクトリの外）に保存し、§7 手順3 で再実行して照合する。

### 手順0: 事前確認（4章の処理を開始する前に**一度だけ**行う）

```bash
uv run python -c "
import hashlib, json
from pathlib import Path
B2 = Path('/home/sakagawa/work/確率統計')
EXP = {
 'chap01': dict(chars=24776, lines=584, images=27, nfix=2,
   cl='bd53e369c349f2754e110642d8801577f5dd320c2b04d06303899ede243bc92a',
   fx='25f04c94a543e7fdad6acb5895d303b077bee6ebc478cb5941d60d49143ed97a',
   old='描いたらいんでしたっけ', new='描いたらいいんでしたっけ'),
 'chap02': dict(chars=68838, lines=1859, images=47, nfix=4,
   cl='a4ebb69a04863ac89c6b7ef1e2cf737377b20b168f50aa665ad523bf3aff260f',
   fx='e2d0ffbb8337343929acfa6b88fc7ba6de03ea6dfdbe8c9dc2ae229727e5a660',
   old='こぜんぶ覚えない', new='これぜんぶ覚えない'),
 'chap03': dict(chars=53925, lines=1460, images=66, nfix=6,
   cl='d269034e9b54fd993a3d4f9e092421a3b7974d3441519eb389678055e5103220',
   fx='c2a8942bfb2731eee62fb6f150a437f1387d9ebe635ea1ad96e9fce24643b923',
   old='賭けるということですよね', new='賭けろということですよね'),
 'chap08': dict(chars=67199, lines=1566, images=43, nfix=1,
   cl='7febf605cd86d279257d4d6c519bf626cf028d06c4147ac0703a391a61c83426',
   fx='ccb8a7a48e059621d2b35e50ce1b2c45e2b75cde02fa751824259014b4c08f6b',
   old='そういうことだる', new='そういうことだろ'),
}
h = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
ok = True
for ch, e in EXP.items():
    norm = B2/f'ocr/mineru-full/{ch}/run-01-normalized'
    fin  = B2/f'ocr/final/{ch}'
    mdn, mdf = norm/f'{ch}_gray300.md', fin/f'{ch}_gray300.md'
    cln, clf = norm/f'{ch}_gray300_content_list.json', fin/f'{ch}_gray300_content_list.json'
    t = mdn.read_text(encoding='utf-8')
    fx = B2/f'ocr/fixes/{ch}.json'
    r = dict(md_identical=mdn.read_bytes()==mdf.read_bytes(), chars=len(t),
             lines=len(t.split(chr(10))), old=t.count(e['old']), new=t.count(e['new']),
             images=len(list((fin/'images').iterdir())), cl_norm=h(cln), cl_final=h(clf),
             fx=h(fx), nfix=len(json.loads(fx.read_text(encoding='utf-8'))['fixes']))
    good = (r['md_identical'] and r['chars']==e['chars'] and r['lines']==e['lines']
            and r['old']==1 and r['new']==0 and r['images']==e['images']
            and r['cl_norm']==e['cl'] and r['cl_final']==e['cl']
            and r['fx']==e['fx'] and r['nfix']==e['nfix'])
    ok = ok and good
    print(ch, 'OK' if good else 'MISMATCH', r)
print('ALL_OK' if ok else 'ABORT')
"
```

期待値（2026-09-03 実測）: 4章とも `OK` で、最終行が `ALL_OK` であること。内訳は次のとおり。

| 章 | `md_identical` | `chars` | `lines` | `old` | `new` | `images` | `nfix` |
|---|---|---|---|---|---|---|---|
| chap01 | `True` | 24776 | 584 | 1 | 0 | 27 | 2 |
| chap02 | `True` | 68838 | 1859 | 1 | 0 | 47 | 4 |
| chap03 | `True` | 53925 | 1460 | 1 | 0 | 66 | 6 |
| chap08 | `True` | 67199 | 1566 | 1 | 0 | 43 | 1 |

`cl_norm` / `cl_final` / `fx` の期待値はスクリプト内の `EXP` に記載した SHA-256 と一致すること
（`cl_norm` と `cl_final` は同値。この値は §7 手順3 で `content_list.json` が変更されていない
ことを検証するために使う。FR-003 基準8）。

**本スクリプトは4章すべてが未適用（`old` = 1 / `new` = 0）であることを要求するため、
4章の処理を開始する前に一度だけ実行する。** 章ごとの処理の直前に行う確認は手順0-B に分けてある
（chap01 の適用後に本スクリプトを再実行すると、chap01 が `MISMATCH` になり必ず `ABORT` になる）。

あわせて次を確認する。

```bash
for ch in chap01 chap02 chap03 chap08; do
  echo "== $ch"; ls "/home/sakagawa/work/確率統計/ocr/mineru-full/$ch/"
done
```

- 4章とも `run-01-normalized` が存在し、それが最大の run 番号であること
- **件数はすべて Python の `str.count()` による出現回数で数える**。`grep -c` は
  マッチした「行数」を返すため、`apply_fixes.py` の不変条件（`str.count()` ベース）と
  数え方が一致しない。本書のすべての件数確認で `grep -c` を使ってはならない

いずれかが期待と異なる場合は、その場で回避策を取らず**中断して報告する**。

また、更新前の md・`{FINAL_NN}` 全体・修正定義ファイルを `{SCRATCH}`（シェル変数 `$SCRATCH`）に
退避する（§7 手順2 の `diff` と、§6「失敗時の復元」に使う）。

```bash
B2=/home/sakagawa/work/確率統計
for ch in chap01 chap02 chap03 chap08; do
  cp "$B2/ocr/mineru-full/$ch/run-01-normalized/${ch}_gray300.md" "$SCRATCH/${ch}_gray300.md.before"
  cp -a "$B2/ocr/final/$ch" "$SCRATCH/final_${ch}.before"
  cp "$B2/ocr/fixes/${ch}.json" "$SCRATCH/${ch}.json.before"
done

# 退避の成功確認（すべて一致すること）
for ch in chap01 chap02 chap03 chap08; do
  cmp "$B2/ocr/mineru-full/$ch/run-01-normalized/${ch}_gray300.md" "$SCRATCH/${ch}_gray300.md.before" \
    && cmp "$B2/ocr/fixes/${ch}.json" "$SCRATCH/${ch}.json.before" \
    && diff -r "$B2/ocr/final/$ch" "$SCRATCH/final_${ch}.before" \
    && echo "BACKUP_OK $ch"
done
```

- 4章すべてで `BACKUP_OK {章名}` が出ること（md・修正定義ファイル・`{FINAL_NN}` 全体＝md・
  content_list.json・images/ が退避できたこと）

**退避に失敗した場合は手順1 に進まず中断して報告する**（失敗時の復元手段がない状態で
`{FINAL_NN}` を書き換えてはならない）。

### 手順0-B: 章ごとの直前確認（各章の手順1 の直前に行う）

**対象の1章だけ**を検査する。手順0 と違い、既に処理を終えた他の章の状態には影響されない。

```bash
uv run python -c "
import hashlib, json, sys
from pathlib import Path
ch = sys.argv[1]
B2 = Path('/home/sakagawa/work/確率統計')
EXP = {
 'chap01': dict(chars=24776, lines=584, images=27, nfix=2,
   cl='bd53e369c349f2754e110642d8801577f5dd320c2b04d06303899ede243bc92a',
   fx='25f04c94a543e7fdad6acb5895d303b077bee6ebc478cb5941d60d49143ed97a',
   old='描いたらいんでしたっけ', new='描いたらいいんでしたっけ'),
 'chap02': dict(chars=68838, lines=1859, images=47, nfix=4,
   cl='a4ebb69a04863ac89c6b7ef1e2cf737377b20b168f50aa665ad523bf3aff260f',
   fx='e2d0ffbb8337343929acfa6b88fc7ba6de03ea6dfdbe8c9dc2ae229727e5a660',
   old='こぜんぶ覚えない', new='これぜんぶ覚えない'),
 'chap03': dict(chars=53925, lines=1460, images=66, nfix=6,
   cl='d269034e9b54fd993a3d4f9e092421a3b7974d3441519eb389678055e5103220',
   fx='c2a8942bfb2731eee62fb6f150a437f1387d9ebe635ea1ad96e9fce24643b923',
   old='賭けるということですよね', new='賭けろということですよね'),
 'chap08': dict(chars=67199, lines=1566, images=43, nfix=1,
   cl='7febf605cd86d279257d4d6c519bf626cf028d06c4147ac0703a391a61c83426',
   fx='ccb8a7a48e059621d2b35e50ce1b2c45e2b75cde02fa751824259014b4c08f6b',
   old='そういうことだる', new='そういうことだろ'),
}[ch]
h = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
norm = B2/f'ocr/mineru-full/{ch}/run-01-normalized'
fin  = B2/f'ocr/final/{ch}'
mdn, mdf = norm/f'{ch}_gray300.md', fin/f'{ch}_gray300.md'
cln, clf = norm/f'{ch}_gray300_content_list.json', fin/f'{ch}_gray300_content_list.json'
t = mdn.read_text(encoding='utf-8')
fx = B2/f'ocr/fixes/{ch}.json'
r = dict(md_identical=mdn.read_bytes()==mdf.read_bytes(), chars=len(t),
         lines=len(t.split(chr(10))), old=t.count(EXP['old']), new=t.count(EXP['new']),
         images=len(list((fin/'images').iterdir())), cl_norm=h(cln), cl_final=h(clf),
         fx=h(fx), nfix=len(json.loads(fx.read_text(encoding='utf-8'))['fixes']))
good = (r['md_identical'] and r['chars']==EXP['chars'] and r['lines']==EXP['lines']
        and r['old']==1 and r['new']==0 and r['images']==EXP['images']
        and r['cl_norm']==EXP['cl'] and r['cl_final']==EXP['cl']
        and r['fx']==EXP['fx'] and r['nfix']==EXP['nfix'])
print(ch, 'OK' if good else 'MISMATCH', r)
print('PROCEED' if good else 'ABORT')
" chap01
```

（chap02・chap03・chap08 についても、それぞれの章の手順1 の直前に引数を変えて実行する。）

- 期待: 当該章が `OK` で、最終行が `PROCEED` であること（期待値は手順0 の表と同じ）
- `ABORT` の場合は、その章の手順1 に進まず**中断して報告する**
- **手順0 を4章分まとめて再実行してはならない**（処理済みの章が `MISMATCH` になるため）

### 手順1: 修正定義ファイルへの追記

§4.2 の内容で4ファイルを更新する。**§2.1 の順序で1章ずつ処理する**（手順0-B → 手順1 → 手順2 →
手順3 を章ごとに完結させる）。各章の手順1 に入る前に、その章について手順0-B を実行して
`PROCEED` であることを確認する。

- 既存 JSON を読み込み、`fixes` 配列の末尾に新規1件を `append` して書き戻す。
  既存要素の4キーを1文字も変更しないこと
- 追記前に §4.1 の SHA-256 と既存 ID を照合し、**異なっていた場合は上書きせず中断して報告する**
- 追記後に次を確認する:
  1. `uv run python -c "import json; json.load(open(...))"` で JSON として妥当であること
  2. `fixes` 配列の要素数が期待値（chap01 = 3 / chap02 = 5 / chap03 = 7 / chap08 = 2）であること
  3. 既存要素が1件も変わっていないこと。退避した `"$SCRATCH/{ch}.json.before"` を読み込み、
     追記後のファイルの先頭 N 件（N = 既存件数）と**オブジェクトとして等しい**ことを比較する

     ```bash
     uv run python -c "
     import json, sys
     ch = sys.argv[1]; n = int(sys.argv[2]); scratch = sys.argv[3]
     before = json.load(open(f'{scratch}/{ch}.json.before', encoding='utf-8'))['fixes']
     after  = json.load(open(f'/home/sakagawa/work/確率統計/ocr/fixes/{ch}.json', encoding='utf-8'))['fixes']
     assert len(before) == n and len(after) == n + 1, (len(before), len(after))
     assert after[:n] == before, 'EXISTING FIXES CHANGED'
     print(ch, 'APPEND_OK', after[n]['id'])
     " chap01 2 "$SCRATCH"
     ```

     （chap02 は `chap02 4`、chap03 は `chap03 6`、chap08 は `chap08 1`。）

### 手順2: 修正の適用（章ごと）

```bash
B2=/home/sakagawa/work/確率統計
ch=chap01   # 以降 chap02 / chap03 / chap08 について同様に実行する
uv run python scripts/apply_fixes.py \
  "$B2/ocr/mineru-full/$ch/run-01-normalized/${ch}_gray300.md" \
  "$B2/ocr/fixes/${ch}.json" \
  -o "$B2/ocr/mineru-full/$ch/run-01-normalized" --overwrite
```

- 出力先を入力と同じディレクトリにし、`--overwrite` でインプレース更新する
  （feat-013 ADR-4・feat-015・feat-017・feat-019 と同じ）
- 期待: 終了コード 0、標準出力に次の2行（`{N}` は章ごとの skipped 数）

  ```
  {ch}_gray300.md: 1 applied, {N} skipped
  total: 1 applied, {N} skipped
  ```

  | 章 | applied | skipped |
  |---|---|---|
  | chap01 | 1 | 2 |
  | chap02 | 1 | 4 |
  | chap03 | 1 | 6 |
  | chap08 | 1 | 1 |

- **`applied` / `skipped` が上表と異なる場合は、終了コードが 0 でも次の手順に進まず中断して
  報告する**（feat-014 で顕在化した論点。終了コード 0 は不変条件の充足を意味するが、
  想定と異なる件数が適用された可能性を排除できない）
- **手順2 が終了コード 0 以外で終わった場合、または `applied` / `skipped` が上表と異なる場合は、
  後述の「失敗時の復元（手順1〜手順3 に共通）」に従って当該章の3点（`{NORM_NN}` の md・
  `{FINAL_NN}`・修正定義ファイル）を退避から復元してから中断・報告する。**
  この時点で修正定義ファイルは既に追記済みであり、復元しないと次回の手順1 の SHA-256 照合が
  必ず失敗して再開できない（`apply_fixes.py` はエラー時に md を書かないが、
  `applied` / `skipped` 不一致は終了コード 0 で md が書かれているため、md も併せて戻す）

### 手順3: final の再構築（章ごと）

```bash
B2=/home/sakagawa/work/確率統計
ch=chap01   # 以降 chap02 / chap03 / chap08 について同様に実行する
uv run python scripts/build_final.py \
  "$B2/ocr/mineru-full/$ch/run-01-normalized" \
  -o "$B2/ocr/final/$ch" --overwrite
```

- 期待: 終了コード 0（バイト同一・画像参照・`img_path` 集合一致の3検証がすべて合格）

### 失敗時の復元（手順1〜手順3 に共通）

**本手順は、手順1・手順2・手順3 のいずれかが期待どおりに終わらなかったときに実行する。**
発動条件は次のとおり（いずれも §9 のエラーハンドリング表に対応する）。

| 発動する手順 | 条件 |
|---|---|
| 手順1 | 追記後の JSON 妥当性確認・要素数確認・`APPEND_OK` 確認のいずれかが失敗した |
| 手順2 | `apply_fixes.py` の終了コードが 0 以外、または `applied` / `skipped` が §6 手順2 の表と異なる |
| 手順3 | `build_final.py` の終了コードが 0 以外 |

**復元は、その章について既に書き換えた対象だけを戻せばよい**（手順1 で失敗したなら
修正定義ファイルのみ、手順2 以降で失敗したなら3点すべて）。判断に迷う場合は3点すべてを
復元してよい（退避からの復元は冪等である）。

**手順3 で失敗した場合に復元が必須である理由**（手順1・手順2 の失敗では `{FINAL_NN}` は未変更）:

`build_final.py` は**ファイル単位では原子的**（一時ファイルに書いてから `os.replace` で
差し替える `copy_atomic`）だが、**ディレクトリ全体としては原子的ではない**
（md → content_list.json → images/ の順に上書きし、孤児画像を削除したうえで最後に3検証を行う。
`scripts/build_final.py` の `main()` を 2026-09-02 に確認）。

そのため、コピーの途中で失敗した場合や3検証が不合格（終了コード 1）だった場合、
**`{FINAL_NN}` が新旧混在の部分更新状態で残りうる**。この状態を放置してはならない。

対応（**失敗した章についてのみ行う**）:

1. **その場で再実行やリトライをしない**
2. 退避した `"$SCRATCH/final_{ch}.before"` から `{FINAL_NN}` を復元する

   ```bash
   B2=/home/sakagawa/work/確率統計
   ch=chap01   # 失敗した章
   rm -rf "$B2/ocr/final/$ch"
   cp -a "$SCRATCH/final_${ch}.before" "$B2/ocr/final/$ch"
   diff -r "$SCRATCH/final_${ch}.before" "$B2/ocr/final/$ch" && echo RESTORED
   ```

3. **`{NORM_NN}` 側の md も退避から復元する**（下記の理由により必須）

   ```bash
   cp "$SCRATCH/${ch}_gray300.md.before" \
      "$B2/ocr/mineru-full/$ch/run-01-normalized/${ch}_gray300.md"
   ```

4. **修正定義ファイルも退避から復元する**（追記済みのまま残すと、次回の手順1 の
   SHA-256 照合で必ず中断して再開できないため）

   ```bash
   cp "$SCRATCH/${ch}.json.before" "$B2/ocr/fixes/${ch}.json"
   ```

5. 復元後、`{NORM_NN}` と `{FINAL_NN}` が**再びバイト同一**であることを確認する
   （手順0 の事前確認が通る状態に戻ったことの検証）

   ```bash
   cmp "$B2/ocr/mineru-full/$ch/run-01-normalized/${ch}_gray300.md" \
       "$B2/ocr/final/$ch/${ch}_gray300.md" && echo NORM_FINAL_IDENTICAL
   ```

   あわせて、**手順0-B**（当該章のみを検査する版）を実行し、**その章が再び `OK` / `PROCEED` に
   なること**を確認する。**手順0 を4章分まとめて再実行してはならない**（既に処理を終えた章が
   `MISMATCH` になるため）
6. `RESTORED` と `NORM_FINAL_IDENTICAL` を確認したうえで、**何が起きたか・どの章をどこまで
   処理したか・当該章の `{NORM_NN}` / `{FINAL_NN}` / 修正定義ファイルの3つすべてを修正前の状態に
   復元したことを報告して中断する**。**後続の章には進まない**

**`{NORM_NN}` と修正定義ファイルも必ず復元すること。** `apply_fixes.py` は冪等なので
`{NORM_NN}` を修正済みのまま残しても再適用自体は安全に見えるが、その状態では
`{NORM_NN}`（修正済み）と `{FINAL_NN}`（修正前）がバイト同一でなくなり、**手順0-B の確認で
必ず中断する**ため、次回の実行を再開できない。3つとも修正前に戻すことで、手順0-B から素直に
やり直せる状態になる。

## 7. 確認手順（FR-002〜FR-005 の受け入れ基準）

### 手順1: 修正内容の確認

手順0 と同じ数え方（`str.count()` による出現回数）で、`{NORM_NN}` と `{FINAL_NN}` の
両方の md を確認する。

```bash
uv run python -c "
from pathlib import Path
B2 = Path('/home/sakagawa/work/確率統計')
EXP = {
 'chap01': dict(chars=24777, lines=584, ln=298, old='描いたらいんでしたっけ', new='描いたらいいんでしたっけ',
                frag='どんなやり方で描いたらいいんでしたっけ'),
 'chap02': dict(chars=68839, lines=1859, ln=1395, old='こぜんぶ覚えない', new='これぜんぶ覚えない',
                frag='2.10 これぜんぶ覚えないといけませんか'),
 'chap03': dict(chars=53925, lines=1460, ln=585, old='賭けるということですよね', new='賭けろということですよね',
                frag='期待値の高いほうに賭けろということですよね'),
 'chap08': dict(chars=67199, lines=1566, ln=520, old='そういうことだる', new='そういうことだろ',
                frag='高い。そういうことだろ'),
}
ok = True
for ch, e in EXP.items():
    for label, p in [('NORM',  B2/f'ocr/mineru-full/{ch}/run-01-normalized/{ch}_gray300.md'),
                     ('FINAL', B2/f'ocr/final/{ch}/{ch}_gray300.md')]:
        t = p.read_text(encoding='utf-8'); lines = t.split(chr(10))
        good = (t.count(e['old'])==0 and t.count(e['new'])==1 and len(t)==e['chars']
                and len(lines)==e['lines'] and e['frag'] in lines[e['ln']-1])
        ok = ok and good
        print(ch, label, 'OK' if good else 'MISMATCH',
              'old', t.count(e['old']), 'new', t.count(e['new']),
              'chars', len(t), 'lines', len(lines))
print('ALL_OK' if ok else 'ABORT')
"
```

期待値（`{NORM_NN}` / `{FINAL_NN}` とも同じ。4章 × 2 = 8 行すべて `OK`、最終行が `ALL_OK`）:

| 項目 | 期待値 | 対応する受け入れ基準 |
|---|---|---|
| 誤読文字列（`old`）の出現回数 | 0（4章とも） | FR-002 基準1 |
| 訂正後文字列（`new`）の出現回数 | 1（4章とも） | FR-002 基準2 |
| 該当行に `frag` が含まれること | 真（4章とも） | FR-002 基準4 |
| 文字数 | chap01 = 24777 / chap02 = 68839 / chap03 = 53925 / chap08 = 67199 | FR-003 基準3 |
| 行数 | chap01 = 584 / chap02 = 1859 / chap03 = 1460 / chap08 = 1566 | FR-003 基準4 |

**スコープ外が変更されていないこと**もあわせて確認する（FR-005 基準4・requirements.md §7）。

```bash
uv run python -c "
from pathlib import Path
B2 = Path('/home/sakagawa/work/確率統計/ocr/final')
l8 = B2.joinpath('chap08/chap08_gray300.md').read_text(encoding='utf-8').split(chr(10))[519]
l3 = B2.joinpath('chap03/chap03_gray300.md').read_text(encoding='utf-8').split(chr(10))[584]
print('chap08 L520 starts with \'? 8.6\' (## を補っていない):', l8.startswith('? 8.6'))
print('chap08 L520 does NOT start with \'##\':', not l8.startswith('##'))
print('chap03 L585 ends with half-width ? (全角にしていない):', l3.endswith('?'))
print('chap03 L585 does NOT end with 全角？:', not l3.endswith('？'))
"
```

4行とも `True` であること。

さらに、確率統計の final 全10章に対するバリアント調査を再実行する（FR-002 基準5）。

```bash
uv run python -c "
import re
from collections import Counter
from pathlib import Path
base = Path('/home/sakagawa/work/確率統計/ocr/final')
for k, p in [('A', r'.{6}でしたっけ'), ('B', r'.{4}ぜんぶ'), ('C', r'賭け.{0,4}'), ('D', r'.{4}だ[るろ]')]:
    c = Counter()
    for f in sorted(base.glob('chap*/*.md')):
        for m in re.findall(p, f.read_text(encoding='utf-8')):
            c[m] += 1
    print(k, 'total', sum(c.values()), dict(sorted(c.items())) if k != 'D' else
          {'だる系': {x: n for x, n in c.items() if x.endswith('だる')}})
"
```

期待される出力（2026-09-03 に適用前後を実測して求めた値）:

| 記号 | 期待 |
|---|---|
| A | `total 4`。`いたらいいんでしたっけ` 1 / `ってどんな話でしたっけ` 1 / `どこが違うのでしたっけ` 1 / `やって導くのでしたっけ` 1（適用前の `描いたらいんでしたっけ` が消える） |
| B | `total 5`。`)$ をぜんぶ` 2 / `0 これぜんぶ` 1 / `やすさをぜんぶ` 1 / `エ’）もぜんぶ` 1（適用前の `10 こぜんぶ` が消える） |
| C | `total 16`。`賭けるという` が消え `賭けろという` が 1 になる。他の14件（`賭けるほうが` を含む）は変化なし |
| D | `total 39`、`だる系` が **空**（適用前は `いうことだる` 1。`…だろ` 38 件は変化なし） |

**A・B は正規表現の先読み文字数の都合で、適用前後でマッチ文字列の先頭が変わる**
（`描いたらいんでしたっけ` → `いたらいいんでしたっけ`、`10 こぜんぶ` → `0 これぜんぶ`）。
これは1文字の挿入によるもので、想定どおりである。

### 手順2: 差分が該当箇所のみであることの確認

手順0 で退避した適用前の md と、適用後の md の `diff` を章ごとに取る。

```bash
B2=/home/sakagawa/work/確率統計
for ch in chap01 chap02 chap03 chap08; do
  echo "===== $ch"
  diff "$SCRATCH/${ch}_gray300.md.before" "$B2/ocr/final/$ch/${ch}_gray300.md"
done
```

期待される差分は**各章ともハンク1つのみ**で、§4.3 の行の削除と追加の1組である。
他の行に差分があってはならない（FR-003 基準5）。

### 手順3: 非影響の確認（FR-004）

```bash
git status --short
```

**この確認は実装（CLAUDE.md 機能追加フローのステップ6）の時点で行う。**
`docs/CHANGELOG.md`・`docs/PROJECT_KNOWLEDGE.md` の更新と `docs/BACKLOG.md` のステータス
Closed 化は完了処理（ステップ8）で Claude Code 本体が行うため、**この時点ではまだ
変更されていない**。

期待される変更は次の3件のみである。それ以外（`scripts/`・`tests/test_*.py`・
`docs/CHANGELOG.md`・`docs/PROJECT_KNOWLEDGE.md`・**`CLAUDE.md`**・ルートの `README.md`・
`docs/issues/feat-020-qa-heading-not-recognized/`）に変更があってはならない。

| パス | 状態 | 理由 |
|---|---|---|
| `docs/issues/feat-022-qa-heading-vocab-misread/` | `??`（未追跡） | 案件ドキュメント。起票時（ステップ1〜3）に作成済み |
| `docs/BACKLOG.md` | `M` | 起票時に feat-022 の行を追加済み |
| `tests/results/feat-022_test_result.txt` | `??`（未追跡） | 手順4 で新規作成する |

完了処理（ステップ8）の後は、上記に加えて `docs/CHANGELOG.md` と
`docs/PROJECT_KNOWLEDGE.md` が `M` になり、`docs/BACKLOG.md` のステータスが `Closed` に変わる。
これは想定どおりの変更であり、本手順の検証対象ではない。

さらに次を確認する。

```bash
uv run python -c "
import hashlib
from pathlib import Path
B2 = Path('/home/sakagawa/work/確率統計')
EXP = {'chap01': ('bd53e369c349f2754e110642d8801577f5dd320c2b04d06303899ede243bc92a', 27),
       'chap02': ('a4ebb69a04863ac89c6b7ef1e2cf737377b20b168f50aa665ad523bf3aff260f', 47),
       'chap03': ('d269034e9b54fd993a3d4f9e092421a3b7974d3441519eb389678055e5103220', 66),
       'chap08': ('7febf605cd86d279257d4d6c519bf626cf028d06c4147ac0703a391a61c83426', 43)}
h = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
ok = True
for ch, (sha, n) in EXP.items():
    cln = B2/f'ocr/mineru-full/{ch}/run-01-normalized/{ch}_gray300_content_list.json'
    clf = B2/f'ocr/final/{ch}/{ch}_gray300_content_list.json'
    imgs = len(list((B2/f'ocr/final/{ch}/images').iterdir()))
    good = h(cln) == sha and h(clf) == sha and imgs == n
    ok = ok and good
    print(ch, 'OK' if good else 'MISMATCH', 'images', imgs)
print('ALL_OK' if ok else 'ABORT')
"
```

- 各 `{FINAL_NN}/images/` のファイル数が変わっていないこと（chap01 = 27 / chap02 = 47 /
  chap03 = 66 / chap08 = 43）
- 各章の `chapNN_gray300_content_list.json` が `{NORM_NN}` と `{FINAL_NN}` の**両方で
  バイト単位で変更されていない**こと（FR-003 基準8）。`git` 管理外のため、手順0 で記録した
  SHA-256 と照合して検証する。mtime とサイズの比較では、同サイズの変更や mtime の復元を
  検出できないため用いない

最後に、**§6 手順A のコマンドを再実行**し、`git` 管理外の不変対象が変更されていないことを
検証する（FR-004 基準3・4・5）。

- 出力先を `"$SCRATCH/invariant_manifest_after.txt"` に変えて実行し、
  `files = 513` かつ `AGGREGATE = 68f5af84c591ee2e657d6be3483283186d2802ec4492c35f55e624b7aa976414`
  であること（手順A で記録した値と同一）
- あわせて `diff "$SCRATCH/invariant_manifest_before.txt" "$SCRATCH/invariant_manifest_after.txt"` が
  **無出力**であること
- 一致しない場合は、上記 `diff` の出力から**どのファイルが変わったかを特定し、中断して報告する**

この検証により、`git status` では検出できない次の3種類の非影響が確認できる。

| 対象 | 対応する受け入れ基準 |
|---|---|
| 確率統計の非対象6章（chap00・04・05・06・07・09）の成果物 | FR-004 基準3 |
| 既存の修正定義ファイル5件（chap04・05・06・07・09） | FR-004 基準4 |
| PRML（`{BASE}`）の成果物 | FR-004 基準5 |

### 手順4: 自動テストの全件実行（FR-004 基準7）

```bash
uv run pytest -v > tests/results/feat-022_test_result.txt 2>&1
```

- コード変更がないため、feat-021 完了時点（**236 passed**）と同じくすべて成功することを確認する
- 上記コマンドは出力を `tests/results/feat-022_test_result.txt` に**保存しながら**実行する
  （CLAUDE.md「テスト」のルール: テストコマンドの出力をそのまま保存する）。
  保存後、ファイルの末尾で全件成功（`failed` が 0 件）であることを確認する

## 8. md と content_list.json の非対称性（既知事項）

`apply_fixes.py` は md のみを対象とし、`content_list.json` を変更しない（feat-010 の設計）。
そのため最終的な状態は次のようになる。

| ファイル | 当該箇所の状態 | 理由 |
|---|---|---|
| `final/chapNN/chapNN_gray300.md` | 訂正後（正しい） | `apply_fixes.py` の適用対象 |
| `final/chapNN/chapNN_gray300_content_list.json` | 誤読のまま（4章とも各1件） | `apply_fixes.py` の対象外 |

これは feat-013 §6.1・feat-016 §8・feat-017 design.md §8・feat-019 design.md §8 で
許容済みの既存ポリシーであり、本案件では変更しない。LLM に読ませる主成果物は md であり、
`content_list.json` の主用途は `page_idx` による原本ページとの対応付けと図ブロックの座標参照
である（feat-005 ADR-7）ため、実用上の影響はない。また `build_final.py` の検証はコピー元と
final のバイト同一性・画像参照の整合を見るものであり、md と json の間の本文の一致は
検査しないため、検証にも影響しない。

**この非対称性は後続案件に影響する。** feat-021 が指摘したとおり（`collation_summary.md` §8-2）、
content_list を基準に走査すると本案件で修正した4件は誤読のままに見える。
本案件の完了後に content_list 基準の走査を行う案件は、**md 側が修正済みであることを
前提に読む**必要がある。この点は `docs/PROJECT_KNOWLEDGE.md` に記載済みの既知事項である。

## 9. エラーハンドリングと境界条件

| 事象 | 挙動 | 対応 |
|---|---|---|
| `old` が md に存在しない（0件）かつ `new` が1件 | `apply_fixes.py` は `skipped` として扱い終了コード 0・内容不変 | 冪等性の担保。手順2 を2回実行しても安全 |
| `old` が2件以上 | `apply_fixes.py` がエラー終了（出力なし） | §6「失敗時の復元」に従い当該章を復元してから中断・報告する（想定外。文面が変わっている） |
| `old` も `new` も0件 | `apply_fixes.py` がエラー終了（出力なし） | §6「失敗時の復元」に従い当該章を復元してから中断・報告する |
| 適用後に `new` が2件以上 | 最終不変条件違反でエラー終了（出力なし） | §6「失敗時の復元」に従い当該章を復元してから中断・報告する（§5 の実測と矛盾する） |
| 既存 fix が最終不変条件に違反 | 同上 | §6「失敗時の復元」に従い当該章を復元してから中断・報告する（先行案件の適用状態が変わっている） |
| `apply_fixes.py` の終了コードが 0 でも `applied` / `skipped` が §6 手順2 の表と異なる | md は書き換わっている（終了コード 0 のため） | **次の手順に進まず**、§6「失敗時の復元」に従い当該章の3点（`{NORM_NN}` の md・`{FINAL_NN}`・修正定義ファイル）を復元してから中断・報告する |
| 修正定義ファイルが JSON として不正 | `apply_fixes.py` が読み込み時にエラー終了 | §6「失敗時の復元」に従い修正定義ファイルを復元し、追記内容を見直して中断・報告する（手順1 の JSON 妥当性確認で事前に検出する） |
| 既存ファイルの SHA-256 が §4.1 の表と異なる | — | 上書きせず**中断して報告する**（手順1） |
| 手順1 の `APPEND_OK` 確認で `EXISTING FIXES CHANGED` が出る、または追記後の要素数が期待値と異なる | — | §6「失敗時の復元」に従い退避（`"$SCRATCH/{ch}.json.before"`）から修正定義ファイルを復元し、中断して報告する（この時点では md・`{FINAL_NN}` は未変更のため復元不要） |
| `build_final.py` の3検証のいずれかが不合格、またはコピー途中で失敗 | 終了コード 1。**`{FINAL_NN}` が部分更新状態で残りうる**（ディレクトリ全体としては原子的でないため） | §6「失敗時の復元」に従い、退避から **`{FINAL_NN}`・`{NORM_NN}` の md・修正定義ファイルの3つ**を復元する。復元後に `{NORM_NN}` と `{FINAL_NN}` がバイト同一であること・**手順0-B**（当該章のみを検査する版）が `OK` / `PROCEED` になることを確認し、復元したことを明記して中断・報告する。**後続の章には進まない** |
| ある章で失敗し、先行する章は成功済み | — | 失敗した章のみ復元する。成功済みの章は戻さない（章どうしは独立しており、各章の `{NORM_NN}` と `{FINAL_NN}` は整合している）。どの章まで完了したかを明記して報告する |
| 手順0 の退避（md・`{FINAL_NN}`・修正定義ファイルのコピー）に失敗 | — | 手順1 に進まず中断して報告する（復元手段がない状態で書き換えないため） |
| 手順A のマニフェストが期待値と異なる | — | 中断して報告する |
| 手順0 が `ABORT`（4章のいずれかが `MISMATCH`） | — | 手順0-B に進まず中断して報告する |
| 手順0-B が `ABORT`（当該章が `MISMATCH`） | — | その章の手順1 に進まず中断して報告する。**処理済みの章を戻す必要はない**（章どうしは独立している） |
| 処理済みの章がある状態で手順0 を4章分まとめて再実行した | 処理済みの章が `MISMATCH` になり `ABORT` する | 手順0 は一度だけ実行する設計である（§6 手順0）。章ごとの確認には手順0-B を使う |
| `run-01-normalized` が存在しない、または最大の run 番号でない | — | 中断して報告する |
| 出力先が入力と同一・入れ子、またはシンボリックリンク | `build_final.py` が書き込み前に拒否 | 本案件のパス指定では発生しない（`{NORM_NN}` と `{FINAL_NN}` は別ツリー） |

## 10. 実装の担当と進め方

CLAUDE.md「実装の実行方法（Sonnetサブエージェント）」に従い、**Agent ツールで model: sonnet を
指定したサブエージェントに委任する**。委任時に渡す情報は次のとおり。

1. 必読ドキュメントと順序: `CLAUDE.md` → `docs/PROJECT_KNOWLEDGE.md` → 本案件の `README.md` →
   `requirements.md` → 本 `design.md` → `fixes/README.md`・`fixes/template.json` →
   `scripts/apply_fixes.py`・`scripts/build_final.py`
2. 厳密準拠（本書に書かれていない独自判断・改善・リファクタは禁止。**コードは1行も変更しない**）
3. 想定外事象（§9 の「中断して報告する」に該当する事象を含む）が起きたら回避策を実装せず
   直ちに中断し、何が起きたか・どこまで完了したかを報告して終了する
4. 検証まで実施（§6 の手順A・手順0・手順0-B・手順1〜3 と §7 の手順1〜4、
   `tests/results/feat-022_test_result.txt` への保存）。**手順0 の退避（md・`{FINAL_NN}` 全体・
   修正定義ファイル）を4章すべてについて必ず先に行い、手順1〜手順3 のいずれかが期待どおりに
   終わらなかった場合は §6「失敗時の復元」に従って当該章を復元してから報告する**
5. 禁止事項: git commit / push、`docs/BACKLOG.md` / `docs/CHANGELOG.md` / `CLAUDE.md` /
   `README.md` / `docs/PROJECT_KNOWLEDGE.md` の更新（完了処理で Claude Code 本体が行う）、
   **`docs/issues/feat-020-qa-heading-not-recognized/` の変更**
6. 報告形式: 変更ファイル一覧、テスト結果サマリ、§7 の確認結果（章ごと）、想定外事象の有無

## 11. ドキュメントの更新（完了処理で Claude Code 本体が実施する）

| ファイル | 更新内容 |
|---|---|
| `docs/BACKLOG.md` | feat-022 のステータスを Closed に更新する（行は起票時に追加済み）。**feat-020 の行に「chap08 `? 8.6` の `old` は feat-022 適用後の md（「そういうことだ**ろ**？」）に合わせて書くこと」を追記する**（FR-005。feat-020 の案件フォルダは変更せず、BACKLOG の備考で引き渡す） |
| `docs/CHANGELOG.md` | 完了内容を記録する |
| `docs/PROJECT_KNOWLEDGE.md` | 「データ」節の第2の書籍の項に、**Q&A 見出しの語彙誤読4件を修正済みであること**を1行追記する（feat-021 が記録した「74件中37件が不一致」の状態が本案件で一部解消したため）。**追記には案件 ID「（feat-022）」を付す**。ディレクトリ構成の変更はない（ファイルの追加・削除がないため） |
| **`CLAUDE.md`** | **更新しない。** update-003 で確定した非対称ルールにより、CLAUDE.md 本体の変更は update 案件でのみ行う |
| `README.md`（ルート） | **更新不要**。コマンド・CLI オプション・入出力形式・既定値・実行環境のいずれも変わらない |
| 案件 `README.md` | ステータスを Closed に更新する |
| `docs/issues/feat-020-qa-heading-not-recognized/` | **更新しない**（FR-005 基準3。引き渡しは BACKLOG の備考と本案件 README §2.1・§7 で行う） |

## 12. 設計判断の記録（ADR）

### ADR-1: 4件を字形正規化テーブルに入れず、修正定義ファイルで扱う

- **決定**: `normalize_punct.py` の `CJK_REPLACEMENTS_CN` / `OLD_FORM_REPLACEMENTS` に追加せず、
  `{BASE2}/ocr/fixes/chapNN.json` で補正する
- **理由**:
  1. 置換表は**1文字 → 1文字**の字形対応表である。chap01・chap02 の2件は「い」「れ」の
     **挿入**であり、1対1の字形対応として表現できない（feat-019 ADR-1 と同じ）
  2. chap03・chap08 の2件は「る」→「ろ」の1対1置換だが、**「る」も「ろ」も正当な日本語の文字**
     であり、全書籍に常時適用される置換表に入れれば大量の正当な「る」を壊す
     （確率統計の final だけで「る」は数千件ある）
  3. feat-011 ADR-3・feat-013 ADR-2・feat-015 ADR-1・feat-016 ADR-1・feat-017 ADR-1・
     feat-019 ADR-1 で確立した方針（字形の1対1対応が成立しない個別誤認識は
     `apply_fixes.py` で扱う）と一致する
- **代替案**: 置換表に4件を追加する → 置換表の意味が「字形正規化」から「文字列置換」に変質し、
  テーブルの適用範囲（全書籍・常時適用）とリスクが釣り合わない。不採用

### ADR-2: `old` / `new` に疑問符（`?` / `？`）を含めない

- **決定**: 4件の `old` / `new` はいずれも疑問符の手前で切る
  （例: chap08 は `そういうことだる` までとし `？` を含めない）
- **理由**: 対象4件のうち3件（1.8・2.10・8.6）は行末が全角「？」、1件（3.5）は半角「?」である。
  **約物の全角/半角ゆれは feat-021 の後続案件案 C（10件）の対象**であり、そこで文字が
  変更されると本案件の `old` / `new` が一致しなくなる。疑問符を含めなければ、
  案 C の実施順序に関わらず本案件の修正定義が有効なまま保たれる
- **代替案**: 行末の疑問符まで含めて一意化する → 一意化には不要であり（§5 の実測で
  疑問符なしでも全件一意）、後続案件との結合度を無用に上げる。不採用

### ADR-3: chap08 `? 8.6` は `D1` のみを修正し、`##` の補完は feat-020 に残す

- **決定**: 本案件では chap08 md 520 行の行頭を `? 8.6` のままとし、`## ` を補わない。
  **本案件を feat-020 より先に完了させる**
- **理由**:
  1. `##` の欠落（`D2`）は feat-020 のスコープ（19件）に含まれており、**19件を一括で扱う
     ほうが体裁の一貫性を保ちやすい**（1件だけ先に直すと feat-020 の受け入れ基準
     「19件すべてが `## ? N.M` になる」の起点がずれる）
  2. 語彙誤読（`D1`）は feat-016・017・019 と同系統であり、**4件をまとめて扱うほうが
     調査（バリアント走査）と検証を一度で済ませられる**
  3. 同じ行を2案件が触るため `old` に順序依存が生じるが、feat-020 は**未着手**であり、
     本案件を先に完了させれば feat-020 側が適用後の md を見て `old` を書けば済む
     （逆順にすると本案件の `old` を書き直す必要が生じる）
- **代替案1**: 本案件で `##` も同時に補う → feat-020 のスコープを侵食し、19件のうち1件だけが
  別案件で処理された状態になる。不採用
- **代替案2**: 8.6 の語彙誤読を feat-020 に渡す → 語彙誤読の調査・検証が2案件に分断され、
  feat-020 の要求仕様に `D1` の修正を追加する必要が生じる。ユーザーが 2026-09-03 に
  「4件すべてを本案件で扱う」と決定済み。不採用

### ADR-4: 章単位で「追記 → 適用 → 再構築」を完結させ、失敗時は当該章のみ復元する

- **決定**: §2.1 のとおり chap01 → chap02 → chap03 → chap08 の順に章ごとに処理し、
  失敗した章のみを退避から復元して後続の章には進まない
- **理由**: `apply_fixes.py`・`build_final.py` はいずれも**章単位**のインターフェースであり、
  章をまたぐ原子性はもともと提供されない。章どうしは独立しているため、途中まで完了した
  状態でも各章の `{NORM_NN}` と `{FINAL_NN}` は整合しており、再開が容易である
  （feat-013 で10章を章ごとに再適用した先例と同じ）
- **代替案**: 4章分の追記をすべて済ませてから4章の適用をまとめて行う → 失敗時に
  「どの章まで適用されたか」と「修正定義ファイルはどこまで追記されたか」がずれ、
  復元の手順が複雑になる。不採用

### ADR-5: 既存 fix を本書に転記せず、SHA-256 で照合する

- **決定**: §4.1 のとおり、既存 fix の内容を本書に転記せず、追記前のファイルの SHA-256 と
  fix 一覧（件数・ID）を照合することで「既存が想定どおりであること」を確認する
- **理由**: 対象4ファイルの既存 fix は計13件あり、chap02・chap03 の `old` には 64 桁の
  画像ハッシュを含む複数行文字列がある。**転記は誤りを持ち込む risk があり、
  SHA-256 の照合のほうが厳密**である。加えて実装は「読み込んだ既存要素をそのまま再利用して
  書き出す」append 方式であり、転記した内容を使わない
- **代替案**: feat-019 design.md §4 と同じく既存の JSON 全文を転記する → 4ファイル分で
  200 行を超え、転記ミスの risk が一意性の担保に寄与しない。不採用
  （feat-019 は1ファイル・既存3件だったため転記が現実的だった）

### ADR-6: MinerU と `normalize_punct.py` を再実行しない

- **決定**: `apply_fixes.py` と `build_final.py` のみを実行する
- **理由**: 語彙単位の誤読は OCR の認識結果に起因し、同一入力に対して同じ結果になるため、
  再実行しても再発する（`docs/PROJECT_KNOWLEDGE.md` ドメイン知識「OCR の個別誤り…再OCRでも再発する」）。
  `normalize_punct.py` は置換表を変更しないため結果が変わらず、冪等でもある
- **代替案**: `ocr_dir.py --punct-style touten --final --fixes-dir ...` で4章を再実行する →
  MinerU の実行時間が無駄であり、run 番号が増えて履歴が追いにくくなる。不採用
  （feat-013 ADR-3・feat-015 ADR-4・feat-016 ADR-2・feat-017 ADR-4・feat-019 ADR-3 と同じ判断）

### ADR-7: 知見の追記先を `docs/PROJECT_KNOWLEDGE.md` とし、`CLAUDE.md` を変更しない

- **決定**: §11 の追記は `docs/PROJECT_KNOWLEDGE.md` に案件 ID 付きで行い、
  `CLAUDE.md` は1文字も変更しない
- **理由**: update-003 で確定した非対称ルール（CLAUDE.md 本体の変更は update 案件でのみ、
  知識ファイルの内容は各案件の完了処理で更新）に従う。本件で追記するのは
  **データの状態の変化**（Q&A 見出しの語彙誤読が解消したこと）であり、統治文書に置く内容ではない
- **代替案**: `CLAUDE.md` のドメイン知識に追記する → update-003 で外出し済みのため
  参照先が存在しない。不採用
