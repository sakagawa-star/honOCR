> メタ: 2026-08-18 / 対象: feat-006 requirements.md・design.md / session id: 01a01332-7be7-7463-b7bd-aaf9c51e58df / 初回レビュー
> 対応: 高1（PDF再利用の同一性 → manifest 完全一致必須＋name 重複の事前エラー）・中3（ページ数検証を MinerU 前へ、glob を feat-005 と同一の2パターンに固定、pypdf を通常依存へ移動）すべて対応済み。codex-02 で解消を確認

**高**
- [requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-006-ocr-pipeline-cli/requirements.md:32) と [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-006-ocr-pipeline-cli/design.md:87) は既存 PDF 再利用を「ページ数一致」だけで許可しています。さらに出力は [name のみ](/home/sakagawa/git/honOCR/docs/issues/feat-006-ocr-pipeline-cli/requirements.md:17) で決まるため、同じ `name` の別ディレクトリや、TIF 差し替え後にページ数だけ同じケースで、別入力の PDF を OCR しても機械確認が通り得ます。これは成果物の正当性を壊す致命点です。  
  **修正提案**: 複数入力時は derived `name` の重複を事前エラーにする。既存 PDF はページ数だけでなく、対象 TIF の正規化パス列・サイズ・mtime ないし sha256 を記録した manifest と一致する場合だけ再利用する。manifest のない既存 PDF は `--overwrite-pdf` 必須、または明示的な `--trust-existing-pdf` を要求する。

**中**
- [requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-006-ocr-pipeline-cli/requirements.md:32) は「確認した上で再利用」としていますが、[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-006-ocr-pipeline-cli/design.md:68) と [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-006-ocr-pipeline-cli/design.md:75) では PDF ページ数検証が MinerU 実行後の機械確認に回っています。不一致 PDF でも長時間の MinerU を走らせ、失敗 run を残します。  
  **修正提案**: PDF 生成直後または既存 PDF 再利用判定直後、MinerU 起動前にページ数検証を行う設計に変更する。§4.2 の機械確認では再確認扱いにする。

- feat-005 の全TIF定義は `page-*_1L.tif` と `page-*_2R.tif` ですが、feat-006 の既定 glob は [requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-006-ocr-pipeline-cli/requirements.md:18) / [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-006-ocr-pipeline-cli/design.md:34) で `page-*_[12][LR].tif` になっており、`1R`/`2L` も拾います。余分な同系統ファイルがあると feat-005 と同一入力列ではなくなります。  
  **修正提案**: 既定列挙を `page-*_1L.tif` と `page-*_2R.tif` の2 glob 結合 + sort に固定する。単一 `--glob` を残すなら、既定とは別の上級オプションとして扱い、feat-005 同一レイアウト実行では使わない前提を明記する。

- [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-006-ocr-pipeline-cli/design.md:26) は `ocr_dir.py` の実行時に `pypdf` を使いますが、現状の [pyproject.toml](/home/sakagawa/git/honOCR/pyproject.toml:14) では `pypdf` は dev group で、[TECH_STACK.md](/home/sakagawa/git/honOCR/docs/TECH_STACK.md:20) もテスト用途としています。CLI の実行環境定義として不整合です。  
  **修正提案**: `pypdf` を通常 dependency に移すか、CLI 実行は dev group 同期済み環境を前提にすると明記する。前者なら TECH_STACK の用途も「PDFページ数確認」に更新する。

**低**
- 致命的な低重要度指摘はありません。