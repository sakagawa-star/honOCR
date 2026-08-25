**前回指摘の確認**

前回の3件は解消されています。

- 公開分離違反: 具体式文字列は削除され、位置参照に変更済みです。
- array 分割仕様: `&` / `\\` などの構文要素除去が明記され、実データとの衝突は解消済みです。
- skipped 判定: `new` 非空必須、`count(new) == 1` の厳密判定になり、削除修正の抜け道は解消済みです。

**指摘**

- **中: 冪等性を保証する最終不変条件がまだ不足しています。**  
  [requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-010-apply-fixes/requirements.md:49)〜[requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-010-apply-fixes/requirements.md:56) は再実行時に全件 skipped になることを要求していますが、[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-010-apply-fixes/design.md:74)〜[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-010-apply-fixes/design.md:80) の検証と [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-010-apply-fixes/design.md:86)〜[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-010-apply-fixes/design.md:102) の適用規則だけでは、`old` が `new` に残る修正や、後続 fix が先行 fix の `new` をさらに変更する修正を防げません。その場合、初回は成功しても再実行で applied または error になり得ます。  
  **修正提案**: 出力前の最終検証として、全 fix について「最終 md 内で `count(old) == 0` かつ `count(new) == 1`」を要求し、満たさなければエラーとして出力しない、と FR-003 / §4.3 に追加してください。併せて `old` が `new` に含まれるケース、後続 fix が先行 fix の `new` を消すケースのテストを追加すると、この穴を固定できます。

高・低の新規致命的指摘はありません。
---

## Claude Code の対応方針（2026-08-25）

- メタ: 対象 = requirements.md / design.md（再レビュー）。session id: 01a036f3-2af5-7202-83dc-226f84263c8e（codex-01 から resume）
- **中1（冪等性の最終不変条件不足）**: 採用。FR-003 に規則 6（出力前に全 fix の `count(old) == 0` かつ `count(new) == 1` を最終 md で検査、violate はエラーで出力しない）を追加。design §4.3 擬似コード・§8 エラー表・§9 README 記載事項・§12 テスト（#15 old ⊂ new、#16 fix 間干渉）を更新
