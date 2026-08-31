> 日付: 2026-08-28 / 対象: requirements.md・design.md・README.md（実装中断後の設計修正）
> session id: 01a05545-fb31-7d93-9fc2-3d10ec15f320 / 区分: 再(4回目・実装中断後の設計修正)
> 検出: 高1
> Claude Code の対応: 反映。実装再開手順に「リポジトリ外の chap02.json・chap06.json を新定義へ更新する工程」が欠けていた（実際に旧定義のまま残存していることを実データで確認）。README §7.5 に再開手順0として追加し、章ごとの期待結果を表にした

---

| 重要度 | 問題 | 修正提案 |
|---|---|---|
| 高 | README §7.4 の再開手順は「全10章で手順1〜3を最初から実行」とするだけで、失敗原因だったリポジトリ外の `{BASE2}/ocr/fixes/chap02.json`・`chap06.json` を新しい文脈付き定義へ更新する工程／更新済み確認がありません。中断時に実行された定義は旧 `\text {亻} → \text {イ}` であり、これを更新しなければ再実行しても同じ最終不変条件違反で停止します。([README.md:128](/home/sakagawa/git/honOCR/docs/issues/feat-013-expand-cjk-table/README.md:128), [README.md:175](/home/sakagawa/git/honOCR/docs/issues/feat-013-expand-cjk-table/README.md:175)) | §7.4 の先頭に再開手順0を追加し、外部の `chap02.json`・`chap06.json` を設計§5.1/§5.4の新定義へ置換したことを明示してください。続けて、各章で `count(old)==1`・適用後 `count(new)==1`、chap02/06 は `1 applied, 0 skipped`、chap04/05 は skip、chap09 は再正規化後に applied、を確認してから final 再構築へ進む手順にします。 |

修正定義そのものは妥当です。文脈を `old` / `new` の双方へ含め、適用後の `count(new)==1` を受け入れ基準と設計確定値に追加したため、`apply_fixes.py` の最終不変条件と整合しています。([requirements.md:127](/home/sakagawa/git/honOCR/docs/issues/feat-013-expand-cjk-table/requirements.md:127), [design.md:250](/home/sakagawa/git/honOCR/docs/issues/feat-013-expand-cjk-table/design.md:250))

上記以外に致命的な問題はありません。