# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-06-21（run 001 技術解説/Kubernetes, 002 公的文書/オンライン申請）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done` `hits: 2run` `applied: 2026-06-21-001`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。Sample A も 47.6% と高止まり。
- 出所: rewriter-A, rewriter-B, naturalness-B / **再現 run 001: rewriter-001（change_rate 48.4% だが純縮小 16.9%）, naturalness-001（change_rate_verdict=正当な縮約）**
- 提案: (a) 「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を change_rate から控除。(c) 挿入率を単独併記し、del≫ins の削除主導ケースは中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`
- **適用（2026-06-21）**: playbook §変更率を二軸化（change_rate / net_shrink_rate / insert_ratio）。SKILL §総合判定に override accept 条項を明文化。naturalness-reviewer.md の過推敲判定を二軸へ。playbook を v1.1 に。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 3run` `applied: 2026-06-21-001/002`
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える（Sample A raw106→92.5、taxonomy 例は raw56→71.5 と不整合）。
- 出所: detector-A, detector-B / **再現 run 001: detector-001（728字で 85.9）, naturalness-001（係数を逆算する羽目に）/ run 002: detector-002（raw 29.5 で初回 100 飽和）**
- 提案: 飽和しにくい正規化を SSOT 明記（例 `100*(1-exp(-raw/k))` か「100字あたり加重和」）。分母（input_length 依存 or 固定 max）を確定。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出`
- **適用（2026-06-21）**: 正規化式を `100*(1-exp(-raw/40))` に固定し SSOT 明記。入力長非依存。`meta.raw_weighted_sum`/`meta.normalization` を追加。taxonomy/detector 双方を更新。taxonomy v1.1（taxonomist 承認済み）。

### IMP-003 score_before のフィールド契約が曖昧 `status: done` `hits: 2run` `applied: 2026-06-21-001`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score 92.5）。レビュアーごとに数値がぶれる。
- 出所: naturalness-A / **再現 run 001: naturalness-001（係数 1.236 を逆算）**
- 提案: 「score_before = 02_detection.json の meta.severity_weighted_score」と明文化。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`
- **適用（2026-06-21）**: IMP-002 と一括。taxonomy に「score_before = 02_detection.json の meta.severity_weighted_score、score_after は同一式で再計算」を明記。naturalness-reviewer.md の手順 2 を契約化。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: done` `hits: 3run` `applied: 2026-06-21-001/002`
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
- 出所: detector-B, detector-A / **再現 run 001: detector-001（E-1/E-2 を start=0/end=728 で表現）, rewriter-001（document_level edit 要望）/ run 002: detector-002（scope:document 要望）**
- 提案: `span_type: "contiguous"|"scattered"|"document"` と scattered 用 `occurrences: [[s,e],...]` を追加。density は重複・locator を除いた実 AI クセ文字数ベースと定義。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`
- **適用（2026-06-21）**: finding に `scope: "span"|"document"` を追加（taxonomy/detector/rewriter/diff を round-trip）。`scope:"document"` は推敲役の 0〜N 一括置換を禁止。density も locator 二重計上を禁止と注記。`occurrences` 配列（scattered 用）は次回以降の拡張として保留。

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 3run`
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。
- 出所: detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A / **再現 run 001: detector-001（overlaps/primary_category 要望）, rewriter-001（resolves:[...] 複数 finding 紐付け要望）/ run 002: rewriter-002（untouched_findings 要望）**
- 提案: 「1 span = 主分類 1 finding」を基本とし、`merged_findings: [...]` 配列を許容。category_summary は「findings の category 先頭文字を集計」と注記。diff に `resolves:[...]` と `untouched_findings[].reason` を追加。
- 影響: 全 .md のスキーマ節
- **次回適用候補**（3run・ready。今回は IMP-001/002/004 を優先したため見送り）

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: done` `hits: 2run` `applied: 2026-06-21-001`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。
- 出所: naturalness-A / **本 run では両 reviewer が実際に detector を再走査して解消の方向（naturalness-001/002 とも再実行を実施）**
- 提案: `ai-tell-detector` をサブエージェントとして再呼び出しする経路を必須化（手動照合禁止）。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`
- **適用（2026-06-21）**: naturalness-reviewer.md 手順 1 に「手動照合のみで済ませない（IMP-006）」を明記。スコアは固定式の再計算に統一（IMP-002 連動）。

---

## P2 — 分類・レシピ・チェックリスト

### 2026-06-21 新規候補（run 001 技術解説 / 002 公的文書 由来）
- **A-5 二重可能形のサブ化（A-5a/A-5b）** 「することができるようになります」= can + become able to の二重直訳は単純 A-5 より露見度が一段高い。実例 f008/f018（run 001）。`hits: 1run(2agent: detector-001, rewriter-001)` 昇格条件は**独立 run での A-5b 再現**（現 2 例は同一 run 由来）。taxonomist が拡張候補欄 C-001 に記録済み。
- **公的文書の依頼定型「ご〜いただく必要がございます」** 二重敬語＋形式名詞の依頼で「〜ください」一語で足りる。実例 4 件（ご提出/ご了承/ご承知おき/利用者登録、run 002）。`hits: 1run(detector-002)` 人間（公的文書）も使うため単独 S1 不可。K カテゴリ案に吸収候補。taxonomist が C-002 に記録済み。
- **過剰敬語カテゴリ K 新設候補** K-1 二重敬語 / K-2「させていただく」濫用 / K-3 三重丁寧依頼。CLAUDE.md の「させていただく過剰」と整合。実例: 「賜りますよう」「頂戴する」「所存でございます」（run 002）。`hits: 1run(detector-002, naturalness-002)` 分類体系改訂のため **v1.2 マイルストーン**。E-2/I-4 との責務境界明文化が昇格条件。taxonomist が C-003 に記録済み。
- **B-2 カタカナ語の件数閾値（N 語以上で S2）** taxonomy は「多用」とだけで S2/S3 切り分けが検出器裁量。集約ルールが grade を左右する（run 001: 3語集約で S2=1→A、1語=1件なら S2=3→B）。`hits: 1run(3agent: detector-001, rewriter-001, naturalness-001)` `status: ready`（次回適用候補）。
- **ジャンル別「概念語の平易化禁止リスト」+ 入力 genre フィールド** 技術解説で概念語の和語化は原則毀損。実例 f013「再スケジュール→組み直す」が rescheduling の厳密性を毀損し round2 ロールバック（run 001）。`hits: 1run(2agent: fidelity-001, rewriter-001)` fidelity スキーマに `genre` 入力＋ジャンル別ホワイトリスト提案。
- **fidelity チェックの 3 値化（pass/watch/fail）** 「同一カテゴリ内の近接語で語義ベクトルがずれる」（seamless→一元的）を二値で裁けない。実例 f003（run 001、毀損未満だが無害でもない）。`hits: 1run(fidelity-001)`。
- **diff スキーマに `self_flagged_risks` / `untouched_findings[].reason` を正式採用** 推敲役の自己申告リスク（f013 はロールバック候補と warnings に明記）と「意図的非対応」を監査が機械的に拾えるよう標準化。`hits: 1run(2agent: rewriter-002, fidelity-001)`。
- **公的文書の定型結句を Do-NOT ホワイトリスト化** 「運びとなりました」「お願い申し上げます」「賜りますよう」「所存でございます」を A-6/E-2 の過検出から除外。run 002 では検出器が正しく S3 降格したが判断が走査者依存。`hits: 1run(2agent: rewriter-002, naturalness-002)`。
- **依頼形の敬意グラデーション表（playbook I-3/I-4）** 「お願いします（柔）／ご〜ください（標準）／〜いただきますようお願い申し上げます（丁重）」を負担度で使い分け、4 連反復の分散時に機械化を回避。`hits: 1run(rewriter-002)`。
- **A-10 と D-5 の動詞リストでの線引き** 「もたらす/示す/提供する」=A-10、「問いを投げかける/終わらない」等の人間的動詞=D-5。実例 f011（run 001、両該当しうる）。`hits: 1run(detector-001)`。
- **位置重み（冒頭/結びの finding は severity 半段引上げ）** 冒頭 1 文目の D-4「欠かせない」が S3 のため grade に響かず放置。AI 印象への寄与は大きい。`hits: 1run(naturalness-001)`。
- **「〜していきます」緩衝的進行形** 「解説します」で足りるのに going to 的に「ていく」。実例「解説していきます」（run 001）。`hits: 1run(detector-001)` 要再現確認。
- **F-1 副詞削除の公的文書例外（信頼性機能語の保持）** 「厳重に管理」「適切に処理」は安心情報を担う機能語で機械削除は減情報。`hits: 1run(2agent: rewriter-002, fidelity-002)`。

### 新パターン候補（taxonomist 審査待ち）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 001。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B

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
