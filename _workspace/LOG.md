# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-07-18 | 001,002 | A,A | 新候補: K メタ言及・K 過剰冗長敬語・A-8b 行為者省略受動＋fidelity #15/#17 等 | IMP-001,002,003,004 | cycle_day1（技術解説記事/公的文書）。両 run fidelity=pass・grade A。001 は change_rate 30.5% 削除主導で override accept。P0 4件を適用（score 正規化 exp・span_type・change_rate insertion_ratio・score_before 契約）。taxonomist v1.1 審査で適用スキーマのバグ4件（例値82.9・improvement_rate を raw 定義・density 和集合）を検出し即修正。IMP-005/006 が hits=2 到達＝次回適用候補。 |
