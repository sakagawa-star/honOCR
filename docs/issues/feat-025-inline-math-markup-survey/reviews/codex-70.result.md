# codex-70: M3 閾値実験 criteria（実装者判断の明記版）の全文ゲート（C）

- **日付**: 2026-10-06
- **対象ファイル**: `docs/issues/feat-025-inline-math-markup-survey/m3-pilot-measure/experiments/thresholds/criteria.md`（関連: 同フォルダの `extract_samples.py`・`measure_glyphs.py`、`../../design.md` ADR-22）
- **ストリーム名**: `rev-honocr-feat-025`
- **依頼種別**: **C**（全文ゲート。本レビュー単位で 1 回目）
- **直前に `/new` を送ったか**: **Yes**（画面で会話のクリアを確認）
- **ゲート状態**: 本ファイルが当該 C
- **指摘数**: 高 **0** / 中 **1** / 低 **0**
- **収束判定**: **未収束（次: 全件反映 → B。2 回目の `/new` はしない）**
- **トークン実測**: `total_tokens` = 464,858（input 460,332 / cached_input 369,920 / output 4,526 / reasoning 2,586）
- **rollout jsonl**: `/home/sakagawa/.codex/sessions/2026/10/06/rollout-2026-10-06T16-09-04-01a1100b-6620-7b33-8408-44523851d07e.jsonl`

## レビュー結果（回収した内容）

[AGENTS.md適用]

**中**: `locate` の `crop_blocks.py` 失敗時、criteria の再実行可能性保証を実装していない。criteria.md §3.6.4 は一時ディレクトリの削除失敗を報告し、残存物を明示することを要求するが、実装は `extract_samples.py` 303 行目の `shutil.rmtree(tmp_dir, ignore_errors=True)` で握り潰す。削除に失敗すると隠れた一時ディレクトリが残り、本文が保証する状態復旧・中断報告が成り立たない。後続の段階で使う cleanup と同等の処理に置き換え、残存パスを標準エラーへ出すこと。

指定の 6 点（ギリシャ制御語集合、入れ子添字、§3.6.3〜5・7）は、確認した範囲で文書と実装が一致していた。`extract_samples.py --selftest` は成功。`measure_glyphs.py --selftest` は読み取り専用環境で一時ディレクトリを作れず実行不能。

## 対応（Claude Code 本体）

**文書（criteria.md）は正しく、実装が規定に従っていなかった**ため、文書は変更せず実装を規定に合わせた。コードの修正は `CLAUDE.md`「実装の実行方法」に従い Sonnet サブエージェントに委任した。

- `cleanup` 関数（中身は不変）を `crop_blocks.py` を呼ぶループの前に移動
- 終了コードが 0 以外のときの `shutil.rmtree(tmp_dir, ignore_errors=True)` を `cleanup([tmp_dir])` に置き換え（残ったパスを標準エラー出力に示す）
- 同種の穴として本体が見つけた、`subprocess.run` 自体が `OSError` を送出した場合も、`cleanup([tmp_dir])` してから `OpError`（`crop_blocks.py の起動に失敗（{章} ブロック {番号}）: {例外}`）で終了するようにした

修正後、Claude Code 本体が `ignore_errors` が残っていないことと、両 `--selftest` が終了コード 0（`OK (E1-E7)`・`OK (M1-M6)`）であることを確認した。
