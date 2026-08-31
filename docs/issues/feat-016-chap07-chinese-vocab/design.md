# feat-016 機能設計書: chap07 の中国語語彙誤認識「上的」の修正

対象案件: `docs/issues/feat-016-chap07-chinese-vocab/`
要求仕様書: 同フォルダの `requirements.md`

## 1. 対応要求マッピング

| 要求 | 設計箇所 |
|---|---|
| FR-001 修正定義ファイルの新規作成 | §4（ファイル内容）・§5（一意性の確認） |
| FR-002 既存成果物への適用と final 再構築 | §6（適用手順）・§7（確認手順） |
| FR-003 影響範囲の限定 | §3（変更しないもの）・§7 手順3 |

## 2. システム構成

本案件は**リポジトリ内のコードを変更しない**。既存スクリプトを引数を変えて実行するのみである。

```
{BASE2} = /home/sakagawa/work/確率統計
{NORM}  = {BASE2}/ocr/mineru-full/chap07/run-02-normalized
{FINAL} = {BASE2}/ocr/final/chap07
{FIXES} = {BASE2}/ocr/fixes/chap07.json   ← 本案件で新規作成（リポジトリ外）

  {NORM}/chap07_gray300.md ──┐
                             ├─→ apply_fixes.py ──→ {NORM}/chap07_gray300.md（インプレース更新）
  {FIXES} ───────────────────┘

  {NORM}/（md + content_list.json + images/）
        └─→ build_final.py ──→ {FINAL}/（再構築・3種類の機械検証）
```

`run-02` は 2026-08-28 の実行結果である（chap07 のみ `run-02`、他章は `run-01`）。
実装時に `ls {BASE2}/ocr/mineru-full/chap07/` を実行し、`run-02-normalized` が存在すること、
およびそれが最大の run 番号であることを確認する。異なっていた場合は中断して報告する。

## 3. 変更しないもの（FR-003）

| 対象 | 理由 |
|---|---|
| `scripts/` 配下のすべてのファイル | 本案件はデータ側の修正のみで実現できる |
| `tests/test_*.py`（テストコード） | コード変更がないため、テストの追加・変更も生じない。ただし `tests/results/feat-016_test_result.txt` は検証記録として**新規作成する**（CLAUDE.md「テスト」のルール。§7 手順4） |
| `{NORM}/chap07_gray300_content_list.json` | `apply_fixes.py` は md のみを対象とする（feat-010 の設計） |
| `{NORM}/images/`・`{FINAL}/images/` | 画像は本案件の対象外。`build_final.py` がコピーするのみ |
| chap07 以外の9章、および PRML（`{BASE}`）の成果物 | 「上的」は chap07 の1件のみ（案件 README.md §5） |
| `{BASE2}/ocr/mineru-full/chap07/run-01*` および `run-02/`（MinerU 生出力） | 読み取りも変更もしない |

## 4. 修正定義ファイルの内容（FR-001）

`{BASE2}/ocr/fixes/chap07.json` を次の内容で**新規作成**する（UTF-8・末尾に改行あり）。

```json
{
  "fixes": [
    {
      "id": "chap07-001",
      "reason": "p8（原本 page-05_2R.tif）の本文で、原本の「[0,1) 上の一様分布」の「の」が中国語の「的」として認識された（原本 TIF 目視確認済み）。「的」は「比較的」等で正当に使われる字であり字形正規化テーブルでは扱えないため、修正定義ファイルで補正する。「上の一様分布」は同章に16件存在するため、直前の「[0,1)」まで含めて old / new の両方を一意にしている",
      "old": "[0,1)上的一様分布",
      "new": "[0,1)上の一様分布"
    }
  ]
}
```

- `[0,1)` の `[` `0` `,` `1` `)` はすべて**半角**である（2026-08-31 に該当箇所のコードポイントで確認:
  `0x5b 0x30 0x2c 0x31 0x29`）。全角で書くと `old` が一致せず `apply_fixes.py` がエラーになる
- 「上的一様分布」の直後は「に従う」であるが、`old` / `new` の一意性は直前の `[0,1)` だけで
  確保できるため（§5）、後方の文脈は含めない
- 書式は `fixes/template.json` および `fixes/README.md` に従う

## 5. 一意性の確認（FR-001 受け入れ基準 3・4）

`apply_fixes.py` は、適用後に**全 fix について `count(old) == 0` かつ `count(new) == 1`** を
検査し、1つでも破れていればエラー終了して出力を書かない（最終不変条件。feat-010 FR-003 規則6）。
そのため `old` の一意性だけでなく、**適用後に `new` がちょうど1件になること**を事前に数える
（CLAUDE.md の運用ルール。feat-013 でこれを怠って実装が1度中断した）。

