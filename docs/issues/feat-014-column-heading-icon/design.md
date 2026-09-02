# feat-014 機能設計書: Q&A コラム見出しの「？」アイコン分離8件の修正

本書は `docs/DESIGN_STANDARD.md` に従う。用語は `requirements.md` §2 の定義をそのまま用いる。
**本書だけを読めば（会話の文脈なしで）反映作業ができること**を要件とする。

## 1. 対応要求マッピング

| 要求 ID | 内容 | 本書の該当セクション |
|---|---|---|
| FR-001 | 修正定義ファイル6件への修正追記 | §4・§5・§6 手順1 |
| FR-002 | アイコン画像行の削除（8件） | §4・§7 手順1 |
| FR-003 | A 型3件の見出しへの「? 」の補完 | §4・§7 手順1 |
| FR-004 | 既存成果物への修正の適用と final の再構築 | §6・§7 手順2 |
| FR-005 | 影響範囲の限定 | §3・§7 手順3・手順4 |

## 2. システム構成

### 2.1 使用するもの（すべて既存。新規実装はない）

| ファイル | 役割 | 本案件での変更 |
|---|---|---|
| `scripts/apply_fixes.py` | 修正定義ファイルの `old` → `new` を md に機械適用する（feat-010） | **なし** |
| `scripts/build_final.py` | `run-NN-normalized/` から `final/chapNN/` を構築し3種類の機械検証を行う（feat-012） | **なし** |
| `fixes/template.json` / `fixes/README.md` | 修正定義ファイルの書式定義（feat-010） | **なし** |

### 2.2 データの所在（すべてリポジトリ外）

- `{BASE2}` = `/home/sakagawa/work/確率統計`
- `{BASE}` = `/home/sakagawa/work/Pattern_Recognition_and_Machine_Learning`
- `{NORM_NN}` = `{BASE2}/ocr/mineru-full/chapNN/run-01-normalized`（NN = 01〜06）
- `{FINAL_NN}` = `{BASE2}/ocr/final/chapNN`（NN = 01〜06）
- 修正定義ファイル = `{BASE2}/ocr/fixes/chapNN.json`

6章とも `run-01-normalized` が唯一かつ最大の run である（2026-09-02 確認）。

### 2.3 技術スタック

`docs/TECH_STACK.md` の既存環境をそのまま用いる（Ubuntu 24 系 / Python 3.12.3 / uv）。
本案件で**ライブラリの追加・変更・削除はない**ため、`docs/TECH_STACK.md` は更新しない。
コマンドはすべて `uv run` 経由で実行する。

### 2.4 処理の流れ

```
{BASE2}/ocr/fixes/chapNN.json  ──┐
                                 ├─→ apply_fixes.py ─→ {NORM_NN}/chapNN_gray300.md（インプレース更新）
{NORM_NN}/chapNN_gray300.md ─────┘                             │
                                                               ↓
                                                    build_final.py ─→ {FINAL_NN}/
```

MinerU（`ocr_dir.py`）と `normalize_punct.py` は**実行しない**（ADR-4）。

## 3. 変更しないもの（FR-005）

| 対象 | 理由 |
|---|---|
| `scripts/` 配下のコード | 本案件は既存機能の適用のみで、コード変更を要しない |
| `tests/test_*.py` | 同上。ただし `tests/results/feat-014_test_result.txt` の新規作成は必須（CLAUDE.md「テスト」） |
| 確率統計 chap00・chap07・chap08・chap09 の成果物 | 対象8件が存在しない章 |
| `{BASE2}/ocr/fixes/chap07.json`・`chap08.json`・`chap09.json` | 同上 |
| PRML（`{BASE}`）の成果物 | 対象8件が存在しない（案件 README.md §7 で確認済み。長辺 80px 以下の画像が0枚） |
| 各 `{FINAL_NN}/images/` の全画像ファイル | `content_list.json` を無改変にするため、アイコン画像8個も削除しない（§8・ADR-3） |
| 各 `{NORM_NN}` / `{FINAL_NN}` の `content_list.json` | `apply_fixes.py` は md のみを対象とする既存ポリシー（§8） |
| `CLAUDE.md` | update-003 の非対称ルール（ADR-5） |
| `docs/TECH_STACK.md` | ライブラリの追加・変更・削除がない |

## 4. 修正定義ファイルへの追記内容（FR-001・FR-002・FR-003）

以下の8件を、各修正定義ファイルの `fixes` 配列の**末尾に追記**する（既存要素は変更しない）。

`old` / `new` 中の `\n` は **JSON のエスケープ**であり、実際の値は改行文字である
（`apply_fixes.py` は md 全文を1つの文字列として `str.count()` / `str.replace()` するため、
改行を含む複数行の `old` / `new` を指定できる。feat-015 で確立済み）。

**以下の `old` / `new` は 2026-09-02 に実データから機械的に抽出し、
一意性と最終不変条件をドライランで検証した確定値である（§5）。1文字も変えずに使うこと。**

### 4.1 chap01.json に追記（1件）

```json
{
  "id": "chap01-002",
  "reason": "p? の Q&A コラム見出し「? 1.2」（原本 page-03_2R.tif）で、原本の見出し先頭にある ？アイコン（影付きの装飾疑問符）が MinerU の layout 解析で見出しテキストから切り離され、独立した画像ブロックとして出力された（原本 TIF 目視確認済み）。見出しテキスト側に「?」が無い A 型のため、アイコン画像行を削除したうえで見出しに半角「? 」を補う。",
  "old": "![](images/6d4bdf52cb73a1ddea77e4d0a4e8cb852cfe6b679297fa3affdc7ecba78e86b3.jpg)\n\n## 1.2 そんなにたくさん会場を用意しなくても 18 会場で十分なのでは？",
  "new": "## ? 1.2 そんなにたくさん会場を用意しなくても 18 会場で十分なのでは？"
}
```

### 4.2 chap02.json に追記（2件・この順序で）

```json
{
  "id": "chap02-003",
  "reason": "p45 の Q&A コラム見出し「? 2.8」（原本 page-10_2R.tif）で、原本の見出し先頭にある ？アイコンが MinerU の layout 解析で切り離され、独立した画像ブロックとして出力された（原本 TIF 目視確認済み）。見出しテキスト側に「?」がある B 型のため、重複したアイコン画像行のみを削除する。アイコンは content_list 上でページ下部（bbox y=736-761）にあり、読み順ソートで md 上はページ先頭（「## 答」の直前）に置かれている。「## 答」は md 内に11回出現し一意にならないため、old / new に後続2行を含めて一意化した。",
  "old": "![](images/b7e3da6d29770ca5190f32677007fffd047b89ddc9364ea1f1d60ac0fc68c9ea.jpg)\n\n## 答\n\n1. Yes。P(リス目撃) = P(リス目撃, 雪が降る) + P(リス目撃, 雪がふらない) ですから。",
  "new": "## 答\n\n1. Yes。P(リス目撃) = P(リス目撃, 雪が降る) + P(リス目撃, 雪がふらない) ですから。"
}
```

```json
{
  "id": "chap02-004",
  "reason": "p45 の Q&A コラム見出し「? 2.6」（原本 page-10_2R.tif）で、原本の見出し先頭にある ？アイコンが MinerU の layout 解析で切り離され、独立した画像ブロックとして出力された（原本 TIF 目視確認済み）。見出しテキスト側に「?」が無い A 型のため、アイコン画像行を削除したうえで見出しに半角「? 」を補う。",
  "old": "![](images/58740cd09cd5eb4e04dc53590024b93ad80f5aff3fd534f432848109858a09bf.jpg)\n\n## 2.6 むずかしすぎてもうだめです……",
  "new": "## ? 2.6 むずかしすぎてもうだめです……"
}
```

### 4.3 chap03.json に追記（1件）

```json
{
  "id": "chap03-006",
  "reason": "p96 の Q&A コラム見出し「? 3.7」（原本 page-14_1L.tif）で、原本の見出し先頭にある ？アイコンが MinerU の layout 解析で切り離され、独立した画像ブロックとして出力された（原本 TIF 目視確認済み）。見出しテキスト側に「?」がある B 型のため、重複したアイコン画像行のみを削除する。アイコンは content_list 上でページ中程（bbox y=275-299）にあり、読み順ソートで md 上はページ先頭（「## 例題 3.8」の直前）に置かれている。",
  "old": "![](images/063ed77a474db1f9301633770cdf50ed4362382c06f885cfd312c1a2b6954885.jpg)\n\n## 例題 3.8",
  "new": "## 例題 3.8"
}
```

