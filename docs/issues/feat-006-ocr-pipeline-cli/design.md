# feat-006 機能設計書: OCR 一括実行スクリプト（ocr_dir.py）

## 1. 対応要求マッピング

対象: `docs/issues/feat-006-ocr-pipeline-cli/requirements.md`

| 要求ID | 設計セクション |
|---|---|
| FR-001 | §4.1 |
| FR-002 | §4.2 |
| FR-003 | §4.3 |
| FR-004 | §4.4 |

## 2. システム構成

| ファイル | 種別 | 担当内容 |
|---|---|---|
| `scripts/ocr_dir.py` | 新規 | 一括実行 CLI（単一モジュール） |
| `tests/test_ocr_dir.py` | 新規 | 自動テスト（§4.4） |
| `tests/results/feat-006_test_result.txt` | 新規 | テスト結果の保存先 |

依存方向: `ocr_dir.py` → （サブプロセス）→ `make_ocr_pdf.py` / `mineru` / `normalize_punct.py`。import による依存はなし。

`pyproject.toml` の変更: **pypdf を dev group から通常依存（`[project.dependencies]`）へ移動する**（CLI 実行時に使うため。新規パッケージのインストールは発生しない。`uv lock` の更新を伴う）。あわせて `docs/TECH_STACK.md` の pypdf の用途を「テスト用途」から「PDF ページ数確認（CLI 実行時）・テスト用途」に更新する。

## 3. 技術スタック

- Python 3.12 標準ライブラリ（`argparse` / `pathlib` / `sys` / `os` / `subprocess` / `json` / `shutil`）＋ `pypdf`（PDF ページ数確認。feat-002 から既存）
- サブプロセス起動: 同梱スクリプトは `[sys.executable, str(SCRIPTS_DIR / "make_ocr_pdf.py"), ...]`（`SCRIPTS_DIR = Path(__file__).resolve().parent`）、MinerU は `["mineru", "-p", ..., "-o", ...]`（uv 環境の PATH 上にある）

## 4. 各機能の詳細設計

### 定数

```python
TIF_PATTERNS = ("page-*_1L.tif", "page-*_2R.tif")  # 既定の対象TIF（feat-005 の全TIF定義と同一）。--glob で単一パターンに変更可（上級用途）
BLANK_MAX_BYTES = 10240               # これ未満の対象TIFを白紙ページとみなす
PDF_SUFFIX = "_gray300.pdf"
MANIFEST_SUFFIX = "_gray300.pdf.manifest.json"     # PDF の隣に置く manifest
DEFAULT_TIMEOUT_MIN = 60              # MinerU タイムアウト（分）。--timeout で変更可
REPLACEMENTS = {"、": "，", "。": "．"}  # 機械確認の許可置換（normalize_punct.py と同一定義）
```

### 4.1 一括パイプライン（FR-001）

#### CLI 仕様

```
uv run python scripts/ocr_dir.py DIR [DIR ...] -o ROOT
    [--name NAME] [--glob PATTERN] [--overwrite-pdf] [--timeout MINUTES]
```

| 引数 | 型 | 必須 | 意味 |
|---|---|---|---|
| `dirs`（位置引数、`nargs="+"`） | パス1個以上 | 必須 | 入力ディレクトリ |
| `-o` / `--root` | パス | 必須 | 出力先ルート `{ROOT}`（`pdf/`・`mineru-full/` を配下に作る） |
| `--name` | 文字列 | 任意 | name の明示指定。入力ディレクトリが1個のときのみ有効（複数との併用は argparse 後の検証でエラー・終了コード 2） |
| `--glob` | 文字列 | 任意 | 対象TIF を単一パターンに変更する上級オプション（既定は `TIF_PATTERNS` の2パターン結合。feat-005 と同一入力列にする場合は指定しない） |
| `--overwrite-pdf` | フラグ | 任意 | 既存の入力PDF を作り直す（既定は検証の上で再利用） |
| `--timeout` | 整数（分） | 任意 | MinerU のタイムアウト（既定 60） |

#### 実行前検証（`main`。全ディレクトリの処理開始前）

- `--name` と複数 dir の併用 → エラー・終了コード 2
- 各 dir から導出した name に重複がある → エラー・終了コード 2（同一 name の出力が混ざるのを防ぐ。FR-003 基準3b）

#### ディレクトリごとの処理フロー（`process_dir`）