2026-08-31 に `{NORM}/chap07_gray300.md`（= `{FINAL}` の md とバイト同一）で実測した件数:

| 文字列 | 適用前 | 適用後（予測） | 判定 |
|---|---|---|---|
| `上的` | 1 | 0 | — |
| `上の` | 22 | 23 | 参考値（`old` / `new` には使わない） |
| `上的一様分布` | 1 | 0 | 文脈なしでは `new` 側が16件になるため不採用 |
| `上の一様分布` | 16 | 17 | 同上 |
| `[0,1)上的一様分布` | **1** | 0 | `old` に採用（一意） |
| `[0,1)上の一様分布` | **0** | **1** | `new` に採用（適用後ちょうど1件） |

`old` = `[0,1)上的一様分布` は適用前に1件、`new` = `[0,1)上の一様分布` は適用前0件・適用後1件と
なり、最終不変条件を満たす。

## 6. 適用手順（FR-002）

**MinerU（`ocr_dir.py`）と `normalize_punct.py` は実行しない。**
`{NORM}` は feat-013 の再適用（2026-08-28）で字形正規化済みの状態にあり、
本案件は置換表を変更しないため、再正規化しても結果は変わらない。

### 手順0: 事前確認（実行前に必ず行う）

```bash
ls /home/sakagawa/work/確率統計/ocr/mineru-full/chap07/

uv run python -c "
t = open('/home/sakagawa/work/確率統計/ocr/mineru-full/chap07/run-02-normalized/chap07_gray300.md', encoding='utf-8').read()
print('上的', t.count('上的'))
print('[0,1)上的一様分布', t.count('[0,1)上的一様分布'))
print('[0,1)上の一様分布', t.count('[0,1)上の一様分布'))
print('上の一様分布', t.count('上の一様分布'))
print('chars', len(t))
"

cmp /home/sakagawa/work/確率統計/ocr/mineru-full/chap07/run-02-normalized/chap07_gray300.md \
    /home/sakagawa/work/確率統計/ocr/final/chap07/chap07_gray300.md
```

- `run-02-normalized` が存在すること
- 期待値: `上的` = 1、`[0,1)上的一様分布` = 1、`[0,1)上の一様分布` = 0、
  `上の一様分布` = 16、`chars` = 22958
- **件数はすべて Python の `str.count()` による出現回数で数える**。`grep -c` は
  マッチした「行数」を返すため、`apply_fixes.py` の不変条件（`str.count()` ベース）と
  数え方が一致しない。本書のすべての件数確認で `grep -c` を使ってはならない
- `{NORM}` と `{FINAL}` の md がバイト同一であること（差分があれば未反映の変更が存在する）

いずれかが期待と異なる場合は、その場で回避策を取らず**中断して報告する**。

また、更新前の md の文字数（2026-08-31 実測: **22958 文字**）を記録しておく
（手順3の確認で使う）。

### 手順1: 修正定義ファイルの作成

§4 の内容で `/home/sakagawa/work/確率統計/ocr/fixes/chap07.json` を新規作成する。
既存ファイルがある場合は上書きせず**中断して報告する**（2026-08-31 時点では
`chap02・04・05・06・09.json` の5件のみが存在し、chap07 は存在しない）。

### 手順2: 修正の適用

```bash
uv run python scripts/apply_fixes.py \
  /home/sakagawa/work/確率統計/ocr/mineru-full/chap07/run-02-normalized/chap07_gray300.md \
  /home/sakagawa/work/確率統計/ocr/fixes/chap07.json \
  -o /home/sakagawa/work/確率統計/ocr/mineru-full/chap07/run-02-normalized --overwrite
```

- 出力先を入力と同じディレクトリにし、`--overwrite` でインプレース更新する（feat-013 ADR-4 と同じ）
- 期待: 終了コード 0、標準出力に `applied = 1`（実際の表記は `apply_fixes.py` の実装に従う）

### 手順3: final の再構築

```bash
uv run python scripts/build_final.py \
  /home/sakagawa/work/確率統計/ocr/mineru-full/chap07/run-02-normalized \
  -o /home/sakagawa/work/確率統計/ocr/final/chap07 --overwrite
```

- 期待: 終了コード 0（バイト同一・画像参照・`img_path` 集合一致の3検証がすべて合格）

