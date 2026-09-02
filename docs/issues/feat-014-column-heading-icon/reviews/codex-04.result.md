# codex-04 レビュー結果（feat-014）

| 項目 | 内容 |
|---|---|
| 日付 | 2026-09-02 |
| 対象ファイル | `docs/issues/feat-014-column-heading-icon/requirements.md`<br>`docs/issues/feat-014-column-heading-icon/design.md` |
| ストリーム名 | `rev-honocr-feat-014` |
| 依頼種別 | **C: 全文ゲート** |
| 直前に `/new` を送ったか | **Yes** |
| ゲート状態 | **実施済み**（本ファイルが当該 C の結果） |
| 指摘数 | 高 1 / 中 0 / 低 0 |
| 収束判定 | **未収束（次: 全件反映 → B: 解消確認。2回目の `/new` はしない）** |
| トークン実測 | `total_tokens = 322976`（input 319914 / cached_input 257280 / output 3062 / reasoning 1768）※`/new` 後の新セッションの累積 |
| rollout jsonl | `~/.codex/sessions/2026/09/02/rollout-2026-09-02T11-28-36-01a05ff2-6741-7550-abc5-5df20f882e27.jsonl` |

## 依頼文

> docs/REVIEW_CRITERIA.md の基準に従い、以下のドキュメントをレビューせよ:
> docs/issues/feat-014-column-heading-icon/requirements.md,
> docs/issues/feat-014-column-heading-icon/design.md 。
> 本ドキュメントは対話ベースのレビューを経ている。今回は最終ゲートとして、
> 文書全体の整合性（セクション間の矛盾、参照切れ、抜け）を含めて全文を確認して。

## 回答（冒頭マーカー `[AGENTS.md適用]` あり）

### 高

- `apply_fixes.py` が終了コード 0 でも `applied` / `skipped` が期待値と違った場合、
  設計は中断のみで復元しません（`design.md:876`）。この時点で NORM の md は更新済み、
  FINAL は更新前のままになり、次回は事前確認のバイト同一条件で停止します。
  これは「章で失敗したら NORM と FINAL を修正前へ復元する」という要求
  （`requirements.md:261`）と矛盾します。

  **修正案**: `applied` / `skipped` 不一致も手順3 の失敗と同じ復元対象として明記し、
  NORM を退避 md から戻し、FINAL とのバイト同一性を確認して中断する手順を追加してください。

### 中

なし。

### 低

なし。

上記以外に、高・中の整合性問題、参照切れ、必須条件の欠落は見つかりませんでした。

## 反映（Claude Code 本体が実施）

| 箇所 | 対応 |
|---|---|
| `design.md` §6.6 | 「終了コードが 0 でも `applied` / `skipped` が §5.2 と異なる場合の復元」を新設。退避 md からの `{NORM_NN}` の復元 → `{FINAL_NN}` とのバイト同一確認（`cmp` → `NORM_FINAL_IDENTICAL`）→ 文字数・行数・`img ref lines` が §6.4 の修正前の値に戻ったことの確認 → 報告して中断、の5ステップを明記。`{FINAL_NN}` は手順3 未実行のため復元不要であること、修正定義ファイルは戻さないことも明記した |
| `design.md` §9 の表 | 該当行を「**中断して報告**（終了コードが 0 でも中断する）」から「§6.6 の復元を実施したうえで中断して報告」に変更。あわせて終了コード 1 の行の「§6.7 の復元は不要」を「復元は不要」に改めた（参照先が §6.7 だけではなくなったため） |
