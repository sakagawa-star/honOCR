# codex-75: M3 閾値実験 criteria（書き込みの失敗の規定の追加版）の解消確認（B。全文ゲートの後）— 収束

- **日付**: 2026-10-06
- **対象ファイル**: `docs/issues/feat-025-inline-math-markup-survey/m3-pilot-measure/experiments/thresholds/criteria.md`（関連: 同フォルダの `extract_samples.py`・`measure_glyphs.py`）
- **ストリーム名**: `rev-honocr-feat-025`
- **依頼種別**: **B**（解消確認。codex-74 の高 1 への対応〔ユーザー指示 2026-10-06 の案 1 による方針の選び直し〕の確認）
- **直前に `/new` を送ったか**: No（C の後に 2 回目の `/new` は送らない）
- **ゲート状態**: **実施済み**（`codex-74.result.md`）
- **指摘数**: 高 **0** / 中 **0** / 低 **0**
- **収束判定**: **収束**（ゲート状態が「実施済み」の B で高・中ゼロ。根拠となる C の結果ファイル: `codex-74.result.md`）
- **トークン実測**: `total_tokens` = 896,619（input 891,092 / cached_input 794,112 / output 5,527 / reasoning 3,098）
- **rollout jsonl**: `/home/sakagawa/.codex/sessions/2026/10/06/rollout-2026-10-06T16-24-42-01a11019-b54b-7f60-a5a1-c74b43574fc3.jsonl`

## レビュー結果（回収した内容）

[AGENTS.md適用]

前回の高指摘は解消。`OSError` は両スクリプトの `main` で終了コード 1・標準エラー出力に統一され、親ディレクトリの作成だけでなく、一時ファイル／ディレクトリの作成、書き込み、置き換え、画像の保存も対象になっている。`population`・`sample`・`summarize` の原子的な出力、`annotate` の 2 出力の後片付け、`locate` 段 a の一時ファイル作成失敗時の後片付け、壊れた JSONL 行の `summarize` による検出も、§3.6.1 の追加規定と実装で整合している。今回の変更による致命的な問題は無い。

## 対応の記録（Claude Code 本体）

- **文書**: criteria.md §3.6.1 に「書き込みの失敗」（`OSError` は運用エラー。両 `main` で一括捕捉）と「部分的な出力を残さない書き方」の表を追加。§3.6.9 の記録の検査 5 に「JSON として読めない行は違反」を明記
- **実装**（Sonnet サブエージェントに 2 回委任）: (1) 両 `main` に `except OSError`、`write_jsonl`・`atomic_write_text` の一時ファイル方式、`annotate` の 2 ファイルの置き換えと後片付け、`read_log_rows` で読めない行を記録の違反に (2) 1 回目の報告で実装者が見つけた、`locate` 段 a の `tempfile.mkstemp` が後片付けの `try` の外にあった点を、規定（§3.6.4）に合わせて修正
- 修正後、Claude Code 本体が両 `--selftest` の終了コード 0 と、置き換え式の書き込み 4 か所を確認した。`mkstemp` 失敗の経路は `--selftest` で通らず、実行での確認はしていない（コードの読みでの確認のみ）

## 本単位の経過（codex-72〜75）

| 回 | 種別 | 高/中/低 | 内容 |
|---|---|---|---|
| 72 | A | 0/1/0 | `--log` の親ディレクトリ（＋付言: `--crops-dir` の親・`--out-dir`） |
| 73 | B | 0/0/0 | 解消（ゲート未実施） |
| 74 | **C** | 1/0/0 | 書き込み権限が無い既存ディレクトリでの書き込み全般が未処理の例外（同じ種類の指摘の 3 回目 → 行き詰まり検出でユーザーに判断を仰ぎ、案 1） |
| 75 | B | **0/0/0** | **収束** |
