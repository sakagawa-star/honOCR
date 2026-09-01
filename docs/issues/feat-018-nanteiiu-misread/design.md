# feat-018 機能設計書: chap03 の誤読「なんていいう → なんていう」2件の修正

対象案件: `docs/issues/feat-018-nanteiiu-misread/`
要求仕様書: 同フォルダの `requirements.md`
調査記録: 同フォルダの `README.md`

## 1. 対応要求マッピング

| 要求 | 設計箇所 |
|---|---|
| FR-001 修正定義ファイルへの修正追記 | §4（追記内容）・§5（一意性の確認） |
| FR-002 「なんていいう」の誤読の訂正 | §4（`old` / `new` の設計）・§7 手順1 |
| FR-003 既存成果物への適用と final 再構築 | §6（適用手順）・§7（確認手順） |
| FR-004 影響範囲の限定 | §3（変更しないもの）・§6 手順A（不変対象マニフェストの記録）・§7 手順3 |

## 2. システム構成

本案件は**リポジトリ内のコードを変更しない**。既存スクリプトを引数を変えて実行するのみである。

```
{BASE2} = /home/sakagawa/work/確率統計
{NORM}  = {BASE2}/ocr/mineru-full/chap03/run-01-normalized
{FINAL} = {BASE2}/ocr/final/chap03
{FIXES} = {BASE2}/ocr/fixes/chap03.json   ← 本案件で追記（リポジトリ外・feat-017 で作成済み）

  {NORM}/chap03_gray300.md ──┐
                             ├─→ apply_fixes.py ──→ {NORM}/chap03_gray300.md（インプレース更新）
  {FIXES} ───────────────────┘

  {NORM}/（md + content_list.json + images/）
        └─→ build_final.py ──→ {FINAL}/（再構築・3種類の機械検証）
```

chap03 は `run-01` のみが存在する（2026-09-01 実測: `{BASE2}/ocr/mineru-full/chap03/` の内容は
`run-01` / `run-01-normalized` / `run-01.log` の3つ）。
実装時に `ls {BASE2}/ocr/mineru-full/chap03/` を実行し、`run-01-normalized` が存在すること、
およびそれが最大の run 番号であることを確認する。異なっていた場合は中断して報告する。

## 3. 変更しないもの（FR-004）

| 対象 | 理由 |
|---|---|
| `scripts/` 配下のすべてのファイル | 本案件はデータ側の修正のみで実現できる |
| `tests/test_*.py`（テストコード） | コード変更がないため、テストの追加・変更も生じない。ただし `tests/results/feat-018_test_result.txt` は検証記録として**新規作成する**（CLAUDE.md「テスト」のルール。§7 手順4） |
| `{NORM}/chap03_gray300_content_list.json` | `apply_fixes.py` は md のみを対象とする（feat-010 の設計）。§8 の非対称性 |
| `{NORM}/images/`・`{FINAL}/images/` | 画像は本案件の対象外。`build_final.py` がコピーするのみ（66 ファイル） |
| `{BASE2}/ocr/fixes/chap03.json` の既存 fix `chap03-001`〜`chap03-003` | feat-017 で作成・適用済み。本案件では追記のみを行う |
| `{BASE2}/ocr/fixes/` の他8ファイル（chap01・02・04・05・06・07・08・09） | 本案件の対象外 |
| 確率統計の chap03 以外の9章の成果物 | 「なんていいう」の出現は chap03 のみ（案件 README.md §6） |
| PRML（`{BASE}`）の成果物 | 「なん〜いう」系の出現は 0 件（案件 README.md §6） |
| `{BASE2}/ocr/mineru-full/chap03/run-01/`（MinerU 生出力） | 読み取りも変更もしない |

## 4. 修正定義ファイルへの追記内容（FR-001・FR-002）

