# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-08-30（run 2026-08-30-001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done(2026-08-30-001/002)` `hits: 2run(6agent)`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。Sample A も 47.6% と高止まり。
- **再現(2026-08-30)**: run-001 で change_rate 0.374（30% 警告域）だが内訳は swap 0.209/trim 0.157＝冗長削除主導。override accept で正しく処理。rewriter-001/002 が swap/trim 分離を先行実装、naturalness-001/002 も指標の穴を再指摘。異なる run での再現を確認 → 昇格。
- 出所: rewriter-A, rewriter-B, naturalness-B（day0）＋ rewriter-001, rewriter-002, naturalness-001, naturalness-002（day1）
- 提案: (a) 「語句改変率(swap)」と「構造/削除率(trim)」を分離計上。(b) 装飾・常套句の純削除分を change_rate から控除。(c) 挿入率を単独併記し、del≫ins の削除主導ケースは中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`
- **適用(2026-08-30)**: playbook に §変更率の数え方 を新設し swap/trim 分離と閾値（swap 30% 警告 / trim は中断対象外 / 全体 50% は意味改変 edit 比率で判定）を明記。rewriter/ SKILL の変更率監視をこの二指標に更新。diff スキーマに `kind: swap|trim|rhythm` を標準化。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done(2026-08-30, v1.1)` `hits: 2run(4agent)`
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える（Sample A raw106→92.5、taxonomy 例は raw56→71.5 と不整合）。
- **再現(2026-08-30)【決定的】**: detector-001 と detector-002 が**別々の正規化式を独自採用**（001: `100·S/(S+15)` → 87.1／002: `min(100, raw/input_length*1000)` → 83.6）。同一パイプラインで検出器ごとに互換性のないスコアが出ることを実証。異なる run での再現かつ 2 検出器の不一致 → 昇格。
- 出所: detector-A, detector-B（day0）＋ detector-001, detector-002（day1）
- 提案: 飽和しにくい正規化を SSOT 明記。分母（input_length 依存 or 固定 max）を確定。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出`
- **適用(2026-08-30, taxonomist 審査 → v1.1)**: SSOT に正規化式 `severity_weighted_score = 100·S/(S+K)`（K=20 飽和定数、S=5·S1+2·S2+0.5·S3）を確定。`ai_tell_density` の分母は「改行を除いた本文文字数」に固定。全検出器・naturalness 再計測でこの単一式を強制。

### IMP-003 score_before のフィールド契約が曖昧 `status: ready` `hits: 1run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score 92.5）。レビュアーごとに数値がぶれる。
- 出所: naturalness-A
- 提案: 「score_before = 02_detection.json の meta.severity_weighted_score」と明文化。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run(5agent)`
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
- **再現(2026-08-30)**: detector-001（E-2 文末反復を初文末に便宜的に紐付け → start/end が誤誘導）、detector-002（overlap 節の span 切り分け）、rewriter-001（E-2 の before/after が同一で diff 表現不能）が再指摘。次回 Step4 適用の最有力候補。
- 出所: detector-B, detector-A（day0）＋ detector-001, detector-002, rewriter-001（day1）
- 提案: `scope: "span"|"scattered"|"document"` と scattered 用 `occurrences: [[s,e],...]` を追加。density は重複・locator を除いた実 AI クセ文字数ベースと定義。document スコープは before/after を「パターン記述」で持てるようにする。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`, `japanese-style-rewriter.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run(8agent)`
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。
- **再現(2026-08-30)**: detector-001（A-5+G-1「でしょう」／A-13+A-1+B-2「というアーキテクチャにおいて」の重畳を主カテゴリ1件へ自己流集約 → detected_count が実態より少ない）、detector-002（A-9/I-1/A-10 入れ子）、rewriter-002（f005-f007 を 1 edit へ統合）が再指摘。次回 Step4 の有力候補。
- 出所: detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A（day0）＋ detector-001, detector-002, rewriter-002（day1）
- 提案: 「1 span = 主分類 1 finding」を基本とし、`merged_categories: [...]` 配列を許容。category_summary は「findings の主 category を集計」と注記。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: done(2026-08-30)` `hits: 2run(3agent)`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。
- **再現(2026-08-30)**: naturalness-001／002 の**両方**が「サブエージェント実行コンテキストからは ai-tell-detector を新規スポーンできない（Task/Agent 系ツール非搭載・ListAgents に detector 不在）」と明示報告。score_after はいずれも手動再走査による推定。異なる run で再現。
- 出所: naturalness-A（day0）＋ naturalness-001, naturalness-002（day1）
- 提案: 呼び出し経路を必須化するか、不可時は手動である旨をスキーマで強制記録。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`, `ai-tell-taxonomy.md §スキーマ`
- **適用(2026-08-30)**: naturalness-reviewer.md に「Agent ツールで ai-tell-detector を呼べる場合は必須。不可なら taxonomy 同一 score_formula で手動再走査し、`detector_rerun: {method: "agent"|"manual", score_formula, note}` を **必須フィールド**として 05_*.json に記録」を規定。SKILL.md の Phase4 記述も更新。手動照合の暗黙化を禁止し、方法の透明化を強制。

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 001。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B