### 4.4 chap04.json に追記（1件）

```json
{
  "id": "chap04-002",
  "reason": "Q&A コラム見出し「? 4.4」（原本 page-10_1L.tif）で、原本の見出し先頭にある ？アイコンが MinerU の layout 解析で切り離され、独立した画像ブロックとして出力された（原本 TIF 目視確認済み）。見出しテキスト側に「?」がある B 型のため、重複したアイコン画像行のみを削除する。",
  "old": "![](images/edda6fb462eba763a851044c4356ac0d1f49943b6553401a25d30c52d82fd2b2.jpg)\n\n## ? 4.4 実数値の確率分布とは結局何のこと？",
  "new": "## ? 4.4 実数値の確率分布とは結局何のこと？"
}
```

### 4.5 chap05.json に追記（2件・この順序で）

```json
{
  "id": "chap05-002",
  "reason": "Q&A コラム見出し「? 5.1」（原本 page-08_1L.tif）で、原本の見出し先頭にある ？アイコンが MinerU の layout 解析で切り離され、独立した画像ブロックとして出力された（原本 TIF 目視確認済み）。見出しテキスト側に「?」がある B 型のため、重複したアイコン画像行のみを削除する。",
  "old": "![](images/a2daa7088706076dc0f8045ff539463ada0ce69032cd2579bee17849e4c42652.jpg)\n\n## ? 5.1 X は「ランダムにゆらぐベクトル」だと思えばいいですか？",
  "new": "## ? 5.1 X は「ランダムにゆらぐベクトル」だと思えばいいですか？"
}
```

```json
{
  "id": "chap05-003",
  "reason": "p186 の Q&A コラム見出し「? 5.2」（原本 page-08_2R.tif）で、原本の見出し先頭にある ？アイコンが MinerU の layout 解析で切り離され、独立した画像ブロックとして出力された（原本 TIF 目視確認済み）。見出しテキスト側に「?」が無い A 型のため、アイコン画像行を削除したうえで見出しに半角「? 」を補う。なお同章の本文（5.2 節）には「すぐ上の？5.1 で説明しました」という全角「？」を用いた参照があるが、これは原本どおりであり本修正の対象ではない。",
  "old": "![](images/fd2ca04a23957e8a0ba27a4f84417b4ca163850cbeca24ac3407953cca938374.jpg)\n\n## 5.2 なぜそんなふうにまとめて書けるのかわかりません。",
  "new": "## ? 5.2 なぜそんなふうにまとめて書けるのかわかりません。"
}
```

### 4.6 chap06.json に追記（1件）

```json
{
  "id": "chap06-006",
  "reason": "p243 の Q&A コラム見出し「? 6.4」（原本 page-10_2R.tif）で、原本の見出し先頭にある ？アイコンが MinerU の layout 解析で切り離され、独立した画像ブロックとして出力された（原本 TIF 目視確認済み）。見出しテキスト側に「?」がある B 型のため、重複したアイコン画像行のみを削除する。アイコンは content_list 上でページ下部（bbox y=617-643）にあり、読み順ソートで md 上はページ先頭（本文段落の直前）に置かれている。直後が見出しではなく本文段落のため、old / new はその段落の先頭から最初の句点までを用いる。",
  "old": "![](images/b0d8e683fc90987f8adddb280fe77a0842fab9289774d78792325fd9dab228a0.jpg)\n\n実はさらに、もっと根本的なところで Bayes 推定を受け入れない（もしくは Bayes 推定を推測統計とは全く異なる問題設定だと考える）統計学者も多くいます。",
  "new": "実はさらに、もっと根本的なところで Bayes 推定を受け入れない（もしくは Bayes 推定を推測統計とは全く異なる問題設定だと考える）統計学者も多くいます。"
}
```

### 4.7 `old` / `new` の設計規則

8件すべてに次の規則を適用した（ADR-2）。

1. **`old` の基本形**は「アイコン画像行 ＋ 空行 ＋ 直後の非空行」である。
   md 上ではアイコン画像行の前後が必ず空行になっているため、この形で
   「画像行1行 ＋ 空行1行」がまとめて削除される
2. **直後の非空行が見出し行（`## ` で始まる）のとき**は、その行**全体**を用いる（6件）
3. **直後の非空行が本文段落のとき**は、その行の**先頭から最初の句点「。」まで**を用いる
   （chap06-006 の1件）。行全体（437文字）は冗長であり、句点は文の切れ目として
   一意に決まるため、恣意的な打ち切りにならない
4. 上記で `new` が md 全体で一意にならない場合のみ、**一意になるまで後続の行を追加する**
   （chap02-003 の1件。`## 答` が11回出現するため後続2行を追加した）
5. **`new` の値は、A 型では「`## ` の直後に半角 `?` と半角空白1つを挿入した見出し行」、
   B 型では「`old` からアイコン画像行と空行を取り除いた残り」である**
6. `old` / `new` を**文の途中で打ち切らない**（行末または句点で終える）

## 5. 一意性の確認（FR-001 受け入れ基準 5・6）

### 5.1 新規8件（適用前の `count(old)`）

2026-09-02 に `{NORM_NN}/chapNN_gray300.md` に対して `str.count()` で実測した。

| fix ID | 型 | `count(old)` | `count(new)`（適用前） | `len(old)` | `len(new)` | 文字数の増減 |
|---|---|---|---|---|---|---|
| `chap01-002` | A | 1 | 0 | 121 | 41 | −80 |
| `chap02-003` | B | 1 | 1 | 142 | 60 | −82 |
| `chap02-004` | A | 1 | 0 | 104 | 24 | −80 |
| `chap03-006` | B | 1 | 1 | 91 | 9 | −82 |
| `chap04-002` | B | 1 | 1 | 108 | 26 | −82 |
| `chap05-002` | B | 1 | 1 | 119 | 37 | −82 |
| `chap05-003` | A | 1 | 0 | 113 | 33 | −80 |
| `chap06-006` | B | 1 | 1 | 162 | 80 | −82 |

- **A 型の `count(new)` が適用前に 0 なのは正しい**。`new` は「`? ` を補った見出し行」であり、
  適用によって初めて md に出現する。適用後は 1 になる
- **B 型の `count(new)` が適用前に 1 なのは正しい**。`new` は `old` の部分文字列
  （アイコン画像行と空行を除いた残り）であり、`old` の出現箇所にそのまま含まれている。
  適用後も 1 のままである
- 文字数の増減は A 型が −80（画像行80文字＋改行2文字を削除し、`? ` 2文字を追加）、
  B 型が −82（画像行80文字＋改行2文字を削除）である。
  アイコン画像行は `![](images/` (11) ＋ 64桁 hex ＋ `.jpg)` (5) = **80文字**で固定である

### 5.2 既存15件（追記後も最終不変条件を満たすこと）

`apply_fixes.py` は適用後に**当該ファイルの全 fix**について
`count(old) == 0` かつ `count(new) == 1` を検査する。
既存15件はすでに適用済みのため `count(old) == 0`・`count(new) == 1` の状態にあり、
新規8件の適用によってこれが崩れないことを確認する必要がある。

**2026-09-02 に `apply_fixes.apply_fixes()` を実データに対してドライラン
（結果を書き出さずに戻り値のみを検査）した結果、6ファイルすべてで `errors` が空であった。**
すなわち既存15件・新規8件の計23件すべてで最終不変条件が満たされる。

| ファイル | 既存 | 新規 | 合計 | `applied` | `skipped` | `errors` |
|---|---|---|---|---|---|---|
| `chap01.json` | 1 | 1 | 2 | 1 | 1 | なし |
| `chap02.json` | 2 | 2 | 4 | 2 | 2 | なし |
| `chap03.json` | 5 | 1 | 6 | 1 | 5 | なし |
| `chap04.json` | 1 | 1 | 2 | 1 | 1 | なし |
| `chap05.json` | 1 | 2 | 3 | 2 | 1 | なし |
| `chap06.json` | 5 | 1 | 6 | 1 | 5 | なし |

`skipped` が既存件数と一致するのは、既存 fix が `count(old) == 0` かつ `count(new) == 1`
（＝適用済み）と判定されるためである（`apply_fixes.py` の冪等性）。

### 5.3 干渉が起きないことの根拠

