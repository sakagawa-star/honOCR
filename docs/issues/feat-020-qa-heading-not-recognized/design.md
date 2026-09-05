# feat-020 機能設計書: Q&A コラム見出しが見出しとして認識されない19件の修正

対象案件: `docs/issues/feat-020-qa-heading-not-recognized/`
要求仕様書: 同フォルダの `requirements.md`
調査記録: 同フォルダの `README.md`（**§0.5「起票時の記載の訂正」を必ず読むこと**）

## 1. 対応要求マッピング

| 要求 | 設計箇所 |
|---|---|
| FR-001 修正定義ファイルへの追記（19件） | §4（追記内容）・§5（一意性の確認）・§6 手順1 |
| FR-002 19件すべてを正常な見出しにする | §4.2〜§4.4（型別の `old`/`new`）・§7 手順1 |
| FR-003 既存成果物への適用と final 再構築 | §6（適用手順）・§7（確認手順） |
| FR-004 影響範囲の限定 | §3（変更しないもの）・§6 手順A（不変対象マニフェスト）・§7 手順3 |
| FR-005 構造復元3件における例外の限定 | §4.4（3件の逐語的な `old`/`new`）・§7 手順1 |

## 2. システム構成

本案件は**リポジトリ内のコードを変更しない**。既存スクリプトを引数を変えて実行するのみである。

```
{BASE2} = /home/sakagawa/work/確率統計
対象9章 NN ∈ {00, 01, 02, 04, 05, 06, 07, 08, 09}（chap03 は対象外）

{NORM_NN}  = {BASE2}/ocr/mineru-full/chapNN/{RUN_NN}
{FINAL_NN} = {BASE2}/ocr/final/chapNN
{FIXES_NN} = {BASE2}/ocr/fixes/chapNN.json   ← 本案件で追記（chap00 は新規作成）

  {NORM_NN}/chapNN_gray300.md ──┐
                                ├─→ apply_fixes.py ──→ {NORM_NN}/chapNN_gray300.md（インプレース更新）
  {FIXES_NN} ───────────────────┘

  {NORM_NN}/（md + content_list.json + images/）
        └─→ build_final.py ──→ {FINAL_NN}/（再構築・3種類の機械検証）
```

### 2.1 `{RUN_NN}` の対応（**取り違え厳禁**）

| 章 | `{RUN_NN}` | 根拠 |
|---|---|---|
| chap00・01・02・04・05・06・08・09 | **`run-01-normalized`** | 各章に run は1つだけ（2026-09-05 実測） |
| **chap07** | **`run-02-normalized`** | chap07 のみ `run-01` と `run-02` があり、`{FINAL_07}` は **`run-02-normalized` と md・content_list.json がバイト同一**（`run-01-normalized` の md とは不一致）。2026-09-05 実測。案件 README §0.5 訂正6 |

実装時に各章で `ls {BASE2}/ocr/mineru-full/chapNN/` を実行し、上表の run が存在することと、
それが最大の run 番号であることを確認する。異なっていた場合は中断して報告する。

### 2.2 処理の単位と順序

**章単位で「直前確認（手順0-B）→ 追記 → 適用 → final 再構築」を完結させ、9章を次の順に処理する。**

```
chap00 → chap01 → chap02 → chap04 → chap05 → chap06 → chap07 → chap08 → chap09
```

（手順A の不変対象マニフェストと手順0 の事前確認は、9章の処理を始める前に**一度だけ**行う。）

- 章の処理が1つでも失敗した場合、**その章のみを退避から復元し、後続の章には進まず中断して報告する**
  （§6「失敗時の復元」）。既に完了した章はそのままでよい（章どうしは独立しており、
  途中まで完了した状態でも各章の `{NORM_NN}` と `{FINAL_NN}` は整合している）
- 順序に技術的な依存はない（章間に干渉がないことは §5.4 で示す）。再現性のために章番号順に固定する

## 3. 変更しないもの（FR-004・FR-005）

| 対象 | 理由 |
|---|---|
| `scripts/` 配下のすべてのファイル | 本案件はデータ側の修正のみで実現できる |
| `tests/test_*.py`（テストコード） | コード変更がないため。ただし `tests/results/feat-020_test_result.txt` は検証記録として**新規作成する**（§7 手順4） |
| **`CLAUDE.md`** | update-003 の非対称ルール（本体の変更は update 案件のみ）。本案件の知見は `docs/PROJECT_KNOWLEDGE.md` に追記する（§11） |
| 各 `{NORM_NN}/chapNN_gray300_content_list.json` | `apply_fixes.py` は md のみを対象とする（feat-010 の設計）。§8 の非対称性 |
| 各 `{NORM_NN}/images/`・`{FINAL_NN}/images/` | 画像は対象外。`build_final.py` がコピーするのみ |
| 既存の fix 計23件（chap01 3・chap02 5・chap04 2・chap05 3・chap06 6・chap07 1・chap08 2・chap09 1） | 先行案件で作成・適用済み。本案件では追記のみ |
| `{BASE2}/ocr/fixes/chap03.json` | chap03 は対象外（Q&A 8件すべて正常） |
| **確率統計 chap03 の成果物** | 同上 |
| PRML（`{BASE}`）の成果物 | 本案件は確率統計のみを対象とする |
| **「?」と番号の間の空白**（`?2.1`・`?2.12` は空白なしのまま） | 2026-09-05 ユーザー決定。原本側で空白文字の有無を確定できない（feat-021 ADR-10） |
| **既存の正常な見出し55件** | 表記ゆれ（`## ?N.M` 8件）を含めてスコープ外 |
| **併発する `D1`/`D4`**（chap02 2.9 のアキ・chap07 7.4 の全角括弧・chap09 B.1 の末尾疑問符・数式の平文化） | 2026-09-05 ユーザー決定。feat-021 の後続案件案 C・D・F に残す |
| **chap02 2.5 / chap07 7.3 の答え本文**（構造復元の対象ブロック内の質問文以外） | FR-005 基準2・3。フェンス・タグの削除と見出し化のみを行う |

## 4. 修正定義ファイルへの追記内容（FR-001）

### 4.1 追記の方法と追記前の状態

**既存 JSON を読み込み、`fixes` 配列の末尾に新規 fix を `append` して書き戻す。**
既存要素（4キー）を1文字も変更してはならない。**`chap00.json` は存在しないため新規作成する**
（`{"fixes": [ … ]}` の形。`fixes/template.json` と同じ体裁）。

追記の**前**に、対象ファイルが下表の状態であることを SHA-256 と fix 一覧で確認する。
**異なっていた場合は上書きせず中断して報告する。**

| ファイル | 追記前の SHA-256（2026-09-05 実測） | 既存 fix 数 | 既存 ID |
|---|---|---|---|
| `chap00.json` | **（ファイルなし）** | 0 | — |
| `chap01.json` | `a8f75c7bc5908968e02cc223a440952b22f90302fd1fb6ffa296d131d902959b` | 3 | `chap01-001`〜`003` |
| `chap02.json` | `d11d9c806b292b152f33da4c1015fbb86c8ffcd867b47d6a4676c4570acfb446` | 5 | `chap02-001`〜`005` |
| `chap04.json` | `2e692835caabe91a260eed0c928d40c79f534fe057404009cb5a7967c2995247` | 2 | `chap04-001`・`002` |
| `chap05.json` | `ba81054b982b5561aa6d44253390a5b847e2d5c66f07a313377748306302fa77` | 3 | `chap05-001`〜`003` |
| `chap06.json` | `789275036e063609dba386c9805d6d63d3a0b7b29fdc18518041ab2ca9453222` | 6 | `chap06-001`〜`006` |
| `chap07.json` | `675541de24b946911cd6201506c141cf29c1643e1cbb84b53d8f49444867e294` | 1 | `chap07-001` |
| `chap08.json` | `7830abe2948407621ed4fc5ade44bdeff6d3ff972a092299aaf157ac8a29db76` | 2 | `chap08-001`・`002` |
| `chap09.json` | `80e357d7091496e802992b1a3b54bfd1f3a98174ec42db6c97ab0ce3edf0594f` | 1 | `chap09-001` |

**既存 fix の内容は本書に転記しない**（複数行文字列と 64 桁の画像ハッシュを含むため、
転記は誤りを持ち込む risk がある）。上表の SHA-256 の一致をもって確認とする（feat-022 ADR-5 と同じ判断）。

書式は `fixes/template.json`・`fixes/README.md` に従う（キーは `id` / `reason` / `old` / `new` の
4つ、すべて文字列。JSON はインデント2・`ensure_ascii=False`・末尾改行ありで書き出す）。

### 4.2 型α（3件）: `## ` の後に `? ` を補う

`old` / `new` は**いずれも先頭に改行（`\n`。JSON では `\n` とエスケープ）を含める**。
行頭に固定するためであり、`old` の一意性の根拠でもある（§5）。

