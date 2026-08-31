# feat-015 機能設計書: chap02 の Q&A コラム見出しの分断修復

対象案件: `docs/issues/feat-015-chap02-split-heading/`
要求仕様書: 同フォルダの `requirements.md`

## 1. 対応要求マッピング

| 要求 | 設計箇所 |
|---|---|
| FR-001 修正定義ファイルへの追記 | §4（追記内容）・§5（一意性の確認） |
| FR-002 分断した見出しの結合 | §4（`old` / `new` の設計）・§7 手順1 |
| FR-003 「なんという」の誤読の訂正 | §4（同一 fix に含める）・§7 手順1・ADR-2 |
| FR-004 既存成果物への適用と final 再構築 | §6（適用手順）・§7（確認手順） |
| FR-005 影響範囲の限定 | §3（変更しないもの）・§7 手順3 |

## 2. システム構成

本案件は**リポジトリ内のコードを変更しない**。既存スクリプトを引数を変えて実行するのみである。

```
{BASE2} = /home/sakagawa/work/確率統計
{NORM}  = {BASE2}/ocr/mineru-full/chap02/run-01-normalized
{FINAL} = {BASE2}/ocr/final/chap02
{FIXES} = {BASE2}/ocr/fixes/chap02.json   ← 本案件で追記（リポジトリ外・既存ファイル）

  {NORM}/chap02_gray300.md ──┐
                             ├─→ apply_fixes.py ──→ {NORM}/chap02_gray300.md（インプレース更新）
  {FIXES} ───────────────────┘

  {NORM}/（md + content_list.json + images/）
        └─→ build_final.py ──→ {FINAL}/（再構築・3種類の機械検証）
```

chap02 は `run-01` のみが存在する（2026-08-31 実測: `{BASE2}/ocr/mineru-full/chap02/` の内容は
`run-01` / `run-01-normalized` / `run-01.log` の3つ）。
実装時に `ls {BASE2}/ocr/mineru-full/chap02/` を実行し、`run-01-normalized` が存在すること、
およびそれが最大の run 番号であることを確認する。異なっていた場合は中断して報告する。

## 3. 変更しないもの（FR-005）

| 対象 | 理由 |
|---|---|
| `scripts/` 配下のすべてのファイル | 本案件はデータ側の修正のみで実現できる |
| `tests/test_*.py`（テストコード） | コード変更がないため、テストの追加・変更も生じない。ただし `tests/results/feat-015_test_result.txt` は検証記録として**新規作成する**（CLAUDE.md「テスト」のルール。§7 手順4） |
| `{NORM}/chap02_gray300_content_list.json` | `apply_fixes.py` は md のみを対象とする（feat-010 の設計）。§8 の非対称性 |
| `{NORM}/images/`・`{FINAL}/images/` | 画像は本案件の対象外。`build_final.py` がコピーするのみ（47 ファイル） |
| `{BASE2}/ocr/fixes/chap02.json` の既存 fix `chap02-001` | feat-013 で作成・適用済み。本案件では追記のみを行う |
| `{BASE2}/ocr/fixes/` の他5ファイル（chap04・05・06・07・09） | 本案件の対象外 |
| chap02 以外の9章、および PRML（`{BASE}`）の成果物 | 見出しの分断は chap02 の1件のみ（案件 README.md §6.1）。「なんという」の残り9件は本案件のスコープ外（requirements.md §7） |
| `{BASE2}/ocr/mineru-full/chap02/run-01/`（MinerU 生出力） | 読み取りも変更もしない |

## 4. 修正定義ファイルへの追記内容（FR-001・FR-002・FR-003）

`{BASE2}/ocr/fixes/chap02.json` の `fixes` 配列の**末尾**に、次の1件を追記する
（既存の `chap02-001` は1文字も変更しない）。追記後のファイル全体は次のとおりになる。

