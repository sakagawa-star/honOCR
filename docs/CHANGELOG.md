# CHANGELOG

## リリース履歴

### 2026-08-25

- **feat-010**: 手動修正の永続化 — 修正定義ファイルの機械適用
  - `scripts/apply_fixes.py` を追加。OCR 誤りの手動修正を「old→new の完全一致文字列ペア」として章ごとの修正定義ファイルに記録し、md に機械適用する CLI。old ちょうど1回一致で置換、old 不在でも new ちょうど1回なら適用済みスキップ（冪等）、それ以外（不在・複数一致・曖昧）は全件エラーで出力を書かない。出力前に最終不変条件（全 fix で old=0回・new=1回）を検査し、再実行が冪等にならない定義を初回に検出する
  - **公開分離**: 定義ファイルの実体（書籍本文の文字列を含む）はリポジトリ外 `{BASE}/ocr/fixes/{name}.json` にのみ置く（GitHub 公開時に露出しない。ユーザー要件）。リポジトリには `fixes/template.json`（架空文字列のみ）と `fixes/README.md`（書式仕様・適用規則）のみ
  - `scripts/ocr_dir.py` に `--fixes-dir` オプションを追加: 脚注挿入の直後に `{name}.json` があれば適用（なければ何もしない）。PASS サマリに `fixes=` を追加
  - 初期データ: MinerU の式番号誤結合5件（chap01 の (1.25)/(1.26)、chap02 の (2.218)/(2.219)、chap05 の (5.98)〜(5.100)・(5.106)/(5.107)・(5.159)/(5.160)。全て原本 TIF 目視確認済み）を定義し、final / run-01-normalized 両系統に適用（applied 1/1/3、両系統バイト同一・content_list 無改変・迷子番号 0 件・各タグちょうど1回・冪等性を検証）。統合型3件は array を独立 `$$` ブロックに分割（構文要素のみ除去）
  - テスト34件追加（計143件全 PASS、`tests/results/feat-010_test_result.txt`）。Codex レビュー: 3サイクルで収束（高2・中2を検出。主要指摘は要求仕様内の公開分離違反、array 分割と alignment marker の衝突、適用済み判定の甘さ、冪等性の最終不変条件不足）
- **feat-009**: MinerU 出力から欠落する脚注（訳注）の Markdown 挿入
  - `scripts/insert_footnotes.py` を追加。MinerU が Markdown に出力しない `page_footnote` 型ブロック（chap01 の訳注1〜13 を含む計31ブロック。ユーザー報告: 式 (1.45) 後の注釈4・5 が md に見当たらない）を content_list.json からページ単位で組み立て、該当ページ本文末尾の直後に blockquote（`> 4 訳注：…`）として挿入する CLI。組み立ては「浮遊断片除去（空白除去後の部分文字列判定）→ bbox (y0, x0) 読み順ソート → 脚注番号プレフィックスで結合」。アンカー探索は単調増加カーソルの完全一致（table は `table_body` → `convert_table` 再生成パイプテーブル → `img_path` の3候補）。冪等（既挿入はスキップ）、content_list は無改変
  - `scripts/ocr_dir.py` に組み込み: HTML 表変換の直後に正規化済み md へインプレース適用（`insert_footnotes` / `parse_footnote_summary` を新設。非0終了・サマリ解析不能は FAIL）。PASS サマリに `footnotes=` を追加
  - 既存データ適用: 全8章 × final / run-01-normalized 両系統。挿入は chap01 = 14件＋1件スキップ（第2章冒頭が写った最終ページ。アンカーなしで正）、chap02 = 3件、chap06 = 2件、他5章 = 0件（設計の期待値と完全一致）。適用後も final = run-01-normalized のバイト同一・content_list 16ファイルの sha256 不変を検証。実データで冪等性も確認（再実行 0件挿入・md 不変）。ユーザー手動テストで注釈4・5 の表示を確認
  - テスト24件追加（計109件全 PASS、`tests/results/feat-009_test_result.txt`）。Codex レビュー: 2サイクルで収束（高1・中1を検出。主要指摘は feat-008 変換後 md で table アンカーが `img_path` では一致しない矛盾）