## 7. 確認手順（FR-002・FR-003 の受け入れ基準）

### 手順1: 修正内容の確認

手順0 と同じ数え方（`str.count()` による出現回数）で、`{NORM}` と `{FINAL}` の
両方の md を確認する。

```bash
uv run python -c "
for label, path in [
    ('NORM',  '/home/sakagawa/work/確率統計/ocr/mineru-full/chap07/run-02-normalized/chap07_gray300.md'),
    ('FINAL', '/home/sakagawa/work/確率統計/ocr/final/chap07/chap07_gray300.md'),
]:
    t = open(path, encoding='utf-8').read()
    print(label, '上的', t.count('上的'))
    print(label, '[0,1)上の一様分布', t.count('[0,1)上の一様分布'))
    print(label, '上の一様分布', t.count('上の一様分布'))
    print(label, 'chars', len(t))
"
```

期待値（`{NORM}` / `{FINAL}` とも同じ）:

| 項目 | 期待値 |
|---|---|
| `上的` の出現回数 | 0 |
| `[0,1)上の一様分布` の出現回数 | 1 |
| `上の一様分布` の出現回数 | 17（適用前16 ＋ 本修正1） |
| 文字数 | 22958（適用前と不変） |

あわせて修正箇所の行番号を確認する（期待: 228 行目に1件）。

```bash
grep -n "\[0,1)上の一様分布" {FINAL}/chap07_gray300.md
```

### 手順2: 差分が1箇所のみであることの確認

適用前の md を作業用にコピーしておき（スクラッチパッド等、成果物ディレクトリの外）、
適用後と `diff` を取る。期待される差分は 228 行目の1行のみで、その行の変化は
`上的一様分布` → `上の一様分布` のみである。

### 手順3: 非影響の確認（FR-003）

```bash
git status --short
```

期待される変更は次の2種類のみである。それ以外（`scripts/`・`tests/test_*.py`）に
変更があってはならない。

- `docs/issues/feat-016-chap07-chinese-vocab/` 配下（案件ドキュメント）
- `tests/results/feat-016_test_result.txt`（新規作成。手順4）

確率統計 final 全10章に「上的」が残っていないことを、出現回数で確認する。

```bash
uv run python -c "
from pathlib import Path
root = Path('/home/sakagawa/work/確率統計/ocr/final')
for f in sorted(root.glob('chap*/*')):
    if f.suffix in ('.md', '.json'):
        n = f.read_text(encoding='utf-8').count('上的')
        if n:
            print(f, n)
"
```

期待: `chap07/chap07_gray300_content_list.json` の **1 件のみ**が出力される。

- `{NORM}/chap07_gray300_content_list.json` に「上的」が **1 件残る**ことが**正しい状態**である
  （§8 の非対称性）
- `{FINAL}/images/` のファイル数が **16** のままであることを確認する

### 手順4: 自動テストの全件実行（FR-003 基準5）

```bash
uv run pytest -v > tests/results/feat-016_test_result.txt 2>&1
```

- コード変更がないため、feat-013 完了時点と同じくすべて成功することを確認する
- 上記コマンドは出力を `tests/results/feat-016_test_result.txt` に**保存しながら**実行する
  （CLAUDE.md「テスト」のルール: テストコマンドの出力をそのまま保存する）。
  保存後、ファイルの末尾で全件成功（`failed` が 0 件）であることを確認する

## 8. md と content_list.json の非対称性（既知事項）

`apply_fixes.py` は md のみを対象とし、`content_list.json` を変更しない（feat-010 の設計）。
そのため最終的な状態は次のようになる。

| ファイル | 当該箇所の表記 | 理由 |
|---|---|---|
| `final/chap07/chap07_gray300.md` | `[0,1)上の一様分布`（修正済み・正しい） | `apply_fixes.py` の適用対象 |
| `final/chap07/chap07_gray300_content_list.json` | `[0,1)上的一様分布`（誤りのまま） | `apply_fixes.py` の対象外 |

これは feat-013 §6.1 で許容済みの既存ポリシーであり、本案件では変更しない。
LLM に読ませる主成果物は md であり、`content_list.json` の主用途は `page_idx` による
原本ページとの対応付けと図ブロックの座標参照である（feat-005 ADR-7）ため、実用上の影響はない。
また `build_final.py` の検証はコピー元と final のバイト同一性を見るものであり、
md と json の間の整合性は検査しないため、検証にも影響しない。

## 9. エラーハンドリングと境界条件

