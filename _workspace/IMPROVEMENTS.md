# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-06-29（run 001 技術解説, 002 公的文書）

> 2026-06-29 サマリ: P0 群（IMP-001/002/003）が別 run で再現し hits≥2 到達 → **同日適用済み（done）**。IMP-004 は density 飽和対策のみ部分適用（span_type スキーマは ready 継続）、IMP-006 も適用。新候補に I-6（冗長敬語積層）・ジャンル別カタカナ白名単/severity 可変・modality 順序尺度・out_of_scope_residual を追加。

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done` `hits: 2run` 適用: 2026-06-29-001/002
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。Sample A も 47.6% と高止まり。
- 再現(2026-06-29): run 001 で change_rate 34.6%（delete 支配・収縮型）が再発火。fidelity=pass・自然度 A のため override accept した。出所 rewriter-001, rewriter-002, fidelity-001。
- 適用: `semantic_change_rate`（意味置換のみ）を主判定指標として導入。`change_rate`/`insert_rate`/`delete_rate` と分離計上。change_rate のみ閾値超なら override accept を SKILL §総合判定 表に正式化。編集ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md`（§3・§総合判定）。
- 残: `semantic_change_rate` の自動計算（difflib opcode の replace 分のみ集計）を将来スクリプト化したい。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2run` 適用: 2026-06-29-001/002
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える（Sample A raw106→92.5、taxonomy 例は raw56→71.5 と不整合）。
- 再現(2026-06-29): detector-001 は係数を独自に置き 86.2、detector-002 は `raw/total*100*9.5` で 73.1、naturalness は逆算係数 1.336 / 1.523 と run・agent ごとに非互換。
- 適用: 確定式 `score = 100×(1−exp(−per100/5.0))`（K=5.0 固定, per100=raw/input_length×100）を taxonomy §検出出力スキーマ・`ai-tell-detector.md §スコア算出` に明記。taxonomist が K=5.0 を検算承認（run001≈87.6 / run002≈78.5、低残存で一桁、高密度でも非飽和）。`meta.normalization` 併記を必須化。
- 残: score_after も normalization 併記を強制する文言の最終化（taxonomist 提案、次回）。

### IMP-003 score_before のフィールド契約が曖昧 `status: done` `hits: 2run` 適用: 2026-06-29-001/002
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score 92.5）。レビュアーごとに数値がぶれる。
- 再現(2026-06-29): naturalness-001/002 とも normalization_factor が detection.json に無く逆算が必要、と指摘。
- 適用: 「score_before = 02_detection.json の meta.severity_weighted_score をそのまま採用（再計算禁止）」「score_after は同一式・同一 K=5.0」を taxonomy と `naturalness-reviewer.md` に明文化。IMP-002 と一体で適用。出所 naturalness-001, naturalness-002。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready(部分適用)` `hits: 2run`
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
- 再現(2026-06-29): detector-001/002 とも E-1/E-2 文書レベル span が density を 1.0 近くへ飽和させるため手動除外、と指摘。rewriter-002 は文書レベル finding に before/after が紐づかない器の不在を指摘。
- 部分適用(2026-06-29): density から E・C・J の文書レベル finding を除外する規則を taxonomy・detector に明記（飽和対策）。**未適用**: `span_type` / `occurrences` / `document_level`+`achieved_via` のスキーマ拡張は ready 継続。
- 提案(残): `span_type: "contiguous"|"scattered"|"document"`、scattered 用 `occurrences: [[s,e],...]`、文書レベル finding に `resolution: full|partial|none`（naturalness-001）。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`, `naturalness-reviewer.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。
- 再現(2026-06-29): detector-002（A-6＋A-8/A-6＋I-4 が一句に重畳）、rewriter-001（f005/f008→f009 等の入れ子統合）、rewriter-002（findings 15 でも実 span 約 11）、fidelity-001/002（merged_with 欄が欲しい）。横断再現で hits≥2。
- 提案: 「1 span = 主分類 1 finding」を基本とし、diff に `merged_with: ["f001"]` / `co_processed_with`、検出に `merged_findings: [...]` を許容。category_summary は「findings の category 先頭文字を集計」と注記。
- 影響: 全 .md のスキーマ節。**次回適用の最有力候補**（hits≥2 到達済み・スキーマ追記のみで低リスク）。

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: done` `hits: 2run` 適用: 2026-06-29-001/002
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。
- 再現/実証(2026-06-29): 本 run で両レビュアーに `ai-tell-detector` サブエージェント再呼び出しを指示 → 客観再走査が機能（score_after の根拠が明確化）。
- 適用: `naturalness-reviewer.md §処理` に「検出器をサブエージェントとして実呼び出し（手動照合禁止）」を明文化。出所 naturalness-001, naturalness-002。

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **I-6 冗長敬語の積層（公的文書）[S2]** 「ご利用いただくことが可能となっております」「ご持参いただく必要がございます」型の可能＋状態＋形式名詞＋丁寧補助動詞の多層積み重ね。A-5/A-6/I-3 単独では捉えきれない複合形。taxonomy 拡張候補欄に v1.1 で記載済み（候補据え置き、hits≥2 で I-6 採番）。 `hits: 1run` 出所 detector-002。taxonomist が独立サブパターンとして妥当と承認。
- **技術解説ジャンル用 カタカナ語ホワイトリスト** embedding/vector/token/prompt/API/SDK 等は維持、leverage/retrieve/inject/knowledge base/solution 等は開く。B-2「例外」を別表化。 `hits: 1run` 出所 detector-001, rewriter-001。
- **ジャンル別 severity 可変** 公的文書の定型敬語（「につきましては」「お願い申し上げます」bookend）は density 閾値を緩め反復しても据え置き/減格。許容反復回数の数値定義が必要。 `hits: 1run` 出所 naturalness-002。
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 001。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019（並列→基盤の序列混入）はこの項が無く #5/#11 へ漏れ込んだ。`status: ready` `hits: 1` 出所 fidelity-A
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。`status: ready` `hits: 1` 出所 fidelity-B
- 「情報を含む削除 vs ボイラープレート削除」二分判定: 削除 span に (a)数値/固有名詞/日付 (b)条件/因果節 (c)固有の例示 を含めば情報欠落、挨拶/CTA/装飾/自己言及のみならボイラープレート。出所 fidelity-B
- #5論理関係 と #11情報追加 の責任境界を一意化（主因項目を 1 つに正規化）。出所 fidelity-A
- **modality 強度を順序尺度化（要請/推奨/義務/必須）** `status: ready` `hits: 2run`。2026-06-29 再現: fidelity-001（求められます→欠かせません、と言えるでしょう→です を within_tolerance 判定）、fidelity-002（必要がございます→お済ませください の義務度軟化）。pass/fail の二値では「許容域内だがゼロでない強度変化」を表現できず、`severity: clean|within_tolerance|breach` の3段階導入を両監査官が要求。**次回適用候補**。出所 fidelity-A, fidelity-001, fidelity-002
- **fidelity スキーマに `monitored_edits` を正式化** rewriter が申告した要監査 edit（f004 受動保持・f007 指示語化）を id 単位で受け取り結果を返す。`hits: 1run` 出所 fidelity-001, fidelity-002, rewriter-002
- **vacuous pass の `not_applicable` ステータス** 原文に数値/引用/出典が無い項を空通過と真の検証通過で区別。`hits: 1run` 出所 fidelity-001, fidelity-002

### playbook レシピ追補
- **C-5 絵文字削除後の文末/区切り吸収ルール**（句点で吸収 or 削除のどちらか明記）。出所 rewriter-B
- **D 系結びは削除一択でなく「最小着地文を残す」**（減らしすぎ下限）。実例: B の「気軽に始めてみてください」。出所 rewriter-B, naturalness-B
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**という例外則。出所 rewriter-A
- **原文が元から推量の D 系は推量を保持**（「断定へ」の一律処方の例外）。出所 rewriter-A

### naturalness 判定の精緻化
- 過推敲シグナルの定量化（敬体/常体混入は文末形態の二値カウントで機械検出）。出所 naturalness-A
- クラスタ系 finding（B-2 密集・C-1 列挙）はクラスタ崩壊時に個別 severity を降格するルール。出所 naturalness-A
- E-2 文末単調の到達可能ライン緩和（体言止め1箇所以上で合格、文体維持制約下の過推敲回避）。出所 naturalness-B
- 絶対残存数ガードを grade 表に組込み（改善率が高くても S1 が1件でも C 以下）。出所 naturalness-A, naturalness-B, naturalness-001（短文で改善率が過大評価される逆方向も指摘。A は raw≤5 等の上限併記を提案）
- **`out_of_scope_residual` フラグ** 元 finding に無く rewriter が span-grounded 原則で正当に放置した残存（例 run001 結語のカタカナ密集）を grade 計算から除外しつつ可視化。`hits: 1run` 出所 naturalness-001
- **過推敲シグナルの構造化** `{signal_type, severity, span, evidence}`＋敬体終止比率・体言止め比率・変更率の数値フィールド化で機械判定。`hits: 1run` 出所 naturalness-001, naturalness-002

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 1run(3agent)`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B, fidelity-A, naturalness-A

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。出所 detector-A。2026-06-29 再現: detector-001 が自己検証ループで 2 回オフセットを修正、detector-002 が同一表現多反復での誤マッチ余地を指摘。`hits: 2run`。
- **文字オフセット単位の明記** start/end が「Unicode コードポイント」か UTF-16/バイトか未定義 → 推敲役が別実装だと span がズレる。**2026-06-29 適用: taxonomy・detector に「コードポイント基準」と明記済み**。出所 detector-001
- 同一 text_span が複数出現する場合は occurrence index か文脈付き span を必須化（誤マッチ防止）。`hits: 1run` 出所 detector-001, detector-002
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B
