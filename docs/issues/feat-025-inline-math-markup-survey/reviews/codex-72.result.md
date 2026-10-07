# codex-72: M3 閾値実験 criteria（出力先の親ディレクトリの規定の追加版）の初回レビュー（A）

- **日付**: 2026-10-06
- **対象ファイル**: `docs/issues/feat-025-inline-math-markup-survey/m3-pilot-measure/experiments/thresholds/criteria.md`（関連: 同フォルダの `extract_samples.py`・`measure_glyphs.py`）
- **ストリーム名**: `rev-honocr-feat-025`
- **依頼種別**: **A**（初回レビュー。criteria lock の人レビュー通過後の改版のため**新しいレビュー単位**）
- **直前に `/new` を送ったか**: No
- **ゲート状態**: **未実施**
- **指摘数**: 高 **0** / 中 **1** / 低 **0**
- **収束判定**: **未収束（次: 全件反映 → B）**
- **トークン実測**: `total_tokens` = 1,192,148（input 1,184,636 / cached_input 1,055,232 / output 7,512 / reasoning 3,854）
- **rollout jsonl**: `/home/sakagawa/.codex/sessions/2026/10/06/rollout-2026-10-06T16-09-04-01a1100b-6620-7b33-8408-44523851d07e.jsonl`

## レビュー結果（回収した内容）

[AGENTS.md適用]

**中**: `compute` / `fail` の `--log` は親ディレクトリ未作成時に未処理の `FileNotFoundError` で終了する。criteria は `measurements.jsonl` を「無ければ作る」とだけ定めているが、`append_jsonl`（`measure_glyphs.py` 169 行目）は親を作らず、`compute`・`fail` ともトレースバックになる。`--log` の親も作成し、失敗時はメッセージ付き終了コード 1 とする規定・実装を追加すること。

追加された `-o` 規定は `population`・`sample`・`locate`・`summarize` で一致している。`locate` は段 a の一時ファイル作成前に `-o` 親を作成しており、段 a〜c の後片付け規定とも矛盾しない。

なお同種の未処理例外は、`locate` の `--crops-dir` 親作成と `annotate` の `--out-dir` 作成でも残っている。いずれも `mkdir` 失敗を捕捉していないため、共通約束の「エラーは標準エラー出力・終了コード 1」に合わせるなら、同時に運用エラー化するのが適切。

## 対応（Claude Code 本体）

同じ種類の欠落を一度で塞ぐため、§3.6.1 の項を「**書き込み先のディレクトリが無ければ作ってから書く**」に一般化し、対象を 4 種に限定して列挙した（1 `-o` の親〔population・sample・locate・summarize〕、2 `--log` の親〔compute・fail〕、3 `--crops-dir` の親〔locate〕、4 `--out-dir`〔annotate〕。これ以外にディレクトリを作る箇所は無い）。作れなければ運用エラー（メッセージと終了コード 1）、作るのは入力の検査をすべて通った後・最初の書き込みの直前とした。

実装の修正は Sonnet サブエージェントに委任した（2: `append_jsonl` に親の作成と `OSError` → `OpError` を追加、3・4: 既存の `mkdir` を位置を変えずに `OSError` → `OpError` で囲む。メッセージは「書き込み先のディレクトリを作れない: {パス}（{例外}）」）。修正後、Claude Code 本体が 3 か所の変更と、両 `--selftest` が終了コード 0 であることを確認した。
