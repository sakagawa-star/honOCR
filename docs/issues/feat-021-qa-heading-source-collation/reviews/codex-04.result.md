# codex-04: feat-021 全文ゲート（C）

- **日付**: 2026-09-02
- **対象ファイル**: `docs/issues/feat-021-qa-heading-source-collation/requirements.md`, `docs/issues/feat-021-qa-heading-source-collation/design.md`
- **ストリーム名**: `rev-honocr-feat-021`
- **依頼種別**: C（全文ゲート）
- **直前に `/new` を送ったか**: **Yes**
- **ゲート状態**: 実施済み（本ファイルが当該 C の結果）
- **指摘数**: 高 1 / 中 0 / 低 0
- **収束判定**: 未収束（次: 高1件を反映 → B 解消確認。**2回目の `/new` は送らない**）
- **トークン実測**: total 296,784（input 293,457 / cached 207,360 / output 3,327 / reasoning 2,145）
- **rollout jsonl**: `~/.codex/sessions/2026/09/02/rollout-2026-09-02T17-03-35-01a06125-175d-73b2-a56f-72b9ec68ccf7.jsonl`（`/new` により codex-03 までとは別の rollout になっている）
- **所要時間**: 1分10秒

---

[AGENTS.md適用]

## 高

### 1. FR-001 の再生成手順が `type`・`text_level` を出力・比較していない

`design.md:189` の FR-001 再生成手順は、所在表との「完全一致」を確認するとしていますが、
出力・検証対象に `type` と `text_level` が含まれていません。これらは `requirements.md:77` で
74件ごとに確定すべき必須項目です。現状では表の当該列が変わっても再生成チェックが通り、
FR-001 の受け入れ基準を満たしたと判定できません。

- **修正案**: 再生成スクリプトの行出力に `type`・`text_level` を含め、§4.1 と同じ列構成で
  出力・比較してください。

## 中

なし

## 低

なし

## 総評

上記以外に、要求仕様書・設計書間の重大な矛盾、参照切れ、実装不能となる欠落は確認されませんでした。
