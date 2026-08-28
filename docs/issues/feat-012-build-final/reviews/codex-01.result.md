> 日付: 2026-08-28 / 対象: requirements.md・design.md（背景: README.md）
> session id: 01a0467c-a330-7c22-80c6-4e560b02873f / 区分: 初回
> 検出: 高1・中1
> Claude Code の対応: 全件反映。(1)出力先と入力ディレクトリの重なり（同一・入れ子）を resolve() で検出し --overwrite の有無によらず拒否（ADR-7 追加） (2)images が通常ファイルの場合を書込み前検証に追加し、構築中の OSError 捕捉を明記

---

重大な指摘は2件です。低重要度の指摘はありません。

| 重要度 | 問題 | 修正提案 |
|---|---|---|
| 高 | `--overwrite` 時に `outdir == normalized_dir` を許容しており、コピー元を変更しないという要求に反します。設計自身も `os.replace` で同一ファイルを置換すると明記しており、さらに `outdir` を正規化済みディレクトリ配下に指定すれば md や `images/` を入力側に新規作成できます。これは「コピー元を変更・削除しない」非機能要件を破る入力です。 | コピー開始前に `resolve()` 済みパスで入力・出力の重複／入れ子を検査し、少なくとも `outdir == normalized_dir` と `outdir` が `normalized_dir` 配下である場合は、`--overwrite` の有無にかかわらず終了コード 1 で拒否する。安全側に寄せるなら両者が互いに配下にならないことを要求する。 [requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-012-build-final/requirements.md:188)、[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-012-build-final/design.md:205) |
| 中 | `images_src` の異常状態が定義・検証されていません。`images/` が通常ファイルだった場合、設計上の「直下のファイル列挙」で `NotADirectoryError` となり得ます。また出力側 `images/` が通常ファイルの場合も `mkdir()` が例外になります。どちらも入力検証後・一部コピー後に起こり得るため、定義されたエラー報告ではなく例外終了や中途半端な出力になります。 | `validate_inputs` に、存在する `images_src` と既存の `outdir/images` がディレクトリであることを追加し、違反時は書込み前に標準エラー＋終了コード 1 とする。併せてコピー・列挙中の `OSError` を捕捉し、構築エラーとして終了コード 1 を返す方針を明記する。 [design.md](/home/sakagawa/git/honOCR/docs/issues/feat-012-build-final/design.md:97)、[design.md](/home/sakagawa/git/honOCR/docs/issues/feat-012-build-final/design.md:199)、[requirements.md](/home/sakagawa/git/honOCR/docs/issues/feat-012-build-final/requirements.md:76) |

それ以外については、feat-005 §4.4 の「md参照の解決」と `content_list` の画像集合完全一致、図0件の扱い、章単位の失敗分離は、要求・設計・既存 `colorize_images.py` のI/F間で整合しています。