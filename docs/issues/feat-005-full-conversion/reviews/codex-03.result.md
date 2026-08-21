> メタ: 2026-08-18 / 対象: feat-005 README.md・requirements.md・design.md（スコープ拡大版: chap-00〜04）/ session id: 01a00fac-c16b-7182-94cc-650c2404887d / 再レビュー（3回目）
> 対応: 高1件（partial final の矛盾 → 全5章必須に一本化）・中1件（chap01/out 枚数 87→84 修正と閉包の明記）とも対応済み。codex-04 で解消を確認

**指摘**

- **高**: partial final を許すのか、全5章 final を完了条件にするのかが矛盾しています。  
  [requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-005-full-conversion/requirements.md:70) と [requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-005-full-conversion/requirements.md:72) は final を全5章必須にしています。一方、[requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-005-full-conversion/requirements.md:102) は中断章があっても合格済み章を final に集約してよいとしています。設計側も [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-005-full-conversion/design.md:112) / [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-005-full-conversion/design.md:123) では全5章を作成・検証する一方、[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-005-full-conversion/design.md:131) では中断章のディレクトリを作らないとしています。これだと中断時に FR-004 が合格なのか不合格なのか判断できません。  
  **修正提案**: 完了条件を一つに固定してください。推奨は「feat-005 の完了 final は全5章必須。中断時は final を構築せず、合格済み章は run-NN-normalized までの中間成果物として残す」です。partial final を許すなら、FR-004 の出力・受け入れ基準を「成功章のみ + manifest に成功/中断章を明記」に全面変更し、「全5章の章単位 Markdown 確定」とは別の状態として扱う必要があります。

- **中**: README の chap01/out 枚数が章対応表・実データと一致していません。  
  [README.md](/home/sakagawa/git/honOCR/docs/issues/feat-005-full-conversion/README.md:30) は chap01/out を 87枚としていますが、章対応表は chap-00 17枚 + chap-01 64枚 + 除外3枚 = 84枚です（[README.md](/home/sakagawa/git/honOCR/docs/issues/feat-005-full-conversion/README.md:42), [README.md](/home/sakagawa/git/honOCR/docs/issues/feat-005-full-conversion/README.md:43)）。実ファイル一覧も 84枚で、feat-003 側も位置1〜84を前提にしています（[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-003-mineru-trial/design.md:40)）。このままだと章対応表に未分類の3ページがあるように読めます。  
  **修正提案**: README の chap01/out 行を 84枚に修正し、chap-00/01 の採用・除外合計が 84 で閉じることを検証根拠に追記する。もし 87枚が意図値なら、未分類3枚のファイル名と採否を章対応表に追加してください。

低: なし。