| 事象 | 挙動 | 対応 |
|---|---|---|
| `old` が md に存在しない（0件）かつ `new` が1件 | `apply_fixes.py` は `skipped` として扱い終了コード 0・内容不変 | 冪等性の担保。手順2 を2回実行しても安全 |
| `old` が2件以上 | `apply_fixes.py` がエラー終了（出力なし） | 中断して報告する（想定外。文面が変わっている） |
| `old` も `new` も0件 | `apply_fixes.py` がエラー終了（出力なし） | 中断して報告する |
| 適用後に `new` が2件以上 | 最終不変条件違反でエラー終了（出力なし） | 中断して報告する（§5 の実測と矛盾する） |
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
4. 検証まで実施（§7 の手順1〜4、`tests/results/feat-016_test_result.txt` への保存）
5. 禁止事項: git commit / push、`docs/BACKLOG.md` / `docs/CHANGELOG.md` / `CLAUDE.md` /
   `README.md` の更新（完了処理で Claude Code 本体が行う）
6. 報告形式: 変更ファイル一覧、テスト結果サマリ、§7 の確認結果、想定外事象の有無

## 11. ドキュメントの更新（完了処理で Claude Code 本体が実施する）

| ファイル | 更新内容 |
|---|---|
| `docs/BACKLOG.md` | feat-016 のステータスを Closed に更新する |
| `docs/CHANGELOG.md` | 完了内容を記録する |
| `CLAUDE.md` | 「字形対応が成立しない誤認識」の例に語彙単位の誤り（`上的`→`上の`）を追記する。ディレクトリ構成の変更はない（リポジトリ内のファイル追加・削除がないため） |
| `README.md` | **更新不要**。コマンド・CLI オプション・入出力形式・既定値・実行環境のいずれも変わらない |
| 案件 `README.md` | ステータスを Closed に更新する |

## 12. 設計判断の記録（ADR）

### ADR-1: 「上的 → 上の」を字形正規化テーブルに入れず、修正定義ファイルで扱う

- **決定**: `normalize_punct.py` の `CJK_REPLACEMENTS_CN` / `OLD_FORM_REPLACEMENTS` に追加せず、
  `{BASE2}/ocr/fixes/chap07.json` で補正する
- **理由**:
  1. 置換表は**1文字 → 1文字**の字形対応表である。「的 → の」は字形の対応関係ではなく、
     「比較的」「一般的な」等で「的」が正当に使われる（実測: 確率統計 final に多数）ため、
     字単位の置換にすると本文を破壊する
  2. 2文字「上的」に限っても、日本語で「〜上、的確に」のような並びが将来の書籍で
     出現しうる。一般規則にすると誤置換のリスクが残る
  3. feat-011 ADR-3・feat-013 ADR-2 で確立した方針（字形の1対1対応が成立しない個別誤認識は
     `apply_fixes.py` で扱う）と一致する
- **代替案**: 置換表に `上的 → 上の` を2文字ルールとして追加する → 置換表の意味が
  「字形正規化」から「文字列置換」に変質し、テーブルの適用範囲（全書籍・常時適用）と
  リスクが釣り合わない。不採用

### ADR-2: MinerU と `normalize_punct.py` を再実行しない

- **決定**: `apply_fixes.py` と `build_final.py` のみを実行する
- **理由**: MinerU は同一入力に対して同じ結果を出すうえ 10 章で約 35 分かかる。本案件は
  chap07 の1章のみだが、再実行しても「上的」は再現する（layout / 認識結果は変わらない）。
  `normalize_punct.py` は置換表を変更しないため結果が変わらず、冪等でもある
- **代替案**: `ocr_dir.py --punct-style touten --final --fixes-dir ...` で chap07 を
  再実行する → MinerU の実行時間が無駄であり、run 番号が増えて履歴が追いにくくなる。不採用
  （feat-013 ADR-3 と同じ判断）

### ADR-3: `old` / `new` に直前の `[0,1)` を含める

- **決定**: `old` = `[0,1)上的一様分布`、`new` = `[0,1)上の一様分布` とする
- **理由**: `old` = `上的` だけでも適用前は一意だが、`new` = `上の` は適用後に 23 件となり
  `apply_fixes.py` の最終不変条件（`count(new) == 1`）に違反してエラー停止する。
  直前の `[0,1)` を含めると `new` は適用後ちょうど1件になる（§5 の実測）
- **代替案**: 後方の「に従う」まで含める → 一意性は `[0,1)` だけで確保できており、
  文脈を長くするほど再 OCR 時に文面が変わって一致しなくなる可能性が上がる。不採用
