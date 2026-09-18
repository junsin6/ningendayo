# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-09-18（run 001 技術解説, 002 公的文書）。この日 IMP-001 / IMP-002 / IMP-003 / IMP-006 を適用（done）、IMP-004 を部分適用。

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done(2026-09-18)` `hits: 2run(8agent)`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除・カタカナ→漢字縮約で機械的に膨張。day0 Sample B は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。day1 も run001 39.3%・run002 35% と警告域に入ったが両者 fidelity=pass・自然度 A の正当削除だった（**別 run で再現＝昇格**）。
- 出所: (day0) rewriter-A, rewriter-B, naturalness-B /（day1）rewriter-001, rewriter-002, naturalness-001, naturalness-002
- 提案→**適用済み**: (a) `change_rate`（総・参考）/ `insertion_rate` / `deletion_rate` を分離計上。(b)(c) 純削除主導（del≫ins）で fidelity=pass なら change_rate 50% 超でも中断しない。(d) 強制中断は `insertion_rate` 30% 超など意味改変基準へ置換。
- 適用: `rewriting-playbook.md §変更率の数え方 v1.1`, `japanese-style-rewriter.md`（3指標＋判定）, `SKILL.md §3・§総合判定`。適用 run: 2026-09-18。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done(2026-09-18)` `hits: 2run(6agent)`
- 症状: 正規化式が SSOT に無く各エージェントが K を逆算 → 数値がぶれる。day1 でも detector-001/002・naturalness-001/002 が各々 K=40/45/逆算係数 を独自採用（**別 run で再現＝昇格**）。
- 出所: (day0) detector-A, detector-B /（day1）detector-001, detector-002, naturalness-001, naturalness-002
- 提案→**適用済み**: 長さ非依存の飽和曲線 `severity_weighted_score = 100×raw/(raw+40)`（K=40 半飽和点）を SSOT 確定。`raw_weighted_sum`（生値）を meta に併記必須化。旧 `min(100,raw/length×1000)` は短文飽和欠陥のため不採用。
- 適用: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出＋スキーマ`。適用 run: 2026-09-18。taxonomist が v1.1 として審査。

### IMP-003 score_before のフィールド契約が曖昧 `status: done(2026-09-18)` `hits: 1run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。
- 出所: naturalness-A
- 提案→**適用済み**: 「score_before = 02_detection.json の meta.severity_weighted_score」を naturalness-reviewer.md §処理 step1 に明文化（IMP-006 適用と同時、同一正規化式 K=40 で可換化）。
- 適用: `naturalness-reviewer.md`。適用 run: 2026-09-18。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: partial(2026-09-18)` `hits: 2run(4agent)`
- 症状: 文末単調・文頭接続詞過多は文書レベル分布。単一 start/end では density が過大化（day1 detector-001 は E-2 を start=0/end=740 で表現し density 混入を手動除外、detector-002 も同様）。**別 run で再現＝昇格**。
- 出所: (day0) detector-B, detector-A /（day1）detector-001, detector-002
- 提案→**部分適用**: finding に `scope: "span"|"document"` を追加。`ai_tell_density` は重複区間をユニオンで数え document スコープを分子から除外、と SSOT 明記。**残: `scope:"scattered"` ＋ `occurrences:[[s,e],…]` 配列は未実装（次回昇格候補）**。
- 適用: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md`。適用 run: 2026-09-18。

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run(8agent)`
- 症状: 1 span が複数カテゴリに該当（day1: 001「ソリューションを提供します」= B-2＋A-10、002「実施されることとなりました」= A-8＋A-6）。edits/findings 1:1 前提で category_summary が実態を過小評価。rewriter-001 は diff に `finding_ids`（複数）を採用して回避。**別 run で再現＝昇格継続、未適用**。
- 出所: (day0) detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A /（day1）detector-001, detector-002, rewriter-001
- 提案: 「1 span = 主分類 1 finding」を基本とし `merged_findings`/`secondary_category` 配列を許容。diff は `finding_ids`（複数）を正式化。category_summary は「findings の category 先頭文字を集計」と注記。**次回（day2 以降）適用候補**。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を再実行できず score_after が推定 `status: done(2026-09-18)` `hits: 2run(2agent)`
- 症状: 仕様は「検出器を同基準で再走査」。day1 で判明した構造的制約: **naturalness-reviewer 自身がサブエージェントで、そこから更に ai-tell-detector をサブエージェント起動できない環境**（Task/Agent/ListAgents 未提供）。両 naturalness（001/002）が同一報告 → **別 run で再現＝昇格**。
- 出所: (day0) naturalness-A /（day1）naturalness-001, naturalness-002
- 提案→**適用済み**: 再実行経路を 2 通り規定し `detector_run_mode: "subagent"|"in_process"` を出力必須化。サブエージェント起動不可なら、レビュアーが detector.md 手順＋taxonomy 同一スキーマ・**同一正規化式（K=40）**でインプロセス厳密再走査（手動印象照合は禁止＝span を必ず数える）。オーケストレーターが detector を再走査モードで呼ぶ 2 段構成も可。
- 適用: `naturalness-reviewer.md §処理・出力スキーマ`, `SKILL.md §5 チーム説明`。適用 run: 2026-09-18。

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 001(day0)。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。 `hits: 1` 出所 detector-B(day0)
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B(day0)
- **【NEW 2026-09-18】硬敬語の懇請定型（公的文書）★日本語固有** 「〜いただきますようお願い申し上げます／〜する次第です／におかれましては／につきましては」。実例(002): 「行っていただきますようお願い申し上げます」「ご了承いただきますようお願いいたします」。※D-7 符号は既存ブログ候補と衝突するため taxonomist が別符号を割当（taxonomy.md 候補欄参照）。 `hits: 1run(2agent)` 出所 detector-002, rewriter-002
- **【NEW 2026-09-18】A-8 拡張: 行為者不在受動（agentless passive）** 現 A-8 は「によって」限定。実例(002): 「実施される／行われる／中止される／指定された」。公的文書 AI 文の主症状。A-8 定義拡張 or A-8b 分離候補。 `hits: 1run(2agent)` 出所 detector-002, rewriter-002
- **【NEW 2026-09-18】A-10 万能動詞に「可能にする（enables）」追加** 実例(001): 「処理することを可能にし」。detector が取りこぼし naturalness が carryover 検出。 `hits: 1` 出所 detector-001, naturalness-001
- **【NEW 2026-09-18】I-6「〜という面/観点で」論点水増し** in terms of / from the perspective of の直訳。実例(001): 「スケーラビリティという面でもメリットをもたらします」「セキュリティやプライバシーの観点からも」。 `hits: 1` 出所 detector-001

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019（並列→基盤の序列混入）はこの項が無く #5/#11 へ漏れ込んだ。`status: ready` `hits: 1` 出所 fidelity-A
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。`status: ready` `hits: 1` 出所 fidelity-B
- 「情報を含む削除 vs ボイラープレート削除」二分判定: 削除 span に (a)数値/固有名詞/日付 (b)条件/因果節 (c)固有の例示 を含めば情報欠落、挨拶/CTA/装飾/自己言及のみならボイラープレート。出所 fidelity-B
- #5論理関係 と #11情報追加 の責任境界を一意化（主因項目を 1 つに正規化）。出所 fidelity-A
- modality 強度を順序尺度化（任意<推奨<要請<義務<必須）。1段でも下がったら要フラグ。`hits: 2run` 出所 fidelity-A(day0), fidelity-002(day1)（「必要がある」→「してください」で必須→依頼にずれる懸念）
- **【NEW 2026-09-18】並列属性の属性保存チェック（項目10配下）** 「AかつB」「A・B」二重修飾の推敲で片属性が落ちやすい。実例(002 f023): 「迅速かつ的確な」→「的確な」で**「迅速」脱落＝実質情報の欠落**（迅速≠的確）。content_breach 判定 → f023 ロールバックで復元。`hits: 1run(3agent)` 出所 fidelity-002, rewriter-002, naturalness-002
- **【NEW 2026-09-18】依頼行為の欠落チェックを独立項目化（公的文書）** 「〜のお願い/ご了承/ご協力」等の発話行為スロットが推敲文に残るかの照合表。丁寧形削減時の依頼消失を機械検出。実例(002): 依頼5件全保持を確認。 `hits: 1` 出所 fidelity-002
- **【NEW 2026-09-18】決定告知のアスペクト判定基準（項目8）** 「実施されることとなりました（決定済み）」→「実施します」で決定済み性の含意が変わりうる。事実同一なら可／決定主体・決定済み性が変わるなら fail、と明文化。 `hits: 1` 出所 fidelity-002

### playbook レシピ追補
- **C-5 絵文字削除後の文末/区切り吸収ルール**（句点で吸収 or 削除のどちらか明記）。出所 rewriter-B
- **D 系結びは削除一択でなく「最小着地文を残す」**（減らしすぎ下限）。実例: B の「気軽に始めてみてください」。出所 rewriter-B, naturalness-B
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**という例外則。出所 rewriter-A
- **原文が元から推量の D 系は推量を保持**（「断定へ」の一律処方の例外）。出所 rewriter-A
- **【NEW 2026-09-18】硬敬語の懇請定型の削減下限（公的文書）** 全削除・全「ください」化は失礼・不自然。「文書の中心的な結び1件は敬意形（お願い申し上げます 等）を保持、他は ください／お願いします へ分散」。実例(002): 5定型→中心1件保持＋分散。`hits: 1run(2agent)` 出所 rewriter-002, naturalness-002
- **【NEW 2026-09-18】A-8 能動化の安全条件** 「主体が発信者（自治体・企業等）で自明な場合のみ能動化可。第三者・不特定・法令主体の受動は保持」。実例(002): 全件が市主体で能動化可、中立性・責任所在を保持。`hits: 1` 出所 rewriter-002
- **【NEW 2026-09-18】F-2 二重修飾は真の同義のみ集約** 「迅速≠的確」のように二語が別次元の情報なら両方保持。playbook 例（重要かつ中心的）は真の同義のみ。`hits: 1run(3agent)` 出所 rewriter-002, fidelity-002, naturalness-002（f023 毀損の根治）
- **【NEW 2026-09-18】ジャンル係数（公的文書）** E-2 変奏で体言止めは本文で不自然→見出し/箇条書きに限る。H-1 文頭接続詞削減率は公的文書で緩め、機能する「なお」1件は保持。`hits: 1run(2agent)` 出所 rewriter-002, naturalness-002

### naturalness 判定の精緻化
- 過推敲シグナルの定量化（敬体/常体混入は文末形態の二値カウントで機械検出）。出所 naturalness-A
- **【NEW 2026-09-18】公的文書ジャンルの敬語下限チェック** 過推敲サブシグナル「過度な脱丁寧化（de-politening）」を追加。依頼の中心的結び≥1保持・市民向け要請は尊敬/謙譲形保持・安全指示は「〜してください」可。`hits: 1` 出所 naturalness-002
- **【NEW 2026-09-18】change_rate を等級表へ反映** 30〜50% は原則 B 上限（削除主導かつ fidelity クリア時のみ A 許容）、50% 超は hold 強制。「降格しない warning」と「降格する signal」を分離（現状 change_rate 30%超が二重計上リスク）。`hits: 1` 出所 naturalness-002 ※IMP-001 と連動、等級表反映は次回候補
- **【NEW 2026-09-18】fidelity と naturalness の裁定順位** naturalness-A でも fidelity finding が残るケース（002 f023）用に「fidelity finding は naturalness の accept に優先」を等級表に明記。`hits: 1run(2agent)` 出所 naturalness-002, fidelity-001（責任境界）
- **【NEW 2026-09-18】検出器再実行の run_mode 記録**（IMP-006 で適用済）。`detector_run_mode` を出力必須化。
- クラスタ系 finding（B-2 密集・C-1 列挙）はクラスタ崩壊時に個別 severity を降格するルール。出所 naturalness-A
- E-2 文末単調の到達可能ライン緩和（体言止め1箇所以上で合格、文体維持制約下の過推敲回避）。出所 naturalness-B
- 絶対残存数ガードを grade 表に組込み（改善率が高くても S1 が1件でも C 以下）。出所 naturalness-A, naturalness-B

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 1run(3agent)`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B, fidelity-A, naturalness-A

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。出所 detector-A
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B
