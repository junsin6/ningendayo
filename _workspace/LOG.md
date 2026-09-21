# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-09-21 | 001,002 | A,A | 新パターン候補5+fidelity/playbook/naturalness 多数 | IMP-001, IMP-002, IMP-006 (＋taxonomy v1.1) | day-1(技術記事/公的文書)。両 run とも fidelity 1件ロールバック(001 枠づけ名詞「アプローチ」欠落 / 002 modality 必須→依頼降格)→修正→accept。change_rate 0.46/0.35 は override accept(IMP-001)。IMP-006 は「reviewer は検出器を spawn 不能」が両 run で判明し設計反転(オーケストレーター事前再検出)で適用。taxonomy v1.1(スコアスキーマ確定・新パターンは再現待ち据え置き)。 |
