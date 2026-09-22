# 日次ログ

| date | runs | grades | new IMP | applied | note |
|---|---|---|---|---|---|
| 2026-06-12 | 001,002 | A,A | 18件起票(P0×3,P1×3,P2多数) | — | パイプライン end-to-end 初完走。change_rate 指標欠陥(IMP-001)・正規化欠陥(IMP-002)を実証。A は f019 ロールバック→再推敲で復旧。 |
| 2026-09-22 | 001,002 | A,A | 新候補8+追補多数 | IMP-002,IMP-004,IMP-006 | day-1(技術解説/公的文書)。IMP-002 の実害（検出器2機が別式でスコア比較不能: min(100,raw) vs 100raw/(raw+30)）を観測し正規化式を SSOT 確定。IMP-004 scope 追加, IMP-006 検出器再走査をオーケストレーター責務化。taxonomy v1.1 昇格(taxonomist審査)。run001 は f033 因果毀損を rollback→round2 で復旧。IMP-001/002/004/006 が 2run 再現で ready→(002/004/006)done。 |