### 2026-08-24

- **feat-008**: MinerU 出力の HTML 表を Markdown パイプテーブルに変換
  - `scripts/html_table_to_md.py` を追加。MinerU が1行の HTML `<table>` として出力する表（CommonMark の HTML ブロックとなり `$…$` が数式描画されない。VS Code プレビューで chap01 表 1.1/1.2 の数式が LaTeX ソースのまま表示される問題の原因）を GFM パイプテーブルに変換する CLI。表タグ6種・属性なし・列数一致の単純表のみ変換し、`colspan` 等の複雑な表は壊さずスキップして警告（忠実性優先）。数式中の `<`（`$a<b$`）はセルテキストとして保持。改行コード（LF/CRLF）を含め表行以外はバイト不変
  - `scripts/ocr_dir.py` に組み込み: 機械確認合格後に正規化済み md をインプレース変換（`convert_tables` / `parse_table_summary` を新設。合計行を読み取れない場合は FAIL）。PASS サマリに `tables=` を追加。content_list.json は MinerU スキーマ維持のため無改変
  - 既存データ適用: chap01（2表）・chap06（1表）の final / run-01-normalized 計4ファイルを変換（スキップ 0、変更行は表行の置換のみ、content_list・images の sha256 不変）。ユーザー手動テストで chap01 表 1.1/1.2 の数式描画を確認
  - **付随して発見・復旧**: run-01-normalized の md 2件が feat-005 の final 構築（8/21 15:05、バイト同一 PASS 記録あり）後に外的要因で損傷していた（chap06 末尾49行欠落・chap07 先頭28行欠落。mtime 8/21 15:12、原因プロセス特定不能）。final は全8章とも生出力＋正規化とバイト一致（正）であることを確認の上、final からのコピーで復旧。復旧後、全8章で final = run-01-normalized のバイト同一・`<table` 行 0 を検証（調査記録は案件 README「実装中の発見」）
  - テスト29件追加（計85件全 PASS、`tests/results/feat-008_test_result.txt`）。Codex レビュー: 5サイクルで収束（高2・中5を検出。うち1件は Sonnet 実装時検出の設計書の名前衝突 `convert_table(html)` × `import html`）。実装中断2回（設計書矛盾・データ損傷）はいずれも調査→設計改訂→レビュー→承認を経て再開

### 2026-08-21

- **feat-005**: 全スキャンデータの本処理（フェーズ4 完了）
  - chap00〜07 の8ディレクトリ・補正済み TIF 全396枚（除外なし・辞書順）を OCR し、最終成果物 `{BASE}/ocr/final/chapNN/`（Markdown＋content_list.json＋カラー images/）を確立。**書籍スキャン分の LLM 用 Markdown 化が完了**
  - 経緯: 当初「章単位の再構成・重複/白紙除外」を計画したが、ユーザーレビューで「ゴールは入力への忠実な高精度 OCR」と指摘され全面是正（2026-08-18）。入力範囲も chap01〜04 → chap00〜07 に拡大
  - 実測: chap00〜03 は手動＋ocr_dir.py、chap04〜07 は ocr_dir.py 一括（PASS。計178ページ約16分、モデル追加DLなし）。全8章で page_idx 検査（白紙位置のみ欠落許容）・正規化のコードポイント機械確認に合格。図はカラー化済み（計207枚。chap07 は図なし）
  - final 構築の機械確認: コピー16ファイルのバイト同一、md 参照画像の存在、content_list の img_path ユニーク集合 = images 一致（全8章）。回帰テスト56件 PASS（`tests/results/feat-005_test_result.txt`）
  - Codex レビュー: 8サイクル（高2・中7を検出。スコープ2転換を含む）

### 2026-08-18

