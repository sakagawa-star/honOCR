**高**
- [requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-008-html-table-to-md/requirements.md:62) で chap07 の run-01-normalized md 復旧を FR-005 に追加している一方、[requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-008-html-table-to-md/requirements.md:78) はまだ「chap01・chap06 以外の既存データ」をスコープ外にしています。chap07 復旧が Must なのかスコープ外なのか矛盾します。
  修正提案: スコープ外を「HTML 表変換対象は chap01・chap06 以外対象外。ただし FR-005 の chap07 normalized md 復旧は対象」と明記してください。

**中**
- FR-005 の検証範囲と設計手順がずれています。[requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-008-html-table-to-md/requirements.md:65) は「全 md で `<table` 0」「content_list.json・images/ の sha256 不変」を要求していますが、[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-008-html-table-to-md/design.md:193) と [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-008-html-table-to-md/design.md:202) の手順は主に変換対象4 mdと final/chap01・chap06 の sha に限定されています。全8章 cmp はありますが、`<table` 0 と content/images 不変の検証対象が要求どおりに閉じていません。
  修正提案: 手順3.5後に、全8章の final/run-01-normalized md 16件で `<table` 0を確認する手順を追加してください。content_list/images も「全8章で sha 確認」するか、要求側を「本手順で触れないため final/chap01・chap06 の記録対象のみ」と狭めてください。

- [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-008-html-table-to-md/design.md:262) の実施方法がまだ「§4.5 の手順 1〜3」までになっており、追加された復旧手順 3.5 が完了手順から漏れています。
  修正提案: 「§4.5 の手順 1〜3.5」または「§4.5 の手順 1〜3.5 と手順4のユーザー確認」に更新してください。

「final が正」の根拠自体は、README の記録で致命的な不足は見ませんでした。feat-005 構築時 cmp PASS、final と生出力＋正規化の一致、mtime からの外的要因推定が揃っています。