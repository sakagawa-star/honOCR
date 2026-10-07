# codex-62: M3 閾値実験 criteria と M3 文書（ADR-22 の新設）の解消確認（B）

- **日付**: 2026-10-06
- **対象ファイル**: `docs/issues/feat-025-inline-math-markup-survey/m3-pilot-measure/experiments/thresholds/criteria.md`、`docs/issues/feat-025-inline-math-markup-survey/m3-pilot-measure/design.md`、`docs/issues/feat-025-inline-math-markup-survey/m3-pilot-measure/requirements.md`
- **ストリーム名**: `rev-honocr-feat-025`
- **依頼種別**: **B**（解消確認。codex-61 の高 1 への対応〔ユーザー指示 2026-10-06 の案 A による M3 文書の改訂〕の確認）
- **レビュー単位**: criteria.md は criteria lock の単位（C 実施済み: `codex-60.result.md`）。`design.md`・`requirements.md` は M3 文書の単位（人レビュー未通過のため同一単位の修正。C 実施済み: `codex-55.result.md`）
- **直前に `/new` を送ったか**: No
- **ゲート状態**: **実施済み**（criteria.md: `codex-60.result.md` / M3 文書: `codex-55.result.md`）
- **指摘数**: 高 **0** / 中 **2** / 低 **0**
- **収束判定**: **未収束（次: 全件反映 → B）**
- **トークン実測**: `total_tokens` = 1,218,654（input 1,207,551 / cached_input 1,062,144 / output 11,103 / reasoning 5,587）
- **rollout jsonl**: `/home/sakagawa/.codex/sessions/2026/10/06/rollout-2026-10-06T10-04-39-01a10ebd-c2ad-79c0-9f9a-0527ef670f1d.jsonl`

## レビュー結果（回収した内容）

[AGENTS.md適用]

前回の高指摘は**解消**。ADR-22、C-309、criteria §0 が整合しており、閾値実験コードは M3 配下の実験コードとして事前に位置付けられ、S3 の実行手段・ログ・標本とは別であること、作成は委任し実データ測定は本体が行うことも明確。S3 に限る新規コード禁止との矛盾はない。

**中**

- 閾値実験コードは Pillow と numpy を使うが、criteria.md は「導入済み」とするだけで、`design.md` の技術スタックと ADR-22 に依存ライブラリ・固定バージョンが無い。`docs/TECH_STACK.md` にも numpy の記載が無い。実行環境を再現・検証できない
  - 修正案: Pillow 12.3.0 と numpy の lock 上の版を、既存依存を利用し追加導入しない旨とともに `design.md` の技術スタックへ記載し、必要なら `TECH_STACK.md` も更新する
- ADR-22 は実験コード作成時に「仕様に定めた動作確認」を行うとするが、criteria にはコード作成直後の動作確認手順・合格条件が無い。一方で C-306 は新規テストを置かないとする。抽出・連結成分計測の実装が仕様どおりかを、測定開始前に判断なしで確認できない
  - 修正案: 実験コード専用の最小の動作確認ケース、期待出力、実行コマンド、失敗時の中断を criteria または `design.md` に固定する

## 対応（Claude Code 本体）

### 中 1（依存と版）

`pyproject.toml` を確認したところ、Pillow は `dependencies` に `pillow==12.3.0` として宣言済み（`docs/TECH_STACK.md` 記載済み）だが、**numpy は宣言されておらず推移的依存（`uv.lock` 上 2.5.2）として入っているだけ**であった。直接使うと依存の追加に当たるため、**numpy を使わない仕様に改めた**。

- criteria.md §3.2: 使うのは Python 標準ライブラリと Pillow 12.3.0 だけ、numpy は使わない（理由つき）。`extract_samples.py` は標準ライブラリだけ
- `design.md` §1.3 に閾値実験の実験コードの行を追加（依存と版、numpy を使わない理由、`docs/TECH_STACK.md` の更新が不要であること）。ADR-22 に「依存」の項を追加

### 中 2（動作確認）

criteria.md に **§3.5「実験コードの動作確認」**を新設した。

- 両スクリプトに `--selftest` を持たせ、固定ケースがすべて期待どおりなら終了コード 0、違えば終了コード 1。実行コマンドを固定。**0 でなければ測定に進まず中断して報告する**
- `extract_samples.py`: 5 ケース（E1 = 4 群の混在と `token_pos`・`before`・`after`、E2 = 添字の先頭のギリシャ文字は SUP にだけ数える、E3 = `$$` の除外、E4 = 末尾の `^` の無視、E5 = 添字の先頭が `\mathrm` なら数えない）と期待出力
- `measure_glyphs.py`: 100×60 の画像に矩形 3 個（基準文字・標本・面積 4 の雑音）を描いたケースと期待値（成分 2 個、`H` = 20・`BL` = 39・`h` = 8・`r` = 0.4・`d` = 1.1）
- あわせて §3.2 に、外接矩形の座標の取り方（画素の添字・両端を含む、高さ = `ymax − ymin + 1`、下端 = `ymax`）と成分の番号の振り方（`(xmin, ymin)` の昇順）を明記した
- ADR-22 に「動作確認」の項を追加し、委任の範囲を「§3.5 の `--selftest` が終了コード 0 で終わることの確認まで」とした。§6 の手順 2 に動作確認を加えた
