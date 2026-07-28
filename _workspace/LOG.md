# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-07-28 | 001,002 | A(R2),A | IMP-007/008 起票, 新パターン A-14/A-15/二重敬語 候補追加 | IMP-002,004,005 (taxonomy v1.1) | cycle_day1（技術解説・公的文書）。001 は多出現単一アンカーバグ(IMP-007)で grade C→round2 で A。002 は 1 発 A。スキーマ確定: 正規化式(非飽和)・scope/occurrences・merged_categories。taxonomist が K=40 検算し承認。両 run とも change_rate<30% で override 不要、fidelity 全 pass。 |