- 新規8件の `old` はいずれも**64桁の画像ハッシュ**を含む。ハッシュは md 内で一意であり、
  他の fix の `old` / `new` と文字列として重ならない
- 新規8件の `new` のうち、B 型5件は既存の md にそのまま存在する文字列であり、
  適用によって**新たな文字列は一切生まれない**（削除のみ）
- A 型3件の `new` は `## ? N.M …` の見出し行である。適用前の `count == 0` を実測済みであり、
  適用によって 1 件だけ生まれる
- 既存15件の `old` / `new` には画像参照行を含むものがなく、
  新規8件が削除する範囲（アイコン画像行と直後の空行）と重ならない。
  上記ドライランで実際に干渉がないことを確認済みである

### 5.4 適用による文字数・行数の変化（実測）

| 章 | 文字数（前 → 後） | 行数（前 → 後） | md 内の画像参照行数（前 → 後） |
|---|---|---|---|
| chap01 | 24856 → 24776 | 586 → 584 | 22 → 21 |
| chap02 | 69000 → 68838 | 1863 → 1859 | 23 → 21 |
| chap03 | 54007 → 53925 | 1462 → 1460 | 48 → 47 |
| chap04 | 74083 → 74001 | 1929 → 1927 | 92 → 91 |
| chap05 | 87209 → 87047 | 1801 → 1797 | 76 → 74 |
| chap06 | 36479 → 36397 | 835 → 833 | 17 → 16 |

行数は1件につき2行減る（アイコン画像行1行 ＋ 直後の空行1行）。

## 6. 適用手順（FR-004）

### 6.1 作業用ディレクトリ `{SCRATCH}` の定義

本書で `{SCRATCH}` と書いた箇所は、**Claude Code のセッション用スクラッチパッド**
（`/tmp/claude-1000/-home-sakagawa-git-honOCR/{session-id}/scratchpad/feat014/`）を指す。
成果物ディレクトリ（`{BASE2}` 配下）とリポジトリの**外**であり、実装の冒頭で作成する。

```bash
SCRATCH=/tmp/claude-1000/-home-sakagawa-git-honOCR/{session-id}/scratchpad/feat014
mkdir -p "$SCRATCH"
```

`{session-id}` は実装時のセッションのものを用いる（サブエージェントは自身に与えられた
スクラッチパッドのパスを使ってよい）。**本書のシェルコマンド中では `{SCRATCH}` ではなく
シェル変数 `"$SCRATCH"` の形で書いてある。`{SCRATCH}` は本文の説明でのみ用いる記法であり、
コマンドにそのまま貼り付けてはならない**（展開されず `{SCRATCH}` という名前のディレクトリが
作られてしまう）。**保存期間はセッション中のみ**であり、§7 の検証が完了すれば破棄してよい。
恒久的な記録は `tests/results/feat-014_test_result.txt` と案件ドキュメントに残す。

**MinerU（`ocr_dir.py`）と `normalize_punct.py` は実行しない**（ADR-4）。

### 6.2 章の処理順序と原子性の方針

対象6章を **chap01 → chap02 → chap03 → chap04 → chap05 → chap06 の順**に、
**1章ずつ「手順0 → 手順1 → 手順2 → 手順3」を完了させてから次の章に進む**。

- ある章で失敗した場合は §6.7 に従って**その章のみを復元**し、**直ちに中断して報告する**。
  未処理の章には手をつけない（既に完了した章はそのままでよい。
  各章の成果物は独立しており、章をまたぐ不整合は生じない）
- **6章を一括で処理してから検証する方式は採らない**。失敗時に復元すべき範囲が
  広がるうえ、どの章で問題が起きたかの切り分けが難しくなるためである（ADR-6）

### 6.3 手順A: 不変対象マニフェストの記録（最初に1回だけ）

FR-005 基準3・4・5・6 の対象のうち、**`git` 管理外のため `git status` では変更を検出できない
ファイル群**について、SHA-256 のマニフェストを2種類記録する。

- **M1（触らないファイル群）**: 計 **355ファイル**
  - `{BASE2}/ocr/fixes/chap07.json`・`chap08.json`・`chap09.json` … 3ファイル
  - 確率統計の chap00・chap07・chap08・chap09 の `final/chapNN/` 配下の全通常ファイル（再帰）
  - PRML（`{BASE}`）の `ocr/final/chap00〜07/` 配下の全通常ファイル（再帰）
- **M2（対象6章の `images/`）**: 計 **335ファイル**
  - `{FINAL_NN}/images/` 配下の全通常ファイル（NN = 01〜06）。
    内訳は chap01=27・chap02=47・chap03=66・chap04=98・chap05=78・chap06=19
  - `build_final.py` は `{NORM_NN}/images/` から `{FINAL_NN}/images/` へコピーし直すため、
    **内容が変わらないこと**を M2 で検証する（アイコン画像8個が削除されていないことの確認を含む）

**本手順は §6.1 の `mkdir -p "$SCRATCH"` を実行した後に行う。**

```bash
uv run python -c "
import hashlib
from pathlib import Path
B2 = Path('/home/sakagawa/work/確率統計/ocr')
B1 = Path('/home/sakagawa/work/Pattern_Recognition_and_Machine_Learning/ocr')

def emit(label, paths):
    lines = [f'{p}\t{hashlib.sha256(p.read_bytes()).hexdigest()}' for p in sorted(paths)]
    manifest = chr(10).join(lines) + chr(10)
    print(f'===== {label} =====')
    print(manifest, end='')
    print(f'{label} files =', len(lines))
    print(f'{label} AGGREGATE', hashlib.sha256(manifest.encode()).hexdigest())

m1 = [B2/'fixes'/f'chap{n}.json' for n in ['07','08','09']]
for n in ['00','07','08','09']:
    m1 += [p for p in (B2/'final'/f'chap{n}').rglob('*') if p.is_file()]
for d in sorted((B1/'final').iterdir()):
    if d.is_dir():
        m1 += [p for p in d.rglob('*') if p.is_file()]
emit('M1', m1)

m2 = []
for n in ['01','02','03','04','05','06']:
    m2 += [p for p in (B2/'final'/f'chap{n}'/'images').rglob('*') if p.is_file()]
emit('M2', m2)
" | tee "$SCRATCH/invariant_manifest_before.txt"
```

`print(manifest, end='')` により**個別のパスと SHA-256 の一覧も標準出力に出す**。
`tee` でファイルに保存されるため、不一致時に行単位で比較して変更ファイルを特定できる。

期待値（2026-09-02 実測）:

| 項目 | 期待値 |
|---|---|
| `M1 files` | 355 |
| `M1 AGGREGATE` | `5b72f48e3aa51ec4f2770824ed0e6ad577b85919dfa798f2d01a605830413dc2` |
| `M2 files` | 335 |
| `M2 AGGREGATE` | `58e0a0e6bfd683a82c850bc7920d4fd91d470b759000c13f37acc577f6cea2e5` |

**4値のいずれかが期待と異なる場合は、その場で回避策を取らず中断して報告する**
（対象外のデータが既に変更されている、またはファイル構成が変わっていることを意味する）。

### 6.4 手順0: 事前確認（各章の処理の直前に必ず行う）

以下は chapNN の `NN` を対象章に読み替えて実行する（章ごとに1回）。

```bash
uv run python -c "
import hashlib, sys
from pathlib import Path
NN = 'NN'   # ← 対象章の 2 桁（01〜06）に置き換える
B2 = Path('/home/sakagawa/work/確率統計/ocr')
norm = B2/'mineru-full'/f'chap{NN}'/'run-01-normalized'
fin  = B2/'final'/f'chap{NN}'
md_n, md_f = norm/f'chap{NN}_gray300.md', fin/f'chap{NN}_gray300.md'
cl_n, cl_f = norm/f'chap{NN}_gray300_content_list.json', fin/f'chap{NN}_gray300_content_list.json'
t = md_n.read_text(encoding='utf-8')
h = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
print('md bytes identical:', md_n.read_bytes() == md_f.read_bytes())
print('chars', len(t), 'lines', len(t.split(chr(10))))
print('img ref lines', len([l for l in t.split(chr(10)) if l.startswith('![](images/')]))
print('content_list sha256 NORM ', h(cl_n))
print('content_list sha256 FINAL', h(cl_f))
print('images', len([p for p in (fin/'images').iterdir() if p.is_file()]))
"
ls /home/sakagawa/work/確率統計/ocr/mineru-full/chapNN/
```

