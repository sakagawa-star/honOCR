# feat-001 要求仕様書: uv 環境構築と MinerU 導入

## 1. プロジェクト概要

- **何を作るのか**: honOCR リポジトリに uv 管理の Python 実行環境を構築し、OCR エンジン MinerU を導入する
- **なぜ作るのか**: 後続フェーズ（TIF→OCR用PDF生成スクリプト、MinerU による OCR 実行）の前提となる実行環境がまだ存在しないため
- **誰が使うのか**: 本リポジトリの開発者（ユーザーおよび Claude Code）
- **どこで使うのか**: ローカルマシン（Ubuntu 24.04 / NVIDIA RTX 5060 Ti 16GB / Python 3.12.3 / uv 導入済み）

## 2. 用語定義

| 用語 | 定義 |
|---|---|
| uv | Astral 製の Python パッケージ・プロジェクト管理ツール。本プロジェクトで環境管理に用いる唯一の手段 |
| MinerU | OCR エンジン。レイアウト解析・数式の LaTeX 化・Markdown 出力・座標付き JSON 出力を行う |
| mineru[core] | MinerU の pip パッケージ `mineru` に extra `core` を付けた指定。pipeline / vlm / hybrid バックエンドの実行に必要な依存一式を含む |
| スモークテスト | 環境が最低限機能すること（GPU 認識・パッケージ導入）を確認する自動テスト |
| sm_120 | 本環境の GPU（Blackwell 世代）の compute capability 12.0 を指す表記 |

機能設計書・コード内でも上記と同じ用語を使う。

## 3. 機能要求一覧

### FR-001: uv プロジェクト初期化

- **機能名**: uv プロジェクト初期化
- **概要**: honOCR ルートに uv プロジェクト定義（`pyproject.toml`・`.python-version`・`uv.lock`）を作成し、`.venv` を構築できる状態にする
- **入力**: なし（コマンド実行のみ）
- **出力**: `pyproject.toml`、`.python-version`、`uv.lock`、`.venv/`（git 管理外）
- **受け入れ基準**: `uv sync` がエラーなく完了し、`uv run python --version` の出力が `Python 3.12` で始まる

### FR-002: MinerU の導入

- **機能名**: MinerU の導入
- **概要**: `mineru[core]==3.4.4` を uv の依存関係として追加し、CLI が実行可能な状態にする
- **入力**: なし（コマンド実行のみ）
- **出力**: `pyproject.toml` の dependencies への `mineru[core]==3.4.4` の記録、更新された `uv.lock`
- **受け入れ基準**: `uv run mineru --version` の出力に文字列 `3.4.4` が含まれる

### FR-003: GPU 動作確認スモークテスト

- **機能名**: GPU 動作確認スモークテスト
- **概要**: 導入した PyTorch が本環境の GPU（sm_120）を認識し、導入パッケージのバージョンが指定どおりであることを確認する pytest テストを作成・実行する
- **入力**: なし（`uv run pytest -v` の実行）
- **出力**: `tests/test_env.py`、`tests/results/feat-001_test_result.txt`
- **受け入れ基準**: `uv run pytest -v` が全件 PASS（失敗 0 件・エラー 0 件）し、その出力が `tests/results/feat-001_test_result.txt` に保存されている

## 4. 非機能要求

- **パフォーマンス**: 要求しない（環境構築のみの案件。インストール所要時間の上限は定めない）
- **対応環境**: Ubuntu 24.04 / NVIDIA RTX 5060 Ti 16GB（Blackwell, compute capability 12.0）/ Python 3.12.3 / uv。導入される PyTorch は CUDA 12.8 以降対応ビルドであること（sm_120 対応に必須）
- **信頼性**: インストールの変更範囲は uv 管理下（リポジトリ内の `.venv`・`pyproject.toml`・`.python-version`・`uv.lock`）に限定し、システム Python・グローバル環境に変更を加えない。失敗時は失敗内容を報告して中断する（部分的に構築された `.venv` が残ることは許容する。`uv sync` の再実行で回復できるため）
- **セキュリティ**: 該当なし

## 5. 制約条件

- **使用必須**: uv（環境管理）、`mineru[core]==3.4.4`、`torch==2.13.0`（CUDA 13.0 ビルド。PyTorch 公式 cu130 インデックスから導入）、`torchvision==0.28.0`（同じく cu130 インデックスから導入）、`pytest==9.1.1`（テストランナー、dev 依存）。バージョンはすべて完全固定とする
- **使用禁止**: pip の直接実行、`python -m venv` の直接実行、conda、uv の Python 自動ダウンロード機能（システムの Python 3.12.3 を使用する）
- **ネットワーク**: PyPI（`https://pypi.org`）および PyTorch 公式 cu130 インデックス（`https://download.pytorch.org/whl/cu130`、実体は `https://download-r2.pytorch.org` にリダイレクトされる）への HTTPS アクセスが必要（オフライン動作は要求しない）
- **ディスク**: 空き容量 20GB 以上ある状態で実行する（2026-08-05 の事前検証で `.venv` が数 GB 規模になることを確認済み）
- **スコープ外**: MinerU の実行（OCR 処理）とモデルのダウンロードは本案件では行わない（BACKLOG のフェーズ3案件で行う）

## 6. 優先順位

| 要求ID | MoSCoW |
|---|---|
| FR-001 | Must |
| FR-002 | Must |
| FR-003 | Must |

MVP = FR-001〜FR-003 のすべて（本案件は3要求で完結する）。
