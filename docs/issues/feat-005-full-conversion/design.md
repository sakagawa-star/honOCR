# feat-005 機能設計書: 全スキャンデータの本処理（ディレクトリ単位の高精度 OCR）

## 1. 対応要求マッピング

対象: `docs/issues/feat-005-full-conversion/requirements.md`

| 要求ID | 設計セクション |
|---|---|
| FR-001 | §4.1 |
| FR-002 | §4.2 |
| FR-003 | §4.3 |
| FR-004 | §4.4 |

## 2. システム構成

本案件で新規コードは書かない（既存の `scripts/make_ocr_pdf.py`・`mineru` CLI・`scripts/normalize_punct.py` を使う。機械確認は使い捨てスクリプトをスクラッチパッドで実行する）。成果物はデータとドキュメント。

`{BASE}` = `/home/sakagawa/work/Pattern_Recognition_and_Machine_Learning`、`{ROOT}` = `{BASE}/ocr`（本案件で新設）。

| 成果物 | 場所 | 担当内容 |
|---|---|---|
| 入力PDF（8件） | `{ROOT}/pdf/chapNN_gray300.pdf` | FR-001 |
| MinerU 生出力（8件） | `{ROOT}/mineru-full/chapNN/run-NN/` と `run-NN.log` | FR-002 |
| 正規化済み md・content list（8件） | `{ROOT}/mineru-full/chapNN/run-NN-normalized/` | FR-003 |
| final ディレクトリ（8件） | `{ROOT}/final/chapNN/`（構成は requirements.md FR-004 のとおり） | FR-004 |
| 作業記録 | `docs/issues/feat-005-full-conversion/work_log.md` | 各手順の実測値（所要時間・置換件数・確認結果）の記録 |

既存データ（`chap01/out/ocr/` と `chap00/out/ocr/` 配下の feat-003/004 成果物、各ディレクトリの閲覧用 PDF）は参照も使用もしない。削除・変更もしない。

## 3. 技術スタック

- 追加ライブラリ: なし。`mineru==3.4.4`（hybrid-engine 既定設定）、`scripts/make_ocr_pdf.py`（feat-002、改変しない）、`scripts/normalize_punct.py`（feat-004、改変しない）、検証は Python 3.12 標準ライブラリと coreutils（`cmp`、`grep`、`du`、`df`、`pdfinfo`）のみ

## 4. 各機能の詳細設計

処理はディレクトリ単位で独立している。実施順序は §10 を参照。定数（requirements.md §1.2・案件 README の実測値）:

| 対象 | ページ数 P | 白紙ページの位置 B（0始まり） |
|---|---|---|
| chap00 | 20 | {0, 4, 8, 10, 18} |
| chap01 | 84 | {0, 4, 8, 10, 18} |
| chap02 | 70 | {}（なし） |
| chap03 | 44 | {0} |
| chap04 | 48 | {}（なし） |
| chap05 | 70 | {0} |
| chap06 | 36 | {0, 8, 26, 30} |
| chap07 | 24 | {}（なし） |

### 4.1 入力PDF の生成（FR-001）

1. 入力ファイル列の構成（除外なし・辞書順）: `ls {BASE}/chapNN/out/page-*_1L.tif {BASE}/chapNN/out/page-*_2R.tif | sort`
2. 実行前照合: 各ディレクトリのファイル数が P（§4 の表: 20 / 84 / 70 / 44 / 48 / 70 / 36 / 24）と一致することを確認する。不一致なら実行せず中断して報告する（TIF の追加・削除があった場合は調査に戻る）
3. `mkdir -p {ROOT}/pdf` の後、ディレクトリごとに `uv run python scripts/make_ocr_pdf.py <全TIFの列挙> -o {ROOT}/pdf/chapNN_gray300.pdf` を実行する
4. 検証: `pdfinfo` でページ数（P と一致）を確認し、結果と実測（所要時間・ファイルサイズ）を work_log.md に記録する

