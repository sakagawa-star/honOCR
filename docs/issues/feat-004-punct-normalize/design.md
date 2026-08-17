# feat-004 機能設計書: 句読点正規化の後処理と再判定

## 1. 対応要求マッピング

対象: `docs/issues/feat-004-punct-normalize/requirements.md`

| 要求ID | 設計セクション |
|---|---|
| FR-001 | §4.1 |
| FR-002 | §4.2 |
| FR-003 | §4.3 |
| FR-004 | §4.4 |

## 2. システム構成

| ファイル | 種別 | 担当内容 |
|---|---|---|
| `scripts/normalize_punct.py` | 新規 | 正規化 CLI（単一モジュール。依存は標準ライブラリのみ） |
| `tests/test_normalize_punct.py` | 新規 | 自動テスト（§4.3） |
| `tests/results/feat-004_test_result.txt` | 新規 | テスト結果の保存先 |
| `experiments/renorm-quality/experiment_log.md` | 新規 | 再判定の実験ログ（案件フォルダ配下、git 管理） |
| 正規化済み run-02 出力 | データ（git 管理外） | `.../out/ocr/mineru-trial/run-02-normalized/` 配下（§4.4） |

`pyproject.toml` の変更: なし（新規ライブラリを追加しないため）。

## 3. 技術スタック

- Python 3.12 標準ライブラリのみ（`argparse` / `pathlib` / `sys` / `os` / `tempfile`）
- 原子的書き込みは feat-002 の `write_pdf_atomic` と同じ方式（本スクリプト内に同等の関数を実装する。feat-002 からの import はしない — スクリプト間依存を作らない。§9 ADR-3）

## 4. 各機能の詳細設計

### 4.1 句読点正規化スクリプト（FR-001）

#### CLI 仕様

```
uv run python scripts/normalize_punct.py FILE [FILE ...] -o OUTDIR [--overwrite]
```

| 引数 | 型 | 必須 | 意味 |
|---|---|---|---|
| `files`（位置引数、`nargs="+"`） | パス1個以上 | 必須 | 入力ファイル（UTF-8 テキスト） |
| `-o` / `--outdir` | パス | 必須 | 出力ディレクトリ（同じベース名で書き出す。存在しなければ `parents=True` で作成） |
| `--overwrite` | フラグ | 任意 | 出力先の同名ファイルが既存でも上書きする（既定は拒否） |

置換規則は定数で持つ: `REPLACEMENTS: dict[str, str] = {"、": "，", "。": "．"}`（これ以外の変換をしない）。置換の実装は `TRANSLATION_TABLE = str.maketrans(REPLACEMENTS)` を定義した上で `text.translate(TRANSLATION_TABLE)` とする（`str.translate` は ordinal ベースの変換表を要求するため、`dict[str, str]` を直接渡してはならない）。

#### データフロー

```
入力ファイル (UTF-8 テキスト)
  → read_text(encoding="utf-8")            # デコード不能なら検証フェーズで排除（§4.2）
  → text.translate(TRANSLATION_TABLE) による一括置換（、→，、。→．）
  → 出力ディレクトリへ原子的書き込み（一時ファイル → fsync → os.link / os.replace）
標準出力: ファイルごとに「{basename}: {置換件数} replaced」、最後に合計
```

- 置換件数 = 置換前の「、」出現数 + 「。」出現数
- 入力ベース名が重複している場合（例: 異なるディレクトリの同名ファイル）は検証フェーズでエラーにする（出力先で衝突するため）

#### 処理ロジック

1. 引数解析
2. 検証フェーズ（§4.2。1件でも不合格なら変換を開始しない）
3. 各ファイルを読み込み → 置換 → 出力ディレクトリへ原子的書き込み（feat-002 と同じ: `overwrite=False` は `os.link` の no-clobber、`overwrite=True` は `os.replace`、失敗時は一時ファイルを削除）
4. 置換件数を標準出力へ報告し、終了コード 0

ループ終了条件: 入力ファイルリストの末尾まで。

### 4.2 入力検証とエラー処理（FR-002）

検証フェーズ（全件検査してから終了）:

| 検査 | 不合格条件 | 動作 |
|---|---|---|
| 入力存在 | パスが存在しない、またはファイルでない | 標準エラーへ `not found: {path}`（該当全件）、終了コード 1 |
| UTF-8 デコード | `read_text(encoding="utf-8")` が `UnicodeDecodeError` | 標準エラーへ `not utf-8: {path}`（該当全件）、終了コード 1。検証フェーズで実際に全文デコードして確認する |
| ベース名の重複 | 入力列に同じベース名が2回以上現れる | 標準エラーへ `duplicate basename: {name}`、終了コード 1 |
| 出力先の既存 | `--overwrite` なしで出力先に同名ファイルが存在 | 標準エラーへ `output exists: {path} (use --overwrite)`（該当全件）、終了コード 1 |

変換フェーズ以降のエラー（書き込み失敗）: 標準エラーへ例外メッセージ、一時ファイルを削除して終了コード 1（既存の出力ファイルは不変）。

#### 境界条件

- 置換対象が0件のファイル → そのまま複製される（置換件数 0 と報告）
- 空ファイル → 空ファイルが出力される
- 入力0件 → argparse（`nargs="+"`）が終了コード 2

### 4.3 自動テスト（FR-003）

`tests/test_normalize_punct.py`。`sys.path` への `scripts/` 追加は feat-002 のテストと同じ方式。フィクスチャは `tmp_path` に生成する。

| テスト関数名 | 内容（assert する条件） |
|---|---|
| `test_replaces_punctuation` | 「今日は、晴れ。」を含むファイル → 出力が「今日は，晴れ．」、置換対象以外は不変、戻り値 0 |
| `test_preserves_other_content` | 「，．$x_{1}$ \tag{1.9}」などの置換非対象のみのファイル → 内容が完全一致（バイト同一）、置換件数 0 |
| `test_input_unchanged` | 実行後、入力ファイルの内容が実行前と同一 |
| `test_cli_missing_input` | 存在しないパス → 戻り値 1、出力なし |
| `test_cli_not_utf8` | UTF-8 でないバイト列のファイル（`bytes([0x80, 0xFF])` を書いたもの） → 戻り値 1、出力なし |
| `test_cli_duplicate_basename` | 異なるディレクトリの同名ファイル2件 → 戻り値 1、出力なし |
| `test_cli_refuses_overwrite` | 出力先に既存ファイル、`--overwrite` なし → 戻り値 1、既存不変 |
| `test_cli_overwrite_flag` | 同条件で `--overwrite` → 戻り値 0、正規化済み内容に置き換わる |

実行手順: `uv run pytest -v > tests/results/feat-004_test_result.txt 2>&1` → 終了コード 0、`24 passed`（既存16件＋本案件8件）を確認する。

### 4.4 再判定（FR-004）

前提: criteria lock（`experiments/renorm-quality/criteria.md` の Codex レビュー収束）と人レビュー承認の後に実施する。実施者は Claude Code 本体（feat-003 ADR-5 と同じ理由。§9 ADR-1）。

1. **フェーズ1: 正規化の実行**
   1. 直前予測（Markdown・content list の置換件数）を experiment_log.md に記録する（feat-003 実測の「、。」計241箇所は全ブロック合計。Markdown 単体・JSON 単体の件数はここで予測する）
   2. `uv run python scripts/normalize_punct.py <run-02の chap-01_gray300.md> <同 _content_list.json> -o <.../mineru-trial/run-02-normalized` を実行する
   3. 実測（置換件数）を記録し、予測と照合する
   4. 引き継ぎの妥当性確認: criteria.md §2「項目A・C の扱い」に固定した機械確認アルゴリズム（正規化前後のコードポイント列の位置ごと比較）を実行し、結果を experiment_log.md に記録する。確認できなければ中断して報告する
2. **フェーズ2: 項目B′ の再判定**
   1. 直前予測（合格数）を記録する
   2. feat-003 実験ログの判定表と同一の10段落について、正規化後のテキストで criteria の規則どおり判定し、判定表を experiment_log.md に記録する
   3. 予測と照合し、総合 Go/No-Go を criteria §2 のとおり決定する
3. ユーザーの二次確認を受ける（手動テストステップを兼ねる）

## 5. 状態遷移

