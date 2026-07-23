# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-07-23 | 001,002 | A,A | 新3件(IMP-007/008/009)+候補4件, hits更新6件 | IMP-002,IMP-001,fidelity#14 | cycle_day1(技術解説/公的文書)。001 は f013(重要→不可欠)・f020(進化→普及)を fidelity 検出→round2 ロールバックで pass 復旧。002 は初回 pass。taxonomy v1.1(正規化式固定)。両 run change_rate<30% で override 不要。 |
