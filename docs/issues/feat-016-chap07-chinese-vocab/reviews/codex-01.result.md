致命的な指摘は以下です。

## 高

- 要求仕様と設計で、リポジトリ内の `tests/` を変更しないという制約に矛盾があります。  
  [requirements.md:12-14](/home/sakagawa/git/honOCR/docs/issues/feat-016-chap07-chinese-vocab/requirements.md:12) は成果物をリポジトリ外の修正定義と既存成果物の更新だけに限定していますが、[design.md:184](/home/sakagawa/git/honOCR/docs/issues/feat-016-chap07-chinese-vocab/design.md:184) および [design.md:223](/home/sakagawa/git/honOCR/docs/issues/feat-016-chap07-chinese-vocab/design.md:223) は `tests/results/feat-016_test_result.txt` の新規作成を必須にしています。さらに [design.md:169](/home/sakagawa/git/honOCR/docs/issues/feat-016-chap07-chinese-vocab/design.md:169) の `git status` の期待値とも両立しません。  
  修正提案: 「テストコードは変更しないが、検証記録として `tests/results/feat-016_test_result.txt` は新規作成する」と要件・影響範囲・`git status` の期待値を統一してください。リポジトリ変更を完全禁止する意図なら、テスト結果の保存要件を削除してください。

## 中

- 件数検証に `grep -c` を使っていますが、これは文字列の出現回数ではなく「マッチした行数」です。  
  [requirements.md:83](/home/sakagawa/git/honOCR/docs/issues/feat-016-chap07-chinese-vocab/requirements.md:83) は「上の一様分布」が17件であることを受け入れ基準にしている一方、[design.md:149](/home/sakagawa/git/honOCR/docs/issues/feat-016-chap07-chinese-vocab/design.md:149) のコマンドでは同一行に複数出現しても1件として数えます。`apply_fixes.py` は `str.count()` による出現回数で不変条件を検証するため、検証の意味も一致しません。  
  修正提案: `rg -o -F '上の一様分布' {NORM}/chap07_gray300.md | wc -l`、または Python の `text.count(...)` を用い、`old`／`new` を含むすべての件数確認を「出現回数」に統一してください。

低重要度の指摘は、依頼どおり省略します。