# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-06-27 | 001,002 | A,A | P0/P1 6件を hits2runs へ昇格＋P2新規(A-8/I-3-4/格式結語/D-8候補等) | IMP-001,IMP-002,IMP-003,taxonomy v1.1(D-8採番) | cycle_day1(技術解説ゼロトラスト/公的文書コンビニ交付)。002は0.504でhold→fidelity pass+自然度A→override accept。IMP-002は2検出器が別式使用で決定的に再現。スコア正準式100*(1-exp(-raw/45))をSSOT固定。 |
