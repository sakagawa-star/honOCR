# feat-013 機能設計書: 字形正規化テーブルの拡充と確率統計への適用

対象要求仕様書: `docs/issues/feat-013-expand-cjk-table/requirements.md`

## 1. 対応要求マッピング

| 要求ID | 設計セクション |
|---|---|
| FR-001 字形正規化テーブルの拡充 | §4 |
| FR-002 確率統計の既存成果物への再適用 | §6 |
| FR-003 修正定義ファイルの作成と適用 | §5, §6 |
| FR-004 PRML への非影響の確認 | §7 |
| FR-006 旧字体の置換箇所の警告出力 | §4.2, §4.3 |
| FR-005 自動テスト | §8 |

## 2. システム構成

コードの変更は `scripts/normalize_punct.py` 1ファイルに閉じる。
新規スクリプトはなく、既存関数のシグネチャも変更しない
（追加するのは新規関数2つと定数2つ、および `main` への警告出力2行）。

```
scripts/
└── normalize_punct.py    # 変更: 置換表を3定数に分割し13エントリを追加（8 → 21種）、
                          #       旧字体の警告（find_old_forms / format_old_form_warning）を追加
tests/
└── test_normalize_punct.py   # 変更: テスト追加
```

`ocr_dir.py` は変更しない（`CJK_REPLACEMENTS` を参照する既存コードが自動的に追随し、
サブプロセスの標準エラーを素通しする既存の仕組みで警告が表示されるため）。

リポジトリ外に作成するデータ（コミットしない）:

```
{BASE2}/ocr/fixes/
├── chap02.json   # 新規（1件）
├── chap04.json   # 新規（1件）
├── chap05.json   # 新規（1件）
├── chap06.json   # 新規（1件）
└── chap09.json   # 新規（1件）
```

`{BASE2}` = `/home/sakagawa/work/確率統計`

## 3. 技術スタック

変更なし（Python 3.12.3 / 標準ライブラリのみ）。`docs/TECH_STACK.md` の更新は不要。

## 4. `normalize_punct.py` の変更（FR-001・FR-006）

### 4.1 置換表の定義（FR-001）

置換表を**種別ごとの3定数**に分割し、合成した結果を既存の名前 `CJK_REPLACEMENTS` に束ねる。
分割の目的は、FR-006 の警告対象（旧字体のみ）を二重管理せずに取り出せるようにすることである。

```python
# 簡体字・繁体字（日本語で正当に使われることはない）
CJK_REPLACEMENTS_CN: dict[str, str] = {
    # feat-011: PRML・確率統計 chap07 で実測
    "值": "値",
    "变": "変",
    "单": "単",
    "对": "対",
    "图": "図",
    "换": "換",
    "徵": "徴",
    "樣": "様",
    # feat-013: 確率統計 chap00〜09 で実測
    "黑": "黒",
    "說": "説",
    "题": "題",
    "戾": "戻",
    "边": "辺",
    "橫": "横",
    "虛": "虚",
    "錄": "録",
}

# 旧字体（固有名詞では正当な表記になりうる。FR-006 で置換箇所を警告する）
OLD_FORM_REPLACEMENTS: dict[str, str] = {
    # feat-013: 確率統計 chap00〜09 で実測
    "權": "権",
    "收": "収",
    "檢": "検",
    "縱": "縦",
    "廣": "広",
}

CJK_REPLACEMENTS: dict[str, str] = CJK_REPLACEMENTS_CN | OLD_FORM_REPLACEMENTS
```

`CJK_REPLACEMENTS` の名前・型・意味は変わらないため、これを参照する既存コード
（`build_replacements` / `normalize_text` / `ocr_dir.py` の `check_normalized`）は
一切変更しない（feat-011 の設計により自動的に追随する）。

### 4.2 旧字体の警告（FR-006）

```python
def find_old_forms(text: str) -> dict[str, tuple[int, str]]:
    """置換【前】のテキストから旧字体の出現を検出する。

    戻り値: 旧字体 -> (出現件数, 最初の出現箇所の文脈)。
    """
```

