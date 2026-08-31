# codex-02 レビュー結果（feat-015・全文ゲート）

- 日付: 2026-08-31
- 対象ファイル:
  - `docs/issues/feat-015-chap02-split-heading/requirements.md`
  - `docs/issues/feat-015-chap02-split-heading/design.md`
- ストリーム名: `rev-honocr-feat-015`
- フェーズ: **全文ゲート**（`/new` で会話をクリアしてから実施。「新しい目」の確保）
- 指摘数: 高 0 / 中 1 / 低 0
- モデル: gpt-5.6-terra medium（`~/.codex/config.toml` の既定）
- トークン実測: セッション累計 `total_tokens` = 207,898（input 205,911 / cached_input 159,232 / output 1,987 / reasoning 1,047）
- rollout jsonl: `~/.codex/sessions/2026/08/31/rollout-2026-08-31T13-24-48-01a05610-122a-7e10-add0-beb776205153.jsonl`
  （`/new` により codex-01 とは別ファイル。上記の値は本ターン終了時点の累計）

## 依頼文

```
docs/REVIEW_CRITERIA.md の基準に従い、以下のドキュメントをレビューせよ: docs/issues/feat-015-chap02-split-heading/requirements.md docs/issues/feat-015-chap02-split-heading/design.md 。本ドキュメントは対話ベースのレビューを経ている。今回は最終ゲートとして、文書全体の整合性（セクション間の矛盾、参照切れ、抜け）を含めて全文を確認して。
```

## 結果

```
[AGENTS.md適用]

## 中

- docs/issues/feat-015-chap02-split-heading/design.md:325 の content_list.json 非変更確認が、
  mtime とサイズの比較だけです。これは docs/issues/feat-015-chap02-split-heading/
  requirements.md:146 の「変更されない」という受け入れ基準を保証しません。
  同サイズの変更は検出できず、mtime も保存・復元可能です。
  修正案: 手順0で対象JSONのSHA-256を記録するか退避コピーを作成し、手順3で sha256sum または
  cmp によりバイト同一性を検証する手順へ変更してください。

上記以外に、要求仕様書・設計書間の矛盾、参照先セクションの不在、実装を妨げる不足は
確認されませんでした。
```

## 対応

指摘（中・1件）を反映した。`design.md` の変更点は次の2箇所。

1. **§6 手順0（事前確認）**: `{NORM}` と `{FINAL}` の `chap02_gray300_content_list.json` の
   SHA-256 を `sha256sum` で記録する手順を追加し、2026-08-31 実測の基準ハッシュ
   `a4ebb69a04863ac89c6b7ef1e2cf737377b20b168f50aa665ad523bf3aff260f` を期待値として明記した
2. **§7 手順3（非影響の確認）**: `content_list.json` の非変更確認を、mtime とサイズの比較から
   **SHA-256 によるバイト同一性検証**へ差し替えた。あわせて「mtime とサイズの比較では
   同サイズの変更や mtime の復元を検出できないため用いない」と理由を明記した

解消確認は codex-03 を参照。
