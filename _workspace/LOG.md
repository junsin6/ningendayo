# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-07-31 | 001,002 | A,A | new IMP-007,008 +P2多数 | IMP-001,002,003,004 (taxonomy→v1.2) | day1(技術解説/公的文書)。両run fidelity=pass・自然度A。002は change_rate 0.317 だが del主導で override accept(IMP-001)。正規化を対数圧縮K=60へ(飽和解消: raw87→旧100→新76.5)、scope/occurrences導入、del/ins分離。taxonomist が mixed文体を type A/B に定義しv1.2へ。 |
