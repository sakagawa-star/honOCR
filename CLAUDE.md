# CLAUDE.md

このファイルはClaude Codeがプロジェクトを理解するためのガイドです。

## セッション引き継ぎ

- セッション開始時にプロジェクトルートの `.claude/handovers/` ディレクトリを確認し、ファイルが存在すれば最新のものを読み込む
- セッション終了時や作業の区切りでは `/handover` の実行を促す

## プロジェクト概要

スキャンした書籍（PRML: パターン認識と機械学習）をOCRし、LLMに渡して勉強できる形式に変換するプロジェクト。数式を含む書籍のため、数式をLaTeXとして認識できるOCR（MinerU）を用いる。

### 目標

- 書籍のスキャンデータを **LaTeX数式入り Markdown**（章単位）に変換し、LLMが読める形にする（主目的）
- （任意）OCRの座標付きJSONを使い、閲覧用PDFに不可視テキスト層を埋め込む（副目的）

### 背景

- 閲覧用PDFをそのままLLMに渡したところ「読めない」と応答された（テキスト層なしの画像PDFのため）
- NDL OCR（ndlocr_cli / ndlocr-lite）は当初候補だったが、**数式を認識できない**ため不採用
- ndlocr_cli は CUDA 11.1 世代前提で、本環境の GPU（Blackwell, sm_120）では動作リスクがある
- VLM系OCRの比較（2026-08-05 調査）: PaddleOCR-VL-1.5/1.6（数式CDM 94.21、総合SOTA）、GLM-OCR（数式93.90だが多言語弱め）、MinerU 2.5（数式CDM 88.46）。書籍まるごとの変換パイプライン（レイアウト解析・読み順・Markdown出力・座標付きJSON）が最も整備されている **MinerU を採用**。商用最高峰は Mathpix（有料API、未採用）

## 技術スタック

- **言語**: Python 3.12.3
- **パッケージ管理**: uv
- **主要フレームワーク/ライブラリ**: MinerU 3.4.4（OCR本体）、img2pdf / pillow（前処理・OCR用PDF生成）
- **詳細**: `docs/TECH_STACK.md` を参照
- **注意**: GPU は RTX 5060 Ti 16GB（Blackwell, sm_120）。CUDA 12.8 以降のビルドが必須で、古い CUDA 前提のツールは動かない

## データ

`{BASE}` = `/home/sakagawa/work/Pattern_Recognition_and_Machine_Learning`（git 管理外・リポジトリ外）

- **スキャン原本**: `{BASE}/chapNN/out/`（NN = 00〜07）の `page-NN_{1L,2R}.tif` 計396枚（chap00: 20 / chap01: 84 / chap02: 70 / chap03: 44 / chap04: 48 / chap05: 70 / chap06: 36 / chap07: 24。2026-08-18 実測）。補正済み、600dpi、RGB、LZW可逆（章によりピクセル寸法は微差）。**OCR入力はこちらを使う**。白紙ページのみ 1-bit G4（約1KB）
- 各 `out/` の `chapNN_300dpi.pdf` は LLM閲覧用の非可逆圧縮PDF（テキスト層なし）。**OCR入力には使わない**（JPEGノイズが数式の添字認識に不利）
- **OCR 成果物**: `{BASE}/ocr/` 配下 — `pdf/`（入力PDF＋manifest）、`mineru-full/chapNN/run-NN{,-normalized}/`（実行別出力）、**`final/chapNN/`（最終成果物: Markdown＋content_list.json＋カラー images/。feat-005 で全8章構築済み）**

## ディレクトリ構成（主要部分）

