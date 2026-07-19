# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-07-19 | 001,002 | A,A | 新候補: K過剰敬語, A-8手段by分割(昇格), A-14, genre-modifier ほか | IMP-002,003,004,006（taxonomy v1.1） | day1(技術解説/公的文書)。両 run fidelity=pass・自然度A/accept。IMP-006 を naturalness で実証(検出器再実行成功)。IMP-002正規化式(100*(1-exp(-kW/L)),k=23)＋IMP-004 scopeフィールドを taxonomist 審査で v1.1 昇格。回帰なし(等級A維持)。IMP-001は次サイクルへ保留。 |
