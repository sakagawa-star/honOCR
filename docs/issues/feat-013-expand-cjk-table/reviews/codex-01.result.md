> 日付: 2026-08-28 / 対象: requirements.md・design.md（背景・実測: README.md）
> session id: 01a05545-fb31-7d93-9fc2-3d10ec15f320 / 区分: 初回
> 検出: 高2
> Claude Code の対応: 全件反映。(1)再適用の冪等性を「apply_fixes 単体=skip型」と「3ステップ全体=出力内容の不変」に分離し、chap09 が毎回 applied になる理由を明記 (2)FR-006（旧字体の置換箇所を置換【前】の文脈つきで警告）を新設し、ADR-1 のリスク対策を「機械的検出＋運用ゲート」の2段構えに再設計

---

致命的な問題は2件です。低重要度の指摘は省略します。

| 重要度 | 問題 | 修正提案 |
|---|---|---|
| 高 | 固有名詞復元を含む「再適用」は、要求するスキップ型の冪等性を満たせません。初回後の `廣済堂` は、次回の手順1で `廣→広` に戻り、手順2で再び `applied` になります。`apply_fixes.py` 単体なら skip ですが、設計された3ステップ全体では chap09 が毎回 applied です。要求の「2回目は適用済みスキップ」([requirements.md:112](/home/sakagawa/git/honOCR/docs/issues/feat-013-expand-cjk-table/requirements.md:112)) と、正規化→復元の順序 ([design.md:182](/home/sakagawa/git/honOCR/docs/issues/feat-013-expand-cjk-table/design.md:182), [design.md:203](/home/sakagawa/git/honOCR/docs/issues/feat-013-expand-cjk-table/design.md:203)) が矛盾します。実装もこの通りの挙動です（`old` があれば常に置換）([apply_fixes.py:92](/home/sakagawa/git/honOCR/scripts/apply_fixes.py:92))。 | 「冪等性」の対象を明確化してください。現方針を維持するなら、パイプライン全体は「出力内容が不変」、`apply_fixes.py` 単体のみ「全件 skipped」と受け入れ基準を分け、chap09 は再適用ごとに `applied` になることを明記・テストします。全工程で skip を必須にするなら、`廣` の一律置換をやめるか、正規化前に除外できる仕組みが必要です。 |
| 高 | 旧字体5字をグローバル置換する一方で、将来の書籍・既存の他成果物で固有名詞が壊れたことを機械的に検出する手段がありません。`廣済堂` は既に反例です。置換後に JIS外漢字警告を出す実装なので、JIS内の旧字体は警告されず、元の字も失われます ([normalize_punct.py:52](/home/sakagawa/git/honOCR/scripts/normalize_punct.py:52), [normalize_punct.py:67](/home/sakagawa/git/honOCR/scripts/normalize_punct.py:67))。「新書籍では目視確認する」だけでは、いつ・どの入力を・どの基準で確認し、未確認なら処理を止めるかが未定義です ([design.md:93](/home/sakagawa/git/honOCR/docs/issues/feat-013-expand-cjk-table/design.md:93))。PRMLの0件確認はPRMLだけを保証し、他書籍の安全性を保証しません。 | 少なくとも正規化前の `run-NN/` を対象に、5旧字体の出現箇所を列挙・原本照合・復元定義作成する必須ゲートを手順化し、結果を記録してください。未分類の出現が1件でもあれば final 構築を行わない、という合格条件が必要です。より安全には、旧字体の一律変換を通常の字形表から分離し、明示的に監査済みの書籍だけで有効化できる設計にします。 |

それ以外は、`normalize_punct.py` → `apply_fixes.py` → `build_final.py` の順序、md と `content_list.json` の非対称性、確率統計での byte 一致確認は、既存実装・feat-010/011 の前提と整合しています。