`{BASE2}/ocr/fixes/chap03.json` の `fixes` 配列の**末尾**に、次の2件を追記する
（既存の `chap03-001`〜`chap03-003` は1文字も変更しない）。追記後のファイル全体は次のとおりになる。

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
    },
    {
      "id": "chap03-004",
      "reason": "3.5.4 節の本文（原本 page-19_1L.tif）で、原本の「なんていうことはありません」が「なんていいうことはありません」と誤読されていた（「い」が1文字余分。原本 TIF 目視確認済み）。同じ行にある chap03-005 と区別するため、係助詞「は」を含む「ことはありません」まで含めて一意にしている",
      "old": "なんていいうことはありません",
      "new": "なんていうことはありません"
    },
    {
      "id": "chap03-005",
      "reason": "3.5.4 節の本文（原本 page-19_1L.tif）で、原本の「なんていうこともありません」が「なんていいうこともありません」と誤読されていた（「い」が1文字余分。原本 TIF 目視確認済み）。同じ行にある chap03-004 と区別するため、係助詞「も」を含む「こともありません」まで含めて一意にしている",
      "old": "なんていいうこともありません",
      "new": "なんていうこともありません"
    }
  ]
}
```

**注意**: 上の `chap03-001`〜`chap03-003` は 2026-09-01 時点の既存ファイルの内容を
**そのまま転記した**ものである。実装時はこれらを1文字も変更してはならない
（`id` / `reason` / `old` / `new` の4キーすべてを既存の値のまま残す）。実装は
「既存 JSON を読み込み、`fixes` 配列の末尾に2件を `append` して書き戻す」方法で行い、
既存要素を書き換えないこと。

### 4.1 `old` / `new` の設計

- 誤読は2件とも「なんていいう」→「なんていう」の**1文字（「い」）の削除**である
- `old` を「なんていいう」だけにすると、同一行に2件あるため一意にならず、また `new`
  （「なんていう」）が適用後に複数件になって最終不変条件に違反する
  （chap03 には feat-017 で修正した「なんていう」が既に3件ある）。
  そのため**両方に文脈を付けて一意化する**
- 2件は「ことは**は**ありません」/「こと**も**ありません」の係助詞で区別できる。
  `old` の末尾を「ことはありません」「こともありません」まで伸ばせば一意になる（§5）
- 文脈は一意性が確保できる最小限にとどめる。文脈を長くするほど再 OCR 時に文面が変わって
  `old` が一致しなくなる可能性が上がる（feat-015 ADR-3・feat-016 ADR-3・feat-017 §4.5 と同じ判断）
- 数式（`3.5n`・`n/2`）や脚注記号（`$^{*15}$`）を `old` に含めない。再 OCR で記法が
  1文字でも変われば `old` が一致しなくなるため

## 5. 一意性の確認（FR-001 受け入れ基準 4・5）

`apply_fixes.py` は、適用後に**全 fix について `count(old) == 0` かつ `count(new) == 1`** を
検査し、1つでも破れていればエラー終了して出力を書かない（最終不変条件。feat-010 FR-003 規則6）。
そのため `old` の一意性だけでなく、**適用後に `new` がちょうど1件になることも事前に数える**
（CLAUDE.md の運用ルール。feat-013 でこれを怠って実装が1度中断した）。

2026-09-01 に `{FINAL}/chap03_gray300.md`（= `{NORM}` の md とバイト同一）で実測した。
**新規2件を逐次適用したうえで**最終不変条件を検査している。

### 5.1 新規2件

| fix | 文字列 | 適用前 | 適用後（実測） |
|---|---|---|---|
| `chap03-004` | `old` = `なんていいうことはありません` | **1** | 0 |
| `chap03-004` | `new` = `なんていうことはありません` | **0** | **1** |
| `chap03-005` | `old` = `なんていいうこともありません` | **1** | 0 |
| `chap03-005` | `new` = `なんていうこともありません` | **0** | **1** |

### 5.2 既存3件（追記後も最終不変条件を満たすこと）

| fix | 文字列 | 適用前 | 適用後（実測） |
|---|---|---|---|
| `chap03-001` | `old` = `等しいなんという勘違い` | 0 | 0 |
| `chap03-001` | `new` = `等しいなんていう勘違い` | 1 | **1** |
| `chap03-002` | `old` = `3.5n に近づいていく、なんということはない` | 0 | 0 |
| `chap03-002` | `new` = `3.5n に近づいていく、なんていうことはない` | 1 | **1** |
| `chap03-003` | `old` = `n/2 に近づいていく、なんということはない` | 0 | 0 |
| `chap03-003` | `new` = `n/2 に近づいていく、なんていうことはない` | 1 | **1** |

既存3件は feat-017 で適用済みのため `count(old) == 0` / `count(new) == 1` であり、
`apply_fixes.py` の規則2により **skipped** として扱われ、最終不変条件も満たす。

### 5.3 干渉が起きないことの根拠

- 新規2件の `old`（`なんていいう…`）は、既存3件の `new` に含まれない
  （既存の `new` はいずれも「なんて**いう**」であり「なんてい**い**う」ではない）。
  したがって既存の適用結果を壊さない
- 新規2件の `new`（`なんていうことはありません` / `なんていうこともありません`）は、
  既存3件の `new`（`…勘違い` / `…ことはない`）と文字列として重ならない。
  したがって既存の `count(new)` を 2 にしてしまうことはない
- 新規2件どうしも、`ことは` / `ことも` で区別され、どちらも他方の部分文字列ではない。
  したがって適用順に依存しない
- 上記はすべて §5.1・§5.2 の実測（5件すべてが適用後 `count(old) == 0` かつ
  `count(new) == 1`）で確認済みである

### 5.4 適用による文字数・行数の変化（実測）

| 項目 | 適用前 | 適用後 |
|---|---|---|
| 文字数 | 54009 | **54007**（「い」2文字の削除） |
| 行数 | 1462 | **1462**（変化なし） |
| `なんていいう` | 2 | **0** |
| `なんていう` | 3 | **5** |

## 6. 適用手順（FR-003）

**MinerU（`ocr_dir.py`）と `normalize_punct.py` は実行しない。**
`{NORM}` は feat-013 の再適用（2026-08-28）で字形正規化済み、feat-017 の再適用（2026-08-31）で
「なんという」の修正済みの状態にあり、本案件は置換表を変更しないため、
再正規化しても結果は変わらない。

### 手順A: 不変対象マニフェストの記録（最初に1回だけ）

FR-004 基準3・4・5 の対象のうち、**`git` 管理外のため `git status` では変更を検出できない
ファイル群**について、SHA-256 のマニフェストを記録する。対象は次の**639ファイル**である。
**`images/` を含む配下のすべての通常ファイルを再帰的に対象とする**（`.md` / `.json` だけでは
図画像の変更を検出できないため）。

- `{BASE2}/ocr/fixes/` の他8ファイル（`chap01`・`chap02`・`chap04`・`chap05`・`chap06`・
  `chap07`・`chap08`・`chap09` の各 `.json`）… 8ファイル
- 確率統計の chap03 以外の9章（chap00・01・02・04・05・06・07・08・09）の
  `final/chapNN/` 配下の全通常ファイル（再帰）
- PRML（`{BASE}` = `/home/sakagawa/work/Pattern_Recognition_and_Machine_Learning`）の
  `ocr/final/chap00〜07/` 配下の全通常ファイル（再帰）

```bash
uv run python -c "
import hashlib
from pathlib import Path
B2 = Path('/home/sakagawa/work/確率統計/ocr')
B1 = Path('/home/sakagawa/work/Pattern_Recognition_and_Machine_Learning/ocr')
paths = [B2/'fixes'/f'chap{n}.json' for n in ['01','02','04','05','06','07','08','09']]
for n in ['00','01','02','04','05','06','07','08','09']:
    paths += [p for p in (B2/'final'/f'chap{n}').rglob('*') if p.is_file()]
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

