# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-09-17（run 2026-09-17-001 技術記事, -002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2runs`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結び・冗長敬語/状態叙述の純削除で機械的に膨張。Sample B(6/12) は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。Sample A も 47.6% と高止まり。
- **9/17 再現**: run 001 change_rate 27.3%（del153≫ins44、挿入率6%）、run 002 27.9%（del135≫ins37）。両 run とも削除主導で 30% 閾値に近接。公的文書は冗長敬語/無主語受動/状態叙述の純削除が正解のため del が構造的に大きく、健全な推敲ほど閾値に迫る（rewriter-B, fidelity-B, naturalness-B が指摘）。round2 で f009 を正しく戻したら change_rate はむしろ低下（0.2788→0.269）し、「短い＝良い」という変更率的直感と毀損の関係が逆転する好例も観測（rewriter round2）。
- 出所: rewriter-A/B, fidelity-A/B, naturalness-A/B（6/12 + 9/17、6エージェント横断）
- 提案: (a) 「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を change_rate から控除。(c) 挿入率を単独併記し、del≫ins の削除主導ケースは中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。(e) ジャンル別に削除許容枠を可変化（公的文書は上げる）。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`
- 次サイクル適用候補（P0・ready）。今サイクルは IMP-002/003 とチェックリスト#14 を優先適用。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2runs` `applied: 2026-09-17-001/002`
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える（Sample A raw106→92.5、taxonomy 例は raw56→71.5 と不整合）。
- **9/17 再現（決定的）**: detector-A は k=70（run001 raw81→68.6）、detector-B は k=41（run002 raw34.5→56.9）と**係数が run 間で割れた**。同一入力でも detector ごとにスコアが非可比になる欠陥が実証された。
- 出所: detector-A/B, naturalness-A/B（4エージェント）
- **適用（2026-09-17）**: 式を確定明記。`raw=Σ(S1×5+S2×2+S3×0.5)`、`severity_weighted_score = round(100*(1-exp(-raw/41)),1)`（k=41 固定・input_length 非依存。基準 run 2026-06-12-001 の raw106→92.5 を再現する逆算値）。05 再計測も同式・同 k。編集: `ai-tell-detector.md §スコア算出`・`naturalness-reviewer.md §処理`・`ai-tell-taxonomy.md §検出出力スキーマ`（taxonomist が v1.1 で反映）。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出`, `naturalness-reviewer.md`

### IMP-003 score_before のフィールド契約が曖昧 `status: done` `hits: 2runs` `applied: 2026-09-17`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score 92.5）。レビュアーごとに数値がぶれる。
- **9/17 再現**: naturalness-A/B とも「SSOT 未明記で各レビュアー依存」と再指摘（今回は指示で 68.6/56.9 に固定して回避）。
- 出所: naturalness-A/B
- **適用（2026-09-17）**: 「`score_before` = 対象 run の `02_detection.json` の `meta.severity_weighted_score` をそのまま用いる」を `naturalness-reviewer.md §処理` に明文化。あわせて `score_after` は detector と同一正規化式で算出する契約も明記（IMP-002 連動）。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2runs`
> 9/17 再現: E-2 文末単調・A-5×5・B-2 分散・C-1/C-7 段落冒頭公式（run001）、E-2/定型敬語反復（run002）が単一 start/end に収まらず代表 anchor で回避。density は union 文字数で算出して過大化を回避。次サイクル適用候補。
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
- 出所: detector-B, detector-A
- 提案: `span_type: "contiguous"|"scattered"|"document"` と scattered 用 `occurrences: [[s,e],...]` を追加。density は重複・locator を除いた実 AI クセ文字数ベースと定義。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2runs`
> 9/17 再現: run001「メリットを持つ」=A-7+B-2、「というアプローチ」=A-13+B-2 等、run002「されることとなっております」=A-6+A-8+I-1。`merged_findings[]` 導入が両 run で必要。次サイクル適用候補。
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。
- 出所: detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A（横断的に最多）
- 提案: 「1 span = 主分類 1 finding」を基本とし、`merged_findings: [...]` 配列を許容。category_summary は「findings の category 先頭文字を集計」と注記。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 2runs`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。
- **9/17 再現**: naturalness-A/B とも検出ロジックを inline 再適用して回避したが、`ai-tell-detector` を別プロセス起動する経路は未整備と再指摘。
- 出所: naturalness-A/B
- **一部適用（2026-09-17）**: `naturalness-reviewer.md §処理` に「推定値で済ませない／サブエージェント経路が無い場合も体系的再走査を明記」を追記。完全適用（オーケストレーターが detector サブエージェントを必須起動）は SKILL.md 側の対応が残るため `ready` 維持。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 001。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。 `status: done` `hits: 2runs` — **v1.1 昇格・適用（2026-09-17、taxonomist）**。実例: 2026-06-12-002（SEO ブログ）＋2026-09-17-001「導入を検討してみてはいかがでしょうか」（技術記事）で異 run 2回再現。
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B
- **E-4 定型敬語・挨拶句の機械反復**（★日本語固有・公的文書ジャンル）「申し上げます」「賜り」「何卒」「ございます」の過剰反復。E-2（です/ます単調）とは別で語彙的反復。処方に「初出保存＋反復分の変奏（残存下限）」が要る。 `hits: 1` 実例 2026-09-17-002 出所 detector-B, rewriter-B, naturalness-B → 拡張候補欄へ登録（taxonomist）。
- **A-8 の一般化候補** 現 A-8 は「〜によって by-passive」限定だが公的文書は「実施される/配布される/図られる」等の**行為者不在の無主語受動**が主。A-8a(by-passive)/A-8b(無主語受動) 二分を検討。 `hits: 1` 実例 2026-09-17-002 出所 detector-B, rewriter-B。

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019（並列→基盤の序列混入, 6/12）はこの項が無く #5/#11 へ漏れ込んだ。`status: done` `hits: 2runs` `applied: 2026-09-17` — **9/17 再現**（run001 f023「重要な技術。それがコンテナ技術です」が同型監査対象、結果は pass だが #14 があれば単一項で一貫評価できた）。`content-fidelity-auditor.md` に第14項を追加し、cleft/体言止めによる唯一的同定の強調も本項で監査する旨を明記。出所 fidelity-A（6/12+9/17）
- **modality 強度の順序尺度化** `status: done` `hits: 2runs` `applied: 2026-09-17` — 6/12 は義務軸のみ提案だったが、9/17 run002 f009（「混雑することが予想されます」→「混雑します」）で**認識軸（epistemic）**の毀損が発生。#7 を「義務軸〔要請＜推奨＜義務＜必須〕＋認識軸〔可能性＜推量/見込み＜蓋然＜断定〕」の2軸に拡張し、**統制外事象の予測を断定化しないルール**を `content-fidelity-auditor.md #7` に明記。出所 fidelity-A/B
- **G-1-EX1 統制可能性ゲート（新・playbook 候補）** G-1 ヘッジ除去の前に事象の統制可能性を判定。統制外事象（交通・気象・第三者行動・物理現象・市場）の予測は断定化せず予測標識（見込み/予想/と見られる）を残す。統制内事象（自組織の決定・実施）のみ平叙断定を許可。`status: ready` `hits: 1` 実例 2026-09-17-002 f009（2ラウンドを要した根本原因）出所 rewriter round2, fidelity-B, re-audit。
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。`status: ready` `hits: 2runs`（9/17 run002 で「情報を含む削除 vs ボイラープレート削除」判定が有効に機能）出所 fidelity-B
- 「情報を含む削除 vs ボイラープレート削除」二分判定: 削除 span に (a)数値/固有名詞/日付 (b)条件/因果節 (c)固有の例示 を含めば情報欠落、挨拶/CTA/装飾/自己言及のみならボイラープレート。`hits: 2runs` 出所 fidelity-B
- #5論理関係 と #11情報追加 の責任境界を一意化（主因項目を 1 つに正規化）→ #14 新設で一元化（9/17 適用）。出所 fidelity-A

