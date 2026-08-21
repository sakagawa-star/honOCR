> メタ: 2026-08-18 / 対象: feat-005 requirements.md FR-004・design.md §4.4（feat-007 起票に伴う差分）/ session id: 01a00fac-c16b-7182-94cc-650c2404887d / 差分レビュー（7回目）
> 対応: 中3件（final ゲートへのカラー再切出条件、content_list 由来画像の検証手順、基準番号）すべて対応済み。codex-08 で解消を確認

差分起因の高重要度はありません。コピー元を `run-NN-normalized/images/` に変える本筋は、feat-005 / feat-007 間で整合しています。

**中**
- final 実施ゲートに旧条件が残っています。  
  [requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-005-full-conversion/requirements.md:84) は「FR-001〜FR-003 で中断した場合」だけを final 中止条件にしており、[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-005-full-conversion/design.md:171) も「§4.3 合格後に §4.4」と読めます。一方で [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-005-full-conversion/design.md:116) は feat-007 のカラー再切出完了を §4.4 前提にしています。  
  修正提案: requirements 基準5と design §10 に「全8章で feat-007 のカラー再切出が完了し、`img_path` ユニーク数 = `run-NN-normalized/images/` ファイル数を満たすこと」を §4.4 実施前条件として明記する。

- 新しい FR-004 基準4が design の検証手順に反映されていません。  
  [requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-005-full-conversion/requirements.md:83) は `content_list` の `img_path` ユニーク数と `final/chapNN/images/` ファイル数の一致を要求していますが、[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-005-full-conversion/design.md:127)〜[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-005-full-conversion/design.md:129) の final 検証は存在確認・cmp・md参照確認までです。md参照は content_list の `img_path` 全体の部分集合になり得るため、このままだと content_list からのみ参照される画像の欠落を検出できません。  
  修正提案: §4.4 検証に「final 側 content_list から `img_path` の basename ユニーク集合を抽出し、`final/chapNN/images/` 直下のファイル集合または件数と一致すること」を追加する。

- 番号繰り下げ漏れがあります。  
  [requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-005-full-conversion/requirements.md:110) が「final の全ディレクトリ必須条件は FR-004 受け入れ基準4」としていますが、現在その条件は基準5です。  
  修正提案: `基準5` に修正する。

**低**
- なし。