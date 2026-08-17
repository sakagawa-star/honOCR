# feat-004: 句読点正規化の後処理と再判定

- **ステータス**: Open
- **種別**: feat（機能追加。再判定を伴うため「実験・検証の進め方」プロトコルを併用）
- **概要**: feat-003 の No-Go 対策。MinerU 出力の句読点スタイル揺れ（原本「，．」の約15%が「、。」に置換される）を正規化する後処理スクリプトを作成し、feat-003 と同一サンプル・同一基準で本文品質を再判定して Go/No-Go を決め直す
- **背景**: feat-003 の品質判定は数式 19/20・読み順 5/5 と良好だったが、本文が句読点置換の系統誤差により 7/10 で不合格となり No-Go だった。純粋な文字誤認識は10段落で1文字のみ（詳細は `../feat-003-mineru-trial/experiments/trial-quality/experiment_log.md`）
- **ドキュメント**: [requirements.md](requirements.md) / [design.md](design.md) / [experiments/renorm-quality/criteria.md](experiments/renorm-quality/criteria.md)
