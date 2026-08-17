# feat-001 機能設計書: uv 環境構築と MinerU 導入

## 1. 対応要求マッピング

対象: `docs/issues/feat-001-env-setup-mineru/requirements.md`

| 要求ID | 設計セクション |
|---|---|
| FR-001 | §4.1 |
| FR-002 | §4.2 |
| FR-003 | §4.3 |

## 2. システム構成

### 追加・変更ファイル

| ファイル | 種別 | 担当内容 |
|---|---|---|
| `pyproject.toml` | 新規 | プロジェクト定義と依存関係（§4.1 に全文を記載） |
| `.python-version` | 新規 | Python バージョン固定（内容: `3.12`） |
| `uv.lock` | 自動生成 | `uv sync` が生成するロックファイル（手編集しない） |
| `tests/test_env.py` | 新規 | スモークテスト（§4.3 に仕様を記載） |
| `tests/results/feat-001_test_result.txt` | 新規 | テスト実行結果の保存先 |
| `docs/TECH_STACK.md` | 変更 | 導入ライブラリと環境構築手順の反映（§11 に内容を記載。完了ステップ8で Claude Code 本体が実施） |

### 依存関係

- `tests/test_env.py` → `torch`（mineru の推移的依存）、`importlib.metadata`（標準ライブラリ）
- モジュール間の循環依存: なし（本案件でソースモジュールは作成しない）

### ディレクトリ構成（実施後）

```
honOCR/
├── CLAUDE.md
├── pyproject.toml          # 新規
├── .python-version         # 新規
├── uv.lock                 # 新規（自動生成）
├── .venv/                  # 新規（git 管理外）
├── docs/
└── tests/                  # 新規
    ├── test_env.py
    └── results/
        └── feat-001_test_result.txt
```

## 3. 技術スタック

- **言語**: Python 3.12（`.python-version` で固定。パッチバージョンは固定しない — uv がシステムの 3.12.3 を解決する）
- **パッケージ管理**: uv
- **導入ライブラリ**:
  - `mineru[core]==3.4.4` — OCR エンジン本体。選定理由: 数式の LaTeX 認識と書籍まるごとの変換パイプラインを持つ（詳細は CLAUDE.md「背景」）。バージョンは 2026-08-05 の事前検証で GPU 認識を確認した 3.4.4 に完全固定
  - `pytest==9.1.1`（dev 依存）— テストランナー。CLAUDE.md「テスト」のルールで使用が前提とされている。作成時点（2026-08-17）の最新安定版に完全固定
  - `torch==2.13.0`・`torchvision==0.28.0` — PyTorch 公式 cu130 インデックス（`https://download.pytorch.org/whl/cu130`）から導入する明示依存（§9 ADR-3 参照）。mineru 3.4.4 のメタデータ上の要求は `torch>=2.6,<3` と `torchvision`（未固定）であり、範囲指定のままでは事前検証済みのビルドに固定されないため明示する。両バージョンの cp312 / manylinux x86_64 / +cu130 ホイールが同インデックスに存在することを確認済み（2026-08-17）。2026-08-05 の事前検証では torch 2.13.0+cu130 が RTX 5060 Ti を認識した

## 4. 各機能の詳細設計

### 4.1 uv プロジェクト初期化（FR-001）

#### データフロー

- 入力: なし
- 出力: `pyproject.toml`（UTF-8 テキスト）、`.python-version`（内容は `3.12` の1行）、`uv.lock`、`.venv/`

#### 処理ロジック

1. リポジトリルート（`/home/sakagawa/git/honOCR`）に以下の内容の `pyproject.toml` を作成する（下記が完成形。これをそのまま使う）:

```toml
[project]
name = "honocr"
version = "0.1.0"
description = "スキャン書籍（PRML）をOCRしてLLM学習用Markdownに変換する"
requires-python = ">=3.12"
dependencies = [
    "mineru[core]==3.4.4",
    "torch==2.13.0",
    "torchvision==0.28.0",
]

[dependency-groups]
dev = [
    "pytest==9.1.1",
]

[tool.uv]
python-downloads = "never"
python-preference = "only-system"

[[tool.uv.index]]
name = "pytorch-cu130"
url = "https://download.pytorch.org/whl/cu130"
explicit = true

[tool.uv.sources]
torch = { index = "pytorch-cu130" }
torchvision = { index = "pytorch-cu130" }
```

