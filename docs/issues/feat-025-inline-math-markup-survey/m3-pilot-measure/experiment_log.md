# feat-025 M3 実験ログ（ステージ S3）

本ステージは測るステージであり、想定値を置かない（`../roadmap.md` §8 の S3）。直前予測・照合は行わず、測った値を記録する（`design.md` §1.9.2、`requirements.md` FR-307）。判定規則の閾値は設計値（0.8 / 1.2 / 1.5 / 0.2）のままで未検証である（`design.md` §1.4.4「閾値の検証の状態」。閾値実験の記録は `experiments/thresholds/experiment_log.md`）。

## S3 の実行（2026-10-07。開始 16:39:53）

### 手順 -1: 前回の実行の成果物の退避

- -1.1: `ls -A {BASE2}/ocr/feat-025` の結果は `m1_chap01_candidates.jsonl`・`m2-1-crops`・`m2_1_judged.jsonl`・`m2_1_located.jsonl`・`m2_all_candidates.jsonl`・`m3-thresholds`・`prev`
- -1.2: すべて許可リストに含まれる
- -1.3: 「対象」の 5 つ（`m3_sample_candidates.jsonl`・`m3_located.jsonl`・`m3_judged/`・`m3_judged.jsonl`・`m3-crops/`）はいずれも無い。初回の実行であり、退避は行っていない（`mkdir`・`mv` を実行していない）

（同日 16:24 の実行の試みは、手順 -1.2 で `m3-thresholds` が許可リストに無かったため、`mkdir`・`mv` を行わず中断した。その時点で手順 0 以降は実行していない。経緯は案件 `README.md` の実施記録）

### 手順 0: 全件テスト

`uv run pytest -v` を実行し、出力を `tests/results/feat-025_test_result.txt` に上書き保存した。終了コード 0、`315 passed, 3 warnings`。

### 手順 1: 入力の確認と標本の抽出

- `wc -l {BASE2}/ocr/feat-025/m2_all_candidates.jsonl` = 414
- 抽出コマンド（`design.md` §1.4.1）を 1 回実行した。標本の行番号（昇順）:

```
[3, 11, 22, 67, 74, 78, 107, 110, 122, 134, 159, 169, 191, 192, 203, 247, 267, 279, 282, 285, 296, 316, 333, 336, 342, 371, 377, 386, 388, 396]
```

### 手順 2: 標本の行番号の対応表

（手順 3 の `sed -n` を、本表の記録より先に実行した。記録した行番号と対応は手順 1 の出力のとおりで、`sed -n` の結果〔30 行〕と一致することを確認した）

| 予備標本ファイル内の行番号 | 元ファイルの物理行番号 |
|---|---|
| 1 | 3 |
| 2 | 11 |
| 3 | 22 |
| 4 | 67 |
| 5 | 74 |
| 6 | 78 |
| 7 | 107 |
| 8 | 110 |
| 9 | 122 |
| 10 | 134 |
| 11 | 159 |
| 12 | 169 |
| 13 | 191 |
| 14 | 192 |
| 15 | 203 |
| 16 | 247 |
| 17 | 267 |
| 18 | 279 |
| 19 | 282 |
| 20 | 285 |
| 21 | 296 |
| 22 | 316 |
| 23 | 333 |
| 24 | 336 |
| 25 | 342 |
| 26 | 371 |
| 27 | 377 |
| 28 | 386 |
| 29 | 388 |
| 30 | 396 |

### 手順 3: 予備標本ファイルの作成

`sed -n '3p;11p;…;396p' {BASE2}/ocr/feat-025/m2_all_candidates.jsonl > {BASE2}/ocr/feat-025/m3_sample_candidates.jsonl`（行番号は手順 1 の 30 個）。`wc -l` = 30。元ファイルの 1 行目（M2-1 で判定した候補）は標本に含まれていない。

### 手順 4: 逆引き

```
uv run python scripts/locate_candidates.py {BASE2}/ocr/feat-025/m3_sample_candidates.jsonl \
  --final-dir {BASE2}/ocr/final -o {BASE2}/ocr/feat-025/m3_located.jsonl
```