エラー時: `make_ocr_pdf.py` が非0終了したら中断して報告する（feat-002 で検証済みのため想定外事象として扱う。白紙の 1-bit G4 TIF を含む変換は feat-003 の chap-00 PDF 生成で成功実績あり）。

### 4.2 MinerU 変換（FR-002）

ディレクトリごとに以下を行う。

1. 事前確認（初回のみ）: `df -h {BASE}` で空き容量 20GB 以上を確認する（不足時は中断して報告）。`du -sb ~/.cache` を記録する（受け入れ基準4の実行前値。全8件の完了後に再測定して差分を確認する）
2. 実行ディレクトリの確保: ディレクトリ別に実行番号 NN（01 から。そのディレクトリの再実行のたびに +1）を決め、`{ROOT}/mineru-full/chapNN/run-NN/` を新規作成する。既に存在する場合は次の番号に進む（feat-003 §4.2 と同じ規則。完了確認は今回の run-NN 配下のみを対象にする）
3. 実行（**バックグラウンドで行う**。8件は逐次実行し、並列にしない — GPU メモリを1ジョブで占有するため）:
   `env no_proxy="localhost,127.0.0.1,$no_proxy" NO_PROXY="localhost,127.0.0.1,$NO_PROXY" uv run mineru -p {ROOT}/pdf/chapNN_gray300.pdf -o {ROOT}/mineru-full/chapNN/run-NN` の標準出力・標準エラーを `{ROOT}/mineru-full/chapNN/run-NN.log` に保存する
   - `no_proxy`/`NO_PROXY` への `localhost,127.0.0.1` 追加は必須（feat-003 run-01 の 502 失敗の再発防止）
   - バックエンド・オプションは指定しない（既定 = hybrid-engine。feat-003/004 の品質確認条件と揃える）
4. 完了確認（対象は `run-NN/chapNN_gray300/hybrid_auto/` 配下）:
   1. 終了コード 0
   2. `chapNN_gray300.md` が存在しサイズ > 0（`test -s`）
   3. `chapNN_gray300_content_list.json` の page_idx 検査 — 使い捨ての Python スクリプト（スクラッチパッド）で確認する。判定規則（requirements.md FR-002 基準3）:
      - content list が非空で、全ブロックが整数 `page_idx` を持つ（欠落キー・非整数値は不合格）
      - `pages = {b["page_idx"] for b in blocks}` について、`extra = pages - set(range(P))` が空（範囲外なし）
      - `missing = set(range(P)) - pages` が **B（白紙ページの位置）の部分集合**（白紙はブロックが出ないことが正常。白紙以外の欠落は不合格）
      - 不合格の場合は該当ページ番号を報告して中断する。`missing` の内容（白紙と一致したか）は合否によらず work_log.md に記録する
5. 実測記録: 所要時間・生出力の合計サイズ・md の独立数式件数（`grep -o '\$\$' <md> | wc -l` の値。参考記録）を work_log.md に記録する

エラー時の対応（feat-003 §4.2 と同じ判断基準）:

| エラー | 検出方法 | 処理 |
|---|---|---|
| ローカル API ヘルスチェック失敗（502） | run-NN.log の `Timed out waiting for local mineru-api` | 手順3の `no_proxy` 追加漏れを確認して再実行（そのディレクトリの番号を進める）。追加済みでも失敗なら中断・報告 |
| 想定外のモデルダウンロード開始 | run-NN.log のダウンロード進捗表示 | そのまま完了を待ち、全8件完了後の `~/.cache` 差分が 100MB 以上なら受け入れ基準4の不合格として報告（原因調査はユーザー報告後） |
| GPU メモリ不足（OOM） | run-NN.log の CUDA OOM メッセージ | 中断して報告（バックエンド変更はしない） |
| 60分超過（1件あたり） | バックグラウンドタスクの経過時間 | プロセス停止して中断・報告 |