補足: `python-downloads = "never"` により uv の Python 自動ダウンロードを禁止し、`python-preference = "only-system"` により uv 管理下の（managed）Python の使用も禁止する（システムの Python 3.12.3 のみを使う）。`torch==2.13.0` は PEP 440 の規則によりローカルバージョン付きの `2.13.0+cu130`（cu130 インデックス上のホイール）に一致する。`explicit = true` により cu130 インデックスは `tool.uv.sources` で指定した torch / torchvision の解決のみに使われる。

2. 内容が `3.12` の1行である `.python-version` を作成する
3. `uv python find 3.12` を実行し、終了コードが 0 であること、かつ出力されたパスが `/usr/` 配下（システム Python。uv 管理の `~/.local/share/uv/python/` 配下ではない）であることを確認する。どちらかを満たさない場合は中断して報告する（手順1の `python-preference = "only-system"` により `uv sync` もシステム Python のみを使う）
4. `uv sync` を実行する（`uv.lock` と `.venv` が生成され、dependencies と dev グループの両方が導入される）
5. `uv run python --version` を実行し、出力が `Python 3.12` で始まることを確認する

注: `uv init` コマンドは使わない（§9 ADR-2 参照）。

#### エラーハンドリング

| エラー | 検出方法 | 処理 |
|---|---|---|
| `uv sync` の失敗（ネットワーク・依存解決） | 終了コード非0 | 1回だけ再実行する。再度失敗したら中断し、エラーメッセージ全文を報告する |
| Python 3.12 が見つからない | 手順3の `uv python find 3.12` の終了コード非0 | 中断して報告する。`[tool.uv] python-downloads = "never"` により uv による Python 自動ダウンロードは発生しない |
| バージョン確認の不一致 | 出力文字列の目視比較 | 中断して報告する |

ログ出力: uv の標準出力をそのまま用いる（追加のログ実装はしない）。

#### 境界条件

- `.venv` が既に存在する場合: `uv sync` が既存 `.venv` を再利用・更新する（削除は不要）
- ディスク不足の場合: `uv sync` がエラー終了する → 上記エラーハンドリングに従い中断・報告する

### 4.2 MinerU の導入（FR-002）

#### データフロー

- 入力: なし（§4.1 の `pyproject.toml` に依存指定済み。`uv sync` で導入される）
- 出力: `.venv` 内の mineru 一式と CLI エントリポイント

#### 処理ロジック

1. §4.1 の手順3（`uv sync`）で導入は完了している
2. `uv run mineru --version` を実行し、出力に `3.4.4` が含まれることを確認する

#### エラーハンドリング

| エラー | 検出方法 | 処理 |
|---|---|---|
| `mineru` コマンドが見つからない | 終了コード非0 | 中断して報告する |
| バージョン出力に `3.4.4` が含まれない | 出力文字列の確認 | 中断して報告する |

#### 境界条件

- 本案件では `mineru` の OCR 実行・モデルダウンロードを行わない。`--version` の表示のみ行う（モデルダウンロードは発生しない）

### 4.3 GPU 動作確認スモークテスト（FR-003）

#### データフロー

- 入力: なし（pytest がテスト関数を自動収集する）
- 出力: pytest の実行結果（終了コード、テキスト出力）。出力全文を `tests/results/feat-001_test_result.txt` に保存する

#### 処理ロジック

`tests/test_env.py` に以下の6つのテスト関数を実装する（関数名・判定条件はこの表のとおりに実装する）:

| テスト関数名 | 判定条件（assert） |
|---|---|
| `test_python_version` | `sys.version_info[:2] == (3, 12)` |
| `test_torch_cuda_available` | `torch.cuda.is_available() is True` |
| `test_torch_cuda_build_version` | `torch.version.cuda` が `None` でなく、`tuple(int(x) for x in torch.version.cuda.split(".")[:2]) >= (12, 8)` |
| `test_gpu_compute_capability` | `torch.cuda.get_device_capability(0) == (12, 0)` |
| `test_cuda_kernel_execution` | `torch.ones(2, 2, device="cuda")` を2倍した結果の `sum().item()` が `8.0` と等しい（CUDA カーネルが実際に実行できることの確認） |
| `test_mineru_version` | `importlib.metadata.version("mineru") == "3.4.4"` |