### playbook レシピ追補
- **C-5 絵文字削除後の文末/区切り吸収ルール**（句点で吸収 or 削除のどちらか明記）。出所 rewriter-B
- **敬語残存下限（K系候補・D 系「最小着地文を残す」の敬体一般化）** `status: ready` `hits: 2runs` — 6/12 は D 系結び「気軽に始めてみてください」。9/17 run002 で公的文書の敬語（「賜り」「ございます」「何卒よろしくお願い申し上げます」）へ一般化して再現。**同一敬語表現は文書内で最低1つ保持し反復分のみ変奏・軽量化**、冒頭挨拶初出・結句は保存必須。処方リストを playbook に SSOT 化すべき。出所 rewriter-B, naturalness-B, fidelity-B。次サイクル適用候補。
- **機能が必要な接続詞は削除でなく変奏** `status: ready` `hits: 2runs` — 6/12「しかしながら」、9/17 run001 f024「一方で」で再現。出所 rewriter-A（両 run）
- **原文が元から推量／予測の D・G 系は推量を保持**（「断定へ」の一律処方の例外。G-1-EX1 と連動）`hits: 2runs`。出所 rewriter-A, rewriter round2
- **A-8 無主語受動の能動化に伴う格助詞整合ルール** 「工事が実施される→工事を実施する」等で格助詞（が→を）が finding span 外に及ぶ。自動詞化／省略主語で「市」を前面化しない例を明記すべき。`hits: 1` 実例 2026-09-17-002 出所 rewriter-B。
- **D-2 ハイプ語の言い換えは同一意味圏内に限る** 「注目を集める→広がる」は注目(attention)→普及(adoption)の含意ずれで意味不変則違反。第一選択は削除・受動化（注目されています）、別語言い換えは含意一致時のみ。`hits: 1` 実例 2026-09-17-001 f018 出所 rewriter-A。

