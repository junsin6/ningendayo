# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-09-23（run 2026-09-23-001 技術解説, -002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2runs`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。Sample A も 47.6% と高止まり。
- 出所: rewriter-A, rewriter-B, naturalness-B（001,002 で再現）
- 再現(2026-09-23): run 001 で change_rate 28.8%（削除178/挿入55）と削除主体で 30% 閾値に近接、rewriter-A #6・naturalness-A #2 が「削除率と挿入率を分離し削除率に緩い閾値を」と再提案。閾値近接を naturalness の過推敲シグナルに反映する要望も併発。
- 提案: (a) 「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を change_rate から控除。(c) 挿入率を単独併記し、del≫ins の削除主導ケースは中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。(e) naturalness 側で deletion_pressure=change_rate/0.30 を連続値化し 0.8 超を黄信号帯として grade に反映。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`, `naturalness-reviewer.md`
- 次回適用候補（今回は IMP-002/004/005 を優先適用したため見送り）。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2runs` 適用 run: 2026-09-23-001/002
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える（Sample A raw106→92.5、taxonomy 例は raw56→71.5 と不整合）。
- 出所: detector-A, detector-B, naturalness-A（001,002 で再現）
- 再現(2026-09-23): **検出器2体が別々の式を発明**（detector-A: `100*(1-exp(-raw/(len*0.05)))` k=0.05／detector-B: `min(100, raw/len*1000)` 線形）。同一入力で正規化がブレる欠陥を実証。naturalness-A #4 は before/after で input_length が変わりスケール差が改善率に混入すると指摘。
- 対応(適用済み): SSOT に**文長非依存の飽和式**を確定明記。`raw = S1×5 + S2×2 + S3×0.5`、`raw_per100 = raw / 本文文字数 × 100`（本文文字数＝改行・タイトル込みの全文字。定義を明記）、`severity_weighted_score = round(100×(1−exp(−raw_per100 / 8)), 1)`。k=8 固定。改善率は before/after とも各自の本文長で算出（スケールは各自固定）。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`（式確定）, `ai-tell-detector.md §スコア算出`（手順反映）。
- 回帰確認: 001 before raw84/809字→raw_per100=10.4→score72.7、after raw7/686字→12.0、改善83.5%（B 維持）。002 before raw45/689字→6.53→55.9、after raw3→5.3、改善90.5%（A 維持）。等級は不変で回帰なし。

### IMP-003 score_before のフィールド契約が曖昧 `status: ready` `hits: 1run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score 92.5）。レビュアーごとに数値がぶれる。
- 出所: naturalness-A
- 提案: 「score_before = 02_detection.json の meta.severity_weighted_score」と明文化。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: done` `hits: 2runs` 適用 run: 2026-09-23-001/002
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
- 出所: detector-B, detector-A（001,002 で再現）
- 再現(2026-09-23): detector-A #1「E-1/E-2 は本来スパン非依存だが start/end 必須のため代表文にアンカーせざるを得ず不自然」、detector-B #4「document_level フラグか spans[] を許す拡張が要る」。両 run で E-2 文末単調を代表 span に無理やり帰着させていた。
- 対応(適用済み): スキーマに `scope: "span" | "scattered" | "document"`（既定 span）と、scattered 用 `occurrences: [[s,e],...]`、document 用 `spans` 省略可（start/end を null 許容）を追加。`ai_tell_density` は locator・重複を除いた実クセ文字数基準と明記。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md`。
- 回帰確認: 既存の contiguous finding は scope 省略で従来どおり。document-level finding のみ scope:"document" を付与する追加運用で、既存 JSON の後方互換あり。

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: done` `hits: 2runs` 適用 run: 2026-09-23-001/002
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。change_rate も per-edit 合算だと重複二重計上。
- 出所: detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A（001,002 で再現・横断的に最多）
- 再現(2026-09-23): rewriter-A #1「para1-S3 に A-5+E-2+E-1+A-13 が同一文で重なり、per-edit の insert/delete 合算は二重計上。change_rate は全文 diff で算出した」。detector-A #5「オーバーラップ span の優先順位・重複許可が未定義」。fidelity-A #6「2 finding 統合 edit で単独では起きぬ意味変化（『大きな』脱落）が紛れる」。
- 対応(適用済み): (a)「1 span = 主分類 1 finding、副該当は `merged_categories: [...]` に列挙」を SSOT に明記。(b)「**change_rate は per-edit 合算ではなく推敲文全体の difflib グローバル diff で計測**」を playbook §変更率に明記。(c)「複数 finding を 1 edit に統合した場合は diff に `merged_finding_ids` を記し、fidelity 重点監査対象とする」を rewriter.md に追加。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`。
- 回帰確認: 今回の 03_rewrite_diff.json は既に全文 diff で change_rate を算出済みで整合。追加フィールドはすべて任意で後方互換。

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 1run`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。
- 出所: naturalness-A
- 提案: `ai-tell-detector` をサブエージェントとして再呼び出しする経路を必須化（手動照合禁止）。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 001(day0)。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B
- **A-8b 無主語受動（agentless passive）の濫用 ★公的文書固有** [S2] — A-8 は「〜によって」後置受動限定だが、行為者を完全に伏せた「〜される」の連鎖（実施される/図られる/行われる/更新される）を捕捉できない。公的文書 AI 文の最頻出クセ。能動化は発信者が文脈から一意に導ける場合のみ。 `hits: 1run(3agent)` 出所 detector-B#1, rewriter-B#3, naturalness-B#2。実例(002): 「工事が実施される」「周知が図られる」「安全管理の徹底が行われる」「お知らせが更新される」。昇格有望（別 run 再現で ready）。
- **K. 過剰敬語・儀礼定型句の連鎖 ★公的文書固有** [S2] — 「賜り」「厚く御礼申し上げます」「お願い申し上げます」等の謙譲・美化語の高密度連鎖。A〜J に受け皿が無い。※ただし「除去対象」ではなく「格式として保持しつつ機械的反復のみ緩和」の両義扱いが必要。むしろ Do-NOT/ホワイトリスト側で扱うべきとの反対意見（rewriter-B#1）もあり、taxonomist 審査で「新カテゴリ化」か「儀礼句ホワイトリスト」かを裁定要。 `hits: 1run(4agent)` 出所 detector-B#2, rewriter-B#1, naturalness-B#1/#4。
- **G/I 系: 「〜場合がございます」曖昧可能性ヘッジの反復** — 「延長される場合が」「濁る場合が」「交通整理が行われる場合が」等、起こりうる事態の定型ぼかし。G-1 とも I-4 ともずれる。 `hits: 1` 出所 detector-B#3, naturalness-B。実例(002) 3反復。
- **A-5+A-6 複合「〜することが可能となっている」** [S1候補] — A-5(できる冗長)＋A-6(状態化)の連結。単独より露見度が高い決定シグネチャ。個別レシピだと継ぎ目が不自然になるため統合レシピが要る。 `hits: 1` 出所 detector-A#3, rewriter-A#2。実例(001): 「実現することが可能となっています」。
- **B-1b 日常カタカナ語・定着訳語への英語併記** [S1候補] — B-1 は「初出専門語への併記」想定だが、日常カタカナ語（クラウド(Cloud)/デバイス(Device)）や定着訳語（量子化(Quantization)/プルーニング(Pruning)）への英語併記は専門語併記より露見度が高い。B-1 を二段基準化（日常語・定着訳語には併記しない／主概念と業界標準語のみ初出1回）。 `hits: 1` 出所 detector-A#4, rewriter-A#4。実例(001) 4件。
- **D-6b 予測型誇張結び「今後ますます〜となっていくでしょう」** [S2] — D-6（〜すべき時だ型結び）に含まれない「予測＋誇張＋状態化」の別型結び。 `hits: 1` 出所 detector-A#6。実例(001): 「今後ますます重要な存在となっていくでしょう」。

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019（並列→基盤の序列混入）はこの項が無く #5/#11 へ漏れ込んだ。`status: ready` `hits: 1` 出所 fidelity-A
- **#15 評価語・強調修飾の減衰チェック** — 「二つの**大きな**メリット」→「メリットは**大きく**二つ」で評価形容詞『大きな』が量近似副詞へ化けた（fidelity-A#1, run001 f001）。現行13項は数値/量化/欠落/modality に分散し評価的形容詞の脱落を正面から捕えられない。`status: ready` `hits: 1` 出所 fidelity-A
- **#16 依頼・義務・要請の強度保存** — 「〜必要がある（義務）」→「〜ください（依頼）」変換で、依頼形が命令的要請（公的通知の「ください」）なら義務力保持=pass、「〜を推奨/〜するとよい」等の推奨形へ落ちたら弱化=fail 候補。`status: ready` `hits: 1` 出所 fidelity-B#1（run002 f006 は pass 事例）
- **#17 受動→能動化の補完主語の一意性** — 無主語受動を能動化する際、補う主語が原文文脈から一意に導けるなら pass、導けない主語挿入は情報追加=fail。字面挿入は最小限に。`status: ready` `hits: 1` 出所 fidelity-B#2, rewriter-B#3（A-8b と対の監査規約）
- **F-2 二重修飾の集約は「近義」限定** — 「安全で安定した」の『安全(水質)』と『安定(供給継続)』は別次元の概念で集約不可。集約前に両語が真に近義かを確認する（run002 f015 が fidelity fail→ロールバックの実例）。`status: ready` `hits: 1` 出所 fidelity-B（本 run 実害あり）
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。`status: ready` `hits: 1` 出所 fidelity-B
- 「情報を含む削除 vs ボイラープレート削除」二分判定: 削除 span に (a)数値/固有名詞/日付 (b)条件/因果節 (c)固有の例示 を含めば情報欠落、挨拶/CTA/装飾/自己言及のみならボイラープレート。出所 fidelity-B
- #5論理関係 と #11情報追加 の責任境界を一意化（主因項目を 1 つに正規化）。出所 fidelity-A
- modality 強度を順序尺度化（要請/推奨/義務/必須）。出所 fidelity-A

### playbook レシピ追補
- **C-5 絵文字削除後の文末/区切り吸収ルール**（句点で吸収 or 削除のどちらか明記）。出所 rewriter-B
- **D 系結びは削除一択でなく「最小着地文を残す」**（減らしすぎ下限）。実例: B の「気軽に始めてみてください」。出所 rewriter-B, naturalness-B
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**という例外則。出所 rewriter-A
- **原文が元から推量の D 系は推量を保持**（「断定へ」の一律処方の例外）。出所 rewriter-A
- **A-6 敬体では「でしょう」を許容変奏に** — suggested_fix が常体「〜だろう」でも機械適用せず、敬体では「でしょう」を E-2 変奏として温存。出所 rewriter-A#3（run001 f008）。`hits: 1`
- **D-5 非擬人化の定番 after 追加** — 「重要な役割を果たす」→「欠かせない/要となる」。出所 rewriter-A#5。`hits: 1`
- **公的文書ジャンル: 儀礼定型句ホワイトリスト節**（Do-NOT に「平素より〜賜り」「〜申し上げます」等を保護明記）。I-3 の敬体・謙譲の受け皿（ご〜ください/〜くださいますようお願いいたします 等を敬語レベル別に分散）も playbook I-3 に不足。出所 rewriter-B#1/#2。`hits: 1`
- **A-6＋A-8 複合「されることとなっております」→「します/されます（発信者主体で断定）」** の一括レシピ。出所 rewriter-B#4。`hits: 1`

### naturalness 判定の精緻化
- 過推敲シグナルの定量化（敬体/常体混入は文末形態の二値カウントで機械検出）。出所 naturalness-A
- **残存 finding を「元 finding の未解消」と「検出器が原文で見落とした新規検出」に二分**し、改善率は前者ベース・grade の絶対残存数は合算で評価する二層方式。改善率が推敲役の貢献でなく検出器のリコール差を混入させる問題への対処。出所 naturalness-A#1（run001: 元 finding は 27/27 完全解消だが検出漏れの B-2 3件が残存し B 判定）。`status: ready` `hits: 1`
- **grade の S2 カウントを件数でなく「カテゴリ系統数」または raw 加重和ベースへ** — 語単位で膨らむ B-2 と文書レベル1件の E-2 が同じ「S2 1件」では重みが違う。出所 naturalness-A#3。`hits: 1`
- **儀礼句保存率 = 推敲後儀礼句数/推敲前儀礼句数** を公的文書の逆方向過推敲（格式崩し）の定量指標に。出所 naturalness-B#1。`hits: 1`
- **A-8 のジャンル感応 severity** — 公的文書では「周知が図られる」等の無主語受動は正当な register で、能動化するとむしろ過推敲。ジャンル別 severity テーブルが要る。出所 naturalness-B#2（A-8b 候補と対）。`hits: 1`
- **丁寧度（敬意強度）の段階判定** — 「ご確保ください」と「確保してください」の格差を測る指標。敬体/常体の二値では公的文書の命令的トーンを検出できない。出所 naturalness-B#3。`hits: 1`
- クラスタ系 finding（B-2 密集・C-1 列挙）はクラスタ崩壊時に個別 severity を降格するルール。出所 naturalness-A
- E-2 文末単調の到達可能ライン緩和（体言止め1箇所以上で合格、文体維持制約下の過推敲回避）。出所 naturalness-B
- 絶対残存数ガードを grade 表に組込み（改善率が高くても S1 が1件でも C 以下）。出所 naturalness-A, naturalness-B

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 1run(3agent)`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B, fidelity-A, naturalness-A

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。出所 detector-A
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B
