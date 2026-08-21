> メタ: 2026-08-18 / 対象: 同上 / 再レビュー（4回目）
> 対応: 高1件（同一ピクセルサイズと 1/3 丸めの矛盾 → 1%以内許容に緩和）対応済み

前回指摘2件は解消されています。

- `validate` への `scale` 接続: 解消。処理フローで `args.scale` を検証対象に含め、`validate(..., scale: float)` に更新されています。参照: [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-007-colorize-images/design.md:60), [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-007-colorize-images/design.md:84), [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-007-colorize-images/design.md:134)
- `--overwrite` 付き再生成と手動テスト条件: 解消。chap00〜03 の `--overwrite` 再生成と「カラーかつ旧表示サイズ相当」の確認が §10 に入りました。参照: [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-007-colorize-images/design.md:158), [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-007-colorize-images/design.md:159)

**高**
- `DEFAULT_SCALE=1/3` と「旧グレー画像と同一ピクセルサイズ」の確認条件が矛盾しています。  
  README 検証サンプルは旧画像 `631×946`、600dpi crop `1890×2833` です。設計どおり `round(width/3)` なら出力は `630×944` になり、[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-007-colorize-images/design.md:158) の「旧グレー画像（631×946）と同一ピクセルサイズ」は通りません。requirements/investigation でも「旧 MinerU 生成画像と同じピクセルサイズ」と書かれており、実測と合いません。  
  参照: [requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-007-colorize-images/requirements.md:27), [investigation.md](/home/sakagawa/git/honOCR/docs/issues/feat-007-colorize-images/investigation.md:9), [investigation.md](/home/sakagawa/git/honOCR/docs/issues/feat-007-colorize-images/investigation.md:23), [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-007-colorize-images/design.md:65)  
  **修正提案**: 仕様を「旧画像と同一ピクセルサイズ」ではなく「旧画像と同等の表示サイズ」に緩和し、動作確認は `DEFAULT_SCALE` の計算結果、例: サンプルなら `630×944`、または旧画像との差が数px/1%以内、のように判定してください。厳密に旧画像と同一サイズが必要なら、`1/3` 固定ではなく旧 MinerU 画像の実サイズを参照してリサイズする設計に変更が必要です。

**中**
- なし。

**低**
- なし。