#### 2026-08-30（day1）新規候補
- **【新分類 K】過剰敬語・二重敬語** ★日本語固有・公的文書ジャンルの塊。taxonomy 冒頭の設計思想が重心に挙げる「(2) 過剰な丁寧体・敬語」に対応カテゴリが A〜J に無い穴。サブ候補:
  - **K-1 謙譲の過剰スタッキング**「〜いただきますようお願い申し上げます」の反復。実例(002): 「ご理解賜りますようお願い申し上げます」「ご了承いただきますようお願い申し上げます」「お問い合わせいただきますようお願いいたします」「ご協力を賜りますよう、重ねてお願い申し上げます」＝1文書に4連。
  - **K-2「賜る」の濫用**、**K-3 二重敬語**。
  - 実例2件以上・人間の書き手はここまで機械的に積み上げない → v1.1 昇格要件充足。 `hits: 1` 出所 detector-002／裏づけ fidelity-002・naturalness-002（「敬語密度・敬意水準」を fidelity と naturalness の中間の穴として独立指摘）。**今日 taxonomist へ審査依頼。**
- **A-14「〜することによって」手段構文** 「動詞＋こと＋によって」＝英語 by -ing の直訳（手段）。A-8(by-passive) とも A-3(を通じて) ともズレる。実例(001) 4回: 活用することによって／与えることによって／選定することによって／この仕組みによって。 `hits: 1` 出所 detector-001。**今日 taxonomist へ審査依頼。**
- **A-8 の定義拡張: 無標受動(bare passive)の連発** 「〜される/された」を行為者省略のまま連鎖（公的文書で主症状）。現 A-8 は「によって後置」に限定され境界事例を拾えない。加えて (a)行為者不明化の受動＝除去／(b)主体秘匿の自然受動＝1〜2回許容 の敬体向けサブルールが要る。実例(002): 実施される/停止される×2/改善される/拡充される/告知が行われる。 `hits: 1` 出所 detector-002, rewriter-002, naturalness-002。
- **「〜が期待されます」行為者不在の未来受動締め** I-4 と D-6 の隙間に落ちる楽観的締め。実例(001): 「基盤となっていくことが期待されます」。 `hits: 1` 出所 detector-001。

### fidelity チェックリスト追補（day1 追加）
- **#14 敬意水準・依頼強度の保存**（公的文書・法令・謝罪文で必須）: 謙譲↔丁寧の gradient（申し上げます↔ください）を評価軸に。系統的ダウンシフトの累積を検知。 `status: ready` `hits: 1` 出所 fidelity-002, naturalness-002。
- **#15 談話標識クラスの入替検査**: 具体化/例示/換言/帰結の標識が入れ替わっていないか。実例(001) f020「具体的には(=これがその仕組み)」→「たとえば(=一例)」。 `hits: 1` 出所 fidelity-001。
- **#12 細分化: 逆極性・上位下位ずれ**: 「低いほど良い指標を高いほど良い語で言い換えていないか」。実例(001) f024「レイテンシ(遅延)→応答速度(速度)」逆極性、「スケーラビリティ→拡張性(≒extensibility)」下位ずれ。 `hits: 1` 出所 fidelity-001。
- **遂行的発話(performative)の保存**: 告知・依頼・謝罪など発話行為自体の保存。実例(002) 「お知らせいたします」を受動除去の巻き添えで消さない。 `hits: 1` 出所 fidelity-002, rewriter-002。
- **modality escalation の閾値**: 推量/見込み→断定は fidelity fail（実例 002 f009「見込まれております」→「拡充されます」でロールバック発生）。可能性(可能性がございます)は正しく温存できた対比あり。 `hits: 1` 出所 fidelity-002。

