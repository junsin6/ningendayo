# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-07-14（run 001, 002）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。Sample A も 47.6% と高止まり。
- 出所: rewriter-A, rewriter-B, naturalness-B（2026-06-12）／ rewriter-001, rewriter-002（2026-07-14 再現。両者が lexical/structural を独自に分離計上して meta に記録）
- 追補（2026-07-14, rewriter-001）: **分子の数え方が短縮リライトを過大評価**。`ブーストできる(7)→高められる(5)` は意味等価なのに del7+ins5=12 と計上。分子を `max(del,ins)` か Levenshtein に統一すれば短縮ペナルティを回避（今回 max 基準なら 128/729=0.176 と実態に近い）。分母は「改行除去後の本文字数」に固定すべき。
- 提案: (a) 「語句改変率」と「構造/削除率」を分離計上（rewriter は既に meta で実践）。(b) 装飾・常套句の純削除分を change_rate から控除。(c) 挿入率を単独併記し、del≫ins の削除主導ケースは中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。(e) 分子=max(del,ins)、分母=本文字数(改行除く)。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`
- 次回適用最有力（hits:2, ready）。今回は 3 スコア系（IMP-002/003/006）を優先適用したため見送り。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2run` `applied: 2026-07-14-001/002`
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える（Sample A raw106→92.5、taxonomy 例は raw56→71.5 と不整合）。
- **2026-07-14 の決定的再現**: 同 run の2検出器が**別々の式**を採用 — detector-001 は raw クリップで **81.0**、detector-002 は `raw/L×1000` で **44.9**。同程度密度でスコアが非比較になる欠陥を実証。
- 出所: detector-A, detector-B（2026-06-12）／ detector-001, detector-002, naturalness-001, naturalness-002（2026-07-14）
- **適用（2026-07-14）**: taxonomy §検出出力スキーマに式を確定 `severity_weighted_score = min(100, round((5·S1+2·S2+0.5·S3)/L×1000,1))`、L=本文字数(改行除く)。worked example を self-consistent 化（45.6）。`ai-tell-detector.md §スコア算出`・`naturalness-reviewer.md` も同式へ統一。飽和緩和（`100·(1-exp(-dw/K))`）は follow-up として保留。taxonomy v1.1。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出`, `naturalness-reviewer.md`

### IMP-003 score_before のフィールド契約が曖昧 `status: done` `hits: 2run` `applied: 2026-07-14-001/002`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score 92.5）。レビュアーごとに数値がぶれる。
- 出所: naturalness-A（2026-06-12）／ naturalness-001, naturalness-002（2026-07-14, 両者とも meta.severity_weighted_score を score_before に採用して再現）
- **適用（2026-07-14）**: `naturalness-reviewer.md §処理` に「score_before = 02_detection.json の meta.severity_weighted_score をそのまま使う（独自再計算禁止）」を明文化。`meta.severity_counts` を新設しスコア再現を担保（taxonomy §スキーマ）。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run`
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
- 出所: detector-B, detector-A（2026-06-12）／ detector-001（E-2 を代表 span に anchor）, detector-002（E-1/E-2/H-1 を点 span に押し込み density 過大化）（2026-07-14 再現）
- 提案: `span_type: "contiguous"|"scattered"|"document"`（または `scope`）と scattered 用 `occurrences: [[s,e],...]` を追加。document 型は span 任意化し density 計算から除外。density は重複・locator を除いた実 AI クセ文字数（union）ベースと定義。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`
- 次点適用候補（hits:2, ready）。IMP-001 と合わせ次回検討。

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。
- 出所: detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A（2026-06-12）／ detector-001（A-5＋A-10 重複を also[] 提案）, fidelity-001（1 span 複数該当）（2026-07-14 再現）
- 提案: 「1 span = 主分類（最上位 severity）1 finding」を基本とし、副次カテゴリは `also: [...]` に記録。category_summary は「findings の主 category 先頭文字を集計」と注記。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: done` `hits: 2run` `applied: 2026-07-14-001/002`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。
- 出所: naturalness-A（2026-06-12）／ naturalness-001, naturalness-002（2026-07-14: 両者とも実際に ai-tell-detector をサブエージェント起動して再走査。経路が機能することを実証）
- **適用（2026-07-14）**: `naturalness-reviewer.md §処理` の手順1を「Agent ツールで ai-tell-detector を実起動する必須手順・手動照合禁止」と明文化。
- 影響: `naturalness-reviewer.md §処理`