| ID | 章 | 番号 | `old` | `new` |
|---|---|---|---|---|
| `chap00-001` | chap00 | 0.2 | `\n## 0.2 なぜ線形代数本` | `\n## ? 0.2 なぜ線形代数本` |
| `chap01-004` | chap01 | 1.3 | `\n## 1.3 翻訳って言うけど` | `\n## ? 1.3 翻訳って言うけど` |
| `chap06-007` | chap06 | 6.2 | `\n## 6.2 パラレルワールド` | `\n## ? 6.2 パラレルワールド` |

### 4.3 型β（12件）と型γ（1件）: 行頭に `## `（型γは `## ? `）を補う

**「?」と番号の間の空白は現状のまま**とする（`?2.1` は `## ?2.1`、`? 2.9` は `## ? 2.9`）。

| ID | 章 | 番号 | 型 | `old` | `new` |
|---|---|---|---|---|---|
| `chap01-005` | chap01 | 1.10 | β | `\n? 1.10 確率論の本格的な` | `\n## ? 1.10 確率論の本格的な` |
| `chap02-006` | chap02 | 2.1 | β | `\n?2.1 P(Y = ウ` | `\n## ?2.1 P(Y = ウ` |
| `chap02-008` | chap02 | 2.9 | β | `\n? 2.9 「▲▲は` | `\n## ? 2.9 「▲▲は` |
| `chap02-009` | chap02 | 2.11 | β | `\n? 2.11 なぜ（オ）` | `\n## ? 2.11 なぜ（オ）` |
| `chap02-010` | chap02 | 2.12 | β | `\n?2.12 P(○○` | `\n## ?2.12 P(○○` |
| `chap04-004` | chap04 | 4.7 | β | `\n? 4.7 積分する順番` | `\n## ? 4.7 積分する順番` |
| `chap04-005` | chap04 | 4.8 | β | `\n? 4.8 なぜ` | `\n## ? 4.8 なぜ` |
| `chap05-004` | chap05 | 5.6 | β | `\n? 5.6 なぜ □` | `\n## ? 5.6 なぜ □` |
| `chap05-005` | chap05 | 5.10 | β | `\n? 5.10 いまの図` | `\n## ? 5.10 いまの図` |
| `chap07-003` | chap07 | 7.4 | β | `\n? 7.4 整数値の擬似乱数` | `\n## ? 7.4 整数値の擬似乱数` |
| `chap08-003` | chap08 | 8.6 | β | `\n? 8.6 ツキには波が` | `\n## ? 8.6 ツキには波が` |
| `chap09-002` | chap09 | B.1 | β | `\n? B.1 3σ 以上` | `\n## ? B.1 3σ 以上` |
| `chap02-007` | chap02 | 2.7 | γ | `\n2.7 さっきの例題 2.4 は` | `\n## ? 2.7 さっきの例題 2.4 は` |

**`chap08-003` の `old` について**: chap08 8.6 の質問文末尾は feat-022 で
「そういうことだ**る**？」→「そういうことだ**ろ**？」に修正済みである。本 `old` は
**行頭側のみ**を対象とし末尾に触れないため、feat-022 の適用状態に依存しない
（案件 README §0.5 訂正4）。

### 4.4 構造復元（3件）: ブロックの解体（FR-005）

**`old` / `new` は複数行文字列である**（JSON では改行を `\n` とエスケープする）。
以下は**逐語的な定義**であり、1文字も変えてはならない。空白の数（半角2つ連続の箇所がある）に注意する。

#### `chap02-011`（chap02 2.5・数式ブロック → 見出し）

`old`（3行。`$$` で囲まれた数式ブロック全体）:

```
$$
\text {2.5 もし} \mathrm{P} (X = a) = 0 \text {だったら} \mathrm{P} (Y = b | X = a) \text {はどうなるの？}
$$
```

`new`（1行）:

```
## ? 2.5 もし $\mathrm{P}(X = a) = 0$ だったら $\mathrm{P}(Y = b \mid X = a)$ はどうなるの？
```

- **本件のみインライン数式の記法を変更する**（FR-005 基準1）。`$$` ブロックのままでは
  見出しにできないため不可避である。数式は原本に一致させた
  （原本: `？2.5 もし $\mathrm{P}(X = a) = 0$ だったら $\mathrm{P}(Y = b \mid X = a)$ はどうなるの？`。
  feat-021 の突合記録および 2026-09-05 の原本 TIF 再確認による）
- 答えの段落（md の直後の行）には手を触れない。原本でも枠内は見出しのみである（§4.5）

#### `chap04-003`（chap04 4.6・HTML `div` → 見出し＋段落）

`old`（4行）:

```
<div class="mineru-algorithm" style="white-space: pre-wrap; font-family:monospace;">
? 4.6  $f_{X,Y}(x,y)$  と  $f_{Y,X}(y,x)$  は同じですか？
いつでも  $f_{X,Y}(x,y)=f_{Y,X}(y,x)$  です。それぞれの意味を考えれば納得いただけるでしょう。
</div>
```

`new`（3行。2行目は空行）:

```
## ? 4.6  $f_{X,Y}(x,y)$  と  $f_{Y,X}(y,x)$  は同じですか？

いつでも  $f_{X,Y}(x,y)=f_{Y,X}(y,x)$  です。それぞれの意味を考えれば納得いただけるでしょう。
```

- **質問行・答え行の文字は1文字も変更しない**（FR-005 基準2）。`$` の前後にある半角2つの空白も維持する
- `div` の開始タグ・終了タグを削除し、質問行の行頭に `## ` を補い、質問と答えの間に空行を1行入れる

#### `chap07-002`（chap07 7.3・コードブロック → 見出し＋本文）

`old`（12行。` ```txt ` から ` ``` ` まで）:

```
```txt
7.3 [0,1) って何ですか？

図7.5 のように括弧の微妙な違いで区間の種類を区別します。

- [a,b] → 「a ≤ x ≤ b な x たち」
- (a,b) → 「a < x < b な x たち」
- [a,b) → 「a ≤ x < b な x たち」
- (a,b) → 「a < x ≤ b な x たち」

連続値の一様分布としては [0,1) と [0,1] との違いを気にする必要はありません。ちょうどぴったり 1 が出る確率なんてどちらにせよゼロだからです (→ 4.2.1 項 (p.123) 「確率ゼロ」)。本文であえて [0,1) と書いているのは、世の中の擬似乱数列生成ルーチンの仕様にあわせるためです。
```
```

`new`（10行。フェンス2行を削り、1行目を見出しにしたもの）:

```
## ? 7.3 [0,1) って何ですか？

図7.5 のように括弧の微妙な違いで区間の種類を区別します。

- [a,b] → 「a ≤ x ≤ b な x たち」
- (a,b) → 「a < x < b な x たち」
- [a,b) → 「a ≤ x < b な x たち」
- (a,b) → 「a < x ≤ b な x たち」

連続値の一様分布としては [0,1) と [0,1] との違いを気にする必要はありません。ちょうどぴったり 1 が出る確率なんてどちらにせよゼロだからです (→ 4.2.1 項 (p.123) 「確率ゼロ」)。本文であえて [0,1) と書いているのは、世の中の擬似乱数列生成ルーチンの仕様にあわせるためです。
```

- **質問行以外の8行は1文字も変更しない**（FR-005 基準3）。箇条書きの `- ` はそのまま残す
  （原本でも箇条書き（●）で組まれている。§4.5）
- **chap07 の ` ```txt ` フェンスは、本件を解体した後も 4 つ残る**（適用前は 5 つ）。
  残る4つは Q&A 見出しとは無関係の正当なコードブロックである
  （md 283 行のプログラム例、544・565・576 行の端末セッション。2026-09-05 実測）。
  **「chap07 の ` ```txt ` が 0 件になる」ことを受け入れ基準にしてはならない**
  （本設計の初版はこれを誤っており、実装フェーズで発覚して修正した）
- 4番目の箇条書きの括弧の誤読（原本は `(a,b]` だが md は `(a,b)`）は**本案件では直さない**（§12）

**実装上の注意**: 本書のコードブロック内に ` ``` ` が現れるため、上の `old` / `new` を
そのままコピーすると Markdown の入れ子が壊れて見える。**実装時は md の当該行を直接読み取って
`old` を組み立てること**（§6 手順1 に手順を示す）。

### 4.5 原本の確認（2026-09-05 実施）

19件のうち16件（型α・β・γ）は feat-021 が全74件を原本 TIF と突合した記録
（`{BASE2}/ocr/collation/feat-021_qa_headings.md`。リポジトリ外）による。
**構造復元3件は、本案件として `scripts/crop_blocks.py` で原本を切り出して再確認した**。

| 章 | content_list の index | `page_idx` | 原本 TIF | 原本の枠内の構成 |
|---|---|---|---|---|
| chap02 | 264（`type=equation`） | 16 | `page-09_2R.tif` 相当 | **見出し1行のみ**（`？2.5 もし P(X = a) = 0 だったら P(Y = b\|X = a) はどうなるの？`） |
| chap04 | 379（`type=code`, `sub_type=algorithm`） | 25 | — | **見出し1行＋答えの段落1行** |
| chap07 | 78（`type=code`, `sub_type=code`） | 6 | — | **見出し1行＋段落＋箇条書き4項目（●）＋段落** |

確認の手順（再実行可能）:

```bash
uv run python scripts/crop_blocks.py \
  /home/sakagawa/work/確率統計/ocr/final/chap07/chap07_gray300_content_list.json \
  /home/sakagawa/work/確率統計/dewarping/chap07/out \
  -o "$SCRATCH/crops/chap07" --index 78 --margin 15 --max-width 1700
