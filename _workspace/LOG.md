# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-06-19 | 001,002 | A,A | 新規 IMP-007/008 ＋ 候補多数(A-6こととなる昇格等) | IMP-001,IMP-002,IMP-004 | day1(技術解説/公的文書)。001 は C→round2(A-10 patch)→A。両 run change_rate 30%超だが del 主導で override accept。taxonomy v1.1(正規化式K=8確定・scope追加・A-6拡張)。playbook v1.1(del/ins分離)。IMP-001/002/004 を2run再現で適用。 |
