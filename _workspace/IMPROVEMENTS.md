# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-09-05（cycle day 1: run 2026-09-05-001 技術解説記事 / 002 公的文書）

> **2026-09-05 適用サマリ**: IMP-002 / IMP-004 / IMP-005 を検出スキーマ v1.1 として適用（`status: done`）。両 run とも fidelity=pass・自然度 A・ロールバック 0。新パターン候補 K-1（過剰敬語スタッキング）ほかを追記。C-9 導入定型は 2 例目確認で taxonomist 昇格候補。

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run`
- **2026-09-05 再現**: run 001 で B-2 カタカナ語 13 件の**語単位置換**だけで change_rate 32% に到達（削除でなく置換の二重計上）。rewriter-A「同義語置換を別係数で／Levenshtein 距離で数えるべき」、fidelity=pass・自然度 A のため override せず accept。削除主導（day0 SEO ブログ）に加え**置換主導**でも同欠陥が出ることを確認。→ 次サイクルの最優先適用候補。
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。Sample A も 47.6% と高止まり。
- 出所: rewriter-A, rewriter-B, naturalness-B
- 提案: (a) 「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を change_rate から控除。(c) 挿入率を単独併記し、del≫ins の削除主導ケースは中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2run` 適用: 2026-09-05-001/002
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える（Sample A raw106→92.5、taxonomy 例は raw56→71.5 と不整合）。
- **2026-09-05 再現**: detector-A は `raw/(0.25*len)*100`、detector-B は `raw/len*1000` と**別式**を使用（母数依存で長文ほど低く出る）。式が SSOT に無いため検出器間で不整合、という欠陥を実証。
- 出所: detector-A, detector-B（day0 + 2026-09-05）
- **適用（v1.1）**: SSOT に単一式 `score = round(100×(1−exp(−raw/K)),1)`, K=40 を固定。`input_length` は改行除外。母数依存を廃止。detector / naturalness 両方が同式で score_before/after を算出。検証: raw56→75.3（≒旧例71.5）, raw97→91.2, raw28→50.3 で解像度維持・非飽和。
- 影響（適用済）: `ai-tell-taxonomy.md §検出出力スキーマ v1.1`, `ai-tell-detector.md §スコア算出`, `naturalness-reviewer.md §処理`

### IMP-003 score_before / score_after のフィールド契約が曖昧 `status: done` `hits: 2run` 適用: 2026-09-05-001/002
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score 92.5）。レビュアーごとに数値がぶれる。
- **2026-09-05 再現（後半＝score_after 側）**: naturalness-A「score_after の分母(推敲後長)が未固定で 0.974〜0.979 に振れる」、naturalness-B「score_after=0.0/改善率1.0 の解釈が短文で過大」。**before だけでなく after の算出契約も欠けていた**。
- 出所: naturalness-A, naturalness-B
- **適用（v1.1）**: `naturalness-reviewer.md §処理` に「score_before = 02_detection.json の meta.severity_weighted_score」「score_after = 残存 raw を同一飽和式(K=40)で算出（母数依存なし）」「等級は絶対残存数を主根拠」を明文化。IMP-002 の単一式で before/after を統一。
- 影響（適用済）: `naturalness-reviewer.md`, `ai-tell-taxonomy.md §フィールド契約`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: done` `hits: 2run` 適用: 2026-09-05-001/002
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
- **2026-09-05 再現**: detector-A「E-1/E-2/H-1 に start/end が馴染まず統計値(std=9.3, です率=1.0)が reason 文字列に埋没。`doc_level:true` と `metrics{}` を追加すべき」、detector-B「文書レベル所見を単一 span に押し込む構造的無理。`scope:document` / `spans[]` 追加を提案」。両 run で独立再現。
- 出所: detector-A, detector-B（day0 + 2026-09-05）
- **適用（v1.1）**: `span_type`(contiguous/scattered/document) ＋ `occurrences:[[s,e],…]` ＋ `metrics{}` を追加。density は contiguous span の**和集合**で数え document/scattered の locator を除外、と明文化。
- 影響（適用済）: `ai-tell-taxonomy.md §検出出力スキーマ v1.1`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: done` `hits: 2run` 適用: 2026-09-05-001/002
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。
- **2026-09-05 再現**: detector-A「A-7『ポテンシャルを持った』と B-2『ポテンシャル』が文字範囲で重複、density の和集合定義が未規定」、detector-B「f002=A-9＋A-8＋過剰敬語, f006=A-6＋A-8 が同一句に共起するが category は単一値。`secondary_categories[]` 提案」、rewriter-A も `chain_members` を提案。複数 run・複数エージェントで再現。
- 出所: detector-A/B, rewriter-A, fidelity-A（day0 5agent + 2026-09-05）
- **適用（v1.1）**: `secondary_categories: []` を追加し「1 span = 主分類 1 finding」「category_summary は主 category の先頭文字で集計」「density は和集合、detected_count は finding 数」を明文化。
- 影響（適用済）: `ai-tell-taxonomy.md §検出出力スキーマ v1.1`, `ai-tell-detector.md`

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。
- **2026-09-05 再現**: naturalness-A「ai-tell-detector の実起動不可、手動 span 走査で代替」、naturalness-B「span 追跡＋手動全文走査で新規混入 tell の見落としリスク」。両 run で再現。
- 出所: naturalness-A, naturalness-B（day0 + 2026-09-05）
- **部分対応（2026-09-05）**: `naturalness-reviewer.md §処理` に「サブエージェント再起動が不可なら span 追跡＋手動再走査可、採った経路を notes に明記」を追加。ただし**検出器 programmatic 呼び出し経路の必須化は未達**（次サイクル継続）。
- 提案: `ai-tell-detector` サブエージェント再呼び出しをオーケストレーター側で仲介する経路整備。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

