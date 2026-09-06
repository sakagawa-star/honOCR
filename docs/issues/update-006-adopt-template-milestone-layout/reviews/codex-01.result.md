# codex-01: update-006 初回レビュー（A）

- 日付: 2026-09-07
- 対象ファイル: `docs/issues/update-006-adopt-template-milestone-layout/README.md`、`docs/issues/update-006-adopt-template-milestone-layout/design.md`
- ストリーム: `rev-honocr-update-006`（ペイン wH:p13。新規起動。`--sandbox read-only --ask-for-approval never`、モデルは `~/.codex/config.toml` の既定 gpt-5.6-terra medium。反映前の `AGENTS.md`〔規定適合確認なし〕で起動）
- 依頼種別: A（初回レビュー）
- 直前に `/new` を送ったか: No（新規起動）
- ゲート状態: 未実施
- 指摘数: 高 1 / 中 0 / 低 0
- 収束判定: 未収束（次: 全件反映 → B、同じ会話）
- トークン実測（rollout jsonl の `total_token_usage` 累積）: input 302,701（うち cached 244,992）/ output 3,652（reasoning 2,136）/ total 306,353
- rollout jsonl: `~/.codex/sessions/2026/09/07/rollout-2026-09-07T02-46-17-01a077d3-fea6-7930-a791-747ffda03ca8.jsonl`

## 依頼文

> 以下のドキュメントをレビューせよ: docs/issues/update-006-adopt-template-milestone-layout/README.md と docs/issues/update-006-adopt-template-milestone-layout/design.md 。レビュー観点は次の3点: (1) 反映計画の自己完結性 (2) 情報の喪失 (3) 変更後のドキュメント間整合性。design.md の変更前テキストは現行の CLAUDE.md・AGENTS.md・docs/BUGFIX_STANDARD.md・docs/PROJECT_KNOWLEDGE.md に一致している必要がある。

## レビュー結果

[AGENTS.md適用]

高: 旧配置の feat-001〜024 を継続する手順が自己矛盾しています。

P6b は旧配置案件について「案件全体でステップ4〜7を繰り返す」としますが、変更後 P2 のステップ4・6 はそれぞれマイルストーンフォルダの作成と roadmap.md／当該マイルストーン文書の読了を必須にしています。旧配置案件にはこれらが存在せず、P6b もレビュー時に不適合としないことしか定めていません。README が明示する進行中の feat-024 は実装以降を旧配置のまま進めるため、直ちに実行不能です。

修正案: P6b に、旧配置案件のステップ4〜7相当の具体的な読み替えを追加してください。少なくとも、直接配置の requirements.md / design.md を更新・レビュー・実装時の必読対象とし、roadmap.md とマイルストーンフォルダを作成・参照しないことを明記する必要があります。P2・P14・P11 の該当表現も、この例外と矛盾しないか確認してください。

なお、design.md の各「変更前」テキストは、現行4ファイルとの照合で一致していました。

## 対応

- 高: P6b の但し書きに「`roadmap.md` とマイルストーンフォルダを作成・参照しない」と、ステップ4〜7 の読み替え（ステップ4: 直下の `requirements.md` / `design.md` の作成・更新〔差し戻し時は `investigation.md`〕、ステップ5: そのレビュー〔旧規定の依頼文、工程はステップ5 扱い、不在を不適合としない、基準書で判定〕、ステップ6: 必読は直下の文書、ステップ7: 差し戻しは BUGFIX_STANDARD §3 の feat の項を ID なしで案件全体に適用）を追加。design.md §1 R3・改訂履歴、README §6.2 を同期。P2・P11・P14 は反映元と同文のまま（例外は但し書きに集約し、AGENTS.md は但し書きを指す）
- 遷移表に従い、同じ会話で解消確認（B）を依頼する（codex-02）