期待値（2026-09-01 実測）:

- `files = 639`
- `AGGREGATE = e62ceb4034e91a1c5bd97f876d7d1e8f999fe6810844fc0e5f19cb46405d3821`

**この2値が期待と異なる場合は、その場で回避策を取らず中断して報告する**
（対象外のデータが既に変更されている、またはファイル構成が変わっていることを意味する）。
出力はスクラッチパッド等（成果物ディレクトリの外）に保存し、§7 手順3 で再実行して照合する。

### 手順0: 事前確認（実行前に必ず行う）

```bash
ls /home/sakagawa/work/確率統計/ocr/mineru-full/chap03/

uv run python -c "
import hashlib
from pathlib import Path
norm = Path('/home/sakagawa/work/確率統計/ocr/mineru-full/chap03/run-01-normalized')
fin  = Path('/home/sakagawa/work/確率統計/ocr/final/chap03')
md_n, md_f = norm/'chap03_gray300.md', fin/'chap03_gray300.md'
cl_n, cl_f = norm/'chap03_gray300_content_list.json', fin/'chap03_gray300_content_list.json'
t = md_n.read_text(encoding='utf-8')
print('md bytes identical:', md_n.read_bytes() == md_f.read_bytes())
print('chars', len(t), 'lines', len(t.split(chr(10))))
print('なんていいう', t.count('なんていいう'), 'なんていう', t.count('なんていう'))
print('old1', t.count('なんていいうことはありません'), 'old2', t.count('なんていいうこともありません'))
print('new1', t.count('なんていうことはありません'), 'new2', t.count('なんていうこともありません'))
h = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
print('content_list sha256 NORM ', h(cl_n))
print('content_list sha256 FINAL', h(cl_f))
print('images', len(list((fin/'images').iterdir())))
"
```

