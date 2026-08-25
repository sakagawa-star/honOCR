**レビュー結果**

致命的でない表記ゆれ・軽微な曖昧さは省略した。

**高**

1. `table` アンカー仕様が feat-008 後の Markdown と矛盾しており、表がページ末尾アンカーになるケースで脚注位置を誤る可能性がある。

[requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-009-insert-footnotes/requirements.md:58) と [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-009-insert-footnotes/design.md:75) は `table` ブロックの検索文字列を `img_path` としている。さらに [requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-009-insert-footnotes/requirements.md:83) は HTML 表変換の直後に脚注挿入するとしているが、feat-008 では Markdown 中の表は HTML `<table>` から GFM パイプテーブルへ変換済みで、content_list 側の `table_body` は無改変のまま残る設計になっている（[feat-008 README](/home/sakagawa/git/honOCR/docs/issues/feat-008-html-table-to-md/README.md:8), [feat-008 README](/home/sakagawa/git/honOCR/docs/issues/feat-008-html-table-to-md/README.md:17)）。

このため [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-009-insert-footnotes/design.md:166) の「table ブロックのアンカーは `img_path` を使い、md の `![](images/…)` 行は表変換で変化しない」という前提が成立しない。表がそのページの最後の検出可能ブロックなら、アンカー未発見または表より前への挿入になり得る。

修正提案:
- 脚注挿入を HTML 表変換より前に移すなら、FR-006 と設計 §5.2 を更新し、`table` の needle を `table_body` にする。
- HTML 表変換後に実行する方針を維持するなら、`table_body` から feat-008 と同じ変換規則で GFM パイプテーブル文字列を生成して検索する、または `table_body` / 変換後パイプテーブル / `img_path` の優先順を明記する。
- テストに「変換済みパイプテーブルがページ最後のアンカーになるケース」を追加する。現状の [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-009-insert-footnotes/design.md:243) は画像アンカーのみで、table アンカーを検証していない。

**中**

1. スキップ時の stderr 契約が要求内で矛盾している。

[requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-009-insert-footnotes/requirements.md:36) は「スキップ発生時は標準エラーに 1 件 1 行の警告」としている一方、[requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-009-insert-footnotes/requirements.md:69) は冪等性スキップでは警告を出さないとしている。設計側も no-anchor は警告、既挿入は警告なしとしており（[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-009-insert-footnotes/design.md:201), [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-009-insert-footnotes/design.md:202)）、FR-001 の総称的な記述だけが矛盾している。

修正提案:
- FR-001 を「警告対象スキップは標準エラーに出す。既挿入による冪等性スキップは警告しない」に修正する。
- chap01 再実行時の stderr 期待値も明記する。例: 14 件は既挿入で無警告、page_idx 83 の 1 件は no-anchor 警告あり、など。

**低**

なし。
---

## Claude Code の対応方針（2026-08-25）

- メタ: 対象 = requirements.md / design.md（初回）。session id: 01a036ae-2954-7072-9d19-08b784ca14bb
- **高1（table アンカー）**: 採用。実データで裏取りし（final/chap01 の表 2 件: 変換後 md では `img_path`・`table_body` とも不一致、`convert_table` 再生成のパイプテーブル文字列のみ一致）、table の検索文字列を「(a) `table_body` → (b) `convert_table` 再生成文字列 → (c) `img_path`」の 3 候補優先順に変更。FR-003・design §2/§3/§4.3/§5.2 を更新し、テストケース 9b/9c（未変換・変換後の表アンカー）を追加
- **中1（stderr 契約の矛盾）**: 採用。FR-001 を「アンカー未発見スキップのみ警告、冪等性スキップは警告なし」に修正し、FR-004 に再実行時の期待値（0 inserted / 15 skipped、警告は page_idx 83 の 1 行のみ）を明記
