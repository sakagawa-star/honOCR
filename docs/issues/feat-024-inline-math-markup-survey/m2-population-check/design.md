# feat-024 M2 機能設計書: 母集団の検証と逆引き可能性の判定

- **案件 / マイルストーン**: feat-024 / **M2**（`docs/issues/feat-024-inline-math-markup-survey/m2-population-check/`）
- **作成日**: 2026-09-07
- **準拠**: `docs/DESIGN_STANDARD.md`
- **必読の関連文書**: `requirements.md`（本マイルストーンの要求と**判定基準**）/ `../roadmap.md` /
  `../survey_notes.md`（**候補の定義（§3）・逆引きの予備実測（§7）**）/ `../m1-scan-cli/design.md`（候補 TSV の列）

**本設計書と上記4文書だけで実行できる。**

---

## 1.1 対応要求マッピング

| 要求ID | 内容 | 設計セクション |
|---|---|---|
| FR-M2-001 | 検査1（除外領域の対） | §4 |
| FR-M2-002 | 検査2（`D4` 16件の被覆） | §5 |
| FR-M2-003 | 検査3（逆引きの成功率） | §6・§7 |
| FR-M2-004 | 予測と実測の照合 | §8 |
| FR-M2-005 | 判定結果の報告 | §8.3 |
| NFR-M2-001 | データ不変性 | §9.1 |
| NFR-M2-002 | 再現可能性 | §6.2・§9.2 |
| NFR-M2-003 | 処理時間 | §7.5 |
| NFR-M2-004 | 対応環境 | §1.3 |

---

## 1.2 システム構成

### 新設するもの

| パス | 役割 | git 管理 |
|---|---|---|
| `m2-population-check/check_d4_coverage.py` | 検査2 のスクリプト（**ジョブスクリプト・実験コード**） | **する** |
| `m2-population-check/locate_candidates.py` | 逆引きのスクリプト（同上。**M3 でも使う**。ADR-M2-2） | **する** |
| `m2-population-check/experiment_log.md` | 予測・実測・照合の記録 | **する** |

**検査1 はスクリプトを作らない**（`grep -c` で足りる。§4）。

### 生成するデータ

| パス | 内容 | git 管理 |
|---|---|---|
| `{BASE2}/ocr/collation/feat-024_m2_d4_coverage.tsv` | 検査2 の結果（**見出しの文脈を含む**） | **しない**（リポジトリ外） |
| `{BASE2}/ocr/collation/feat-024_m2_locate_sample.tsv` | 検査3 の検査標本60件と逆引き結果（**候補の文脈を含む**） | **しない**（リポジトリ外） |

### 入力（すべて読み取りのみ）

| パス | 内容 |
|---|---|
| `{BASE2}/ocr/collation/feat-024_candidates.tsv` | M1 の候補 TSV（4,782行＋ヘッダ） |
| `{BASE2}/ocr/final/chapNN/chapNN_gray300.md` | 成果物 md（全10章） |
| `{BASE2}/ocr/final/chapNN/chapNN_gray300_content_list.json` | content_list（全10章） |

### 依存関係

```
候補 TSV ─┬─▶ check_d4_coverage.py ──▶ d4_coverage.tsv    （検査2）
          │        ▲
   md ────┴────────┘
          │
          └─▶ locate_candidates.py ──▶ locate_sample.tsv   （検査3）
                     ▲
   content_list ─────┘
```

**`scripts/scan_plain_math.py`（M1）を変更しない。** 本マイルストーンは M1 の出力を入力に使うだけである。

---

## 1.3 技術スタック

- **言語**: Python 3.12。**標準ライブラリのみ** — `argparse` / `csv` / `json` / `pathlib` / `random` / `re` / `sys`
  - 本マイルストーンのスクリプトは**入力の TSV を読む**ため `csv` を使ってよい
    （M1 が `csv` を使わないのは**出力**の書式を単純に保つためであり〔`../m1-scan-cli/design.md` ADR-M1-5〕、
    読み取りには制約がない）。ただし**出力の TSV は M1 と同じ流儀**（タブ区切り・引用符なし・
    タブと改行を半角スペースに置換）で書く
  - **Pillow を import しない**（原本画像を開かない。`requirements.md` §1.7 範囲外4）
- `docs/TECH_STACK.md` は**更新しない**（依存が増えないため）

---

## 4. 検査1: 除外領域の対（FR-M2-001）

### 4.1 手順

スクリプトを作らず、次のコマンドで実施する。

```bash
B2=/home/sakagawa/work/確率統計
for f in $B2/ocr/final/chap*/*_gray300.md; do
  ch=$(basename $(dirname "$f"))
  fence=$(grep -c '^```' "$f")
  disp=$(grep -c '^\$\$' "$f")
  echo "$ch fence=$fence disp=$disp fence_even=$((fence % 2 == 0)) disp_even=$((disp % 2 == 0))"
