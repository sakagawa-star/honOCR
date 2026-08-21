# BACKLOG

## ロードマップ

- フェーズ1: 環境構築（uv プロジェクト初期化、MinerU 導入）
- フェーズ2: TIF → OCR用可逆PDF（300dpiグレースケール・章単位1ファイル）生成スクリプト
- フェーズ3: MinerU 試行（chap-00 の数ページ）→ 日本語本文・数式LaTeXの品質確認
- フェーズ4: 全ページ処理 → 章単位 Markdown 生成（LLM学習用の主成果物）
- フェーズ5（任意）: 座標付きJSONを使い、既存PDFへ不可視テキスト層を挿入

## 案件一覧

| ID | 概要 | ステータス | 備考 |
|---|---|---|---|
| feat-001 | uv 環境構築と MinerU 導入 | Closed | 2026-08-17 完了。案件フォルダ: feat-001-env-setup-mineru |
| feat-002 | TIF → OCR用可逆PDF生成スクリプト | Closed | 2026-08-17 完了。案件フォルダ: feat-002-tif-to-ocr-pdf |
| feat-003 | MinerU 試行（章単位PDFの品質確認） | Closed | 2026-08-17 完了（判定 No-Go、対策は feat-004）。案件フォルダ: feat-003-mineru-trial |
| feat-004 | 句読点正規化の後処理と再判定 | Closed | 2026-08-17 完了（再判定 Go、ユーザー二次確認済み）。feat-003 No-Go 対策。案件フォルダ: feat-004-punct-normalize |
| feat-005 | 全スキャンデータの本処理（ディレクトリ単位の高精度 OCR） | Open | フェーズ4。chap00〜07 の全TIF 計396枚（除外なし）を OCR。2026-08-18 ユーザー指摘でスコープを「入力への忠実な OCR」に是正。chap00〜03 処理・カラー化済み。chap04〜07 はユーザーが ocr_dir.py で実行予定、その後 final 構築。案件フォルダ: feat-005-full-conversion |
| feat-006 | OCR 一括実行スクリプト（ocr_dir.py） | Closed | 2026-08-18 完了。PDF生成→MinerU→正規化→機械確認を1コマンド化（Claude Code 不要）。案件フォルダ: feat-006-ocr-pipeline-cli |
| feat-007 | 図画像のカラー再切出（colorize_images.py） | Closed | 2026-08-18 完了（差し戻し1回: 既定1/3縮小を追加）。bbox で原本TIF からカラー再切出。案件フォルダ: feat-007-colorize-images |
