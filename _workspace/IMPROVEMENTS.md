# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-08-06（run 001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結び・過剰敬語末尾の純削除で機械的に膨張。2026-06-12 Sample B は 54.6% で `hold_and_report` 誤発火。2026-08-06 run 002（公的文書）も **0.37** で警告誤発火（「いただきますようお願い申し上げます」13字→「ください」4字 等の純削除主導、実際は fidelity=pass / 自然度 A）→ override accept で救済。
- 出所: rewriter-A, rewriter-B, naturalness-B（06-12）／ rewriter-002, naturalness-002（08-06）
- 提案: (a) 「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句・過剰敬語末尾・受動助動詞の純削除分を重み 0.5 で控除。(c) 挿入率を単独併記し、del≫ins の削除主導ケースは中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。(e) 警告文に削除内訳を必ず添える。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: ready` `hits: 2run(適用: 2026-08-06)` → **APPLIED**
- 症状: 正規化式が SSOT に無く、分母（input_length 依存 or 固定 max）が未定義。高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える。08-06 で決定的に再現: run 001 raw86.5→95.5、run 002 raw41.5→53.2（係数1.282を逆算）、taxonomy 例 raw?→71.5 と 3 者すべて不整合。同じ finding 数でも文長で score が倍変動し、文書間比較・等級判定（A〜D）が長さ依存でブレる。
- 出所: detector-A, detector-B（06-12）／ detector-001, detector-002, naturalness-001, naturalness-002（08-06・4agent 横断）
- 提案: 正規化式を文字列で SSOT 明記。採用: `score = min(100, raw_weighted / input_length * 1000)`（per-1000字加重）を正準とし K=1000・キャップ100を固定。score_after も同一 input_length で正規化。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出`
- **適用 2026-08-06（run 001,002）**: taxonomy スキーマ節と detector.md に式を明記。

