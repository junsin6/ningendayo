# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-08-30 | 001,002 | A,A | 既出5件 hits+1(IMP-001/002/004/005/006)・新候補15件(新分類K/A-14 等) | IMP-001,IMP-002(taxonomy v1.1),IMP-006 | day1 技術解説/公的文書。002 は f009 modality escalation(見込み→断定)で rollback→pass。検出器2機が別正規化式を採用し IMP-002 を決定的に実証→v1.1 で K=20 式に統一。change_rate swap/trim 分離を playbook/rewriter/SKILL に適用。naturalness の detector_rerun 契約を明文化。 |
