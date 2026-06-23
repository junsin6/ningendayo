# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-06-23（run 001 技術解説, 002 公的文書）。本日 IMP-001 / IMP-002 / IMP-003 / IMP-006 を適用（done）。

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done` `hits: 2run` `applied: 2026-06-23-001/002`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。Sample A も 47.6% と高止まり。
- **2026-06-23 再現**: run001 change_rate 32.6%（ins 9.2%/del 23.4%）、run002 48.76%（ins 15.5%/del 33.2%）。いずれも fidelity=pass・自然度 A だが del 主導。両 run で再現 → 適用。
- 出所: rewriter-A, rewriter-B, naturalness-B（day0）/ rewriter-A, rewriter-B, naturalness-A, naturalness-B（2026-06-23）
- **適用内容**: ins_rate/del_rate を分離計上。警告・中断は `ins_rate`（語句改変率）基準（>0.15 警告 / >0.30 中断）に変更。del 主導の純削除は中断対象外＝override accept を正式化。`rewriting-playbook.md §変更率の数え方`・`SKILL.md §推敲/§総合判定`（override 行を追加）を編集済み。
- 残: `japanese-style-rewriter.md` への ins/del 出力明記は次回（diff には既に算出あり）。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2run` `applied: 2026-06-23 (taxonomy v1.1)`
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える（Sample A raw106→92.5、taxonomy 例は raw56→71.5 と不整合）。
- **2026-06-23 再現**: detector-A が `100*raw/(raw+25)`（→71.9）、detector-B が `raw/文字数*1000`（→59.4）と**別式を即興採用**し再現性崩壊。両 run で再現 → 適用。
- 出所: detector-A, detector-B（day0・2026-06-23 とも）
- **適用内容**: taxonomy §検出出力スキーマに canonical 式 `severity_weighted_score = 100 * raw / (raw + 22)`（raw=S1×5+S2×2+S3×0.5、長さ非依存・飽和型、小数1位丸め）を明記。K=22 は worked example フィット（raw56→71.8）。taxonomist 審査で **v1.0→v1.1** へ昇格。`ai-tell-detector.md §スコア算出` も同式参照に編集。score_after も同式（IMP-003 整合）。