- **feat-007**: 図画像のカラー再切出スクリプト
  - `scripts/colorize_images.py` を追加。MinerU content_list の図ブロック（img_path を持つ image/chart/table）の bbox（0–1000 正規化。実データで座標系を検証）と page_idx から、原本 TIF（600dpi カラー）の同一領域を切り出してグレー画像と同名で差し替える CLI。md・content_list は無改変（確認済みテキストに手を付けない）
  - 手動テスト差し戻し1回（イテレーション1）: 原寸出力で表示サイズが約3倍になったため、既定 1/3 縮小（200dpi 相当 = 旧画像と同等の表示サイズ、差1%以内）＋ `--scale` オプションを追加
  - 動作確認: chap00〜03 の全図ブロック（3/55/55/36）を再生成し、カラー（彩度指標 0.00→6.15）・サイズ 630×944（旧 631×946 比 0.2%差）を確認。ユーザー手動テストでカラー表示・表示サイズを確認
  - テスト15件追加（計56件全 PASS、`tests/results/feat-007_test_result.txt`）。Codex レビュー: 6サイクルで収束（高2・中6を検出。主要指摘は feat-005 final 構築とのコピー元矛盾、JPEG 非可逆とテスト完全一致の矛盾、1/3 丸めと「同一サイズ」表現の矛盾）。feat-005 の FR-004・§4.4 も併せて改訂（final の images コピー元を正規化側に変更、カラー再切出完了を前提条件化）
- **feat-006**: OCR 一括実行スクリプト
  - `scripts/ocr_dir.py` を追加。TIF ディレクトリを指定するだけで「PDF 生成 → MinerU 変換（no_proxy 設定・run 連番・ログ保存・60分タイムアウト）→ 句読点正規化 → 機械確認（ページ数・page_idx（白紙位置のみ欠落許容）・コードポイント比較）」を一括実行し、ユーザーが Claude Code を介さず OCR できるようにした（ユーザー要望）。複数ディレクトリの逐次処理・PASS/FAIL サマリ付き
  - 安全設計: PDF 生成時に対象TIF のパス・サイズ・mtime を manifest（JSON）として記録し、既存 PDF の再利用は manifest 完全一致時のみ（Codex 指摘・高）。name 重複の事前エラー、ページ数検証は MinerU 実行前
  - 依存変更: pypdf 6.16.1 を dev group から通常依存へ移動（新規インストールなし）
  - 動作確認: chap03 実データで PASS（44ページ・505ブロック・置換330箇所・4分35秒）。feat-005 の chap03 処理を兼ねる。テスト17件追加（当時計41件全 PASS、`tests/results/feat-006_test_result.txt`）。Codex レビュー: 2サイクルで収束（高1・中3を検出）

### 2026-08-17

- **feat-004**: 句読点正規化の後処理と再判定
  - `scripts/normalize_punct.py` を追加。MinerU 出力（md / content_list.json）の「、→，」「。→．」を無条件全文置換する CLI（原本が「、。」を不使用のため安全。JSON は文字列値のみ置換し構造を保存）
  - run-02 出力を正規化（md 247 + json 258 = 505箇所置換）。コードポイント位置比較で「差分は許可置換のみ・長さ一致・残存『、。』ゼロ」を機械確認し、feat-003 の項目A（数式 19/20）・項目C（読み順 5/5）の引き継ぎを成立させた
  - 再判定（criteria lock 済みの事前基準・feat-003 と同一10段落）: 本文 **10/10 合格**（feat-003 は 7/10）→ 総合 **Go**。残存誤りは「;→；」1文字と「ようやく→よやく」1文字脱落のみ。疑義の括弧2件は原本TIF（600dpi）切り出しで確認し誤りではないと判定。ユーザー二次確認済み
  - テスト8件追加（計24件全 PASS、`tests/results/feat-004_test_result.txt`）。Codex レビュー: 2サイクルで収束（高2・中1を検出。主要指摘は `str.translate` に dict を渡す設計不備、A/C 引き継ぎの機械確認アルゴリズム未定義）
  - フェーズ4（全章の本処理）へ進行可

