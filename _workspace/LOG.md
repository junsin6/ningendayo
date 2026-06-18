# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-06-18 | 001,002 | A,A | IMP-007新規(公的文書ジャンル床)＋v1.2候補4＋P2追補多数 | IMP-002,004,005(taxonomy v1.1) | day1(技術解説/公的文書)。両 run とも fidelity 毀損1件をrollback round2で復旧(001:核心→欠かせない要素/でしょう＋文体崩れ修正、002:効率的の概念欠落復元)。001は change_rate超のみ残→IMP-001 override accept。IMP-002正規化式・IMP-004 scope・IMP-005 secondary_categories を SSOTに適用しtaxonomist審査でv1.1承認(例71.5→72.0訂正)。回帰: detected_count==len 全run成立。 |
