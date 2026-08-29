# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-08-29 | 001,002 | A,A(002は round2 で C→A) | 新パターン候補5・fidelity #7a/#7b/#5b・playbook 公文書レシピ・レジスター軸 等 | IMP-001,IMP-002,IMP-003,IMP-006 | day-1（技術解説/公的文書）。002 は f011 義務標識脱落で fidelity rollback＋過推敲2件→round2 外科修復で accept。全 P0 が hits≥2 到達し実適用: 変更率二層化＋override accept、飽和スコア式 100×(1−exp(−raw_density/8))、score_before 契約明文化、detector 再走査経路正規化(05_rescan.json+rescan_method 必須)。taxonomy v1.0→v1.1。回帰なし(旧 run スコア非飽和)。 |