期待値（2026-09-01 実測）:

| 項目 | 期待値 |
|---|---|
| `md bytes identical` | `True` |
| `chars` | 54009 |
| `lines` | 1462 |
| `なんていいう` | 2 |
| `なんていう` | 3 |
| `old1` / `old2` | 1 / 1 |
| `new1` / `new2` | 0 / 0 |
| `images` | 66 |
| content_list SHA-256（NORM・FINAL とも） | `d269034e9b54fd993a3d4f9e092421a3b7974d3441519eb389678055e5103220` |

あわせて次を確認する。

- `run-01-normalized` が存在し、それが最大の run 番号であること
- `md bytes identical` が `True` であること（`{NORM}` と `{FINAL}` の md がバイト同一。
  差分があれば未反映の変更が存在する）
- content_list の SHA-256 が NORM と FINAL で互いに一致し、かつ上表の値であること。
  この値は §7 手順3 で `content_list.json` が変更されていないことを検証するために使う
  （FR-003 基準8）
- **件数はすべて Python の `str.count()` による出現回数で数える**。`grep -c` は
  マッチした「行数」を返すため、`apply_fixes.py` の不変条件（`str.count()` ベース）と
  数え方が一致しない。本書のすべての件数確認で `grep -c` を使ってはならない

いずれかが期待と異なる場合は、その場で回避策を取らず**中断して報告する**。

また、更新前の md を作業用にコピーしておく（成果物ディレクトリの**外**、
スクラッチパッド等に置く。§7 手順2 の `diff` で使う）。

### 手順1: 修正定義ファイルへの追記

§4 の内容で `/home/sakagawa/work/確率統計/ocr/fixes/chap03.json` を更新する。

- 既存 JSON を読み込み、`fixes` 配列の末尾に `chap03-004`・`chap03-005` の2件を `append` して
  書き戻す。既存の `chap03-001`〜`chap03-003` の4キーを1文字も変更しないこと