実装イメージ（意図伝達のためのコード例。import 文の配置と関数分割はこのとおりでよいが、そのままの転記を保証するものではない）:

```python
import importlib.metadata
import sys

import torch


def test_python_version() -> None:
    assert sys.version_info[:2] == (3, 12)


def test_torch_cuda_available() -> None:
    assert torch.cuda.is_available() is True


def test_torch_cuda_build_version() -> None:
    assert torch.version.cuda is not None
    assert tuple(int(x) for x in torch.version.cuda.split(".")[:2]) >= (12, 8)


def test_gpu_compute_capability() -> None:
    assert torch.cuda.get_device_capability(0) == (12, 0)


def test_cuda_kernel_execution() -> None:
    x = torch.ones(2, 2, device="cuda")
    y = x + x
    assert y.sum().item() == 8.0


def test_mineru_version() -> None:
    assert importlib.metadata.version("mineru") == "3.4.4"
```

実行手順:

1. `mkdir -p tests/results`
2. `uv run pytest -v > tests/results/feat-001_test_result.txt 2>&1` を実行する（CLAUDE.md「テスト」ルールに従い出力をそのまま保存する）
3. 終了コード 0（全件 PASS）を確認する。`cat tests/results/feat-001_test_result.txt` で `6 passed` を確認する

#### エラーハンドリング

| エラー | 検出方法 | 処理 |
|---|---|---|
| いずれかのテストが FAIL / ERROR | pytest 終了コード非0 | 修正を試みず中断し、`feat-001_test_result.txt` の内容を報告する |

#### 境界条件

- GPU が他プロセスに使用中の場合: `test_cuda_kernel_execution` は CUDA コンテキスト初期化と 2×2 テンソル2個分（1KB 未満。コンテキスト込みでも数百 MB）の GPU メモリを確保する。本環境（16GB）では他プロセスとの併用でも確保に失敗しない想定とし、GPU メモリ空き容量の事前チェックは実装しない。確保に失敗した場合はテスト FAIL として上記エラーハンドリングに従う

## 5. 状態遷移

該当なし（GUI・ステートフル処理はない）。

## 6. ファイル・ディレクトリ設計

- 入出力パス規約: §2 のディレクトリ構成に従う。すべてリポジトリルートからの相対パス
- テスト結果ファイル命名: `tests/results/{type}-{number}_test_result.txt`（本案件は `feat-001_test_result.txt`）
- 設定ファイル: `pyproject.toml`（TOML、スキーマと全内容は §4.1 に記載）。それ以外の設定ファイルは作成しない
- `.gitignore` の変更: 不要（`.venv/` は既にエントリ済み）

## 7. インターフェース定義

- 公開関数・クラス: なし（本案件でソースモジュールは作成しない）
- テスト関数: §4.3 の6関数。すべて引数なし・戻り値 `None`・assert による判定

## 8. ログ・デバッグ設計

- 本案件ではログ機構を実装しない。uv・pytest の標準出力をそのまま記録として用いる
- テスト結果の記録は `tests/results/feat-001_test_result.txt` への保存で行う

## 9. 設計判断の記録（ADR）

