# codex-74: M3 閾値実験 criteria（出力先の親ディレクトリの規定の追加版）の全文ゲート（C）

- **日付**: 2026-10-06
- **対象ファイル**: `docs/issues/feat-025-inline-math-markup-survey/m3-pilot-measure/experiments/thresholds/criteria.md`（関連: 同フォルダの `extract_samples.py`・`measure_glyphs.py`）
- **ストリーム名**: `rev-honocr-feat-025`
- **依頼種別**: **C**（全文ゲート。本レビュー単位で 1 回目）
- **直前に `/new` を送ったか**: **Yes**（画面で会話のクリアを確認）
- **ゲート状態**: 本ファイルが当該 C
- **指摘数**: 高 **1** / 中 **0** / 低 **0**
- **収束判定**: **未収束**（次の手は未定。下記のとおりユーザーに判断を仰いでいる）
- **トークン実測**: `total_tokens` = 441,864（input 438,272 / cached_input 368,384 / output 3,592 / reasoning 2,019）
- **rollout jsonl**: `/home/sakagawa/.codex/sessions/2026/10/06/rollout-2026-10-06T16-24-42-01a11019-b54b-7f60-a5a1-c74b43574fc3.jsonl`

## レビュー結果（回収した内容）

[AGENTS.md適用]

**高**: 書き込み権限がない既存の親ディレクトリで、規定の運用エラー（標準エラー出力・終了コード 1）にならず未処理の例外で終了する。共通規定は権限不足時の扱いを要求しているが、`mkdir(..., exist_ok=True)` は既存ディレクトリなら成功し、その後の `open`・`write_text`・`Image.save`・`tempfile.mkdtemp` などは `PermissionError` を捕捉していない。対象は `population`・`sample`・`locate`・`annotate`・`compute`・`fail`・`summarize`。例: criteria.md 317 行目の約束に対し、`extract_samples.py` 188 行目、`measure_glyphs.py` 172 行目。

修正案: 各書き込み・一時ファイル／一時ディレクトリ作成を `OSError` として `OpError` に変換するか、`main` で該当する `OSError` を捕捉して標準エラー出力と終了コード 1 に統一する。部分出力が残る操作は、既存の `locate` と同様に後片付けも定義する。

親ディレクトリが存在しない場合の作成処理そのものは、文書の追加規定と実装で一致している。

## 対応（Claude Code 本体）

「書き込みの失敗が未処理の例外になる」という同じ種類の指摘が 3 回続いた（実データでの `population` の異常終了 → codex-72 の `--log` の親と `mkdir` → 本 C の書き込み全般）。`CLAUDE.md`「行き詰まり検出」に従い、箇所ごとに塞ぐ修正を重ねる方針を取り下げ、ユーザーに方針の選択を仰いだ（2026-10-06）。