### naturalness 判定の精緻化
- 過推敲シグナルの定量化（敬体/常体混入は文末形態の二値カウントで機械検出）。出所 naturalness-A
- クラスタ系 finding（B-2 密集・C-1 列挙）はクラスタ崩壊時に個別 severity を降格するルール。出所 naturalness-A
- E-2 文末単調の到達可能ライン緩和（体言止め1箇所以上で合格、文体維持制約下の過推敲回避）。出所 naturalness-B
- 絶対残存数ガードを grade 表に組込み（改善率が高くても S1 が1件でも C 以下）。出所 naturalness-A, naturalness-B

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 1run(3agent)`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B, fidelity-A, naturalness-A

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。`status: done`（9/17 両 detector・両 fidelity が全 span を `text[start:end]==text_span` で assert 実施）出所 detector-A/B。
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B
- **単発 S1 の扱い規約が無い（新）** A-1「における」等は密度依存で S1↔S3 が動く。「深刻度は出現密度で動的決定・単発は過検出しない」を `ai-tell-detector.md` に明文化すべき（run002 で detector-B が I-4 severity を SSOT=S2 と参照 run=S1 の不一致で判断に迷った）。`hits: 1` 出所 detector-B。

### 新規（9/17 起票）

### IMP-007 品質等級の改善率が飽和スコアと非整合 `status: ready` `hits: 1`
- 症状: IMP-002 で score を指数飽和関数に確定したが、CLAUDE.md/SKILL.md の品質等級は「score 改善 70%+/50%+」を線形前提で用いる。飽和関数では相対削減率と pp 差の解釈がずれ、閾値の意味が不明確。
- 出所: taxonomist（v1.1 審査時）
- 提案: 改善率を「相対削減率 (before−after)/before」で定義すると SSOT 明記（現行運用と一致）。絶対残存 S1/S2 ガードを主判定に、改善率は補助指標に格下げする案も併記。
- 影響: `SKILL.md §品質等級`, `CLAUDE.md §品質等級`, `naturalness-reviewer.md`
