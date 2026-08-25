**指摘**

- **高: 公開分離要件に反する式文字列が要求仕様に入っています。**  
  [requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-010-apply-fixes/requirements.md:35) が具体的な式文字列を受け入れ基準に含めています。一方、[README.md](/home/sakagawa/git/honOCR/docs/issues/feat-010-apply-fixes/README.md:47) はリポジトリ内ドキュメントに書籍本文由来の文字列を書かない方針です。将来公開時の分離要件をこのドキュメント自身が破ります。  
  **修正提案**: 式の内容は書かず、「README 調査表 #1 の対象式」「content_list index 217〜219」「該当式ブロック先頭/次式」などの番号・位置参照だけに置き換える。

- **高: 統合型 array の分割仕様が、実データ上の LaTeX 構造と衝突します。**  
  [requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-010-apply-fixes/requirements.md:79) と [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-010-apply-fixes/design.md:236) は、array の各行の LaTeX 本体を変更せず独立 `$$...$$` に分割するとしています。しかし対象の chap02 統合型ブロックには alignment marker `&` が含まれており、そのまま display math に出すと壊れます（実データ: [/home/sakagawa/work/Pattern_Recognition_and_Machine_Learning/ocr/final/chap02/chap02_gray300.md](/home/sakagawa/work/Pattern_Recognition_and_Machine_Learning/ocr/final/chap02/chap02_gray300.md:1644)）。  
  **修正提案**: 「array 環境外へ出す際は、行頭/等号前の alignment marker `&` と行末 `\\` は構文要素として除去する。数式トークン自体は変更しない」と明記し、対象3件それぞれで許される構文除去を定義する。

- **中: skipped 判定が甘く、適用失敗を正常終了にできます。**  
  [requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-010-apply-fixes/requirements.md:48)〜[requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-010-apply-fixes/requirements.md:56) は `old` 不在でも `new` が1回以上あれば skipped、`new` 空なら常に skipped とします。これは「OCR 出力変化で適用不能ならエラー検出する」という目的と衝突します。特に削除修正は初回から `old` が無くても成功扱いになります。  
  **修正提案**: `new == ""` を禁止するか、削除修正には `applied_marker` / `postcondition` のような確認用フィールドを追加する。少なくとも skipped は `count(new) == 1` を要求し、`>=2` は曖昧としてエラーにする。
---

## Claude Code の対応方針（2026-08-25）

- メタ: 対象 = requirements.md / design.md（初回）
- **高1（公開分離違反）**: 採用。FR-001 の受け入れ基準から式文字列を除去し、README 調査表番号・content_list インデックスによる位置参照に置換。案件 README 調査表の同様の1箇所も修正
- **高2（array 分割と `&` の衝突）**: 採用。実データで裏取り（chap02 = `{r l}` 環境・`&` 2個、chap05 の2件 = `{l}` 環境・`&` なし）。「分割時に除去してよいのは構文要素（`\begin{array}{…}`・`\end{array}`・`&`・`\\`）のみ、数式トークンは変更しない」と FR-006・design §10・ADR に明記
- **中1（skipped 判定の甘さ）**: 採用。`new` 空（削除専用修正）を禁止し（検証エラー）、削除は前後文脈を含む置換で表現する方式に変更。適用済み判定は `count(new) == 1` の厳密判定とし、0 はエラー（適用不能）、2 以上もエラー（曖昧）。FR-002/003、design §4.2/§4.3/§8/§9/§12、ADR を更新
