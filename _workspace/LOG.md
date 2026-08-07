# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-08-07 | 001,002 | A,A | 新規 IMP-007,008,009,010＋候補4件 | IMP-001,002,003,004 | day1（技術解説/公的文書）。両 run とも fidelity=pass・自然度A、change_rate 超過は delete_dominant で override accept（IMP-001 適用後の正規経路）。IMP-001 を playbook/SKILL/rewriter に、IMP-002/003/004 を taxonomy v1.1 に適用。f019 型序列改変は再発せず。 |
