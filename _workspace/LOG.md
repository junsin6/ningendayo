# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-07-22 | 001,002 | A,A | 新IMP-007(cluster-anchor,P0)/IMP-008(modality順序尺度)/IMP-009(公的文書過推敲) + 候補I-6,B-4 | IMP-001,IMP-002,IMP-004+007 | cycle_day1(技術解説/公的文書)。001 は cluster-anchor 欠陥で grade C→2次推敲→A(97.5%)。002 は削除主導0.38 を override accept(A,95.95%)。taxonomy v1.1 昇格(正規化式確定・scope/occurrences・severity_breakdown)。 |