```

（chap02 は index 264、chap04 は index 379。）**実装フェーズでの再実行は必須としない。**

## 5. 一意性の確認（FR-001 受け入れ基準 5・6）

`apply_fixes.py` は適用後に**全 fix について `count(old) == 0` かつ `count(new) == 1`** を検査し、
1つでも破れていればエラー終了して出力を書かない（最終不変条件。feat-010 FR-003 規則6）。
そのため `old` の一意性だけでなく、**適用後に `new` がちょうど1件になることも事前に数える**
（`docs/PROJECT_KNOWLEDGE.md` の規定）。

2026-09-05 に各 `{FINAL_NN}/chapNN_gray300.md`（= 対応する `{NORM_NN}` の md とバイト同一）で実測した。

### 5.1 新規19件（章内での出現回数）

**19件すべてについて、適用前は `count(old) == 1` かつ `count(new) == 0`、
適用後は `count(old) == 0` かつ `count(new) == 1` である**（2026-09-05 実測。19件とも合格）。

型α・β・γ の16件は `old` の先頭に改行を含めることで行頭に固定しており、
`? N.M` / `## N.M` / `2.7 …` の形が章内に1つしかないことを実測で確認している。

### 5.2 既存23件（追記後も最終不変条件を満たすこと）

新規 fix を適用した後の md に対し、当該章の**全 fix**（既存 ＋ 新規）について
`count(old) == 0` かつ `count(new) == 1` を検算した結果、**違反は9章とも0件**であった
（2026-09-05 実測）。

| 章 | 検査した fix 数（既存 ＋ 新規） | 最終不変条件の違反 |
|---|---|---|
| chap00 | 0 + 1 = 1 | **なし** |
| chap01 | 3 + 2 = 5 | **なし** |
| chap02 | 5 + 6 = 11 | **なし** |
| chap04 | 2 + 3 = 5 | **なし** |
| chap05 | 3 + 2 = 5 | **なし** |
| chap06 | 6 + 1 = 7 | **なし** |
| chap07 | 1 + 2 = 3 | **なし** |
| chap08 | 2 + 1 = 3 | **なし** |
| chap09 | 1 + 1 = 2 | **なし** |

### 5.3 干渉が起きないことの根拠（章内）

- 新規 fix の `old` はいずれも当該章の既存 fix の `new` に部分文字列として含まれない。
  したがって既存の適用結果を壊さない
- 新規 fix の `new` はいずれも当該章の既存 fix の `new` と文字列として重ならない
- 同一章に複数の新規 fix がある場合（chap01 2 / chap02 6 / chap04 3 / chap05 2 / chap07 2）も、
  互いに部分文字列の関係にないため適用順に依存しない
- 上記はすべて §5.1・§5.2 の実測（全 fix が適用後 `count(old) == 0` かつ `count(new) == 1`）で
  確認済みである

### 5.4 干渉が起きないことの根拠（章間）

`apply_fixes.py` は **md 1ファイルと修正定義ファイル1件**を受け取り、そのファイル内でのみ
`str.count()` / `str.replace()` を行う（feat-010 の設計）。したがって章をまたぐ干渉は原理的に起きない。

### 5.5 適用による文字数・行数の変化（実測）

| 章 | 新規 fix | 文字数（前 → 後） | 行数（前 → 後） |
|---|---|---|---|
| chap00 | 1 | 11840 → **11842**（+2） | 437 → **437** |
| chap01 | 2 | 24777 → **24782**（+5） | 584 → **584** |
| chap02 | 6 | 68839 → **68836**（−3） | 1859 → **1857**（−2） |
| chap04 | 3 | 74001 → **73919**（−82） | 1927 → **1926**（−1） |
| chap05 | 2 | 87047 → **87053**（+6） | 1797 → **1797** |
| chap06 | 1 | 36397 → **36399**（+2） | 833 → **833** |
| chap07 | 2 | 22958 → **22955**（−3） | 592 → **590**（−2） |
| chap08 | 1 | 67199 → **67202**（+3） | 1566 → **1566** |
| chap09 | 1 | 71011 → **71014**（+3） | 2384 → **2384** |

- 増加は挿入する `## ` / `? ` の分（型α = +2、型β = +3、型γ = +5）
- **減少するのは構造復元3件を含む章**である。chap02 は数式ブロックの `$$`・`\text {}` の削除で
  −3 文字・−2 行、chap04 は `div` タグの削除で −82 文字・−1 行、
  chap07 はフェンスの削除で −3 文字・−2 行になる

## 6. 適用手順（FR-003）

### 作業用ディレクトリ `{SCRATCH}` の定義

本書で `{SCRATCH}` と書いた箇所は、**Claude Code のセッション用スクラッチパッド**
（`/tmp/claude-1000/-home-sakagawa-git-honOCR/{session-id}/scratchpad/feat020/`）を指す。
成果物ディレクトリ（`{BASE2}` 配下）とリポジトリの**外**であり、実装の冒頭で作成する。

```bash
SCRATCH=/tmp/claude-1000/-home-sakagawa-git-honOCR/{session-id}/scratchpad/feat020
mkdir -p "$SCRATCH"
```

**本書のシェルコマンド中では `{SCRATCH}` ではなくシェル変数 `"$SCRATCH"` の形で書いてある。
`{SCRATCH}` は本文の説明でのみ用いる記法であり、コマンドにそのまま貼り付けてはならない。**
保存期間はセッション中のみであり、恒久的な記録は
`tests/results/feat-020_test_result.txt` と案件ドキュメントに残す。

**MinerU（`ocr_dir.py`）と `normalize_punct.py` は実行しない。**

### 手順A: 不変対象マニフェストの記録（最初に一度だけ）

FR-004 基準3・4・5 の対象のうち、**`git` 管理外のため `git status` では変更を検出できない
ファイル群**について、SHA-256 のマニフェストを記録する。対象は次の**327ファイル**である。

- `{BASE2}/ocr/fixes/chap03.json` … 1ファイル
- 確率統計 **chap03** の `final/chap03/` 配下の全通常ファイル（再帰）
- PRML（`{BASE}`）の `ocr/final/chap00〜07/` 配下の全通常ファイル（再帰）

