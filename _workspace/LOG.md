# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-07-20 | 001,002 | A,A | IMP-007,008 新規+候補K(4agent)+P2多数。IMP-001/002/003/004/005/006 が2run再現 | IMP-002,004,005 → taxonomy v1.1 | day1（技術解説/K8s, 公的文書/図書館休館）。001 は naturalness 再スキャン(IMP-006)が検出漏れの A-1 S1 を捕捉→grade C→round2→A で復旧。002 は1発 A。score正規化式を 100·raw/(raw+28.5) に固定、span_type/occurrences/secondary_category 追加、density union 化。候補 K「過剰敬語」登録(昇格は次の公的文書 run 待ち)。 |
