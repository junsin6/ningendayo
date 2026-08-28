# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-08-28（run 2026-08-28-001 技術記事, -002 公的文書）。適用: IMP-001 / IMP-002(v1.1) / fidelity #14。

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done` `hits: 2run` 適用: 2026-08-28-001,002
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。Sample A も 47.6% と高止まり。
- 再現 2026-08-28: 002 で総 change_rate 30.3% が 30% 警告を誤発火（語句改変率は 17.1%）。001 も総 26.9%（語句改変率≈6%、純削除主導）。rewriter-A/B が独立に goku_kaihen_rate を分離実装。
- 出所: rewriter-A, rewriter-B, naturalness-B（run1）／ rewriter-A, rewriter-B（run2）
- 提案: (a) 「語句改変率(replace)」と「構造/削除率(insert+delete)」を分離計上。(b) 中断・警告判定は語句改変率で。(c) 純削除主導の総変更率超過は override accept。
- **適用済み**: `rewriting-playbook.md §変更率の数え方` に 3 指標分離＋判定閾値を明記、`japanese-style-rewriter.md §推敲手順5`・出力 meta を更新、`SKILL.md §3/§総合判定` に override accept 条項を追加。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2run` 適用: 2026-08-28-001,002 (taxonomy v1.1)
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える（Sample A raw106→92.5、taxonomy 例は raw56→71.5 と不整合）。
- 再現 2026-08-28: detector-A が `100*(1-exp(-raw/60))`、detector-B が `raw/input_length×1000` と**別々の式を発明**し run 間比較不能を実証。
- 出所: detector-A, detector-B（両 run）
- **適用済み（taxonomist 審査 → v1.1）**: `score = 100·(1−exp(−d/6.0))`, `d = 100·W/input_length` に確定。密度基底で長さ飽和を回避、exp 平滑で高密度短文の 100 張り付きを回避。JSON 例の 71.5→40.1 に是正、density の union 規約（IMP-005 整合）も明記。`ai-tell-taxonomy.md §検出出力スキーマ／バージョン管理`。
- 残: `input_length` の数え方（コードポイント等）が未定義（次版候補）。2026-06-12 run は L 未記録で遡及再計算不能。

