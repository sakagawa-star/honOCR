# codex-85: M3 design.md（手順 -1.2 の許可リストへの m3-thresholds/ の追加）の初回レビュー（A）

- **日付**: 2026-10-07
- **対象ファイル**: `docs/issues/feat-025-inline-math-markup-survey/m3-pilot-measure/requirements.md`・`design.md`（関連: `../roadmap.md`）
- **ストリーム名**: `rev-honocr-feat-025`
- **依頼種別**: **A**（初回レビュー。人レビュー通過後の改版のため**新しいレビュー単位**）
- **直前に `/new` を送ったか**: No
- **ゲート状態**: **未実施**
- **指摘数**: 高 **0** / 中 **0** / 低 **0**
- **収束判定**: **未収束（次: `/new` → C）**
- **トークン実測**: `total_tokens` = 1,082,283（input 1,078,166 / cached_input 815,872 / output 4,117 / reasoning 1,461）。codex-84 と同じ会話の累積値
- **rollout jsonl**: `/home/sakagawa/.codex/sessions/2026/10/07/rollout-2026-10-07T10-16-03-01a113ee-8ca7-7cd3-a2fd-17170fc0eefd.jsonl`

## レビュー結果（回収した内容）

[AGENTS.md適用]

指摘事項なし（高・中・低すべて 0 件）です。

- m3-thresholds/ は criteria.md §3.6.1 の {OUT} と一致し、S3の退避対象外として許可リストに明記されています。
- 手順 -1.3〜-1.5 の退避対象は従来どおり M3/S3 の5成果物だけで、m3-thresholds/ を移動・削除しません。C-305とも整合しています。
- m3-thresholds/ だけが存在する初回再開時は、-1.3 により退避せず手順0へ進めます。
- 判定規則の閾値・項の順序は変更されておらず、ロードマップのM3目的・完了条件とも整合しています。

## 対応（Claude Code 本体）

高・中ゼロ。遷移表（A・高中ゼロ）に従い `/new` → C へ進む。