```
honOCR/
├── CLAUDE.md               # 本ファイル
├── pyproject.toml          # uv プロジェクト定義（依存・[tool.uv] 設定・cu130 インデックス）
├── .python-version         # Python 3.12 固定
├── uv.lock                 # ロックファイル（自動生成）
├── docs/                   # ドキュメント（開発プロセス基準）
│   ├── BACKLOG.md
│   ├── CHANGELOG.md
│   ├── BUGFIX_STANDARD.md
│   ├── DESIGN_STANDARD.md
│   ├── REQUIREMENTS_STANDARD.md
│   ├── REVIEW_CRITERIA.md
│   ├── TECH_STACK.md
│   ├── codex-exec-ubuntu24-bwrap-fix.md
│   └── issues/             # 案件ディレクトリ
├── scripts/
│   ├── make_ocr_pdf.py     # TIF → OCR用可逆PDF生成 CLI（feat-002）
│   ├── normalize_punct.py  # MinerU 出力の句読点正規化 CLI（feat-004）
│   ├── ocr_dir.py          # OCR 一括実行 CLI: PDF生成→MinerU→正規化→機械確認（feat-006）
│   └── colorize_images.py  # 図画像のカラー再切出 CLI（feat-007）
└── tests/
    ├── test_env.py         # 環境スモークテスト（feat-001）
    ├── test_make_ocr_pdf.py  # 変換スクリプトのテスト（feat-002）
    ├── test_normalize_punct.py  # 正規化スクリプトのテスト（feat-004）
    ├── test_ocr_dir.py     # 一括実行スクリプトのテスト（feat-006）
    ├── test_colorize_images.py  # カラー再切出スクリプトのテスト（feat-007）
    └── results/            # テスト結果の保存先
```

## ドメイン知識

- MinerU の対応入力: pdf / png / jpeg / jp2 / webp / gif / bmp / jpg / tiff（**拡張子 `.tif` は非対応**、`.tiff` のみ）
- MinerU の内部処理は **200dpi** レンダリング（`DEFAULT_PDF_IMAGE_DPI = 200`）。画像入力も内部で JPEG(q=95) の PDF に変換される → 高解像度を渡しても 200dpi 相当で頭打ち。**重要なのは可逆（非JPEG）ソースを渡すこと**
- MinerU 3.4.4 のデフォルトバックエンドは `hybrid-engine`。事前検証で MinerU 3.4.4 + PyTorch 2.13 (cu130) が本環境の GPU を認識することを確認済み（2026-08-05。検証環境は削除済み）
- OCR入力用PDFは TIF から作り直す（300dpi グレースケール・Flate 可逆、章単位1ファイル）
- テキスト層埋め込み時の座標変換: TIF ピクセル → PDF ポイントは `pt = px × 72/600`（600dpi 原稿の場合）。閲覧用PDFのページサイズは 441.96 × 696.72 pt
- 書籍は日本語＋数式＋英語混在。NDL OCR 系は日本語専用で数式非対応
- 章とファイルの対応（確定）: chap-00 = `page-01_2R`〜`page-09_2R` の17ファイル、chap-01 = `page-10_2R`〜`page-42_1L` の64ファイル。除外3件（章頭白紙 `page-01_1L`・`page-10_1L`、第2章が写った `page-42_2R`）。詳細は feat-003 案件 README
- 本環境はプロキシ必須（大学ネットワーク）。MinerU 実行時は `no_proxy`/`NO_PROXY` に `localhost,127.0.0.1` を追加しないとローカルAPIヘルスチェックが 502 で失敗する
- MinerU の出力は句読点スタイルが揺れる（原本「，．」の約15%が「、。」に置換される。feat-003 で実測）。`scripts/normalize_punct.py` による「、→，」「。→．」の全文置換後処理で解消する（feat-004。MinerU 変換後は必ず適用する）
- OCR の一括実行（feat-006）: `uv run python scripts/ocr_dir.py <TIFディレクトリ> -o <出力ルート>` で PDF 生成 → MinerU → 正規化 → 機械確認まで1コマンド（ユーザーが Claude Code なしで実行できる）。入力PDF には manifest（TIF のパス・サイズ・mtime）が付き、一致時のみ再利用される
- MinerU content_list の `bbox` は 0–1000 正規化座標（ページ左上原点）。図ブロック（img_path を持つ image/chart/table）は `uv run python scripts/colorize_images.py <content_list> <TIFディレクトリ> -o <images出力先>` で原本 TIF からカラー再切出できる（feat-007。既定 1/3 縮小 = 旧画像と同等の表示サイズ。MinerU の生成画像はグレースケール PDF 由来のため必ず適用する）

