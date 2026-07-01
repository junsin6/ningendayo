# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-07-01 | 001,002 | A,A | 新規 IMP-007〜009＋新パターン候補7件 | IMP-001,IMP-002(v1.1) | day1(技術解説/公的文書)。002 は「システムが」主体注入で fidelity=fail→f009/f010 ロールバック→A。IMP-001(change_rate を net/weighted 分離・override 明文化)と IMP-002(score を非飽和指数式 v1.1・001 の score100.0 飽和を解消)を適用。IMP-004/005 も 2run 到達(未適用)。 |
