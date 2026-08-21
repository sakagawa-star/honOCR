> メタ: 2026-08-17 / 対象: feat-005 requirements.md・design.md / session id: 01a00fac-c16b-7182-94cc-650c2404887d / 初回レビュー
> 対応: 中2件とも対応済み（page_idx 集合一致チェックへの強化、chap-01 再利用成果物2ファイルの再検証＋コードポイント比較の追加）。codex-02 で解消を確認

**指摘**

- **中**: `page_idx` 最大値だけでは全17ページ処理を証明できません。  
  [requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-005-full-conversion/requirements.md:36) と [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-005-full-conversion/design.md:45) は `max(page_idx) == 16` を「17ページ全て処理」とみなしていますが、0〜15ページが欠落していても最大値が16なら通ります。全章成果物の欠落を合格にする受け入れ基準なので修正対象です。  
  **修正提案**: content list が非空で、全ブロックに整数 `page_idx` があり、`set(page_idx) == set(range(17))` を満たすことを受け入れ基準と設計手順に明記する。あわせて欠落ページ・範囲外ページを報告して中断する。

- **中**: chap-01 の再利用成果物の検証が md に偏っており、final に含める `content_list.json` の正規化状態を最終確認していません。  
  [requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-005-full-conversion/requirements.md:73) と [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-005-full-conversion/design.md:99) は chap-01 md の残存「、」「。」だけを再確認しています。一方、final には chap-01 の `content_list.json` も成果物として含めます。既存の feat-004 で合格済みとはいえ、外部データを再利用する本案件の final 構築条件としては検証漏れです。  
  **修正提案**: chap-01 の `chap-01_gray300.md` と `chap-01_gray300_content_list.json` の両方について、残存「、」「。」0件を確認する。可能なら feat-004 と同じコードポイント比較を run-02 生出力との間で再実行し、失敗時は final 構築を中断する。

**分類結果**

高: なし。  
低: 報告対象なし。