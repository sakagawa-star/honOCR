# CHANGELOG

## リリース履歴

### 2026-08-17

- **feat-001**: uv 環境構築と MinerU 導入
  - uv プロジェクトを初期化（`pyproject.toml` / `.python-version` / `uv.lock`）。`mineru[core]==3.4.4`、`torch==2.13.0+cu130`・`torchvision==0.28.0+cu130`（PyTorch 公式 cu130 インデックスから固定）、`pytest==9.1.1` を導入
  - `[tool.uv]` で Python 自動ダウンロード禁止（`python-downloads = "never"`）とシステム Python 限定（`python-preference = "only-system"`）を設定
  - 検証結果: スモークテスト6件全件 PASS（Python 3.12 / CUDA 認識 / CUDA ビルド 12.8 以上 / compute capability (12,0) / CUDA カーネル実行 / mineru バージョン）。結果は `tests/results/feat-001_test_result.txt`。ユーザーの手動テストでも全件 PASS を確認
  - Codex レビュー: 4サイクルで収束（高3・中3を検出）。主要指摘は torch の推移的依存任せによるバージョン不定、Python 自動ダウンロードの禁止漏れ、cu130 インデックスのネットワーク要件記述漏れ、TECH_STACK.md 更新計画の漏れ
