# CHANGELOG

## リリース履歴

### 2026-08-17

- **feat-002**: TIF → OCR用可逆PDF生成スクリプト
  - `scripts/make_ocr_pdf.py` を追加。原本TIF（600dpi）をグレースケール化・1/2縮小（300dpi相当）し、Flate 可逆で複数ページPDFに格納する CLI（入力TIF列 + `-o` + `--overwrite`。章対応は呼び出し時のファイル指定で表現）
  - 安全設計: 変換前の全件検証（存在・モード・`im.load()` による実デコード）、一時ファイル経由の原子的書き込み（no-clobber は `os.link`、上書きは `os.replace`）
  - 依存追加: `img2pdf==0.6.3`（新規）、`pillow==12.3.0`・`pypdf==6.16.1`（ロック済み版の明示固定）
  - 検証結果: テスト10件追加（計16件全 PASS、`tests/results/feat-002_test_result.txt`）。実データ確認: 4件サンプルで gray/8-bit/Flate/300ppi を確認、全84件の一括変換が 22.4秒・62.3MB（`.../chap01/out/ocr/` に `sample4.pdf`・`all-pages.pdf` を残置）。ユーザーの目視で文字・数式の可読性を確認
  - Codex レビュー: 3サイクルで収束（高1・中3を検出）。主要指摘は非原子的書き込みによる不完全PDF残留、壊れたTIFの事前検出漏れ、`--overwrite` なし時の競合上書き、書き込み失敗テストの実効性

- **feat-001**: uv 環境構築と MinerU 導入
  - uv プロジェクトを初期化（`pyproject.toml` / `.python-version` / `uv.lock`）。`mineru[core]==3.4.4`、`torch==2.13.0+cu130`・`torchvision==0.28.0+cu130`（PyTorch 公式 cu130 インデックスから固定）、`pytest==9.1.1` を導入
  - `[tool.uv]` で Python 自動ダウンロード禁止（`python-downloads = "never"`）とシステム Python 限定（`python-preference = "only-system"`）を設定
  - 検証結果: スモークテスト6件全件 PASS（Python 3.12 / CUDA 認識 / CUDA ビルド 12.8 以上 / compute capability (12,0) / CUDA カーネル実行 / mineru バージョン）。結果は `tests/results/feat-001_test_result.txt`。ユーザーの手動テストでも全件 PASS を確認
  - Codex レビュー: 4サイクルで収束（高3・中3を検出）。主要指摘は torch の推移的依存任せによるバージョン不定、Python 自動ダウンロードの禁止漏れ、cu130 インデックスのネットワーク要件記述漏れ、TECH_STACK.md 更新計画の漏れ