done
```

**`fence_even` / `disp_even` は 1 が偶数（合格）、0 が奇数（不合格）である。**

### 4.2 判定

- **合格**: 全10章で `fence` と `disp` がともに偶数
- **不合格**: いずれかの章で奇数 → **M3 に進まず原因を特定する**（`requirements.md` FR-M2-001 受け入れ基準4）。
  奇数になった章の該当行を `grep -n` で列挙し、対が閉じていない箇所を特定して報告する

### 4.3 記録

章ごとの `fence` と `disp` の実測値を `experiment_log.md` に記録する（§8.1 の予測と照合する）。

---

## 5. 検査2: `D4` 16件の被覆（FR-M2-002）

### 5.1 `check_d4_coverage.py` の仕様

**配置**: `m2-population-check/check_d4_coverage.py`

| 引数 | 種別 | 説明 |
|---|---|---|
| `--candidates` | 必須 | 候補 TSV のパス |
| `--final-root` | 必須 | `{BASE2}/ocr/final`（章ディレクトリの親） |
| `-o` / `--out` | 必須 | 出力 TSV のパス |
| `--overwrite` | フラグ | 既存ファイルの上書きを許可する |

**対象16件の定義**（スクリプト内の定数として持つ。`requirements.md` FR-M2-002 の表と同一）:

```python
D4_TARGETS: tuple[tuple[str, str], ...] = (
    ("chap02", "2.1"), ("chap02", "2.4"), ("chap02", "2.7"), ("chap02", "2.12"),
    ("chap03", "3.3"),
    ("chap04", "4.5"), ("chap04", "4.8"),
    ("chap05", "5.1"), ("chap05", "5.6"),
    ("chap07", "7.1"), ("chap07", "7.3"), ("chap07", "7.4"),
    ("chap08", "8.4"), ("chap08", "8.7"),
    ("chap09", "A.2"), ("chap09", "B.1"),
)
```

### 5.2 処理ロジック

```
1. 候補 TSV を読み、(chapter, line) をキーに候補をまとめる
   （line は md の行番号。M1 の出力列。../m1-scan-cli/design.md §3.2）
2. D4_TARGETS の各件について:
   2-1. その章の md を読み、見出し行を探す
        正規表現: ^##\s+\?\s*{番号をエスケープしたもの}(\s|$)
        （feat-020 により全74件が「## ? N.M …」の見出し行になっている。../survey_notes.md §1.2）
        - ちょうど1行 → その行番号を採る
        - 0 行 または 2 行以上 → 「見出し行を特定できない」として記録し、次の件へ進む
          （エラーで停止しない。件数と理由を報告することが目的のため）
   2-2. その (chapter, 見出し行の行番号) に属する候補を 1 の索引から引く
   2-3. 候補の件数と種別（G / L / C の内訳）、所在（location）を記録する
3. 出力 TSV を書き出す
4. 標準エラーへサマリを出力する
```

**番号のエスケープ**: `2.1` の `.` は正規表現のメタ文字であるため `re.escape` を適用する。
**`2.1` が `2.12` に前方一致しないよう、番号の直後に `\s` または行末を要求する**
（例: `^##\s+\?\s*2\.1(\s|$)` は `## ? 2.12 …` にマッチしない）。

### 5.3 出力 TSV の仕様

ヘッダ行（タブ区切り）:

```
chapter	number	heading_line	status	n_candidates	kinds	location	not_covered_reason	heading_text
```

| 列 | 内容 |
|---|---|
| `chapter` | 章名 |
| `number` | Q&A 番号（`2.1` 等） |
| `heading_line` | 見出し行の行番号（1 始まり）。特定できない場合は `-1` |
| `status` | **`covered`（その行に属する母集団の候補〔`location != table`〕が1件以上ある）** / **`not_covered`（母集団の候補が0件）** / `heading_not_found`（見出し行を特定できない）。**`table` の候補は `covered` の判定に数えない**（母集団外のため。`../roadmap.md` 前提6） |
| `n_candidates` | その行に属する候補の件数 |
| `kinds` | 種別の内訳（例: `G=0,L=2,C=1`） |
| `location` | その行の所在（候補がある場合。複数あれば `;` 区切りで一意化した値） |
| `not_covered_reason` | `status=not_covered` のときの分類（`requirements.md` FR-M2-002 受け入れ基準3）。**`no_symbol`（その行に候補が1件も無い）/ `table_only`（候補はあるが所在がすべて `table`）の2値で網羅的**である。`status` が `not_covered` 以外のときは空文字 |
| `heading_text` | 見出し行の全文（**書籍本文を含むため出力先はリポジトリ外**。`requirements.md` §1.5 制約1） |

**`not_covered_reason` の決め方**（スクリプトが機械的に判定する）:

```
その (chapter, heading_line) に属する候補を、候補 TSV から location を問わず集める。
  all   = その行の候補（location を問わない）
  pop   = all のうち location != table のもの（＝母集団の候補）

  - len(pop) >= 1  → status = "covered"、       not_covered_reason = ""（空文字）
  - len(pop) == 0 かつ len(all) == 0 → status = "not_covered"、not_covered_reason = "no_symbol"
  - len(pop) == 0 かつ len(all) >= 1 → status = "not_covered"、not_covered_reason = "table_only"
```

**この3分岐で網羅されており、他の値は生じない**（`len(pop)` は 0 か 1 以上のいずれかであり、
`len(pop) == 0` のとき `len(all)` は 0 か 1 以上のいずれかであるため）。
**`other` という分類は設けない。**

**サニタイズ**: タブ・改行を半角スペースに置換する（M1 と同じ流儀）。

### 5.4 標準エラーへのサマリ

```
d4 coverage: covered={n1} not_covered={n2} heading_not_found={n3} (total 16)
not_covered breakdown: no_symbol={r1} table_only={r2}
```

**書籍本文をサマリに含めない。**

### 5.5 判定

| 項目 | 扱い |
|---|---|
| **`heading_not_found`** | **合格条件（0 件であること）**。1件でもあれば**検査3 に進まず中断**し、原因を特定して報告する（`requirements.md` FR-M2-002 受け入れ基準1）。feat-020 により全74件が見出し行になっているため、特定できない件があることは**前提が崩れていることを意味する** |
| **`not_covered`** | **合格ラインを設けない**（同 受け入れ基準4）。件数を記録し、「本手法で検出できない型」の実測値として M5 の報告に引き渡す |

`not_covered` の件については、**スクリプトが出力した `not_covered_reason` を確認し、
分類別の件数（`no_symbol` / `table_only`）を `experiment_log.md` に記録する**
（`requirements.md` FR-M2-002 受け入れ基準3）。
**この2分類は §5.3 の3分岐により網羅的であり、目視での追加分類は行わない。**
この分類別件数は **M5 の報告に「本手法で検出できない型」の根拠として引き渡す**。

---

## 6. 検査3 の検査標本（FR-M2-003）

### 6.1 抽出の仕様

`locate_candidates.py` に検査標本の抽出機能を持たせる（§7.1 の `--sample-size` / `--seed`）。

```
1. 候補 TSV を読み、location が table 以外の行だけを残す（母集団 4,624 件）
2. chapter 昇順 → offset 昇順でソートする
3. rng = random.Random(20260907) を作る
4. rng.sample(母集団, 60) で検査標本を得る
5. 検査標本を chapter 昇順 → offset 昇順に並べ直す（作業順を安定させるため）
```

**乱数の使い方をこの手順に固定する。** `random.Random` のインスタンスを1つ作り、
ソート済みの母集団に対して1回だけ `sample` を呼ぶ。**この順序を変えると同じシードでも別の標本になる。**

### 6.2 再現性の確認（FR-M2-003 受け入れ基準5）

同じコマンドを別の出力先に対して実行し、`diff` が無出力であることを確認する。

```bash
uv run python docs/issues/feat-024-inline-math-markup-survey/m2-population-check/locate_candidates.py \
  --candidates <候補TSV> --final-root <{BASE2}/ocr/final> \
  --sample-size 60 --seed 20260907 -o /tmp/locate_recheck.tsv
diff <出力済みのTSV> /tmp/locate_recheck.tsv && echo "REPRODUCIBLE"
```

---

## 7. `locate_candidates.py` の詳細設計（FR-M2-003）

**配置**: `m2-population-check/locate_candidates.py`

**M3 でもこのスクリプトを使う**（M3 では `--sample-size` を使わず、M3 の標本 TSV を入力にする）。
M3 で仕様変更が必要になった場合は、完了済みの M2 のファイルを変更せず
「ロードマップの改訂（再計画）」に従う（ADR-M2-2）。

### 7.1 インターフェース

| 引数 | 種別 | 既定 | 説明 |
|---|---|---|---|
| `--candidates` | 必須 | — | 候補 TSV のパス（母集団の抽出母体） |
| `--final-root` | 必須 | — | `{BASE2}/ocr/final`（md と content_list を含む章ディレクトリの親） |
| `--sample-size` | 任意 | なし | 指定時は母集団から無作為抽出する（検査3 用） |
| `--seed` | 任意 | なし | `--sample-size` と対で指定する乱数シード |
| `--input-sample` | 任意 | なし | 既存の標本 TSV を入力にする（**M3 用**。`--sample-size` と排他） |
| `-o` / `--out` | 必須 | — | 出力 TSV のパス |
| `--overwrite` | フラグ | 偽 | 既存ファイルの上書きを許可する |