- 既存ファイルが §4 に示した `chap03-001`〜`chap03-003` の内容と異なっていた場合は、
  上書きせず**中断して報告する**
- 追記後に `uv run python -c "import json; json.load(open(...))"` で JSON として妥当なことと、
  `fixes` 配列の要素数が **5** であることを確認する

### 手順2: 修正の適用

```bash
uv run python scripts/apply_fixes.py \
  /home/sakagawa/work/確率統計/ocr/mineru-full/chap03/run-01-normalized/chap03_gray300.md \
  /home/sakagawa/work/確率統計/ocr/fixes/chap03.json \
  -o /home/sakagawa/work/確率統計/ocr/mineru-full/chap03/run-01-normalized --overwrite
```

- 出力先を入力と同じディレクトリにし、`--overwrite` でインプレース更新する
  （feat-013 ADR-4・feat-015・feat-017 と同じ）
- 期待: 終了コード 0、標準出力に次の2行

  ```
  chap03_gray300.md: 2 applied, 3 skipped
  total: 2 applied, 3 skipped
  ```

### 手順3: final の再構築

```bash
uv run python scripts/build_final.py \
  /home/sakagawa/work/確率統計/ocr/mineru-full/chap03/run-01-normalized \
  -o /home/sakagawa/work/確率統計/ocr/final/chap03 --overwrite
```

- 期待: 終了コード 0（バイト同一・画像参照・`img_path` 集合一致の3検証がすべて合格）

## 7. 確認手順（FR-002〜FR-004 の受け入れ基準）

### 手順1: 修正内容の確認

手順0 と同じ数え方（`str.count()` による出現回数）で、`{NORM}` と `{FINAL}` の
両方の md を確認する。

```bash
uv run python -c "
for label, path in [
    ('NORM',  '/home/sakagawa/work/確率統計/ocr/mineru-full/chap03/run-01-normalized/chap03_gray300.md'),
    ('FINAL', '/home/sakagawa/work/確率統計/ocr/final/chap03/chap03_gray300.md'),
]:
    t = open(path, encoding='utf-8').read()
    print(label, 'なんていいう', t.count('なんていいう'), 'なんていう', t.count('なんていう'),
          'chars', len(t), 'lines', len(t.split(chr(10))))
    print(label, 'A', t.count('3.5n に近づいていくなんていうことはありませんし'),
                 'B', t.count('n/2 に近づいていくなんていうこともありません'))
"
```

期待値（`{NORM}` / `{FINAL}` とも同じ）:

| 項目 | 期待値 | 対応する受け入れ基準 |
|---|---|---|
| `なんていいう` の出現回数 | 0 | FR-002 基準1 |
| `なんていう` の出現回数 | 5 | FR-002 基準2 |
| `A`（3.5n の文） | 1 | FR-002 基準4 |
| `B`（n/2 の文） | 1 | FR-002 基準4 |
| 文字数 | 54007（適用前 54009 − 2） | FR-003 基準3 |
| 行数 | 1462（適用前と同一） | FR-003 基準4 |

あわせて修正後の行を目視確認する（期待: 1256 行目に1件）。

```bash
grep -n "なんていうことはありませんし" \
  /home/sakagawa/work/確率統計/ocr/final/chap03/chap03_gray300.md
```

さらに、両書籍の final 全章に対するバリアント調査を再実行する（FR-002 基準5）。

```bash
uv run python -c "
import re
from collections import Counter
from pathlib import Path
pat = re.compile(r'なん.{0,5}?[いゆ]う')
for label, base in [('確率統計','/home/sakagawa/work/確率統計/ocr/final'),
                    ('PRML','/home/sakagawa/work/Pattern_Recognition_and_Machine_Learning/ocr/final')]:
    c = Counter()
    for f in sorted(Path(base).glob('chap*/*.md')):
        for m in pat.findall(f.read_text(encoding='utf-8')):
            c[m] += 1
    print(label, dict(c))
"
```

