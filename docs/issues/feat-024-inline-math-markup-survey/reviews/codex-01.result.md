# feat-024 Codex レビュー結果 01

| 項目 | 内容 |
|---|---|
| 日付 | 2026-09-06 |
| 対象ファイル | `docs/issues/feat-024-inline-math-markup-survey/requirements.md` / `design.md` / `experiments/inline-math-survey/criteria.md` |
| ストリーム名 | `rev-honocr-feat-024` |
| 依頼種別 | **A: 初回レビュー** |
| 直前に `/new` を送ったか | No（起動直後のため不要） |
| ゲート状態 | **未実施** |
| 指摘数 | **高 1 / 中 1 / 低 0** |
| 収束判定 | **未収束（次: 全件反映 → B）** |
| トークン実測 | 未取得（レート制限ダイアログにより rollout jsonl の特定を保留） |
| 備考 | 回答冒頭に `[AGENTS.md適用]` マーカーあり。所要 1分08秒。**回答後に codex がレート制限のモデル切替ダイアログを表示**（weekly limit 残 10% 未満） |

---

## 高

### 高-1: Q1・Q2 の合算可否が requirements.md と criteria.md で矛盾する

`requirements.md` は FR-006 で「3層の推定件数の合計を『影響範囲の推定値』として報告する」と
要求しているが、`criteria.md` §6.4 は「**Q1 と Q2 を合算しない**（測っている対象が異なるため）」と
明確に禁止している。`design.md` §9.2 は criteria 側に従っている。

**影響**: 最終報告の主要な結論が一意に決まらず、criteria lock の前提を壊す。

**修正案（codex）**: `requirements.md:222` を、Q1 は層G・層L の合計、Q2 は層C 単独として
別々に報告し両者を合算しない、と `criteria.md:132` と同一の文言へ修正する。

---

## 中

### 中-1: `estimate_rates.py` が保存済み標本と照合しない

推定スクリプトの入力が `sample_id`・`kind`・`judgment` だけで、保存済み `sample.tsv` との
照合を行う設計がない。判定 TSV に**標本ID の欠落・重複・標本外 ID・kind 不一致・
層に不正な判定**（例: 層G に J2）があっても、「130件全件を一度ずつ判定した」という
FR-005 / FR-006 の前提を機械的に保証できない。

**影響**: 誤った推定値を正常な結果として報告し得る。

**修正案（codex）**: `estimate_rates.py` に `--sample` を追加し、各 `sample_id` が保存済み標本に
ちょうど1回現れ、`kind` が一致し、層G・層L は `J0`/`J1`/`J9`、層C は `J0`/`J2`/`J9` のみで
あることを検証する。不一致時は終了コード 1 にする（`design.md:563`）。

---

## 低

なし。
