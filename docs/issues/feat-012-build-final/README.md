# feat-012: final ディレクトリ構築の自動化（build_final.py）

- ステータス: Closed（2026-08-28 完了。実装・自動テスト・実データ検証・ユーザー実機テスト済み）
- 起票日: 2026-08-28
- 種別: feat（機能追加）

## 1. 背景

`ocr_dir.py` のパイプラインは「入力PDF生成 → MinerU → 正規化 → 機械確認 → HTML表変換 →
脚注挿入 → 修正適用」までで終わり、**図画像を扱わない**。そのため正規化済み出力
（`run-NN-normalized/`）には md と content_list.json しか置かれず、md 中の
`![](images/…)` の参照が解決できない（2026-08-28 のユーザー手動テストで確認された）。

LLM に渡せる最終成果物 `final/chapNN/` を作るには、feat-005 で定義された次の手作業が
章ごとに必要である。

1. `colorize_images.py` で `run-NN-normalized/images/` を生成する
2. md・content_list.json・images/ を `final/chapNN/` へコピーする
3. 3種類の機械検証（バイト同一・md の画像参照の解決・content_list の `img_path` 集合の一致）

PRML（8章）では一度きりの作業として許容できたが、次に処理する『プログラミングのための確率統計』は
**10章**ある。同じ手作業を10回繰り返す前に自動化する（2026-08-28 ユーザー決定）。

## 2. 調査で確認した既存の仕組み

- **final の構造と検証項目**: `docs/issues/feat-005-full-conversion/design.md` §4.4 に
  手順とチェック項目が定義されている。本案件はこれをコード化する
  （コピーで集約する・ベース名を維持する・`middle.json` 等は含めない、は feat-005 の ADR-5/6/7）
- **`colorize_images.py` の I/F**（feat-007）: 引数は `content_list` `tif_dir` `-o` で、
  出力ファイル名は `img_path` の basename。図 0 件でも空ディレクトリを作って
  終了コード 0 を返す。標準出力のサマリは `blocks={n} unique={n} outdir={path}`
- **PRML の実績**（feat-005 work_log）: chap07 は図 0 件で空 `images/`。
  chap01/02/06 は md 参照画像が content_list の `img_path` の真部分集合になる
  （content_list からのみ参照される画像が存在する）。この2点を境界条件として設計に反映した

## 3. スコープ

- `scripts/build_final.py` の新設（集約＋3種類の検証）
- `scripts/ocr_dir.py` への `--final` 追加（カラー再切出 → final 構築を章単位で実行）
- 自動テスト（新規 `tests/test_build_final.py` と `tests/test_ocr_dir.py` への追加）

### スコープ外

- 確率統計の実データ本処理（全10章の OCR）は本案件完了後に別案件で行う
- PRML の既存 `final/` の作り直し（本案件では**変更しない**。検証は一時ディレクトリで行う）
- `colorize_images.py` 自体の変更（呼び出されるだけで、I/F は変えない）

## 4. 決定事項

| 論点 | 決定 | 根拠 |
|---|---|---|
| final の構築単位 | **章ごと**（1章の処理完了ごとに構築） | 2026-08-28 ユーザー決定。ある章が FAIL しても完成章の成果物は使える |
| `--final` の既定 | オプトイン（既定は構築しない） | 既存の呼び出しの動作を変えない（`--fixes-dir` と同じ方針） |
| 画像生成の担当 | `ocr_dir.py` が `colorize_images.py` を呼ぶ。`build_final.py` は呼ばない | `build_final.py` の入力を「正規化済みディレクトリ」1つに保つ（design.md ADR-5） |