## 開発方針

- **シンプルな機能を一つずつ作り、積み重ねて目的を達成する**
- 大きな機能を一度に作らない。小さく作って動作確認し、次の機能へ進む
- **環境を変更する操作（パッケージのインストール、モデルのダウンロード、長時間ジョブの開始）は、必ず事前にユーザーの承認を得る**。調査・提案までは自律的に行ってよい

### 機能追加フロー（feat-XXX 案件）

新機能を追加する場合、以下のフローを**厳守**する。**planモードは使わない**（通常モードで調査・計画を行う）。

1. **案件作成** → `docs/issues/feat-{number}-{slug}/` フォルダを作成し、`docs/BACKLOG.md` に追加する
2. **調査・計画** → 通常モードで既存コードを調査し、要求仕様書（`docs/REQUIREMENTS_STANDARD.md` 準拠）と機能設計書（`docs/DESIGN_STANDARD.md` 準拠）を作成する
3. **ドキュメント保存** → 要求仕様書を `docs/issues/{案件フォルダ}/requirements.md`、機能設計書を `docs/issues/{案件フォルダ}/design.md` にファイル保存する。**保存が完了するまで実装に進んではならない**
4. **レビュー（Codex → 人）** → 保存されたドキュメントを **Codex** でレビューする。実行方法は後述の「Codexによるレビューの実行方法」を参照。**まず Codex の再帰レビュー（修正→再レビュー）を重要度「高・中」がゼロに収束するまで回し、その後に人（ユーザー）がレビューする**（収束前に人レビューはしない）。レビュー実行時は `docs/REVIEW_CRITERIA.md` の基準に従うこと
5. **修正（必要な場合）** → レビューで問題があれば、再調査してドキュメントを更新する。**ステップ2〜4を問題がなくなるまで繰り返す**
6. **実装** → ドキュメント（要求仕様書・機能設計書・CLAUDE.md）を読んで実装する。実装は後述の「実装の実行方法（Sonnetサブエージェント）」に従い、Sonnet サブエージェントに委任する。実装完了後、「テスト」のルールに従ってテストを実行する
7. **手動テスト** → ユーザーがテストする。以下の問題があれば `docs/BUGFIX_STANDARD.md` に従って修正計画を `docs/issues/{案件フォルダ}/investigation.md` に追記する（上書きしない。イテレーション番号を付けて履歴を残す）。**ユーザーの承認を得た上で、ステップ2〜7を繰り返す**（コード修正はステップ6で行う。ステップ7で直接コードを編集してはならない）
   - 不具合の発見
   - 要求通りに実装されていない
   - 要求仕様作成時のヒアリング漏れ
8. **完了** → `docs/BACKLOG.md` のステータスを Closed に更新する。`docs/CHANGELOG.md` に完了内容を記録する。ファイルの追加・削除があった場合は `CLAUDE.md` のディレクトリ構成を最新に更新する。`README.md` に記載済みの内容（コマンド、CLIオプション、入力/出力形式、既定値、実行環境・依存条件）に変更があった場合は `README.md` を最新に更新する

### 不具合修正フロー（bug-XXX 案件）

既存機能の不具合を修正する場合、以下のフローを**厳守**する。

