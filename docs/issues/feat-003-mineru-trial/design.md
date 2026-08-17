# feat-003 機能設計書: MinerU 試行（章単位PDFの品質確認）

## 1. 対応要求マッピング

対象: `docs/issues/feat-003-mineru-trial/requirements.md`

| 要求ID | 設計セクション |
|---|---|
| FR-001 | §4.1 |
| FR-002 | §4.2 |
| FR-003 | §4.3 |

## 2. システム構成

本案件で新規コードは書かない（既存の `scripts/make_ocr_pdf.py` と `mineru` CLI を使う）。成果物はデータとドキュメント。

| 成果物 | 場所 | 担当内容 |
|---|---|---|
| `chap-00_gray300.pdf` / `chap-01_gray300.pdf` | `/home/sakagawa/work/Pattern_Recognition_and_Machine_Learning/chap01/out/ocr/` | 章単位PDF（FR-001） |
| MinerU 出力一式 | 同ディレクトリの `mineru-trial/run-NN/` 配下（実行ごとに新規ディレクトリ） | Markdown・JSON・切り出し画像（FR-002） |
| `experiment_log.md` | `docs/issues/feat-003-mineru-trial/experiments/trial-quality/` | 予測・実測・照合・判定表・Go/No-Go の記録（FR-003） |
| モデルファイル | `~/.cache/`（MinerU の既定位置） | 初回実行時に自動ダウンロードされる |

## 3. 技術スタック

- 追加ライブラリ: なし。`mineru==3.4.4`（hybrid-engine 既定設定）、`scripts/make_ocr_pdf.py`（feat-002）をそのまま使う
- 実験ログは Markdown 手書き（ツール不使用）

## 4. 各機能の詳細設計

### 4.1 章単位PDF の生成（FR-001）

案件 README.md の確定対応に従い、以下の2コマンドを実行する（`{OUT}` = `/home/sakagawa/work/Pattern_Recognition_and_Machine_Learning/chap01/out`）:

1. chap-00（17ファイル = 辞書順の位置2〜18）:
   `uv run python scripts/make_ocr_pdf.py` に位置2〜18 の TIF をフルパスで列挙し `-o {OUT}/ocr/chap-00_gray300.pdf`
2. chap-01（64ファイル = 辞書順の位置20〜83）:
   同様に位置20〜83 を列挙し `-o {OUT}/ocr/chap-01_gray300.pdf`

ファイル列挙は `ls {OUT}/page-*.tif | sed -n '2,18p'` / `sed -n '20,83p'` の結果を使う（辞書順が保証される。除外3件: 位置1・19・84）。

確認: `pdfinfo` でページ数 17 / 64 を確認する。

**実験プロトコル**: 実行直前に予測（各PDFのページ数・ファイルサイズ）を experiment_log.md に記録し、実行後に実測と照合する。

エラー時: `make_ocr_pdf.py` が非0終了したら中断して報告する（feat-002 で検証済みのため想定外事象として扱う）。

### 4.2 MinerU による変換の実行（FR-002）

1. 実行前確認: `df -h /` で空き容量 30GB 以上を確認する（不足時は中断して報告）
2. 実行ディレクトリの確保: 今回の実行番号 NN（01 から。再実行のたびに +1）を決め、`{OUT}/ocr/mineru-trial/run-NN/` を新規作成する。**既に存在する場合は次の番号に進む**（過去の実行の生成物と混ざらないよう、実行ごとに空の新規ディレクトリを使う。完了確認・品質判定は今回の run-NN 配下のみを対象にする）
3. **実験プロトコル**: 実行直前に予測（モデルダウンロード容量・変換所要時間・独立数式件数）を experiment_log.md に記録する
4. 実行（**バックグラウンドで行う**。初回はモデルダウンロードを含み長時間になるため）:
   `env no_proxy="localhost,127.0.0.1,$no_proxy" NO_PROXY="localhost,127.0.0.1,$NO_PROXY" uv run mineru -p {OUT}/ocr/chap-01_gray300.pdf -o {OUT}/ocr/mineru-trial/run-NN` の標準出力・標準エラーを `{OUT}/ocr/mineru-trial/run-NN.log` に保存する（ログの連番はディレクトリと揃える）
   - **`no_proxy` / `NO_PROXY` への `localhost,127.0.0.1` 追加は必須**。本環境はプロキシ必須（`/etc/environment` の `http_proxy` 指定）だが既定の `no_proxy=.u-fukui.ac.jp` に localhost が含まれず、MinerU CLI が起動するローカル API（`http://127.0.0.1:<port>`）へのヘルスチェックがプロキシへ転送されて 502 で失敗する（run-01 で実測）。モデルダウンロード（外部 HTTPS）は引き続きプロキシ経由で行われる
   - バックエンド・オプションは指定しない（既定 = hybrid-engine / effort medium。criteria の判定対象は既定設定の品質）
5. 完了確認（対象は `run-NN/` 配下のみ）: 終了コード 0、(1) Markdown（`*.md`）が1個以上あり `grep -o '\$\$' <md> | wc -l` が **2以上かつ偶数**（独立数式1個以上。`-c` は行数カウントのため使わない）、(2) 各ブロックのページ番号情報（page_idx 相当）を含む JSON（content list）が1個以上ある（FR-003 のページ対応付けに必須）
6. 実測記録: モデルダウンロード容量（実行前後の `~/.cache` サイズ差）、所要時間、出力ディレクトリ構成（MinerU 3.4.4 の実際のレイアウトをここで確定し experiment_log.md に記録する）、Markdown の独立数式件数
7. 照合: 手順3の予測と手順6の実測を照合し、乖離があれば原因を記録してから §4.3 に進む

エラー時の対応:

