# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-09-03 | 001,002 | A,A | IMP-007新規+候補多数, hits昇格(001/002/004/005/006, B-2辞書) | IMP-002,IMP-004,B-2辞書,taxonomy v1.1(A-8b昇格) | day1(技術解説/公的文書)。両 run fidelity=pass 過推敲0 で clean accept(override 不要, change_rate 0.24/0.246)。IMP-002 正規化式を実測 72.43/59.25 で検証(回帰なし)。A-8→A-8a/A-8b 分割。 |
