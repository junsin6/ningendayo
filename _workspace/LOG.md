# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-06-25 | 001,002 | A,A | 新候補11(C-001〜003+fidelity#15-18+playbook4+自然度profile) | IMP-001,002,003 適用＋taxonomy v1.1＋IMP-006/自然度精緻化3 | day1（技術解説・公的文書）。両 run とも round2 rollback で fidelity 復旧（001 f035b 伝聞マーカー復元・002 f009「等」復元）→A/accept。P0 三大欠陥(変更率指標・正規化式・score_before契約)を別 run 再現で昇格・適用。taxonomist が v1.1 を承認。 |
