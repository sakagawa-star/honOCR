# codex-01 レビュー結果（feat-017・初回レビュー）

- 日付: 2026-08-31
- 対象ファイル:
  - `docs/issues/feat-017-nanteiu-misread/requirements.md`
  - `docs/issues/feat-017-nanteiu-misread/design.md`
- ストリーム名: `rev-honocr-feat-017`（ペイン `wH:pE`）
- 依頼種別: **A（初回レビュー）**
- 直前に `/new` を送ったか: **No**（新規起動直後のため会話は空）
- ゲート状態: **未実施**
- 指摘数: 高 0 / 中 2 / 低 0
- 収束判定: **未収束（次: 全件反映 → B〔同じ会話〕）**
- モデル: gpt-5.6-terra medium（`~/.codex/config.toml` の既定）
- rollout jsonl: `~/.codex/sessions/2026/08/31/rollout-2026-08-31T20-20-41-01a0578c-d1dc-7390-8b9f-7e941843061f.jsonl`

## 依頼文

```
docs/REVIEW_CRITERIA.md の基準に従い、以下のドキュメントをレビューせよ: docs/issues/feat-017-nanteiu-misread/requirements.md docs/issues/feat-017-nanteiu-misread/design.md 。
```

## 結果

```
[AGENTS.md適用]

中

- 完了処理と git status の期待値が矛盾しています。requirements.md:20 と design.md:490 は
  docs/CHANGELOG.md の更新を必須としますが、非影響確認の期待変更一覧には含まれていません。
  正しく完了処理を行うと検証が失敗扱いになります。
  修正案: §7 手順3の許可変更一覧へ docs/CHANGELOG.md を追加し、完了処理前後のどちらで
  確認するかも明記してください。

- FR-004 の対象外確認が不十分です。設計は対象外6章の md の SHA-256 のみ確認しますが、
  要求で不変としたリポジトリ外の他5つの fixes ファイルと PRML 成果物は検証しません。
  git status ではこれら管理外データの変更を検出できません。
  修正案: 実装前に {BASE2}/ocr/fixes/chap02/04/05/07/09.json と PRML 対象成果物の
  SHA-256 を記録し、実装後に照合する手順を §7 へ追加してください。

高・低の指摘はありません。
```

## 対応

指摘（中・2件）を全件反映した。

1. **§7 手順3 の許可変更一覧**: 本手順が実装（ステップ6）の時点で行われ、`docs/CHANGELOG.md` の
   更新と `docs/BACKLOG.md` の Closed 化は完了処理（ステップ8）で行うため
   この時点では未変更であることを明記した。許可される変更3件を表にし、完了処理後の状態も併記した
2. **§6 手順A（不変対象マニフェストの記録）を新設**: `git` 管理外の不変対象について
   SHA-256 のマニフェストを実装前に記録し、§7 手順3 で再実行して照合する手順を追加した。
   2026-08-31 実測の基準値も記載した

解消確認は codex-02 を参照。
