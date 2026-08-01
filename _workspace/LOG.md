# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-08-01 | 001,002 | A,B | 新候補多数(D-7公文依頼公式/A-8受動拡張/severityジャンル依存/#11b主張すり替え/fix-induced regression/accept_with_micro_fix) | IMP-001,002,005,006 | day1(技術解説,公的文書)。IMP-002再現(raw120→100飽和)を両detector実証→飽和正規化100*(1-exp(-raw/60))適用でraw120→86.5に解消。IMP-001二軸化・IMP-005 density union・IMP-006 orchestrator再検出経路を適用。001は e002命題すり替え(fidelity rollback)+A-5残存S1をround2局所修正で A 復旧。002は依頼公式除去の副作用でE-2再発(ください8連発)もB/accept。taxonomist審査済(v1.0据置)。 |
