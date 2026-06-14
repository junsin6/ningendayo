# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-06-14（run 001 エッジ解説, 002 公的文書）。本日 IMP-001/002/003 を適用（done）。

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done(2026-06-14-001/002)` `hits: 2run(全agent)`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。Sample A も 47.6% と高止まり。**2026-06-14 で再現: run001 0.59（reorder＋カタカナ和語化で二重計上）/ run002 0.341（同形クセ高密度是正の累積）。両 run とも fidelity=pass・自然度 A で override accept。**
- 出所: rewriter-A, rewriter-B, naturalness-A, naturalness-B, fidelity-A, fidelity-B（2 run 横断で全工程が指摘）
- 提案: (a) 「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を change_rate から控除。(c) 挿入率を単独併記し、del≫ins の削除主導ケースは中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。
- **適用(2026-06-14)**: `edit_change_rate`（finding 紐付き置換・reorder は移動扱いで除外・装飾純削除は控除）/ `gross_change_rate`（difflib 参考）/ `semantic_edit_ratio` の3指標分離を playbook §変更率の数え方に明記。判定は edit_change_rate、50% 超でも fidelity=pass・自然度A/B・S1=0 なら override accept を SKILL §総合判定・rewriter.md に反映。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`✓, `japanese-style-rewriter.md`✓, `SKILL.md §総合判定`✓

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done(2026-06-14-001/002)` `hits: 2run(2agent)`
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える（Sample A raw106→92.5、taxonomy 例は raw56→71.5 と不整合）。**2026-06-14 で再現: detector-A は独自に K=120 飽和、detector-B は raw/1000字×1.6 と式がバラバラ → 同一基準でないとスコアが比較不能。**
- 出所: detector-A, detector-B（2 run）
- 提案: 飽和しにくい正規化を SSOT 明記（例 `100*(1-exp(-raw/k))` か「100字あたり加重和」）。分母（input_length 依存 or 固定 max）を確定。
- **適用(2026-06-14)**: `severity_weighted_score = round(100×(1−exp(−raw/45)),1)`、`raw=ΣS1×5+ΣS2×2+ΣS3×0.5`（ユニーク finding）を taxonomy §検出出力スキーマに固定。K=45 は既存アンカー raw56→71.5 を再現。density もユニーク文字集合基準に明記。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`✓, `ai-tell-detector.md §スコア算出`（taxonomy 参照で間接反映・次回明示追記候補）