- **feat-003**: MinerU 試行（章単位PDFの品質確認）
  - 章単位PDF を生成（chap-00: 17ページ 6.9MB / chap-01: 64ページ 54.5MB。章対応はユーザー回答＋機械検証で確定し案件 README に記録）
  - MinerU 3.4.4（hybrid-engine 既定）で chap-01 を変換。初回モデルDL 2.4GB、所要 6分26秒、独立数式157件。プロキシ環境で localhost ヘルスチェックが 502 になる想定外事象が発生し、`no_proxy` への localhost 追加を設計に反映して解決（run-01 失敗 → run-02 成功）
  - 品質判定（criteria lock 済みの事前基準）: 数式 19/20 合格・本文 7/10 **不合格**・読み順 5/5 合格 → **No-Go**。不合格の主因は句読点「，．」→「、。」の系統的置換（全ブロックの15%・241箇所）。純粋な文字誤認識は10段落で1文字のみ。対策として feat-004（句読点正規化の後処理）を起票
  - 回帰テスト16件 PASS（`tests/results/feat-003_test_result.txt`）。Codex レビュー: 4サイクル（高3・中4を検出、criteria lock 含む）

- **feat-002**: TIF → OCR用可逆PDF生成スクリプト
  - `scripts/make_ocr_pdf.py` を追加。原本TIF（600dpi）をグレースケール化・1/2縮小（300dpi相当）し、Flate 可逆で複数ページPDFに格納する CLI（入力TIF列 + `-o` + `--overwrite`。章対応は呼び出し時のファイル指定で表現）
  - 安全設計: 変換前の全件検証（存在・モード・`im.load()` による実デコード）、一時ファイル経由の原子的書き込み（no-clobber は `os.link`、上書きは `os.replace`）
  - 依存追加: `img2pdf==0.6.3`（新規）、`pillow==12.3.0`・`pypdf==6.16.1`（ロック済み版の明示固定）
  - 検証結果: テスト10件追加（計16件全 PASS、`tests/results/feat-002_test_result.txt`）。実データ確認: 4件サンプルで gray/8-bit/Flate/300ppi を確認、全84件の一括変換が 22.4秒・62.3MB（`.../chap01/out/ocr/` に `sample4.pdf`・`all-pages.pdf` を残置）。ユーザーの目視で文字・数式の可読性を確認
  - Codex レビュー: 3サイクルで収束（高1・中3を検出）。主要指摘は非原子的書き込みによる不完全PDF残留、壊れたTIFの事前検出漏れ、`--overwrite` なし時の競合上書き、書き込み失敗テストの実効性

- **feat-001**: uv 環境構築と MinerU 導入
  - uv プロジェクトを初期化（`pyproject.toml` / `.python-version` / `uv.lock`）。`mineru[core]==3.4.4`、`torch==2.13.0+cu130`・`torchvision==0.28.0+cu130`（PyTorch 公式 cu130 インデックスから固定）、`pytest==9.1.1` を導入
  - `[tool.uv]` で Python 自動ダウンロード禁止（`python-downloads = "never"`）とシステム Python 限定（`python-preference = "only-system"`）を設定
  - 検証結果: スモークテスト6件全件 PASS（Python 3.12 / CUDA 認識 / CUDA ビルド 12.8 以上 / compute capability (12,0) / CUDA カーネル実行 / mineru バージョン）。結果は `tests/results/feat-001_test_result.txt`。ユーザーの手動テストでも全件 PASS を確認
  - Codex レビュー: 4サイクルで収束（高3・中3を検出）。主要指摘は torch の推移的依存任せによるバージョン不定、Python 自動ダウンロードの禁止漏れ、cu130 インデックスのネットワーク要件記述漏れ、TECH_STACK.md 更新計画の漏れ