該当なし。

## 6. ファイル・ディレクトリ設計

- 正規化済みデータの出力先: `/home/sakagawa/work/Pattern_Recognition_and_Machine_Learning/chap01/out/ocr/mineru-trial/run-02-normalized/`（ファイル名は入力と同じベース名）
- 実験ログ: `docs/issues/feat-004-punct-normalize/experiments/renorm-quality/experiment_log.md`（フェーズごとに追記、上書きしない）

## 7. インターフェース定義

`scripts/normalize_punct.py` 内（すべて型ヒント付き）:

| 関数 | シグネチャ | 責務 |
|---|---|---|
| `normalize_text` | `(text: str) -> tuple[str, int]` | 置換後テキストと置換件数を返す |
| `validate_inputs` | `(files: list[Path], outdir: Path, overwrite: bool) -> list[str]` | §4.2 の検証。エラーメッセージのリストを返す（空 = 合格） |
| `write_text_atomic` | `(text: str, output: Path, overwrite: bool) -> None` | 原子的書き込み（feat-002 の `write_pdf_atomic` と同方式・テキスト版） |
| `parse_args` | `(argv: list[str] \| None = None) -> argparse.Namespace` | CLI 引数の解析 |
| `main` | `(argv: list[str] \| None = None) -> int` | 全体制御。終了コードを返す |

定数: `REPLACEMENTS: dict[str, str] = {"、": "，", "。": "．"}`

## 8. ログ・デバッグ設計

- logging モジュールは使わない（feat-002 と同じ）。進捗・置換件数は標準出力、エラーは標準エラー
- 出力フォーマット: `"{basename}: {count} replaced"`、最終行 `"total: {sum} replaced in {n} files"`

## 9. 設計判断の記録（ADR）

| # | 採用 | 却下と理由 |
|---|---|---|
| 1 | スクリプト実装は Sonnet サブエージェント委任、再判定（§4.4）は Claude Code 本体が実施 | 全部委任 — 再判定は原本画像の読解と判定根拠の記録が必要で、feat-003 ADR-5 と同じ理由で本体が行う。スクリプトとテストはコードを書く実装なので CLAUDE.md のルールどおり委任する |
| 2 | 無条件の全文置換（「、」「。」→「，」「．」） | 文脈解析による選択的置換 — 原本は全編「，．」スタイルで「、。」を使わないため（feat-003 で原本ページを確認済み）、無条件置換で誤変換の余地がない。LaTeX 数式内にも「、」「。」は出現しない |
| 3 | 原子的書き込みを本スクリプト内に再実装 | feat-002 からの import — `scripts/` 配下のスクリプト間依存を作らない（単一ファイルで自己完結させ、個別に実行・テスト可能に保つ）。実装は約20行で重複コストは小さい |
| 4 | 対象は run-02 出力の Markdown と content list JSON の2ファイル | middle.json ほか全ファイルの正規化 — 再判定と LLM 用途に使うのはこの2ファイルのみ。フェーズ4で全章処理する際の対象選定はフェーズ4の案件で決める |
| 5 | 異体字「乘」の訂正はしない | 置換辞書への追加 — feat-003 で1件しか観測されておらず、一般化できる根拠がない。数式品質は 19/20 で合格済み |

## 10. 実装・検証の実施方法

- 手順: Codex レビュー収束（criteria lock 含む）→ 人レビュー承認 → 実装（Sonnet 委任: スクリプト＋テスト＋テスト実行）→ 再判定（本体: §4.4）→ ユーザー二次確認 → 完了処理
- 検証: §4.3 のテスト全件（`24 passed`）と、§4.4 の実験プロトコル完遂

## 11. 完了処理でのドキュメント更新

- `docs/TECH_STACK.md`: 変更なし（ライブラリ追加がない）
- `CLAUDE.md`: ディレクトリ構成に `scripts/normalize_punct.py`・`tests/test_normalize_punct.py` を追記する。「ドメイン知識」の句読点揺れの行に「feat-004 の後処理で正規化する」旨を追記する
- `docs/BACKLOG.md` / `docs/CHANGELOG.md`: 完了時に更新（再判定の Go/No-Go と実測値を記録）