- 処理: `OLD_FORM_REPLACEMENTS` の各キーについて `text.count(ch)` が 1 以上のものを集める
- 文脈は `find_non_jis_kanji`（feat-011）と同じ規則で作る:
  `pos = text.find(ch)` として `text[max(0, pos - CONTEXT_CHARS):pos + CONTEXT_CHARS + 1]` を取り、
  改行（`\n`）と復帰（`\r`）を半角空白 1 文字に置換する（`CONTEXT_CHARS` = 25 は既存定数）

```python
def format_old_form_warning(name: str, found: dict[str, tuple[int, str]]) -> list[str]:
    """警告行のリストを返す（found が空なら空リスト）。"""
```

- 出力書式（FR-006）:
  - 1 行目: `{name}: 旧字体 {字種数} 種 {総件数} 件（固有名詞の可能性。必要なら fixes で復元すること）`
  - 2 行目以降: `sorted(found)` の順（コードポイント昇順・決定的）に
    `  '{ch}'→'{OLD_FORM_REPLACEMENTS[ch]}' x{件数}: ...{文脈}...`

### 4.3 `main` の処理順序（変更点）

feat-011 の `main` に対する変更は、**正規化前のテキストで旧字体を検出しておく**ことと、
警告を 2 種類出力することの 2 点のみ。

```python
for file_path in files:
    text = file_path.read_text(encoding="utf-8")
    old_forms = find_old_forms(text)              # 追加: 正規化【前】に検出する
    normalized, count = normalize_text(text, args.punct_style)
    output_path = outdir / file_path.name
    write_text_atomic(normalized, output_path, overwrite)   # 既存

    for line in format_old_form_warning(file_path.name, old_forms):        # 追加
        print(line, file=sys.stderr)
    for line in format_non_jis_warning(file_path.name, find_non_jis_kanji(normalized)):  # 既存
        print(line, file=sys.stderr)

    print(f"{file_path.name}: {count} replaced")   # 既存（書式変更なし）
```

- 旧字体の検出を**正規化前**に行うのは、正規化後では元の字が失われ、
  固有名詞かどうかを判断する手がかりが残らないためである（FR-006 基準2）
- 警告の順序は「旧字体 → JIS 外漢字」に固定する（決定的な出力にするため）
- 標準出力（集計行）の書式は変更しない

### 4.4 旧字体を置換表に入れる判断（重要）

旧字体5種（權・收・檢・縱・廣）は、**固有名詞では正当な表記になりうる**。
実例として確率統計 chap09 の奥付に「印刷·製本 廣済堂」があり、
これは旧字を正式名称に用いる実在の社名である。

本案件では 2026-08-28 のユーザー決定に従い、次の方針を採る。

- 固有名詞以外で旧字体が現れることは現代日本語ではないため、**置換表に入れて一律に置換する**
- 置換によって壊れる固有名詞は、**修正定義ファイルで個別に元へ戻す**（§5 の chap09）
- 固有名詞の破壊に気づけるよう、**置換した箇所を置換前の文脈つきで必ず警告する**（§4.2）

この3点目が運用上の要である。警告がなければ「置換して壊れたこと」に気づく手段がなく、
「目視で確認する」という運用も、どこを見ればよいかが分からないため機能しない。

## 5. 修正定義ファイルの内容（FR-003）

書式は `fixes/README.md`・`fixes/template.json` に従う
（トップレベル `{"fixes": [...]}`、各要素は `id` / `reason` / `old` / `new` の4キー・すべて非空文字列）。

`old` は「正規化・HTML表変換・脚注挿入がすべて済んだ md」の文字列として書く。
本案件では**字形正規化（FR-001 適用後）の md** を基準とする。

### 5.1 `{BASE2}/ocr/fixes/chap02.json`

```json
{
  "fixes": [
    {
      "id": "chap02-001",
      "reason": "p23 の式で選択肢のカタカナ「イ」が部首「亻」として認識された（原本 TIF 目視確認済み。他の選択肢は ウ・ア）。`\\text {イ}` は同章に11件、`\\underline {{\\text {イ}}}` は3件正当に存在するため、`| Y` まで含めて一意にしている",
      "old": "\\underline {{\\text {亻}}} | Y",
      "new": "\\underline {{\\text {イ}}} | Y"
    }
  ]
}
```

### 5.2 `{BASE2}/ocr/fixes/chap04.json`