```bash
uv run python -c "
import hashlib
from pathlib import Path
B2 = Path('/home/sakagawa/work/確率統計/ocr')
B1 = Path('/home/sakagawa/work/Pattern_Recognition_and_Machine_Learning/ocr')
paths = [B2/'fixes'/'chap03.json']
paths += [p for p in (B2/'final'/'chap03').rglob('*') if p.is_file()]
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

期待値（2026-09-05 実測）:

- `files = 327`
- `AGGREGATE = de46d2b04f2afa7fe299b1baccbfddfe76520d09062881e2a4de75aa65dedc8b`

**この2値が期待と異なる場合は、その場で回避策を取らず中断して報告する。**

### 手順0: 事前確認（9章の処理を開始する前に**一度だけ**行う）

```bash
uv run python -c "
import hashlib, json
from pathlib import Path
B2 = Path('/home/sakagawa/work/確率統計')
EXP = {
 'chap00': dict(run='run-01-normalized', chars=11840, lines=437,  images=2,  nfix=0,
   cl='1e7ca0c6d1ebf6e557ec56d063344712f17c9bf7f04605c55ea253dd057121e7', fx=None),
 'chap01': dict(run='run-01-normalized', chars=24777, lines=584,  images=27, nfix=3,
   cl='bd53e369c349f2754e110642d8801577f5dd320c2b04d06303899ede243bc92a',
   fx='a8f75c7bc5908968e02cc223a440952b22f90302fd1fb6ffa296d131d902959b'),
 'chap02': dict(run='run-01-normalized', chars=68839, lines=1859, images=47, nfix=5,
   cl='a4ebb69a04863ac89c6b7ef1e2cf737377b20b168f50aa665ad523bf3aff260f',
   fx='d11d9c806b292b152f33da4c1015fbb86c8ffcd867b47d6a4676c4570acfb446'),
 'chap04': dict(run='run-01-normalized', chars=74001, lines=1927, images=98, nfix=2,
   cl='a5fd16baa99e391b6fbd8a0cdfed1d06218332eb1a14f54eae5f551eeca8b8df',
   fx='2e692835caabe91a260eed0c928d40c79f534fe057404009cb5a7967c2995247'),
 'chap05': dict(run='run-01-normalized', chars=87047, lines=1797, images=78, nfix=3,
   cl='ba0f8398748440fc3da1325928f836e7e0f652c64ca8931d5e463189df5dfd48',
   fx='ba81054b982b5561aa6d44253390a5b847e2d5c66f07a313377748306302fa77'),
 'chap06': dict(run='run-01-normalized', chars=36397, lines=833,  images=19, nfix=6,
   cl='f41ce4ca1b838792ede2a985ac08466fb5fdcc6ccc1704d02355ce903bd99860',
   fx='789275036e063609dba386c9805d6d63d3a0b7b29fdc18518041ab2ca9453222'),
 'chap07': dict(run='run-02-normalized', chars=22958, lines=592,  images=16, nfix=1,
   cl='559b51624039af8209af3196c75a765df2befe6fbdc983fa9c25086f304b8d0e',
   fx='675541de24b946911cd6201506c141cf29c1643e1cbb84b53d8f49444867e294'),
 'chap08': dict(run='run-01-normalized', chars=67199, lines=1566, images=43, nfix=2,
   cl='7febf605cd86d279257d4d6c519bf626cf028d06c4147ac0703a391a61c83426',
   fx='7830abe2948407621ed4fc5ade44bdeff6d3ff972a092299aaf157ac8a29db76'),
 'chap09': dict(run='run-01-normalized', chars=71011, lines=2384, images=25, nfix=1,
   cl='1c921e12904bc823ff8ad953985c6a7d91e41fc6549104015258eaca16347d6d',
   fx='80e357d7091496e802992b1a3b54bfd1f3a98174ec42db6c97ab0ce3edf0594f'),
}
h = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
ok = True
for ch, e in EXP.items():
    norm = B2/f'ocr/mineru-full/{ch}/{e[\"run\"]}'
    fin  = B2/f'ocr/final/{ch}'
    mdn, mdf = norm/f'{ch}_gray300.md', fin/f'{ch}_gray300.md'
    cln, clf = norm/f'{ch}_gray300_content_list.json', fin/f'{ch}_gray300_content_list.json'
    fx = B2/f'ocr/fixes/{ch}.json'
    t = mdn.read_text(encoding='utf-8')
    fxh = h(fx) if fx.exists() else None
    nfix = len(json.loads(fx.read_text(encoding='utf-8'))['fixes']) if fx.exists() else 0
    r = dict(md_identical=mdn.read_bytes()==mdf.read_bytes(), chars=len(t),
             lines=len(t.split(chr(10))), images=len(list((fin/'images').iterdir())),
             cl_norm=h(cln), cl_final=h(clf), fx=fxh, nfix=nfix)
    good = (r['md_identical'] and r['chars']==e['chars'] and r['lines']==e['lines']
            and r['images']==e['images'] and r['cl_norm']==e['cl'] and r['cl_final']==e['cl']
            and r['fx']==e['fx'] and r['nfix']==e['nfix'])
    ok = ok and good
    print(ch, 'OK' if good else 'MISMATCH', {k: v for k, v in r.items() if k not in ('cl_norm','cl_final','fx')})
print('ALL_OK' if ok else 'ABORT')
"
```

期待値: 9章とも `OK` で、最終行が `ALL_OK` であること。
**本スクリプトは9章すべてが未適用であることを前提とするため、9章の処理を開始する前に
一度だけ実行する。** 章ごとの確認は手順0-B を使う。

あわせて run の構成を確認する。

```bash
for ch in chap00 chap01 chap02 chap04 chap05 chap06 chap07 chap08 chap09; do
  echo "== $ch"; ls "/home/sakagawa/work/確率統計/ocr/mineru-full/$ch/"
done
```

- chap07 のみ `run-01` / `run-01-normalized` / `run-02` / `run-02-normalized` があり、
  他8章は `run-01` / `run-01-normalized` のみであること（§2.1）
- **件数はすべて Python の `str.count()` で数える。`grep -c` を使わない**

いずれかが期待と異なる場合は、その場で回避策を取らず**中断して報告する**。

また、更新前の md・`{FINAL_NN}` 全体・修正定義ファイルを `{SCRATCH}` に退避する。

```bash
B2=/home/sakagawa/work/確率統計
# 連想配列は declare -A で初期化する。事前に RUN[...]= の代入を行うと添字配列として
# 作られてしまい、declare -A が "cannot convert indexed to associative array" で失敗し、
# chap07 の run が run-01-normalized に解決される（誤り）。必ず本行を最初に実行すること。
declare -A RUN=( [chap00]=run-01-normalized [chap01]=run-01-normalized [chap02]=run-01-normalized \
                 [chap04]=run-01-normalized [chap05]=run-01-normalized [chap06]=run-01-normalized \
                 [chap07]=run-02-normalized [chap08]=run-01-normalized [chap09]=run-01-normalized )
# 初期化の検証（chap07 だけ run-02-normalized になること）
[ "${RUN[chap07]}" = run-02-normalized ] && [ "${RUN[chap00]}" = run-01-normalized ] \
  && echo RUN_MAP_OK || { echo "RUN_MAP_NG"; exit 1; }
for ch in chap00 chap01 chap02 chap04 chap05 chap06 chap07 chap08 chap09; do
  cp "$B2/ocr/mineru-full/$ch/${RUN[$ch]}/${ch}_gray300.md" "$SCRATCH/${ch}_gray300.md.before"
  cp -a "$B2/ocr/final/$ch" "$SCRATCH/final_${ch}.before"
  if [ -f "$B2/ocr/fixes/${ch}.json" ]; then cp "$B2/ocr/fixes/${ch}.json" "$SCRATCH/${ch}.json.before"; fi
done

# 退避の成功確認（md・final・修正定義ファイルの3点すべてを検査する）
for ch in chap00 chap01 chap02 chap04 chap05 chap06 chap07 chap08 chap09; do
  cmp "$B2/ocr/mineru-full/$ch/${RUN[$ch]}/${ch}_gray300.md" "$SCRATCH/${ch}_gray300.md.before" || { echo "BACKUP_NG_MD $ch"; continue; }
  diff -r "$B2/ocr/final/$ch" "$SCRATCH/final_${ch}.before" || { echo "BACKUP_NG_FINAL $ch"; continue; }
  if [ "$ch" = chap00 ]; then
    # chap00 のみ修正定義ファイルが存在しないため、退避も存在しないことを確認する
    if [ -f "$B2/ocr/fixes/chap00.json" ] || [ -f "$SCRATCH/chap00.json.before" ]; then
      echo "BACKUP_NG_FIXES chap00 (chap00.json は存在しないはず)"; continue
    fi
  else
    # chap00 以外は、退避が存在しバイト一致することを必須とする
    cmp "$B2/ocr/fixes/${ch}.json" "$SCRATCH/${ch}.json.before" || { echo "BACKUP_NG_FIXES $ch"; continue; }
  fi
  echo "BACKUP_OK $ch"
done
```

- **9章すべてで `BACKUP_OK {章名}` が出ること。** `BACKUP_NG_*` が1つでも出たら手順1 に進まない
- **chap00 だけは修正定義ファイルの退避が存在しない**（`chap00.json` を新規作成するため）。
  上のスクリプトは chap00 について「本体・退避ともに存在しないこと」を確認する。
  **この非対称性が、復元時に `chap00` 以外で削除を行ってはならない理由である**（§6「失敗時の復元」手順4）

**退避に失敗した場合は手順1 に進まず中断して報告する。**

### 手順0-B: 章ごとの直前確認（各章の手順1 の直前に行う）

手順0 のスクリプトの `EXP` から**当該章の1エントリだけ**を残したものを実行し、
`OK` であることを確認してから手順1 に進む。`MISMATCH` の場合はその章の手順1 に進まず
**中断して報告する**。**手順0 を9章分まとめて再実行してはならない**（処理済みの章が
`MISMATCH` になるため）。

### 手順1: 修正定義ファイルへの追記

§4.2〜§4.4 の内容で9ファイルを更新する。**§2.2 の順序で1章ずつ処理する**
（手順0-B → 手順1 → 手順2 → 手順3 を章ごとに完結させる）。

- `chap00.json` は**新規作成**する（`{"fixes": [ … ]}`）
- 他8ファイルは既存 JSON を読み込み、`fixes` 配列の末尾に `append` して書き戻す。
  追記前に §4.1 の SHA-256 と既存 ID を照合し、**異なっていた場合は上書きせず中断して報告する**
- **構造復元3件（`chap02-011`・`chap04-003`・`chap07-002`）の `old` は、md の当該行を
  直接読み取って組み立てる**（本書のコードブロックからのコピーでは、` ``` ` の入れ子や
  連続する半角空白を取り違える危険があるため）。手順の例:

  ```bash
  uv run python -c "
  from pathlib import Path
  NL = chr(10)
  p = Path('/home/sakagawa/work/確率統計/ocr/final/chap07/chap07_gray300.md')
  lines = p.read_text(encoding='utf-8').split(NL)
  # 開始行（'\`\`\`txt'）と終了行（'\`\`\`'）を特定して逐語的に取り出す
  i = lines.index('7.3 [0,1) って何ですか？') - 1
  assert lines[i] == chr(96)*3 + 'txt', lines[i]
  j = i + 1
  while lines[j] != chr(96)*3: j += 1
  old = NL.join(lines[i:j+1])
  new = NL.join(['## ? 7.3 [0,1) って何ですか？'] + lines[i+2:j])
  print(repr(old)); print(repr(new))
  "
  ```

  取り出した `old` / `new` が §4.4 の記載と一致することを目視で確認したうえで JSON に格納する。
  **一致しない場合は中断して報告する**
