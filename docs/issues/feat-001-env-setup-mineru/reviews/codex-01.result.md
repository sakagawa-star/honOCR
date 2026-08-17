**高**

1. CUDA 対応 PyTorch の解決条件が仕様化されていない  
[requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-001-env-setup-mineru/requirements.md:51) は CUDA 12.8 以降対応ビルドを必須にしていますが、[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-001-env-setup-mineru/design.md:53) は `torch` を MinerU の推移的依存に任せています。MinerU 3.4.4 のメタデータ上、`mineru[core]` は `torch>=2.6,<3` の範囲指定であり、検証済みとされる `2.13.0+cu130` には固定されません。さらにテストは [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-001-env-setup-mineru/design.md:141) の `is_available()` と compute capability だけで、CUDA ビルド版数や実際の CUDA kernel 実行を検証していません。

修正提案: `pyproject.toml` に検証済みの `torch==2.13.0+cu130` と対応する `torchvision==...+cu130` を明示依存として追加し、`[[tool.uv.index]]` / `[tool.uv.sources]` で `https://download.pytorch.org/whl/cu130` を明示する。テストにも `torch.version.cuda >= 12.8` と、`torch.tensor(..., device="cuda")` の最小演算を追加する。

2. uv の Python 自動ダウンロード禁止が実行手順で担保されていない  
[requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-001-env-setup-mineru/requirements.md:52) は変更範囲をリポジトリ内に限定していますが、[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-001-env-setup-mineru/design.md:85) は単に `uv sync` を実行します。uv は既定で不足 Python を自動ダウンロードし得るため、[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-001-env-setup-mineru/design.md:95) の「自動ダウンロードは行わない」と矛盾します。

修正提案: 手順を `uv sync --no-python-downloads --no-managed-python` に変更するか、`[tool.uv] python-downloads = "never"` を設計に含める。事前確認として system Python 3.12.3 の存在確認手順も明記する。

**中**

3. `TECH_STACK.md` 更新が設計対象から漏れており、依存バージョンも固定されていない  
[CLAUDE.md](/home/sakagawa/git/honOCR/CLAUDE.md:151) は新規ライブラリ導入時の `docs/TECH_STACK.md` 更新を必須にしていますが、[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-001-env-setup-mineru/design.md:17) の変更ファイルに含まれていません。現状の [TECH_STACK.md](/home/sakagawa/git/honOCR/docs/TECH_STACK.md:24) には `uv init / uv add` 前提の記述も残っており、設計の「`uv init` は使わない」と食い違います。また `pytest>=8` はバージョン未固定です。

修正提案: `docs/TECH_STACK.md` を変更対象に追加し、実施後の確定コマンドと依存一覧を固定版数で記載する。少なくとも `mineru==3.4.4`、`pytest==<固定版>`、`torch==<CUDA対応固定版>`、必要なら `torchvision==<固定版>` を反映する。

**低**

なし。

外部確認元: [MinerU 3.4.4 PyPI metadata](https://pypi.org/pypi/mineru/3.4.4/json), [uv PyTorch guide](https://docs.astral.sh/uv/guides/integration/pytorch/), [uv Python versions](https://docs.astral.sh/uv/concepts/python-versions/)