```json
{
  "fixes": [
    {
      "id": "chap04-001",
      "reason": "p54 の脚注 *19「…という掟に反してしまうからです」の「掟」が「揾」と誤認識された（原本 TIF 目視確認済み）",
      "old": "という揾に反して",
      "new": "という掟に反して"
    }
  ]
}
```

### 5.3 `{BASE2}/ocr/fixes/chap05.json`

```json
{
  "fixes": [
    {
      "id": "chap05-001",
      "reason": "p43 の見出し「5.4.2 （ケース 2）対角行列の場合 —— 楕円」の「楕」が「椕」と誤認識された（原本 TIF 目視確認済み）",
      "old": "—— 椕円",
      "new": "—— 楕円"
    }
  ]
}
```

### 5.4 `{BASE2}/ocr/fixes/chap06.json`

```json
{
  "fixes": [
    {
      "id": "chap06-001",
      "reason": "p12 の式番号「……（イ）」の「イ」が部首「亻」として認識された（原本 TIF 目視確認済み）。`(\\text {イ})` は同章に別の式番号として1件存在するため、`\\dots \\dots` まで含めて一意にしている",
      "old": "\\dots \\dots (\\text {亻})",
      "new": "\\dots \\dots (\\text {イ})"
    }
  ]
}
```

### 5.5 `{BASE2}/ocr/fixes/chap09.json`（固有名詞の復元）

```json
{
  "fixes": [
    {
      "id": "chap09-001",
      "reason": "奥付の印刷会社「廣済堂」は旧字を正式名称に用いる実在の社名。feat-013 の字形正規化（廣→広）で壊れるため元に戻す",
      "old": "印刷·製本 広済堂",
      "new": "印刷·製本 廣済堂"
    }
  ]
}
```

**注意**: chap09 の `old` は「字形正規化を適用した**後**」の文字列である。
したがって §6 の手順では、必ず正規化 → 修正適用の順に実行する（順序を逆にすると
`old` が見つからず `apply_fixes.py` がエラーで停止する）。

### 5.6 一意性の確認（`old` と `new` の両方）

`apply_fixes.py` は次の2つを要求する（feat-010）。

1. `old` が md 内にちょうど1回出現すること
2. **適用後に `new` が md 内にちょうど1回出現すること**（最終不変条件）。
   これは「再実行が冪等にならない定義」を初回に検出するための検査である

**2 を見落とすと実装が失敗する。**2026-08-28 の初回実装では、chap02 と chap06 の
修正を `old = "\text {亻}"` / `new = "\text {イ}"` と定義したため、
`\text {イ}` が他所に正当に存在すること（chap02 で11件、chap06 で1件）により
最終不変条件に違反し、`apply_fixes.py` がエラーで停止した（案件 README.md §7）。

2026-08-28 の再実測による確定値（`run-NN-normalized` の md を対象）:

| 章 | `old` | `count(old)` | `new` | 適用前の `count(new)` | 適用後の `count(new)` |
|---|---|---|---|---|---|
| chap02 | `\underline {{\text {亻}}} \| Y` | 1 | `\underline {{\text {イ}}} \| Y` | 0 | 1 |
| chap04 | `という揾に反して` | 1 | `という掟に反して` | 0 | 1 |
| chap05 | `—— 椕円` | 1 | `—— 楕円` | 0 | 1 |
| chap06 | `\dots \dots (\text {亻})` | 1 | `\dots \dots (\text {イ})` | 0 | 1 |
| chap09 | `印刷·製本 広済堂` | 1 | `印刷·製本 廣済堂` | 0 | 1 |

**新しい修正を定義するときは、`old` の一意性だけでなく `new` の適用後の一意性も
必ず事前に数えること。**`new` が既に存在する場合は、一意になるまで前後の文脈を
`old` / `new` の両方に含める（本案件の chap02・chap06 がその例）。

## 6. 再適用の手順（FR-002・FR-003）

**MinerU は再実行しない。**`run-NN/` 配下の生出力は読み取りも変更もしない。

対象は全10章。run 番号は chap07 のみ `run-02`、他は `run-01`
（2026-08-28 の実行結果。実装時に `{BASE2}/ocr/mineru-full/chapNN/` を
`ls` して実際の最大 run 番号を確認すること）。

