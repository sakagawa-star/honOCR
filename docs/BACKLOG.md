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
| feat-005 | 全スキャンデータの本処理（ディレクトリ単位の高精度 OCR） | Closed | 2026-08-21 完了。chap00〜07 計396枚を OCR・正規化・カラー化し final を構築（全8章 PASS、ユーザー確認済み）。2026-08-18 にスコープを「入力への忠実な OCR」に是正。案件フォルダ: feat-005-full-conversion |
| feat-006 | OCR 一括実行スクリプト（ocr_dir.py） | Closed | 2026-08-18 完了。PDF生成→MinerU→正規化→機械確認を1コマンド化（Claude Code 不要）。案件フォルダ: feat-006-ocr-pipeline-cli |
| feat-007 | 図画像のカラー再切出（colorize_images.py） | Closed | 2026-08-18 完了（差し戻し1回: 既定1/3縮小を追加）。bbox で原本TIF からカラー再切出。案件フォルダ: feat-007-colorize-images |
| feat-008 | MinerU 出力の HTML 表を Markdown パイプテーブルに変換（html_table_to_md.py） | Closed | 2026-08-24 完了。VS Code プレビューで表内数式が描画されない問題（chap01 表 1.1/1.2）の対処。既存データ適用済み・ocr_dir.py 組み込み済み。付随して normalized md 2件の損傷を発見し final から復旧。案件フォルダ: feat-008-html-table-to-md |
| feat-009 | MinerU 出力から欠落する脚注（訳注）の Markdown 挿入（insert_footnotes.py） | Closed | 2026-08-25 完了。MinerU が md に出力しない page_footnote 型（chap01=訳注1〜13 等）を content_list から組み立てて挿入。既存データ適用済み・ocr_dir.py 組み込み済み。ユーザー手動テストで注釈4・5 の表示を確認。案件フォルダ: feat-009-insert-footnotes |
| feat-010 | 手動修正の永続化: 修正定義ファイルの機械適用（apply_fixes.py） | Closed | 2026-08-25 完了。修正を old→new の定義ファイル（{BASE}/ocr/fixes/、リポジトリ外）として管理しパイプライン最終段で機械適用。初期データとして式番号誤結合5件を修正・適用済み。ユーザー実データ確認済み。案件フォルダ: feat-010-apply-fixes |
| feat-011 | 他書籍対応: 正規化・脚注処理の一般化（句読点スタイル選択・中国語字正規化・脚注 `*N` 対応） | Closed | 2026-08-28 完了。第2の書籍『プログラミングのための確率統計』の OCR 化に向けた一般化。`--punct-style {comma,touten}`・中国語字8種の字形正規化・JIS 外漢字の警告・脚注 `*N` 対応。ユーザー手動テスト済み。案件フォルダ: feat-011-multi-book-normalization |
| feat-012 | final ディレクトリ構築の自動化（build_final.py） | Closed | 2026-08-28 完了。feat-005 で手作業だった「カラー再切出 → final/chapNN/ への集約 → 検証」を CLI 化し、ocr_dir.py に `--final` として章単位で組み込んだ。PRML 8章で既存 final とバイト同一を確認。ユーザー実機テスト済み。案件フォルダ: feat-012-build-final |
