> 日付: 2026-08-28 / 対象: requirements.md・design.md（背景: README.md）
> session id: 01a045e9-e5d6-77b2-b77c-c9d6df0c0aac / 区分: 初回
> 検出: 高1・中2
> Claude Code の対応: 全件反映。(1)回帰の期待件数を実データ再集計で md 13件・json 23件に訂正 (2)design §2 にテスト結果ファイルの例外を明記 (3)上付き数式のアスタリスク個数を「0個または1個」に統一

---

致命的な指摘のみです。

## 高

- 回帰受け入れ基準の置換件数が自己矛盾しています。  
  [requirements.md:165](/home/sakagawa/git/honOCR/docs/issues/feat-011-multi-book-normalization/requirements.md:165) と [design.md:431](/home/sakagawa/git/honOCR/docs/issues/feat-011-multi-book-normalization/design.md:431) は合計 **15件**としていますが、列挙値は `3+4+2+1+1+2=13` 件です。背景資料の表とも整合しません。  
  このままでは「ペア別の件数」と「総件数15件」を同時に満たせず、FR-007 と自動テストの合否を決められません。  
  修正案: PRML final を再集計して正しい値を確定し、README・要求・設計・テスト期待値を同じ内訳と合計へ統一してください。列挙値が正しければ総件数は13件です。

## 中

- 「新規ファイルは作らない」と、テスト結果ファイルの作成要求が矛盾しています。  
  [design.md:21](/home/sakagawa/git/honOCR/docs/issues/feat-011-multi-book-normalization/design.md:21) は新規ファイルを作らないと明記する一方、[requirements.md:176](/home/sakagawa/git/honOCR/docs/issues/feat-011-multi-book-normalization/requirements.md:176) と [design.md:459](/home/sakagawa/git/honOCR/docs/issues/feat-011-multi-book-normalization/design.md:459) は `tests/results/feat-011_test_result.txt` の新規作成を要求しています。  
  修正案: 設計§2を「ソース・テスト以外では、テスト結果ファイルのみ新規作成」と修正するか、結果ファイルを成果物要件から外してください。

- 上付き数式プレフィックスで許容する `*` の個数が要求と設計で一致しません。  
  [requirements.md:133](/home/sakagawa/git/honOCR/docs/issues/feat-011-multi-book-normalization/requirements.md:133) は「アスタリスク0個以上」、[design.md:304](/home/sakagawa/git/honOCR/docs/issues/feat-011-multi-book-normalization/design.md:304) は `\*?`（0個または1個）です。実装者によって認識範囲が変わります。  
  修正案: 実測対象が `$^{3}$` と `$^{*4}$` のみなら、要求側も「0個または1個」に統一してください。複数個を許容する意図なら正規表現を `\**` 相当に変更し、テストを追加してください。

現行コードについては、上記以外に今回の変更範囲で高・中として報告すべき問題は見つかりませんでした。