### 手順0: 旧字体の分類（事前ゲート。FR-002 基準8）

再適用に着手する前に、**正規化前の生出力**に対して旧字体5種の全出現箇所を列挙し、
固有名詞かどうかを分類する。

対象は **md と content_list.json の両方**である（手順1の正規化は両方を一律に置換するため、
md だけを見ると json にのみ現れる固有名詞を見落とす）。

```python
# 例: 正規化前の生出力（run-NN/.../hybrid_auto/）を対象に、前後25文字つきで列挙する
import re
from pathlib import Path
OLD_FORMS = "權收檢縱廣"
for f in [md_path, content_list_path]:          # 両方を対象にする
    text = f.read_text(encoding="utf-8")
    for ch in OLD_FORMS:
        for m in re.finditer(ch, text):
            ctx = text[max(0, m.start()-25):m.start()+26].replace("\n", " ")
            print(f"{f.name} [{ch}]: ...{ctx}...")
```

- 分類結果（各出現が「OCR 誤り」か「固有名詞」か）を案件 README.md に記録する
- 固有名詞と判定した箇所は、§5 の要領で修正定義ファイルに復元を登録する
- **未分類の出現が1件でも残っている状態で手順1〜3に進んではならない**
- **復元が効くのは md のみ**である（§6.1）。json 側の固有名詞は正規化された表記のままとなるが、
  これは許容する（要求仕様書 FR-002 基準9）

本案件では 2026-08-28 に実施済みであり、確率統計10章の旧字体9件のうち
固有名詞は chap09 の「廣済堂」1件のみであることを確認している
（案件 README.md §2・§4）。実装時はこの分類が現在のデータと一致することを再確認する。

各章について、次の3ステップをこの順に実行する。

### 手順1: 再正規化（インプレース）

```
uv run python scripts/normalize_punct.py \
  {NORM}/chapNN_gray300.md {NORM}/chapNN_gray300_content_list.json \
  -o {NORM} --punct-style touten --overwrite
```

- `{NORM}` = `{BASE2}/ocr/mineru-full/chapNN/run-NN-normalized`
- `--punct-style touten` を**必ず指定する**（確率統計は「、。」表記。
  指定を誤ると句読点が破壊される）
- 出力先を入力と同じディレクトリにし、`--overwrite` でインプレース更新する
- 字形正規化は冪等である（置換後の文字は置換対象に含まれない）ため、
  この手順を複数回実行しても結果は変わらない

### 手順2: 修正適用（該当5章のみ）

```
uv run python scripts/apply_fixes.py \
  {NORM}/chapNN_gray300.md {BASE2}/ocr/fixes/chapNN.json \
  -o {NORM} --overwrite
```

- 対象は chap02・chap04・chap05・chap06・chap09 の5章のみ
- 他の5章（chap00・01・03・07・08）は修正定義ファイルを作らないため実行しない

### 手順3: final の再構築

```
uv run python scripts/build_final.py {NORM} -o {BASE2}/ocr/final/chapNN --overwrite
```

- `build_final.py`（feat-012）が3種類の機械検証を行うため、
  バイト同一・画像参照・`img_path` 集合の一致がここで自動的に確認される
- `images/` は `run-NN-normalized/images/` からコピーされ、内容は変化しない

### 手順4: 全体の確認（実装時に実施し、結果を報告する）

1. 全10章の final の md・content_list.json に、FR-001 の21種
   （既存8種＋追加13種）が**1件も残らない**ことを確認する。
   ただし chap09 の `廣済堂` は FR-003 で復元した固有名詞であり、
   `廣` が md にちょうど1件残ることが**正しい状態**である
   （content_list 側は復元しないため `広済堂` のままとなる。§6.1 参照）
2. 全10章で「、」「。」が保持されることを確認する。
   **「，」「．」は0件になるとは限らない**（実測: chap02・03・04・05・09 に計21件）。
   `touten` スタイルは「、。→，．」の置換を行わないだけであり、
   原本が正当に用いている「，．」を除去するものではない。実測した21件はすべて原本由来である
   （chap09 の参考文献リスト13件、chap05 の箇条書き記号「イ．ロ．ハ．」3件、
   chap02・03 の「○と．の系列」という文字そのものへの言及3件、
   chap02・04 の数式の区切り2件）
