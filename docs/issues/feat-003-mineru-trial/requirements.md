# feat-003 要求仕様書: MinerU 試行（章単位PDFの品質確認）

## 1. プロジェクト概要

- **何を作るのか**: 章単位の OCR用PDF（chap-00 / chap-01）を生成し、chap-01 を MinerU で Markdown + JSON に変換して、日本語本文・数式 LaTeX の品質を事前定義基準で判定する
- **なぜ作るのか**: フェーズ4（全章の Markdown 化）に進む前に、MinerU の出力品質が目的（LLM に読ませて勉強する）に足りるかを確認するため。品質不足のまま全量処理すると手戻りが大きい
- **誰が使うのか**: 本リポジトリの開発者（ユーザーおよび Claude Code）
- **どこで使うのか**: ローカルマシン（feat-001 で構築した uv 環境。GPU: RTX 5060 Ti 16GB を使用）

## 2. 用語定義

| 用語 | 定義 |
|---|---|
| 章単位PDF | feat-002 の `scripts/make_ocr_pdf.py` で生成する OCR用PDF。chap-00（17ページ）と chap-01（64ページ）。章とファイルの対応は案件 README.md に確定記録がある |
| hybrid-engine | MinerU 3.4.4 のデフォルトバックエンド。試行はこの既定設定で行う |
| 独立数式 | Markdown 出力中の display math（`$$...$$` で囲まれたブロック）。行内数式（`$...$`）と区別する |
| criteria 文書 | 実行前に判定基準を数値で固定する文書（`experiments/trial-quality/criteria.md`）。CLAUDE.md「実験・検証の進め方」に従う |
| 実験ログ | 予測と実測の照合記録（`experiments/trial-quality/experiment_log.md`） |
| Go/No-Go | フェーズ4に進んでよいか（Go）、対策の再検討が必要か（No-Go）の判定 |

機能設計書・コード内でも上記と同じ用語を使う。

## 3. 機能要求一覧

### FR-001: 章単位PDF の生成

- **機能名**: 章単位PDF の生成
- **概要**: 確定済みの章対応（README.md 記載）に従い、feat-002 のスクリプトで chap-00 / chap-01 の OCR用PDF を生成する
- **入力**: chap-00 用 TIF 17ファイル、chap-01 用 TIF 64ファイル（対応は README.md の確定記録に従う）
- **出力**: `/home/sakagawa/work/Pattern_Recognition_and_Machine_Learning/chap01/out/ocr/chap-00_gray300.pdf`（17ページ）、`.../ocr/chap-01_gray300.pdf`（64ページ）
- **受け入れ基準**: 両 PDF が生成され、`pdfinfo` のページ数が 17 / 64 と一致する

### FR-002: MinerU による変換の実行

- **機能名**: MinerU による変換の実行
- **概要**: chap-01_gray300.pdf を MinerU（hybrid-engine、既定設定）で変換し、Markdown と JSON 出力を得る。初回実行に伴うモデルのダウンロードを含む
- **入力**: `chap-01_gray300.pdf`（64ページ。数式・日本語本文を多く含む章）
- **出力**: `/home/sakagawa/work/Pattern_Recognition_and_Machine_Learning/chap01/out/ocr/mineru-trial/` 配下の MinerU 出力一式（Markdown、JSON、切り出し画像）
- **受け入れ基準**: MinerU が終了コード 0 で完了し、(1) Markdown ファイルが1個以上生成され、その中に `$$` で囲まれた独立数式が1個以上含まれる、(2) 各ブロックのページ番号情報（page_idx 相当）を含む JSON（content list）が1個以上生成されている

### FR-003: 品質判定

- **機能名**: 品質判定
- **概要**: criteria 文書に事前定義した基準・サンプリング方法・合格ラインに従い、chap-01 の出力品質を判定して Go/No-Go を決める
- **入力**: FR-002 の Markdown 出力、FR-002 の content list JSON（ブロックと原本ページの対応付けに使用）、原本ページ画像（照合用）
- **出力**: 実験ログ（予測・実測・照合・判定を記録）
- **受け入れ基準**: criteria 文書のすべての判定項目について実測値が記録され、Go/No-Go が criteria 文書の事前定義どおりに決定されている（事後解釈をしない）

## 4. 非機能要求

- **パフォーマンス**: MinerU の変換時間そのものは判定対象にしない（実測を記録するのみ。フェーズ4の計画材料にする）
- **対応環境**: feat-001 の uv 環境 + GPU（RTX 5060 Ti 16GB）。モデルダウンロードのため HTTPS アクセスが必要
- **ディスク**: モデルダウンロードと出力の合計で 15GB 以下（実行前の空き容量 30GB 以上を前提とする）
- **信頼性**: 原本TIF・生成済みファイルへの書き込みを行わない（新規出力のみ）。MinerU の実行はバックグラウンドで行い、失敗時は出力を残したまま中断・報告する
- **セキュリティ**: 該当なし

## 5. 制約条件

- **使用必須**: feat-001 で導入済みの `mineru[core]==3.4.4`（バックエンドは既定の hybrid-engine。オプション変更をしない）、feat-002 の `scripts/make_ocr_pdf.py`
- **追加ライブラリ**: なし（新規インストールはモデルファイルのダウンロードのみ）
- **実験プロトコル**: CLAUDE.md「実験・検証の進め方」を厳守する。criteria 文書を Codex レビューで収束（criteria lock）させてから実行し、各フェーズ直前に予測を記録し、実測と照合する
- **承認ゲート**: モデルのダウンロードと MinerU の実行（長時間ジョブ）は環境変更操作にあたるため、実装開始のユーザー承認を得てから行う
- **スコープ外**: chap-00 の MinerU 変換（前付け中心で数式が少なく、品質判定は chap-01 で足りる。フェーズ4で処理する）、パラメータチューニング（No-Go の場合の対策検討は別案件）、テキスト層埋め込み（フェーズ5）
- **テストデータ**: 原本TIF・生成PDF は git 管理外・リポジトリ外

## 6. 優先順位

| 要求ID | MoSCoW |
|---|---|
| FR-001 | Must |
| FR-002 | Must |
| FR-003 | Must |

MVP = FR-001〜FR-003 のすべて（本案件は3要求で完結する）。
