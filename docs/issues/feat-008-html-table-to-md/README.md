# feat-008: MinerU 出力の HTML 表を Markdown パイプテーブルに変換（html_table_to_md.py）

- **ステータス**: Closed（2026-08-24 完了。ユーザー手動テストで chap01 表 1.1/1.2 の数式描画を確認）
- **種別**: feat（機能追加）

## 概要

MinerU は表を Markdown テーブルではなく **1行の HTML `<table>…</table>`** として Markdown に出力する。CommonMark の仕様では `<table` で始まる行は HTML ブロック（type 6）として素通しされ、内部の `$…$` は Markdown（数式）として解釈されない。そのため VS Code のプレビューで表 1.1 / 1.2（chap01）のセル内数式 `$w_{0}^{*}$` 等が LaTeX ソースのまま表示される（ユーザー報告 2026-08-24）。

対処として、Markdown 中の単純な HTML 表を **GFM パイプテーブル**に変換する後処理 CLI `scripts/html_table_to_md.py` を追加し、既存の最終成果物に適用する。あわせて `scripts/ocr_dir.py` の一括パイプラインに組み込み、今後の OCR 実行でも自動適用されるようにする。

## 調査記録（2026-08-24）

- 原因の確認: VS Code プレビューと同じパーサ（markdown-it。本環境では MinerU の推移的依存 `markdown-it-py` で再現）で該当行を解析すると、行全体が `html_block` トークンになる。本文段落（`inline` トークン）と異なり数式拡張が作用しない。VS Code の不具合でも OCR 誤りでもない
- 影響範囲（`{BASE}/ocr/final/chap*/*.md` 実測）: HTML 表は **chap01 に2件（表 1.1・表 1.2）、chap06 に1件（乱数表）** の計3件。数式を含むのは chap01 の2件のみ。他章は0件
- 3件とも構造は同一: **1行で `<table>` から `</table>` まで完結**、タグは `<table>` `<tr>` `<td>` のみ（属性なし。`<th>` `<thead>` `<tbody>` `colspan` `rowspan` なし）、セル内に `|` なし、全行の列数が一致（表 1.1: 5列×11行、表 1.2: 4列×11行、chap06: 10列×10行）。表の前後は空行
- content_list.json の `table` ブロックは `table_body` に同じ HTML を持つ（md とは別に保持）。content_list は座標・画像用のデータであり閲覧用ではないため、本案件では **md のみ変換し content_list は無改変**とする
- `final/chapNN/*.md` は `mineru-full/chapNN/run-01-normalized/*.md` とバイト同一（feat-005 の構築時検証）。既存データへの適用は final と run-01-normalized の両方に行い、同一性を維持する
- VS Code 側の設定で HTML ブロック内の数式を描画する手段はない。MinerU 3.4.4 に Markdown テーブルを直接出力するオプションもない
- 案件番号: ユーザー指示は「feat001」だったが feat-001 は「uv 環境構築」で使用済み（Closed）のため、連番の次にあたる feat-008 とした

## 実装中の発見（2026-08-24。Sonnet 実装時に検出、Claude Code 本体が調査）

FR-005 の検証で「final と run-01-normalized の md がバイト同一」が chap06 で不成立と判明。調査の結果:

- **final は全8章とも「MinerU 生出力（run-01/…/hybrid_auto/*.md）＋句読点正規化」とバイト一致**（chap06・chap07 は `sed 's/、/，/g; s/。/．/g'` 適用後の diff で無差分を確認）。final は忠実で正
- 損傷していたのは **run-01-normalized 側の md 2件**: chap06 = 末尾49行欠落（「# 上巻のための参考文献」セクション、3,350バイト）、chap07 = 先頭28行欠落（2,631バイト。追加・変更行は 0）。chap00〜05 は全章一致
- feat-005 の final 構築時（2026-08-21 15:05）は「md・content_list 計16ファイルのバイト同一（cmp）PASS」を記録済み。chap07 の normalized md の mtime は 2026-08-21 15:12:07 で **final 構築より後**。本リポジトリのスクリプトにこの時刻に normalized md へ書き込む処理はなく、損傷の原因プロセスは特定できなかった（エディタでの偶発的な部分保存等の外的要因と推定）。chap06 側の痕跡は本案件のインプレース変換（2026-08-24）で上書きされ失われたが、変換前バックアップ（スクラッチディレクトリ）で同型の欠落を確認済み
- content_list.json（final と normalized で cmp 一致）・images/ は全章無傷

対処: final を正として run-01-normalized の md 2件を final からコピーして復旧する（requirements.md FR-005・design.md §4.5 に反映）。chap07 は表 0 件で当初スコープ外だったが、同一原因の損傷のため本案件で併せて復旧する。

## 関連ドキュメント

- `requirements.md`: 要求仕様書
- `design.md`: 機能設計書
- feat-004: `normalize_punct.py`（CLI 仕様・原子的書き込みの参照元）、feat-006: `ocr_dir.py`（組み込み先）、feat-005: final の構成
