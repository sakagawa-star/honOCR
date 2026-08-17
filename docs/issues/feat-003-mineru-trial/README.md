# feat-003: MinerU 試行（章単位PDFの品質確認）

- **ステータス**: Closed（2026-08-17 完了。判定 **No-Go**、対策は feat-004。詳細は experiments/trial-quality/experiment_log.md）
- **種別**: feat（機能追加。品質判定を伴うため「実験・検証の進め方」プロトコルを併用）
- **概要**: 章単位の OCR用PDF（chap-00 / chap-01）を生成して MinerU にかけ、日本語本文・数式 LaTeX の出力品質を事前定義した基準（criteria.md）で判定する。フェーズ4（全章 Markdown 化の本処理）へ進む Go/No-Go を決める。ロードマップのフェーズ3
- **章とファイルの対応（2026-08-17 ユーザー回答＋機械検証で確定）**:
  - 原本TIF 84 ファイル（辞書順）のうち、位置1 `page-01_1L.tif`（章頭白紙）・位置19 `page-10_1L.tif`（章頭白紙）・位置84 `page-42_2R.tif`（第2章が写ったページ）の3件は章に属さない（既存閲覧用PDFでも除外されている）
  - **chap-00 = 位置2〜18 の17ファイル（`page-01_2R.tif`〜`page-09_2R.tif`）**
  - **chap-01 = 位置20〜83 の64ファイル（`page-10_2R.tif`〜`page-42_1L.tif`）**
  - 傍証: 章内白紙3枚（`page-03_1L` / `page-05_1L` / `page-06_1L`）の位置が既存閲覧用PDF chap-00 の白紙ページ位置（4・8・10ページ目）と一致
- **ドキュメント**: [requirements.md](requirements.md) / [design.md](design.md) / [experiments/trial-quality/criteria.md](experiments/trial-quality/criteria.md)