### playbook レシピ追補（day1 追加）
- **A 系 助詞置換の衝突回避**: 同一文内で A-8「によって→で」と A-3「を通じて→で」が重なると二重「で」で不自然。一方を動詞句化（を使って）。実例(001) f010+f011。出所 rewriter-001。
- **技術ドメイン カタカナ ホワイトリスト**: RAG・エンベディング・コンテキスト・クエリ・インデックス・アルゴリズムは維持、レイテンシは括弧併記で開く、スケーラビリティ→拡張性 は文脈依存。出所 rewriter-001。
- **公的文書 E-2 クロージング辞書（体言止め除外）**: 公的お知らせの結びは体言止めが軽すぎる。`ご了承ください`/`賜りますようお願い申し上げます`/`いただけますと幸いです` の敬体辞書を別立てにし、同一クロージング形の上限を定義。出所 rewriter-002。

### naturalness 判定の精緻化（day1 追加）
- **ジャンル補正係数**: 公的文書の定型 whitelist（賜る・申し上げる・何卒・おかれましては・中立受動）を S 件数から控除。件数だけ見る鑑が良文を B/C に押し下げるリスク。出所 naturalness-002。
- **score_after 絶対値上限を grade に併記**: 改善率だけで A を出さず、A は score_after<15 必須 等。長文＋大量 finding で改善率が高く出やすい歪みの補正。出所 naturalness-001。
- **過推敲の定量化**: 文末最頻形の占有率（実例 001 ます 5/13=38%）、敬語マーカー密度（前後比較・ジャンル別フロア）を数値メトリクス化。bool 判定の属人性を除去。出所 naturalness-001, naturalness-002。
- **同一表現多用による指示混同**: 推敲で新たに生じた同一語反復が、原文で区別されていた指示対象を混同させていないか。実例(001) 「中核を担う」が2段で反復。出所 fidelity-001, naturalness-001。

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019（並列→基盤の序列混入）はこの項が無く #5/#11 へ漏れ込んだ。`status: ready` `hits: 1` 出所 fidelity-A
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。`status: ready` `hits: 1` 出所 fidelity-B
- 「情報を含む削除 vs ボイラープレート削除」二分判定: 削除 span に (a)数値/固有名詞/日付 (b)条件/因果節 (c)固有の例示 を含めば情報欠落、挨拶/CTA/装飾/自己言及のみならボイラープレート。出所 fidelity-B
- #5論理関係 と #11情報追加 の責任境界を一意化（主因項目を 1 つに正規化）。出所 fidelity-A
- modality 強度を順序尺度化（要請/推奨/義務/必須）。出所 fidelity-A

### playbook レシピ追補
- **C-5 絵文字削除後の文末/区切り吸収ルール**（句点で吸収 or 削除のどちらか明記）。出所 rewriter-B
- **D 系結びは削除一択でなく「最小着地文を残す」**（減らしすぎ下限）。実例: B の「気軽に始めてみてください」。出所 rewriter-B, naturalness-B
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**という例外則。出所 rewriter-A
- **原文が元から推量の D 系は推量を保持**（「断定へ」の一律処方の例外）。出所 rewriter-A

### naturalness 判定の精緻化
- 過推敲シグナルの定量化（敬体/常体混入は文末形態の二値カウントで機械検出）。出所 naturalness-A
- クラスタ系 finding（B-2 密集・C-1 列挙）はクラスタ崩壊時に個別 severity を降格するルール。出所 naturalness-A
- E-2 文末単調の到達可能ライン緩和（体言止め1箇所以上で合格、文体維持制約下の過推敲回避）。出所 naturalness-B
- 絶対残存数ガードを grade 表に組込み（改善率が高くても S1 が1件でも C 以下）。出所 naturalness-A, naturalness-B

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 1run(3agent)`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B, fidelity-A, naturalness-A

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。出所 detector-A
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B