```
1. name 決定      : --name があればそれ。なければ dir のベース名（ベース名が "out" なら親の名前）
2. 対象TIF 列挙   : TIF_PATTERNS（--glob 指定時は単一パターン）で列挙し辞書順 sort。0件なら不合格
3. 白紙位置検出   : サイズ < BLANK_MAX_BYTES の対象TIF の 0始まり位置の集合 B
4. PDF 準備       : pdf = ROOT/pdf/{name}_gray300.pdf、manifest = ROOT/pdf/{name}_gray300.pdf.manifest.json
   a. --overwrite-pdf 指定時 → make_ocr_pdf.py をサブプロセス実行（--overwrite 付き）→ manifest を書き直す
   b. pdf が存在しない → make_ocr_pdf.py をサブプロセス実行 → manifest を書く
   c. pdf が存在する → manifest が存在し、その内容が現在の対象TIF の
      (絶対パス, サイズ, mtime_ns) の列と完全一致する場合のみ再利用。
      manifest がない・一致しない → 不合格（メッセージで --overwrite-pdf を案内）
5. PDF ページ数検証: len(pypdf.PdfReader(pdf).pages) == len(対象TIF)。不一致なら不合格
                    （MinerU 実行前に行う。不一致 PDF で長時間ジョブを走らせない）
6. run 番号決定   : ROOT/mineru-full/{name}/ 直下の run-NN ディレクトリの最大 NN + 1（なければ 01）
7. MinerU 実行    : env に no_proxy/NO_PROXY へ "localhost,127.0.0.1" を追記した上で
                    mineru -p <pdf> -o ROOT/mineru-full/{name}/run-NN
                    stdout/stderr は ROOT/mineru-full/{name}/run-NN.log に保存。timeout 超過は打ち切り不合格
8. 正規化         : normalize_punct.py をサブプロセス実行
                    （入力: hybrid_auto/ の md と content_list.json、-o run-NN-normalized）
9. 機械確認       : §4.2 の項目2〜4（項目1は手順5で実施済み）
10. 戻り値        : 合否と主要数値（ページ数・ブロック数・置換件数・所要時間）の結果オブジェクト
```

manifest の形式（JSON）: `{"files": [{"path": "<絶対パス>", "size": <int>, "mtime_ns": <int>}, ...]}`。生成は PDF 書き込み成功後に行う。比較は列の長さ・順序を含む完全一致。

- `hybrid_auto` ディレクトリの位置は `ROOT/mineru-full/{name}/run-NN/{pdf の stem}/hybrid_auto/`（feat-005 実測のレイアウト）。存在しなければ不合格
- ステップ4〜8 のいずれかで失敗したディレクトリは不合格とし、残りのディレクトリの処理を継続する（FR-001 基準5）
- `no_proxy` の追記は既存値を保持して先頭に追加する（`"localhost,127.0.0.1," + 既存値`。既存値が空なら `"localhost,127.0.0.1"`）

### 4.2 機械確認（FR-002）

各確認は関数として実装し（§7）、不合格理由の文字列リストを返す（空 = 合格）。

1. **PDF ページ数**: `len(pypdf.PdfReader(pdf).pages) == len(対象TIF)`。**§4.1 手順5として MinerU 実行前に実施する**（生成直後・再利用判定直後の両方が対象）
2. **md**: `hybrid_auto/{stem}.md` が存在しサイズ > 0
3. **page_idx 検査**（feat-005 design §4.2 手順4.3 と同一規則）:
   - content list が非空で、全ブロックが整数 `page_idx` を持つ
   - `pages = {b["page_idx"] for b in blocks}`、`extra = pages - set(range(P))` が空、`missing = set(range(P)) - pages` が B の部分集合
   - 不合格時は missing/extra の番号をメッセージに含める
4. **正規化の機械確認**（feat-004 criteria §2 と同一規則。md・content list の2ファイル各々）:
   - 正規化前後のコードポイント数が一致
   - 各位置の差分が REPLACEMENTS の組（「、→，」「。→．」）のみ
   - 正規化後の残存「、」「。」が 0 件

### 4.3 CLI・エラー処理（FR-003）

| 事象 | 検出 | 動作 |
|---|---|---|
| 引数不正（`--name` と複数 dir の併用を含む） | argparse / 引数検証 | 標準エラーにメッセージ、終了コード 2 |
| 入力ディレクトリ不存在・対象TIF 0件 | ステップ2 | そのディレクトリを不合格として継続 |
| サブプロセス非0終了（make_ocr_pdf / normalize_punct） | returncode | 標準エラー出力を添えて不合格として継続 |
| MinerU 非0終了・タイムアウト | returncode / `subprocess.TimeoutExpired` | `run-NN.log` のパスを添えて不合格として継続 |
| 機械確認の不合格 | §4.2 | 理由を標準エラーに出力して不合格として継続 |

