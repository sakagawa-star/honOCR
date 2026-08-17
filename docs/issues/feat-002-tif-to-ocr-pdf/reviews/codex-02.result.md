**高**

なし。前回の「最終出力パスへの直接書き込みで不完全 PDF が残る」問題は、[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-002-tif-to-ocr-pdf/design.md:93) の一時ファイル + `fsync` + `os.replace` 設計で解消されています。前回の「壊れた TIFF が事前検証を通る」問題も、[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-002-tif-to-ocr-pdf/design.md:120) の `im.load()` 明記で解消されています。

**中**

1. `--overwrite` なしでも競合時に出力ファイルを上書きし得る  
[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-002-tif-to-ocr-pdf/design.md:96) は置換直前に存在確認しますが、その直後に [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-002-tif-to-ocr-pdf/design.md:97) で `os.replace` するため、確認後から置換前の間に同名ファイルが作られると上書きします。[requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-002-tif-to-ocr-pdf/requirements.md:43) の意図しない上書き防止としては穴があります。

修正提案: `overwrite=False` では `os.replace` を使わず、同一ディレクトリ内の一時ファイルを `os.link(tmp, output)` で no-clobber に確定し、成功後に tmp を削除する設計にする。競合をスコープ外にするなら、その前提を明記する。

2. 書き込み失敗テストが実際の書き込み失敗を検証していない  
[requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-002-tif-to-ocr-pdf/requirements.md:46) は「書き込み途中の失敗」を受け入れ基準に追加していますが、[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-002-tif-to-ocr-pdf/design.md:159) のテストは `build_pdf` を例外化しており、書き込み処理に入る前に失敗します。これでは atomic write の失敗時 cleanup と既存ファイル不変を検証できません。

修正提案: `write_pdf_atomic` を直接テストし、`NamedTemporaryFile.write` または `os.replace` を monkeypatch して `OSError` を発生させる。既存ファイル不変、一時ファイル削除、戻り値/終了コード 1 を確認する。

**低**

なし。