| エラー | 検出方法 | 処理 |
|---|---|---|
| モデルダウンロード失敗（ネットワーク） | run-NN.log のエラー・非0終了 | 1回だけ再実行する（ログは連番を進める）。再失敗で中断・報告 |
| ローカル API のヘルスチェック失敗（プロキシ転送による 502） | run-NN.log の `Timed out waiting for local mineru-api` とプロキシの HTML 応答 | 手順4の `no_proxy` 追加が漏れていないか確認して再実行する。追加済みでも失敗する場合は中断・報告 |
| GPU メモリ不足（OOM） | run-NN.log の CUDA OOM メッセージ | 中断して報告する（バックエンド変更・パラメータ変更は行わない。対策は要ドキュメント改訂） |
| 変換が2時間を超えて未完了 | バックグラウンドタスクの経過時間 | 中断（プロセス停止）して報告する |

### 4.3 品質判定（FR-003）

criteria 文書（`experiments/trial-quality/criteria.md`。**criteria lock 済みの版**）に従って判定する。手順:

1. **実験プロトコル**: 判定作業前に項目A/B/Cの実測値の予測を experiment_log.md に記録する
2. 項目A（独立数式）: criteria の規則に従い**原本側**から母集団（番号付き独立数式の先頭20件）を確定する。原本ページの TIF を Read ツールで表示して数式番号を走査し、content list の page_idx で Markdown 側の対応数式を特定して目視比較する。判定表（サンプルID・原本ページ・数式番号・判定・不一致内容）を experiment_log.md に記録する
3. 項目B（本文10段落）・項目C（読み順5ページ）: 同様に criteria の規則（母集団の確定方法・対応付け・誤りカウント規則を含む）で判定し、判定表を記録する
4. 合否集計と Go/No-Go を criteria の合格ラインどおりに決定し記録する（**事後解釈をしない**。合格ラインの変更・条件追加は禁止）
5. ユーザーの二次確認を受ける（手動テストステップを兼ねる）。一次判定の誤りが指摘された場合は該当サンプルを再判定し、履歴を experiment_log.md に残す

## 5. 状態遷移

該当なし。

## 6. ファイル・ディレクトリ設計

- 実験ログ: `docs/issues/feat-003-mineru-trial/experiments/trial-quality/experiment_log.md`（git 管理。フェーズごとに「予測 → 実行 → 実測 → 照合」の見出しで追記し、上書きしない）
- データ出力（git 管理外）: §2 の表のとおり
- 命名: 章単位PDF は `chap-{NN}_gray300.pdf`（フェーズ4でも同じ規則を使う想定）

## 7. インターフェース定義

新規関数・クラスなし（既存 CLI の呼び出しのみ）。

## 8. ログ・デバッグ設計

- MinerU 実行ログ: `{OUT}/ocr/mineru-trial/run-NN.log`（標準出力・標準エラーをそのまま保存。実行ごとに連番）
- 実験の記録: experiment_log.md（§6）

## 9. 設計判断の記録（ADR）

| # | 採用 | 却下と理由 |
|---|---|---|
| 1 | 試行対象は chap-01 のみ（chap-00 は生成のみ） | 両章の変換 — chap-00 は前付け中心で数式が少なく、品質判定の情報量が増えない。モデルダウンロード後なら chap-00 の変換はフェーズ4で低コストに実施できる |
| 2 | バックエンドは既定の hybrid-engine 固定 | バックエンド比較 — まず既定設定で Go/No-Go を判定する。比較・チューニングは No-Go だった場合に別案件で行う（一度に変数を増やさない） |
| 3 | 品質判定は原本との目視比較による二値判定（criteria で判定規則を固定） | 文字列類似度による自動判定 — 原本の正解テキスト（ground truth）が存在せず、自動化にはまず正解データ作成が必要。サンプル数を絞った目視のほうが実験目的（Go/No-Go）に対して低コストで十分 |
| 4 | 独立数式のみ判定（行内数式は除外） | 全数式 — 行内数式は短く判定の客観性が低い。独立数式が合格水準なら行内も同水準と推定できる（この推定の妥当性はフェーズ4の計画時に必要なら再検証） |
| 5 | 実装ステップも Claude Code 本体が実行（Sonnet 委任しない） | Sonnet サブエージェント委任 — 本案件の「実装」はコマンド実行と目視判定が主体で、新規コードがない。判定（§4.3）は原本画像の読解が必要で、委任すると判定根拠の記録・二次確認への応答が分断される。CLAUDE.md の委任ルールは「コードを書く実装」を対象としており、本案件は該当しない |

## 10. 実装・検証の実施方法

- 手順: criteria lock（Codex レビュー収束）→ 人レビュー承認 → §4.1 → §4.2 → §4.3 の順に実行する。各フェーズで実験プロトコル（直前予測 → 実行 → 照合）を厳守する
- **承認ゲート**: §4.2 のモデルダウンロードと長時間ジョブは、人レビュー承認（実装開始指示）をもって承認とみなす
- 本案件は新規コードがないため pytest の追加はない。回帰確認として完了前に `uv run pytest -v` を実行し、既存16件が PASS のままであることを確認して `tests/results/feat-003_test_result.txt` に保存する
- 手動テスト（ステップ7）は §4.3 手順5 のユーザー二次確認を充てる

## 11. 完了処理でのドキュメント更新

- `docs/TECH_STACK.md`: 変更なし（ライブラリの追加がない）
- `CLAUDE.md`: ディレクトリ構成の変更なし（リポジトリ内の新規ファイルは案件フォルダ配下のみ）。「ドメイン知識」に確定した章対応（README.md の要約1行）を追記する
- `docs/BACKLOG.md` / `docs/CHANGELOG.md`: 完了時に更新（Go/No-Go の結果と主要実測値を CHANGELOG に記録する）
