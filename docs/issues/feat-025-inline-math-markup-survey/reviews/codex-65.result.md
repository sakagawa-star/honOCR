# codex-65: M3 閾値実験 criteria（§3.6 追加版）の初回レビュー（A）

- **日付**: 2026-10-06
- **対象ファイル**: `docs/issues/feat-025-inline-math-markup-survey/m3-pilot-measure/experiments/thresholds/criteria.md`（関連: `../../design.md` ADR-22・§1.4.4、`../../requirements.md` C-309、`../../../m2-1-locate-smoke/design.md` §1.4.1・§1.4.3、`scripts/crop_blocks.py`）
- **ストリーム名**: `rev-honocr-feat-025`
- **依頼種別**: **A**（初回レビュー。criteria lock の人レビュー通過後に §3.6 を追加して §6 を書き直した改版のため、**新しいレビュー単位**）
- **直前に `/new` を送ったか**: **Yes**（**遷移表からの逸脱**。遷移表の「（開始時）→ A」に `/new` は含まれないが、Claude Code 本体が A の前に送った。会話を空にしただけでレビューの内容には影響しない。記録として残す）
- **ゲート状態**: **未実施**
- **指摘数**: 高 **2** / 中 **1** / 低 **0**
- **収束判定**: **未収束（次: 全件反映 → B）**
- **トークン実測**: `total_tokens` = 338,540（input 333,036 / cached_input 265,472 / output 5,504 / reasoning 3,701）
- **rollout jsonl**: `/home/sakagawa/.codex/sessions/2026/10/06/rollout-2026-10-06T15-33-52-01a10feb-28e5-7d80-9d5e-460b8b91f56f.jsonl`

## レビュー結果（要旨）

**高**
1. `summary.json` の `ranges` は全値を `float` とする一方、`ok` が 0 件の群・Q2 の値が未定義で、スキーマに `null` を置けない。`ranges` を `float | null`、`ok` = 0 なら全 `null`、測定不足時の `thresholds`・`conditions` も `null` と固定し、`ok` = 0 の群の `--selftest` ケースを追加せよ
2. `summarize` の記録の検査が、`measurements.jsonl` の行と `located.jsonl` の標本の対応を検査していない（`group`・`png`・`status`・成分・計算値の改変や取り違えを検出できない）。`fail` も `locate_status` = `ok` に `特定不能` を記録することを禁止していない。キー・型・許容値・null の可否、Q1 の `sample_id → group/png` の一致、Q2 の初出 Q1 `sample_id → png` の一致、`ok` 行の再計算一致、失敗行の測定値・成分が `null`、`locate_status` = `ok` での `特定不能` の禁止を加え、不正なら終了コード 1 とせよ

**中**
1. `locate` の途中失敗時に、先に作られた `crops/` と PNG の扱いが未定義で、`crops-dir` が存在すると次回の実行を拒否するため、再実行できない。一時ディレクトリに出して全成功後に原子的に移動するか、失敗時に作ったものだけを削除する手順を明記せよ

## 対応（Claude Code 本体）

- **高 1**: `ranges` の各値を `f|null` とし、`ok` = 0 件の群はすべて `null`、`測定不足` のときは `thresholds`・`conditions` をすべて `null`、`合格`・`不合格` のときは `null` を置かないと固定した。`--selftest` に **M5**（G3 の 2 標本がいずれも `特定不能` で `ok` = 0 → `ranges.G3` が `null`・`測定不足`）を追加した
- **高 2**: `summarize` の記録の検査に 5〜10 を追加した（5 形式／6 Q1 の `located.jsonl` との対応と `特定不能` の整合／7 Q2 の対象画像との対応／8 `ok` の行を `components.json` から**再計算して一致**〔`r`・`d` は 1e-9 以下〕／9 失敗の行の測定値・成分がすべて `null`／10 `italic` の型）。再計算のため `summarize` に `--annot-dir` を追加した。`fail` で `locate_status` = `ok` の標本に `--reason 特定不能` を与えることを引数の誤りにした。M2 の固定ケースに、再計算と一致する `components.json` の作り方（3 成分の座標）を明記し、**M6**（`r` だけを書き換えた行 → 検査 8 違反で終了コード 1）を追加した。M4 は、成分から整数の座標で作れるよう `d` を 0.05 に改めた（`T_raise` = `T_bl` = 0.05 で条件が `false`）
- **中 1**: `locate` は実行前に `-o` と `--crops-dir` の両方が存在しないことを確認し、切り出しを `tempfile.mkdtemp` の一時ディレクトリに対して行う。途中で失敗したら一時ディレクトリを削除して終了コード 1（何も残さないので同じコマンドで再実行できる）、すべて成功したら `os.rename` で `--crops-dir` に改名し、そのあと `located.jsonl` を原子的に書く、と定めた