最終サマリ（標準出力）: ディレクトリごとに1行 `"{name}: PASS pages={P} blocks={n} replaced={md}+{json} ({M分S秒})"` または `"{name}: FAIL <理由の要約>"`。終了コード: 全 PASS = 0、1件でも FAIL = 1。

進捗表示: 各ステップ開始時に1行（`"[chap03] mineru run-01 開始 (44 pages)..."` の形式）。logging モジュールは使わない（feat-002/004 と同じ方針。標準出力＝進捗・サマリ、標準エラー＝エラー理由）。

#### 境界条件

- 白紙のみのディレクトリ（全対象TIF が白紙）→ そのまま処理する（page_idx 検査は missing = 全ページ ⊆ B で合格し得る）
- `ROOT` が存在しない → `parents=True` で作成する
- 同一 name の再実行 → run 番号が進むだけで過去の run は不変（PDF は再利用）

### 4.4 自動テスト（FR-004）

`tests/test_ocr_dir.py`。`sys.path` への `scripts/` 追加は既存テストと同じ方式。フィクスチャは `tmp_path`。GPU・MinerU・実 TIF は使わない（関数単体を対象にする）。

| テスト関数名 | 内容（assert する条件） |
|---|---|
| `test_derive_name_plain` | `/x/chap03` → `chap03` |
| `test_derive_name_out` | `/x/chap03/out` → `chap03` |
| `test_blank_positions` | サイズ違いのダミーファイル列 → 閾値未満の位置集合が返る |
| `test_next_run_number_empty` | run ディレクトリなし → 1 |
| `test_next_run_number_existing` | `run-01`・`run-03` あり → 4 |
| `test_check_page_idx_pass` | missing が白紙位置の部分集合 → エラーなし |
| `test_check_page_idx_missing_fail` | 白紙以外の欠落 → エラーに番号を含む |
| `test_check_page_idx_extra_fail` | 範囲外 page_idx → エラー |
| `test_check_page_idx_non_int_fail` | `page_idx` 欠落・非整数 → エラー |
| `test_check_normalized_pass` | 許可置換のみの前後ペア → エラーなし |
| `test_check_normalized_bad_diff` | 許可外の差分 → エラー |
| `test_check_normalized_residual` | 残存「、」→ エラー |
| `test_manifest_roundtrip_match` | build_manifest で書いた manifest → manifest_matches が True |
| `test_manifest_mismatch` | TIF の追加・サイズ変更後 → manifest_matches が False |
| `test_cli_name_with_multiple_dirs` | `--name` ＋ dir 2個 → 終了コード 2 |
| `test_cli_duplicate_names` | 同じ name に導出される dir 2個（例: `a/out` と `a`）→ 終了コード 2 |
| `test_cli_missing_dir` | 不存在ディレクトリ1個 → 終了コード 1、FAIL サマリ |

実行手順: `uv run pytest -v > tests/results/feat-006_test_result.txt 2>&1` → 全件 PASS（既存24件＋本案件17件 = 41件）を確認する。

## 5. 状態遷移

該当なし。

## 6. ファイル・ディレクトリ設計

出力レイアウト（feat-005 と同一。§4.1 のとおり）:

```
{ROOT}/
├── pdf/{name}_gray300.pdf
└── mineru-full/{name}/
    ├── run-NN/            # MinerU 生出力
    ├── run-NN.log         # MinerU 実行ログ
    └── run-NN-normalized/ # 正規化済み md・content_list.json
```

## 7. インターフェース定義

`scripts/ocr_dir.py` 内（すべて型ヒント付き）:

| 関数 | シグネチャ | 責務 |
|---|---|---|
| `derive_name` | `(d: Path) -> str` | name 決定（ベース名。`out` なら親の名前） |
| `list_tifs` | `(d: Path, glob: str \| None = None) -> list[Path]` | 対象TIF の辞書順列挙（既定 `TIF_PATTERNS` の結合。`glob` 指定時は単一パターン） |
| `build_manifest` | `(files: list[Path]) -> dict` | 対象TIF の (絶対パス, サイズ, mtime_ns) 列から manifest 辞書を作る |
| `manifest_matches` | `(manifest_path: Path, files: list[Path]) -> bool` | 既存 manifest と現在の対象TIF の完全一致判定 |
| `blank_positions` | `(files: list[Path], threshold: int = BLANK_MAX_BYTES) -> set[int]` | 白紙位置の検出 |
| `next_run_number` | `(name_dir: Path) -> int` | run 番号の決定 |
| `check_page_idx` | `(content_list: Path, page_count: int, blanks: set[int]) -> list[str]` | §4.2-3 の検査。エラーメッセージのリストを返す |
| `check_normalized` | `(src: Path, dst: Path) -> list[str]` | §4.2-4 の検査。同上 |
| `process_dir` | `(d: Path, root: Path, args: argparse.Namespace) -> DirResult` | §4.1 のフロー全体（1ディレクトリ分） |
| `parse_args` | `(argv: list[str] \| None = None) -> argparse.Namespace` | CLI 引数の解析 |
| `main` | `(argv: list[str] \| None = None) -> int` | 全体制御・サマリ表示。終了コードを返す |

