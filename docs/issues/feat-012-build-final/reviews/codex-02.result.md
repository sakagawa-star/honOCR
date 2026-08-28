> 日付: 2026-08-28 / 対象: requirements.md・design.md（背景: README.md）
> session id: 01a0467c-a330-7c22-80c6-4e560b02873f / 区分: 再(2回目)
> 検出: 高2
> Claude Code の対応: 全件反映。(1)validate_inputs のシグネチャに normalized_dir を追加し §7 と呼び出し側も更新 (2)出力先本体と outdir/images のシンボリックリンクを is_symlink() で拒否（検証9・10、テスト2件追加）

---

前回指摘の2点は解消されています。

- 入出力ディレクトリの重なりは、実体パス比較で双方向に拒否する仕様・テストが追加されています。
- `images/` が通常ファイルの場合と、コピー中の `OSError` は、事前検証または終了コード 1 のエラー処理として定義されています。

残る重大な指摘は以下です。

| 重要度 | 問題 | 修正提案 |
|---|---|---|
| 高 | `validate_inputs` の定義に `normalized_dir` がありませんが、検証6では `normalized_dir.resolve()` を使う設計です。このままのインターフェースでは、重なり検査を設計どおり実装できません。 | シグネチャを `validate_inputs(normalized_dir, md, content_list, outdir, overwrite)` に変更し、§7のインターフェース定義も同じ形に更新する。あるいは `md.parent` を入力ディレクトリとするなら、その仕様を明記する。 [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-012-build-final/design.md:157)、[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-012-build-final/design.md:178) |
| 高 | 出力先の既存 `images/` がシンボリックリンクの場合、`is_dir()` 判定は通ります。`--overwrite` 時のコピー・孤児削除はリンク先に対して実行されるため、final 外のファイルを上書き・削除し得ます。「シンボリックリンクを使わない」制約にも反します。`outdir` 自体がシンボリックリンクの場合も同様です。 | 事前検証で、既存の `outdir` と `outdir/images` がシンボリックリンクなら終了コード 1 で拒否する。`Path.is_symlink()` または `lstat()` を用い、通常の実ディレクトリだけを許可するテストも追加する。 [requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-012-build-final/requirements.md:196)、[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-012-build-final/design.md:173) |

中・低の指摘はありません。