1. **案件作成** → `docs/issues/bug-{number}-{slug}/` フォルダを作成し、`docs/BACKLOG.md` に追加する。案件フォルダの `docs/issues/bug-{number}-{slug}/README.md` に不具合の概要と再現手順を記録する（ルートの `README.md` ではない）
2. **調査・修正計画** → `docs/BUGFIX_STANDARD.md` に従い、既存コードを調査する。修正計画を `docs/issues/{案件フォルダ}/investigation.md` に記録する。**この時点でコードを編集してはならない**
3. **ドキュメント保存** → investigation.md の保存を確認する。調査の結果 `requirements.md` / `design.md` の修正が必要になった場合は、それらも併せて保存する。**保存が完了するまで実装に進んではならない**
4. **レビュー（Codex → 人）** → 保存されたドキュメントを **Codex** でレビューする。実行方法は後述の「Codexによるレビューの実行方法」を参照。**まず Codex の再帰レビュー（修正→再レビュー）を重要度「高・中」がゼロに収束するまで回し、その後に人（ユーザー）がレビューする**（収束前に人レビューはしない）。レビュー実行時は `docs/REVIEW_CRITERIA.md` の基準に従うこと
5. **修正（必要な場合）** → レビューで問題があれば、再調査してドキュメントを更新する。**ステップ2〜4を問題がなくなるまで繰り返す**
6. **実装** → 承認された修正計画に沿ってコードを修正する。実装は後述の「実装の実行方法（Sonnetサブエージェント）」に従い、Sonnet サブエージェントに委任する。計画にない変更が必要になった場合は中断して報告する
7. **手動テスト** → ユーザーがテストする。問題があれば `docs/BUGFIX_STANDARD.md` に従って investigation.md にイテレーション番号を付けて追記し、**ユーザーの承認を得た上で、ステップ2〜7を繰り返す**（コード修正はステップ6で行う。ステップ7で直接コードを編集してはならない）
8. **完了** → `docs/BACKLOG.md` のステータスを Closed に更新する。`docs/CHANGELOG.md` に完了内容を記録する。ファイルの追加・削除があった場合は `CLAUDE.md` のディレクトリ構成を最新に更新する。`README.md` に記載済みの内容（コマンド、CLIオプション、入力/出力形式、既定値、実行環境・依存条件）に変更があった場合は `README.md` を最新に更新する

### ドキュメント更新フロー（update-XXX 案件）

開発プロセスを定める運用ドキュメント（`CLAUDE.md`、`docs/` 直下の基準書・BACKLOG・CHANGELOG、`.gitignore` 等）の改訂は **update-XXX 案件**として扱い、以下のフローを**厳守**する。典型例:

- 本プロジェクトのコピー元テンプレートリポジトリ（開発ドキュメントテンプレート）の改訂の取り込み
- ドキュメント間の二重管理・不整合の解消、運用ルールの新設・変更

**ソースコード・テストコードの変更は含まない。** 作業中にコード変更が必要と判明した場合は中断し、feat/bug 案件として起票し直す。個別機能のドキュメント（案件フォルダ内の requirements.md 等）の修正は元案件側で扱い、update 案件にはしない。

要求仕様書・機能設計書は作らず、README.md（調査）と design.md（反映設計）の2点で代替する。

1. **案件作成** → `docs/issues/update-{number}-{slug}/` フォルダを作成し、`docs/BACKLOG.md` に追加する。slug は変更の目的がわかる名前にする（例: `adopt-dev-template`）
2. **調査** → 現状と変更理由を調査し、案件フォルダの `README.md` に記録する。テンプレート取り込みの場合は反映元パス・コミットID・差分の全量と、取り込む/取り込まない の選別と理由を書く。**この時点で反映先を編集してはならない**
3. **設計・保存** → 変更対象ファイルごとに「どのセクションを・どう変えるか」を `design.md` に書いてファイル保存する。自己完結（/clear 後でも design.md だけで反映作業ができる）・曖昧表現禁止。全置換に後処理が伴う場合は、変更方式の一覧・該当セクション・実施手順のすべてに明記する。完了処理（BACKLOG・CHANGELOG の更新）も設計に含める。**保存が完了するまで反映に進んではならない**
4. **レビュー（Codex → 人）** → 「Codexによるレビューの実行方法」に従う（バックグラウンド実行、`-o` + full.log 分離、`resume` による逐次再レビュー、重要度「高・中」ゼロ収束後に人レビュー）。レビュー対象は `README.md` と `design.md`。レビュー観点は次の3点を明示して依頼する:
   1. 反映計画の自己完結性（design.md だけで作業ができるか）
   2. 情報の喪失（削除・置換対象に、他所に存在しない情報が含まれていないか）
   3. 変更後のドキュメント間整合性（参照切れ、矛盾、案件の漏れ・重複）
