> 日付: 2026-08-28 / 対象: requirements.md・design.md（背景・実測: README.md）
> session id: 01a05545-fb31-7d93-9fc2-3d10ec15f320 / 区分: 再(2回目)
> 検出: 高1
> Claude Code の対応: 全件反映。事前ゲートの対象を md と content_list.json の両方に拡張し（正規化は両方に効くため）、実データで全18件を分類して README に記録。あわせて「復元は md のみ」という制約と許容理由・build_final への非影響を要求/設計/記録に一貫して明示

---

前回の指摘のうち、再適用の冪等性の矛盾は解消されています。`apply_fixes.py` 単体の skip 型冪等性と、3工程全体の内容不変性を明確に分離しており、chap09 が毎回 `applied` になる理由も正しく記述されています。([requirements.md:116](/home/sakagawa/git/honOCR/docs/issues/feat-013-expand-cjk-table/requirements.md:116))

| 重要度 | 問題 | 修正提案 |
|---|---|---|
| 高 | 固有名詞保護の事前ゲートが Markdown 生出力だけを対象にしており、実際に正規化する `content_list.json` を分類対象から漏らしています。手順1は md と JSON の両方を一律置換する一方 ([design.md:287](/home/sakagawa/git/honOCR/docs/issues/feat-013-expand-cjk-table/design.md:287))、手順0の列挙コマンドは md だけです。([design.md:271](/home/sakagawa/git/honOCR/docs/issues/feat-013-expand-cjk-table/design.md:271)) したがって、JSON にのみ現れる旧字体の固有名詞は未分類のまま破壊されます。さらに `apply_fixes.py` は md 専用なので、発見後も JSON 側を復元できません。これは「全出現箇所を分類する」という受け入れ基準 ([requirements.md:93](/home/sakagawa/git/honOCR/docs/issues/feat-013-expand-cjk-table/requirements.md:93)) を満たしません。 | 手順0で md と `content_list.json` の両方を列挙・分類対象にしてください。そのうえで、JSON 内の固有名詞も保持する必要があるなら、JSON にも適用できる例外・復元方式を設計する必要があります。JSON 側の固有名詞表記を正規化してよい方針なら、その意図と「復元対象は md のみ」という制約を明示し、受け入れ基準の「全出現箇所」は md に限定してください。 |

旧字体警告そのものは、置換前の文脈を md・JSON の各入力から標準エラーに出す設計となっており、前回の「破壊に気づけない」問題は大幅に改善されています。([design.md:105](/home/sakagawa/git/honOCR/docs/issues/feat-013-expand-cjk-table/design.md:105)) ただし上記のとおり、事前ゲートと復元範囲が JSON を覆っていない点が残ります。その他に致命的な問題は見つかりません。