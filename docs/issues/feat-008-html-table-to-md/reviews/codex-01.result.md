以下、実害があるものだけです。低重要度の指摘はありません。

**高**
- [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-008-html-table-to-md/design.md:65) は `Path.read_text(encoding="utf-8")` で「改行は正規化しない」としているが、Python の既定テキスト読み込みは `\r\n` / `\r` を `\n` に変換する。これだと [requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-008-html-table-to-md/requirements.md:33) の「表行以外はバイト単位で不変」と、[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-008-html-table-to-md/design.md:102) の「表行0件はバイト同一」を満たせない。
  修正提案: 本文読み込みは `Path.read_text(encoding="utf-8", newline="")` または `read_bytes().decode("utf-8")` に変更する設計にする。CRLF の表なしファイル、CRLF の表ありファイルの回帰テストを追加する。

**中**
- [requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-008-html-table-to-md/requirements.md:54) は FR-001〜FR-003 を pytest で検証するとしているが、[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-008-html-table-to-md/design.md:169) の `ocr_dir.py` 追加テストは `parse_table_summary` だけで、FR-003 の本体である「機械確認合格後だけ変換する」「変換失敗時 FAIL」「スキップ警告は FAIL にしない」が未検証。
  修正提案: `ocr_dir.py` 側に小さな変換実行 helper を切り出し、`subprocess.run` を stub/monkeypatch して PASS 時の呼び出し、非0終了時の FAIL、stderr 警告時の PASS をテストする。

- [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-008-html-table-to-md/design.md:136) の `parse_table_summary` は stdout が想定書式に合わない場合 `(0, 0)` を返すため、変換スクリプトが壊れて件数を出さなくても `ocr_dir.py` 側は PASS になり得る。§4.1 で stdout 書式を固定して [ocr_dir.py がパースする](/home/sakagawa/git/honOCR/docs/issues/feat-008-html-table-to-md/design.md:54) としているので、これは機械契約違反を握りつぶしている。
  修正提案: パース失敗は `HTML表変換失敗: summary parse failed` として FAIL にする。stdout 全文を理由に含めるかログ表示する。

- raw `<` を含むセルの扱いが要求と設計で曖昧です。[requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-008-html-table-to-md/requirements.md:16) の「単純表」条件にはセル内 raw `<` の除外がない一方、[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-008-html-table-to-md/design.md:86) は `$a<b$` をスキップ扱いにします。表内数式が目的なので、不等号入り数式の表が出た場合に問題が残ります。
  修正提案: raw `<` をスキップ条件として requirements に明記するか、既知タグだけをタグとして扱い、それ以外の `<` はセルテキストとして保持する方針に変更する。どちらにするかを受け入れ基準とテストで固定する。