期待値（2026-09-02 実測。`content_list sha256` は NORM・FINAL とも同じ値）:

| 章 | `md bytes identical` | `chars` | `lines` | `img ref lines` | `images` | content_list SHA-256 |
|---|---|---|---|---|---|---|
| chap01 | `True` | 24856 | 586 | 22 | 27 | `bd53e369c349f2754e110642d8801577f5dd320c2b04d06303899ede243bc92a` |
| chap02 | `True` | 69000 | 1863 | 23 | 47 | `a4ebb69a04863ac89c6b7ef1e2cf737377b20b168f50aa665ad523bf3aff260f` |
| chap03 | `True` | 54007 | 1462 | 48 | 66 | `d269034e9b54fd993a3d4f9e092421a3b7974d3441519eb389678055e5103220` |
| chap04 | `True` | 74083 | 1929 | 92 | 98 | `a5fd16baa99e391b6fbd8a0cdfed1d06218332eb1a14f54eae5f551eeca8b8df` |
| chap05 | `True` | 87209 | 1801 | 76 | 78 | `ba0f8398748440fc3da1325928f836e7e0f652c64ca8931d5e463189df5dfd48` |
| chap06 | `True` | 36479 | 835 | 17 | 19 | `f41ce4ca1b838792ede2a985ac08466fb5fdcc6ccc1704d02355ce903bd99860` |

`img ref lines`（md 内の画像参照行数）と `images`（`{FINAL_NN}/images/` のファイル数）が
一致しないのは正常である。`content_list.json` には md に出力されない画像ブロック
（脚注・表画像など）が含まれ、`images/` はその全件を保持するためである。
`img ref lines` の値は §5.4 の表の「前」の値と一致する。

あわせて次を確認する。

- `ls` の出力に `run-01` と `run-01-normalized` 以外の **run ディレクトリが存在しない**こと
  （`run-01-normalized` が唯一かつ最大の run であること）。
  なお同ディレクトリには `ocr_dir.py` の実行ログ `run-01.log` も存在する。
  これはディレクトリではないため本チェックの対象外である
  （2026-09-02 の feat-014 実装時に全章で存在を確認。当初「2つだけであること」と
  記していたが実態と食い違っていたため是正した）
- `md bytes identical` が `True` であること（`{NORM_NN}` と `{FINAL_NN}` の md がバイト同一。
  差分があれば未反映の変更が存在する）
- content_list の SHA-256 が NORM と FINAL で互いに一致し、かつ上表の値であること。
  この値は §7 手順3 で `content_list.json` が変更されていないことの検証に使う（FR-004 基準7）
- **件数はすべて Python の `str.count()`（および行分割後の `startswith` 判定）で数える**。
  `grep -c` はマッチした「行数」を返すため `apply_fixes.py` の不変条件（`str.count()` ベース）と
  数え方が一致しない。**本書のすべての件数確認で `grep -c` を使ってはならない**

いずれかが期待と異なる場合は、その場で回避策を取らず**中断して報告する**。

さらに、更新前の md と `{FINAL_NN}` 全体を `{SCRATCH}` に退避する
（§7 手順2 の `diff` と、§6.7 の復元に使う）。

```bash
NN=NN   # ← 対象章の 2 桁（01〜06）に置き換える
cp "/home/sakagawa/work/確率統計/ocr/mineru-full/chap${NN}/run-01-normalized/chap${NN}_gray300.md" \
   "$SCRATCH/chap${NN}_gray300.md.before"
cp -a "/home/sakagawa/work/確率統計/ocr/final/chap${NN}" "$SCRATCH/final_chap${NN}.before"

# 退避の成功確認（いずれも一致すること）
sha256sum "/home/sakagawa/work/確率統計/ocr/mineru-full/chap${NN}/run-01-normalized/chap${NN}_gray300.md" \
          "$SCRATCH/chap${NN}_gray300.md.before"
diff -r "/home/sakagawa/work/確率統計/ocr/final/chap${NN}" "$SCRATCH/final_chap${NN}.before" && echo BACKUP_OK
```

- `md.before` の SHA-256 が原本と一致すること
- `diff -r` が無出力で `BACKUP_OK` が出ること（`{FINAL_NN}` 全体＝md・content_list.json・
  images/ が退避できたこと）

**退避に失敗した場合は手順1 に進まず中断して報告する**（失敗時の復元手段がない状態で
`{FINAL_NN}` を書き換えてはならない）。

### 6.5 手順1: 修正定義ファイルへの追記

§4 の内容で `/home/sakagawa/work/確率統計/ocr/fixes/chapNN.json` を更新する。

- 既存 JSON を読み込み、`fixes` 配列の末尾に §4 の該当 fix を **`append` して書き戻す**。
  既存要素の4キーを1文字も変更しないこと
- chap02 と chap05 は2件を追記する。**§4 に示した順序**（`chap02-003` → `chap02-004`、
  `chap05-002` → `chap05-003`）で追記する
- 既存ファイルの `fixes` 配列の要素数が §5.2 の「既存」欄と異なっていた場合は、
  上書きせず**中断して報告する**
- 追記後に JSON として妥当なこと（`json.load` が成功すること）と、`fixes` 配列の要素数が
  §5.2 の「合計」欄と一致することを確認する
- 書き出しは UTF-8・`ensure_ascii=False`・`indent=2`（既存ファイルと同じ整形）とする

### 6.6 手順2: 修正の適用

```bash
NN=NN   # ← 対象章の 2 桁（01〜06）に置き換える
uv run python scripts/apply_fixes.py \
  "/home/sakagawa/work/確率統計/ocr/mineru-full/chap${NN}/run-01-normalized/chap${NN}_gray300.md" \
  "/home/sakagawa/work/確率統計/ocr/fixes/chap${NN}.json" \
  -o "/home/sakagawa/work/確率統計/ocr/mineru-full/chap${NN}/run-01-normalized" --overwrite
```

- 出力先を入力と同じディレクトリにし、`--overwrite` でインプレース更新する
  （feat-013 ADR-4・feat-015・feat-017・feat-019 と同じ）
- 期待: 終了コード 0、標準出力に次の2行（`{A}` / `{S}` は §5.2 の `applied` / `skipped`）

  ```
  chapNN_gray300.md: {A} applied, {S} skipped
  total: {A} applied, {S} skipped
  ```

- 終了コードが 0 以外の場合、`apply_fixes.py` は**出力を書かない**ため
  `{NORM_NN}` は変更されていない。この場合は復元を行わず、
  標準エラーの内容とともに**中断して報告する**

#### 終了コードが 0 でも `applied` / `skipped` が §5.2 と異なる場合の復元

**終了コード 0 で `applied` / `skipped` が期待値と異なるときは、`{NORM_NN}` の md が
既に更新されている。** 一方 `{FINAL_NN}` は手順3 を実行していないため未更新であり、
両者はバイト同一でなくなる。この状態を放置すると、次回の手順0 の事前確認
「`md bytes identical` が `True` であること」で必ず中断するため**再開できない**。

そのため、`applied` / `skipped` の不一致も**手順3 の失敗と同じ復元対象**として扱う。

1. **その場で再実行やリトライをしない**
2. 手順0 で退避した md から `{NORM_NN}` を復元する

   ```bash
   cp "$SCRATCH/chap${NN}_gray300.md.before" \
      "/home/sakagawa/work/確率統計/ocr/mineru-full/chap${NN}/run-01-normalized/chap${NN}_gray300.md"
   ```

3. `{NORM_NN}` と `{FINAL_NN}` が**再びバイト同一**であることを確認する

   ```bash
   cmp "/home/sakagawa/work/確率統計/ocr/mineru-full/chap${NN}/run-01-normalized/chap${NN}_gray300.md" \
       "/home/sakagawa/work/確率統計/ocr/final/chap${NN}/chap${NN}_gray300.md" \
     && echo NORM_FINAL_IDENTICAL
   ```

   あわせて、文字数・行数・`img ref lines` が §6.4 の表の値（＝修正前の値）に
   戻っていることを確認する
4. **`{FINAL_NN}` は復元しない**（手順3 を実行していないため未更新のままであり、
   触る必要がない）。`{BASE2}/ocr/fixes/chapNN.json` も元に戻さない
   （追記内容は正しく、`apply_fixes.py` は冪等であるため再開時にそのまま使える）