終了コード 0、経過時間 0.10 秒。標準エラー出力: `処理: 30 件（逆引き成功 26 件 / 失敗 4 件）`。標準出力の内訳 30 行:

```
1 chap00 offset=6371 block=87 page=9 k=40
2 chap01 offset=976 block=20 page=2 k=40
3 chap01 offset=8708 block=100 page=9 k=40
4 chap01 offset=16806 block=196 page=16 k=40
5 chap01 offset=17820 block=208 page=17 k=40
6 chap01 offset=18610 block=215 page=17 k=40
7 chap01 offset=21108 block=248 page=19 k=10
8 chap02 offset=12430 block=168 page=10 k=40
9 chap03 offset=16119 block=212 page=14 k=40
10 chap03 offset=23673 block=307 page=20 k=40
11 chap03 offset=48438 block=None page=None k=None
12 chap04 offset=23613 block=None page=None k=None
13 chap04 offset=50391 block=641 page=43 k=40
14 chap04 offset=50766 block=649 page=44 k=40
15 chap04 offset=62851 block=797 page=51 k=40
16 chap05 offset=60906 block=595 page=30 k=40
17 chap06 offset=20468 block=229 page=15 k=40
18 chap06 offset=30363 block=341 page=22 k=40
19 chap06 offset=31130 block=347 page=22 k=40
20 chap06 offset=31536 block=352 page=22 k=40
21 chap07 offset=3293 block=40 page=2 k=40
22 chap08 offset=57528 block=629 page=39 k=40
23 chap09 offset=4071 block=None page=None k=None
24 chap09 offset=4130 block=None page=None k=None
25 chap09 offset=5168 block=61 page=3 k=40
26 chap09 offset=43482 block=543 page=29 k=40
27 chap09 offset=44171 block=544 page=29 k=40
28 chap09 offset=56742 block=710 page=36 k=40
29 chap09 offset=56780 block=710 page=36 k=40
30 chap09 offset=60320 block=773 page=40 k=40
```

逆引きに失敗した候補: 予備標本ファイル内の行番号 11・12・23・24 の 4 件。

### 手順 5: 切り出し

章ごとに 1 回、`crop_blocks.py` を既定の `--margin`（8.0）で実行した（10 回。いずれも終了コード 0）。`--index` に与えたブロック番号（同じブロックは 1 回だけ）: chap00 [87]、chap01 [20, 100, 196, 208, 215, 248]、chap02 [168]、chap03 [212, 307]、chap04 [641, 649, 797]、chap05 [595]、chap06 [229, 341, 347, 352]、chap07 [40]、chap08 [629]、chap09 [61, 543, 544, 710, 773]。出力 25 枚（逆引きに成功した 26 件の重複なしの `(chapter, ブロック番号)` の組数 25 と一致。行番号 28・29 は chap09 のブロック 710 を共用する）。

候補の元ファイル行番号 → PNG（`{BASE2}/ocr/feat-025/m3-crops/` 配下）:

