> メタ: 2026-08-18 / 対象: feat-007 requirements.md・design.md / session id: 01a021d3-62ff-7143-8924-b2957221f9d4 / 初回レビュー
> 対応: 高1（feat-005 final とのコピー元矛盾 → feat-005 FR-004/§4.4 を修正して整合）・中1（JPEG テストを許容誤差付きに変更）とも対応済み。codex-02 で解消を確認

レビュー結果です。致命的なものに絞りました。

**高**
- final 連携が現行 feat-005 と矛盾しています。  
  feat-007 はカラー画像を `run-NN-normalized/images/` に出す前提ですが、feat-005 の final 構築はまだ `run-NN/.../hybrid_auto/images/` をコピーする設計です。  
  参照: [feat-007 design.md](/home/sakagawa/git/honOCR/docs/issues/feat-007-colorize-images/design.md:116), [feat-007 design.md](/home/sakagawa/git/honOCR/docs/issues/feat-007-colorize-images/design.md:117), [feat-005 design.md](/home/sakagawa/git/honOCR/docs/issues/feat-005-full-conversion/design.md:123), [feat-005 design.md](/home/sakagawa/git/honOCR/docs/issues/feat-005-full-conversion/design.md:124)  
  このままだと、feat-007 を実装しても final 成果物にはグレー画像が入る経路が残ります。  
  **修正提案**: feat-007 の完了条件、または feat-005 側の FR-004 を更新し、final の images コピー元を `run-NN-normalized/images/` に固定してください。加えて「final 構築前に各章で colorize_images.py 済みであること」「unique img_path 数と生成数が一致すること」を受け入れ基準に入れるべきです。

**中**
- JPEG 出力なのに、テスト仕様がピクセル完全一致を要求しています。  
  要求・設計は JPEG quality 95 を指定していますが、設計の `test_crop_color_and_size` は「元画像の該当領域と一致」としています。JPEG は非可逆なので、カラー画素の完全一致 assert は成立しません。  
  参照: [requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-007-colorize-images/requirements.md:27), [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-007-colorize-images/design.md:63), [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-007-colorize-images/design.md:95)  
  **修正提案**: テストは `RGB`・サイズ・切り出し位置を確認し、画素比較は許容誤差つきにするか、同じ JPEG 設定で保存した期待画像との比較に変更してください。

**低**
- なし。