5. **反映** → design.md に厳密に従って編集する。実装は Claude Code 本体が行ってよい（転記・削除中心で Sonnet 委任のオーバーヘッドに見合わないため。分量が大きい機械的変更では委任も可。どちらにするかは design.md に明記する）。設計にない変更が必要になったら中断してステップ2に戻る。反映後 `git diff` で「意図した変更のみか・保持対象が変わっていないか」を検証する
6. **完了** → `docs/BACKLOG.md` のステータスを Closed に更新する。`docs/CHANGELOG.md` に完了内容を記録し、案件 README のステータスを Closed に更新する。ファイルの追加・削除があった場合は `CLAUDE.md` のディレクトリ構成を最新に更新する
7. **テスト** → コード変更がないためテスト（自動・手動とも）は不要（不要であることを design.md に明記する）

#### 運用メモ

- 汎用性のある改善は、完了後にコピー元の開発ドキュメントテンプレートリポジトリへの還元（テンプレート側の update-XXX 案件）を検討する
- ルートの `.gitignore` がグローバル gitignore（`~/.gitignore_global`）の影響で未追跡になる環境では、コミットに含める際に `git add -f` が必要

### 実験・検証の進め方（予測→実行→照合）

数値判定を伴う実験・検証（案件の調査フェーズでの実験、閾値・パラメータの妥当性検証、性能測定等）では、以下のプロトコルを**厳守**する。

1. **判定基準の事前定義**: 実験の実行前に「答える問い」「判定閾値」「合格ライン（何%・何件なら合格か）」を数値で criteria 文書（案件フォルダ配下、例: `docs/issues/{案件フォルダ}/experiments/{実験名}/criteria.md`）に文書化する。数値で定義できない場合は、その実験を「基準を測ることがゴールの実験」と明示的に再定義する（未知の量を既知のように扱わない）。criteria 文書は実行前に「Codexによるレビューの実行方法」に従って Codex レビューを行い（レビュー依頼時に対象の criteria 文書と関連ドキュメントを明示する。結果は案件フォルダの `reviews/` に案件の連番を進めて保存）、重要度「高・中」ゼロに収束させてから実験に着手する（criteria lock）
2. **直前予測**: 各フェーズの実行直前に、入出力の予測を数値で実験ログ（例: `experiment_log.md`）に記録してから実行する。予測は前段の実測結果を使って直前に立てる（全フェーズ一括の事前予測はしない——前段の結果で後段の内容が変わるため）。予測する項目の枠（何を予測するか）は criteria 文書に事前定義してよい（値はフェーズ直前に確定する）
3. **照合**: 実行後に予測と実測を照合して実験ログに記録する。乖離した場合はそのフェーズの前提・理解を疑い、原因を特定してから次フェーズに進む
4. **事後解釈の禁止**: 基準のない実験は「測定」であって「判定」ではない。結果を見てから合格ラインを定めることや、事前基準にない条件を付けて合格扱いにすること（事後解釈での Go/No-Go 判定）を行わない

対象外: 通常の実装・自動テスト（自動テストはテストコード自体が期待値＝予測の文書化に当たる）、および数値判定を伴わない調査（コード読解、ドキュメント調査等）。

### ドキュメント作成ルール

- **実装（反映）前に必ず案件種別に応じたドキュメントを作成し、案件フォルダにファイル保存すること**
  - feat: 要求仕様書（`requirements.md`、`docs/REQUIREMENTS_STANDARD.md` 準拠）と機能設計書（`design.md`、`docs/DESIGN_STANDARD.md` 準拠）
  - bug: 修正計画（`investigation.md`、`docs/BUGFIX_STANDARD.md` 準拠）。要求仕様書・機能設計書の変更が必要な場合はその変更案も併せて保存する
  - update: 調査記録（`README.md`）と反映設計書（`design.md`）。詳細は「ドキュメント更新フロー（update-XXX 案件）」に従う
- ドキュメントが保存されていない場合は、**実装を中止**する
- レビュー実行時は `docs/REVIEW_CRITERIA.md` の基準に従うこと
- ドキュメントは `docs/issues/{案件フォルダ}/` に置く。ファイル名は上記の案件種別ごとの必須ドキュメント定義に従う
- **/clear 後でも実装がスムーズにできるよう、必要な情報を全て記述する**
- 暗黙知に頼らず、**自己完結したドキュメント**にする（前の会話コンテキストがなくても実装できること）
- ライブラリの追加・変更・削除を行った場合は `docs/TECH_STACK.md` も更新すること
- 新規ライブラリ導入時は用途・選定理由・バージョンを `TECH_STACK.md` に追記すること

