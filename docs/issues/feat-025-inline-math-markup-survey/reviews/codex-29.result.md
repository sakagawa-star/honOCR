# codex-29: M2 文書の解消確認（B）

- **日付**: 2026-09-10
- **対象ファイル**: `docs/issues/feat-025-inline-math-markup-survey/m2-population/requirements.md`、`docs/issues/feat-025-inline-math-markup-survey/m2-population/design.md`（関連: `../roadmap.md`）
- **ストリーム名**: `rev-honocr-feat-025`
- **依頼種別**: **B**（解消確認。codex-28 の指摘への対応の確認）
- **直前に `/new` を送ったか**: No
- **ゲート状態**: **未実施**（本レビュー単位で全文ゲート C はまだ行っていない）
- **指摘数**: 高 **0** / 中 **0** / 低 **0**
- **収束判定**: **未収束（次: `/new` → C）**（ゲート未実施の B のゼロは収束ではない）
- **トークン実測**: `total_tokens` = 1,514,817（input 1,506,774 / cached_input 1,121,024 / output 8,043 / reasoning 4,810）
- **rollout jsonl**: `/home/sakagawa/.codex/sessions/2026/09/10/rollout-2026-09-10T11-14-17-01a08918-2c3f-7ed1-8d34-a2a7c1c2c493.jsonl`

## レビュー結果（回収した内容）

[AGENTS.md適用]

前回指摘（高）は解消済みです。

- `verify_candidates_jsonl.py` とその要求・設計を削除し、M2 の手段をロードマップどおり M1 の既存 CLI のみに戻しています。
- `N` は CLI の合計件数と `wc -l` の一致で確定するため、新規スクリプトや先行する単体疎通ステージを必要としません。
- ADR-7 に、検証スクリプトを採らない理由とロードマップとの整合が明記されています。

変更による新たな高・中・低の指摘はありません。

## 指摘ごとの解消判定

| codex-28 の指摘 | 判定 |
|---|---|
| 高: 新規の検証スクリプトが、ロードマップで「S1 の CLI」に固定された S2 の手段と衝突する | **解消** |
