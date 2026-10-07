# feat-025 M1 実験ログ（ステージ S1）

想定値と外れの幅は `../roadmap.md` §8 の S1 を参照する（本書には再掲も追加もしない）。

## S1: chap01 への抽出 CLI の適用

### 直前予測（2026-09-10 記録。実行前）

`roadmap.md` §8 の S1 の想定値の式に入力値を代入した。

```
予想値 = 式（入力値）
候補件数 = C_chap01 = 98
```

- **式**: `候補件数 = C_chap01`（`roadmap.md` §8 の S1）
- **入力値**: `C_chap01` = 98 — **ロードマップで固定した定数**（`roadmap.md` §3 の P13）。本ステージは最初のステージであり、前のステージの出力は無い
- **予測値**: **98**
- **幅**: **0**（外れとみなす幅は「98 以外のすべて」。`roadmap.md` §8 の S1）

### 実行（2026-09-10）

`design.md` §1.9.2 の手順 3 のコマンドを 1 回実行した。

```
uv run python scripts/extract_math_candidates.py \
  /home/sakagawa/work/確率統計/ocr/final/chap01/chap01_gray300.md \
  -o /home/sakagawa/work/確率統計/ocr/feat-025/m1_chap01_candidates.jsonl
```

標準エラー出力:

```
/home/sakagawa/work/確率統計/ocr/final/chap01/chap01_gray300.md: 98 件
合計: 98 件 → /home/sakagawa/work/確率統計/ocr/feat-025/m1_chap01_candidates.jsonl
```

終了コード: 0

### 実測

- **候補件数（出力 JSONL の行数）**: **98**
- 出力ファイル: `/home/sakagawa/work/確率統計/ocr/feat-025/m1_chap01_candidates.jsonl`

出力の性質（`requirements.md` の受け入れ基準の確認に用いた値）:

| 項目 | 実測 |
|---|---|
| JSON として読み戻せたレコード数 | 98 |
| 章名の種類 | `chap01` のみ |
| `offset` の順序 | 昇順 |
| 候補レコードの成分数 `c_i` の分布 | すべて 88（`roadmap.md` §5 の実測と一致） |

### 照合

| 項目 | 予測値 | 実測値 | 差 |
|---|---|---|---|
| 候補件数 | 98 | 98 | **0** |

幅は 0（`roadmap.md` §8 の S1）であり、差は 0 である。