5. `NORM_FINAL_IDENTICAL` を確認したうえで、**実際の `applied` / `skipped` の値・
   どの章まで完了したか・`{NORM_NN}` を修正前の状態に復元したことを報告して中断する**

### 6.7 手順3: final の再構築と失敗時の復元

```bash
NN=NN   # ← 対象章の 2 桁（01〜06）に置き換える
uv run python scripts/build_final.py \
  "/home/sakagawa/work/確率統計/ocr/mineru-full/chap${NN}/run-01-normalized" \
  -o "/home/sakagawa/work/確率統計/ocr/final/chap${NN}" --overwrite
```

- 期待: 終了コード 0（バイト同一・画像参照の解決・`img_path` 集合一致の3検証がすべて合格）と、
  標準出力の `chapNN_gray300: md=1 content_list=1 images={画像数}`
  （画像数は §6.4 の表の `images` 欄）

#### 失敗時の復元（`{FINAL_NN}` の部分更新への対処）

`build_final.py` は**ファイル単位では原子的**（一時ファイルに書いてから `os.replace` で
差し替える `copy_atomic`）だが、**ディレクトリ全体としては原子的ではない**
（md → content_list.json → images/ の順に上書きし、孤児画像を削除したうえで最後に3検証を行う。
`scripts/build_final.py` の `main()` を 2026-09-02 に確認）。

そのため、コピーの途中で失敗した場合や3検証が不合格（終了コード 1）だった場合、
**`{FINAL_NN}` が新旧混在の部分更新状態で残りうる**。この状態を放置してはならない。

手順3 が終了コード 0 以外で終わった場合の対応:

1. **その場で再実行やリトライをしない**
2. 手順0 で退避した `"$SCRATCH/final_chap${NN}.before"` から `{FINAL_NN}` を復元する

   ```bash
   rm -rf "/home/sakagawa/work/確率統計/ocr/final/chap${NN}"
   cp -a "$SCRATCH/final_chap${NN}.before" "/home/sakagawa/work/確率統計/ocr/final/chap${NN}"
   diff -r "$SCRATCH/final_chap${NN}.before" "/home/sakagawa/work/確率統計/ocr/final/chap${NN}" \
     && echo RESTORED
   ```

3. **`{NORM_NN}` 側の md も退避から復元する**（下記の理由により必須）

   ```bash
   cp "$SCRATCH/chap${NN}_gray300.md.before" \
      "/home/sakagawa/work/確率統計/ocr/mineru-full/chap${NN}/run-01-normalized/chap${NN}_gray300.md"
   ```

4. 復元後、`{NORM_NN}` と `{FINAL_NN}` が**再びバイト同一**であることを確認する
   （手順0 の事前確認が通る状態に戻ったことの検証）

   ```bash
   cmp "/home/sakagawa/work/確率統計/ocr/mineru-full/chap${NN}/run-01-normalized/chap${NN}_gray300.md" \
       "/home/sakagawa/work/確率統計/ocr/final/chap${NN}/chap${NN}_gray300.md" \
     && echo NORM_FINAL_IDENTICAL
   ```

   あわせて、文字数・行数・`img ref lines` が §6.4 の表の値（＝修正前の値）に
   戻っていることを確認する

5. **修正定義ファイル `chapNN.json` は元に戻さない**（追記した内容は正しく、
   `apply_fixes.py` は冪等であるため、再開時にそのまま使える）。
   ただし再開は手順0 からやり直す
6. `RESTORED` と `NORM_FINAL_IDENTICAL` を確認したうえで、**何が起きたか・
   どの章まで完了したか・当該章の `{NORM_NN}` と `{FINAL_NN}` の両方を修正前の状態に
   復元したことを報告して中断する**

**`{NORM_NN}` も必ず復元すること。** `apply_fixes.py` は冪等なので `{NORM_NN}` を修正済みのまま
残しても再適用自体は安全に見えるが、その状態では `{NORM_NN}`（修正済み）と
`{FINAL_NN}`（修正前）がバイト同一でなくなり、**手順0 の事前確認
「`md bytes identical` が `True` であること」で必ず中断する**ため、次回の実行を再開できない。
両方を修正前に戻すことで、手順0 から素直にやり直せる状態になる。

## 7. 確認手順（FR-002〜FR-005 の受け入れ基準）

6章すべての適用が完了した後に、以下を実施する。

### 7.1 手順1: 修正内容の確認（FR-002・FR-003）

`{NORM_NN}` と `{FINAL_NN}` の**両方**の md を検査する。
下記の内容をそのまま `"$SCRATCH/verify_feat014.py"` に保存して実行する
（`python -c` のワンライナーにはしない。引用符の入れ子で壊れやすいため）。
**このスクリプトは判定まで行い、1つでも不合格なら終了コード 1 で終わる。**

```python
import collections
import re
import sys
from pathlib import Path

B2 = Path('/home/sakagawa/work/確率統計/ocr')

# 8件のアイコン画像ハッシュ（章 -> ハッシュのリスト）
ICONS = {
    '01': ['6d4bdf52cb73a1ddea77e4d0a4e8cb852cfe6b679297fa3affdc7ecba78e86b3'],
    '02': ['b7e3da6d29770ca5190f32677007fffd047b89ddc9364ea1f1d60ac0fc68c9ea',
           '58740cd09cd5eb4e04dc53590024b93ad80f5aff3fd534f432848109858a09bf'],
    '03': ['063ed77a474db1f9301633770cdf50ed4362382c06f885cfd312c1a2b6954885'],
    '04': ['edda6fb462eba763a851044c4356ac0d1f49943b6553401a25d30c52d82fd2b2'],
    '05': ['a2daa7088706076dc0f8045ff539463ada0ce69032cd2579bee17849e4c42652',
           'fd2ca04a23957e8a0ba27a4f84417b4ca163850cbeca24ac3407953cca938374'],
    '06': ['b0d8e683fc90987f8adddb280fe77a0842fab9289774d78792325fd9dab228a0'],
}

# 適用後の期待値（章 -> (chars, lines, imgrefs)）
EXPECT = {
    '01': (24776, 584, 21),
    '02': (68838, 1859, 21),
    '03': (53925, 1460, 47),
    '04': (74001, 1927, 91),
    '05': (87047, 1797, 74),
    '06': (36397, 833, 16),
}

# A 型3件（章 -> [(補完後の見出し行, 補完前の見出し行)]）
A_HEADINGS = {
    '01': [('## ? 1.2 そんなにたくさん会場を用意しなくても 18 会場で十分なのでは？',
            '## 1.2 そんなにたくさん会場を用意しなくても 18 会場で十分なのでは？')],
    '02': [('## ? 2.6 むずかしすぎてもうだめです……',
            '## 2.6 むずかしすぎてもうだめです……')],
    '05': [('## ? 5.2 なぜそんなふうにまとめて書けるのかわかりません。',
            '## 5.2 なぜそんなふうにまとめて書けるのかわかりません。')],
}

QA_HEADING_RE = re.compile(r'^## (\?)([ 　]*)([0-9A-C]+\.[0-9]+)(?=[ 　])')
EXPECT_SEPARATORS = {' ': 47, '': 8}

errors: list[str] = []


def md_path(label: str, nn: str) -> Path:
    if label == 'NORM':
        return B2 / 'mineru-full' / f'chap{nn}' / 'run-01-normalized' / f'chap{nn}_gray300.md'
    return B2 / 'final' / f'chap{nn}' / f'chap{nn}_gray300.md'


for label in ('NORM', 'FINAL'):
    for nn in ('01', '02', '03', '04', '05', '06'):
        text = md_path(label, nn).read_text(encoding='utf-8')
        lines = text.split('\n')
        chars, n_lines = len(text), len(lines)
        imgrefs = len([l for l in lines if l.startswith('![](images/')])
        icon_refs = sum(text.count(h) for h in ICONS[nn])
        print(f'{label} chap{nn}: chars={chars} lines={n_lines} '
              f'imgrefs={imgrefs} icon_refs={icon_refs}')

        exp = EXPECT[nn]
        if (chars, n_lines, imgrefs) != exp:
            errors.append(f'{label} chap{nn}: (chars, lines, imgrefs) = '
                          f'{(chars, n_lines, imgrefs)}, expected {exp}')
        if icon_refs != 0:
            errors.append(f'{label} chap{nn}: icon_refs = {icon_refs}, expected 0')

        for new_h, old_h in A_HEADINGS.get(nn, []):
            n_new = sum(1 for l in lines if l == new_h)
            n_old = sum(1 for l in lines if l == old_h)
            print(f'    A-type: new x{n_new} / old x{n_old} | {new_h[:28]}')
            if n_new != 1:
                errors.append(f'{label} chap{nn}: 補完後の見出しが {n_new} 件（期待 1）: {new_h}')
            if n_old != 0:
                errors.append(f'{label} chap{nn}: 補完前の見出しが {n_old} 件残存（期待 0）: {old_h}')

# Q&A コラム見出しの表記別件数（final 全10章）
counter: collections.Counter = collections.Counter()
for d in sorted((B2 / 'final').iterdir()):
    if not d.is_dir():
        continue
    for line in (d / f'{d.name}_gray300.md').read_text(encoding='utf-8').split('\n'):
        m = QA_HEADING_RE.match(line)
        if m:
            counter[m.group(2)] += 1
print('Q&A headings by separator:', dict(counter), 'total', sum(counter.values()))
if dict(counter) != EXPECT_SEPARATORS:
    errors.append(f'Q&A 見出しの表記別件数が {dict(counter)}、期待 {EXPECT_SEPARATORS}')

if errors:
    print()
    print('*** FAILED ***')
    for e in errors:
        print(' -', e)
    sys.exit(1)
print()
print('ALL CHECKS PASSED')
```

