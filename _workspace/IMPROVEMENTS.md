# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-09-08（run 2026-09-08-001 技術解説記事, 2026-09-08-002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run(6agent)`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。Sample A も 47.6% と高止まり。
- 再現 2026-09-08-001: change_rate 0.331（削除 219 字・挿入 45 字＝削除主導）で 30% 警告超過。純削除だけで 27.4%。rewriter-A/naturalness-A ともに「削除主導の膨張であり damaging でない」と判定し **override accept**。挿入率は 5.6% にすぎない。
- 出所: rewriter-A, rewriter-B, naturalness-B（day0）＋ rewriter-001, rewriter-002, naturalness-001, naturalness-002（day1）
- 提案: (a) 「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を change_rate から控除。(c) 挿入率を単独併記し、del≫ins の削除主導ケースは中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。(e) 【day1 追加】段落別 change_rate を併記し過推敲の局所偏在を検知（rewriter-002）。(f) 【day1 追加】ジャンル別 churn 特性（公的文書は 1 編集あたり削除字数が大）を閾値に反映。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done(2026-09-08)` `hits: 2run(2agent)`
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える（Sample A raw106→92.5、taxonomy 例は raw56→71.5 と不整合）。
- **再現 2026-09-08: 1 日で 3 通りの式が並存**。detector-001 は飽和関数 `100*raw/(raw+len*0.024)`→84.6、同 run のファイルは K=350 線形→46.0、detector-002 は `raw/len*1000`→31.8。同一パイプライン内で正規化が不統一という決定的証拠。
- 出所: detector-A, detector-B（day0）＋ detector-001, detector-002（day1）
- 提案: 飽和しにくい正規化を SSOT 明記（例 `100*(1-exp(-raw/k))` か「100字あたり加重和」）。分母（input_length 依存 or 固定 max）を確定。
- **適用（2026-09-08-001/002）**: `ai-tell-taxonomy.md §検出出力スキーマ` に単一の正規化式を明記。`rate = raw/input_length*1000`（1000字あたり加重和）→ `score = 100*(1-exp(-rate/K))`, **K=30 固定**。全検出器・レビュアーがこの式のみを使用する契約とし、`ai-tell-detector.md`/`naturalness-reviewer.md` から参照。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出`, `naturalness-reviewer.md`

