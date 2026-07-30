# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-07-30 | 001,002 | A(override),A | 新候補 K/A-5b/A-8b＋fidelity #15/中間値warn 等 | IMP-001,IMP-002,IMP-003 (+taxonomy v1.1) | day1: 技術解説(001)・公的文書(002)。001 は fidelity 3件毀損(f011/12/13)→round2 ロールバック→再監査 pass、change_rate 0.404 削除主導で override accept。002 は fidelity pass・grade A。IMP-001(change_rate多軸化)/002(スコア正規化非飽和)/003(score_before契約)を適用。K=8 で raw107→85.9 に脱飽和を確認。 |
