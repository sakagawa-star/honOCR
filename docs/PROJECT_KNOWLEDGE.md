# PROJECT_KNOWLEDGE

honOCR の**プロジェクト知識**（データの所在と仕様・ディレクトリ構成・ドメイン知識）を集約したファイル。
開発フロー・レビュー手順・運用ルールなどの**統治**は `CLAUDE.md` にあり、本ファイルには含めない。

## 本ファイルの扱い

- **必読**: OCR 作業・案件の調査に入る前に本ファイルを全文読む（`CLAUDE.md`「プロジェクト知識」参照）
- **更新**: 各案件の完了処理で更新する（feat/bug: 案件で得た知見・データの状態・ファイルの追加削除の反映。update: ファイルの追加削除の反映）。更新内容は案件の設計書等に定義しレビューを通したものに限る。追記には出所の案件 ID を付す（例: 「（feat-016）」）
- **構成の変更**（分割・セクション再編）は update 案件で扱う
- **分割の目安**: **本ファイルが 500 行を超えたら分割を検討する。分割しない判断をしてもよいが、その判断と理由を記録する**（記録先は末尾の「分割検討の記録」）。行数は `wc -l docs/PROJECT_KNOWLEDGE.md` で確認する
- 本ファイルは `CLAUDE.md` から 2026-09-02 に分離した（update-003）。分離時点の内容は CLAUDE.md の当時の記述を無改変で転記したものである（例外は「ディレクトリ構成」ツリー内の本ファイル自身と `CLAUDE.md` の注記の2行のみ）

## データ

`{BASE}` = `/home/sakagawa/work/Pattern_Recognition_and_Machine_Learning`（git 管理外・リポジトリ外）

- **スキャン原本**: `{BASE}/chapNN/out/`（NN = 00〜07）の `page-NN_{1L,2R}.tif` 計396枚（chap00: 20 / chap01: 84 / chap02: 70 / chap03: 44 / chap04: 48 / chap05: 70 / chap06: 36 / chap07: 24。2026-08-18 実測）。補正済み、600dpi、RGB、LZW可逆（章によりピクセル寸法は微差）。**OCR入力はこちらを使う**。白紙ページのみ 1-bit G4（約1KB）
- 各 `out/` の `chapNN_300dpi.pdf` は LLM閲覧用の非可逆圧縮PDF（テキスト層なし）。**OCR入力には使わない**（JPEGノイズが数式の添字認識に不利）
- **OCR 成果物**: `{BASE}/ocr/` 配下 — `pdf/`（入力PDF＋manifest）、`mineru-full/chapNN/run-NN{,-normalized}/`（実行別出力）、**`final/chapNN/`（最終成果物: Markdown＋content_list.json＋カラー images/。feat-005 で全8章構築済み）**、`fixes/chapNN.json`（手動修正の定義ファイル。書籍本文の文字列を含むため**リポジトリに置かない・コミットしない**。feat-010）

### 第2の書籍（『プログラミングのための確率統計』）

`{BASE2}` = `/home/sakagawa/work/確率統計`（git 管理外・リポジトリ外）

- **スキャン原本**: `{BASE2}/dewarping/chapNN/out/`（NN = 00〜09）の `page-NN_{1L,2R}.tif` 計383枚（chap00 は前付け、chap09 は付録ABC・参考文献・目次・索引）。仕様は PRML と同条件（600dpi・LZW 可逆・白紙のみ 1-bit G4）だが**大半がグレースケール**（`L`）。`out/cache/` は glob 対象外
- **句読点スタイルは「、。」**のため、OCR 時は必ず `--punct-style touten` を指定する（feat-011）
- **Q&A コラム見出しは全10章で 74 件**あり、2026-09-03 に全件を原本 TIF と突合した（feat-021）。結果は `{BASE2}/ocr/collation/feat-021_qa_headings.md`（書籍本文を含むためリポジトリ外）に、要約は `docs/issues/feat-021-qa-heading-source-collation/collation_summary.md` にある。**74件中 37 件が原本と不一致**（体裁19・文字14・ブロック構造3・数式18。フラグは重複する）
- 上記の不一致のうち**語彙単位の誤読4件は 2026-09-05 に修正済み**（feat-022）。chap01 `? 1.8`（「いい」→「い」）/ chap02 `? 2.10`（「これ」→「こ」）/ chap03 `? 3.5`（「賭けろ」→「賭ける」）/ chap08 `? 8.6`（「だろ」→「だる」）。修正は md のみで、**`content_list.json` には誤読が残る**（既存ポリシー。content_list を基準に走査する後続案件は、md 側が修正済みであることを前提に読むこと）。chap08 `? 8.6` の `##` 欠落は feat-020 の担当として残してある（feat-022）
- 2026-08-28 に**全10章（383ページ）の本処理が完了**（`ocr_dir.py --punct-style touten --final` で約35分、全章 PASS）。`{BASE2}/ocr/final/chap00〜09/` に最終成果物（Markdown 計約932KB＋画像421枚）がある。feat-013 の字形正規化・修正定義（`{BASE2}/ocr/fixes/` の5ファイル）も適用済み

