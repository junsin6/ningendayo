# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-06-26 | 001,002 | A,A | IMP-007新規＋候補5件、6項を hits 2runs へ昇格 | IMP-002,IMP-004,fidelity#14 (taxonomy v1.1) | day1（技術解説/公的文書）。両 run change_rate 超過だが圧縮/削除主導につき override accept(IMP-001)。IMP-002 正規化式を 100·(1−exp(−raw/45)) で固定、IMP-004 span_type 追加、fidelity を14項化(f019対策)。taxonomist 審査で v1.1 昇格。 |
