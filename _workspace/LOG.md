# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-09-12 | 001,002 | A,A | IMP-007/008/002b 起票＋新パターン候補4件(K/メタ橋渡し/過剰確信/単なる〜ではなく) | IMP-004,005,008,007(A-8)＋IMP-002(式のみ) | day1(技術解説/公的文書)。両 run fidelity=fail→round2 ロールバックで復旧(001 能力欠落, 002 証拠性毀損)。taxonomy→**v1.2**: scope/occurrences・merged_findings・style連動fix を確定、A-8 に証拠性ヘッジ保護を追加。playbook I-5 に定義文核名詞の例外。IMP-002 は式の形のみ採用、係数校正は IMP-002b(OPEN)＝taxonomist が例71.5→30.2 の到達不能を指摘し次版送り。 |