- 追記後に次を確認する:
  1. JSON として妥当であること
  2. `fixes` 配列の要素数が FR-001 基準1 の表のとおりであること
  3. 既存要素が1件も変わっていないこと（退避した `"$SCRATCH/{ch}.json.before"` の全要素と、
     追記後のファイルの先頭 N 件がオブジェクトとして等しい。chap00 は既存0件のため対象外）

### 手順2: 修正の適用（章ごと）

```bash
B2=/home/sakagawa/work/確率統計
ch=chap00; run=run-01-normalized   # 章ごとに §2.1 の run を指定する
uv run python scripts/apply_fixes.py \
  "$B2/ocr/mineru-full/$ch/$run/${ch}_gray300.md" \
  "$B2/ocr/fixes/${ch}.json" \
  -o "$B2/ocr/mineru-full/$ch/$run" --overwrite
```

- 期待: 終了コード 0、標準出力の `applied` / `skipped` が FR-003 基準1 の表と一致すること
- **`applied` / `skipped` が表と異なる場合は、終了コードが 0 でも次の手順に進まず、
  「失敗時の復元」に従って当該章を復元してから中断・報告する**

### 手順3: final の再構築（章ごと）

```bash
B2=/home/sakagawa/work/確率統計
ch=chap00; run=run-01-normalized
uv run python scripts/build_final.py \
  "$B2/ocr/mineru-full/$ch/$run" -o "$B2/ocr/final/$ch" --overwrite
```

- 期待: 終了コード 0（3種類の機械検証がすべて合格）

### 失敗時の復元（手順1〜手順3 に共通）

**本手順は、本案件が既にファイルを書き換えた後に失敗したときにのみ実行する。**

**書き込み前の不一致では復元してはならない。** 復元は退避時点の内容で上書きする操作であり、
本案件が書いていないファイルに対して行うと、**退避後に他の作業が加えた変更を消してしまう**。
書き込み前の不一致（下表「復元しない」の行）は、**何も戻さずそのまま中断して報告する**。

本案件が書き込むファイルは、章ごとに次の順序で増えていく。

| 段階 | この時点までに本案件が書き換えたファイル |
|---|---|
| 手順0-B の実行中 | **なし** |
| 手順1 の照合中（追記前）・構造復元の `old` の組み立て中 | **なし** |
| 手順1 の追記後 | 修正定義ファイル（`{FIXES_NN}`）のみ |
| 手順2 の後 | `{FIXES_NN}` ＋ `{NORM_NN}` の md |
| 手順3 の後 | `{FIXES_NN}` ＋ `{NORM_NN}` の md ＋ `{FINAL_NN}` |

したがって発動条件と復元対象は次のとおりである。

| 失敗した箇所 | 条件 | 復元対象 |
|---|---|---|
| 手順0-B | 当該章が `MISMATCH` | **復元しない**（中断して報告するのみ） |
| 手順1（追記**前**） | §4.1 の SHA-256 の不一致・既存 ID の不一致・`chap00.json` が既に存在する・構造復元の `old` が §4.4 と不一致 | **復元しない**（中断して報告するのみ） |
| 手順1（追記**後**） | JSON 不正・要素数の不一致・既存要素の変化 | **`{FIXES_NN}` のみ**（手順4） |
| 手順2 | `apply_fixes.py` の終了コードが 0 以外、または `applied` / `skipped` が §6 手順2 の表と異なる | **`{FIXES_NN}` と `{NORM_NN}` の md**（手順3・4） |
| 手順3 | `build_final.py` の終了コードが 0 以外 | **`{FIXES_NN}`・`{NORM_NN}` の md・`{FINAL_NN}` の3点**（手順2〜4） |

**復元対象を広げてはならない。** 「判断に迷うから3点とも戻す」ことは禁止する
（本案件が書いていないファイルを退避内容で上書きする危険があるため）。
どの段階で失敗したか判断できない場合は、**何も戻さずに中断して報告する**。

**手順3 で失敗した場合に復元が必須である理由**（手順0-B・手順1・手順2 の失敗では
`{FINAL_NN}` は未変更）: `build_final.py` は**ファイル単位では原子的**
（`copy_atomic` による一時ファイル＋`os.replace`）だが、**ディレクトリ全体としては原子的ではない**
（md → content_list.json → images/ の順に上書きし、孤児画像を削除したうえで最後に3検証を行う。
`scripts/build_final.py` の `main()` を 2026-09-02 に確認）。そのため
**`{FINAL_NN}` が新旧混在の部分更新状態で残りうる**。

対応（**失敗した章についてのみ、上表の「復元対象」に含まれる手順だけを実行する**）:

1. **その場で再実行やリトライをしない**
2. （手順3 で失敗した場合のみ）`{FINAL_NN}` を退避から復元する

   ```bash
   B2=/home/sakagawa/work/確率統計
   ch=chap00   # 失敗した章
   rm -rf "$B2/ocr/final/$ch"
   cp -a "$SCRATCH/final_${ch}.before" "$B2/ocr/final/$ch"
   diff -r "$SCRATCH/final_${ch}.before" "$B2/ocr/final/$ch" && echo RESTORED
   ```

3. （手順2 または手順3 で失敗した場合のみ）`{NORM_NN}` の md を退避から復元する（§2.1 の run を使う）

   ```bash
   cp "$SCRATCH/${ch}_gray300.md.before" \
      "$B2/ocr/mineru-full/$ch/${RUN[$ch]}/${ch}_gray300.md"
   ```

4. （手順1 の追記後・手順2・手順3 のいずれかで失敗した場合）修正定義ファイルを復元する。
   **chap00 は退避が存在しないため、作成した `chap00.json` を削除する**（元の状態＝ファイルなし に戻す）

   ```bash
   if [ -f "$SCRATCH/${ch}.json.before" ]; then
     cp "$SCRATCH/${ch}.json.before" "$B2/ocr/fixes/${ch}.json"
   elif [ "$ch" = chap00 ]; then
     rm -f "$B2/ocr/fixes/chap00.json"   # chap00 のみ。元の状態＝ファイルなし に戻す
   else
     # chap00 以外で退避が無いのは異常。既存の修正定義ファイルを削除してはならない
     echo "RESTORE_ABORT $ch: 退避 ${ch}.json.before が存在しない。削除せず中断する"
     exit 1
   fi
   ```

   **`rm` を実行してよいのは `chap00` だけである。** chap00 以外で退避が見つからない場合は、
   退避の取り漏らし（手順0 の欠陥）であって「元からファイルが無かった」ことを意味しない。
   **削除すれば先行案件が作成した既存の修正定義ファイルを失う。** その場合は何も消さずに
   `RESTORE_ABORT` を報告して中断する

5. 復元後、**手順0-B**（当該章のみ）を実行し `OK` になることを確認する。
   手順2 または手順3 で失敗した場合は、あわせて `{NORM_NN}` と `{FINAL_NN}` が
   **再びバイト同一**であることを確認する

   ```bash
   cmp "$B2/ocr/mineru-full/$ch/${RUN[$ch]}/${ch}_gray300.md" \
       "$B2/ocr/final/$ch/${ch}_gray300.md" && echo NORM_FINAL_IDENTICAL
   ```

6. 上表の復元対象をすべて戻したことを確認したうえで、**何が起きたか・どの章まで処理したか・
   どのファイルを復元したか（および復元しなかったものとその理由）を報告して中断する。
   後続の章には進まない**

**その段階の復元対象は漏れなく戻すこと。** たとえば手順2 で失敗したときに `{NORM_NN}` の md を
修正済みのまま残すと `{FINAL_NN}` とバイト同一でなくなり、手順0-B で必ず中断するため
次回の実行を再開できない。逆に、**復元対象に入っていないファイルには触れないこと**。

## 7. 確認手順（FR-002〜FR-005 の受け入れ基準）

### 手順1: 修正内容の確認

