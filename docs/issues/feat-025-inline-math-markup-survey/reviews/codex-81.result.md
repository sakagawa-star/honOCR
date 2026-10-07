# codex-81: M3 閾値実験 criteria（Q3 の傾きの規則の追加版）の解消確認（B）

- **日付**: 2026-10-07
- **対象ファイル**: `docs/issues/feat-025-inline-math-markup-survey/m3-pilot-measure/experiments/thresholds/criteria.md`
- **ストリーム名**: `rev-honocr-feat-025`
- **依頼種別**: **B**（解消確認。codex-80 の指摘への対応）
- **直前に `/new` を送ったか**: No
- **ゲート状態**: **実施済み: codex-80.result.md**
- **指摘数**: 高 **0** / 中 **1** / 低 **0**
- **収束判定**: **未収束（次: 全件反映 → B）**
- **トークン実測**: `total_tokens` = 646,447（input 641,570 / cached_input 557,312 / output 4,877 / reasoning 2,115）
- **rollout jsonl**: `/home/sakagawa/.codex/sessions/2026/10/07/rollout-2026-10-07T09-25-22-01a113c0-2606-7750-bf50-0577e99d868c.jsonl`

## レビュー結果（回収した内容）

[AGENTS.md適用]

前回指摘: 解消

§6 の改訂により、再記録先を退避先内の rebuild.jsonl に限定し、照合成功かつ全CLI成功時だけ正式な measurements.jsonl を作るようになりました。失敗・照合不一致時は退避済みの元ファイルを復元し、既存の正式ファイルがあれば何もせず中断します。したがって、前回懸念した不整合な測定ログの残留や、次回実行時のそれを起点とする欠落・重複は解消されています。(criteria.md:578)

新規指摘:

中: 確定・復元とも cp を直接 {OUT}/measurements.jsonl に実行するため、コピー中のI/O失敗で部分ファイルが残る可能性があります。次回は「既に存在する」として中断するものの、正式パスには破損したログが残ります。

修正案: {OUT} 内の一時ファイルへコピーを完了させ、成功後に mv / os.replace で measurements.jsonl に確定してください。コピー失敗時は一時ファイルを削除し、退避元はそのまま残す手順にします。

## 対応（Claude Code 本体）

- 中 1 件を反映（§6 の見直し手順の 6）
  - `cp` の前に、`{OUT}/measurements.jsonl` と `{OUT}/.tmp-measurements.jsonl` がともに無いことを確かめる
  - コピーは `{OUT}/.tmp-measurements.jsonl` に完了させてから、`mv` で `{OUT}/measurements.jsonl` に置き換える
  - `cp` が失敗したら一時ファイルを削除し、退避先の 2 ファイルは残して中断する
- 遷移表（B〔C の後〕・高中 1 件以上）に従い、同じ会話で B を送る
