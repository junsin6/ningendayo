# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-06-30 | 001,002 | A,A | 新規IMP-007,008+候補多数。IMP-001/004/005/006 を2run目で再現→ready昇格 | IMP-002,IMP-003 (taxonomy v1.0→v1.1) | day1: 技術解説(WebAssembly)/公的文書(図書館休館)。両 run fidelity=pass・自然度A・accept。IMP-002 を4agentが三者三様の式で再現(k=18/k=44.6/線形16.5-8-2)→SSOTに `100·(1−exp(−raw/44.6))` k=44.6固定で確定、score_before契約も明文化。taxonomist審査で v1.1 承認+候補欄2区画化。回帰: 過去4run の score 乖離(最大28pt)を確認、grade不変。 |
