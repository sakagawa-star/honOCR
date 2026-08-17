前回指摘は解消済みです。

- 既存/部分出力混入: [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-003-mineru-trial/design.md:51) で実行ごとの `run-NN/` 新規ディレクトリに固定され、[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-003-mineru-trial/design.md:56) で確認対象も `run-NN/` 配下に限定されています。
- `grep -c` 問題: [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-003-mineru-trial/design.md:56) で `grep -o ... | wc -l` に修正されています。
- 行内数式の扱い: [criteria.md](/home/sakagawa/git/honOCR/docs/issues/feat-003-mineru-trial/experiments/trial-quality/criteria.md:24) で行内数式全体を誤りカウント対象外にし、存在だけ確認する形に修正されています。

**高: なし**

**中: なし**

**低: なし**

criteria lock を阻む致命的な問題は見つかりませんでした。