### IMP-007 ジャンル別の深刻度係数・許容変奏リストが無い `status: ready` `hits: 1run(4agent)`
- 症状: 深刻度と E-2 変奏処方が全ジャンル一律。公的文書では (a) A-8 受動濫用の露見度が高く実質 S1 相当、(b) 「ください」連発や定型敬語はむしろ自然で減点不要、(c) 体言止め・「〜でしょう」変奏はかえって格を崩す。技術記事では B-2 の可否境界がジャンル依存。
- 出所（2026-09-05・複数エージェント横断）: detector-B（公文で A-8 を +1 段階、硬い敬語を −0.5 段階のジャンル係数提案）、rewriter-B（「敬語の格の下限」ガイド・公文用変奏 allow/deny 要求）、naturalness-B（genre×許容変奏マトリクスを playbook へ）、rewriter-A（敬体専用文末バリエーション表）。
- 提案: taxonomy に「ジャンル別 severity 係数」節、playbook E-2 に「ジャンル×許容変奏マトリクス（公文＝体言止め/でしょう回避・能動化と依頼言い換えで変奏、敬体＝ます/でしょう/体言止め/ません/てきました）」を追加。
- 影響: `ai-tell-taxonomy.md`, `rewriting-playbook.md §E`
- 次サイクル（同ジャンル再現で hits:2）で適用候補。

### IMP-008 change_rate が naturalness の過推敲シグナルに二重計上 `status: ready` `hits: 1run`
- 症状: `naturalness-reviewer.md` の過推敲シグナルに「変更率 30% 超」が含まれるが、これは IMP-001（change_rate 指標欠陥）と衝突。fidelity 別担当なのに naturalness 側でも change_rate を減点材料にすると、置換主導・削除主導の良質推敲を二重に罰する。
- 出所: naturalness-A（run 001, change_rate 32% を IMP-001 に従い減点せず処理した際に露見）
- 提案: naturalness の過推敲判定から change_rate 閾値を外し、意味劣化・文体崩れ・ぶつ切り等の**内容シグナル**に限定。IMP-001 適用時に同時修正。
- 影響: `naturalness-reviewer.md §処理`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 001。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B
- **C-9 導入定型（冒頭メタ宣言＋本論ブリッジ）** `status: ready` `hits: 2` — day0(SEO ブログ)「さっそく見ていきましょう」＋ 2026-09-05-001(技術記事)「本記事では〜わかりやすく解説していきます」。記事冒頭の自己言及的な導入宣言／本論への橋渡し定型。実務ライターは省く。**実例2件で昇格条件充足 → 次サイクルで taxonomist が C-9 として v1.1 本体へ**。 出所 detector-B, detector-A
- **K-1 過剰敬語スタッキング** ★日本語固有・公文特化 `hits: 1` — 「受動＋形式名詞(もの/こと)＋でございます」「動詞＋する必要がございます」で多層膨張。実例: 002「提供することを目的として行われるものでございます」「ご了承いただく必要がございます」(2回)。公文お知らせでもう1例確認で昇格。 出所 detector-B, rewriter-B
- **依頼型結びの反復（D-6 公文版）** `hits: 1` — 「〜ようお願い申し上げます／お願いいたします」が3連続。1回は自然、3回反復は AI 的。実例: 002。 出所 detector-B, naturalness-B
- **無生物への役割メタファ叙述（A-10/D-5 の二股）** `hits: 1` — 無生物主語に「役割を担う／果たす」を当てる型。実例: 001「意味的な空間上にマッピングする役割を担っています」「重要な役割を果たすことができます」。独立サブパターン化候補。 出所 detector-A

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019（並列→基盤の序列混入）はこの項が無く #5/#11 へ漏れ込んだ。`status: ready` `hits: 1` 出所 fidelity-A
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。`status: ready` `hits: 1` 出所 fidelity-B
- 「情報を含む削除 vs ボイラープレート削除」二分判定: 削除 span に (a)数値/固有名詞/日付 (b)条件/因果節 (c)固有の例示 を含めば情報欠落、挨拶/CTA/装飾/自己言及のみならボイラープレート。出所 fidelity-B
- #5論理関係 と #11情報追加 の責任境界を一意化（主因項目を 1 つに正規化）。出所 fidelity-A
- modality 強度を順序尺度化（要請/推奨/義務/必須）。出所 fidelity-A
- **#15 含意ずれ（多義語 drift）** 同義に見えて技術文脈で評価指標名と衝突する語（正確→精度=precision 等）を拾うサブチェック。実例: 001 f010「正確なアウトプット→出力の精度」。`hits: 1` 出所 fidelity-A（2026-09-05）
- **#16 暗黙主語追加の二段テスト（公文特化）** 受動→能動化で復元した主語が〈①その行為の真の実行者か ②文書内他箇所と矛盾しないか〉。実例: 002 f004「停止されます→停止します」（図書館を主語に確定）は①②合格、f001 は②で救済。`hits: 1` 出所 fidelity-B（2026-09-05）
- **形式名詞の「実質語 vs 包装語」判定** 措置・もの・こと・場合・点 を除いても指す実質動作/対象が本文に残れば minor(包装除去)、残らなければ major(情報欠落)。実例: 002 f008「措置」欠落は「自動延長」保存で minor。`hits: 1` 出所 fidelity-B（2026-09-05）
- **N/A と pass の区別** 数値/引用ゼロ文書で該当項目を pass 計上すると pass 率が実力以上に見える。出力スキーマで N/A を分離。出所 fidelity-A（2026-09-05）