あるディレクトリで中断が発生した場合、原因がデータ固有であれば残りのディレクトリの §4.2〜4.3 は継続してよい。原因が環境共通（OOM・ヘルスチェック失敗・モデルダウンロード）であれば全体を中断して報告する。

### 4.3 句読点正規化と機械確認（FR-003）

ディレクトリごとに以下を行う。

1. 正規化の実行:
   `uv run python scripts/normalize_punct.py {RUN}/chapNN_gray300/hybrid_auto/chapNN_gray300.md {RUN}/chapNN_gray300/hybrid_auto/chapNN_gray300_content_list.json -o {ROOT}/mineru-full/chapNN/run-NN-normalized`
   （`{RUN}` = `{ROOT}/mineru-full/chapNN/run-NN`）。終了コード 0 と2ファイルの出力を確認し、置換件数を work_log.md に記録する
2. 機械確認（feat-004 criteria §2 に固定したアルゴリズムと同一。2ファイルそれぞれに実施する）:
   1. 正規化前後のファイルを UTF-8 でデコードし、コードポイント列の長さが等しいことを確認する
   2. 各位置 i について「前後で同一」「前が「、」(U+3001) かつ後が「，」(U+FF0C)」「前が「。」(U+3002) かつ後が「．」(U+FF0E)」のいずれかであることを確認する
   3. 正規化後のファイルに「、」「。」が残存していない（0件）ことを確認する
   4. 上記以外の差分・長さ不一致・出力欠落が1つでもあれば中断して報告する
   - 実装: 使い捨ての Python スクリプトをスクラッチパッドに書いて実行する（リポジトリには置かない。以下は意図伝達用の擬似コードであり、そのままコピーして使うものではない）
     ```python
     a, b = read(src), read(dst)  # UTF-8 デコード済み文字列
     assert len(a) == len(b)
     allowed = {("、", "，"), ("。", "．")}
     for x, y in zip(a, b):
         assert x == y or (x, y) in allowed
     assert b.count("、") == 0 and b.count("。") == 0
     ```
   5. 確認結果（長さ・許可置換数・不許可差分数・残存数）を work_log.md に記録する

エラー時: `normalize_punct.py` の非0終了は中断して報告する（feat-004 で検証済みのため想定外事象として扱う）。

### 4.4 final ディレクトリの構築（FR-004）

前提条件: §4.4 は**全8ディレクトリの §4.3 機械確認が合格し、かつ各ディレクトリで図画像のカラー再切出（feat-007 `scripts/colorize_images.py`。出力先 `run-NN-normalized/images/`）が完了している場合のみ**実施する。カラー再切出の完了確認: 各ディレクトリについて content_list の `img_path` のユニーク数と `run-NN-normalized/images/` 内のファイル数が一致すること（図ブロック 0 件の章は空の `images/` または省略で可とし、その旨を work_log.md に記録する）。中断が1つでもある場合は §4.4 全体を実施せず（final ディレクトリを構築しない）、合格済み分の成果物は `run-NN-normalized/` までの中間成果物として残し、中断分と合わせて報告する（requirements.md FR-004 基準5のとおり）。

1. `{ROOT}/final/chapNN/`（NN = 00〜07）を作成する（`mkdir -p`。既に `{ROOT}/final/` が存在する場合は中断して報告する — 本案件初回実行時には存在しないはずであり、存在するなら前回試行の残骸か想定外の状態のため）
2. コピー（`cp`。移動・リンクは使わない。コピー元を変更しない）:

   | コピー元 | コピー先 |
   |---|---|
   | `{ROOT}/mineru-full/chapNN/run-NN-normalized/chapNN_gray300.md` と `..._content_list.json` | `final/chapNN/` |
   | `{ROOT}/mineru-full/chapNN/run-NN-normalized/images/`（feat-007 のカラー再切出の出力。ディレクトリごと） | `final/chapNN/images/` |