```bash
uv run python -c "
import re
from pathlib import Path
B2 = Path('/home/sakagawa/work/確率統計')
RUN = {'chap00':'run-01-normalized','chap01':'run-01-normalized','chap02':'run-01-normalized',
       'chap04':'run-01-normalized','chap05':'run-01-normalized','chap06':'run-01-normalized',
       'chap07':'run-02-normalized','chap08':'run-01-normalized','chap09':'run-01-normalized'}
EXP = {'chap00':(11842,437),'chap01':(24782,584),'chap02':(68836,1857),'chap04':(73919,1926),
       'chap05':(87053,1797),'chap06':(36399,833),'chap07':(22955,590),'chap08':(67202,1566),
       'chap09':(71014,2384)}
ok = True
for ch,(c,l) in EXP.items():
    for label, p in [('NORM', B2/f'ocr/mineru-full/{ch}/{RUN[ch]}/{ch}_gray300.md'),
                     ('FINAL', B2/f'ocr/final/{ch}/{ch}_gray300.md')]:
        t = p.read_text(encoding='utf-8')
        good = len(t)==c and len(t.split(chr(10)))==l
        ok = ok and good
        print(ch, label, 'OK' if good else 'MISMATCH', 'chars', len(t), 'lines', len(t.split(chr(10))))
# 全10章の Q&A 見出しの走査（FR-002 基準1〜3）
pat = re.compile(r'^(##\s+)?([？?][ 　]*)?([0-9A-C]+)\.([0-9]+)(?=[ 　])')
head = plain = 0
for f in sorted((B2/'ocr/final').glob('chap*/chap*_gray300.md')):
    for line in f.read_text(encoding='utf-8').split(chr(10)):
        m = pat.match(line)
        if m and m.group(2):
            if m.group(1): head += 1
            else:
                plain += 1
                print('  ★見出しでない:', f.parent.name, line[:60])
print('Q&A 見出し（##付き） =', head, '/ 見出しでない =', plain)
ok = ok and head == 74 and plain == 1   # plain の1件は chap09 の相互参照 ?3.8（下の注を参照）
# 構造復元の痕跡（FR-002 基準5）
c4 = (B2/'ocr/final/chap04/chap04_gray300.md').read_text(encoding='utf-8')
c7 = (B2/'ocr/final/chap07/chap07_gray300.md').read_text(encoding='utf-8')
fence = chr(96)*3 + 'txt'
c7l = c7.split(chr(10))
qa_in_fence = [c7l[i+1] for i, l in enumerate(c7l) if l.startswith(fence) and i+1 < len(c7l)
               and re.match(r'^[0-9A-C]+\.[0-9]+[ 　]', c7l[i+1])]
print('mineru-algorithm =', c4.count('mineru-algorithm'),
      '/ txt フェンス =', c7.count(fence), '（正当な4件が残るのが正しい）',
      '/ フェンス直後が Q&A 見出しの形 =', len(qa_in_fence), qa_in_fence)
ok = ok and c4.count('mineru-algorithm')==0 and c7.count(fence)==4 and len(qa_in_fence)==0
print('ALL_OK' if ok else 'ABORT')
"
```

期待値:

| 項目 | 期待値 | 対応する受け入れ基準 |
|---|---|---|
| 9章の NORM / FINAL の文字数・行数 | FR-003 基準3 の表のとおり（18行すべて `OK`） | FR-003 基準3・4 |
| **Q&A 見出し（`##` 付き）の総数** | **74**（適用前は 55） | FR-002 基準1・2 |
| **`?` 付きで `##` 無しの行** | **1**（適用前は 14）。その1件は `chap09` の `?3.8 $^{(p.101)}$ と同じ勘違いですね。…` であること | FR-002 基準1・3 |
| `mineru-algorithm` の出現回数（chap04） | **0**（適用前は 1） | FR-002 基準5 |
| ` ```txt ` フェンスの出現回数（chap07） | **4**（適用前は 5）。**0 ではない**——§4.4 の注を参照 | FR-002 基準5 |
| ` ```txt ` の直後の行が Q&A 見出しの形であるブロック（chap07） | **0** | FR-002 基準5 |
| 最終行 | `ALL_OK` | — |

**注（`plain` が 0 ではなく 1 になる理由）**: 適用前に「行頭 `?` だが `##` が無い」行は **14件**ある。
うち **13件が本案件の対象**（型β12 ＋ 構造復元の `? 4.6`。型γ の 2.7 は `?` が無いためこの走査に現れない）で、
**残る1件は `chap09` の `?3.8 $^{(p.101)}$ と同じ勘違いですね。…`＝本文中の相互参照**である
（feat-021 が母集団74件から除外済み）。走査の正規表現は番号の直後に空白を要求するが、この行は
`?3.8 ` と空白が続くためマッチする。したがって**適用後の `plain` は必ず 1 になる**
（2026-09-05 に適用をシミュレートして実測: `head = 74` / `plain = 1`）。
`plain` が 1 で、その1件が chap09 の `?3.8 $^{(p.101)}$` であれば**合格**である。
`plain` が 2 以上、または残った1件が別の行である場合は中断して報告する。

構造復元3件は、該当箇所を目視でも確認する。

```bash
B2=/home/sakagawa/work/確率統計
grep -n "^## ? 2.5 もし" $B2/ocr/final/chap02/chap02_gray300.md
grep -n -A2 "^## ? 4.6" $B2/ocr/final/chap04/chap04_gray300.md
grep -n -A9 "^## ? 7.3" $B2/ocr/final/chap07/chap07_gray300.md
```

### 手順2: 差分が該当箇所のみであることの確認

```bash
B2=/home/sakagawa/work/確率統計
for ch in chap00 chap01 chap02 chap04 chap05 chap06 chap07 chap08 chap09; do
  echo "===== $ch"
  diff "$SCRATCH/${ch}_gray300.md.before" "$B2/ocr/final/$ch/${ch}_gray300.md" | grep -c '^[0-9]'
done
```

期待されるハンク数は次のとおりである（FR-003 基準4。2026-09-05 に適用をシミュレートして実測）。
**「ハンク数 ＝ 新規 fix 件数」ではない**ことに注意する。

| 章 | 新規 fix | **期待ハンク数** | 実測したハンク見出し |
|---|---|---|---|
| chap00 | 1 | **1** | `67c67` |
| chap01 | 2 | **2** | `145c145` / `456c456` |
| chap02 | 6 | **6** | `454c454` / `572,574c572` / `734c732` / `1287c1285` / `1451c1449` / `1690c1688` |
| chap04 | 3 | **4** | `757,758c757,758` / `760d759` / `844c843` / `1733c1732` |
| chap05 | 2 | **2** | `1213c1213` / `1736c1736` |
| chap06 | 1 | **1** | `142c142` |
| chap07 | 2 | **3** | `140,141c140` / `151d149` / `172c170` |
| chap08 | 1 | **1** | `520c520` |
| chap09 | 1 | **1** | `940c940` |

**chap04 と chap07 で fix 件数より1つ多くなる理由**: 構造復元では、ブロックの先頭側
（開始タグ・フェンスと見出し行）の置換と、末尾側（`</div>` / 閉じフェンス）の削除が
**非連続なため別ハンクになる**（chap04 の `757,758c757,758` と `760d759`、
chap07 の `140,141c140` と `151d149`）。chap02 2.5 は対象が3行連続のため1ハンクに収まる。

差分の内容も目視で確認し、`##` / `? ` の挿入と構造復元3件のブロック置換以外が無いことを確かめる。
ハンク見出しの行番号は上表と一致するはずである（一致しない場合は中断して報告する）。

### 手順3: 非影響の確認（FR-004）

```bash
git status --short
```

期待される変更は次の3件のみである（`docs/CHANGELOG.md`・`docs/PROJECT_KNOWLEDGE.md` の更新と
`docs/BACKLOG.md` のステータス Closed 化は完了処理で行うため、この時点ではまだ変更されていない）。

| パス | 状態 | 理由 |
|---|---|---|
| `docs/issues/feat-020-qa-heading-not-recognized/` | `M` / `??` | 案件ドキュメント（README は起票時からの変更、requirements.md・design.md・reviews/ は新規） |
| `docs/BACKLOG.md` | `M` | 着手時にステータスを In Progress に更新済み |
| `tests/results/feat-020_test_result.txt` | `??` | 手順4 で新規作成する |

さらに次を確認する。

```bash
uv run python -c "
import hashlib
from pathlib import Path
B2 = Path('/home/sakagawa/work/確率統計')
EXP = {'chap00':('1e7ca0c6d1ebf6e557ec56d063344712f17c9bf7f04605c55ea253dd057121e7',2,'run-01-normalized'),
 'chap01':('bd53e369c349f2754e110642d8801577f5dd320c2b04d06303899ede243bc92a',27,'run-01-normalized'),
 'chap02':('a4ebb69a04863ac89c6b7ef1e2cf737377b20b168f50aa665ad523bf3aff260f',47,'run-01-normalized'),
 'chap04':('a5fd16baa99e391b6fbd8a0cdfed1d06218332eb1a14f54eae5f551eeca8b8df',98,'run-01-normalized'),
 'chap05':('ba0f8398748440fc3da1325928f836e7e0f652c64ca8931d5e463189df5dfd48',78,'run-01-normalized'),
 'chap06':('f41ce4ca1b838792ede2a985ac08466fb5fdcc6ccc1704d02355ce903bd99860',19,'run-01-normalized'),
 'chap07':('559b51624039af8209af3196c75a765df2befe6fbdc983fa9c25086f304b8d0e',16,'run-02-normalized'),
 'chap08':('7febf605cd86d279257d4d6c519bf626cf028d06c4147ac0703a391a61c83426',43,'run-01-normalized'),
 'chap09':('1c921e12904bc823ff8ad953985c6a7d91e41fc6549104015258eaca16347d6d',25,'run-01-normalized')}
h = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
ok = True
for ch,(sha,n,run) in EXP.items():
    cln = B2/f'ocr/mineru-full/{ch}/{run}/{ch}_gray300_content_list.json'
    clf = B2/f'ocr/final/{ch}/{ch}_gray300_content_list.json'
    imgs = len(list((B2/f'ocr/final/{ch}/images').iterdir()))
    good = h(cln)==sha and h(clf)==sha and imgs==n
    ok = ok and good
    print(ch, 'OK' if good else 'MISMATCH', 'images', imgs)
print('ALL_OK' if ok else 'ABORT')
"
```

