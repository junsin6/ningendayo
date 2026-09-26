# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-09-26 | 001,002 | A,A | 新候補6(A-8b無主語受動連鎖/K過剰敬語/I-3敬語変種 等)+IMP-001/002/004/005/006 を hits2昇格 | IMP-002, IMP-006, taxonomy v1.1(D-1勧誘型結び) | day1: 001技術解説記事(90.0→~0.5,99.4%) 002公的文書(45.5→~4.0,91.2%)。両 run fidelity=pass,rollback無,change_rate 30%内で通常accept。IMP-006(reviewerがdetector再走査不可)を両 reviewer が実証→検出経路をオーケストレーター層へ。IMP-002 正規化式 100×(1−e^(−raw/40)) を SSOT 固定(旧 run 001=90.0 と一致確認)。 |
