# codex-80: M3 閾値実験 criteria（Q3 の傾きの規則の追加版）の全文ゲート（C）

- **日付**: 2026-10-07
- **対象ファイル**: `docs/issues/feat-025-inline-math-markup-survey/m3-pilot-measure/experiments/thresholds/criteria.md`（関連: 同フォルダの `experiment_log.md`・`measure_glyphs.py`）
- **ストリーム名**: `rev-honocr-feat-025`
- **依頼種別**: **C**（全文ゲート）
- **直前に `/new` を送ったか**: Yes
- **ゲート状態**: **実施済み: codex-80.result.md**（本回）
- **指摘数**: 高 **0** / 中 **1** / 低 **0**
- **収束判定**: **未収束（次: 全件反映 → B）**
- **トークン実測**: `total_tokens` = 481,164（input 477,384 / cached_input 409,344 / output 3,780 / reasoning 1,599）
- **rollout jsonl**: `/home/sakagawa/.codex/sessions/2026/10/07/rollout-2026-10-07T09-25-22-01a113c0-2606-7750-bf50-0577e99d868c.jsonl`

## レビュー結果（回収した内容）

[AGENTS.md適用]

中: §6 のG2行見直しは、照合失敗時に新しい measurements.jsonl を退避・復元する手順がありません。照合は再記録後なので、欠落・重複・値の変化を検出しても、作業中のファイルは不整合なまま残ります。さらに中断後に同手順を再実行すると、その不整合ファイルを新たな退避元として再記録しかねません。

修正案: 再記録先を一時ファイルに作成し、元ファイルとの行順・行数・全キー（italic 以外、r/d は 1e-9）の照合が成功した場合だけ mv で正式な measurements.jsonl にする。失敗時は元の退避ファイルを復元し、一時ファイルは別名退避または削除する手順を明記してください。

その他は問題ありません。§3.4.1 は全対象で上下帯が空にならず、D > 2 / D < -2 / -2 ≤ D ≤ 2 が排反かつ網羅的で、実装も Fraction による同じ規則を適用しています。--italic の3値、再計算一致検査、既存 (kind, sample_id) の重複拒否も criteria と一致します。事後解釈を許す記述も見当たりません。

なお、この環境では uv のキャッシュが読み取り専用で、かつ python が未導入のため、自己検査の実行はできませんでした。

## 対応（Claude Code 本体）

- 中 1 件を反映: §6 の見直し手順の 2〜6 を改めた
  - 2: `{OUT}/measurements.jsonl` が無ければ中断する
  - 3: 退避先は `{退避先}/measurements.jsonl`
  - 4: 書き直し先を一時の記録 `{退避先}/rebuild.jsonl` にした（`--log` に与える）
  - 6（新設）: 照合と全コマンドの終了コード 0（G2 の 1 回目の `--italic 判定不能` の引数の誤りを除く）が成り立てば `rebuild.jsonl` を `cp` で `{OUT}/measurements.jsonl` に確定する。成り立たなければ退避した元の記録を `cp` で戻して中断する。`cp` の前に `{OUT}/measurements.jsonl` が無いことを確かめる。退避先の 2 ファイルは残す
- 旧 6・7 を 7・8 に繰り下げた。遷移表（C・高中 1 件以上）に従い、同じ会話で B を送る