3. 更新前後で md・content_list.json の文字列長が変わらないことを確認する
   （字形置換も §5 の修正もすべて同じ文字数であるため）
4. `final/chapNN/` の md・content_list.json が `run-NN-normalized/` と
   バイト同一であることを確認する（`build_final.py` の検証に含まれるが、再確認する）

### 6.1 md と content_list.json の非対称性（設計上の既知事項）

`apply_fixes.py` は md のみを対象とし、content_list.json を変更しない（feat-010 の設計）。
そのため §5 の5件の修正は md にのみ反映され、content_list 側には
「亻」「揾」「椕」および「広済堂」（復元されない）が残る。

**固有名詞の復元についても同じ非対称性が生じる**。chap09 の場合、
最終的な状態は次のようになる。

| ファイル | 「廣済堂」の表記 | 理由 |
|---|---|---|
| `final/chap09/chap09_gray300.md` | `廣済堂`（復元済み・正しい） | `apply_fixes.py` の適用対象 |
| `final/chap09/chap09_gray300_content_list.json` | `広済堂`（正規化されたまま） | `apply_fixes.py` の対象外 |

これは MinerU のスキーマを維持するための既存ポリシーであり、本案件では変更しない。
LLM に読ませる主成果物は md であり、content_list.json の主用途は `page_idx` による
原本ページとの対応付けと図ブロックの座標参照である（feat-005 ADR-7）ため、
実用上の影響はない。

なお、この非対称性により **md と content_list.json の同一箇所の文字列が一致しなくなる**が、
`build_final.py` の検証（feat-012）はコピー元と final のバイト同一性を見るものであり、
md と json の間の整合性は検査しないため、検証に影響しない。

## 7. PRML への非影響の確認（FR-004）

PRML の final（md 8ファイル・content_list.json 8ファイル）に対し、
FR-001 で追加する13種の出現回数を数える。2026-08-28 の実測値は **0 件**である。

実装時にこれを再確認し、0 件であることをもって
「PRML の成果物は再適用の対象外とし、変更しない」と結論する。
**PRML の `{BASE}/ocr/` 配下を書き換えてはならない。**

## 8. テスト設計（`tests/test_normalize_punct.py` に追加）

実データに依存しない合成データで行う。

| テスト名 | 対応 | 内容 |
|---|---|---|
| `test_cjk_feat013_simplified_and_traditional` | FR-001 | 「黑說题戾边橫虛錄」を含む入力が「黒説題戻辺横虚録」になる |
| `test_cjk_feat013_old_forms` | FR-001 | 「權收檢縱廣」を含む入力が「権収検縦広」になる |
| `test_cjk_table_has_21_entries` | FR-001 | `CJK_REPLACEMENTS` の要素数が21で、キーに重複がない（`len(set(keys)) == 21`） |
| `test_cjk_feat013_applies_in_touten_style` | FR-001 | `--punct-style touten` でも追加13種が置換される |
| `test_cjk_feat013_length_preserved` | FR-001 | 追加13種を含む入力で置換前後の `len` が等しい |
| `test_old_form_warning_emitted` | FR-006 | 「印刷·製本 廣済堂」を含む入力で `'廣'→'広' x1` と置換前の文脈が標準エラーに出る（`capsys`） |
| `test_old_form_warning_context_is_pre_normalization` | FR-006 | 警告の文脈に置換前の字（廣）が含まれ、置換後の字（広）に変わっていない |
| `test_old_form_warning_absent_for_cn_chars` | FR-006 | 簡体字「变」のみを含む入力では旧字体警告が出ない |
| `test_old_form_warning_exit_code_zero` | FR-006 | 旧字体警告が出ても戻り値が 0 |
| `test_old_form_table_is_subset_of_cjk` | FR-001/006 | `OLD_FORM_REPLACEMENTS` の全キーが `CJK_REPLACEMENTS` に含まれ、`CJK_REPLACEMENTS_CN` と交差しない |

既存テスト206件は改変しない。

## 9. ドキュメントの更新（完了処理で Claude Code 本体が実施する）

実装（Sonnet 委任）の対象外。完了処理として次を行う。