**`--sample-size` と `--input-sample` は排他**である。両方指定された場合、
または両方省略された場合は、標準エラーへメッセージを出して**終了コード 1** とする。
`--sample-size` を指定して `--seed` を省略した場合も同様である（再現性が失われるため）。

```python
def norm(s: str) -> str:
    """md と content_list の表記差を吸収する正規化。
    正規表現 [\\s#>|*\\\\_`\\-:]+ にマッチする文字をすべて除去する。"""

def load_blocks(content_list: Path) -> list[dict]:
    """content_list を読み、text を持つブロックを (index, norm(text), page_idx) で返す。"""

def find_block(md: str, blocks: list, offset: int, symbol: str) -> tuple[int, int, str] | None:
    """【1段階目のみ・非再帰】1件の候補について content_list のブロックを一意に特定する。
    成功時は (block_index, page_idx, key_kind) を返す。key_kind は "block_key10" / "block_key30"。
    一意に特定できなければ None を返す（複数一致・0件のいずれも None）。
    **この関数はページ推定を行わず、自分自身も locate_candidate も呼ばない。**"""

def locate_candidate(md: str, blocks: list, chapter_cands: list, i: int) -> tuple[str, int, int, str]:
    """【統括】章内候補列 chapter_cands の i 番目の候補を逆引きし、
    (stage, block_index, page_idx, reason) を返す。
    1段階目は find_block を1回呼ぶ。2段階目の近傍探索でも【find_block だけ】を呼び、
    locate_candidate を再帰的に呼ばない。特定できない値は -1 とする。"""

def main(argv: list[str] | None = None) -> int: ...
```

### 7.2 逆引きの処理ロジック（2段階）

**正規化関数**: `norm(s)` = `s` から正規表現 `[\s#>|*\\_`\-:]+` にマッチする文字を**すべて除去**した文字列
（`../survey_notes.md` §7）。

**1段階目（ブロックの直接特定）**:

```
key10 = norm( md[max(0, offset-10) : offset + len(symbol) + 10] )
その章の content_list の全ブロックについて norm(block["text"]) を作り、
key10 を部分文字列として含むブロックを探す。
  - ちょうど1件 → find_block は (block_index, page_idx, "block_key10") を返す
  - 2件以上     → 【確定しない】key30 を試さず None を返す（曖昧なため2段階目へ）
  - 0件         → key30 = norm( md[max(0, offset-30) : offset + len(symbol) + 30] ) で再試行
                    - ちょうど1件 → (block_index, page_idx, "block_key30") を返す
                    - それ以外    → None を返す（2段階目へ）
```

**一意一致だけを `block` とする理由**: md の文字オフセットと content_list の `block_index` は
**同一の座標系ではない**（`../survey_notes.md` §7.3）。複数一致から「近い方」を選ぶ規則は定義できず、
誤ったブロックを原本として採ると**原本を見ていないのに判定してしまう**。

**0件のときにキーを長くする理由**: キーを短くすると一致件数が増えて曖昧性が上がる。
広い範囲では他のブロックと重なりにくくなるため、一意一致が得られることがある。

**2段階目（近傍候補によるページ特定。一致検証つき）**:

```
章内候補列 = 同じ章の候補 TSV の全候補（table を含む）を offset 昇順に並べたもの。
対象候補の位置を i とする。

【方向ごとの状態を先に確定する】
  n_fwd = i より後ろにある候補の件数   （= len(列) - i - 1）
  n_bwd = i より前にある候補の件数     （= i）

【各方向を走査する（上限 200 件）】
  fwd = i+1 から後方へ最大 200 件走査し、最初に find_block が None 以外を返した候補の page_idx
        （見つからなければ None）
  bwd = i-1 から前方へ最大 200 件走査し、最初に find_block が None 以外を返した候補の page_idx
        （見つからなければ None）

  ※ 近傍探索では【find_block だけ】を呼ぶ。locate_candidate を再帰的に呼ばない
    （呼ぶと近傍候補についてさらに近傍探索が走り、再帰・循環しうる）

【判定】
  fwd is not None かつ bwd is not None:
      fwd == bwd → stage="page", page_idx=fwd, reason="page_both"
      fwd != bwd → stage="none",               reason="page_mismatch"
  fwd is not None かつ bwd is None:
      n_bwd == 0 → stage="page", page_idx=fwd, reason="page_head"   （対象候補が章内候補列の先頭）
      n_bwd >  0 → stage="none",               reason="search_exhausted"
  fwd is None かつ bwd is not None:
      n_fwd == 0 → stage="page", page_idx=bwd, reason="page_tail"   （対象候補が章内候補列の末尾）
      n_fwd >  0 → stage="none",               reason="search_exhausted"
  fwd is None かつ bwd is None:
      n_fwd == 0 かつ n_bwd == 0 → stage="none", reason="no_neighbor"（章内候補列に他の候補が無い）
      それ以外                    → stage="none", reason="search_exhausted"
```

**一方向のみを `page` とするのは `n_fwd == 0` または `n_bwd == 0` のときに限る。**
探索の打ち切り（200 件）で見つからなかった場合は「章の端である」ことを意味しないため、
**`none`（`search_exhausted`）とする**（`requirements.md` FR-M2-003 の「`page` を成功に数える条件」4）。

**前後の一致を要求する理由**: `page` は近傍候補からの**推定**であり、
対象候補が本当にそのページにあることをスクリプトは検証しない。
前後の双方から同じページが得られれば、対象候補はその2つの候補に挟まれた位置にあり、
**同じページにある蓋然性が高い**。前後で異なるページが得られた場合、対象候補は
**ページの境界をまたぐ位置にある**（どちらのページか決められない）ため、
成功に数えず `none` とする。

**章の端（`page_head` / `page_tail`）を `page` とする理由**: そこでは構造上もう一方が存在せず、
一致検証が**原理的にできない**。これを `none` にすると、逆引き手順の欠陥ではなく
**候補の位置だけを理由に失敗が積み上がる**。件数は出力に記録し、
§7.7 の抜き取り確認で優先的に選ぶ。

**`search_exhausted` を `none` とする理由**: その方向に候補は存在するのに 200 件走査して
1件も逆引きできなかった場合、そもそもその近傍の逆引きが信頼できない。
「章の端」と同じ扱いにすると、**逆引きが弱い領域を成功として数えてしまう**。

**探索の打ち切り**: 前方向・後方向とも、対象候補から**最大 200 件**まで走査して見つからなければ
その方向を打ち切る（無限走査を避ける。章内の候補数は最大 1,000 件程度であり、
200 件走査して1件も逆引きできない場合はページ推定の信頼性も低い）。

**キャッシュ**: 同じ章の content_list は1度だけ読み、`norm` 済みのブロック一覧を再利用する
（章ごとに数百〜千ブロック × 60 件の照合となるため）。

### 7.3 出力 TSV の仕様

ヘッダ行（候補 TSV の全列 ＋ 3列）:

```
chapter	line	offset	kind	location	symbol	context	stage	block_index	page_idx	reason
```

**ヘッダは候補 TSV の7列 ＋ 上記4列の計11列**になる。

| 追加列 | 内容 |
|---|---|
| `stage` | `block` / `page` / `none` |
| `block_index` | content_list の配列内の位置（`stage=block` のとき。それ以外は `-1`） |
| `page_idx` | ブロックの `page_idx`（`stage` が `block` または `page` のとき。`none` は `-1`） |
| `reason` | `stage` の根拠。`block_key10` / `block_key30`（1段階目で一意一致したキー長）／`page_both`（前後一致）／`page_head` / `page_tail`（章内候補列の端。もう一方に候補が 0 件）／`page_mismatch`（前後不一致）／`search_exhausted`（候補はあるが打ち切りまでに逆引きできず）／`no_neighbor`（章内候補列に他の候補が無い） |

**`symbol` と `context` は候補 TSV の値をそのまま引き継ぐ**（再サニタイズしない。M1 で済んでいる）。

### 7.4 標準エラーへのサマリ

```
located: block={b} page={p} none={n} total={t}
success rate: {rate}%  (threshold 90%)
none breakdown: page_mismatch={m} search_exhausted={se} no_neighbor={nn}
page breakdown: page_both={pb} page_head={ph} page_tail={pt}
by location: body(block/page/none)={b1}/{p1}/{n1}  footnote={b2}/{p2}/{n2}
```

**書籍本文をサマリに含めない。**

### 7.5 エラーハンドリングと境界条件

| 事象 | 動作 |
|---|---|
| 候補 TSV が存在しない・読めない | 標準エラーへメッセージ、**終了コード 1** |
| `--final-root` の下に章ディレクトリが無い | 同上 |
| content_list が読めない・配列でない | 同上（章単位で握りつぶさない） |
| 出力先が既存で `--overwrite` 未指定 | 同上。**既存ファイルを変更しない** |
| `--sample-size` > 母集団サイズ | 同上 |
| `--sample-size` と `--input-sample` の同時指定・両方省略 | 同上 |
| `--sample-size` 指定時に `--seed` 省略 | 同上 |
| 候補の `offset` が md の長さを超える | **起こらない**（M1 が md から生成した値のため）。万一起きたら終了コード 1 |

**処理時間**（NFR-M2-003）: 章ごとに content_list を1度読み、`norm` 済み文字列を再利用する。
検査標本 60 件に対し、2段階目の探索（最大 200 件 × 2 方向）が最悪ケースで走っても
**10 分以内**に収まる。

### 7.6 出力の原子性

M1 と同じく、**同一ディレクトリの一時ファイルに書き `os.replace` で置換する**
（`../m1-scan-cli/design.md` §5.1）。理由も同じ（書き込み途中の失敗で既存ファイルを壊さない）。
`check_d4_coverage.py` も同様とする。

### 7.7 テスト

**pytest のテストを書かない**（ADR-M2-3）。検証は次の3つで行う。

1. **再現性**: §6.2 の `diff`
2. **予備実測との整合**: 所在別の成功率が `../survey_notes.md` §7.1 の予備実測
   （`body` 91.4% / `footnote` 75.7%）と**桁違いに乖離していないこと**を目視で確認する。
   乖離した場合は原因を特定してから判定に進む（§8.2 の照合）
3. **手作業での抜き取り確認（`requirements.md` FR-M2-003 受け入れ基準2-b）**:
   - **選び方は決定的とする。乱数を使わない。** stage ごとに次の順で並べ、先頭から
     `min(3, その stage の件数)` 件を採る

     | stage | 並べ替えの規則 |
     |---|---|
     | `page` | `reason` の優先順（`page_head` → `page_tail` → `page_both`）→ `chapter` 昇順 → `offset` 昇順 |
     | `block` | `reason` の優先順（`block_key30` → `block_key10`）→ `chapter` 昇順 → `offset` 昇順 |

   - **`stage=block` の確認**: `block_index` の content_list のブロックの `text` に、
     候補の `context` に対応する文字列が含まれることを目視で確認する
   - **`stage=page` の確認**: 推定した `page_idx` を持つ content_list のブロック群
     （`page_idx` が一致する全ブロック）の `text` を連結し、候補の `context` に対応する文字列が
     含まれることを目視で確認する
   - **件数が 0 の stage は「確認対象なし」と記録し、Go の判定に影響させない**
     （例: 60件すべてが `block` で特定できた場合、`page` の確認は行わない）
   - **確認した件のうち1件でも含まれていなければ、逆引きの手順に欠陥があるとみなし、
     成功率が 90% 以上でも Go にしない**（§8.3）
   - **原本 TIF は開かない**（`requirements.md` §1.7 範囲外4）。content_list のテキストだけで確認する
   - **選んだ件の `chapter`・`offset`・`stage`・`reason` と確認結果**を `experiment_log.md` に
     記録する（`requirements.md` FR-M2-003 受け入れ基準2-c）。
     **記録が無い、または記録された件が上表の選択規則の順序と一致しない場合は、
     抜き取り確認を満たしたとみなさない**

---

## 8. 予測と実測の照合（FR-M2-004）

### 8.1 `experiment_log.md` の構成

```markdown
# feat-024 M2 実験ログ

## 検査1: 除外領域の対
### 予測（実行前に記録）
（章ごとの fence / disp の予測値と、偶数であるという予測）
### 実測
（章ごとの実測値）
### 照合
（一致／乖離。乖離した場合の原因）

## 検査2: D4 16件の被覆
（同じ構成。実測には **`covered` / `not_covered` / `heading_not_found` の件数**と、
`not_covered` の**分類別件数**（`no_symbol` / `table_only`）を書く。**書籍本文は書かない**）

## 検査3: 逆引きの成功率
（同じ構成。段階別件数・成功率・所在別の内訳）

## 判定
（Go / No-Go と、その根拠）
```

**書籍本文を書かない**（件数と判定のみ。`requirements.md` §1.5 制約1）。

### 8.2 予測の立て方

**各検査の実行直前に、その検査の予測を数値で書いてから実行する**（`CLAUDE.md` 手順2）。
**3つの検査の予測を一括で先に書かない**——検査1・2 の結果が検査3 の予測に影響するためである。

予測の根拠に使える実測値:

| 検査 | 参照できる実測値 |
|---|---|
| 検査1 | `../survey_notes.md` §3.2（奇数個の `$` を含むブロックは 0 件）。ただし**行頭 `$$` の対の偶奇は未実測** |
| 検査2 | `../survey_notes.md` §1.2（16件の一覧）。**被覆の件数は未実測** |
| 検査3 | `../survey_notes.md` §7.1（1段階目のみの成功率: `body` 91.4% / `footnote` 75.7%）。**2段階目を含めた成功率は未実測** |

### 8.3 判定（FR-M2-005）

検査3 の実測から Go / No-Go を判定し、`experiment_log.md` の「判定」節に記録する。

| 判定 | 条件 | 次の行き先 |
|---|---|---|
| **Go** | 逆引き成功率が **90% 以上**（`none` が 6 件以下）**かつ** §7.7 の抜き取り確認（各 stage について `min(3, 件数)` 件）に**全件合格**（件数 0 の stage は対象外） | **M3 に進む** |
| **No-Go** | 上の条件のいずれかを満たさない | **M3 に進まない。** 「満たさなかった事実」「所在別の内訳」「`none` の内訳（`page_mismatch` / `no_neighbor`）」「抜き取り確認の結果」「逆引き手順の見直し案」を報告し、`../roadmap.md` の改訂に進むかどうかユーザーの判断を仰ぐ |

**合格ラインを事後に変更しない**（`requirements.md` §1.5 制約5）。

---

## 9. 検証（完了判定）

### 9.1 データ不変性の検証（NFR-M2-001）

M1 と同じ手順を用いる。

```bash
B2=/home/sakagawa/work/確率統計
find $B2/dewarping $B2/ocr/final $B2/ocr/fixes $B2/ocr/mineru-full -type f \
  -exec sha256sum {} + | sort -k2 > /tmp/feat024_m2_before.sha256
# …作業…
find $B2/dewarping $B2/ocr/final $B2/ocr/fixes $B2/ocr/mineru-full -type f \
  -exec sha256sum {} + | sort -k2 > /tmp/feat024_m2_after.sha256
diff /tmp/feat024_m2_before.sha256 /tmp/feat024_m2_after.sha256; echo "DIFF_EXIT=$?"
```

**合格条件**: `DIFF_EXIT=0`（無出力）かつ行数が前後で同数（**3,551**）。
出力先の `{BASE2}/ocr/collation/` は上記4ディレクトリに含まれない。

### 9.2 既存テストの非破壊確認

本マイルストーンは `scripts/` 配下を変更しないが、念のため既存テストを実行する。

```bash
uv run pytest -v 2>&1 | tee tests/results/feat-024_test_result.txt
```

**合格条件**: **260 passed**（M1 と同じ）。`tee` は終了コードを隠すため、判定は出力ファイルの
`passed` 行で行う。

### 9.3 完了の判定

`requirements.md` の受け入れ基準に対応する。次のすべてを満たしたとき M2 完了とする。

| # | 判定項目 | 根拠 |
|---|---|---|
| 1 | 検査1 が全10章で合格（`fence` と `disp` がともに偶数） | FR-M2-001 受け入れ基準1・2 |
| 2 | 検査2 の16件すべてについて状態が記録され、**`heading_not_found` が 0 件**であり、`not_covered` の件に**分類（`not_covered_reason`）が付いている**。分類別の件数が `experiment_log.md` に記録されている | FR-M2-002 受け入れ基準1〜3 |
| 3 | 検査3 の段階別件数・成功率・所在別の内訳・`none` の内訳が記録されている | FR-M2-003 受け入れ基準2 |
| 3-b | §7.7 の抜き取り確認（各 stage について `min(3, 件数)` 件）を実施し、結果が記録されている。件数 0 の stage は「対象なし」と記録されている | FR-M2-003 受け入れ基準2-b |
| 3-c | 抜き取り確認で選んだ各件の `chapter`・`offset`・`stage`・`reason` と確認結果が `experiment_log.md` に記録され、**選択規則の順序と一致する**ことが追えるようになっている | FR-M2-003 受け入れ基準2-c |
| 4 | 検査標本の抽出が再現する（`diff` が無出力） | FR-M2-003 受け入れ基準5・NFR-M2-002 |
| 5 | 3つの検査すべてで予測が実行前に記録され、実測と照合されている | FR-M2-004 |
| 6 | Go / No-Go が `experiment_log.md` に明記されている | FR-M2-005 |
| 7 | §9.1 の `DIFF_EXIT=0`（3,551 ファイル） | NFR-M2-001 |
| 8 | §9.2 が 260 passed | — |

**完了条件に「逆引き成功率が 90% 以上であること」を入れない。**
満たさない場合に M2 が完了できず、再計画で挿入するマイルストーンを開始できなくなるためである
（`../roadmap.md` M4 と同じ理由）。**充足の判定は §8.3 の Go / No-Go で扱う。**

---

## 10. 実装フェーズの作業順序

**Sonnet サブエージェントに委任するのは 2〜4 のみ**（スクリプトの実装）。
検査の実施・予測・判定は Claude Code 本体が行う（ADR-M2-4）。

| # | 作業 | 担当 |
|---|---|---|
| 1 | §9.1 の事前 SHA-256 取得 | 本体 |
| 2 | `check_d4_coverage.py` の実装 | **Sonnet** |
| 3 | `locate_candidates.py` の実装 | **Sonnet** |
| 4 | §9.2 の既存テスト実行と結果保存 | **Sonnet** |
| 5 | 検査1 の予測 → 実行 → 照合 | 本体 |
| 6 | 検査2 の予測 → 実行 → 照合 | 本体 |
| 7 | §7.7 の抜き取り確認（各 stage について `min(3, 件数)` 件）。**検査3 の実行後に行う**（`stage` が確定してから選ぶため。作業順は 8 → 9 → 7 → 10） | 本体 |
| 8 | 検査3 の予測 → 実行 → 照合 | 本体 |
| 9 | §6.2 の再現性確認 | 本体 |
| 10 | §8.3 の Go / No-Go 判定 | 本体 |
| 11 | §9.1 の事後 SHA-256 取得と照合 | 本体 |
| 12 | §9.3 の完了判定 | 本体 |

**5・6・8 は予測を `experiment_log.md` に書いてから実行する**（§8.2）。

---

## 11. 中断規則

1. 検査1 が不合格（奇数の章がある）→ **検査2・3 に進まず**、原因を特定して報告する
   （母集団に不正な候補が混入している可能性があり、検査3 の標本も汚染されるため）
2. 検査2 で `heading_not_found` が1件以上 → **検査3 に進まず**、原因を特定して報告する
   （feat-020 の成果〔全74件が見出し行〕という前提が崩れていることを意味するため）
3. `{BASE2}` のファイルに変更が生じた → **即時中断**
4. 設計書どおりに実行できない事象が起きた → その場で回避策を実装せず**中断して報告する**
5. 同じ原因での失敗が2回続いたら、3回目に進まず前提を疑う（`CLAUDE.md`「行き詰まり検出」）

---

## 12. 設計判断の記録（ADR）

### ADR-M2-1: 検査1 にスクリプトを作らない

- **採用**: `grep -c` を使ったシェルのループで実施する（§4.1）
- **却下**: Python スクリプトを書く
- **理由**: 行頭の固定文字列を数えるだけであり、`grep -c '^```'` と `grep -c '^\$\$'` で
  過不足なく実施できる。スクリプトを作ると、そのスクリプト自体の正しさを検証する必要が生じる
  （M1 のようにテストを書く価値がある処理ではない）

### ADR-M2-2: `locate_candidates.py` を M2 のフォルダに置き、M3 から参照する

- **採用**: `m2-population-check/locate_candidates.py` に置く。M3 は `--input-sample` で同じスクリプトを使う
- **却下1**: `scripts/` に置く（プロダクトコードとして扱う）
- **却下2**: M2 と M3 で別々に実装する
- **理由**: `CLAUDE.md`「ドキュメント作成ルール」の判定基準「**その案件が終わった後も使うか**」に
  照らすと、逆引きは**この調査のためだけ**の処理であり（md と content_list の対応付けは
  本案件の母集団設計に強く依存する）、**ジョブスクリプト・実験コード**に当たる。
  一方、M2 と M3 で二重に実装すると、逆引きの規則がずれたときに検査3 の結果が M3 に適用できなくなる。
  **M3 で仕様変更が必要になった場合は、完了済みの M2 のファイルを変更せず
  「ロードマップの改訂（再計画）」に従う**（`CLAUDE.md`「完了済みマイルストーンの記録は変更しない」）

### ADR-M2-3: 本マイルストーンのスクリプトに pytest のテストを書かない

- **採用**: テストを書かず、§7.7 の3つの検証（再現性・予備実測との整合・抜き取り確認）で担保する
- **却下**: M1 と同じように `tests/` にテストを書く
- **理由**: ADR-M2-2 のとおり、本スクリプトは案件固有のジョブスクリプト・実験コードであり、
  `CLAUDE.md` の「テスト」節が対象とする `scripts/` 配下のプロダクトコードではない。
  逆引きの正しさは**実データでの成功率と抜き取り確認**でしか確かめられず
  （合成データのテストでは md と content_list の実際の表記差を再現できない）、
  pytest を書いても検証の実質が増えない

### ADR-M2-4: 検査の実施と判定を Sonnet に委任しない

- **採用**: スクリプトの実装のみ委任し、予測・実行・照合・判定は Claude Code 本体が行う
- **却下**: 検査の実施まで委任する
- **理由**: `CLAUDE.md`「実験・検証の進め方」は**実行直前の予測**と**実測との照合**を求めており、
  これは設計書に手続きとして書ける作業ではない（前段の結果を踏まえた判断を伴う）。
  また §7.7 の抜き取り確認は目視判断である。feat-021 が突合の実施を委任しなかったのと同じ判断である

### ADR-M2-5: 検査標本の乱数シードを M3 と別にする

- **採用**: 検査3 のシードは **20260907**。M3 の標本のシードは M3 の `requirements.md` で別に定める
- **却下**: 同じシードを使い、検査標本を M3 の標本の一部として再利用する
- **理由**: 検査標本は「逆引きが成功するか」を見るために使い、M3 の標本は「原本と突き合わせて
  判定する」ために使う。同じ候補を両方に使うと、**逆引きに成功した候補が標本に多く含まれる偏り**が
  生じうる（検査3 で `none` だった候補を M3 の標本から外したくなる誘惑が生まれる）。
  独立に抽出することで、この偏りを構造的に排除する