| 予備標本ファイル内の行番号 | 元ファイルの物理行番号 | PNG |
|---|---|---|
| 1 | 3 | `chap00_gray300_content_list_b87_p9.png` |
| 2 | 11 | `chap01_gray300_content_list_b20_p2.png` |
| 3 | 22 | `chap01_gray300_content_list_b100_p9.png` |
| 4 | 67 | `chap01_gray300_content_list_b196_p16.png` |
| 5 | 74 | `chap01_gray300_content_list_b208_p17.png` |
| 6 | 78 | `chap01_gray300_content_list_b215_p17.png` |
| 7 | 107 | `chap01_gray300_content_list_b248_p19.png` |
| 8 | 110 | `chap02_gray300_content_list_b168_p10.png` |
| 9 | 122 | `chap03_gray300_content_list_b212_p14.png` |
| 10 | 134 | `chap03_gray300_content_list_b307_p20.png` |
| 11 | 159 | 無し（逆引き失敗） |
| 12 | 169 | 無し（逆引き失敗） |
| 13 | 191 | `chap04_gray300_content_list_b641_p43.png` |
| 14 | 192 | `chap04_gray300_content_list_b649_p44.png` |
| 15 | 203 | `chap04_gray300_content_list_b797_p51.png` |
| 16 | 247 | `chap05_gray300_content_list_b595_p30.png` |
| 17 | 267 | `chap06_gray300_content_list_b229_p15.png` |
| 18 | 279 | `chap06_gray300_content_list_b341_p22.png` |
| 19 | 282 | `chap06_gray300_content_list_b347_p22.png` |
| 20 | 285 | `chap06_gray300_content_list_b352_p22.png` |
| 21 | 296 | `chap07_gray300_content_list_b40_p2.png` |
| 22 | 316 | `chap08_gray300_content_list_b629_p39.png` |
| 23 | 333 | 無し（逆引き失敗） |
| 24 | 336 | 無し（逆引き失敗） |
| 25 | 342 | `chap09_gray300_content_list_b61_p3.png` |
| 26 | 371 | `chap09_gray300_content_list_b543_p29.png` |
| 27 | 377 | `chap09_gray300_content_list_b544_p29.png` |
| 28 | 386 | `chap09_gray300_content_list_b710_p36.png` |
| 29 | 388 | `chap09_gray300_content_list_b710_p36.png` |
| 30 | 396 | `chap09_gray300_content_list_b773_p40.png` |

### 手順 6: 目視と判定（途中で中断）

判定を決めたもの（`design.md` §1.4.4 の手順を上から適用）:

| 予備標本ファイル内の行番号 | 判定 | 当てはまった項 | PNG で読めた該当箇所の文字列 | 根拠 |
|---|---|---|---|---|
| 1 | `not_missing` | 4 | `1.7 Ω は裏方` | 基準文字「裏」（`H` = 29 画素・`BL` = y 1008）。Ω の高さ 26 画素（0.897 × `H`）、下端 y 1006（`BL` とのずれ 0.069 × `H`）。立体。3-1〜3-3 の項に当てはまらず、前後（`1.7`・`は`）にも 3-1〜3-3 に当てはまる字形が無い |
| 11 | `undecidable` | 1 | `null`（理由: `PNG なし`） | 逆引き失敗 |
| 12 | `undecidable` | 1 | `null`（理由: `PNG なし`） | 逆引き失敗 |
| 23 | `undecidable` | 1 | `null`（理由: `PNG なし`） | 逆引き失敗 |
| 24 | `undecidable` | 1 | `null`（理由: `PNG なし`） | 逆引き失敗 |

（高さとずれは、PNG の該当範囲で画素値 200 未満の画素を含む行の最小・最大から数えた）

#### 行番号 2 で確認した事実（判定を決めていない）

- PNG `chap01_gray300_content_list_b20_p2.png` の該当箇所は `三つ組 (Ω, 𝓕, P) を確率空間と呼ぶ` と読める。Ω の直前の字形は `(`、直後の字形は `,` であり、その後に筆記体の `𝓕`、`,`、立体の `P`、`)` が和文を挟まずに続く
- `design.md` §1.4.4 の 3-4 は「候補の字形の**直前または直後**（同じ行で、間に和文〔ひらがな・カタカナ・漢字〕を挟まない位置）に、3-1〜3-3 のいずれかに当てはまる字形があり……」と定める。「直前または直後」が**隣の 1 字形**だけを指すのか、括弧書きのとおり**和文を挟まない範囲のすべての字形**を指すのかによって、本件の 3-4 の当てはまりが変わる（隣の 1 字形は `(` と `,` で 3-1〜3-3 に当てはまらない。和文を挟まない範囲には `𝓕` がある）
- `design.md` にこの区別の定めが無いため、行番号 2 の判定を決めず、手順 6 を中断してユーザーに報告した（2026-10-07）。行番号 3〜10・13〜22・25〜30 は判定していない。手順 7 以降は実行していない