```bash
uv run python "$SCRATCH/verify_feat014.py"
status=$?
echo "EXIT=$status"
[ "$status" -eq 0 ] || exit "$status"
```

**`echo` の直後で終わらせてはならない。** `echo` は常に 0 を返すため、
そのままではブロック全体の終了コードが 0 になり、検証の失敗が呼び出し側から見えなくなる。
終了コードを `status` に退避して表示し、**非 0 ならその値で `exit` する**こと。

**合格条件**: 標準出力の末尾が `ALL CHECKS PASSED` であり、`EXIT=0` であること。
`*** FAILED ***` が出た場合は、列挙された不一致の内容とともに**中断して報告する**。

スクリプトが検査する内容は次のとおりである。

| 検査 | 対象 | 期待値 |
|---|---|---|
| `chars` / `lines` / `imgrefs` | NORM・FINAL の6章 | §5.4 の「後」の値（スクリプト内 `EXPECT`） |
| `icon_refs`（8件の画像ハッシュの md 内出現数） | NORM・FINAL の6章 | すべて **0** |
| A 型の補完後の見出し行（完全一致） | NORM・FINAL の chap01・02・05 | 各 **1** 件 |
| A 型の補完前の見出し行（完全一致） | NORM・FINAL の chap01・02・05 | 各 **0** 件 |
| Q&A コラム見出しの表記別件数 | FINAL 全10章 | `{' ': 47, '': 8}`（合計 55） |

**適用前に実行すると必ず不合格になる**（2026-09-02 に実データで確認済み。
`icon_refs` が 1〜2、A 型の補完前見出しが残存、表記別件数が `{' ': 44, '': 8}` となり、
終了コード 1 で終わる）。これによりスクリプト自体が機能していることを確認できる。

### 7.2 手順2: 差分が該当箇所のみであることの確認（FR-004 基準4）

各章について、手順0 で退避した修正前の md と適用後の md を `diff` する。

```bash
NN=NN   # ← 対象章の 2 桁（01〜06）に置き換える（6章分繰り返す）
diff -u "$SCRATCH/chap${NN}_gray300.md.before" \
        "/home/sakagawa/work/確率統計/ocr/mineru-full/chap${NN}/run-01-normalized/chap${NN}_gray300.md" \
  | tee "$SCRATCH/diff_chap${NN}.txt"
grep -c '^@@' "$SCRATCH/diff_chap${NN}.txt"
```

**合格条件**: ハンク数（`^@@` の行数）が次表のとおりであり、
各ハンクの変更が「アイコン画像行と直後の空行の削除」（B 型）、
または「それに加えて見出し行への `? ` の挿入」（A 型）のみであること。

| 章 | ハンク数 |
|---|---|
| chap01 | 1 |
| chap02 | 2 |
| chap03 | 1 |
| chap04 | 1 |
| chap05 | 2 |
| chap06 | 1 |

（ここでの `grep -c` は **`diff` 出力のハンク見出し行を数える**用途であり、
書籍本文の件数計数ではないため §6.4 の「`grep -c` を使わない」の対象外である。）

### 7.3 手順3: 非影響の確認（FR-004 基準5・6・7、FR-005 基準3・4・5・6）

**(a) と (b) は、下記の内容をそのまま `"$SCRATCH/verify_feat014_invariants.py"` に保存して
実行する。**（`for` ループと `&& echo` の組み合わせでは、ループの終了コードが
最後の反復のものになるため、途中の章の不一致を呼び出し側から検出できない。
Python にまとめて不一致を収集し、終了コードで判定する。）

```python
import hashlib
import sys
from pathlib import Path

B2 = Path('/home/sakagawa/work/確率統計/ocr')

# content_list.json の SHA-256（適用前後で不変であるべき値）
EXPECT_CL = {
    '01': 'bd53e369c349f2754e110642d8801577f5dd320c2b04d06303899ede243bc92a',
    '02': 'a4ebb69a04863ac89c6b7ef1e2cf737377b20b168f50aa665ad523bf3aff260f',
    '03': 'd269034e9b54fd993a3d4f9e092421a3b7974d3441519eb389678055e5103220',
    '04': 'a5fd16baa99e391b6fbd8a0cdfed1d06218332eb1a14f54eae5f551eeca8b8df',
    '05': 'ba0f8398748440fc3da1325928f836e7e0f652c64ca8931d5e463189df5dfd48',
    '06': 'f41ce4ca1b838792ede2a985ac08466fb5fdcc6ccc1704d02355ce903bd99860',
}

# {FINAL_NN}/images/ のファイル数（適用前後で不変であるべき値）
EXPECT_IMAGES = {'01': 27, '02': 47, '03': 66, '04': 98, '05': 78, '06': 19}

errors: list[str] = []

for nn in ('01', '02', '03', '04', '05', '06'):
    norm = B2 / 'mineru-full' / f'chap{nn}' / 'run-01-normalized'
    fin = B2 / 'final' / f'chap{nn}'

    # (a) NORM と FINAL のバイト同一
    for name in (f'chap{nn}_gray300.md', f'chap{nn}_gray300_content_list.json'):
        same = (norm / name).read_bytes() == (fin / name).read_bytes()
        print(f'chap{nn} {name}: {"IDENTICAL" if same else "DIFFERENT"}')
        if not same:
            errors.append(f'chap{nn}: NORM と FINAL の {name} がバイト同一でない')

    # (b) content_list.json が変更されていないこと
    for label, path in (('NORM', norm), ('FINAL', fin)):
        got = hashlib.sha256((path / f'chap{nn}_gray300_content_list.json').read_bytes()).hexdigest()
        ok = got == EXPECT_CL[nn]
        print(f'chap{nn} {label} content_list sha256: {"OK" if ok else "MISMATCH " + got}')
        if not ok:
            errors.append(f'chap{nn} {label}: content_list.json が変更されている（{got}）')

    # images/ のファイル数
    n_images = len([p for p in (fin / 'images').iterdir() if p.is_file()])
    print(f'chap{nn} images: {n_images}')
    if n_images != EXPECT_IMAGES[nn]:
        errors.append(f'chap{nn}: images が {n_images} 件（期待 {EXPECT_IMAGES[nn]}）')

if errors:
    print()
    print('*** FAILED ***')
    for e in errors:
        print(' -', e)
    sys.exit(1)
print()
print('INVARIANT CHECKS PASSED')
```

```bash
uv run python "$SCRATCH/verify_feat014_invariants.py"
status=$?
echo "EXIT=$status"
[ "$status" -eq 0 ] || exit "$status"
```

**(c) 不変対象マニフェストの再計算と照合**: §6.3 のコマンドを、`tee` の出力先だけを
`"$SCRATCH/invariant_manifest_after.txt"` に変えて再実行する
（Python 部分は §6.3 と1文字も変えない）。そのうえで照合する。

```bash
diff "$SCRATCH/invariant_manifest_before.txt" "$SCRATCH/invariant_manifest_after.txt"
status=$?
if [ "$status" -eq 0 ]; then echo INVARIANTS_UNCHANGED; else exit "$status"; fi
```

**合格条件**:

- (a)(b) 標準出力の末尾が `INVARIANT CHECKS PASSED` であり、`EXIT=0` であること
  （6章とも md・content_list.json が NORM と FINAL でバイト同一、
  content_list.json の SHA-256 が §6.4 の値のまま、`images/` のファイル数も不変）
- (c) `diff` が無出力で `INVARIANTS_UNCHANGED` が出ること
  （M1 の 355ファイル・M2 の 335ファイルがいずれも変化していない。
  **M2 が一致することは、`{FINAL_NN}/images/` のアイコン画像8個が
  削除されていないことの確認でもある**）

あわせて、リポジトリ側に意図しない変更がないことを確認する。

```bash
git -C /home/sakagawa/git/honOCR status --short
```

**合格条件**: 案件ドキュメント（`docs/issues/feat-014-column-heading-icon/`）、
`docs/BACKLOG.md`、`docs/CHANGELOG.md`、`docs/PROJECT_KNOWLEDGE.md`、
`tests/results/feat-014_test_result.txt` 以外に変更が出ないこと。
とくに `scripts/` と `tests/test_*.py` に変更がないこと（FR-005 基準1・2）。
この確認は出力を目視して判定する（`git status --short` は変更の有無によらず 0 を返すため、
終了コードでは判定できない）。

### 7.4 手順4: 自動テストの全件実行（FR-005 基準8）

```bash
set -o pipefail
uv run pytest -v 2>&1 | tee tests/results/feat-014_test_result.txt
status=$?
echo "PYTEST_EXIT=$status"
[ "$status" -eq 0 ] || exit "$status"
```

**`set -o pipefail` は必須である。** これがないとパイプ全体の終了コードは
`tee` のもの（通常 0）になり、pytest が失敗しても成功に見えてしまう。
`set -o pipefail` を使えない実行環境では、代わりに次のようにして
pytest 自身の終了コードを検査する。

```bash
uv run pytest -v 2>&1 | tee tests/results/feat-014_test_result.txt
status=${PIPESTATUS[0]}
echo "PYTEST_EXIT=$status"
[ "$status" -eq 0 ] || exit "$status"
```

**どちらの形でも、`echo` の直後で終わらせてはならない。** `echo` は常に 0 を返すため、
そのままではブロック全体の終了コードが 0 になり、pytest の失敗が呼び出し側から見えなくなる。
終了コードを `status` に退避して表示し、**非 0 ならその値で `exit` する**こと。

**合格条件**: `PYTEST_EXIT=0` であり、かつ保存したファイルの末尾に `216 passed` が
記録されていること（feat-019 完了時点と同じ）。
本案件はコードを変更しないため、テスト結果は変わらないはずである。
`PYTEST_EXIT` が 0 以外、または `216 passed` でない場合は**中断して報告する**。

## 8. md と content_list.json の非対称性（既知事項）

`apply_fixes.py` は **md のみ**を対象とし、`content_list.json` を変更しない（feat-010 の既存ポリシー）。
そのため本案件の適用後、次の非対称が残る。

| 項目 | md | content_list.json | `images/` |
|---|---|---|---|
| アイコンの画像ブロック（8件） | 参照行が**削除される** | `type: "image"` のブロックが**残る** | 画像ファイルが**残る** |
| A 型3件の見出しの「?」 | **補われる** | `text` は「?」の無いまま**残る** | — |

これは feat-013 §6.1・feat-015・feat-016 §8・feat-017 design.md §8・feat-019 design.md §8 と
同じ構図であり、**許容済みの既知事項**である。理由は次のとおり。

- 主成果物は md である（`CLAUDE.md`「目標」の主目的は LaTeX 数式入り Markdown）。
  content_list.json は座標付き JSON として MinerU のスキーマを保つことに価値がある
- `content_list.json` を書き換える機能は存在せず、本案件で新設するのは
  「コード変更なし」の前提を崩す（ADR-3）

**`images/` のアイコン画像8個を削除してはならない。** `build_final.py` の検証3 は
`content_list.json` の `img_path` 集合と `{FINAL_NN}/images/` の実ファイル集合の
**完全一致**を要求する。`content_list.json` を無改変にする以上、画像実体を消すと
`images extra`／`images missing` で終了コード 1 になる（ADR-3）。

なお `build_final.py` の**孤児削除**は `{NORM_NN}/images/` のファイル名集合を基準とし、
md の参照を基準としない（`scripts/build_final.py` の `main()` を 2026-09-02 に確認）。
したがって md から画像参照行を削除しても孤児削除は作動せず、
`{FINAL_NN}/images/` のファイル数は変わらない。

また `build_final.py` の検証2 は「**md の画像参照が `images/` に存在すること**」
（`refs - actual_names` が空）を要求する片方向の包含であり、
md の参照が減ることは不合格にならない。

## 9. エラーハンドリングと境界条件

| 事象 | 検出方法 | 対応 |
|---|---|---|
| 手順A のマニフェストが期待値と異なる | `M1 files` / `M1 AGGREGATE` / `M2 files` / `M2 AGGREGATE` の照合 | **中断して報告**。対象外のデータが既に変更されている |
| 手順0 の実測値が期待値と異なる | §6.4 の表との照合 | **中断して報告**。前提が崩れている |
| 手順0 の退避に失敗（`BACKUP_OK` が出ない） | `sha256sum` / `diff -r` | **中断して報告**。手順1 に進まない |
| 修正定義ファイルの既存件数が §5.2 と異なる | `len(data["fixes"])` | **中断して報告**。上書きしない |
| `apply_fixes.py` が `old not found` / `old is not unique` を出す | 終了コード 1 と標準エラー | **中断して報告**。`apply_fixes.py` は出力を書かないため `{NORM_NN}` は無変更。復元は不要 |
| `apply_fixes.py` が最終不変条件違反を出す | 終了コード 1 と標準エラー | 同上。**中断して報告** |
| `apply_fixes.py` の `applied` / `skipped` が §5.2 と異なる（終了コードは 0） | 標準出力 | **§6.6 の「終了コードが 0 でも `applied` / `skipped` が §5.2 と異なる場合の復元」を実施**（`{NORM_NN}` は更新済みのため退避 md から戻し、`{FINAL_NN}` とのバイト同一を確認する）したうえで中断して報告 |
| `build_final.py` が終了コード 1 で終わる | 終了コード | **§6.7 の復元を実施**したうえで中断して報告 |
| §7 の合格条件をどれか1つでも満たさない | §7 の各表 | **中断して報告**。その場で追加修正をしない |
| `pytest` が1件でも失敗する | §7.4 | **中断して報告** |

**境界条件**:

- **対象0件の章**（chap00・chap07・chap08・chap09）: 本案件では `apply_fixes.py` も
  `build_final.py` も実行しない。§6.3 の M1 で無変更を検証する
- **2件を含む章**（chap02・chap05）: 2件は md 上で離れた位置にあり、
  一方の `old` が他方の `old` / `new` と重ならない（§5.3）。
  `apply_fixes.py` は記載順に逐次適用するため、§4 の順序で追記すれば結果は確定する
- **再実行（冪等性）**: すべての手順を再実行しても、`apply_fixes.py` は
  `count(old) == 0` かつ `count(new) == 1` を検出して `skipped` とし、
  終了コード 0・内容不変で終わる。`build_final.py` も同じ内容を再コピーするだけである

## 10. 実装の担当と進め方

CLAUDE.md「実装の実行方法（Sonnetサブエージェント）」に従い、
**Agent ツールで `model: sonnet` を指定したサブエージェントに委任する。**

サブエージェントへの指示に含めること:

1. **必読ドキュメントと順序**: `CLAUDE.md` → `docs/PROJECT_KNOWLEDGE.md` →
   本案件の `README.md` → `requirements.md` → 本書（`design.md`）→
   `scripts/apply_fixes.py` → `scripts/build_final.py` → `fixes/README.md`
2. **厳密準拠**: 本書に書かれていない独自判断・改善・リファクタは一切禁止。
   §4 の `old` / `new` は1文字も変えない
3. **想定外事象**: §9 のいずれかに該当したら、**その場で回避策を実装せず直ちに中断**し、
   何が起きたか・どの章まで完了したか・復元の実施有無を報告して終了する
4. **検証まで実施**: §7 の手順1〜4 をすべて実施し、
   `tests/results/feat-014_test_result.txt` を保存する
