**高**

1. 失敗時に不完全 PDF を残さない要件を満たせない  
[requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-002-tif-to-ocr-pdf/requirements.md:60) は変換失敗時に不完全 PDF を残さないことを要求していますが、[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-002-tif-to-ocr-pdf/design.md:93) は最終出力パスへ直接一括書き込みする前提です。これは atomic ではないため、ディスク不足や `OSError` の途中発生で部分ファイルが残り得ます。`--overwrite` 時は既存 PDF を破損・喪失するリスクもあります。

修正提案: 最終パスへ直接書かず、同一ディレクトリの一時ファイルへ書き込み、flush/fsync 後に `os.replace()` で置換する設計に変更する。失敗時は一時ファイルを削除し、`--overwrite` なしの場合は置換直前にも既存確認する。書き込み失敗時に既存ファイルが不変であるテストも追加する。

**中**

2. 不正画像を「変換開始前」に検出する設計になっていない  
[requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-002-tif-to-ocr-pdf/requirements.md:43) と [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-002-tif-to-ocr-pdf/design.md:109) は事前検証を要求していますが、[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-002-tif-to-ocr-pdf/design.md:115) の `Image.open` はヘッダ識別中心で、画素データの読み込みは遅延されます。壊れた TIFF が検証を通り、変換フェーズで初めて失敗する可能性があります。

修正提案: 検証フェーズで `with Image.open(path) as im: im.load()` などにより実デコードまで行うことを明記する。壊れた TIFF/途中で切れた TIFF をテストデータに追加し、変換処理開始前に終了コード 1 となることを検証する。

**低**

なし。

外部確認: [Pillow 12.3.0 Image.open documentation](https://pillow.readthedocs.io/en/stable/reference/Image.html)