| # | 採用 | 却下と理由 |
|---|---|---|
| 1 | `mineru[core]==3.4.4` に完全固定 | `>=3.4` の範囲指定 — 再現性を優先。事前検証済みバージョンと一致させる |
| 2 | `pyproject.toml` を本設計書記載の内容で直接作成 | `uv init` の生成物を編集 — 生成内容が uv のバージョンに依存し決定性に欠ける |
| 3 | `torch==2.13.0`・`torchvision==0.28.0` を cu130 インデックスから明示固定 | 推移的依存任せ — mineru の要求は `torch>=2.6,<3` の範囲指定であり、事前検証済みの CUDA 対応ビルドに固定されない（Codex レビュー codex-01 指摘1 への対応）。mineru の範囲と衝突しないことは確認済み（2.13.0 は `>=2.6,<3` に含まれる） |
| 4 | GPU 判定は compute capability `(12, 0)` の等値比較＋CUDA ビルド版数＋カーネル実行の3点 | `is_available()` のみ — 別 GPU 環境での誤合格を防ぎ、CUDA 12.8 以降のビルドと実カーネル実行まで確認する（Codex レビュー codex-01 指摘1 への対応） |
| 5 | extra は `core` を採用 | `all` — sglang を含む重量依存が増えるが本プロジェクトでは不要。`core` で pipeline / vlm / hybrid バックエンドが動作する |
| 6 | `[tool.uv]` に `python-downloads = "never"` と `python-preference = "only-system"` を設定 | CLI フラグでの都度指定 — 宣言的に固定するほうが指定漏れが起きない。`only-system` は uv 管理 Python の使用も防ぐ（Codex レビュー codex-01 指摘2・codex-02 指摘2 への対応） |
| 7 | `pytest==9.1.1` に完全固定 | `>=8` の範囲指定 — TECH_STACK.md の「バージョンは固定して記載する」ルールと整合させる（Codex レビュー codex-01 指摘3 への対応） |

## 10. 実装・検証の実施方法

- 実装は CLAUDE.md「実装の実行方法（Sonnetサブエージェント）」に従い Sonnet サブエージェントに委任する
- 実装（= `uv sync` によるインストールを含む）は、Codex レビュー収束後の人レビュー承認を得てから開始する（環境変更操作の事前承認ルールに従う）
- 検証は §4.1〜4.3 の確認手順（バージョン確認2件、pytest 全件実行と結果保存）をすべて実施する

## 11. 完了処理でのドキュメント更新（`docs/TECH_STACK.md`）

完了ステップ8で Claude Code 本体（サブエージェントではない）が `docs/TECH_STACK.md` に以下の変更を行う:

1. **「ライブラリ一覧」の表**に次の4行を追加する:

| ライブラリ | バージョン | 用途 | 選定理由 |
|---|---|---|---|
| mineru[core] | 3.4.4 | OCR エンジン本体 | 数式の LaTeX 認識と書籍まるごとの変換パイプライン（CLAUDE.md「背景」参照）。事前検証済みバージョンに固定 |
| torch | 2.13.0+cu130 | mineru の実行基盤（GPU 推論） | RTX 5060 Ti（sm_120）対応の CUDA 13.0 ビルド。cu130 インデックスから明示固定 |
| torchvision | 0.28.0+cu130 | mineru（pipeline バックエンド）の依存 | torch 2.13.0 対応版。cu130 インデックスから明示固定 |
| pytest | 9.1.1 | テストランナー（dev 依存） | CLAUDE.md「テスト」ルールで使用が前提。最新安定版に固定 |

2. **「環境構築手順」節**の本文（「未整備。〜」から始まる段落と「導入予定〜」の一覧、「環境依存の注意」の直前まで）を次の内容に置き換える:

> リポジトリルートで `uv sync` を実行する（`.venv` が作成され、全依存が導入される）。Python はシステムの 3.12 系を使用する（`[tool.uv]` の `python-downloads = "never"` により uv の Python 自動ダウンロードが、`python-preference = "only-system"` により uv 管理（managed）Python の使用が、それぞれ無効化されている）。事前確認は `uv python find 3.12` で行い、終了コード 0 かつ出力パスが `/usr/` 配下（uv 管理の `~/.local/share/uv/python/` 配下ではない）であることを確認する。torch / torchvision は PyTorch 公式 cu130 インデックス（`pyproject.toml` の `[[tool.uv.index]]` 定義）から導入される。

3. 「環境依存の注意」の節（Blackwell 世代に関する注意）は変更せず残す

本更新は「新規ライブラリ導入時は TECH_STACK.md に追記する」ルール（CLAUDE.md「ドキュメント作成ルール」）への対応であり、Codex レビュー codex-01 指摘3 への対応として設計に含める。
