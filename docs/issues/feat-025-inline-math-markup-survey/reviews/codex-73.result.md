# codex-73: M3 閾値実験 criteria（出力先の親ディレクトリの規定の追加版）の解消確認（B）

- **日付**: 2026-10-06
- **対象ファイル**: `docs/issues/feat-025-inline-math-markup-survey/m3-pilot-measure/experiments/thresholds/criteria.md`（関連: 同フォルダの `extract_samples.py`・`measure_glyphs.py`）
- **ストリーム名**: `rev-honocr-feat-025`
- **依頼種別**: **B**（解消確認。codex-72 の指摘への対応の確認）
- **直前に `/new` を送ったか**: No
- **ゲート状態**: **未実施**
- **指摘数**: 高 **0** / 中 **0** / 低 **0**
- **収束判定**: **未収束（次: `/new` → C）**
- **トークン実測**: `total_tokens` = 1,448,963（input 1,440,279 / cached_input 1,302,528 / output 8,684 / reasoning 4,498）
- **rollout jsonl**: `/home/sakagawa/.codex/sessions/2026/10/06/rollout-2026-10-06T16-09-04-01a1100b-6620-7b33-8408-44523851d07e.jsonl`

## レビュー結果（要旨）

前回の指摘はすべて解消。`--log` の親は `append_jsonl` が作成し失敗時は運用エラー、`locate` の `--crops-dir` の親と `annotate` の `--out-dir` も作成失敗を運用エラーに変換している。§3.6.1 の 4 分類と各実装の対象が一致し、`locate` の段 a〜c・既存出力の拒否・後片付けの規定とも矛盾しない。`extract_samples.py --selftest` は終了コード 0。高・中の新規問題は無い。
