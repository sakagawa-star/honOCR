**中**

1. `TECH_STACK.md` への反映予定文だけが system-only Python 条件を落としている  
実装設計自体は [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-001-env-setup-mineru/design.md:86) で `python-downloads = "never"` と `python-preference = "only-system"` を指定し、前回指摘は解消されています。一方、完了処理で `TECH_STACK.md` に書く予定の本文は [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-001-env-setup-mineru/design.md:273) で `python-downloads = "never"` だけに戻っており、`python-preference = "only-system"` と `/usr/` 配下確認が欠落しています。完了後の `TECH_STACK.md` が設計本体・要求仕様とズレるため、将来の環境再構築で uv managed Python を許容するように読めます。

修正提案: §11 の置換後本文にも `python-preference = "only-system"` と、`uv python find 3.12` の出力が `/usr/` 配下であることを確認する手順を明記する。

**前回指摘の解消状況**

- PyTorch cu130 インデックスのネットワーク要件: 解消。
- system-only Python の実装設計: 解消。ただし `TECH_STACK.md` 反映予定文に上記の中指摘あり。
- 前々回の PyTorch 固定・CUDA 実行テスト・pytest 固定・TECH_STACK 更新対象化: 解消。

**高 / 低**

なし。