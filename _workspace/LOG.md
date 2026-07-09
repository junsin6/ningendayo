# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-07-09 | 001,002 | A,A | IMP-007/008 起票, 候補4件(A-5b/A-6b/〜ていく/I-3a-b), hits+1: IMP-001/004/005 | IMP-002,003,006 (taxonomy v1.1) | day1: 001 技術解説(オブザーバビリティ)/002 公的文書(お知らせ)。001 は f019 で #5/#6/#14 毀損→rollback_and_rewrite で pass(「大きく寄与」復元)、f004 は強調鉤括弧と裁定し override accept。002 は縮約主導で fidelity pass。両 A/accept。スコア正規化を k=45 exp 式に確定(検出器4体の逆算不整合を解消)、naturalness に検出器実再走査を必須化。 |
