# feat-025 M2 実験ログ（ステージ S2）

想定値と外れの幅は `../roadmap.md` §8 の S2 を参照する（本書には再掲も追加もしない）。

## S2: 全10章への抽出 CLI の適用

### 直前予測（2026-09-10 記録。実行前）

`roadmap.md` §8 の S2 の想定値の式に入力値を代入した。

```
予想値 = 式（入力値）
N = C_all = 414
```

- **式**: `N = C_all`（`roadmap.md` §8 の S2）
- **入力値**: `C_all` = 414 — **ロードマップで固定した定数**（`roadmap.md` §3 の P14）
- **予測値**: **414**
- **幅**: **0**（外れとみなす幅は「414 以外のすべて」。`roadmap.md` §8 の S2）

実行単位は「全10章を 1 回」の 1 単位であり、本予測はこの 1 実行についてのものである。

### 実行（2026-09-10）

`design.md` §1.9.2 の手順 3 のコマンドを 1 回実行した（`--overwrite` は付けていない）。

```
/usr/bin/time -f "経過時間: %e 秒" \
uv run python scripts/extract_math_candidates.py \
  /home/sakagawa/work/確率統計/ocr/final/chap00/chap00_gray300.md \
  （chap01〜chap08 は同じ形式で省略。全10章を chap00 から chap09 の順に指定） \
  /home/sakagawa/work/確率統計/ocr/final/chap09/chap09_gray300.md \
  -o /home/sakagawa/work/確率統計/ocr/feat-025/m2_all_candidates.jsonl
```

標準エラー出力:

```
/home/sakagawa/work/確率統計/ocr/final/chap00/chap00_gray300.md: 9 件
/home/sakagawa/work/確率統計/ocr/final/chap01/chap01_gray300.md: 98 件
/home/sakagawa/work/確率統計/ocr/final/chap02/chap02_gray300.md: 5 件
/home/sakagawa/work/確率統計/ocr/final/chap03/chap03_gray300.md: 48 件
/home/sakagawa/work/確率統計/ocr/final/chap04/chap04_gray300.md: 51 件
/home/sakagawa/work/確率統計/ocr/final/chap05/chap05_gray300.md: 39 件
/home/sakagawa/work/確率統計/ocr/final/chap06/chap06_gray300.md: 44 件
/home/sakagawa/work/確率統計/ocr/final/chap07/chap07_gray300.md: 8 件
/home/sakagawa/work/確率統計/ocr/final/chap08/chap08_gray300.md: 15 件
/home/sakagawa/work/確率統計/ocr/final/chap09/chap09_gray300.md: 97 件
合計: 414 件 → /home/sakagawa/work/確率統計/ocr/feat-025/m2_all_candidates.jsonl
経過時間: 0.12 秒
```

終了コード: 0

### 実測

`N` の計数（`design.md` §1.4.3 の 2 経路）:

| 経路 | 実測 |
|---|---|
| CLI が標準エラー出力に出した合計 | **414** |
| `wc -l` による出力 JSONL の行数 | **414** |

2 経路が一致したため、**`N` = 414** と確定した。

- 出力ファイル: `/home/sakagawa/work/確率統計/ocr/feat-025/m2_all_candidates.jsonl`（108,215 バイト）
- M1 の出力 `m1_chap01_candidates.jsonl` は変更されていない（別名のため上書きの経路が無い）

記録のみの値（照合の対象にしない。`design.md` §1.9.2 の手順 5）:

| 項目 | 実測 |
|---|---|
| 章別件数（chap00〜chap09 の順） | 9 / 98 / 5 / 48 / 51 / 39 / 44 / 8 / 15 / 97 |
| 経過時間（`requirements.md` NFR-103 の受け入れの確認に用いる値） | **0.12 秒**（60 秒以内） |

### 照合

| 項目 | 予測値 | 実測値 | 差 |
|---|---|---|---|
| `N`（母集団の候補件数） | 414 | 414 | **0** |

幅は 0（`roadmap.md` §8 の S2）であり、差は 0 である。
