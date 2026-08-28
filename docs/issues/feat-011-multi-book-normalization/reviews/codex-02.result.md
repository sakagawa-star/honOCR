> 日付: 2026-08-28 / 対象: requirements.md・design.md（背景: README.md）
> session id: 01a045e9-e5d6-77b2-b77c-c9d6df0c0aac / 区分: 再(2回目)
> 検出: 高1・中1
> Claude Code の対応: 全件反映。(1)MVP を「FR-003 を除く7件」に変更し FR-002 を MVP に含めた (2)ADR-2 の「15箇所」を md 13箇所・json 23箇所に訂正し置換対象外3件と区別

---

前回の「新規ファイル」と「アスタリスク個数」の不一致は解消されています。件数も受け入れ基準は13件へ訂正されていますが、設計内に15件の記載が残っています。

## 高

- MVPの範囲が、MVPに含めるFRの受け入れ条件と矛盾しています。  
  [requirements.md:227](/home/sakagawa/git/honOCR/docs/issues/feat-011-multi-book-normalization/requirements.md:227) はFR-002・FR-003をMVP外としますが、MVPに含めるFR-004はFR-002の8字置換を許可・残存検査の必須条件にし、FR-007はFR-002の13件置換およびFR-003の警告件数を受け入れ条件にしています。  
  したがって、記載どおりFR-002/003を実装しないMVPではFR-004/007を満たせません。  
  修正案: MVPにFR-002とFR-003を含めるか、MVP時点のFR-004/007から字形正規化・JIS外警告に依存する条件を分離してください。

## 中

- 前回指摘した件数の自己矛盾は主要な受け入れ基準では13件に修正されていますが、ADRに「PRMLでは15箇所」が残っています。  
  [design.md:535](/home/sakagawa/git/honOCR/docs/issues/feat-011-multi-book-normalization/design.md:535) は15件、[requirements.md:167](/home/sakagawa/git/honOCR/docs/issues/feat-011-multi-book-normalization/requirements.md:167) と [design.md:435](/home/sakagawa/git/honOCR/docs/issues/feat-011-multi-book-normalization/design.md:435) は13件です。  
  修正案: ADR-2の15箇所を13箇所へ修正し、置換対象外の3件とは区別して記載してください。

## 低

該当なし。