```json
{
  "fixes": [
    {
      "id": "chap02-001",
      "reason": "p23 の式で選択肢のカタカナ「イ」が部首「亻」として認識された（原本 TIF 目視確認済み。他の選択肢は ウ・ア）。`\\text {イ}` は同章に11件、`\\underline {{\\text {イ}}}` は3件正当に存在するため、`| Y` まで含めて一意にしている",
      "old": "\\underline {{\\text {亻}}} | Y",
      "new": "\\underline {{\\text {イ}}} | Y"
    },
    {
      "id": "chap02-002",
      "reason": "p41（原本 page-08_2R.tif）の Q&A コラム見出し「? 2.2」が MinerU の layout 解析により2ブロックに分断され、md 上で「見出し行＋空行＋本文段落」になっていた（原本 TIF 目視確認済み。原本では1つの質問文が2行に組まれているだけ）。分断を解消して1行の見出しに結合する。あわせて、同じ行で原本の「なんていう」が「なんという」と誤読されていたのを訂正する（原本 TIF 目視確認済み）。「分数の分数」は同章に2件、「てしまいました。」は2件あるため、両者を改行込みでつないだ形にして old を一意にしている",
      "old": "なんという分数の分数になっ\n\nてしまいました。",
      "new": "なんていう分数の分数になってしまいました。"
    }
  ]
}
```

### 4.1 `old` / `new` の設計

- `old` の `\n\n` は JSON のエスケープであり、`json.loads` で**実際の改行2つ**に展開される。
  `apply_fixes.py` は md 全文を1つの文字列として `str.count()` / `str.replace()` するため
  （`scripts/apply_fixes.py` の `apply_fixes()`）、複数行にまたがる `old` を指定できる
- `apply_fixes.py` の `validate_fixes()` は `old` / `new` に対して「非空」「`old != new`」しか
  検査せず、改行を含む文字列を拒否しない（2026-08-31 にコードを確認）
- md の該当箇所は次の3行である（546〜548 行目）。この `old` は 546 行目の途中から
  548 行目の途中までを覆い、間の空行（547 行目）と2つの改行を取り除く

  ```
  546: ## ? 2.2 本文の例の条件つき確率を式 (2.7) で求めようとしたら、 $\frac{3/16}{9/16}$ なんという分数の分数になっ
  547: （空行）
  548: てしまいました。これはどうやって計算したらいいのですか？
  ```

- 適用後の 546 行目は次の1行になる（`## ` の見出し記法が保たれるため、Markdown 上は
  1つの `<h2>` として解釈される）

  ```
  ## ? 2.2 本文の例の条件つき確率を式 (2.7) で求めようとしたら、 $\frac{3/16}{9/16}$ なんていう分数の分数になってしまいました。これはどうやって計算したらいいのですか？
  ```

- `old` の先頭を「なんという」から始めているのは、見出し行の前半（`## ? 2.2 本文の例の…`）まで
  含めなくても一意性が確保できるためである（§5）。文脈を長くするほど再 OCR 時に
  文面が変わって一致しなくなる可能性が上がる（feat-016 ADR-3 と同じ判断）
- `old` の末尾を「てしまいました。」で止め、後続の「これはどうやって計算したらいいのですか？」を
  含めていないのも同じ理由による（一意性は「てしまいました。」までで確保できる。§5）

## 5. 一意性の確認（FR-001 受け入れ基準 4・5）

`apply_fixes.py` は、適用後に**全 fix について `count(old) == 0` かつ `count(new) == 1`** を
検査し、1つでも破れていればエラー終了して出力を書かない（最終不変条件。feat-010 FR-003 規則6）。
そのため `old` の一意性だけでなく、**適用後に `new` がちょうど1件になること**を事前に数える
（CLAUDE.md の運用ルール。feat-013 でこれを怠って実装が1度中断した）。

2026-08-31 に `{NORM}/chap02_gray300.md`（= `{FINAL}` の md とバイト同一）で実測した件数。
`\n` は実際の改行を表す。