### IMP-003 score_before のフィールド契約が曖昧 `status: ready` `hits: 2run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score 92.5）。レビュアーごとに数値がぶれる。
- 再現 2026-08-28: 明示指示で両レビュアーが meta.severity_weighted_score を採用し安定（73.2 / 66.5）。提案が有効と検証されたが .md 未反映。
- 出所: naturalness-A（run1）／ naturalness-A, naturalness-B（run2 で提案どおり運用）
- 提案: 「score_before = 02_detection.json の meta.severity_weighted_score」を `naturalness-reviewer.md` に明文化。**次回適用候補（低リスク・1行）**。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run`
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
- 再現 2026-08-28: E-2 文末単調が両 run で文書レベル。detector-A は `text_span="", start=end=0` のマーカーで密度除外、detector-B は union で回避。単一 start/end 前提の構造欠陥が継続。
- 出所: detector-B, detector-A（両 run）
- 提案: `span_type: "contiguous"|"scattered"|"document"` と scattered 用 `occurrences: [[s,e],...]` を追加。density は重複・locator を除いた実 AI クセ文字数ベースと定義。**次回適用候補**（v1.1 の density union 規約で密度過大は緩和済みだが、スキーマ拡張は未了）。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run` 一部適用(density union)
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。
- 再現 2026-08-28: 「ソリューションとなっている」= A-6+A-10+B-2、「必要がございます」= I-3+E-2 等の重畳を両 run 検出器・監査が報告。density の二重計上も両検出器が union で回避。統合 edit（複数 finding_id）を rewriter が要望。
- 出所: 両 run の detector-A/B, rewriter-A/B, fidelity-A/B（横断的に最多）
- **一部適用（v1.1）**: density は union 計上と taxonomy に明記済み。**未了**: `secondary_categories` / `merged_findings` / 統合 edit の `finding_ids` 配列（次回適用候補）。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 2run` ★remedy 要修正
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。
- 再現 2026-08-28: **両レビュアーが「サブエージェント文脈では Agent/Task 起動ツールが無く ai-tell-detector を新規スポーン不可」と明確に報告**。つまり現行 remedy（レビュアーが検出器を再呼び出し）は**実行不能**。両者は taxonomy 基準の機械的フルスキャンで代替した。
- 出所: naturalness-A（run1）／ naturalness-A, naturalness-B（run2、実行不能を実証）
- **修正 remedy**: レビュアーに detector 起動権限を与えるのではなく、**オーケストレーター（main）が検出器を再走査し、その再計測 JSON を `05_*` の入力としてレビュアーへ渡す**設計に変更（責務分離）。または naturalness-reviewer.md の「検出器を再実行」を「検出器基準（ai-tell-detector.md 手順＋taxonomy）を同一適用した機械的再スキャン」に緩和明記。**次回適用候補**。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md §4`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 001（2026-06-12）。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B
- **（v1.1 候補欄に記載済み・再現 2run 未満で未昇格）** 2026-08-28 追加:
  - **A-8' 方向助詞「へと」＋受動** 「高次元のベクトル**へと**変換される」「近い位置に配置される」＝英語 `transformed into` 直訳。技術記事で2例。 `hits: 1` 出所 detector-A（run 001）
  - **I-3' 「〜必要がございます」** I-3 の敬体変種。任意依頼の義務化定型。公的文書で3例。 `hits: 1` 出所 detector-B（run 002）
  - **A-6' 「〜されることとなっております」** 受動＋形式名詞＋状態化＋謙譲の複合（S1 候補）。 `hits: 1` 出所 detector-B（run 002）
  - **D-6' 過剰謙譲定型「賜りますよう/お願い申し上げます」反復** 人間使用率が高いため昇格時は反復密度（一文書3回以上）を必須条件に。 `hits: 1` 出所 detector-B（run 002）
  - **D-6'' 「〜のである」＋擬人化の常体結び** 「役割を担っているのである」。常体 AI 記事の結び。 `hits: 1` 出所 detector-A（run 001）

### fidelity チェックリスト追補
- **#14 序列・価値・程度強度の移動** `status: done` `hits: 2run` 適用: 2026-08-28-001,002 ← f019（並列→基盤の序列混入・2026-06-12）に加え、e012「必要→欠かせない」(002, 実ロールバック) と e018「欠かせない→重要な」(001, 境界) で再現。接続語/評価語の置換で序列・優劣・因果強度・価値の程度が新規付与/移動していないかを検査。順序尺度 `望ましい<大切<必要<不可欠<必須`、ハイプ減衰は一段階まで許容。`content-fidelity-auditor.md` に #14 として明記＋#5 の論理接続詞削除は復元可能時のみ pass を追記。出所 fidelity-A（run1）, fidelity-A/B（run2）
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。`status: ready` `hits: 2run`（run2 fidelity-A/B が再度手動照合で代替、定式化未了）出所 fidelity-B（run1）, fidelity-A/B（run2）
- **義務→依頼形変換時の義務担保語チェック** `status: ready` `hits: 1run` 公的文書で「必要がございます→ください」変換時、義務を担保する共起語（あらかじめ・必ず・要）が残存するか。義務性の弱化（義務→任意）を防ぐ。出所 fidelity-B（run2）
- 「情報を含む削除 vs ボイラープレート削除」二分判定: 削除 span に (a)数値/固有名詞/日付 (b)条件/因果節 (c)固有の例示 を含めば情報欠落、挨拶/CTA/装飾/自己言及のみならボイラープレート。出所 fidelity-B
- **term-diff 機械照合**（技術文）: 原文の技術トークン集合 ⊆ 推敲文（開放許可語を除く）を集合演算で照合し専門語の暗黙欠落を捕捉。出所 fidelity-A（run2）
- #5論理関係 と #11情報追加 の責任境界を一意化（主因項目を 1 つに正規化）。出所 fidelity-A
- modality 強度を順序尺度化（要請/推奨/義務/必須）。← #14 適用で一部吸収。出所 fidelity-A

