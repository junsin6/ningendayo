# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-07-06 | 001,002 | A,A | 新規2(IMP-007過剰敬語,IMP-008 agentless受動)+P2追補5 | IMP-002,003,004 (taxonomy v1.1) | day1: 技術解説(B-2/A-10/A-5)・公的お知らせ(A-8/I-3/敬語)。両 run fidelity=pass・等級A・ロールバックなし・change_rate 19.8/22.3%(30%内で override不要)。正規化式 100×(1−exp(−W/40)) を確定、span_type 追加、score_before 契約明文化。 |
