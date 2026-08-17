**レビュー結果**

**高: MinerU 実行コマンドがそのままでは起動不能**
[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-003-mineru-trial/design.md:52) は stdout/stderr を `{OUT}/ocr/mineru-trial/run.log` に保存するとしていますが、`mineru-trial/` を事前作成する手順がありません。シェルリダイレクトは親ディレクトリがないと MinerU 起動前に失敗します。

修正提案: §4.2 手順1〜3に `mkdir -p {OUT}/ocr/mineru-trial` を明記する。再実行時の `run.log` は上書き禁止なら `run-001.log` など連番に固定する。

**高: 項目Aが欠落数式を検出できず、n=0でも合格し得る**
[criteria.md](/home/sakagawa/git/honOCR/docs/issues/feat-003-mineru-trial/experiments/trial-quality/criteria.md:15) は Markdown に出た数式を母集団にしており、MinerU が原本の番号付き数式を落とした場合、その数式はサンプル対象外になります。さらに [criteria.md](/home/sakagawa/git/honOCR/docs/issues/feat-003-mineru-trial/experiments/trial-quality/criteria.md:17) の `ceil(0.8 × n)` では n=0 が合格になり得ます。Go/No-Go 判定として致命的です。

修正提案: 母集団を「原本 chap-01 の先頭20件の番号付き独立数式」に変更し、Markdown 側に対応式が存在しなければ不一致とする。n は原本側の件数で固定し、原本側が20件未満の場合のみその件数を分母にする。n=0は判定不能ではなく No-Go にする。

**高: ページ・サンプル対応の入力が不足しており、項目Cを一意に判定できない**
FR-003 の入力は Markdown と原本画像のみです（[requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-003-mineru-trial/requirements.md:45)）。一方、項目Cは PDF の 5・15・25・35・45ページ内の Markdown 順序を判定します（[criteria.md](/home/sakagawa/git/honOCR/docs/issues/feat-003-mineru-trial/experiments/trial-quality/criteria.md:27)）。Markdown だけでは「どの本文ブロックがどのPDFページ由来か」が安定して特定できません。FR-002 も JSON 生成を要求しているのに、完了確認は Markdown と `$$` だけです（[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-003-mineru-trial/design.md:55)）。

修正提案: FR-003 入力に MinerU JSON/content list を明示追加し、FR-002 受け入れ基準にも JSON 生成確認を入れる。項目A/B/C は `page_idx` 等のページ情報を使って対応付ける、と criteria に固定する。

**中: 項目B/Cの判定単位と誤りカウントが未定義で事後解釈が残る**
項目Bの「本文段落」「3行以上」「誤認識が2文字以下」（[criteria.md](/home/sakagawa/git/honOCR/docs/issues/feat-003-mineru-trial/experiments/trial-quality/criteria.md:21)）と、項目Cの「テキストブロック」（[criteria.md](/home/sakagawa/git/honOCR/docs/issues/feat-003-mineru-trial/experiments/trial-quality/criteria.md:28)）が操作可能な単位として固定されていません。段落の分割・結合、空白、句読点、全半角、改行をどう数えるかで判定が変わります。

修正提案: criteria lock 前に、サンプルID、原本ページ、ページ内段落番号/ブロック番号を固定する。誤りカウントは「正規化対象」「無視する差分」「1文字として数える単位」「段落分割・結合時の扱い」を明文化する。

低重要度の指摘はありません。上記は criteria lock 前に直すべき高・中のみです。