期待される出力:

```
確率統計 {'なんていう': 12, 'なんとなくそういう': 1}
PRML {}
```

（`なんていいう` が消え、`なんていう` が 10 → 12 になる。）

### 手順2: 差分が該当箇所のみであることの確認

手順0 で退避した適用前の md と、適用後の md の `diff` を取る。

```bash
diff /tmp/.../chap03_gray300.md.before \
     /home/sakagawa/work/確率統計/ocr/final/chap03/chap03_gray300.md
```

期待される差分は**ハンク1つのみ**で、1256 行の削除と追加の1組である
（変更内容は同一行の「い」2文字の削除）。他の行に差分があってはならない（FR-003 基準5）。

### 手順3: 非影響の確認（FR-004）

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
| `docs/issues/feat-018-nanteiiu-misread/` | `??`（未追跡） | 案件ドキュメント。起票時（ステップ1〜3）に作成済み |
| `docs/BACKLOG.md` | `M` | 起票時に feat-018 の行（ステータス `Open`）を追加済み |
| `tests/results/feat-018_test_result.txt` | `??`（未追跡） | 手順4 で新規作成する |

**feat-017 の案件フォルダとテスト結果ファイルが未コミットのまま残っている場合は、
それらも `git status` に現れる。** その場合は本案件の変更と混同しないよう、
上記3件が含まれていることを確認したうえで、feat-017 由来の項目を除いて判定する。

完了処理（ステップ8）の後は、上記に加えて `docs/CHANGELOG.md` が `M` になり、
`docs/BACKLOG.md` のステータスが `Closed` に変わる。これは想定どおりの変更であり、
本手順の検証対象ではない。

さらに次を確認する。

- `{FINAL}/images/` のファイル数が **66** のままであること
- `{NORM}` と `{FINAL}` の `chap03_gray300_content_list.json` が**バイト単位で変更されていない**
  こと（FR-003 基準8）。`git` 管理外のため、手順0 で記録した SHA-256
  （`d269034e9b54fd993a3d4f9e092421a3b7974d3441519eb389678055e5103220`）と照合して検証する。
  mtime とサイズの比較では、同サイズの変更や mtime の復元を検出できないため用いない

最後に、**§6 手順A のコマンドを再実行**し、`git` 管理外の不変対象が変更されていないことを
検証する（FR-004 基準3・4・5）。

- 出力先を `invariant_manifest_after.txt` に変えて実行し、
  `files = 639` かつ `AGGREGATE = e62ceb4034e91a1c5bd97f876d7d1e8f999fe6810844fc0e5f19cb46405d3821`
  であること（手順A で記録した値と同一）
- あわせて `diff /tmp/.../invariant_manifest_before.txt /tmp/.../invariant_manifest_after.txt` が
  **無出力**であること
- 一致しない場合は、上記 `diff` の出力から**どのファイルが変わったかを特定し、中断して報告する**

この検証により、`git status` では検出できない次の3種類の非影響が確認できる。

| 対象 | 対応する受け入れ基準 |
|---|---|
| 確率統計の chap03 以外の9章の成果物 | FR-004 基準3 |
| 既存の修正定義ファイル8件（chap01・02・04・05・06・07・08・09） | FR-004 基準4 |
| PRML（`{BASE}`）の成果物 | FR-004 基準5 |

### 手順4: 自動テストの全件実行（FR-004 基準6）

```bash
uv run pytest -v > tests/results/feat-018_test_result.txt 2>&1
```

- コード変更がないため、feat-017 完了時点（**216 passed**）と同じくすべて成功することを確認する
- 上記コマンドは出力を `tests/results/feat-018_test_result.txt` に**保存しながら**実行する
  （CLAUDE.md「テスト」のルール: テストコマンドの出力をそのまま保存する）。
  保存後、ファイルの末尾で全件成功（`failed` が 0 件）であることを確認する