| 文字列 | 適用前 | 適用後（予測） | 判定 |
|---|---|---|---|
| `分数の分数` | 2 | 2 | 文脈なしでは一意にならない（もう1件は 1058 行目「(分数の分数にとまどった方は…」） |
| `てしまいました。` | 2 | 2 | 同上（もう1件は 740 行目「…全く対等になってしまいました。」） |
| `なんという` | 1 | **0** | 参考値（`old` には使わない） |
| `なんていう` | 0 | **1** | 参考値（`new` には使わない） |
| `なんという分数の分数になっ\n\nてしまいました。` | **1** | 0 | **`old` に採用**（一意） |
| `なんていう分数の分数になってしまいました。` | **0** | **1** | **`new` に採用**（適用後ちょうど1件） |

既存の `chap02-001` についても、追記後の最終不変条件を満たすことを確認済みである。

| fix | 文字列 | 適用前 | 適用後（予測） |
|---|---|---|---|
| `chap02-001` | `old` = `\underline {{\text {亻}}} \| Y` | 0 | 0 |
| `chap02-001` | `new` = `\underline {{\text {イ}}} \| Y` | 1 | 1 |

（表中の `\|` は Markdown のセル区切りと区別するためのエスケープであり、
実際の文字列では半角の `|` である。）

`chap02-001` は feat-013 で適用済みのため `count(old) == 0` / `count(new) == 1` であり、
`apply_fixes.py` の規則2により **skipped** として扱われ、最終不変条件も満たす。
新規 `chap02-002` の `old` / `new` は `chap02-001` の `old` / `new` と文字列として重ならないため、
逐次適用の順序による干渉は生じない。

## 6. 適用手順（FR-004）

**MinerU（`ocr_dir.py`）と `normalize_punct.py` は実行しない。**
`{NORM}` は feat-013 の再適用（2026-08-28）で字形正規化済みの状態にあり、
本案件は置換表を変更しないため、再正規化しても結果は変わらない。

### 手順0: 事前確認（実行前に必ず行う）

```bash
ls /home/sakagawa/work/確率統計/ocr/mineru-full/chap02/

uv run python -c "
p = '/home/sakagawa/work/確率統計/ocr/mineru-full/chap02/run-01-normalized/chap02_gray300.md'
t = open(p, encoding='utf-8').read()
print('old', t.count('なんという分数の分数になっ\n\nてしまいました。'))
print('new', t.count('なんていう分数の分数になってしまいました。'))
print('なんという', t.count('なんという'))
print('なんていう', t.count('なんていう'))
print('分数の分数', t.count('分数の分数'))
print('てしまいました。', t.count('てしまいました。'))
print('chars', len(t))
print('lines', len(t.split('\n')))
"

cmp /home/sakagawa/work/確率統計/ocr/mineru-full/chap02/run-01-normalized/chap02_gray300.md \
    /home/sakagawa/work/確率統計/ocr/final/chap02/chap02_gray300.md

sha256sum \
  /home/sakagawa/work/確率統計/ocr/mineru-full/chap02/run-01-normalized/chap02_gray300_content_list.json \
  /home/sakagawa/work/確率統計/ocr/final/chap02/chap02_gray300_content_list.json
```

- `run-01-normalized` が存在し、それが最大の run 番号であること
- 期待値: `old` = 1、`new` = 0、`なんという` = 1、`なんていう` = 0、
  `分数の分数` = 2、`てしまいました。` = 2、`chars` = 69002、`lines` = 1865
- **件数はすべて Python の `str.count()` による出現回数で数える**。`grep -c` は
  マッチした「行数」を返すため、`apply_fixes.py` の不変条件（`str.count()` ベース）と
  数え方が一致しない。本書のすべての件数確認で `grep -c` を使ってはならない
- `cmp` が無出力であること（`{NORM}` と `{FINAL}` の md がバイト同一。差分があれば未反映の変更が存在する）
- `sha256sum` の2行のハッシュが互いに一致し、かつ次の値であること（2026-08-31 実測）

  ```
  a4ebb69a04863ac89c6b7ef1e2cf737377b20b168f50aa665ad523bf3aff260f
  ```

  この値は §7 手順3 で `content_list.json` が変更されていないことを検証するために使う
  （FR-004 基準7）

いずれかが期待と異なる場合は、その場で回避策を取らず**中断して報告する**。

また、更新前の md を作業用にコピーしておく（成果物ディレクトリの**外**、
スクラッチパッド等に置く。§7 手順2 の `diff` で使う）。

### 手順1: 修正定義ファイルへの追記

§4 の内容で `/home/sakagawa/work/確率統計/ocr/fixes/chap02.json` を更新する。

- 既存の `chap02-001` の4キーを1文字も変更しないこと
- 追記後に `python -c "import json; json.load(open(...))"` で JSON として妥当なことと、
  `fixes` 配列の要素数が 2 であることを確認する
- 既存ファイルが §4 に示した `chap02-001` の内容と異なっていた場合は、上書きせず
  **中断して報告する**

### 手順2: 修正の適用

```bash
uv run python scripts/apply_fixes.py \
  /home/sakagawa/work/確率統計/ocr/mineru-full/chap02/run-01-normalized/chap02_gray300.md \
  /home/sakagawa/work/確率統計/ocr/fixes/chap02.json \
  -o /home/sakagawa/work/確率統計/ocr/mineru-full/chap02/run-01-normalized --overwrite
```

- 出力先を入力と同じディレクトリにし、`--overwrite` でインプレース更新する（feat-013 ADR-4 と同じ）
- 期待: 終了コード 0、標準出力に次の2行

  ```
  chap02_gray300.md: 1 applied, 1 skipped
  total: 1 applied, 1 skipped
  ```

### 手順3: final の再構築

```bash
uv run python scripts/build_final.py \
  /home/sakagawa/work/確率統計/ocr/mineru-full/chap02/run-01-normalized \
  -o /home/sakagawa/work/確率統計/ocr/final/chap02 --overwrite
```

- 期待: 終了コード 0（バイト同一・画像参照・`img_path` 集合一致の3検証がすべて合格）

## 7. 確認手順（FR-002〜FR-005 の受け入れ基準）

### 手順1: 修正内容の確認

手順0 と同じ数え方（`str.count()` による出現回数）で、`{NORM}` と `{FINAL}` の
両方の md を確認する。

```bash
uv run python -c "
for label, path in [
    ('NORM',  '/home/sakagawa/work/確率統計/ocr/mineru-full/chap02/run-01-normalized/chap02_gray300.md'),
    ('FINAL', '/home/sakagawa/work/確率統計/ocr/final/chap02/chap02_gray300.md'),
]:
    t = open(path, encoding='utf-8').read()
    print(label, 'old', t.count('なんという分数の分数になっ\n\nてしまいました。'))
    print(label, 'new', t.count('なんていう分数の分数になってしまいました。'))
    print(label, 'なんという', t.count('なんという'))
    print(label, 'なんていう', t.count('なんていう'))
    print(label, '## ? 2.3', t.count('## ? 2.3'))
    print(label, 'chars', len(t))
    print(label, 'lines', len(t.split('\n')))
"
```

期待値（`{NORM}` / `{FINAL}` とも同じ）:

| 項目 | 期待値 | 対応する受け入れ基準 |
|---|---|---|
| `old`（分断形）の出現回数 | 0 | FR-002 基準2 |
| `new`（結合形）の出現回数 | 1 | FR-001 基準5 |
| `なんという` の出現回数 | 0 | FR-003 基準1 |
| `なんていう` の出現回数 | 1 | FR-003 基準2 |
| `## ? 2.3` の出現回数 | 1 | FR-002 基準4（後続の見出しを巻き込んでいない） |
| 文字数 | 69000（適用前 69002 − 改行2） | FR-004 基準3 |
| 行数 | 1863（適用前 1865 − 2） | FR-002 基準3 |

あわせて修正後の見出し行を確認する（期待: 546 行目に1件）。

```bash
grep -n "なんていう分数の分数になってしまいました。" \
  /home/sakagawa/work/確率統計/ocr/final/chap02/chap02_gray300.md
```

出力行が `## ? 2.2 ` で始まり、末尾が `これはどうやって計算したらいいのですか？` で
終わっていることを目視で確認する。

### 手順2: 差分が1箇所のみであることの確認

手順0 で退避した適用前の md と、適用後の md の `diff` を取る。

```bash
diff /tmp/.../chap02_gray300.md.before \
     /home/sakagawa/work/確率統計/ocr/final/chap02/chap02_gray300.md
```

期待される差分は**ハンク1つのみ**で、内容は次のとおりである。

- 削除される 3 行: 546 行目（`…なんという分数の分数になっ`）、547 行目（空行）、
  548 行目（`てしまいました。これは…ですか？`）
- 追加される 1 行: 結合後の見出し行

他の行に差分があってはならない（FR-004 基準4）。

### 手順3: 非影響の確認（FR-005）

```bash
git status --short
```

期待される変更は次の2種類のみである。それ以外（`scripts/`・`tests/test_*.py`）に
変更があってはならない。

- `docs/issues/feat-015-chap02-split-heading/` 配下（案件ドキュメント）
- `tests/results/feat-015_test_result.txt`（新規作成。手順4）

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

期待される出力は次の**9 行**である（md 側 4 章 ＋ content_list 側 5 章）。
これらは本案件のスコープ外であり、**残っているのが正しい状態**である（requirements.md §7）。

| ファイル | 期待件数 | 備考 |
|---|---|---|
| `chap01/chap01_gray300.md` | 1 | スコープ外（feat-017 予定） |
| `chap01/chap01_gray300_content_list.json` | 1 | スコープ外 |
| `chap02/chap02_gray300_content_list.json` | 1 | **本案件で修正しない**（§8 の非対称性） |
| `chap03/chap03_gray300.md` | 3 | スコープ外 |
| `chap03/chap03_gray300_content_list.json` | 3 | スコープ外 |
| `chap06/chap06_gray300.md` | 4 | スコープ外 |
| `chap06/chap06_gray300_content_list.json` | 4 | スコープ外 |
| `chap08/chap08_gray300.md` | 1 | スコープ外 |
| `chap08/chap08_gray300_content_list.json` | 1 | スコープ外 |

`chap02/chap02_gray300.md` が出力に**含まれない**ことが、本案件の修正が効いた証拠である。

さらに次を確認する。

- `{FINAL}/images/` のファイル数が **47** のままであること
- `{NORM}` と `{FINAL}` の `chap02_gray300_content_list.json` が**バイト単位で変更されていない**こと
  （FR-004 基準7）。`git` 管理外のため、手順0 で記録した SHA-256 と照合して検証する。
  mtime とサイズの比較では、同サイズの変更や mtime の復元を検出できないため用いない

  ```bash
  sha256sum \
    /home/sakagawa/work/確率統計/ocr/mineru-full/chap02/run-01-normalized/chap02_gray300_content_list.json \
    /home/sakagawa/work/確率統計/ocr/final/chap02/chap02_gray300_content_list.json
  ```

  期待: 2行とも
  `a4ebb69a04863ac89c6b7ef1e2cf737377b20b168f50aa665ad523bf3aff260f`
  （手順0 で記録した値と同一。`build_final.py` は `{NORM}` から `{FINAL}` へ
  コピーし直すが、コピー元が不変であるため `{FINAL}` 側のハッシュも変わらない）

### 手順4: 自動テストの全件実行（FR-005 基準5）

```bash
uv run pytest -v > tests/results/feat-015_test_result.txt 2>&1
```

- コード変更がないため、feat-016 完了時点と同じくすべて成功することを確認する
- 上記コマンドは出力を `tests/results/feat-015_test_result.txt` に**保存しながら**実行する
  （CLAUDE.md「テスト」のルール: テストコマンドの出力をそのまま保存する）。
  保存後、ファイルの末尾で全件成功（`failed` が 0 件）であることを確認する

## 8. md と content_list.json の非対称性（既知事項）

`apply_fixes.py` は md のみを対象とし、`content_list.json` を変更しない（feat-010 の設計）。
そのため最終的な状態は次のようになる。

| ファイル | 当該箇所の状態 | 理由 |
|---|---|---|
| `final/chap02/chap02_gray300.md` | 1行の見出しに結合済み・「なんていう」（正しい） | `apply_fixes.py` の適用対象 |
| `final/chap02/chap02_gray300_content_list.json` | index 250 / 251 の2ブロックのまま・「なんという」（誤りのまま） | `apply_fixes.py` の対象外 |

これは feat-013 §6.1・feat-016 §8 で許容済みの既存ポリシーであり、本案件では変更しない。
LLM に読ませる主成果物は md であり、`content_list.json` の主用途は `page_idx` による
原本ページとの対応付けと図ブロックの座標参照である（feat-005 ADR-7）ため、実用上の影響はない。
また `build_final.py` の検証はコピー元と final のバイト同一性・画像参照の整合を見るものであり、
md と json の間の本文の一致は検査しないため、検証にも影響しない。

## 9. エラーハンドリングと境界条件

| 事象 | 挙動 | 対応 |
|---|---|---|
| `old` が md に存在しない（0件）かつ `new` が1件 | `apply_fixes.py` は `skipped` として扱い終了コード 0・内容不変 | 冪等性の担保。手順2 を2回実行しても安全 |
| `old` が2件以上 | `apply_fixes.py` がエラー終了（出力なし） | 中断して報告する（想定外。文面が変わっている） |
| `old` も `new` も0件 | `apply_fixes.py` がエラー終了（出力なし） | 中断して報告する |
| 適用後に `new` が2件以上 | 最終不変条件違反でエラー終了（出力なし） | 中断して報告する（§5 の実測と矛盾する） |
| 既存の `chap02-001` が最終不変条件に違反 | 同上 | 中断して報告する（feat-013 の適用状態が変わっている） |
| `chap02.json` が JSON として不正 | `apply_fixes.py` が読み込み時にエラー終了 | 追記内容を見直す（手順1 の JSON 妥当性確認で事前に検出する） |
| `build_final.py` の3検証のいずれかが不合格 | 終了コード 1 | 中断して報告する |
| 出力先が入力と同一・入れ子、またはシンボリックリンク | `build_final.py` が書き込み前に拒否 | 本案件のパス指定では発生しない（`{NORM}` と `{FINAL}` は別ツリー） |

## 10. 実装の担当と進め方

CLAUDE.md「実装の実行方法（Sonnetサブエージェント）」に従い、**Agent ツールで model: sonnet を
指定したサブエージェントに委任する**。委任時に渡す情報は次のとおり。

1. 必読ドキュメントと順序: `CLAUDE.md` → 本案件の `requirements.md` → 本 `design.md` →
   `fixes/README.md`・`fixes/template.json` → `scripts/apply_fixes.py`・`scripts/build_final.py`
2. 厳密準拠（本書に書かれていない独自判断・改善・リファクタは禁止。**コードは1行も変更しない**）
3. 想定外事象（§9 の「中断して報告する」に該当する事象を含む）が起きたら回避策を実装せず
   直ちに中断し、何が起きたか・どこまで完了したかを報告して終了する
4. 検証まで実施（§7 の手順1〜4、`tests/results/feat-015_test_result.txt` への保存）
5. 禁止事項: git commit / push、`docs/BACKLOG.md` / `docs/CHANGELOG.md` / `CLAUDE.md` /
   `README.md` の更新（完了処理で Claude Code 本体が行う）
6. 報告形式: 変更ファイル一覧、テスト結果サマリ、§7 の確認結果、想定外事象の有無

## 11. ドキュメントの更新（完了処理で Claude Code 本体が実施する）

| ファイル | 更新内容 |
|---|---|
| `docs/BACKLOG.md` | feat-015 の行を追加し、ステータスを Closed に更新する |
| `docs/CHANGELOG.md` | 完了内容を記録する |
| `CLAUDE.md` | ドメイン知識に「MinerU は見出しを2ブロックに分断することがあり、機械的な検出手段がないため手動テストで見つけて `apply_fixes.py` で対処する」旨を追記する（複数行にまたがる `old` が指定できることを含む）。ディレクトリ構成の変更はない（リポジトリ内のファイル追加・削除がないため） |
| `README.md` | **更新不要**。コマンド・CLI オプション・入出力形式・既定値・実行環境のいずれも変わらない |
| 案件 `README.md` | ステータスを Closed に更新する |

## 12. 設計判断の記録（ADR）

### ADR-1: 「なんという → なんていう」を字形正規化テーブルに入れず、修正定義ファイルで扱う

- **決定**: `normalize_punct.py` の `CJK_REPLACEMENTS_CN` / `OLD_FORM_REPLACEMENTS` に追加せず、
  `{BASE2}/ocr/fixes/chap02.json` で補正する
- **理由**:
  1. 置換表は**1文字 → 1文字**の字形対応表である。「と → て」は字形の対応関係ではなく、
     字単位の置換にすれば本文が全面的に破壊される
  2. 「なんという」という5文字の並びに限っても、「なんという大事件だ」のように
     日本語として正当な用法がある。一般規則にすると誤置換のリスクが残る
  3. feat-011 ADR-3・feat-013 ADR-2・feat-016 ADR-1 で確立した方針（字形の1対1対応が
     成立しない個別誤認識は `apply_fixes.py` で扱う）と一致する
- **代替案**: 置換表に `なんという → なんていう` を追加する → 置換表の意味が
  「字形正規化」から「文字列置換」に変質し、テーブルの適用範囲（全書籍・常時適用）と
  リスクが釣り合わない。不採用

### ADR-2: 分断の結合と「なんという」の訂正を1件の fix にまとめる

- **決定**: `chap02-002` の1件で、見出しの結合と誤読の訂正を同時に行う
- **理由**:
  1. 誤読「なんという」は、分断を結合する `old` の内部にある。2件の fix に分けると、
     先行 fix の `new` を後続 fix の `old` が書き換える形になり、`apply_fixes.py` の
     最終不変条件（全 fix について適用後 `count(old) == 0` かつ `count(new) == 1`）を
     満たせなくなる（`fixes/README.md` の注意書きに明示されている禁止パターン）
  2. 原本の1行に対する1つの修正であり、`reason` に両方の根拠を書けば追跡性は保たれる
- **代替案**:
  - 誤読を残したまま結合する → 原本と異なる文字列を成果物に残すことになり、
    「入力への忠実な OCR」という本プロジェクトのゴールに反する。不採用
  - 2件の fix に分ける → 上記1の理由により `apply_fixes.py` がエラー停止する。不採用

### ADR-3: `old` に見出し行の先頭（`## ? 2.2 `）を含めない

- **決定**: `old` = `なんという分数の分数になっ\n\nてしまいました。` とする
- **理由**: 「分数の分数」（2件）と「てしまいました。」（2件）はそれぞれ単独では
  一意でないが、両者を改行込みでつないだ形は適用前に1件しかない（§5 の実測）。
  一意性がこれで確保できる以上、文脈を長くするほど再 OCR 時に文面が変わって
  一致しなくなる可能性が上がる（feat-016 ADR-3 と同じ判断）
- **代替案**: 見出し行全体（`## ? 2.2 本文の例の…`）を `old` に含める → 数式
  `$\frac{3/16}{9/16}$` を含むことになり、再 OCR で数式の空白や記法が1文字でも変われば
  `old` が一致しなくなる。一意性の確保に不要な脆弱性を持ち込むため不採用

### ADR-4: MinerU と `normalize_punct.py` を再実行しない

- **決定**: `apply_fixes.py` と `build_final.py` のみを実行する
- **理由**: 見出しの分断は MinerU の layout 解析に起因し、同一入力に対して同じ結果になる
  ため、再実行しても再発する（CLAUDE.md ドメイン知識「OCR の個別誤り…再OCRでも再発する」）。
  `normalize_punct.py` は置換表を変更しないため結果が変わらず、冪等でもある
- **代替案**: `ocr_dir.py --punct-style touten --final --fixes-dir ...` で chap02 を
  再実行する → MinerU の実行時間が無駄であり、run 番号が増えて履歴が追いにくくなる。不採用
  （feat-013 ADR-3・feat-016 ADR-2 と同じ判断）
