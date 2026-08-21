# feat-006: OCR 一括実行スクリプト（ocr_dir.py）

- **ステータス**: Closed（2026-08-18 完了）
- **種別**: feat（機能追加）

## 概要

TIF ディレクトリを指定するだけで「PDF 生成 → MinerU 変換 → 句読点正規化 → 機械確認」を一括実行する CLI `scripts/ocr_dir.py` を追加する。

## 背景

- feat-005 の本処理では、各ステップ（`make_ocr_pdf.py` → `mineru` → `normalize_punct.py` → 検証）を Claude Code が手動でつないで実行している。**ユーザーから「OCR のたびに Claude を通すのは使いづらい。Claude Code の使用量を無駄に使いたくない」との指摘があり（2026-08-18）**、ユーザー自身のターミナルだけで完結する一括 CLI を作ることになった
- 検証ロジック（page_idx 検査・正規化のコードポイント比較）は現在スクラッチパッドの使い捨てスクリプトにあり、恒久化されていない。本案件でスクリプトに組み込む
- 出力レイアウトは feat-005 と同一（`{ROOT}/pdf/`・`{ROOT}/mineru-full/<name>/run-NN/`・`run-NN-normalized/`）とし、feat-005 の残り（chap03〜07）を本スクリプトで実行しても feat-005 の成果物体系に組み込めるようにする

## 関連ドキュメント

- `requirements.md`: 要求仕様書
- `design.md`: 機能設計書
- feat-002: `make_ocr_pdf.py`（PDF 生成）、feat-004: `normalize_punct.py`（正規化）と機械確認アルゴリズム、feat-005: 本処理の手順・出力レイアウト

## 動作確認（2026-08-18）

- `uv run python scripts/ocr_dir.py {BASE}/chap03/out -o {ROOT} --overwrite-pdf` → **PASS** pages=44 blocks=505 replaced=165+165、4分35秒、終了コード 0
- 出力レイアウトが feat-005 design §6 と一致することを確認（pdf＋manifest / run-01 / run-01.log / run-01-normalized）。正規化後の残存「、」「。」0 件
- 自動テスト: 41件全 PASS（`tests/results/feat-006_test_result.txt`）
