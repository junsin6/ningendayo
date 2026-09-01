# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-09-01 | 001,002 | A,A | 再現+新候補多数(K過剰敬語/A-8b/A-14/F-1漸増) | IMP-001,IMP-002,B-2免責(v1.1) | day1(技術解説/公的文書)。001は f020(可能→断定過変換)ロールバック→override accept(変更率44.6%だがfidelity=pass/自然度A)。002は素直にA。taxonomy v1.1昇格(正規化式 score=100×(1−exp(−(raw/L)/0.05)) 確定・density union・B-2 allowlist)。IMP-006昇格(サブエージェント実行不可、要オーケストレーター層移管)。 |
