> 日付: 2026-08-28 / 対象: requirements.md・design.md（背景: README.md）
> session id: 01a045e9-e5d6-77b2-b77c-c9d6df0c0aac / 区分: 再(3回目)
> 検出: 高1
> Claude Code の対応: 全件反映。FR-008 に「FR-003 不採用時はそのテスト5件を追加しない」例外規定を追加し、design §10.1 にも明記

---

前回の2点は解消されています。

- MVPにはFR-002が含まれ、FR-004/FR-007との依存も明記されています。
- ADR-2のPRML差分は、Markdown 13件・JSON 23件へ統一されています。

## 高

- FR-003をMVPから除外可能としながら、MVPに含まれるFR-008がFR-003のテスト実装を必須にしています。  
  [requirements.md:233](/home/sakagawa/git/honOCR/docs/issues/feat-011-multi-book-normalization/requirements.md:233) はFR-003を唯一の任意項目としますが、[requirements.md:188](/home/sakagawa/git/honOCR/docs/issues/feat-011-multi-book-normalization/requirements.md:188) はFR-001〜FR-006すべての受け入れ基準に対応するテストを要求します。FR-003を不採用にすると、その機能とテストを実装せずにFR-008を満たすことができません。  
  修正案: FR-003不採用時はFR-008の対象を「FR-001・FR-002・FR-004〜FR-006」に変更する例外規定を追加し、設計§10のFR-003テストも「採用時のみ」と明記してください。

## 中

該当なし。

## 低

該当なし。