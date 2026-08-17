前回指摘4件は解消されています。新たに高はありません。criteria lock 前に直すべき中だけあります。

**高: なし**

**中: 既存/部分出力が混ざる境界条件が未定義**
[requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-003-mineru-trial/requirements.md:54) は「新規出力のみ」としていますが、[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-003-mineru-trial/design.md:50) は `mkdir -p`、[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-003-mineru-trial/design.md:53) は固定の `mineru-trial` を出力先にしています。既存の `mineru-trial` に古い Markdown/JSON や途中生成物がある場合、完了確認や品質判定に混入します。

修正提案: MinerU の出力先を実行ごとの新規ディレクトリにするか、実行前に `mineru-trial` が非空なら中断する。完了確認は今回実行ディレクトリ配下だけを対象にする。

**中: 独立数式の存在確認が行数カウントになっている**
[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-003-mineru-trial/design.md:55) の `grep -c '\$\$' <md>` は `$$` の出現数ではなく、`$$` を含む行数を数えます。`$$ x $$` のように1行で閉じる形式だと、独立数式1個があっても `1` になり失敗します。

修正提案: `grep -o '\$\\$' <md> | wc -l` などでデリミタ出現数を数え、2以上かつ偶数であることを確認する。

**中: 行内数式を除外すると言いつつ本文判定で中身を数える**
[criteria.md](/home/sakagawa/git/honOCR/docs/issues/feat-003-mineru-trial/experiments/trial-quality/criteria.md:24) は行内数式の `$` だけを無視し、数式内容は誤りカウント対象になります。一方で [criteria.md](/home/sakagawa/git/honOCR/docs/issues/feat-003-mineru-trial/experiments/trial-quality/criteria.md:50) は行内数式品質を判定外にしています。PRML本文では行内数式が多いはずなので、Go/No-Go が事後解釈なしに決まりません。

修正提案: 項目Bでは行内数式全体を比較対象から除外する、または行内数式を含む段落をサンプル対象外にする、と明記する。

**低: なし**