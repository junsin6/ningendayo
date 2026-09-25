# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-09-25 | 001,002 | A,A | 新規2(IMP-007,008)+候補6 | IMP-001,002,003 | day1(技術解説/公的文書)。001: change_rate44.4%だが表層置換主体で override accept、fidelity e004(可能→事実)局所ロールバック。002: accept、A-6検出漏れを micro-fix。taxonomy v1.1昇格(正規化式 100×raw/(raw+52) K=52・score契約・density union)。002の保存scoreは v1.1前clampのため 66.5(新式では56.1相当)だが等級Aは不変。 |
