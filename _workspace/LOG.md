# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-09-15 | 001,002 | A,A | 新規12件(P1隣接1,P2新規11)+候補5件 | IMP-002(done,taxonomy v1.1), fidelity#14(done), IMP-001(部分done) | cycle_day1: 技術解説/公的文書。001 は fidelity fail(f024不可欠性↓・f030受益valence)→rollback_and_rewrite→accept。002 は fidelity pass→accept。改善率 90.3%/91.1%。正規化式 k=45 を SSOT 明記(旧raw106は式上90.5で2ptズレ要観察)。 |