### IMP-003 score_before のフィールド契約が曖昧 `status: done` `hits: 2run` `applied: 2026-06-23 (naturalness-reviewer.md)`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score 92.5）。レビュアーごとに数値がぶれる。
- **2026-06-23 再現**: naturalness-A/B とも score_after の重み・基準が detector 依存でぶれると再指摘。
- 出所: naturalness-A（day0）/ naturalness-A, naturalness-B（2026-06-23）
- **適用内容**: `naturalness-reviewer.md §処理` に「score_before = 02_detection.json の meta.severity_weighted_score をそのまま採用、score_after = 再実行検出器の同 canonical 式の値」を明文化。IMP-002 と式を共有。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run`
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
- **2026-06-23 再現**: detector-A/B とも E-2/E-1 の文書レベル finding に start/end 必須で代表 span を1つ選ぶしかなく規定が曖昧と再指摘。density も span 重複で過大化（run002 density 0.498）。
- 出所: detector-B, detector-A（day0・2026-06-23）
- 提案: `span_type: "contiguous"|"scattered"|"document"` と scattered 用 `occurrences: [[s,e],...]` を追加。density は重複 span をマージし locator を除いた実 AI クセ文字数ベースと定義。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`（density のマージ注記は本日 detector.md に1行追加済み）

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。
- **2026-06-23 再現**: detector-A（A-5＋A-6 複合、A-8＋A-6 複合）、detector-B（A-8＋A-6＋I-1 重畳）、rewriter-A/B（統合 edit の diff 記法）、fidelity-A/B（統合 edit の部分ロールバック不能）が横断再現。secondary_category と merged_findings の両方が要望された。
- 出所: detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A（day0）/ detector-A/B, rewriter-A/B, fidelity-A/B（2026-06-23・横断最多）
- 提案: 「1 span = 主分類 1 finding」を基本とし、`merged_findings: [...]` または `secondary_category` 配列を許容。統合 edit には復元用 `merged_span` ＋元 before 群を必須化（fidelity の部分ロールバック用）。category_summary は主分類先頭文字で集計と注記。
- 影響: 全 .md のスキーマ節。**次回適用最優先候補**（hits 2run・横断的）。

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: done` `hits: 2run` `applied: 2026-06-23 (naturalness-reviewer.md)`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。
- **2026-06-23**: 本日の naturalness-A/B は実際に ai-tell-detector サブエージェントを呼び出して score_after を実測（手動照合に非依存）。運用で再現確認 → 文面に必須化を明記。
- 出所: naturalness-A（day0）/ naturalness-A, naturalness-B（2026-06-23 実証）
- **適用内容**: `naturalness-reviewer.md §処理 1.` に「ai-tell-detector をサブエージェントとして再呼び出し、手動照合は禁止」と明記。

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 001(06-12)。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B
- **D-7案 過剰定型敬語クラスタ（★日本語固有・公的文書）** 「賜りますようお願い申し上げます」(run002 で2回)「所存でございます」「何卒ご了承賜りたく」。AI 生成の公的文書/ビジネス文の決定的シグネチャ。現状 D-1 便宜計上。 `hits: 1run` 出所 detector-B, rewriter-B, naturalness-B（2026-06-23 taxonomy v1.1 候補欄に登録済み。別の公的文書 run で再現すれば昇格）
- **A 系案 進行アスペクト「〜していく／〜ていく」冗長付加** 「解説していきます」「進化を遂げていく」「キャッチアップしていく」。 `hits: 1run` 出所 detector-A（候補欄登録済み）
- **B-2 サブ候補 カタカナ動詞化** 「キャッチアップする／レバレッジする」英語動詞の名詞＋する化。 `hits: 1run` 出所 detector-A（候補欄登録済み。B-2 注記吸収 vs 独立を昇格時に比較）
- **I-6案 他律的決定「〜こととなりました／こととなっております」** 決定主体を曖昧化する公的文書表現。 `hits: 1run` 出所 detector-B（候補欄登録済み）

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019（並列→基盤の序列混入）はこの項が無く #5/#11 へ漏れ込んだ。`status: ready` `hits: 1` 出所 fidelity-A
- **暗黙推論の明示化を独立チェック項目化** 文脈から推論可能な内容を断定命題へ昇格させる過剰補完。本日のロールバック主因 run001 f016「大きなアドバンテージ」→「応答が速いという強み」は #5因果 と #11追加 の両方に跨り責任が曖昧だった。専用項目化で判定が一意になる。`status: ready` `hits: 1` 出所 fidelity-A(2026-06-23)
- **程度修飾（intensifier）の保存を独立サブ項目** 「大きな/非常に/著しい」等の連体・程度修飾は B-2/A-10 の語句置換で機械的に巻き込まれ脱落しやすい（run001 f017「大きなメリット」→「有利」）。量化(#6)とは別軸。`status: ready` `hits: 1` 出所 fidelity-A(2026-06-23)
- **#14案 告知の行動可能性（actionability: who/when/where/what-to-do の保存）** 公的文書 fidelity の核。義務形→依頼形の弱化が行動喚起力を下げていないか。`status: ready` `hits: 1` 出所 fidelity-B(2026-06-23・run002)
- **必須性の文脈復元（単独文 fidelity vs 文脈込み fidelity の分離）** run002 f009「ご利用いただく必要→ご利用ください」は単独では弱化だが文脈で必須性が復元され pass。判断基準が属人的。`status: ready` `hits: 1` 出所 fidelity-B(2026-06-23)
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。`status: ready` `hits: 1` 出所 fidelity-B
- 「情報を含む削除 vs ボイラープレート削除」二分判定: 削除 span に (a)数値/固有名詞/日付 (b)条件/因果節 (c)固有の例示 を含めば情報欠落、挨拶/CTA/装飾/自己言及のみならボイラープレート。出所 fidelity-B（IMP-001 適用時に playbook §変更率へ反映済み）
- #5論理関係 と #11情報追加 の責任境界を一意化（主因項目を 1 つに正規化）。出所 fidelity-A
- **modality 強度を順序尺度化（任意/依頼/推奨/義務/必須、1段の弱化は許容・2段以上は fail）** `status: ready` `hits: 2run`。day0 fidelity-A ＋ 2026-06-23 fidelity-A（f023 推量→確信の強化を fail）・fidelity-B（義務→依頼の弱化判定）で横断再現。**次回適用候補**。

### playbook レシピ追補
- **C-5 絵文字削除後の文末/区切り吸収ルール**（句点で吸収 or 削除のどちらか明記）。出所 rewriter-B
- **D 系結びは削除一択でなく「最小着地文を残す」**（減らしすぎ下限）。実例: B(06-12) の「気軽に始めてみてください」/ run002 の「お知らせいたします」を finding 外として保持。`hits: 2run` 出所 rewriter-B, naturalness-B(day0), rewriter-B(2026-06-23)。**次回適用候補**。
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**という例外則。出所 rewriter-A
- **原文が元から推量の D 系は推量を保持**（「断定へ」の一律処方の例外）。`hits: 2run` 出所 rewriter-A(day0) / round2 で f023「でしょう」復帰(2026-06-23)。
- **公的文書ジャンル専用レシピ群が不在** A-8 能動化時の主語復元語（当館/本館）指針、I-3 義務形→依頼形（〜ください）の変換、硬い並列接続「ならびに/および/につきましては/におかれましては」の自然化、「残す/削る」のジャンル別線引き表。`status: ready` `hits: 1run` 出所 rewriter-B(2026-06-23・run002)
- **ロールバック専用セクションが playbook に無い** 過修正の戻し方（粒度）、統合 edit のロールバック単位＝span 全体になる注意と巻き込み edit の保持、A-10「行為者・動詞は直せても目的語の内実は補完しない」禁止則、置換時の程度修飾保護リスト（大きな/著しい等は不可侵）。`status: ready` `hits: 1run` 出所 rewriter(round2 2026-06-23)

### naturalness 判定の精緻化
- 過推敲シグナルの定量化（敬体/常体混入は文末形態の二値カウントで機械検出）。出所 naturalness-A
- **過推敲シグナルに `severity: real | formal` を付与し、等級降格は real のみで数える**（純削除起因の change_rate 超過は formal＝実害なし）。`status: done` `applied: 2026-06-23 (naturalness-reviewer.md §処理4)` 出所 naturalness-A, naturalness-B（IMP-001 と同時適用）
- クラスタ系 finding（B-2 密集・C-1 列挙）はクラスタ崩壊時に個別 severity を降格するルール。出所 naturalness-A
- E-2 文末単調の到達可能ライン緩和（体言止め1箇所以上で合格、文体維持制約下の過推敲回避）。出所 naturalness-B
- **絶対残存数/絶対 score 値ゲートを grade 表に組込み**（改善率が高くても score_after の絶対値で A/B を AND 条件化、S1 1件でも C 以下）。`status: ready` `hits: 2run` 出所 naturalness-A, naturalness-B(day0 ＋ 2026-06-23)。**次回適用候補**。
- **公的文書ジャンル専用の過推敲シグナル**: 告知の確定性希薄化（断定→依頼の過度転換で義務/制約が曖昧化）、礼儀の不足化（定型敬語の削りすぎ）、主語の過剰補填（「当館が」を毎文に立て翻訳調に逆戻り）。`status: ready` `hits: 1run` 出所 naturalness-B(2026-06-23)
- **新シグナル候補**: `possible_form_chain`（可能形「できます/できるのです」の近接連鎖・run001 残存 S2）、`topic_sentence_uniformity`（段落冒頭が同一主語の C-4 残存）、`deletion_density_drop`（純削除による情報密度の過低下＝formal/real 切り分け指標）。`hits: 1run` 出所 naturalness-A(2026-06-23)

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 1run(3agent)`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B, fidelity-A, naturalness-A

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。出所 detector-A
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B