### IMP-003 score_before のフィールド契約が曖昧 `status: done(2026-06-14-001/002)` `hits: 2run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score 92.5）。レビュアーごとに数値がぶれる。**2026-06-14: 両レビュアーは IMP-003 提案通り 78.3/67.6 を採用したが、未明文のため運用任せだった。**
- 出所: naturalness-A, naturalness-B
- 提案: 「score_before = 02_detection.json の meta.severity_weighted_score」と明文化。
- **適用(2026-06-14)**: naturalness-reviewer.md §処理2 に「score_before は必ず 02_detection.json の meta.severity_weighted_score。score_after は同一正規化式(K=45)で再計測」と明記。
- 影響: `naturalness-reviewer.md`✓, `ai-tell-taxonomy.md`（IMP-002 で式を固定済み）

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run(4agent)`
- **再現(2026-06-14)**: detector-A/B が E-2 文末単調・F 累積敬語など doc-level 所見を代表 span 1 点に押し込むしかなく「点を指すのに所見は面」の不整合を再指摘。`scope: "span"|"document"` フィールド提案を反復。**次回適用候補（昇格条件充足）。**
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
- 出所: detector-B, detector-A
- 提案: `span_type: "contiguous"|"scattered"|"document"` と scattered 用 `occurrences: [[s,e],...]` を追加。density は重複・locator を除いた実 AI クセ文字数ベースと定義。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run(9agent)`
- **再現(2026-06-14)**: detector-A（f004 が A-5＋A-10、f028/f009 重複）・detector-B（f014 E-2 と f007 I-3 が同一 span）・rewriter-A（子 finding 統合表記なし）・fidelity-B が `secondary_categories[]` / `related_ids` を再要望。density は今回ユニーク文字集合で回避したが detected_count と category_summary は二重計上。**次回適用候補。**
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。
- 出所: detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A（横断的に最多）
- 提案: 「1 span = 主分類 1 finding」を基本とし、`merged_findings: [...]` 配列を許容。category_summary は「findings の category 先頭文字を集計」と注記。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。
- 出所: naturalness-A（run001/002 とも）
- **再現/前進(2026-06-14)**: 両レビュアーは今回 detector を**実呼び出しで再走査**でき score_after（5.4 / 11.5）を実測。手動推定問題は緩和。残課題は「再走査時の入力・閾値（公文書ジャンルで敬語閾値を上げた点）を 05 に明記する監査トレース」。IMP-003 適用時に naturalness-reviewer.md §処理2 へ「検出器実呼び出し・手動推定禁止」を併記済み（部分適用）。
- 提案: `ai-tell-detector` をサブエージェントとして再呼び出しする経路を必須化（手動照合禁止）。
- 影響: `naturalness-reviewer.md §処理`(部分✓), `SKILL.md`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 001。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B
- **A 系: 「〜することで／することにより」手段節の濫用** 名詞化手段節を一律多用。実例 2026-06-14-001:「処理することにより」「最小化することで」「オフロードすることで」（本文3回）。A-3「を通じて」近縁の独立シグネチャ。 `hits: 1` 出所 detector-A
- **A 系: 「〜することを可能にする」二重可能化** enable+nominalization。実例 2026-06-14-001「実現することを可能にします」。A-5/A-10 のどちらとも微妙にずれる複合。 `hits: 1` 出所 detector-A
- **公文書: 行為者消失の受動・要請連鎖** 〈受動＋必要＋受動〉が連鎖し行為者が完全消失。実例 2026-06-14-002「図られる必要があると結論づけられました」「困難であると判断されたことを踏まえて実施されるものでございます」。A-8 と I-4 に分割計上したが独立サブ項目化の価値。 `hits: 1` 出所 detector-B
- **公文書: 「〜ものでございます」体言＋丁寧コピュラの説明調** it is something that 的説明迂言。実例 2026-06-14-002「実施されるものでございます」。A-6 近縁だが状態化ではない。 `hits: 1` 出所 detector-B
- **A-2 敬語版: 「〜におかれましては」最上級敬語の主題提示** 実例 2026-06-14-002「市民の皆様におかれましては」。A-2 サブ例として実例2件目で昇格検討。 `hits: 1` 出所 detector-B
- **ブログ見出し公式: タイトルの em-dash ＋「わかりやすく解説／徹底解説」** 実例 2026-06-14-001 タイトル「エッジコンピューティングとは何か——仕組みとメリットをわかりやすく解説」。J-3 は本文ダッシュ前提だがタイトル位置は別立て検討。 `hits: 1` 出所 detector-A
- **E-2b 文体混在（敬体文書内の常体終止）を E-2 から分離** 純粋な文末単調（リズム＝変奏を増やす）と文体混在（鉄則3違反＝統一する）は対処が逆。実例 2026-06-14-001 f003「リスクは下がる」。 `hits: 1` 出所 naturalness-A

### taxonomist 構造審査（2026-06-14 v1.1 昇格時）
- **E-2b は検出 taxonomy でなく品質ゲート側へ**: 処方が E-2 と正反対（変奏 vs 統一＝鉄則3違反是正）。検出分類に違反検出を混在させない原則を明文化。昇格時は「過推敲シグナル」側に置く。 `hits: 1` 出所 taxonomist
- **ジャンル係数（meta.genre）を taxonomy スキーマへ先行導入**: 公文書系候補（行為者秘匿・最上級敬語）は「S1 だが public_doc では温存」を絶対深刻度では表現できず、昇格すると誤検出源。深刻度に「ジャンル条件付き」軸が要る。 `hits: 2run`（IMP 既出のジャンル係数と統合）出所 taxonomist
- **合成項の昇格基準が SSOT に未定義**: 本日候補は全て既存項の合成/派生（x1=A-3近縁, x2=A-5/A-10複合, Pub-1=A-8+I-4合成 等）。「構成要素単独では捕捉漏れ＋処方が要素和と異なる、を両立する場合のみ独立項」という合成項昇格基準を昇格規則に追加提案。これが無いと taxonomy が肥大化し category_summary 集計（IMP-005）も揺らぐ。 `hits: 1` 出所 taxonomist
- **raw の長さ依存残留バイアス**: density は長さ正規化したが raw（→score）は finding 絶対量で増える。文書間比較に使うなら長さ正規化版 raw 併記を将来検討。 `hits: 1` 出所 taxonomist

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019（並列→基盤の序列混入）はこの項が無く #5/#11 へ漏れ込んだ。`status: ready` `hits: 1` 出所 fidelity-A
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。`status: ready` `hits: 1` 出所 fidelity-B
- 「情報を含む削除 vs ボイラープレート削除」二分判定: 削除 span に (a)数値/固有名詞/日付 (b)条件/因果節 (c)固有の例示 を含めば情報欠落、挨拶/CTA/装飾/自己言及のみならボイラープレート。出所 fidelity-B
- #5論理関係 と #11情報追加 の責任境界を一意化（主因項目を 1 つに正規化）。出所 fidelity-A
- modality 強度を順序尺度化（要請/推奨/義務/必須）。出所 fidelity-A
- **#5b 接続の明示度保存** `hits: 1` 「AはBによって生じた」→「A、B」で因果の明示度が低下し読者推測に委ねられる型を独立小項目化。受動能動化で因果弱化（#5）と相の喪失（#8）が同時発生する。実例 2026-06-14-002 f001。出所 fidelity-B
- **#9b 意図的行為者秘匿の保護** `hits: 1` 公文書が意図的に行為者をぼかす受動を能動化＝主体明示すると politeness/曖昧性戦略を毀損。命題等価のみ見る fidelity と naturalness の谷間に落ちる。出所 fidelity-B
- **#7 に「指示の直接性（face-threat）」軸を追加** `hits: 1` 「必要がございます」→「ください」は強度同等でも直接命令性が上昇。義務の量と質を分離。出所 fidelity-B
- **謙譲・尊敬語の付与が主体を取り違えていないかの敬語ベース主体監査**（#9 補助）。「いたします」は発信主体を文法的に確定するため、別主体の行為を謙譲化すると主体誤付与。出所 fidelity-B