5. **禁止事項**: git commit / push を行わない。
   `docs/BACKLOG.md` / `docs/CHANGELOG.md` / `CLAUDE.md` / `README.md`（リポジトリルート）/
   `docs/PROJECT_KNOWLEDGE.md` の更新も行わない（完了処理で Claude Code 本体が行う）
6. **報告形式**: 変更ファイル一覧、§5.2 と §5.4 と §7 の各表に対する実測値、
   テスト結果サマリ、想定外事象の有無

## 11. ドキュメントの更新（完了処理で Claude Code 本体が実施する）

| ファイル | 更新内容 |
|---|---|
| `docs/BACKLOG.md` | feat-014 のステータスを Open → **Closed** に更新し、備考に完了日と結果を追記する |
| `docs/CHANGELOG.md` | `### 2026-09-02`（同日内なら既存見出しの配下、日をまたぐ場合は新規見出しを設ける）に feat-014 の完了内容を記録する |
| `docs/PROJECT_KNOWLEDGE.md` | 「ドメイン知識」に**1項目を追記**する（下記）。あわせて末尾「分割検討の記録」に追記後の実測行数（`wc -l` で確認）で1行追加する |
| `CLAUDE.md` | **更新しない**（ADR-5） |
| `README.md`（リポジトリルート） | **更新しない**（コマンド・CLI オプション・入出力形式・既定値・実行環境のいずれも変更がないため） |
| `docs/TECH_STACK.md` | **更新しない**（§2.3） |
| `tests/results/feat-014_test_result.txt` | 新規作成（§7.4） |

`docs/PROJECT_KNOWLEDGE.md` に追記する項目（既存の「MinerU は1つの見出しを2ブロックに
分断することがある」の項目の**直後**に置く）:

> - **MinerU は見出しの先頭にある装飾図案を、独立した画像ブロックとして切り出すことがある**
>   （実例: 確率統計の Q&A コラム見出し先頭の「？」アイコン。6章8件。feat-014）。
>   md 上には `![](images/{64桁hex}.jpg)` というアイコンだけの画像参照行が現れる。
>   このとき見出しテキスト側の扱いは2通りに割れ、**「?」が欠落する型（3件）と
>   「?」が入ったうえで画像にも重複する型（5件）**の両方が生じる。
>   ブロック分割の問題のため正規化の各種警告にも `build_final.py` の3種類の機械検証にも
>   現れず、手動テストで見つけるほかない。**検出には画像の実寸が使える**——アイコンは
>   長辺 40〜46px で、次に小さい図版（167px）との間に大きな開きがあるため、
>   `images/` を長辺で走査すれば機械的に洗い出せる。対処は `apply_fixes.py` の
>   修正定義ファイルで、アイコン画像行の削除（と欠落型では見出しへの「? 」の補完）を行う。
>   **`content_list.json` と `images/` の画像実体は消さない**——`build_final.py` の検証3が
>   両者の完全一致を要求するため、json を無改変にする以上、画像実体も残す必要がある（feat-014）

## 12. 設計判断の記録（ADR）

### ADR-1: A 型3件に補う表記を `## ? N.M`（半角 `?` ＋ 半角空白1つ）とする

- **採用**: 半角 `?` ＋ 半角空白1つ
- **却下**: 空白なし（`## ?N.M`）／全角「？」
- **理由**: 既存の正常な Q&A コラム見出し52件のうち **44件が半角空白1つ**、8件が空白なし、
  全角空白は0件である（2026-09-02 実測）。多数派に合わせるのが最も自然であり、
  原本でもアイコンと番号の間に空きがある。全角「？」は既存52件に1件もなく、
  導入すると新たな表記ゆれを生む。2026-09-02 にユーザーが決定した

### ADR-2: `old` を「アイコン画像行 ＋ 空行 ＋ 直後の非空行」で構成する

- **採用**: 直後の非空行をアンカーにする（見出し行なら行全体、本文段落なら先頭の1文）
- **却下1**: アイコン画像行のみを `old` にする（`new` を空にする）
  → `apply_fixes.py` は `new` が空文字列の定義を `validate_fixes` で拒否する
  （`fixes/template.json` にも「削除だけの修正は前後の残す文字列を含めて書く」と明記されている）
- **却下2**: **直前**の非空行をアンカーにする
  → A 型では見出し行への `? ` の補完が必要で、どのみち直後の見出し行を含める必要がある。
  アンカーの向きを A 型と B 型で変えると規則が2本になり、レビューと検証が煩雑になる
- **却下3**: 本文段落でも行全体を使う（chap06-006）
  → `old` が437文字になり、JSON が読みづらく、原本の1文字の違いにも過敏になる。
  句点は文の切れ目として一意に決まるため、恣意的な打ち切りにならない
- **補足**: feat-019 ADR-2 は「再 OCR 耐性のため `old` を最小限にする」方針を採ったが、
  本案件の `old` は**64桁の画像ハッシュを必ず含む**ため、再 OCR すればどのみち一致しない。
  したがって長さによる再 OCR 耐性の差は本案件では意味を持たず、
  **可読性と検証しやすさ**を優先した

### ADR-3: `content_list.json` と `images/` の画像実体を変更しない

- **採用**: md のみを修正する（既存ポリシーの踏襲）
- **却下**: `content_list.json` からアイコンの画像ブロック8件を削除し、
  `images/` からアイコン画像8個も削除する
- **理由**:
  1. `content_list.json` を書き換える機能は既存に存在せず、新設は「コード変更なし」の
     前提を崩す。本案件の目的（8件の訂正）に対して過大である
  2. `content_list.json` は MinerU のスキーマを保つことに価値がある（座標付き JSON として
     テキスト層埋め込みの副目的に使う。`CLAUDE.md`「目標」）
  3. `build_final.py` の検証3 は `img_path` 集合と `images/` の**完全一致**を要求するため、
     片方だけを消すと終了コード 1 になる。両方を消すには結局 json の書き換えが必要になる
  4. md と json の非対称は feat-013 以降の全案件で許容してきた既知事項である（§8）
- 2026-09-02 にユーザーが「無改変（既存ポリシー踏襲）」を選択した

### ADR-4: MinerU と `normalize_punct.py` を再実行しない

- **採用**: `apply_fixes.py` → `build_final.py` のみを実行する（再適用）
- **却下**: `ocr_dir.py` で章を再処理する
- **理由**: OCR 結果は同一入力に対して変わらず、10章で約35分の実行コストに見合わない。
  run 番号が増えて履歴も分かりにくくなる。本案件は字形正規化テーブルも句読点スタイルも
  変更しないため、再正規化しても結果は変わらない
  （feat-013 ADR-3・feat-015 ADR-4・feat-016 ADR-2・feat-017 ADR-4・feat-019 ADR-3 と同じ判断）
- **補足**: そもそも MinerU を再実行しても ？アイコンの分離は再発する
  （layout 解析の挙動であり、同一入力に対して同じ結果になる）

### ADR-5: 教訓の追記先を `docs/PROJECT_KNOWLEDGE.md` とし、`CLAUDE.md` を変更しない

- **採用**: `docs/PROJECT_KNOWLEDGE.md` の「ドメイン知識」に追記する（§11）
- **却下**: `CLAUDE.md` に追記する
- **理由**: update-003 で確定した非対称ルール——`docs/PROJECT_KNOWLEDGE.md` の**内容**は
  各案件の完了処理で更新し、**`CLAUDE.md` 本体の変更は update 案件でのみ行う**
  （`CLAUDE.md`「プロジェクト知識」）。feat-019 ADR-4 と同じ判断

### ADR-6: 6章を1章ずつ完了させ、一括処理しない

- **採用**: chap01 → chap06 の順に、章ごとに「手順0 → 1 → 2 → 3」を完了させる
- **却下**: 6章分の追記をまとめて行い、`apply_fixes.py` を6回連続で流してから
  `build_final.py` を6回流す
- **理由**:
  1. `build_final.py` はディレクトリ全体としては原子的でないため、失敗時に
     `{FINAL_NN}` が部分更新のまま残りうる（§6.7）。一括処理では復元すべき範囲が
     最大6章に広がる
  2. 章ごとに完了させれば、失敗しても「完了済みの章」と「未着手の章」に
     はっきり分かれ、どこから再開すればよいかが自明になる
  3. `ocr_dir.py --final` が**章単位**で final を構築する設計（feat-012。
     「後続の章が FAIL しても完成済みの final は残る」）と方針が一致する
