**高**

1. `requirements.md` のネットワーク制約が設計と矛盾している  
[requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-001-env-setup-mineru/requirements.md:59) は「PyPI へのアクセスが必要」とだけ定義していますが、[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-001-env-setup-mineru/design.md:89) は `https://download.pytorch.org/whl/cu130` を必須の追加インデックスとして使います。これは外部依存エンドポイントの記述漏れで、このままだと要件上は PyPI だけ許可すればよいように読め、実装時の `uv sync` が失敗します。

修正提案: `requirements.md` のネットワーク制約を「PyPI および PyTorch 公式 cu130 インデックス `https://download.pytorch.org/whl/cu130` への HTTPS アクセスが必要」と明記する。

**中**

2. 「システム Python 3.12.3 のみ使用」がまだ完全には担保されていない  
前回の Python 自動ダウンロード禁止は [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-001-env-setup-mineru/design.md:86) で解消されています。ただし uv は `python-downloads = "never"` だけでは既存の uv managed Python を使う可能性が残ります。[requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-001-env-setup-mineru/requirements.md:58) は「システムの Python 3.12.3」を使う前提なので、[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-001-env-setup-mineru/design.md:102) の `uv python find 3.12` だけでは弱いです。

修正提案: `[tool.uv]` に `python-preference = "only-system"` を追加し、確認手順も `uv python find 3.12.3 --no-managed-python --no-python-downloads` 相当にする。受け入れ基準も必要なら `Python 3.12.3` まで確認する。

**前回指摘の解消状況**

- CUDA 対応 PyTorch の明示固定と CUDA 実行テスト: 概ね解消。torch / torchvision の cu130 wheel 存在も確認できる。
- uv の Python 自動ダウンロード禁止: 部分解消。ダウンロード禁止は入ったが、system-only 指定が不足。
- `TECH_STACK.md` 更新計画と pytest 固定: 解消。

**低**

なし。

外部確認元: [uv PyTorch guide](https://docs.astral.sh/uv/guides/integration/pytorch/), [uv Python versions](https://docs.astral.sh/uv/concepts/python-versions/), [uv settings](https://docs.astral.sh/uv/reference/settings/), [PyTorch cu130 torch index](https://download.pytorch.org/whl/cu130/torch/), [PyTorch cu130 torchvision index](https://download.pytorch.org/whl/cu130/torchvision/)