### IMP-003 score_before/after のフィールド契約が曖昧 `status: ready` `hits: 2run(適用: 2026-08-06)` → **APPLIED**
- 症状: naturalness-reviewer がどの値を score_before にするか、score_after をどの分母で正規化するか未固定。08-06 で naturalness-001/002 が「score_after の分母（推敲文実長か原文長か）未規定」を追加報告。
- 出所: naturalness-A（06-12）／ naturalness-001, naturalness-002（08-06）
- 提案: 「score_before = 02_detection.json の meta.severity_weighted_score」「score_after は **同一 input_length** で正規化（IMP-002 の式）」と明文化。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`
- **適用 2026-08-06**: IMP-002 の式明記と併せて score_after 分母を固定。

### IMP-007 検出器の char offset が本文実位置とズレる（原文破壊リスク）`status: ready` `hits: 1run(3agent)`
- 症状: 08-06 run 001 で `meta.input_length=906` だが本文実長 871（差35）。全 finding の start/end が実位置とズレ、char-offset ベースの機械照合が原理的に不可能。reason 内の派生位置も全滅。rewriter・fidelity・naturalness の 3 者が独立に検知し、いずれも **text_span 文字列を正アンカー**として回避した。offset を信じて手術すると原文破壊に直結する重大欠陥。
- 出所: rewriter-001, fidelity-001, naturalness-001（08-06・同一 run 3agent 一致）
- 提案: (a) `text_span` を唯一の正規アンカー、offset は補助情報に降格と SSOT 明記。(b) `length_unit`（Unicode コードポイント基準）フィールド必須化＋正規化仕様（改行・タイトル行を数えるか）明記。(c) 検出器がパイプライン先頭で `assert source[start:end]==text_span` と `len(body)==input_length` を全 span 突合するバリデーションゲートを必須化。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §自己検証`, `content-fidelity-auditor.md`（照合は text_span 基準）
- 注: 別 run 再現待ちだが 3agent 一致・修正明快・被害甚大のため schema 文書化を IMP-004/005 の schema 改訂と同時に前倒し適用。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run(適用: 2026-08-06)` → **APPLIED**
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン（06-12）。08-06 でも A-10 抽象主語＋万能動詞は主語と述語が離れ（run 001 f016 で約40字離隔）、単一 start/end では表現不能。E-1 文長均一・E-2 文末単調・H-1 接続詞過多は連続 span を持たない文書レベル現象で、検出器ごとに表現がバラつく（0,0 か全域か）。
- 出所: detector-B, detector-A（06-12）／ detector-001, detector-002, rewriter-001, fidelity-001（08-06）
- 提案: `scope: "span"|"scattered"|"document"` と scattered/document 用 `occurrences: [[s,e],...]` を追加。density は document スコープと重複領域を de-dup した実 AI クセ文字数ベースと定義。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`
- **適用 2026-08-06**: スキーマに `scope`・`occurrences` を追加、density の de-dup 規約を明記。

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run(適用: 2026-08-06)` → **APPLIED**
- 症状: 1 span が複数カテゴリに該当（06-12）。08-06 でも「変更されることとなりました」= A-8+A-6 複合、「実現することができるでしょう」= A-5+G-1 複合が頻出。edits/findings が 1:1 前提のため category_summary が実態とズレ、片方だけロールバックすると文が壊れる（rewriter-002 報告）。集約 vs 個別の基準不在で detected_count・density・score が検出器裁量で変動（受動態を集約すれば 17→10、個別化で 17→24）。
- 出所: detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A（06-12）／ detector-001, detector-002, rewriter-002, fidelity-001（08-06）
- 提案: 「一意な span 文字列 = 主分類 1 finding、reason に回数」を原則化。`co_located_with`/`merged_findings` を許容し、ロールバック単位を finding でなく**セグメント**（連続書き換え領域）とする。category_summary は「findings の category 先頭文字を集計」と注記。
- 影響: 全 .md のスキーマ節, `japanese-style-rewriter.md §ロールバック`
- **適用 2026-08-06**: スキーマに `co_located_with` を追加、集約原則とセグメント単位ロールバックを明記。

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。08-06 も naturalness-001/002 が手動照合（基準明示のうえ）で再現。再現性が属人的。
- 出所: naturalness-A（06-12）／ naturalness-001, naturalness-002（08-06）
- 提案: `ai-tell-detector` をサブエージェントとして再呼び出しする経路（再走査モード）を必須化。難しければ最低限「measurement_basis を JSON に明示」を規約化。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **K 系: 過剰敬語・二重敬語・定型末尾の過剰反復** ★日本語固有 `hits: 1run(4agent)` `status: ready(昇格・2026-08-06 taxonomist審査へ)`
  - 設計思想（taxonomy L5）は「日本語 AIクセ = 翻訳調 + **過剰な丁寧体・敬語** + カタカナ語 + 状態叙述」の 4 本柱を掲げるのに、A〜J のどのサブパターンにも過剰敬語が無い（設計と実装の乖離）。公的文書ジャンルの最頻出クセがここ。暫定で D-1 にマップせざるを得なかった。
  - **提案 K-1「定型末尾の過剰反復」[S2]**: 「お願い申し上げます」「賜りますよう」「御礼申し上げます」の結び反復。実例（run 002）: 申し上げます系 5 回＋賜り 2 回。処方: 開始の御礼・結びの依頼を各 1 回に集約、途中は「ください／お願いします」へ格下げ。
  - **提案 K-2「行為者を隠す授受＋敬語の連結」[S2]**: 「〜していただく必要がございます」（依頼＋授受＋丁重語＋必要）の全依頼への機械適用。実例（run 002）3 回。
  - 出所: detector-002, rewriter-002, naturalness-002, fidelity-002（4agent 一致）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。実例: 001（06-12）。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B
- **A-1/A-2 の敬語変種** 「につきまして(は/も)」「におきまして」「におかれまして」が公的文書で頻出（run 002 で につきまして 5 回）。素朴な正規表現が取りこぼす。→ A-1/A-2 のシグネチャ例に敬語変種を追記。 `hits: 1run(2agent)` 出所 detector-002, （fidelity-002 は about系削除の代替受け検証を提起）
- **可能形ドリフト（potentiality drift）** 「行われない（不作為）」↔「収集できない（不能）」の相互変換は fidelity check 4（極性）でも 7（modality）でも捕捉されないグレー領域。公的文書で法的含意（policy か ability か）が変わりうる。実例 run 002 f007。→ fidelity check 7 に可能・不可能表現の付加/除去サブチェック追加。 `hits: 1` 出所 fidelity-002

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019（並列→基盤の序列混入）はこの項が無く #5/#11 へ漏れ込んだ。`status: ready` `hits: 1` 出所 fidelity-A
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。`status: ready` `hits: 1` 出所 fidelity-B
- 「情報を含む削除 vs ボイラープレート削除」二分判定: 削除 span に (a)数値/固有名詞/日付 (b)条件/因果節 (c)固有の例示 を含めば情報欠落、挨拶/CTA/装飾/自己言及のみならボイラープレート。出所 fidelity-B
- #5論理関係 と #11情報追加 の責任境界を一意化（主因項目を 1 つに正規化）。出所 fidelity-A
- modality 強度を順序尺度化（要請/推奨/義務/必須）。出所 fidelity-A
- **#確定性の相** 「変更されることとなりました（決定既遂）」→「変更します（意志予告）」の確定モダリティ減衰を check 8 時制軸が捕捉できない。公的文書で法的重みが変わる。`hits: 1` 出所 fidelity-002
- **#敬語方向転換による行為者反転** check 9 は「受動→能動」限定で、謙譲/尊敬の切替で行為者の上下（誰が誰に）が反転するケースを明示カバーしない（例 ご参照いただく＝住民主体 vs ご参照する＝市主体）。→ check 9 を「態・敬語変換における行為者・受益者の整合」へ拡張。`hits: 1` 出所 fidelity-002
- **#文分割時の係り受け保存** 長文を 2 文に分割した際、分割点で主節-従属節の係り受け（理由と結論の因果等）が切れるリスク。check 5 下位に追加。`hits: 1` 出所 fidelity-002
- **#変更会計の整合（14項）** Σchange_chars と実 diff 文字数の一致・edit 範囲の非重複を検証する項が無い。change_rate 30%閾値直下（0.287）の信頼性が担保できない。`hits: 1` 出所 fidelity-001
- **#span逸脱チェック** 改変箇所が finding span ∪ 明示 suggested_fix 範囲に収まるか（span-grounded 違反そのものを検出）。意味等価でも逸脱は warning。実例 run 001 f005「外部から→外部に」隣接語改変。`hits: 1` 出所 fidelity-001
- **checks[].status / verdict の enum 未定義** `status ∈ {pass,fail,warn}`・`verdict ∈ {pass,rollback_required}`・`checks[].linked_findings` を JSON Schema で固定。`hits: 1` 出所 fidelity-001

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
- **改善率の飽和で等級 A 条件「改善70%+」が形骸化** score が min(100) で上限張り付き、S1 を数件残しても改善率は容易に 70% 超（例 S1×2 残存でも 85%）。実質 `S1=0 かつ S2≤2` だけが効く。改善率は raw 加重和（キャップ前生値）で算出すべき。`hits: 1run(2agent)` 出所 naturalness-001, naturalness-002
- **過推敲シグナルの「2個」カウント単位が未定義** 二値カテゴリ点灯数か実インスタンス数か不明。「体言止め＝常体混入」と誤カウントすると E-2 処方通りの推敲が減点される矛盾。→ シグナル＝カテゴリ二値点灯数と明記、体言止めは敬体で非点灯（N箇所超で別シグナル）。`hits: 1run(2agent)` 出所 naturalness-001, naturalness-002
- **置換由来の新規反復（二次的単調）が捕捉されない** 勧告化（必要がございます→ください）が「ください×7」の新反復を生む副作用が過推敲シグナル4項目のどれにも該当しない。E-2 は推敲前の単調を測る設計。→ 「置換由来の新規文末/接続反復」を1項目追加。実例 run 002。`hits: 1` 出所 naturalness-002
- **等級表の件/回の混線** S2 定義は「1〜2回許容、3回+で除去」だが等級表は「S2≤2件」。件（finding）と回（occurrence）が混線し閾値ゲート後の finding 数で数えるか未定。`hits: 1` 出所 naturalness-002
- **structurally_unresolvable フィールド** E-1（文長均一）は「情報付加禁止」鉄則と衝突し原理的に完全解消不能。residual と別枠で summary に明示。`hits: 1run(2agent)` 出所 naturalness-001, rewriter-001
- **change_rate override 判定はオーケストレーター層に一元化** naturalness-reviewer は並列の fidelity 結果を前提にできない（タイミング次第で 04 未生成）。reviewer は grade と residual のみ返す責務分離が安全。`hits: 1` 出所 naturalness-002

### カタカナ語 B-2 の allowlist/blocklist 外部ファイル化 `status: ready` `hits: 2run(3agent)`
- 症状: B-2 の「業界標準語は維持」が例示のみで判定が属人的。run 001 で 42 カタカナ語中「リアルタイム」「ツール」が境界例となり density が判定次第で大きく動く。既存の「定着カタカナ語 B-2 免責リスト」（06-12）と同根。
- 提案: `references/katakana-allowlist.md`（維持語: メトリクス/ログ/トレース/API/SDK/トークン等）と `katakana-blocklist.md`（変換推奨: レバレッジ→活用, インサイト→示唆, アジェンダ→課題等）を別ファイル化し playbook B-2 対応表と統合。
- 出所: naturalness-B, fidelity-A, naturalness-A（06-12）／ detector-001（08-06）

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 1run(3agent)`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B, fidelity-A, naturalness-A

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。出所 detector-A
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B