### 案件ディレクトリ構成

```
docs/issues/
└── {type}-{number}-{slug}/    # 例: bug-001-xxx, feat-001-yyy, update-001-zzz
    ├── README.md              # 概要、ステータス、再現手順
    ├── requirements.md        # 要求仕様書（機能追加時、REQUIREMENTS_STANDARD.md 準拠）
    ├── design.md              # 機能設計書（機能追加時、DESIGN_STANDARD.md 準拠）
    ├── investigation.md       # 不具合の調査・修正計画（BUGFIX_STANDARD.md 準拠）
    └── reviews/               # Codexレビューの結果（codex-NN.result.md のみ git 管理。full.log は gitignore）
```

update 案件は requirements.md / investigation.md を持たず、README.md（調査）・design.md（反映設計）・reviews/ で構成される。

### 命名規則

- フォルダ名は英語で統一（例: `bug-001-input-validation`）
- 案件フォルダは完了後も削除・移動しない

### Codexによるレビューの実行方法

機能追加・不具合修正・ドキュメント更新フローのステップ4（レビュー）では、Claude Code 自身が `codex exec` コマンドを実行して Codex にレビューさせる。Subagent は使わない。**Codex は逐次（前回セッションを `resume` で継続）で回し、重要度「高・中」がゼロに収束してから人レビューに進む**。並列にはしない（再レビューの収束確認＝「前回指摘が直ったか」の判定に前回文脈の引き継ぎが必要なため。初回の発見網羅性を上げたい大規模案件でのみ「初回だけ多観点並列→以降逐次」を検討）。

使用するモデルは `~/.codex/config.toml` のデフォルト設定に従う。本ファイルのコマンドにはモデル指定（`-m`）を書かない。モデルを切り替えたい場合は `~/.codex/config.toml` を編集する（全プロジェクト共通で反映される）。

**実行はバックグラウンドで行う**: Codex のレビューは reasoning effort の設定によっては1回10分を超えることがあり、Claude Code の Bash ツールのタイムアウト上限（最大10分）に抵触する。`codex exec` はバックグラウンド実行（`run_in_background`）とし、完了通知後に `codex-NN.result.md` を読んで指摘を確認する。`-o` による結果のファイル保存はこの運用を前提としている。

> **Ubuntu 24系で `bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted` が出る場合**は、`docs/codex-exec-ubuntu24-bwrap-fix.md` を参照して AppArmor プロファイルを追加すること（ホスト側の user namespace 制限が原因。Codex のバグではない）。

#### 出力の保存（結果と過程を分離）

- レビュー結果と過程ログは **案件フォルダの `docs/issues/{案件フォルダ}/reviews/`** に保存する（事前に `mkdir -p` する）。
- **初回から `-o`（`--output-last-message`）を必ず付ける**。`-o` で最終レビュー結果だけを `codex-NN.result.md` に書き、stdout 全体（過程ログ）は `> codex-NN.full.log 2>&1` で別ファイルに保存する（混在させない）。
- ファイル名はレビュー回ごとに連番（`codex-01`, `codex-02`, …）。
- `result.md` のみ git 管理し、`full.log` は `.gitignore`（`docs/issues/*/reviews/*.full.log`）でローカルのみとする（リポジトリ肥大回避）。
- `result.md` には Codex の生出力に加え、Claude Code の対応方針を追記してよい（冒頭に日付・対象・session id・初回/再の定型メタを置くと追いやすい）。

#### 初回レビュー（機能追加の場合）