## ディレクトリ構成（主要部分）

```
honOCR/
├── CLAUDE.md               # Claude Code の統治文書（開発フロー・運用ルール）
├── AGENTS.md               # Codex が起動時に読む指示ファイル（レビュー定型指示）
├── README.md               # プロジェクト概要と使い方（コマンド・CLIオプション・環境）
├── pyproject.toml          # uv プロジェクト定義（依存・[tool.uv] 設定・cu130 インデックス）
├── .python-version         # Python 3.12 固定
├── uv.lock                 # ロックファイル（自動生成）
├── fixes/                  # 修正定義ファイルの書式テンプレートと仕様（feat-010。実体は {BASE}/ocr/fixes/ でリポジトリ外）
│   ├── template.json
│   └── README.md
├── docs/                   # ドキュメント（開発プロセス基準）
│   ├── BACKLOG.md
│   ├── CHANGELOG.md
│   ├── BUGFIX_STANDARD.md
│   ├── DESIGN_STANDARD.md
│   ├── REQUIREMENTS_STANDARD.md
│   ├── REVIEW_CRITERIA.md
│   ├── TECH_STACK.md
│   ├── PROJECT_KNOWLEDGE.md    # 本ファイル（データ・ディレクトリ構成・ドメイン知識。統治は CLAUDE.md）
│   ├── HERDR_SETUP.md
│   ├── codex-exec-ubuntu24-bwrap-fix.md
│   └── issues/             # 案件ディレクトリ
├── scripts/
│   ├── make_ocr_pdf.py     # TIF → OCR用可逆PDF生成 CLI（feat-002）
│   ├── normalize_punct.py  # MinerU 出力の句読点正規化 CLI（feat-004）
│   ├── html_table_to_md.py # HTML 表 → GFM パイプテーブル変換 CLI（feat-008）
│   ├── insert_footnotes.py # content_list の脚注（page_footnote）を md に挿入する CLI（feat-009）
│   ├── apply_fixes.py      # 修正定義ファイル（old→new）を md に機械適用する CLI（feat-010）
│   ├── ocr_dir.py          # OCR 一括実行 CLI: PDF生成→MinerU→正規化→機械確認→HTML表変換→脚注挿入→修正適用（feat-006, 008, 009, 010）
│   ├── colorize_images.py  # 図画像のカラー再切出 CLI（feat-007）
│   ├── crop_blocks.py      # content_list のブロックを原本 TIF から切り出す CLI（feat-021）
│   └── build_final.py      # final ディレクトリ構築 CLI: 集約＋3種類の機械検証（feat-012）
└── tests/
    ├── test_env.py         # 環境スモークテスト（feat-001）
    ├── test_make_ocr_pdf.py  # 変換スクリプトのテスト（feat-002）
    ├── test_normalize_punct.py  # 正規化スクリプトのテスト（feat-004）
    ├── test_html_table_to_md.py  # HTML表変換スクリプトのテスト（feat-008）
    ├── test_insert_footnotes.py  # 脚注挿入スクリプトのテスト（feat-009）
    ├── test_apply_fixes.py # 修正適用スクリプトのテスト（feat-010）
    ├── test_ocr_dir.py     # 一括実行スクリプトのテスト（feat-006）
    ├── test_colorize_images.py  # カラー再切出スクリプトのテスト（feat-007）
    ├── test_build_final.py  # final 構築スクリプトのテスト（feat-012）
    ├── test_crop_blocks.py  # ブロック切り出しスクリプトのテスト（feat-021）
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
- MinerU の出力は句読点スタイルが揺れる（原本「，．」の約15%が「、。」に置換される。feat-003 で実測）。`scripts/normalize_punct.py` による「、→，」「。→．」の全文置換後処理で解消する（feat-004。MinerU 変換後は必ず適用する）。**この置換は書籍の句読点スタイルに依存する**ため `--punct-style {comma,touten}` で選ぶ（feat-011。既定 `comma` = 置換する。PRML 用。「、。」を用いる書籍（例: 『プログラミングのための確率統計』）には `touten` を指定し、置換しない）
- MinerU は日本語字のかわりに中国語字（簡体字・繁体字・旧字体）を出すことがある。`normalize_punct.py` は句読点スタイルによらず**21種**を常時置換する（feat-011 で8種、feat-013 で13種追加）。内訳は `CJK_REPLACEMENTS_CN`（簡体字・繁体字16種: 值→値・变→変・单→単・对→対・图→図・换→換・徵→徴・樣→様・黑→黒・說→説・题→題・戾→戻・边→辺・橫→横・虛→虚・錄→録）と `OLD_FORM_REPLACEMENTS`（旧字体5種: 權→権・收→収・檢→検・縱→縦・廣→広）
- **旧字体5種は固有名詞では正当な表記になりうる**（実例: 確率統計 chap09 奥付の「印刷·製本 廣済堂」は旧字を正式名称に用いる実在の社名）。そのため `normalize_punct.py` は**旧字体を置換した箇所を、置換【前】の文脈つきで標準エラーへ警告する**（feat-013。置換後は元の字が失われ、後から grep しても壊れた箇所を見つけられないため）。新しい書籍を処理したら**この警告を必ず確認し、固有名詞であれば `apply_fixes.py` の修正定義ファイルで元に戻す**
- 字形対応が成立しない誤認識（例: 「濵習」→演習、「跺な解」→疎な解、「揾」→掟）は置換せず、**正規化後に残る JIS X 0208 外の漢字を標準エラーへ警告**するので、`apply_fixes.py` の修正定義ファイルで対処する。ただしこの警告は**正規化の時点**で出力されるため、脚注挿入（feat-009）で content_list から md へ持ち込まれる文字は md 側の警告に現れない（**json 側の警告を正とみなす**。content_list は全ブロックを持つため検出漏れは生じない）
- **語彙単位の誤り**（実例: 確率統計 chap07 の「[0,1)上的一様分布」→「上の」。feat-016）は、字形の 1 対 1 対応では表現できず（「的」は「比較的」等で正当に使われる）、構成する字がすべて JIS X 0208 内にあるため**上記の警告にも現れない**。機械的な検出手段がないため手動テストで見つけるほかなく、発見したら `apply_fixes.py` の修正定義ファイルで対処する（置換表には入れない）
- **語彙単位の誤りを調査するときは、誤読された文字列そのものだけを検索してはならない。正しい語を起点に、表記ゆれ・脱落・挿入のバリアントを正規表現で網羅的に洗い出す**（feat-019）。実例: feat-017 で「なんという」（「て」→「と」の誤読）9件を修正した際、同じ語の別バリアント「なんてい**い**う」（「い」の余分な挿入）2件を見落とした。両者は同一ページの隣接する段落にあった。`なん.{0,5}?[いゆ]う` のような正規表現で全章を走査し、出現形を集計して正当な語（「なんとなくそういう」等）と誤読を選別する。なお「い」の挿入・脱落は 1 文字 → 1 文字の字形対応で表現できないため、置換表では扱えない（feat-019 ADR-1）
- **MinerU は1つの見出しを2ブロックに分断することがある**（実例: 確率統計 chap02 の Q&A コラム見出し `? 2.2`。原本では1つの質問文が2行に組まれているだけだが、layout 解析が2行目を別ブロックとして切り出し、md 上で「見出し行＋空行＋本文段落」になる。feat-015）。文字の認識誤りではなく**ブロック分割の問題**のため、正規化の各種警告にも `build_final.py` の3種類の機械検証にも現れず、手動テストで見つけるほかない。発見したら `apply_fixes.py` の修正定義ファイルで対処する。**`apply_fixes.py` は md 全文を1つの文字列として `str.count()` / `str.replace()` するため、`old` / `new` に改行を含む複数行の文字列を指定でき**（JSON では `\n` でエスケープする）、分断の結合はこれで表現する。なお `content_list.json` は `apply_fixes.py` の対象外のため分断したままになる（md と json の非対称性。既存ポリシー）
- **MinerU は見出しの先頭にある装飾図案を、独立した画像ブロックとして切り出すことがある**（実例: 確率統計の Q&A コラム見出し先頭の「？」アイコン。6章8件。feat-014）。md 上には `![](images/{64桁hex}.jpg)` というアイコンだけの画像参照行が現れる。このとき見出しテキスト側の扱いは2通りに割れ、**「?」が欠落する型（3件）と「?」が入ったうえで画像にも重複する型（5件）**の両方が生じる。ブロック分割の問題のため正規化の各種警告にも `build_final.py` の3種類の機械検証にも現れず、手動テストで見つけるほかない。**検出には画像の実寸が使える**——アイコンは長辺 40〜46px で、次に小さい図版（167px）との間に大きな開きがあるため、`images/` を長辺で走査すれば機械的に洗い出せる。対処は `apply_fixes.py` の修正定義ファイルで、アイコン画像行の削除（と欠落型では見出しへの「? 」の補完）を行う。**`content_list.json` と `images/` の画像実体は消さない**——`build_final.py` の検証3が両者の完全一致を要求するため、json を無改変にする以上、画像実体も残す必要がある（feat-014）
- OCR の一括実行（feat-006）: `uv run python scripts/ocr_dir.py <TIFディレクトリ> -o <出力ルート> [--punct-style {comma,touten}]` で PDF 生成 → MinerU → 正規化 → 機械確認 → HTML表変換 → 脚注挿入 → 修正適用（`--fixes-dir` 指定時）まで1コマンド（ユーザーが Claude Code なしで実行できる）。入力PDF には manifest（TIF のパス・サイズ・mtime）が付き、一致時のみ再利用される。`--punct-style` は正規化と機械確認の両方に効く（feat-011。指定を誤ると機械確認が FAIL するため取り違えは検出される）。`--final` を付けると、修正適用の直後に「カラー再切出 → `final/{name}/` 構築」まで実行する（feat-012。既定は行わない。**章単位**で構築するため、後続の章が FAIL しても完成済みの final は残る）
- MinerU は表を Markdown 中に **1行の HTML `<table>`** として出力する。CommonMark では HTML ブロック内の `$…$` が数式描画されないため（VS Code プレビューで表内数式が LaTeX ソースのまま表示される）、`uv run python scripts/html_table_to_md.py <md> -o <出力先> [--overwrite]` で GFM パイプテーブルに変換する（feat-008。`ocr_dir.py` に組み込み済みのため通常は個別実行不要。`colspan` 等の複雑な表は壊さずスキップして警告。content_list の `table_body` は MinerU スキーマ維持のため無改変）
- MinerU は脚注（訳注）を content_list の `page_footnote` 型ブロックにのみ出力し、**Markdown には含めない**。`uv run python scripts/insert_footnotes.py <md> <content_list> -o <出力先> [--overwrite]` で md の該当ページ本文末尾の直後に blockquote（`> 4 訳注：…`）として挿入する（feat-009。`ocr_dir.py` に組み込み済みのため通常は個別実行不要。冪等・content_list 無改変。脚注ブロックは断片化・読み順乱れがあるため「断片除去 → bbox 読み順ソート → 番号プレフィックス結合」で組み立てる）。番号プレフィックスは数字・上付き数字に加え `*N` / `\*N` / `$^{N}$` / `$^{*N}$` を認識し、断片判定の比較キーは空白・`$`・`\` を除去して行う（feat-011）
- MinerU content_list の `bbox` は 0–1000 正規化座標（ページ左上原点）。図ブロック（img_path を持つ image/chart/table）は `uv run python scripts/colorize_images.py <content_list> <TIFディレクトリ> -o <images出力先>` で原本 TIF からカラー再切出できる（feat-007。既定 1/3 縮小 = 旧画像と同等の表示サイズ。MinerU の生成画像はグレースケール PDF 由来のため必ず適用する。`ocr_dir.py --final` に組み込み済みのため通常は個別実行不要）
- 最終成果物 `final/{name}/`（md＋content_list.json＋images/）は `uv run python scripts/build_final.py <run-NN-normalized> -o <final/chapNN> [--overwrite]` で構築する（feat-012。`ocr_dir.py --final` に組み込み済みのため通常は個別実行不要）。コピー後に3種類の機械検証（バイト同一・md の画像参照が images/ に存在・content_list の `img_path` 集合と images/ の**完全一致**）を行い、1つでも不合格なら終了コード 1。再構築時は `images/` の孤児ファイルを削除する。**出力先がコピー元と同一・入れ子、または出力先やその images/ がシンボリックリンクの場合は書き込み前に拒否する**（コピー元の成果物を壊さないため）
- **原本 TIF の任意の領域は `crop_blocks.py` で PNG 化して目視できる**（feat-021）。`uv run python scripts/crop_blocks.py <content_list> <TIFディレクトリ> -o <出力先> --index <ブロック番号> [--margin N] [--max-width N]` で、content_list の `bbox`・`page_idx` から原本の該当領域を切り出す。**原本 TIF は Read ツールで直接開けない**（TIF 非対応）ため、原本と OCR 結果を突き合わせるにはこの経路を使う。`colorize_images.py` は `img_path` を持つ図ブロックしか扱えないのに対し、本スクリプトは本文・数式・コードのブロックも切り出せる。MinerU が見出しを分断している場合は bbox が1行目しか覆わないことがあるので、`--margin` を広げて周囲ごと確認する
- **Q&A 見出しのような特定の要素を洗い出すときは、md の行頭走査ではなく content_list の全ブロック走査で行う**（feat-021）。md の行頭正規表現では、数式ブロック（`$$…$$`）・コードブロック（```` ``` ````）・HTML `div` に取り込まれた見出しを原理的に見つけられない。content_list なら `type`（`text`/`equation`/`code`）と `text_level`（見出しなら 2）で状態を機械的に分類でき、`bbox`・`page_idx` がそのまま原本の切り出しに使える。ただし **`apply_fixes.py` は md のみを対象とするため、修正済みの箇所は content_list と md の状態がずれる**（feat-014 で md に補完した3件は content_list では未修正のまま。両者を混同しないこと）
- OCR の個別誤り（例: 式番号と式の誤結合。MinerU の layout 解析起因で再OCRでも再発する）は final を直接編集せず、`{BASE}/ocr/fixes/{name}.json` に old→new の修正として登録し `uv run python scripts/apply_fixes.py <md> <fixes.json> -o <出力先> --overwrite` で適用する（feat-010。書式は `fixes/template.json`・`fixes/README.md` 参照。old 不在・複数一致は全件エラーで出力なし＝再OCRで文面が変わると検出できる。冪等。**定義ファイルの実体は書籍本文を含むためコミット禁止**）。**修正を定義するときは `old` の一意性だけでなく、適用後に `new` がちょうど1件になることも必ず事前に数える**（`new` が他所に正当に存在すると最終不変条件違反でエラー停止する。feat-013 で実際に発生。一意にならない場合は `old`/`new` の両方に前後の文脈を含める）

## 分割検討の記録

| 日付 | 行数 | 判断 | 理由 |
|---|---|---|---|
| 2026-09-02 | 104 | 検討不要 | 分離時点。500 行未到達 |
| 2026-09-02 | 106 | 検討不要 | feat-019 の教訓を1行追記。500 行未到達 |
| 2026-09-02 | 108 | 検討不要 | feat-014 の知見を1行追記。500 行未到達 |
| 2026-09-03 | 114 | 検討不要 | feat-021 の知見2行・データの状態1行・ディレクトリ構成2行を追記。500 行未到達 |
| 2026-09-05 | 116 | 検討不要 | feat-022 のデータの状態1行を追記。500 行未到達 |
