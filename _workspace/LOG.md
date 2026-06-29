# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-06-29 | 001,002 | A,A | I-6候補ほか新規多数・modality順序尺度/IMP-005 が hits≥2 到達 | IMP-001,002,003,006 ＋ IMP-004部分 | day1 技術解説(RAG)/公的文書(図書館停止)。正規化式 `100×(1−exp(−per100/5))` K=5.0 確定(taxonomist 検算承認, taxonomy v1.1)、change_rate を semantic_change_rate と分離、検出器再実行を必須化。run001 は change_rate 34.6% を override accept、両 run fidelity=pass・自然度 A。 |