- `CLAUDE.md` のドメイン知識:
  - 字形正規化の対象を「8種」から「21種」に更新する
  - **旧字体5種は固有名詞で正当になりうるため、新しい書籍では出現箇所を目視確認し、
    固有名詞であれば修正定義ファイルで復元する運用**を追記する
  - **JIS 外漢字の警告は正規化時点の出力であり、脚注挿入（feat-009）で
    content_list から md へ持ち込まれる文字は md 側の警告に現れない。
    json 側の警告を正とみなす**ことを追記する
- `docs/BACKLOG.md` / `docs/CHANGELOG.md` の更新
- `README.md`: `normalize_punct.py` の説明の「8種」を「21種」に更新する

## 10. 設計判断の記録（ADR）

### ADR-1: 旧字体を置換表に入れ、固有名詞は修正定義ファイルで戻す

- 採用: 權・收・檢・縱・廣 を置換表に追加し、chap09 の「廣済堂」を修正定義ファイルで復元する
- 理由: 2026-08-28 のユーザー決定。「固有名詞以外では旧字体を現代日本語で使用しないため、
  一律に置換し、その後に固有名詞を個別に戻す」という運用
- 却下: 旧字体を置換表に入れず、章ごとに修正定義ファイルで直す —
  8件（確率統計のみ）を章ごとに書く手間が繰り返し発生し、
  新しい書籍でも同じ作業が必要になる
- リスクと対策: 固有名詞が黙って壊れうる。対策は2段構えとする。
  1. **機械的な検出**（FR-006・§4.2）: 置換した旧字体を、**置換前の文脈つきで**必ず
     標準エラーへ警告する。`ocr_dir.py` は正規化サブプロセスの標準エラーを素通しするため、
     一括実行でも必ず目に入る。これがなければ「置換して壊れたこと」に気づく手段がない
     （置換後のテキストからは元の字が失われるため、後から grep しても見つけられない）
  2. **運用ゲート**（FR-002 基準8・§6.0）: 新しい書籍では、再適用・final 構築の前に
     旧字体の全出現箇所を列挙して固有名詞かどうかを分類し、結果を案件ドキュメントに記録する。
     固有名詞であれば修正定義ファイルに復元を登録してから先に進む
- 却下した代替案: 旧字体の置換を「監査済みの書籍でのみ有効化する」オプションにする —
  書籍ごとに設定を切り替える仕組みが必要になり、指定漏れという別の事故要因を生む。
  警告＋運用ゲートで十分に検出可能であると判断した

### ADR-2: 「椕→楕」を置換表に入れず修正定義ファイルで扱う

- 採用: `apply_fixes.py` で chap05 の1件のみを修正する
- 理由: 「椕」は「楕」の字形バリアントではなく個別の誤認識である。
  feat-011 ADR-3 の基準（1対1対応が確立している文字のみ置換表に入れる）に従う
- 却下: 置換表に入れる — 対応関係が確立していないため、別の文脈で誤置換する危険がある

### ADR-3: MinerU を再実行せず、正規化からやり直す

- 採用: `run-NN-normalized/` に対する再正規化 → 修正適用 → `build_final.py` の3ステップ
- 却下: `ocr_dir.py` を `--final` 付きで再実行する — MinerU に約35分かかるうえ、
  OCR 結果自体は変わらないため無意味である。さらに run 番号が増えて履歴が分かりにくくなる
- 却下: `final/` を直接書き換える — `final/` は `run-NN-normalized/` からの
  コピーであり（feat-012）、コピー元を更新せずに final だけ変えると
  次回の final 再構築で変更が失われる

### ADR-4: 再正規化をインプレース（`-o` に入力と同じディレクトリ）で行う

- 採用: `normalize_punct.py` の出力先を `run-NN-normalized` 自身にし `--overwrite` を付ける
- 理由: `run-NN-normalized/` は「正規化済みの中間成果物」という位置づけであり、
  置換表の更新を反映した状態に保つのが正しい。別ディレクトリに出すと
  `run-NN-normalized/` が古いままとなり、次回 `build_final.py` を実行したときに
  修正が失われる
- 注意: `build_final.py` は出力先が入力と重なる場合を拒否するが（feat-012）、
  `normalize_punct.py` にはその制約がなく、インプレース更新が可能である
  （`write_text_atomic` により原子的に置換される）
