# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-08-06 | 001,002 | A,A | IMP-007新規(offset)+K候補昇格+P2多数, IMP-001..006 を2runへ | IMP-002,003,004,005,007 + K(v1.1) | day1: 技術解説(001)/公的文書(002)。両 run accept(002 は change_rate 0.37 override)。fidelity 両 pass。検出器 offset ズレ(input_length 906 vs 実871)を3agent一致で発見→text_span正アンカー化+自己検証ゲート適用。過剰敬語カテゴリ K を v1.1 昇格。回帰チェック pass。 |