### IMP-007 verdict 語彙が3系統に分裂 `status: ready` `hits: 1run(2agent)`
- 症状: content-fidelity-auditor 定義は `pass | rollback_required`、SKILL.md/CLAUDE.md パイプラインは `rollback_and_rewrite`、rewriter diff は `accept` を使用。オーケストレーターが verdict 文字列を機械照合すると取りこぼす。今回は毀損ゼロで実害なし。
- 出所: fidelity-001, fidelity-002（2026-07-14, 両者が独立指摘）
- 提案: 監査官 verdict を `pass | rollback_and_rewrite` に統一（SKILL.md 総合判定の語彙に合わせる）。checks[].status に `not_applicable`・`pass_with_note`（borderline 記録用）を追加。
- 影響: `content-fidelity-auditor.md §出力スキーマ`, `SKILL.md`
- 小さく安全な適用候補。次回 hits:2 到達で即適用可（実害が出る前の予防）。

### IMP-008 fidelity #7 modality に「義務→依頼」変換の操作的合否基準がない `status: ready` `hits: 1run(2agent)`
- 症状: #7 は「ヘッジ除去が過剰でないか」しか例示せず、公的文書頻出の「必要がございます→ください」型の義務→依頼変換の合否基準が無い。監査官の裁量依存。
- 出所: fidelity-001（#7 と Fidelity First 原則の構造的衝突: de-hedge は常に modality を変える）, fidelity-002（義務→依頼／受動の能動化の判定軸）（2026-07-14）
- 提案: #7 に操作的定義を追加 —「命題の真理条件が変わらなければ pass、over-claim（原文になかった確実性・義務・範囲の付与）／義務→任意への格下げのみ fail」。#9 に「行為者を伏せた受動の能動化は含意の限定に注意」サブ基準。modality 強度を順序尺度化（任意/推奨/要請/義務/必須）。
- 影響: `content-fidelity-auditor.md §13項チェックリスト`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 001。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B
- **K 過剰敬語/誤変換敬語**（公的文書）「お知らせされます」（謙譲を尊敬様受動に誤変換）「ご案内させていただく予定でございます」（過剰敬語連鎖）。→ **taxonomy 拡張候補欄に登録済み（2026-07-14, 未昇格）**。別 run 再現で v1.1 K カテゴリ昇格を審査。 `hits: 1run(2agent)` 出所 detector-002, rewriter-002
- **C-6 記事メタアナウンス** 「本記事では〜わかりやすく解説していきます」ブログ/技術記事の冒頭自己言及公式。 `hits: 1` 出所 naturalness-001（再走査 residual）

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
- **公的文書/敬体レジスタ別の変換段を新設**（常体／丁寧敬体／公文書敬語）。A-8 受動の能動化は敬体では「停止いたします」と謙譲形に、I-3「必要がある」は公文書では「すべきだ」でなく「ご了承ください／お願いいたします」へ。 `hits: 1run` 出所 rewriter-002
- **E-1 文長均一は単独編集禁止**（短文挿入は新規情報＝fidelity 違反を誘発）。既存文の分割・複文の単文化でのみ達成し情報を足さない。 出所 rewriter-002
- **反復系 finding の非対称変換セット**（同カテゴリ近接時の打ち分け）。A-5×6 は 断定/可能/連用中止/連体 の4形へ、I-3×3+I-4 は ください/お願いいたします/していただきます へ分散。全て同一変換にすると新たな単調反復を生む。 `hits: 1run(2agent)` 出所 rewriter-001, rewriter-002
- **A-5 反復分散テンプレート**を playbook A-5 欄に明記（できる/する の二択でなく 連用中止「〜でき、」・連体「〜できる＋名詞」・体言止め も分散カードに）。 出所 rewriter-001
- **suggested_fix の binding**（strict/advisory）を明記。反復回避で suggested_fix と衝突する場合は finding.reason の核心を満たせば代替可。 出所 rewriter-001

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