### playbook レシピ追補
- **C-5 絵文字削除後の文末/区切り吸収ルール**（句点で吸収 or 削除のどちらか明記）。出所 rewriter-B
- **D 系結びは削除一択でなく「最小着地文を残す」**（減らしすぎ下限）。実例: B の「気軽に始めてみてください」。出所 rewriter-B, naturalness-B
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**という例外則。出所 rewriter-A
- **原文が元から推量の D 系は推量を保持**（「断定へ」の一律処方の例外）。出所 rewriter-A
- **状態叙述×受動×謙譲の統合レシピ** `hits: 1run` 「〜されることとなっております／行われるものでございます」は A-6+A-8+敬語が重畳。個別 finding でなく「1 つの能動断定に畳む」統合処方＋統合 edit 記録様式（`finding_ids` 配列）。出所 rewriter-B（run2）
- **敬体 E-2 変奏カードの明示** `hits: 1run` 敬体は手札が少ない。「ください（依頼形）」「〜ません（否定断定）」を変奏カードとして E-2 敬体側に明記。ただし依頼形の反復が新たな単調を生まないか連鎖調整。出所 rewriter-B（run2）
- **H-1 削減率のジャンル可変** `hits: 1run` 公的文書では「また・なお」が要件並置の機能語。70%削減は読みにくさを招くため公的文書は5割目安。出所 rewriter-B（run2）
- **常体「である」収束の二次 E-2 監視** `hits: 1run` A-6/D-5 解消を機械適用すると「である」一本調子が再発生。段落境界で「だ」等に崩す監視項目を E-2 に追加。出所 rewriter-A（run1）
- **業界標準語ホワイトリストの明文化** `hits: 2run` カタカナ開放/維持の線引きが finding 依存で不安定。技術ジャンル用の許容リスト（維持: ベクトルDB/エンベディング/RAG/レイテンシ 等／開放: ソリューション/アプローチ/パフォーマンス/スケーラビリティ 等）を references に固定。出所 rewriter-A（run1）, fidelity-A/naturalness-A（run1,2 で境界不安定を報告）
- **A-8 受動→能動で主題（〜は→〜を）保持の可否判断** `hits: 1run` トピック段落では主題を崩さない。出所 rewriter-A（run1）

### naturalness 判定の精緻化
- 過推敲シグナルの定量化（敬体/常体混入は文末形態の二値カウントで機械検出）。`hits: 2run`（両 run の naturalness が二値カウントで文体崩れ0を実証）出所 naturalness-A（run1）, naturalness-A/B（run2）
- クラスタ系 finding（B-2 密集・C-1 列挙）はクラスタ崩壊時に個別 severity を降格するルール。出所 naturalness-A
- E-2 文末単調の到達可能ライン緩和（体言止め1箇所以上で合格、文体維持制約下の過推敲回避）。`hits: 2run` 敬体（公的文書）は体言止め・「でしょう」が register を崩すため **S2→S3（許容残存）が実質的な床**と明記。常体は「である」3回で露見ラインだが分散良好なら S3 監視。出所 naturalness-B（run1）, naturalness-A/B（run2）
- **grade 表に S3 総量ガード** `hits: 1run` S1/S2=0 でも S3 多数（例 S3≥6）なら A にせず B 据え置き。または「score_after<10 なら改善率要件を緩和」の補助条項（短文対策）。出所 naturalness-A/B（run2）
- 絶対残存数ガードを grade 表に組込み（改善率が高くても S1 が1件でも C 以下）。出所 naturalness-A, naturalness-B
- **ジャンル別 register 許容ホワイトリスト** `hits: 1run` 公的文書の「〜につきましては／対象となる方／掲載されております」等は正当な定型。同一 taxonomy 機械適用で過検出/過小検出が両方向に振れるため、検出器・レビュアーで共有する許容定型リストを taxonomy 参照側に持たせる。出所 naturalness-B（run2）

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 2run`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B, fidelity-A, naturalness-A（run1）
- 再現 2026-08-28: 技術ジャンルで「業界標準語ホワイトリスト」の明文化要望（維持/開放の線引き）。上の playbook レシピ追補「業界標準語ホワイトリスト」と統合して次回適用候補。出所 rewriter-A, fidelity-A, naturalness-A（run2）

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。出所 detector-A
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B
