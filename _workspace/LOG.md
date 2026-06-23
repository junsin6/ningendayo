# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-06-23 | 001,002 | A,A | 新規P2多数+候補4(D-7過剰敬語/A〜していく/B-2カタカナ動詞/I-6こととなる) | IMP-001,002,003,006 | day1(技術解説,公的文書)。run001 fidelity 毀損(f016 帰結捏造)→round2 ロールバックで pass。run002 change_rate 48.8% override accept。IMP-002 で taxonomy v1.1(canonical 正規化式 100*raw/(raw+22))。canonical 再計算 run001≈74.4/run002≈63.9 で検出器間一致を確認(回帰なし)。 |
