# update-001: 開発ドキュメントテンプレート改訂の取り込み

## ステータス

Closed（2026-08-31 完了）

## 概要

本リポジトリの開発プロセスドキュメントは、テンプレートリポジトリ `/home/sakagawa/git/DEV_TEMPLATE`（`template/` ディレクトリ）から構築されている。テンプレートが 2026-08-27 に更新されたため、その改訂を本リポジトリへ取り込む。

- **反映元**: `/home/sakagawa/git/DEV_TEMPLATE/template/`
- **取り込み済みの状態**: コミット `3e62a11`（2026-08-03）。本リポジトリの基準書5点（BUGFIX_STANDARD.md / DESIGN_STANDARD.md / REQUIREMENTS_STANDARD.md / REVIEW_CRITERIA.md / codex-exec-ubuntu24-bwrap-fix.md）が `3e62a11` 時点のテンプレートと**バイト同一**であることを `diff` で確認済み（2026-08-31）
- **反映対象**: `3e62a11..19e4977` の4コミット（すべて 2026-08-27）

| コミット | テンプレート側案件 | 内容 |
|---|---|---|
| `8d5aac9` | update-005 | BACKLOG にステータス凡例（Review / On Hold / Cancelled を含む6種）を追加 |
| `7039b4c` | update-006 | `AGENTS.md` 新設 — Codex が起動時に読むレビュー定型指示（瑣末指摘の抑止・重要度分類・修正提案・「[AGENTS.md適用]」マーカー） |
| `f242897` | update-004 | Codex レビューを `codex exec` バックグラウンド方式から **Herdr 対話方式**へ全面移行。`docs/HERDR_SETUP.md`（179行）新設 |
| `19e4977` | update-007 | 移行後の読み替え不足の整合（委任しない作業・Bash ルール例・reviews/ 説明）と `.gitignore` から full.log 行の削除 |

## 差分の全量（`git -C /home/sakagawa/git/DEV_TEMPLATE diff 3e62a11..19e4977 -- template/`）

変更ファイルは5点。stat: `.gitignore` -3行 / `AGENTS.md` +11行（新規）/ `CLAUDE.md` +121/-50行 / `docs/BACKLOG.md` +11/-1行 / `docs/HERDR_SETUP.md` +179行（新規）。

### template/AGENTS.md（新規・11行）

Codex CLI が起動時に自動で読む指示ファイル。レビュー依頼時の定型指示（瑣末な指摘をしない・重要度(高/中/低)分類・修正提案・回答冒頭の「[AGENTS.md適用]」マーカー）を永続化する。

### template/docs/HERDR_SETUP.md（新規・179行）

Herdr によるエージェント連携（Claude Code → codex レビュー依頼）のセットアップ手順。前提条件・Herdr インストール・Claude Code 連携フック・Herdr スキル導入・動作確認・注意点・内部コマンド・アンインストール・出典。

### template/CLAUDE.md

1. ディレクトリ構成図に `AGENTS.md` と `docs/HERDR_SETUP.md` を追加
2. ドキュメント更新フロー ステップ4 の文言を「「Codexによるレビューの実行方法（Herdr 対話方式）」に従う（重要度「高・中」ゼロ収束後に人レビュー）」に変更（旧: バックグラウンド実行・`-o` + full.log 分離・`resume` 逐次再レビューの列挙）
3. 案件ディレクトリ構成の `reviews/` 説明を「codex-NN.result.md。git 管理」に変更（full.log への言及を削除）
4. 「Codexによるレビューの実行方法」節を「（Herdr 対話方式）」へ**全面差し替え**。旧内容（`codex exec` バックグラウンド実行・`-o`/full.log 分離・`resume` 再レビュー・コマンド例4種）を削除し、新内容は: 前提環境（Herdr + codex CLI、フォールバックなし）／モデル設定（`~/.codex/config.toml`、AGENTS.md は起動時のみ読込）／レビューストリーム（命名 `rev-{略称}-{案件ID}`、排他規則）／エージェントのライフサイクル（生存確認・起動・画面確認・終了）／依頼の送り方（`herdr agent prompt --wait --timeout 1800000` を `run_in_background`、「[AGENTS.md適用]」マーカー検証）／レビューの進め方（全件まとめて反映 → 解消確認 → `/new` による全文ゲート → 収束）／依頼文の基準部分（一括型、定型指示は AGENTS.md が供給）／結果の保存（result.md のみ、冒頭メタにトークン実測、full.log 廃止）／サブエージェントへの委任（並列レビュー時）。bwrap 対策の注記は節末尾に維持
5. 「実装の実行方法（Sonnetサブエージェント）」の「委任しない作業」を「Codexレビューの指摘反映と収束判定…（レビューの定型作業の委任は「Codexによるレビューの実行方法（Herdr 対話方式）」の規定に従う）」に変更
6. 「Claude Code 運用ルール」に「行き詰まり検出（全作業共通・必須）」節を**新設**（同じ指摘の再発・同じ原因での失敗が2回続いたら前提に立ち返る。3回目の試行禁止）
7. 「Bash 実行時のルール」の allowlist 例を `Bash(codex exec *)` → `Bash(herdr *)` に変更