- 各 `{FINAL_NN}/images/` のファイル数が変わっていないこと（FR-003 基準6）
- 各章の `content_list.json` が `{NORM_NN}` と `{FINAL_NN}` の**両方でバイト単位で変更されていない**
  こと（FR-003 基準7）。手順0 で記録した SHA-256 と照合する

最後に、**手順A のコマンドを再実行**する（FR-004 基準3・4・5）。

- 出力先を `"$SCRATCH/invariant_manifest_after.txt"` に変え、
  `files = 327` かつ `AGGREGATE = de46d2b04f2afa7fe299b1baccbfddfe76520d09062881e2a4de75aa65dedc8b` であること
- `diff "$SCRATCH/invariant_manifest_before.txt" "$SCRATCH/invariant_manifest_after.txt"` が**無出力**であること
- 一致しない場合は `diff` の出力から**どのファイルが変わったかを特定し、中断して報告する**

### 手順4: 自動テストの全件実行（FR-004 基準7）

```bash
uv run pytest -v > tests/results/feat-020_test_result.txt 2>&1
```

- コード変更がないため、feat-022 完了時点（**236 passed**）と同じくすべて成功することを確認する
- 出力を保存しながら実行し、保存後にファイル末尾で `failed` が 0 件であることを確認する

## 8. md と content_list.json の非対称性（既知事項）

`apply_fixes.py` は md のみを対象とし、`content_list.json` を変更しない（feat-010 の設計）。
そのため最終的な状態は次のようになる。

| ファイル | 当該箇所の状態 |
|---|---|
| `final/chapNN/chapNN_gray300.md` | 19件すべてが `## ? N.M …` の見出し（正しい） |
| `final/chapNN/chapNN_gray300_content_list.json` | 19件とも `text_level` が付かないまま（型β・γ・構造復元は本文/数式/コードのまま） |

これは feat-013 §6.1・feat-016 §8・feat-017 §8・feat-019 §8・feat-022 §8 で許容済みの
既存ポリシーであり、本案件では変更しない。LLM に読ませる主成果物は md であり、
`content_list.json` の主用途は `page_idx` による原本ページとの対応付けと図ブロックの座標参照である
（feat-005 ADR-7）。`build_final.py` の検証はコピー元と final のバイト同一性・画像参照の整合を
見るものであり、md と json の間の本文の一致は検査しないため、検証にも影響しない。

**本案件により、md と content_list の乖離は19件に拡大する**（feat-014 の3件・feat-022 の4件に加わる）。
この点は `docs/PROJECT_KNOWLEDGE.md` に追記する（§11）。

## 9. エラーハンドリングと境界条件

| 事象 | 挙動 | 対応 |
|---|---|---|
| `old` が md に存在しない（0件）かつ `new` が1件 | `apply_fixes.py` は `skipped` として扱い終了コード 0・内容不変 | 冪等性の担保。手順2 を2回実行しても安全 |
| `old` が2件以上 | `apply_fixes.py` がエラー終了（md は書かれない） | §6「失敗時の復元」の**手順2 の行**に従い `{FIXES_NN}` と `{NORM_NN}` の md を復元してから中断・報告する |
| `old` も `new` も0件 | 同上 | 同上 |
| 適用後に `new` が2件以上 | 最終不変条件違反でエラー終了（出力なし） | 同上（§5 の実測と矛盾する） |
| 既存 fix が最終不変条件に違反 | 同上 | 同上（先行案件の適用状態が変わっている） |
| `apply_fixes.py` の終了コードが 0 でも `applied`/`skipped` が FR-003 基準1 の表と異なる | md は書き換わっている | **次の手順に進まず**、§6「失敗時の復元」の**手順2 の行**に従い `{FIXES_NN}` と `{NORM_NN}` の md を復元してから中断・報告する |
| 修正定義ファイルが JSON として不正 | `apply_fixes.py` が読み込み時にエラー終了（md は書かれない） | §6「失敗時の復元」の**手順1（追記後）の行**に従い `{FIXES_NN}` のみ復元し、中断・報告する |
| 既存ファイルの SHA-256 が §4.1 の表と異なる | — | 上書きせず**中断して報告する**。**この時点では何も書き込んでいないため復元しない**（退避内容での上書きは、退避後に他の作業が加えた変更を消す） |
| **`chap00.json` が既に存在する** | — | §4.1 は「ファイルなし」を前提とする。**中断して報告する**（他案件が作成した可能性がある）。**復元しない**（書き込み前のため） |
| 構造復元の `old` が md から取り出した内容と §4.4 の記載で食い違う | — | **中断して報告する**（md の状態が本書の前提と異なる）。**復元しない**（`old` の組み立ては JSON 書き込みの前に行うため） |
| `build_final.py` の3検証のいずれかが不合格、またはコピー途中で失敗 | 終了コード 1。**`{FINAL_NN}` が部分更新状態で残りうる** | §6「失敗時の復元」の**手順3 の行**に従い3点を復元し、`{NORM_NN}` と `{FINAL_NN}` がバイト同一であること・手順0-B が `OK` になることを確認して中断・報告する。**後続の章には進まない** |
| ある章で失敗し、先行する章は成功済み | — | 失敗した章のみ復元する。成功済みの章は戻さない。どの章まで完了したかを明記して報告する |
| 手順0 が `ABORT`、または手順0-B が `ABORT` | — | 手順1 に進まず中断して報告する。**復元しない**（書き込み前のため） |
| 処理済みの章がある状態で手順0 を9章分まとめて再実行した | 処理済みの章が `MISMATCH` になり `ABORT` する | 手順0 は一度だけ実行する設計である。章ごとの確認には手順0-B を使う |
| **chap07 で `run-01-normalized` を指定してしまった** | `apply_fixes.py` は成功しうるが、`{FINAL_07}` のコピー元ではないため final に反映されない | §2.1 の表に従うこと。手順0 の `md_identical` の検査で事前に検出できる。退避スクリプトでは `declare -A RUN` の初期化を先頭で行い、`RUN_MAP_OK` の出力で検証する（§6 手順0） |
| 手順0 の退避で `BACKUP_NG_MD` / `BACKUP_NG_FINAL` / `BACKUP_NG_FIXES` のいずれかが出る | — | 手順1 に進まず中断して報告する（復元手段がない状態で書き換えないため）。**復元しない** |
| **復元時に `chap00` 以外で退避 `{ch}.json.before` が見つからない** | 退避の取り漏らし（手順0 の欠陥） | **既存の修正定義ファイルを削除してはならない。** 何も消さず `RESTORE_ABORT` を報告して中断する（§6「失敗時の復元」手順4） |
| 手順A のマニフェストが期待値と異なる | — | 中断して報告する |
| **退避スクリプトで `RUN_MAP_NG` が出る（`declare -A RUN` の初期化失敗）** | 連想配列でなく添字配列になり、chap07 の run が `run-01-normalized` に解決される | 退避に進まず中断して報告する。`declare -A RUN=(...)` より前に `RUN[...]=` の代入を書かないこと（§6 手順0） |
| §7 手順1 の `plain` が 1 で、その1件が chap09 の `?3.8 $^{(p.101)}$` | — | **想定どおり・合格**（本文中の相互参照。§7 手順1 の注）。`plain` が 0・2以上、または別の行が残った場合は中断して報告する |
| 出力先が入力と同一・入れ子、またはシンボリックリンク | `build_final.py` が書き込み前に拒否 | 本案件のパス指定では発生しない |

## 10. 実装の担当と進め方

CLAUDE.md「実装の実行方法（Sonnetサブエージェント）」に従い、**Agent ツールで model: sonnet を
指定したサブエージェントに委任する**。委任時に渡す情報は次のとおり。

1. 必読ドキュメントと順序: `CLAUDE.md` → `docs/PROJECT_KNOWLEDGE.md` → 本案件の `README.md`
   （**§0.5 を含む**）→ `requirements.md` → 本 `design.md` → `fixes/README.md`・`fixes/template.json`
   → `scripts/apply_fixes.py`・`scripts/build_final.py`
2. 厳密準拠（本書に書かれていない独自判断・改善・リファクタは禁止。**コードは1行も変更しない**）
3. 想定外事象（§9 の「中断して報告する」に該当する事象を含む）が起きたら回避策を実装せず
   直ちに中断し、何が起きたか・どこまで完了したかを報告して終了する