### IMP-003 score_before のフィールド契約が曖昧 `status: done(2026-09-08)` `hits: 2run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score 92.5）。レビュアーごとに数値がぶれる。
- **再現 2026-09-08-001: naturalness-001 が score_before に 84.6 を採用したが 02_detection.json の meta 実値は 46.0（約 1.8 倍乖離）。レビュアーが「prompt の数値と file 値が矛盾」と明示指摘。**
- 出所: naturalness-A（day0）＋ naturalness-001（day1）
- 提案: 「score_before = 02_detection.json の meta.severity_weighted_score」と明文化。数値をプロンプトに二重記載しない。
- **適用（2026-09-08-001）**: `ai-tell-taxonomy.md §検出出力スキーマ`・`naturalness-reviewer.md` に「score_before は 02_detection.json の meta.severity_weighted_score を唯一の真実源とする（他所に数値を二重記載しない）」を明記。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: done(2026-09-08)` `hits: 2run(5agent)`
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
- **再現 2026-09-08: detector-001（E-1/E-2/C-1 を代表位置で仮アンカー、恣意的と自認）、detector-002（E-2 を「ございます」1点に無理紐づけ）、rewriter-002（f010 E-2 が座標(493-498)を持つが実体は分布問題で単一 span 置換では解けず）が横断的に要求。**
- 出所: detector-B, detector-A（day0）＋ detector-001, detector-002, rewriter-002（day1）
- 提案: `scope: "span"|"document"`（＋ scattered 用 `occurrences: [[s,e],...]`）を追加。document scope は start/end 任意。density は重複・locator を除いた実 AI クセ文字数ベース（ユニオン）と定義。diff 側に `resolved_by_distribution` を許容。
- **適用（2026-09-08-001/002）**: `ai-tell-taxonomy.md §検出出力スキーマ` の finding に `scope: "span"|"document"`（既定 span）と document 用 `occurrences: [[start,end],...]` を追加。`ai_tell_density` を「被覆文字のユニオン / 全体文字数（重複排除）」と明記。`ai-tell-detector.md` に反映。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run(7agent)`
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。
- 再現 2026-09-08-001: detector-001 が「リトリーブというプロセス」= A-13 という + B-2 カタカナ×2 の跨りに `secondary_categories[]` を要望。rewriter-001 が同一文内 finding の相互依存（f009 格助詞×f012 述語が文法競合）を要注記。detector-002 が となる系3件・必要系3件を束ねる `cluster_id` を要望。
- 出所: detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A（day0）＋ detector-001, rewriter-001（day1）
- 提案: 「1 span = 主分類 1 finding」を基本とし、`secondary_categories:[...]`（跨りカテゴリ）と、同一密度クラスタを束ねる `cluster_id` を許容。同一文内で提案が文法競合する finding に相互依存フラグ。category_summary は「findings の category 先頭文字を集計」と注記。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 2run(2agent)`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。
- **再現 2026-09-08: naturalness-001・naturalness-002 の双方が「実行環境に Agent/Task 起動ツールが露出しておらず ai-tell-detector サブエージェントを spawn 不能」と報告し、フォールバックで手動再計測。IMP-006 の自動再走査は現状の権限構成では構造的に不可能であることが確定。**
- 出所: naturalness-A（day0）＋ naturalness-001, naturalness-002（day1）
- 提案: (a) オーケストレーターが推敲後 detection JSON（04.5 相当）を先に生成しレビュアーへ渡す設計にすれば、レビュアーの spawn 権限に依存せず IMP-006 逸脱を構造的に解消。(b) 当面は手動フォールバック時に `detector_rerun.method: "manual"|"subagent"` をスキーマ必須化し監査可能にする。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 001（day0）。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。実例: 2026-09-08-001「見ていきましょう」も同型。 `hits: 2` 出所 detector-B(day0), detector-001(day1)
- **【新 day1】A-8b 不自然な尊敬受動（サ変動詞への -される 付加）** [S2 候補]。可能・尊敬・受動の識別を誤った過剰敬語。実例: 2026-09-08-002「手続きが完了されない場合」（→「完了しない」が正）。公的/ビジネス AI 文の文法崩れシグネチャ。A-8 とは別軸。 `hits: 1` 出所 detector-002, rewriter-002
- **【新 day1】I-4 サブ「〜いただく必要がございます」官庁冗長要請テンプレ**。依頼を「必要」名詞化＋「ございます」化。実例: 2026-09-08-002「ご留意いただく必要がございます」（→「ご留意ください」）。正規表現化容易で高精度。 `hits: 1` 出所 detector-002
- **【新 day1】サ変名詞＋「を行う」冗長分解**。「再設定を行っていただく」→「再設定していただく」。F 系（過度な修飾）か A 系の新サブ。実例: 2026-09-08-002「再設定を行う」。 `hits: 1` 出所 detector-002
- **【新 day1】D 系「〜していきます」ブログ解説体**。「わかりやすく解説していきます」等、技術ブログ AI の進行形結び。D-1 未収載。実例: 2026-09-08-001。 `hits: 1` 出所 detector-001
- **【新 day1】「〜する仕組みです／という仕組み」定義締め**。技術解説 AI が定義文を体言＋断定で機械的に閉じる型。実例: 2026-09-08-001「生成できる仕組みです」。 `hits: 1` 出所 detector-001

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019（並列→基盤の序列混入）はこの項が無く #5/#11 へ漏れ込んだ。`status: ready` `hits: 1` 出所 fidelity-A
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。`status: ready` `hits: 1` 出所 fidelity-B
- 「情報を含む削除 vs ボイラープレート削除」二分判定: 削除 span に (a)数値/固有名詞/日付 (b)条件/因果節 (c)固有の例示 を含めば情報欠落、挨拶/CTA/装飾/自己言及のみならボイラープレート。出所 fidelity-B
- #5論理関係 と #11情報追加 の責任境界を一意化（主因項目を 1 つに正規化）。出所 fidelity-A
- modality 強度を順序尺度化（要請/推奨/義務/必須）。出所 fidelity-A, fidelity-001（day1 再現）
- **【新 day1】近似化副詞（大きく/おおよそ/一般的に）の削除で確信度が上がる**。「大きく二つ」→「二つ」は数量子不変だが断定寄り。#7 modality のサブ項目に「hedge/approximator 削除による確信度上昇」を基準化。出所 fidelity-001
- **【新 day1・公的文書】受動→能動化の「行為者の同一性」と「責任・義務主体の同一性」を 2 軸に分離**。「完了されない→完了しない」は自動詞化で利用者の不作為がシステムの自然不成立に読み替わりうる。#9 を 2 軸化。出所 fidelity-002
- **【新 day1・公的文書】義務→依頼の modality 軟化は「拘束力担保の所在」を明示監査**。「必要がございます→ください」単体は義務を弱めるが、同一義務の拘束力を担保する条件節/帰結文（完了しない場合、利用不可）が保存されていれば pass、担保文が無い/同時に軟化されたら rollback。出所 fidelity-002
- **【新 day1・公的文書】「宛先・手続経路・順序の同一性」を独立チェック項目化**。メール宛先・案内チャネルは公的手続で決定的だが 13 項に薄い。出所 fidelity-002
- **【新 day1】動詞の含意強度マトリクス**（提供＜支援＜可能化＜実現＜解決）。「ソリューションを提供→解決」の 2 段跳躍のみ rollback とする定量ルール。fidelity と naturalness の判定境界（modality は fidelity が一次、naturalness は二次確認）も総合判定表に明記。出所 fidelity-001

### playbook レシピ追補
- **C-5 絵文字削除後の文末/区切り吸収ルール**（句点で吸収 or 削除のどちらか明記）。出所 rewriter-B
- **D 系結びは削除一択でなく「最小着地文を残す」**（減らしすぎ下限）。実例: B の「気軽に始めてみてください」。出所 rewriter-B, naturalness-B
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**という例外則。出所 rewriter-A
- **原文が元から推量の D 系は推量を保持**（「断定へ」の一律処方の例外）。出所 rewriter-A
- **【新 day1・公的文書】敬体 officialese 向け変換表が皆無**。現 playbook は常体/コラム前提の例が多い。「必要がございます→ご留意ください」「実施されることとなりました→実施することといたしました」等、敬体・硬い公的文の置換例を追加。出所 rewriter-002
- **【新 day1・公的文書】A-8 受動の一律除去は危険**。「主体秘匿が機能的な受動（受付が停止される／変更される）は保持」の但し書きを A-8 に追加。能動化すべきは文法違和（完了されない）と連体修飾の連鎖（送信される案内）のみ。出所 rewriter-002, naturalness-002
- **【新 day1】A-13「述語＋という＋名詞」型は削除でなく叙述化**。「難しいという課題」を単純削除すると「難しい課題」で意味変（属性→内容）。叙述化（しづらいのが課題）へ分岐をレシピに追記。出所 rewriter-001
- **【新 day1】E-1 短文挿入は「既存要素の分割・体言止め」に限る（新主張禁止）**。鉄則「新情報を足さない」との両立を明文化。出所 rewriter-001
- **【新 day1】同一語幹カタカナの開閉方針を一意化**（リトリーバー維持 vs リトリーブ開く の非対称、ナレッジ→知識 vs ナレッジベース維持）。terminology-consistency を naturalness の必須チェックに。出所 rewriter-001, fidelity-001, naturalness-001

### naturalness 判定の精緻化
- 過推敲シグナルの定量化（敬体/常体混入は文末形態の二値カウントで機械検出）。出所 naturalness-A
- クラスタ系 finding（B-2 密集・C-1 列挙）はクラスタ崩壊時に個別 severity を降格するルール。出所 naturalness-A
- E-2 文末単調の到達可能ライン緩和（体言止め1箇所以上で合格、文体維持制約下の過推敲回避）。出所 naturalness-B
- 絶対残存数ガードを grade 表に組込み（改善率が高くても S1 が1件でも C 以下）。出所 naturalness-A, naturalness-B
- **【新 day1・重要】過推敲シグナルに `verdict: warning|damaging` を必須化し、grade は damaging 数のみでカウント** `status: ready` `hits: 1run(2agent)`。change_rate 33.1%（報告義務のみ）と f012 含意差（監査委譲）を機械的に 2 個数えると誤って C 降格する。naturalness-001 は JSON に `over_polish_signal_count_damaging` を新設して回避。出所 naturalness-001, naturalness-002
- **【新 day1】絶対残存 raw スコアを grade の主軸に、改善率は補助指標**。短文・低ベース run は改善率が飽和し過大評価（002 は raw 19→0.5 で 97%）。絶対残存 raw<3.0 で A 上限等の二軸判定を等級表に明文化。出所 naturalness-001, naturalness-002
- **【新 day1】意図保持 finding に `intentionally_preserved` フラグ**。preserve 判断した finding を残存として拾うと過推敲回避の正しい判断が減点方向に働く。スコア寄与を分離。出所 naturalness-002
- **【新 day1・公的文書】トーン過剰軽量化の定量検出**。officialese マーカー語（当該/賜る/何卒/申し上げる/いたす）の推敲前後残存比 <0.6 で警告、「ください」等の直接命令形が文末の 40% 超で官報調崩れ疑い。出所 naturalness-002
- **【新 day1】文末反復を語形クラスタ単位（申し上げます系/ください系/です・ます系）で再計測**。置換後に別の単調が生まれるケースを検出。出所 naturalness-002

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 2run(5agent)`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B, fidelity-A, naturalness-A（day0）
- **【day1 拡充】技術ジャンル（RAG/LLM 系）標準カタカナ辞書を references に追加**: コンポーネント・クエリ・ドキュメント・コンテキスト・レスポンス・チャンク・エンベディング・ベクトル・ハルシネーション・リトリーバー・ジェネレーター・アーキテクチャ。維持/開放の判断が推敲役裁量に委ねられ run 間で揺れる。出所 detector-001, rewriter-001（day1）

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。出所 detector-A（day1 で detector-001/002 とも自己検証実施・全 span 一致を確認、有効性実証）。
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B
- **【新 day1】category_label を SSOT で ID→正式ラベル一覧化**（検出器の自作でラベル揺れ、監査突合が不安定）。出所 detector-001, detector-002

### 公的文書ジャンル特有（新 day1）
- **ジャンル別 severity ダウングレード表 / meta.genre**。A-6「となっております」・A-1「において」・I-4「必要がございます」は官庁お知らせでは単発なら正当。`genre==public_notice` で密度到達まで S2 扱いにする明文規定。出所 detector-002
- **公的文書ホワイトリスト**（お願い申し上げます／何卒／賜りますよう／下記のとおり／におかれましては／希望される（尊敬受動））は無条件非検出。出所 detector-002, naturalness-002