3. 検証（受け入れ基準の機械確認）:
   1. 全8ディレクトリ × 3項目の存在確認（`test -s` / `test -d`）
   2. md・content_list.json 計16ファイルについて `cmp <コピー元> <コピー先>` でバイト同一を確認
   3. 画像参照の整合: 各 md から `grep -o 'images/[^)"]*' <md> | sort -u` で参照ファイル名を抽出し、すべて `final/chapNN/images/` 内に存在することを確認する（参照 0 件の場合はその旨を記録して合格扱い）
   4. カラー再切出の完全性（FR-004 基準4）: final 側 content_list から `img_path` の basename のユニーク集合を抽出し、`final/chapNN/images/` 直下のファイル集合と一致することを確認する（md 参照は content_list の部分集合になり得るため、手順3だけでは content_list からのみ参照される画像の欠落を検出できない）
   5. 結果を work_log.md に記録する

境界条件: あるディレクトリの `images/` が生成されない（図が1枚も無い）場合は、空の `final/chapNN/images/` を作成し、その旨を work_log.md に記録する（md に画像参照が無いことを併せて確認する）。

## 5. 状態遷移

該当なし。

## 6. ファイル・ディレクトリ設計

- `{ROOT}` = `{BASE}/ocr` を本処理の作業ディレクトリとして新設し、`pdf/`（入力PDF）・`mineru-full/chapNN/`（実行別出力）・`final/`（最終成果物）を置く。既存データ（`{BASE}/chap01/out/ocr/` 配下ほか）は移動しない
- final ディレクトリの構成・命名: requirements.md FR-004 のとおり（ベース名は MinerU 出力のまま維持する。md 内の `images/...` 相対参照を壊さないため、md と images/ は同じディレクトリに置く）
- 作業記録: `docs/issues/feat-005-full-conversion/work_log.md`（git 管理。手順ごとに追記し、上書きしない）

## 7. インターフェース定義

新規関数・クラスなし（既存 CLI の呼び出しと使い捨て検証スクリプトのみ）。

## 8. ログ・デバッグ設計

- MinerU 実行ログ: `{ROOT}/mineru-full/chapNN/run-NN.log`（標準出力・標準エラーをそのまま保存。ディレクトリ別・実行ごとに連番）
- 作業の記録: work_log.md（§6）

## 9. 設計判断の記録（ADR）