```bash
mkdir -p docs/issues/{案件フォルダ}/reviews
codex exec -o docs/issues/{案件フォルダ}/reviews/codex-01.result.md \
  "docs/REVIEW_CRITERIA.md の基準に従い、以下のドキュメントをレビューせよ: docs/issues/{案件フォルダ}/requirements.md docs/issues/{案件フォルダ}/design.md 。瑣末な点へのクソリプはしないで、致命的な点のみ指摘して。発見した問題を重要度(高/中/低)で分類し、修正提案とともに報告すること。" \
  > docs/issues/{案件フォルダ}/reviews/codex-01.full.log 2>&1
```

#### 初回レビュー（不具合修正の場合）

```bash
mkdir -p docs/issues/{案件フォルダ}/reviews
codex exec -o docs/issues/{案件フォルダ}/reviews/codex-01.result.md \
  "docs/REVIEW_CRITERIA.md および docs/BUGFIX_STANDARD.md の基準に従い、以下のドキュメントをレビューせよ: docs/issues/{案件フォルダ}/investigation.md 。requirements.md / design.md を変更した場合はそれらもレビュー対象に含めること。瑣末な点へのクソリプはしないで、致命的な点のみ指摘して。発見した問題を重要度(高/中/低)で分類し、修正提案とともに報告すること。" \
  > docs/issues/{案件フォルダ}/reviews/codex-01.full.log 2>&1
```

#### 初回レビュー（ドキュメント更新の場合）

```bash
mkdir -p docs/issues/{案件フォルダ}/reviews
codex exec -o docs/issues/{案件フォルダ}/reviews/codex-01.result.md \
  "以下のドキュメントをレビューせよ: docs/issues/{案件フォルダ}/README.md docs/issues/{案件フォルダ}/design.md 。レビュー観点は次の3点: (1) 反映計画の自己完結性（design.md だけで作業ができるか） (2) 情報の喪失（削除・置換対象に、他所に存在しない情報が含まれていないか） (3) 変更後のドキュメント間整合性（参照切れ、矛盾、案件の漏れ・重複）。瑣末な点へのクソリプはしないで、致命的な点のみ指摘して。発見した問題を重要度(高/中/低)で分類し、修正提案とともに報告すること。" \
  > docs/issues/{案件フォルダ}/reviews/codex-01.full.log 2>&1
```

#### 再レビュー（共通）

ドキュメントを更新して再レビューする場合、最初のレビューの文脈を保持するため**同一セッションを `resume` で継続**する。セッション ID は `codex-01.full.log` 冒頭の `session id:` 行に記録されるので、それを明示指定する（`--last` は別の codex 実行が挟まると意図しないセッションを掴む恐れがあるため使わない）。連番を1つ進める:

```bash
codex exec resume {SESSION_ID} -o docs/issues/{案件フォルダ}/reviews/codex-02.result.md \
  "ドキュメントを更新したので再レビューして。前回と同じ基準で。前回指摘が解消されたかを含めて確認して。瑣末な点へのクソリプはしないで、致命的な点のみ指摘して。重要度(高/中/低)で分類し、修正提案とともに報告すること。" \
  > docs/issues/{案件フォルダ}/reviews/codex-02.full.log 2>&1
```

**注意**: `resume`（セッション継続）を使わないと最初のレビューの文脈が失われる。`-o` と `> ...full.log 2>&1` は毎回付け、連番（`codex-03`, `codex-04`, …）を進める。

#### レビュー終了条件

重要度「高」「中」の指摘がゼロに収束するまで、修正 → 再レビュー（連番を進める）を繰り返す。**収束したら人（ユーザー）レビューに進む**（収束前に人レビューはしない）。

### 実装の実行方法（Sonnetサブエージェント）

機能追加・不具合修正フローのステップ6（実装）は、Claude Code 自身が直接コードを書くのではなく、Agent ツールで **model: sonnet** を指定したサブエージェントに委任する。

#### サブエージェントへの指示に必ず含めること