なお、機能追加/不具合修正フローのステップ4、および「実験・検証の進め方」ステップ1の参照文言「Codexによるレビューの実行方法」は、テンプレート側でも旧名のまま維持されている（節名にはサフィックスが付いたが参照は変更されていない）。本リポジトリもテンプレートに合わせて無変更とする。

### template/docs/BACKLOG.md

サンプル（HTMLコメント内）の「ステータス: Open / In Progress / Closed」を「ステータス凡例」節への参照に変更し、ファイル末尾に「ステータス凡例」節を追加: **Open**（起票済み・未着手）/ **In Progress**（調査・実装中）/ **Review**（レビュー中）/ **On Hold**（一時中止。備考に日付・理由・再開点を記録、案件 README も更新）/ **Closed**（完了）/ **Cancelled**（取りやめ・破棄。ドキュメントは履歴として残す）。

### template/.gitignore

`docs/issues/*/reviews/*.full.log` の ignore 行（コメント行含む2行）を削除。新方式では full.log を作らないため。

## 取り込む / 取り込まない の選別

**全量を取り込む。** 除外なし。理由と本リポジトリ固有の適用調整は以下のとおり。

| 項目 | 判断 | 理由・調整 |
|---|---|---|
| AGENTS.md 新設 | 取り込む | テンプレートからそのまま複製（プレースホルダなし） |
| docs/HERDR_SETUP.md 新設 | 取り込む | テンプレートからそのまま複製（プレースホルダなし） |
| CLAUDE.md の変更 1〜7 | 取り込む | 本リポジトリの CLAUDE.md はプロジェクト固有セクション（プロジェクト概要・データ・ドメイン知識・git 操作の Opus 委任等）を多く含むため、**セクション単位でマージ**する（固有セクションは無改変）。レビューストリーム命名の `{{プロジェクト略称}}` プレースホルダは **`honocr`** で実体化する（ユーザー決定） |
| BACKLOG ステータス凡例 | 取り込む | 本リポジトリの BACKLOG は実体化済み（サンプルの HTML コメントなし）のため、末尾に凡例節を追加するのみ。既存案件のステータス値（Open / In Progress / Closed）は凡例と整合しており変更不要 |
| .gitignore の full.log 行削除 | 取り込む | ローカルに残る過去の full.log **55件は削除する**（ユーザー決定。ignore 行を消すと未追跡ファイルとして表示され続けるため）。各レビューの結論は result.md に保存済みだが、full.log にのみある過程情報（依頼文・session id・使用モデル/reasoning effort・調査過程）は**削除で失われる**。完了済み案件の監査用情報であり、意図的な破棄として許容する（詳細は design.md §6） |

## 環境確認結果（2026-08-31）

Herdr 対話方式の前提環境は本マシンで**すべて導入済み**。追加セットアップ不要。

- 本 Claude Code セッション自体が `HERDR_ENV=1` の Herdr 管理ペインで稼働中
- `herdr`・`codex` CLI とも導入済み（`~/.local/bin/`）
- Herdr スキル導入済み（`~/.claude/skills/herdr/SKILL.md`）
- SessionStart フック導入済み（`~/.claude/settings.json` に herdr エントリ1件）

その他の確認事項:

- 基準書5点はテンプレート最新（`19e4977`）とも同一のため変更不要
- ルート `README.md` にはレビュー方式への言及がなく影響なし（`codex exec` / `full.log` の grep 0件）
- `.claude/settings.local.json` に codex / herdr 関連の許可エントリなし（allowlist の書き換え不要）

## ユーザー決定事項（2026-08-31）

1. レビューストリームのプロジェクト略称は **`honocr`**（例: `rev-honocr-update-001`）
2. 既存 full.log（起票時点の実測 55件）は**削除**する
3. 本案件のレビュー自体を**新方式（Herdr 対話方式）で実施**する。その前提として `AGENTS.md` のみレビュー開始前に先行配置する（反映本体はレビュー収束後）

## 実施ステップ（ドキュメント更新フロー準拠）

1. 案件作成（本フォルダ + BACKLOG 追記）— 完了
2. 調査（本 README.md）— 完了
3. 設計・保存（design.md）
4. Codex レビュー（Herdr 対話方式、ストリーム名 `rev-honocr-update-001`。高・中ゼロ収束 → 全文ゲート → 人レビュー）
5. 反映（design.md に厳密に従う。実施は Claude Code 本体）
6. 完了処理（BACKLOG / CHANGELOG / 本 README のステータス更新）
7. テスト: コード変更がないため不要（design.md に明記）