## 8. md と content_list.json の非対称性（既知事項）

`apply_fixes.py` は md のみを対象とし、`content_list.json` を変更しない（feat-010 の設計）。
そのため最終的な状態は次のようになる。

| ファイル | 当該箇所の状態 | 理由 |
|---|---|---|
| `final/chap03/chap03_gray300.md` | 「なんていう」（正しい） | `apply_fixes.py` の適用対象 |
| `final/chap03/chap03_gray300_content_list.json` | 「なんていいう」2件（誤りのまま） | `apply_fixes.py` の対象外 |

これは feat-013 §6.1・feat-015 design.md §8・feat-016 §8・feat-017 design.md §8 で
許容済みの既存ポリシーであり、本案件では変更しない。LLM に読ませる主成果物は md であり、
`content_list.json` の主用途は `page_idx` による原本ページとの対応付けと図ブロックの
座標参照である（feat-005 ADR-7）ため、実用上の影響はない。
また `build_final.py` の検証はコピー元と final のバイト同一性・画像参照の整合を見るもので
あり、md と json の間の本文の一致は検査しないため、検証にも影響しない。

**この非対称性は、本案件の原因調査で「feat-017 の修正が原因ではない」ことを立証する
根拠にもなった**（案件 README.md §3）。`content_list.json` が `apply_fixes.py` によって
変更されないことにより、同じ誤読が json 側に残っていることが「適用前から存在した」ことの
証拠になる。

## 9. エラーハンドリングと境界条件

| 事象 | 挙動 | 対応 |
|---|---|---|
| `old` が md に存在しない（0件）かつ `new` が1件 | `apply_fixes.py` は `skipped` として扱い終了コード 0・内容不変 | 冪等性の担保。手順2 を2回実行しても安全 |
| `old` が2件以上 | `apply_fixes.py` がエラー終了（出力なし） | 中断して報告する（想定外。文面が変わっている） |
| `old` も `new` も0件 | `apply_fixes.py` がエラー終了（出力なし） | 中断して報告する |
| 適用後に `new` が2件以上 | 最終不変条件違反でエラー終了（出力なし） | 中断して報告する（§5 の実測と矛盾する） |
| 既存の `chap03-001`〜`003` が最終不変条件に違反 | 同上 | 中断して報告する（feat-017 の適用状態が変わっている） |
| `chap03.json` が JSON として不正 | `apply_fixes.py` が読み込み時にエラー終了 | 追記内容を見直す（手順1 の JSON 妥当性確認で事前に検出する） |
| 既存ファイルの `chap03-001`〜`003` が §4 と異なる | — | 上書きせず**中断して報告する**（手順1） |
| `build_final.py` の3検証のいずれかが不合格 | 終了コード 1 | 中断して報告する |
| 手順A のマニフェストが期待値と異なる | — | 中断して報告する |
| 出力先が入力と同一・入れ子、またはシンボリックリンク | `build_final.py` が書き込み前に拒否 | 本案件のパス指定では発生しない（`{NORM}` と `{FINAL}` は別ツリー） |

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
   `tests/results/feat-018_test_result.txt` への保存）
5. 禁止事項: git commit / push、`docs/BACKLOG.md` / `docs/CHANGELOG.md` / `CLAUDE.md` /
   `README.md` の更新（完了処理で Claude Code 本体が行う）
6. 報告形式: 変更ファイル一覧、テスト結果サマリ、§7 の確認結果、想定外事象の有無

## 11. ドキュメントの更新（完了処理で Claude Code 本体が実施する）