1. **必読ドキュメントと読む順序**: CLAUDE.md → 案件ドキュメント（機能追加は `requirements.md` と `design.md`、不具合修正は `investigation.md` と、変更した場合は関連する `requirements.md` / `design.md` も必読）→ 変更対象コード → 参考にする既存テスト
2. **厳密準拠の指示**: 設計書・修正計画に厳密に従うこと。書かれていない独自判断・改善・リファクタは一切禁止
3. **想定外事象の扱い**: 想定外の事象（設計書どおりに実装できない、ドキュメントと実コードの矛盾、テストが通らない等）が発生したら、**その場で回避策を実装せず直ちに中断**し、何が起きたか・どこまで完了したかを報告して終了すること。報告を受けたら「調査・計画 → requirements.md / design.md（または investigation.md）の修正」のステップに**必ず戻る**（レビューを経てから実装を再開する）
4. **検証まで実施**: テストの全件実行（「テスト」のルールに従う）、`tests/results/{type}-{number}_test_result.txt` への出力保存、ドキュメントに定義された動作確認（実データ実行等）
5. **禁止事項**: git commit / push はサブエージェントに行わせない。BACKLOG.md / CHANGELOG.md / CLAUDE.md / README.md の更新も行わせない（完了ステップ8で Claude Code 本体が行う）
6. **報告形式**: 変更ファイル一覧、テスト結果サマリ、動作確認結果、想定外事象の有無

#### 委任しない作業

- 調査・計画、ドキュメント作成、Codexレビューの実行と指摘反映、完了処理（ステップ8）、git 操作は Claude Code 本体が行う

### コードレビュー

- レビューでは重要度(高/中/低)で分類し、修正提案とともに報告する
- 重要度:高と中は修正対象とする
- レビュー基準の詳細は `docs/REVIEW_CRITERIA.md` を参照

### テスト

- テストは `tests/` ディレクトリに置く
- テスト実行コマンド: `uv run pytest -v`
- **テスト結果は `tests/results/` にファイル保存する**
  - ファイル名：`{type}-{number}_test_result.txt`（例：`feat-001_test_result.txt`）
  - 内容：テストコマンドの出力をそのまま保存する

## Claude Code 運用ルール

### Bash 実行時のルール

- **`cd <path> && <command>` の連結は禁止。** Bashツールはプロジェクト作業ディレクトリで動くため `cd` は不要。連結すると先頭トークンが `cd` になり、`.claude/settings.json` / `.claude/settings.local.json` のallowlist（例: `Bash(codex exec *)`、`Bash(git status)`）が一致せず、毎回パーミッションプロンプトが発生する
- 別ディレクトリで実行する必要がある場合は、コマンド側のオプションを使う（例: `git -C <path> status`、`make -C <path> ...`）
- どうしても複数コマンド連結が必要な場合も、先頭トークンが安全・許可済みであるかを確認してから書く

### git 操作の実行方法（Opusサブエージェント）

git のコミット・プッシュは、Claude Code 本体が直接実行するのではなく、Agent ツールで **model: opus** を指定したサブエージェントに委任する。

#### サブエージェントへの指示に必ず含めること

1. **コミット内容の背景**: 何をなぜ変更したか（コミットメッセージ作成に必要な情報）を要約して渡す
2. **ステージ対象の明示**: コミットに含めるファイルを列挙する。`.claude/settings.local.json` と `.claude/handovers/` 配下は含めない
3. **コミットメッセージ**: 日本語。末尾トレーラーは `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`
4. **Bashルールの継承**: `cd <path> && <command>` 連結禁止、`git -C <path> ...` 形式を使う
5. **失敗時の扱い**: コンフリクト・push拒否等が起きたら対処（rebase, reset, force push 等）せず、状況をそのまま報告して終了する

#### 委任しない作業

- コミット可否の判断・タイミング（ユーザーの指示を受けて Claude Code 本体が起動する）
- コミット後の結果検証（`git log -1 --stat` 等での確認は本体が行う）

## コーディング規約

- **命名規則**:
  - クラス名 PascalCase / 関数・メソッド snake_case / 定数 UPPER_SNAKE_CASE
  - ファイル名・モジュール名は snake_case
- **型ヒント**: 関数シグネチャに型ヒントを使用
- スクリプトの入出力パス・パラメータはハードコードせず、CLI引数（argparse）で受け取る

## 完了済み案件

詳細は `docs/BACKLOG.md`（一覧）および `docs/CHANGELOG.md`（リリース履歴）を参照。