4. 検証まで実施（§6 の手順A・手順0・手順0-B・手順1〜3 と §7 の手順1〜4、
   `tests/results/feat-020_test_result.txt` への保存）。**手順0 の退避を9章すべてについて必ず
   先に行い、いずれかの手順が期待どおりに終わらなかった場合は §6「失敗時の復元」に従って
   当該章を復元してから報告する**
5. 禁止事項: git commit / push、`docs/BACKLOG.md` / `docs/CHANGELOG.md` / `CLAUDE.md` /
   `README.md`（ルート）/ `docs/PROJECT_KNOWLEDGE.md` の更新
6. 報告形式: 変更ファイル一覧、章ごとの `applied`/`skipped` と終了コード、§7 の確認結果、
   テスト結果サマリ、想定外事象の有無

## 11. ドキュメントの更新（完了処理で Claude Code 本体が実施する）

| ファイル | 更新内容 |
|---|---|
| `docs/BACKLOG.md` | feat-020 のステータスを Closed に更新する（着手時に In Progress へ更新済み） |
| `docs/CHANGELOG.md` | 完了内容を記録する |
| `docs/PROJECT_KNOWLEDGE.md` | 「データ」節の第2の書籍の項に、**Q&A 見出し74件がすべて md 上で見出しになったこと**と、**md と content_list の乖離が19件に拡大したこと**を追記する（1〜2行）。あわせてドメイン知識に、**MinerU が Q&A 見出しを数式ブロック・HTML `div`・コードブロックに取り込むことがあり、`apply_fixes.py` の複数行 `old`/`new` で解体できること**を追記する。**追記には案件 ID「（feat-020）」を付す**。ディレクトリ構成の変更はない |
| **`CLAUDE.md`** | **更新しない**（update-003 の非対称ルール） |
| `README.md`（ルート） | **更新不要**（コマンド・CLI オプション・入出力形式・既定値・実行環境のいずれも不変） |
| 案件 `README.md` | ステータスを Closed に更新する |

## 12. 後続案件への引き渡し

本案件の調査で発見した、**本案件のスコープ外の不一致**を記録する。起票はしない。

1. **chap07 7.3 の4番目の箇条書きの括弧の誤読**（新規発見。2026-09-05）:
   md は `- (a,b) → 「a < x ≤ b な x たち」` だが、**原本は `(a,b]`**（右が角括弧）。
   3番目の `[a,b)` と対になる記法であり、原本の切り出し画像で確認済み。
   `D1`（文字の不一致）に相当するため本案件では直さない
2. feat-021 の後続案件案 **C**（約物の全角/半角ゆれ10件）・**D**（アキの脱落2件）・
   **E**（参照アイコン `？`→`?` 2件）・**F**（インライン数式のマークアップ欠落18件）は未起票。
   本案件で扱った19件のうち、chap02 2.9（アキ）・chap07 7.4（全角括弧）・chap09 B.1（末尾疑問符）は
   これらの案件の対象として残っている
3. `content_list.json` 側の `text_level` は本案件で変更しない（§8）。
   content_list を基準に Q&A 見出しを走査する後続案件は、**md 側が修正済みであること**を
   前提に読む必要がある

## 13. 設計判断の記録（ADR）

### ADR-1: 「?」と番号の間の空白を是正しない

- **決定**: `?2.1` は `## ?2.1` に、`? 2.9` は `## ? 2.9` にする（現状の空白を維持する）
- **理由**: 原本の「？」は装飾アイコンであり、**アイコンと番号の間の隙間が空白文字かどうかを
  原本側から確定できない**（feat-021 ADR-10）。根拠のない変更を加えないため。
  feat-014 も同じ表記ゆれをスコープ外としており、判断が一貫する。2026-09-05 にユーザーが決定
- **代替案**: `## ? N.M` に統一する → 既存の正常な見出しにも `## ?N.M` が8件あり、
  そちらを放置すると新たな不整合になる。統一するなら74件全体を対象とする別案件が適切。不採用

### ADR-2: 併発する `D1` / `D4` を本案件で直さない

- **決定**: 対象19件のうち、同じ行に文字の不一致（chap02 2.9 のアキ・chap07 7.4 の全角括弧・
  chap09 B.1 の末尾疑問符）や数式の平文化がある件でも、**見出し体裁（`D2`）のみ**を直す
- **理由**: これらは feat-021 が後続案件案 C・D・F として型ごとに整理したものであり、
  型ごとに一括で扱うほうが調査・検証を一度で済ませられる。feat-022（`D1` のみを扱い `D2` を
  本案件に残した）と対称の切り分けであり、案件間の担当が明確になる。2026-09-05 にユーザーが決定
- **代替案**: 対象行だけ原本と完全一致させる → 案 C・D・F が「見出し以外の箇所だけ」になり、
  対象件数を数え直す必要が生じる。不採用

### ADR-3: 構造復元3件でも、質問文以外の文字は変更しない（chap02 2.5 を除く）

- **決定**: chap04 4.6 と chap07 7.3 は、ブロックの区切り（タグ・フェンス）を削除して
  見出し化するだけとし、**本文の文字は1文字も変更しない**。chap02 2.5 のみ、
  `$$` ブロック内の `\text {…}` 表現をインライン数式に書き換える
- **理由**: 2.5 は**数式ブロックの中に質問文全体が入っている**ため、ブロックを解体すると
  必然的に数式の記法を選び直すことになる（`$$` のままでは見出しにできない）。
  4.6・7.3 は本文がそのままテキストとして入っているため、区切りを外すだけで成立する。
  変更を不可避な範囲に限定することで、ADR-2 の方針（`D4` は案 F に残す）との衝突を最小化する
- **代替案**: 3件とも原本どおりに数式を書き直す → 4.6・7.3 で `D4` の修正を先取りすることになり、
  案 F の対象件数が変わる。不採用

### ADR-4: chap07 は `run-02-normalized` を適用先とする

- **決定**: chap07 のみ `{NORM_07}` = `run-02-normalized` とする
- **理由**: `{FINAL_07}` は `run-02-normalized` と md・content_list.json がバイト同一であり、
  `run-01-normalized` の md とは一致しない（2026-09-05 実測）。**コピー元でない run を更新しても
  final に反映されない**うえ、次回の final 再構築で変更が失われる
- **代替案**: 全章 `run-01-normalized` に決め打ちする → chap07 で修正が反映されない。不採用。
  なお手順0 の `md_identical` 検査により、取り違えは実行前に検出できる

### ADR-5: chap00 の修正定義ファイルを新規作成する

- **決定**: `{BASE2}/ocr/fixes/chap00.json` を `{"fixes": [ … ]}` の形で新規作成する
- **理由**: chap00 にはこれまで修正定義が無かったが、本案件で1件（型α の 0.2）を追加する。
  `apply_fixes.py` は md と修正定義ファイルの2引数を取るため、章ごとにファイルが必要である
- **代替案**: chap00 の1件を他章のファイルに含める → `apply_fixes.py` は1つの md にしか
  適用しないため、`old` が見つからずエラーになる。不採用

### ADR-6: 既存 fix を本書に転記せず、SHA-256 で照合する

- **決定**: §4.1 のとおり、既存 fix 計23件の内容を転記せず、追記前のファイルの SHA-256 と
  fix 一覧（件数・ID）を照合する
- **理由**: 既存 fix には複数行文字列と 64 桁の画像ハッシュを含むものがあり、
  転記は誤りを持ち込む risk があるうえ、一意性の担保に寄与しない。実装は
  「読み込んだ既存要素をそのまま再利用して書き出す」append 方式である（feat-022 ADR-5 と同じ判断）
- **代替案**: 既存 JSON を全文転記する → 9ファイル分で数百行になり、転記ミスの risk が高い。不採用

### ADR-7: MinerU と `normalize_punct.py` を再実行しない

- **決定**: `apply_fixes.py` と `build_final.py` のみを実行する
- **理由**: 見出しの認識漏れは MinerU の layout 解析に起因し、同一入力に対して同じ結果になるため
  再実行しても再発する。`normalize_punct.py` は置換表を変更しないため結果が変わらず、冪等でもある
- **代替案**: `ocr_dir.py` で9章を再実行する → MinerU の実行時間が無駄であり、run 番号が増えて
  履歴が追いにくくなる（feat-013 ADR-3・feat-022 ADR-6 と同じ判断）。不採用

### ADR-8: 知見の追記先を `docs/PROJECT_KNOWLEDGE.md` とし、`CLAUDE.md` を変更しない

- **決定**: §11 の追記は `docs/PROJECT_KNOWLEDGE.md` に案件 ID 付きで行う
- **理由**: update-003 で確定した非対称ルールに従う。本件で追記するのは
  **データの状態の変化**と**MinerU の挙動に関する知識**であり、統治文書に置く内容ではない
- **代替案**: `CLAUDE.md` のドメイン知識に追記する → update-003 で外出し済みのため参照先が存在しない。不採用
