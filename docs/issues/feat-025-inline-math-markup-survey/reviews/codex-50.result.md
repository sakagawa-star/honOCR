# codex-50: M2-1 文書（再実行手順の追記）の全文ゲート（C）

- **日付**: 2026-09-14
- **対象ファイル**: `docs/issues/feat-025-inline-math-markup-survey/m2-1-locate-smoke/requirements.md`、`docs/issues/feat-025-inline-math-markup-survey/m2-1-locate-smoke/design.md`
- **ストリーム名**: `rev-honocr-feat-025`
- **依頼種別**: **C**（全文ゲート。本レビュー単位で 1 回目）
- **直前に `/new` を送ったか**: **Yes**（画面で会話のクリアを確認）
- **ゲート状態**: 本ファイルが当該 C
- **指摘数**: 高 **1** / 中 **0** / 低 **0**
- **収束判定**: **未収束（次: B。2 回目の `/new` はしない）**
- **トークン実測**: `total_tokens` = 488,259（input 485,269 / cached_input 388,864 / output 2,990 / reasoning 1,097）
- **rollout jsonl**: `/home/sakagawa/.codex/sessions/2026/09/14/rollout-2026-09-14T13-21-22-01a09e25-f577-7203-8242-5151d4579efd.jsonl`

## レビュー結果（回収した内容）

[AGENTS.md適用]

**高**

- `design.md` §1.9.2 手順 4 の `crop_blocks.py` コマンドは、原本 TIF を `/home/sakagawa/work/確率統計/ocr/feat-025/dewarping/{chapter}/out` と指定している一方、設計内の入出力定義・`PROJECT_KNOWLEDGE.md`・ロードマップ P6 は `{BASE2}/dewarping/{chapter}/out` と定めています。`ocr/feat-025/` を余計に挟む現在のコマンドでは TIF を見つけられず、PNG 切り出し、目視、判定結果 1 件の出力という M2-1 完了条件を満たせません。
  - **修正案**: 手順 4 の第 2 引数を `/home/sakagawa/work/確率統計/dewarping/{chapter}/out` に修正してください。

再実行の退避手順そのものは、許可リスト検査・衝突検査を完了するまで状態変更を行わず、M2-1 成果物のみを退避し、`--overwrite` を使わない流れとして自己完結しています。ただし上記のパス不整合により、再実行を最後まで判断なしに完遂できません。

## 対応（Claude Code 本体）

**本指摘は事実誤認である。文書を変更しない。**

`design.md` の手順 4 のコマンドブロック（本レビュー時点の 525〜531 行）を原文のまま引用する。

```
   uv run python scripts/crop_blocks.py \
     /home/sakagawa/work/確率統計/ocr/final/{chapter}/{content_list のファイル名} \
     /home/sakagawa/work/確率統計/dewarping/{chapter}/out \
     -o /home/sakagawa/work/確率統計/ocr/feat-025/m2-1-crops \
     --index {block}
```

第 2 引数は `/home/sakagawa/work/確率統計/dewarping/{chapter}/out` であり、`{BASE2}` = `/home/sakagawa/work/確率統計` を展開したものと一致する。`ocr/feat-025/` を挟んでいるのは第 2 引数ではなく、その次の行の `-o`（PNG の出力先 `ocr/feat-025/m2-1-crops`）である。文書内の他の記述（§1.2 の 36 行、§1.2 の 84 行、§1.4.6 の 331 行、§1.6 の 354 行）もすべて `{BASE2}/dewarping/…` で一貫している。

`grep -n dewarping` の結果（本レビュー時点）:

```
36:| **使う（読み取りのみ）** | `{BASE2}/dewarping/chapNN/out/page-*_{1L,2R}.tif` | 原本 TIF（`roadmap.md` P6） |
84:      {BASE2}/dewarping/chapNN/out/               （原本 TIF）
331:- **TIF ディレクトリ**: `{BASE2}/dewarping/{chapter}/out`（`docs/PROJECT_KNOWLEDGE.md`。…）
354:| 入力（原本 TIF） | `{BASE2}/dewarping/{chapter}/out/` | 読み取りのみ |
528:     /home/sakagawa/work/確率統計/dewarping/{chapter}/out \
```

以上より、指摘が述べる「`ocr/feat-025/` を余計に挟む」記述は存在しない。B（解消確認）で事実を示して再判定を求める。
