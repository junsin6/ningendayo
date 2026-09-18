# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-09-18 | 001,002 | A,A | 新候補7(D-8/A-8b/A-10拡張/I-6 等)+精緻化多数 | IMP-001,002,003,006 done / IMP-004 部分 | day1(技術解説・公的文書)。P0/P1 が別 run で再現し昇格→適用。taxonomy v1.1(正規化式 K=40 確定・raw併記・scope追加)。change_rate を3指標分離。naturalness の検出器再実行 in_process fallback 規定。run002 は f023(迅速≠的確)を fidelity ロールバック→再pass。両 run 改善率90.1%/96.7%。 |
