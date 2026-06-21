# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-06-21 | 001,002 | A,A | 新規候補12件(P2) | IMP-001,002,003,004,006 | cycle_day1: 技術解説(Kubernetes)/公的文書(オンライン申請)。001 は f013「再スケジュール→組み直す」概念語毀損を round2 ロールバックで復旧(85.9→5.6)。002 は一発 accept(79.2→4.7)。taxonomy v1.1/playbook v1.1 昇格(taxonomist 承認): 正規化式 100*(1-exp(-raw/40)) 固定・change_rate 二軸化・scope:document 導入。IMP-005 は 3run ready で次回適用候補。 |