### playbook レシピ追補
- **敬体維持時の E-2 文末変奏ガード（常体終止禁止）** `status: done(2026-06-14-001)` `hits: 1run(実害)`。敬体文書に常体終止を混ぜると変奏でなく文体混在（鉄則3違反）。許容は体言止め・「でしょう/のです/ません」・文長変化のみ。**今回 f003 で実害が出たため即適用**（playbook §E-2 文末変奏のガード）。出所 naturalness-A, rewriter-A
- **C-1 非対称解体に「主題倒置」を明記** `status: done(2026-06-14-001)`。順序語を消し主題を文頭前置して冒頭の機械的均一を崩す。削除一辺倒にしない。playbook に追記済み。出所 rewriter-A
- **公文書専用レシピ節（依頼形グラデーション・温存敬語/是正迂言の対照表）** `status: ready` `hits: 1`。「ください＜くださいますよう＜くださいますようお願い申し上げます」の格付け、温存（御礼申し上げます/賜りますよう）vs 是正（〜いただく必要がございます/〜いただいた上で）。現 playbook はコラム前提で公文書例が無い。出所 rewriter-B
- **A-8 公文書受動の但し書き**「主体明示が断定過剰になる場合は自動詞・連用中止で逃がす」。意図的な行為者秘匿（責任の非人格化）が正当な場面の保護。出所 rewriter-B, fidelity-B
- **B-2 カタカナ標準語ホワイトリストの参照ファイル化** `status: ready` `hits: 2run`。維持リストが Transformer/API/SDK 等 AI 用語に偏在。エッジ系・ネットワーク系（エッジコンピューティング/レイテンシ/クラウド/デバイス/DX）の維持基準と、和語化対象（アプローチ/ソリューション/シームレス 等）の対照表を独立ファイル化し detector/rewriter で共有。出所 detector-A, rewriter-A, naturalness-A
- **C-5 絵文字削除後の文末/区切り吸収ルール**（句点で吸収 or 削除のどちらか明記）。出所 rewriter-B
- **D 系結びは削除一択でなく「最小着地文を残す」**（減らしすぎ下限）。実例: B の「気軽に始めてみてください」。出所 rewriter-B, naturalness-B
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**という例外則。出所 rewriter-A
- **原文が元から推量の D 系は推量を保持**（「断定へ」の一律処方の例外）。出所 rewriter-A

### naturalness 判定の精緻化
- 過推敲シグナルの定量化（敬体/常体混入は文末形態の二値カウントで機械検出）。出所 naturalness-A
- クラスタ系 finding（B-2 密集・C-1 列挙）はクラスタ崩壊時に個別 severity を降格するルール。出所 naturalness-A
- E-2 文末単調の到達可能ライン緩和（体言止め1箇所以上で合格、文体維持制約下の過推敲回避）。出所 naturalness-B
- 絶対残存数ガードを grade 表に組込み（改善率が高くても S1 が1件でも C 以下）。出所 naturalness-A, naturalness-B
- **S3 反復の加重補正** `hits: 1` 同一カテゴリの S3 反復（文末同型3回以上等）は実質 S2 相当として加重、または S3 件数上限ガード（S3≥8 で B 降格検討）。公文書は S3 多数残でも A になりやすく読み手の違和感累積を拾えない。出所 naturalness-B
- **ジャンル係数（meta.genre）** `hits: 2run` 公文書では「申し上げます/賜りますよう/ご〜いただく」が正当な定型。敬語系の検出閾値を public_doc で +1〜2 回緩める係数を持たせ S2 氾濫を防ぐ。出所 detector-B, rewriter-B
- **変更率警告と過推敲判定の突き合わせ**を総合判定に明文化（変更率超過時は naturalness 側で意味希薄化を重点確認）。出所 naturalness-B

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 1run(3agent)`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B, fidelity-A, naturalness-A

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。出所 detector-A
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B