| ファイル | 更新内容 |
|---|---|
| `docs/BACKLOG.md` | feat-018 のステータスを Closed に更新する（行は起票時に追加済み） |
| `docs/CHANGELOG.md` | 完了内容を記録する |
| `CLAUDE.md` | ドメイン知識の「語彙単位の誤り」の項に、**同じ語の表記ゆれ・挿入脱落のバリアントも正規表現で網羅的に洗い出すこと**を追記する（feat-017 で「なんという」のみを検索して本件を見落とした教訓。案件 README.md §5.1）。ディレクトリ構成の変更はない |
| `README.md` | **更新不要**。コマンド・CLI オプション・入出力形式・既定値・実行環境のいずれも変わらない |
| 案件 `README.md` | ステータスを Closed に更新する |

## 12. 設計判断の記録（ADR）

### ADR-1: 「なんていいう → なんていう」を字形正規化テーブルに入れず、修正定義ファイルで扱う

- **決定**: `normalize_punct.py` の `CJK_REPLACEMENTS_CN` / `OLD_FORM_REPLACEMENTS` に追加せず、
  `{BASE2}/ocr/fixes/chap03.json` で補正する
- **理由**:
  1. 置換表は**1文字 → 1文字**の字形対応表である。本件は「い」の**削除**であり、
     1対1の字形対応として表現できない
  2. feat-011 ADR-3・feat-013 ADR-2・feat-015 ADR-1・feat-016 ADR-1・feat-017 ADR-1 で
     確立した方針（字形の1対1対応が成立しない個別誤認識は `apply_fixes.py` で扱う）と一致する
- **代替案**: 置換表に `なんていいう → なんていう` を追加する → 置換表の意味が
  「字形正規化」から「文字列置換」に変質し、テーブルの適用範囲（全書籍・常時適用）と
  リスクが釣り合わない。不採用

### ADR-2: feat-017 に含めず、独立した案件として扱う

- **決定**: feat-017 の `investigation.md` に追記して同案件内で対処するのではなく、
  feat-018 として独立に起票する
- **理由**: 対象文字列が異なり（`なんという` ではなく `なんていいう`）、feat-017 の
  要求仕様（「なんという」9件）とは別の誤りである。2026-09-01 のユーザー決定による
- **代替案**: feat-017 内で `investigation.md` に追記してステップ2〜7 を反復する
  （CLAUDE.md 機能追加フローのステップ7 に規定された経路）→ ユーザーが不採用を選択

### ADR-3: `old` の末尾を係助詞まで伸ばして一意化する

- **決定**: `old` を `なんていいうことはありません` / `なんていいうこともありません` とする
- **理由**: 2件は同一行にあり、「なんていいう」だけでは一意にならない。
  係助詞「は」「も」を含む「ことはありません」「こともありません」まで伸ばせば一意になる
  （§5 の実測）。数式（`3.5n`・`n/2`）を含める必要がないため、再 OCR 耐性が高い
- **代替案**: 直前の数式（`3.5n に近づいていく` / `n/2 に近づいていく`）を `old` に含める →
  数式の空白や記法が1文字でも変われば `old` が一致しなくなる。一意性の確保に不要な
  脆弱性を持ち込むため不採用（feat-015 ADR-3・feat-017 §4.5 と同じ判断）

### ADR-4: MinerU と `normalize_punct.py` を再実行しない

- **決定**: `apply_fixes.py` と `build_final.py` のみを実行する
- **理由**: 語彙単位の誤読は OCR の認識結果に起因し、同一入力に対して同じ結果になるため、
  再実行しても再発する（CLAUDE.md ドメイン知識「OCR の個別誤り…再OCRでも再発する」）。
  `normalize_punct.py` は置換表を変更しないため結果が変わらず、冪等でもある
- **代替案**: `ocr_dir.py --punct-style touten --final --fixes-dir ...` で chap03 を
  再実行する → MinerU の実行時間が無駄であり、run 番号が増えて履歴が追いにくくなる。不採用
  （feat-013 ADR-3・feat-015 ADR-4・feat-016 ADR-2・feat-017 ADR-4 と同じ判断）
