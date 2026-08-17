# TECH_STACK

## 実行環境

- **OS**: Ubuntu 24.04（Linux 6.14.0-35-generic）
- **GPU**: NVIDIA GeForce RTX 5060 Ti 16GB（Blackwell 世代, sm_120。CUDA 12.8 以降のビルドが必須）
- **言語**: Python 3.12.3
- **パッケージ管理**: uv

## ライブラリ一覧

| ライブラリ | バージョン | 用途 | 選定理由 |
|---|---|---|---|
| mineru[core] | 3.4.4 | OCR エンジン本体 | 数式の LaTeX 認識と書籍まるごとの変換パイプライン（CLAUDE.md「背景」参照）。事前検証済みバージョンに固定 |
| torch | 2.13.0+cu130 | mineru の実行基盤（GPU 推論） | RTX 5060 Ti（sm_120）対応の CUDA 13.0 ビルド。cu130 インデックスから明示固定 |
| torchvision | 0.28.0+cu130 | mineru（pipeline バックエンド）の依存 | torch 2.13.0 対応版。cu130 インデックスから明示固定 |
| pytest | 9.1.1 | テストランナー（dev 依存） | CLAUDE.md「テスト」ルールで使用が前提。最新安定版に固定 |

<!--
運用ルール:
- ライブラリの追加・変更・削除を行ったら本表を更新する（CLAUDE.md「ドキュメント作成ルール」参照）
- 新規導入時は用途・選定理由・バージョンを必ず記入する
- バージョンは固定して記載する（未固定のまま残さない）
-->

## 環境構築手順

リポジトリルートで `uv sync` を実行する（`.venv` が作成され、全依存が導入される）。Python はシステムの 3.12 系を使用する（`[tool.uv]` の `python-downloads = "never"` により uv の Python 自動ダウンロードが、`python-preference = "only-system"` により uv 管理（managed）Python の使用が、それぞれ無効化されている）。事前確認は `uv python find 3.12` で行い、終了コード 0 かつ出力パスが `/usr/` 配下（uv 管理の `~/.local/share/uv/python/` 配下ではない）であることを確認する。torch / torchvision は PyTorch 公式 cu130 インデックス（`pyproject.toml` の `[[tool.uv.index]]` 定義）から導入される。

環境依存の注意:

- GPU が Blackwell 世代のため、古い CUDA 前提のツール（例: ndlocr_cli の CUDA 11.1 世代 Docker）は動作しない可能性が高い
