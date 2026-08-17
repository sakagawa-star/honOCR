**高**
[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-004-punct-normalize/design.md:47) / [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-004-punct-normalize/design.md:54): `str.translate` に `dict[str, str]` を渡す設計になっており、このまま実装すると置換されません。Python の `str.translate` は Unicode ordinal ベースの変換表が必要です。FR-001 の中核が動かないため致命的です。

修正提案: `TRANSLATION_TABLE = str.maketrans(REPLACEMENTS)` を設計に明記し、`text.translate(TRANSLATION_TABLE)` とする。もしくは `replace` 連鎖に変更する。

**高**
[criteria.md](/home/sakagawa/git/honOCR/docs/issues/feat-004-punct-normalize/experiments/renorm-quality/criteria.md:15) と [criteria.md](/home/sakagawa/git/honOCR/docs/issues/feat-004-punct-normalize/experiments/renorm-quality/criteria.md:40) が衝突気味です。B′ は feat-003 項目Bと同一規則で「再測定」としている一方、「句読点以外の誤りの新規判定」を除外しています。結果として、正規化後に同一10段落を再読して見つかった非句読点誤りを数えるのか無視するのかが固定されていません。これは Go/No-Go の事後解釈を許します。さらに feat-003 ログでは P5 の `;`→`；` も残存誤りですが、criteria は P9 だけを例示しています。

修正提案: §5 の「句読点以外の誤りの新規判定」を削除し、同一10段落を feat-003 criteria 項目Bの規則で再評価して、残った全誤りを数える、と明記する。事前に固定するなら P1〜P10 ごとの既知残存誤り表を criteria に書き、P5 と P9 も含める。

**中**
[criteria.md](/home/sakagawa/git/honOCR/docs/issues/feat-004-punct-normalize/experiments/renorm-quality/criteria.md:21) / [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-004-punct-normalize/design.md:115): 項目A・Cの引き継ぎ条件である「差分が句読点置換のみ」の確認方法が criteria lock 前に固定されていません。design も「詳細は実装時に experiment_log.md」としており、判定基準の事前定義として弱いです。

修正提案: criteria に機械確認アルゴリズムを明記する。例: 正規化前後をコードポイント列で比較し、各位置について `、→，`、`。→．`、または完全一致のみ許可する。それ以外の差分、長さ差、ファイル欠落があれば A/C 引き継ぎを禁止して中断する。

低重要度の指摘はありません。