| # | 採用 | 却下と理由 |
|---|---|---|
| 1 | 各ディレクトリの全TIF を辞書順のまま処理する（除外・並べ替えなし） | 白紙・重複ページの除外や章境界の再定義 — ゴールは入力ファイルへの忠実な高精度 OCR であり、編集的な加工はゴールの書き換えに当たる（2026-08-18 ユーザー指示）。白紙ページは PDF に含めても MinerU 出力に実質的な影響がない |
| 2 | chap01 は全84枚で作り直し、feat-003/004 の既存成果物（除外3枚あり・章分割）は流用しない | 既存 run-02 出力の流用 — 既存成果物は64枚サブセットに対するもので、本案件の処理単位（全84枚）と一致しない（ユーザー回答 2026-08-18）。既存成果物は削除せず残置する |
| 3 | 新たな数値判定（Go/No-Go）は行わない | criteria を新設した品質判定 — パイプラインの品質は feat-003/004 で chap01 のデータにより判定済み（Go）。検証は機械確認とユーザー目視に限定する（requirements.md「品質確認の扱い」のとおり） |
| 4 | page_idx 検査は「白紙位置の部分集合なら欠落を許容」とする | `set(range(P))` との完全一致 — 白紙ページは MinerU がブロックを出力しない可能性があり、完全一致では正常な白紙を誤検出する。白紙以外の欠落は従来どおり不合格 |
| 5 | final への集約はコピー（`cp`）で行う | シンボリックリンク — final を独立した配布可能な成果物にする。ハードリンク — 誤編集がコピー元に波及する |
| 6 | final のファイル名は MinerU 出力のベース名（`chapNN_gray300.*`）を維持する | 改名 — 由来（どの PDF から生成されたか）の追跡性を優先する。LLM 用途にファイル名の簡潔さは影響しない |
| 7 | `middle.json`・`layout.pdf` ほかは final にコピーしない | 全ファイル集約 — LLM 用途（主目的）に必要なのは md と images、副目的（フェーズ5 のテキスト層埋め込み）の座標取得は run ディレクトリに残る `middle.json` を将来案件で直接参照すればよい。content_list.json は page_idx による原本ページ対応付けに使うため final に含める |
| 8 | 実装は Claude Code 本体が実行する（Sonnet 委任しない） | Sonnet サブエージェント委任 — 本案件の「実装」はコマンド実行と機械確認が主体で、新規コードがない（feat-003 ADR-5 と同じ理由。CLAUDE.md の委任ルールは「コードを書く実装」を対象とする） |
| 9 | 機械確認スクリプトはスクラッチパッドの使い捨てとする | `scripts/` への追加 — 一度きりの検証でありプロダクトコードにしない。再現に必要なアルゴリズムは feat-004 criteria §2 と本書 §4.2/§4.3 に固定済み |
| 10 | 本処理の出力は `{ROOT}` = `{BASE}/ocr` に新設して集約する | `{BASE}/chap01/out/ocr/` への追記 — chap01 のスキャンディレクトリ配下にディレクトリ横断の成果物を置くのは所在が分かりにくい。既存データは移動しない |
| 11 | MinerU はディレクトリごとに逐次実行する | 8件一括の1回実行（`-p` にディレクトリ指定）— 件単位でログ・実行番号・完了確認を独立させ、1件の失敗が他の出力と混ざらないようにする。並列実行 — GPU メモリを1ジョブで占有するため不可 |

## 10. 実装・検証の実施方法

- 手順: Codex レビュー収束 → 人レビュー承認 → §4.1（8件の PDF 生成）→ ディレクトリごとに §4.2 → §4.3（chap00 → 01 → 02 → 03 → 04 → 05 → 06 → 07 の順。MinerU は逐次実行）→ **全8件の §4.3 機械確認が合格し、かつ全8件で feat-007 のカラー再切出が完了（`img_path` ユニーク数 = `run-NN-normalized/images/` ファイル数）した場合のみ** §4.4 を実施する。不合格・未了があれば §4.4 は実施せず（§4.4 前提条件のとおり）、§4.2 のエラー対応表に従って残りの継続可否を判断する
- **承認ゲート**: §4.2 の MinerU 実行（長時間ジョブ）は、人レビュー承認（実装開始指示）をもって承認とみなす（requirements.md 制約条件のとおり）
- 本案件は新規コードがないため pytest の追加はない。回帰確認として完了前に `uv run pytest -v` を実行し、既存24件が PASS のままであることを確認して `tests/results/feat-005_test_result.txt` に保存する
- 手動テスト（ステップ7）: ユーザーが `final/` の成果物を確認する（md の原本との見比べ、LLM への投入試行）。問題発見時は BUGFIX_STANDARD に従い investigation.md に修正計画を追記する

## 11. 完了処理でのドキュメント更新

- `docs/TECH_STACK.md`: 変更なし（ライブラリ追加がない）
- `CLAUDE.md`: ディレクトリ構成の変更なし（リポジトリ内の新規ファイルは案件フォルダ配下のみ）。「テストデータ」の chap01/out の枚数誤記（87枚 → 84枚）を修正し、chap00・chap02〜07 のデータ所在を追記する。「ドメイン知識」に final ディレクトリの場所・構成（1〜2行）を追記する
- `docs/BACKLOG.md` / `docs/CHANGELOG.md`: 完了時に更新（フェーズ4 完了と主要実測値を CHANGELOG に記録する）
