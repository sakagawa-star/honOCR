再レビュー結果: この修正で `html` 名の衝突は解消されています。

確認点:
- §4.1 は [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-008-html-table-to-md/design.md:71) で `convert_table(table_html: str)` になっており、処理手順も [table_html を参照](/home/sakagawa/git/honOCR/docs/issues/feat-008-html-table-to-md/design.md:73) しています。
- `html.unescape(...)` は [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-008-html-table-to-md/design.md:77) に残っており、関数引数 `html` による隠蔽はなくなっています。
- §7 のインターフェース定義も [convert_table(table_html: str)](/home/sakagawa/git/honOCR/docs/issues/feat-008-html-table-to-md/design.md:218) で一致しています。
- `argparse`, `re`, `html`, `sys`, `subprocess`, `pathlib` を隠す同種のローカル名・引数名・同名ローカルファイルは検出しませんでした。

**重要度別**
- 高: なし
- 中: なし
- 低: なし

修正提案はありません。今回の観点では実装再開して問題ありません。