### playbook レシピ追補
- **C-5 絵文字削除後の文末/区切り吸収ルール**（句点で吸収 or 削除のどちらか明記）。出所 rewriter-B
- **D 系結びは削除一択でなく「最小着地文を残す」**（減らしすぎ下限）。実例: B の「気軽に始めてみてください」。出所 rewriter-B, naturalness-B
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**という例外則。出所 rewriter-A
- **原文が元から推量の D 系は推量を保持**（「断定へ」の一律処方の例外）。出所 rewriter-A
- **B-2 残す/開く境界語リストの拡充**（コンポーネント→構成要素、アーキテクチャ→構造、ユーザー→利用者 等のグレー語を明記）。実例: 001。出所 rewriter-A（2026-09-05）
- **I-4「求められる」で原文に行為者が無い技術説明は、主語補完＝情報追加になるため断定的形容へ逃がす**（「欠かせません」等）。実例: 001 f015。出所 rewriter-A（2026-09-05）
- **公文の A-6/A-8 サブレシピ**（「措置が講じられる」「こととなる」等の官僚的状態叙述→行政主体への標準能動復元）。出所 rewriter-B（2026-09-05）

### naturalness 判定の精緻化
- 過推敲シグナルの定量化（敬体/常体混入は文末形態の二値カウントで機械検出）。出所 naturalness-A
- クラスタ系 finding（B-2 密集・C-1 列挙）はクラスタ崩壊時に個別 severity を降格するルール。出所 naturalness-A
- E-2 文末単調の到達可能ライン緩和（体言止め1箇所以上で合格、文体維持制約下の過推敲回避）。出所 naturalness-B
- 絶対残存数ガードを grade 表に組込み（改善率が高くても S1 が1件でも C 以下）。出所 naturalness-A, naturalness-B

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 2run`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B, fidelity-A, naturalness-A
- **2026-09-05 再現**: 技術記事で レイテンシ・アーキテクチャ・コンポーネント・ユーザー が「確立技術語ホワイトリスト」として同種問題。playbook B-2 の例外維持リスト拡充と併せて次サイクル適用候補。出所 naturalness-A, rewriter-A

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。出所 detector-A
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B
- **B-2 の可算単位固定＋カタカナ語率(%)の二本立て指標** 語単位カウントか文塊単位かで件数が数倍ぶれ score が乱高下。`hits: 1run(2agent)` 出所 detector-A, rewriter-A（2026-09-05）
- **A-6 の「変化 vs 状態」判定ルール** 「ようになる／なってくる」等の時間軸語の有無で変化叙述か状態叙述濫用かを機械判定。実例: 001。出所 detector-A（2026-09-05）
- **確立技術語ホワイトリストの固定**（レイテンシ・アーキテクチャ・コンポーネント等を B-2 除外に明記、レビュアー間の残存数ぶれを防ぐ）。出所 naturalness-A（2026-09-05）
