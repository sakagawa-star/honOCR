> メタ: 2026-08-18 / 対象: feat-007 investigation.md（イテレーション1）・requirements.md・design.md / session id: 01a021d3-62ff-7143-8924-b2957221f9d4 / 差し戻しレビュー（3回目）
> 対応: 中2件（validate への scale 接続、--overwrite 再生成手順）対応済み。codex-04 以降で追加指摘も解消

**高**
- なし。

**中**
- `--scale` 検証が設計上の関数I/Fに接続されていません。  
  FR-002 は `--scale <= 0` を終了コード1・出力なしにすると定義し、設計の検証表にも追加されていますが、`validate` のシグネチャは `scale` を受け取らないままです。実装者が §4.2 を `validate` に集約すると、追加検証を落としやすい状態です。  
  参照: [requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-007-colorize-images/requirements.md:44), [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-007-colorize-images/design.md:84), [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-007-colorize-images/design.md:134)  
  **修正提案**: `validate(blocks, tifs, outdir, overwrite, scale)` に変更し、処理フローにも `args.scale` を検証フェーズへ渡すことを明記してください。可能なら `scale <= 0` だけでなく `NaN` / `inf` も拒否する条件にすると堅いです。

- BUGFIX の確認手順が design §10 に反映しきれていません。  
  investigation では chap00〜03 の既存 `images/` を `--overwrite` で再生成し、「カラーのまま・従来と同等の表示サイズ」を確認するとしています。一方 design §10 の動作確認コマンドは `--overwrite` なしの chap01 のみで、手動テストも「カラーで表示」までです。既に oversized 画像がある環境ではコマンドが既存ファイル拒否で失敗するか、表示サイズ修正の確認が曖昧になります。  
  参照: [investigation.md](/home/sakagawa/git/honOCR/docs/issues/feat-007-colorize-images/investigation.md:47), [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-007-colorize-images/design.md:158), [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-007-colorize-images/design.md:159)  
  **修正提案**: design §10 に `--overwrite` 付き再生成手順を明記し、手動テスト条件を「カラーで表示され、旧グレー画像と同等の表示サイズ」に更新してください。

**低**
- なし。