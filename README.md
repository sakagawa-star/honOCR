# honOCR

スキャンした書籍（PRML: パターン認識と機械学習）を OCR し、LLM に渡して勉強できる形式に変換するプロジェクト。数式を含む書籍のため、数式を LaTeX として認識できる OCR（[MinerU](https://github.com/opendatalab/MinerU)）を用いる。

## 目標

- 書籍のスキャンデータを **LaTeX 数式入り Markdown**（章単位）に変換し、LLM が読める形にする（主目的）
- （任意）OCR の座標付き JSON を使い、閲覧用 PDF に不可視テキスト層を埋め込む（副目的）

## 実行環境・依存条件

- **OS**: Ubuntu 24.04
- **GPU**: NVIDIA GeForce RTX 5060 Ti 16GB（Blackwell 世代, sm_120）。CUDA 12.8 以降のビルドが必須で、古い CUDA 前提のツールは動作しない
- **言語**: Python 3.12（システムの 3.12 系を使用。uv の Python 自動ダウンロードは無効化済み）
- **パッケージ管理**: [uv](https://docs.astral.sh/uv/)
- **主要ライブラリ**: MinerU 3.4.4（OCR 本体）、torch 2.13.0+cu130、img2pdf、pillow、pypdf

詳細は [`docs/TECH_STACK.md`](docs/TECH_STACK.md) を参照。

### セットアップ

```bash
uv sync
```

リポジトリルートで実行すると `.venv` が作成され、全依存が導入される。torch / torchvision は `pyproject.toml` に定義された PyTorch 公式 cu130 インデックスから導入される。

### プロキシ環境での注意

プロキシ必須のネットワークでは、MinerU 実行時に `no_proxy` / `NO_PROXY` へ `localhost,127.0.0.1` を追加すること。追加しないとローカル API のヘルスチェックが 502 で失敗する。

## データ

スキャンデータと OCR 成果物はリポジトリ外のデータディレクトリ（以下 `{BASE}`）に置く。

- **スキャン原本**: `{BASE}/chapNN/out/` の `page-NN_{1L,2R}.tif`（600dpi、RGB、LZW 可逆）。**OCR 入力はこちらを使う**
- **OCR 成果物**: `{BASE}/ocr/` 配下
  - `pdf/` — OCR 入力用 PDF と manifest
  - `mineru-full/chapNN/run-NN{,-normalized}/` — MinerU の実行別出力
  - `final/chapNN/` — 最終成果物（Markdown＋content_list.json＋カラー images/）
  - `fixes/chapNN.json` — 手動修正の定義ファイル。**書籍本文の文字列を含むためリポジトリに置かない・コミットしない**（書式はリポジトリ内 [`fixes/README.md`](fixes/README.md)・[`fixes/template.json`](fixes/template.json) を参照）

## 使い方

### 一括実行（通常はこれだけでよい）

TIF ディレクトリから最終 Markdown 生成までを 1 コマンドで実行する:

```bash
uv run python scripts/ocr_dir.py <TIFディレクトリ>... -o <出力ルート> [--punct-style {comma,touten}] [--fixes-dir <修正定義ディレクトリ>]
```

処理内容: 入力 PDF 生成 → MinerU → 句読点正規化・字形正規化 → 機械確認 → HTML 表変換 → 脚注挿入 → 修正適用（`--fixes-dir` 指定時のみ）。

図画像はこのパイプラインの対象外で、正規化済み出力（`run-NN-normalized/`）には Markdown と content_list.json だけが置かれる。画像込みの成果物を作る場合は `colorize_images.py` で `images/` を生成する。

主なオプション:

| オプション | 説明 | 既定値 |
|---|---|---|
| `-o, --root` | 出力先ルート（`pdf/`・`mineru-full/` を配下に作る） | 必須 |
| `--name` | 出力 name の明示指定（入力ディレクトリが 1 個のときのみ有効） | ディレクトリ名から導出 |
| `--glob` | 対象 TIF のパターンを単一パターンに変更 | `page-*_{1L,2R}.tif` 相当の 2 パターン |
| `--overwrite-pdf` | 既存の入力 PDF を作り直す | manifest 検証の上で再利用 |
| `--timeout` | MinerU のタイムアウト（分） | 60 |
| `--fixes-dir` | 修正定義ファイルのディレクトリ（`{name}.json` を探す） | なし（修正適用を行わない） |
| `--punct-style` | 書籍の句読点スタイル。`comma` = 「、。」を「，．」へ置換／`touten` = 句読点を置換しない | `comma` |

入力 PDF には manifest（TIF のパス・サイズ・mtime）が付き、一致時のみ再利用される。

### 個別スクリプト

一括実行に組み込み済みのため通常は個別実行不要。単体で使う場合のコマンドを示す。各スクリプトとも、出力先の同名ファイルが既存の場合は拒否が既定で、`--overwrite` で上書きする。

#### TIF → OCR 用可逆 PDF 生成（`make_ocr_pdf.py`）

```bash
uv run python scripts/make_ocr_pdf.py <TIF>... -o <出力PDF> [--overwrite]
```

引数のページ順で、300dpi グレースケール・Flate 可逆の PDF を生成する。MinerU の内部処理が 200dpi レンダリングのため、重要なのは可逆（非 JPEG）ソースを渡すこと。

#### 句読点正規化（`normalize_punct.py`）

```bash
uv run python scripts/normalize_punct.py <ファイル>... -o <出力ディレクトリ> [--punct-style {comma,touten}] [--overwrite]
```

MinerU 出力の表記揺れを正す。MinerU 変換後は必ず適用する。

- **句読点**: `--punct-style comma`（既定）で「、→，」「。→．」に全文置換する。原本が「、。」を用いる書籍では `--punct-style touten` を指定し、置換を行わない
- **字形**: MinerU が日本語字のかわりに出力する中国語字 8 種（值→値・变→変・单→単・对→対・图→図・换→換・徵→徴・樣→様）を、句読点スタイルによらず常に置換する
- **警告**: 置換後も残る JIS X 0208 外の漢字を標準エラーへ報告する（字形の対応関係が成立しない個別の誤認識。`apply_fixes.py` で対処する）

#### HTML 表 → GFM パイプテーブル変換（`html_table_to_md.py`）

```bash
uv run python scripts/html_table_to_md.py <md> -o <出力ディレクトリ> [--overwrite]
```

MinerU が Markdown 中に 1 行の HTML `<table>` として出す表を GFM パイプテーブルへ変換する（HTML ブロック内では `$…$` 数式が描画されないため）。`colspan` 等の複雑な表は壊さずスキップして警告する。

#### 脚注（訳注）挿入（`insert_footnotes.py`）

```bash
uv run python scripts/insert_footnotes.py <md> <content_list> -o <出力ディレクトリ> [--overwrite]
```

MinerU が content_list の `page_footnote` ブロックにのみ出力する脚注を、md の該当ページ本文末尾の直後に blockquote として挿入する。冪等で、content_list は無改変。脚注番号は数字・上付き数字・`*N`・`$^{N}$` の各形式を認識する。

#### 手動修正の適用（`apply_fixes.py`）

```bash
uv run python scripts/apply_fixes.py <md> <fixes.json> -o <出力ディレクトリ> [--overwrite]
```

修正定義ファイルの old→new ペアを md に機械適用する。old 不在・複数一致は全件エラーで出力なし（再 OCR で文面が変わると検出できる）。冪等。OCR の個別誤りは final を直接編集せず、この仕組みで修正を永続化する。

#### 図画像のカラー再切出（`colorize_images.py`）

```bash
uv run python scripts/colorize_images.py <content_list> <TIFディレクトリ> -o <出力ディレクトリ> [--overwrite] [--scale SCALE]
```

content_list の bbox（0–1000 正規化座標）を使い、原本 TIF から図ブロックをカラーで切り出す。縮小率の既定は 1/3（旧画像と同等の表示サイズ）、`--scale 1.0` で原寸。MinerU の生成画像はグレースケール PDF 由来のため必ず適用する。

## テスト

```bash
uv run pytest -v
```

テストは `tests/` に置き、結果は `tests/results/` に保存する。

## ディレクトリ構成

```
honOCR/
├── CLAUDE.md               # Claude Code 向けプロジェクトガイド
├── pyproject.toml          # uv プロジェクト定義
├── fixes/                  # 修正定義ファイルの書式テンプレートと仕様（実体はリポジトリ外）
├── docs/                   # ドキュメント（開発プロセス基準・案件記録）
├── scripts/                # 各種 CLI スクリプト
└── tests/                  # テスト
```

開発プロセス（案件フロー・レビュー・実装規約）は [`CLAUDE.md`](CLAUDE.md) と `docs/` 配下の基準書を参照。
