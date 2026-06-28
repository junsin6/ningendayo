# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-06-28 | 001,002 | A,A | IMP-007/008 新規, 候補6件(A-14等) | IMP-002,IMP-003,#14 (taxonomy v1.1) | day1(技術解説/公的文書)。両 run fidelity pass・accept。IMP-002 で検出器間スコアブレを実証→飽和正規化式 100×(1−exp(−raw/41)) 確定(参照run 92.5 再現で回帰なし)。IMP-003 score_before 契約・fidelity #14 を適用。IMP-007: 推敲が A-6→D-2 へクセ転位(新規混入)を観測しA等級に新規混入0件ガード追加。 |