`DirResult` は `dataclasses.dataclass`（`name: str` / `passed: bool` / `reasons: list[str]` / `pages: int` / `blocks: int` / `replaced_md: int` / `replaced_json: int` / `seconds: float`）。

## 8. ログ・デバッグ設計

- §4.3 のとおり（標準出力＝進捗・サマリ、標準エラー＝不合格理由、MinerU の生ログ＝ `run-NN.log`）

## 9. 設計判断の記録（ADR）

| # | 採用 | 却下と理由 |
|---|---|---|
| 1 | 既存スクリプトをサブプロセスで呼ぶ | import による再利用 — feat-004 ADR-3 のスクリプト間 import 禁止方針を維持。ロジック再実装 — 検証済みコードの重複はバグ源になる。サブプロセスなら両方を回避できる |
| 2 | 既存 PDF の再利用は manifest（対象TIF のパス・サイズ・mtime の記録）完全一致時のみ | ページ数一致だけでの再利用 — 別入力の同ページ数 PDF や TIF 差し替えを検出できず、成果物の正当性を壊す（Codex 指摘・高）。常に再生成 — 再実行のたびに生成コストがかかる。manifest なしの既存 PDF（feat-005 §4.1 で生成した8件が該当）は `--overwrite-pdf` での作り直しを要求する |
| 3 | 白紙位置はファイルサイズ（< 10,240 バイト）で自動検出する | 白紙位置の手動指定 — feat-005 では調査で実測したが、スキャン運用上の白紙は 1-bit G4 で約 1KB になることが全8ディレクトリで確認済み。閾値 10KB は白紙（~1KB）と最小の本文ページ（>100KB）の間に十分な余裕がある |
| 4 | final 構築（`{ROOT}/final/`）は含めない | `--final` オプション — final は「全ディレクトリ合格後に一括構築」という feat-005 の完了条件と結びついた操作で、ディレクトリ単位の本スクリプトに持たせると条件が二重管理になる。必要になれば別案件で追加する |
| 5 | MinerU のタイムアウトは 60 分/ディレクトリ（`--timeout` で変更可） | 無制限 — ハング時に人手の介在が必要になり一括実行の趣旨に反する。feat-005 非機能要求と同じ値を既定にする |
| 6 | テストは関数単体（GPU・MinerU なし） | パイプライン全体の結合テスト — MinerU 実行には GPU と数分を要し pytest に組み込めない。結合確認は実データでの動作確認（§10）で行う |

## 10. 実装・検証の実施方法

- 手順: Codex レビュー収束 → 人レビュー承認 → 実装（**Sonnet サブエージェント委任**: スクリプト＋テスト＋テスト実行。CLAUDE.md の実装ルールに従う）→ 動作確認 → 完了処理
- 動作確認（実装後、Claude Code 本体が実施）: `uv run python scripts/ocr_dir.py {BASE}/chap03/out -o {ROOT} --overwrite-pdf` を実行し（feat-005 §4.1 生成の既存 PDF には manifest がないため `--overwrite-pdf` で作り直す）、chap03 が PASS すること・出力レイアウトが feat-005 と一致することを確認する。結果は本案件 README への追記と feat-005 の work_log の両方に記録する（feat-005 の chap03 処理を兼ねる）
- **承認ゲート**: 動作確認の MinerU 実行（長時間ジョブ）は、人レビュー承認をもって承認とみなす

## 11. 完了処理でのドキュメント更新

- `docs/TECH_STACK.md`: pypdf の用途を「PDF ページ数確認（CLI 実行時）・テスト用途」に更新する（§2 の依存移動に対応。新規ライブラリの追加はない）
- `CLAUDE.md`: ディレクトリ構成に `scripts/ocr_dir.py`・`tests/test_ocr_dir.py` を追記する。「ドメイン知識」に一括実行コマンドの1行例を追記する
- `docs/BACKLOG.md` / `docs/CHANGELOG.md`: 完了時に更新
- `README.md`（ルート）: 存在しないため対象外
