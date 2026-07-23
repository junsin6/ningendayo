# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数（別 run での再現のみ +1）。

最終更新: 2026-07-23（run 001 技術解説, 002 公的文書。cycle_day 1）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。06-12 Sample B は 54.6% で hold 誤発火。07-23 でも再現: run 001 は削除主導（削除135/挿入48）で 29.1%、rewriter-A/naturalness-A ともに「削除率と挿入率を分離し、閾値判定は挿入率主体にすべき」と指摘。run 002 も格助詞 が→を の replace が両側計上され膨張傾向。
- 出所: 06-12 rewriter-A/B, naturalness-B ＋ 07-23 rewriter-A, rewriter-B, naturalness-A（別 run 再現）
- 提案: (a) 「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を控除。(c) 挿入率を単独併記し del≫ins の削除主導ケースは中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準へ。
- **適用（2026-07-23, run 001/002）**: `rewriting-playbook.md §変更率の数え方` に挿入率/削除率の分離併記と「削除主導は過推敲でない」注記、`SKILL.md §総合判定` に「change_rate 超過でも fidelity=pass かつ自然度 A/B は override accept」を明文化。残: スキーマへの機械的な metric 分離フィールドは将来。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2run`
- 症状: 正規化式が SSOT に無く、検出器ごとに定数を逆算する羽目に。07-23 で detector-A/detector-B が独立に `100*(1-exp(-raw/40))` を採用し `meta.score_formula` を独自追加（前 run 92.5 から k≈41 を逆算）。式が SSOT に無いと run 間でスコア比較が不能。
- 出所: 06-12 detector-A/B ＋ 07-23 detector-A, detector-B（別 run 再現）
- 提案: 飽和しにくい正規化を SSOT 明記。分母を確定。meta に score_formula を正式フィールド化。
- **適用（2026-07-23, run 001/002）**: `ai-tell-taxonomy.md §検出出力スキーマ` に式 `severity_weighted_score = 100*(1-exp(-raw/k))`, `raw = 5*S1 + 2*S2 + 0.5*S3`, `k=40` と meta.score_formula の任意併記を明記（taxonomist 審査で v1.1 へ）。

### IMP-003 score_before のフィールド契約が曖昧 `status: ready` `hits: 1run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。
- 提案: 「score_before = 02_detection.json の meta.severity_weighted_score」と明文化。07-23 はオーケストレーターが値を明示指定して回避したが、仕様側は未固定のまま。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run`
- 症状: 絵文字分散・文末単調・E-2/E-1/C 系は文書レベル指標だが全 finding に start/end 必須。07-23 でも E-2 を代表文末に便宜アンカーせざるを得ず（detector-A「モデルです」に、detector-B は E-2 計上見送り）、推敲役が「この数文字だけ直せばよい」と誤読するリスク。
- 出所: 06-12 detector-A/B ＋ 07-23 detector-A/B, naturalness-A/B（別 run 再現）
- 提案: `scope: "span"|"document"` と、document スコープでは span 任意・`evidence/metric`（文末反復率・文長SD 等）を持たせる。scattered 用 `occurrences:[[s,e],...]`。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリに該当し category_summary が過小評価。07-23 再現: detector-A「実現することが可能となります」は A-6/A-5/A-10 の三重、`secondary_categories:[]` を提案。fidelity-A は #7/#11/#12 の責任境界重複を指摘。
- 出所: 06-12 5agent ＋ 07-23 detector-A, fidelity-A（別 run 再現）
- 提案: 「1 span = 主分類 1 finding + `secondary_categories:[]`」。#7(強度)/#11(新規事実)/#12(別義) の排他的振り分けルールを併せて明記。
- 影響: 全 .md のスキーマ節, `content-fidelity-auditor.md`

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 1run`
- 症状: レビュアーが手動照合 → 数値が推定値。07-23 はオーケストレーターが「同一式・同一 k で再走査せよ」と明示指示し両レビュアーが式ベースで算出（改善）。仕様側は未必須のまま。
- 提案: `ai-tell-detector` 再呼び出し経路（または同一式の明示適用）を naturalness-reviewer.md に必須化。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

### IMP-007 ジャンル別許容基準（genre allowance）が SSOT・スキーマ・reviewer 仕様に無い `status: ready` `hits: 2run`
- 症状: 「につきましては／なお／及び／一貫した『ます』文末／過剰敬語」は、コラムなら即 AI でも公的文書では定型で半ば自然。現状 severity でしか強弱を表せず「本来 S1 だがジャンルで減格」という判断が reason 散文にしか残らず、レビュアーごとに計上がブレる。07-23 run 002（公的文書）で顕在化し、run 001 でも「技術文書での体言止め許容回数」「開けるカタカナのドメイン依存」として同型が出た。
- 出所: 07-23 detector-B, rewriter-B, naturalness-B, fidelity-B（run 002）＋ rewriter-A, naturalness-A（run 001）
- 提案: taxonomy 各カテゴリに「ジャンル別許容表」を付す、または finding に `genre_adjusted:bool`/`base_severity` を追加。meta に `genre` を持たせる。
- 影響: `ai-tell-taxonomy.md`, `ai-tell-detector.md`, `naturalness-reviewer.md`, `rewriting-playbook.md`

### IMP-008 品質等級表に閾値の谷間・単発文体崩れの取りこぼし `status: ready` `hits: 2run`
- 症状: (a) A は改善70%+/B は50%+ で、S1=0・S2=0 でも改善40%だと A でも B でも C でもない未定義ゾーン。(b) B は S2≤4 で、S2=5〜8 帯が無グレード。(c) 鉄則3で文体崩れは最重要違反なのに C 条件は「過推敲シグナル2個」で、常体混入1個だけだと降格せず A のまま通る。(d) score_after の絶対上限が無く短文で残存 S2×2 でも改善率だけで A になり得る。
- 出所: 07-23 naturalness-A（run 001）, naturalness-B（run 002）（別 run 再現）
- 提案: (a) 「S1=0 かつ過推敲0 だが改善率 B 未満」を B か C に落とす下限、(b) S2 上限超帯の扱い、(c)「深刻な過推敲（文体崩れ含む）1個で C 降格」、(d) A 判定に `score_after ≤ 10` 等の絶対上限を追記。
- 影響: `SKILL.md §品質等級`, `naturalness-reviewer.md`, `CLAUDE.md §品質等級`

### IMP-009 「拘束力（bindingness）」保存が #7 modality に埋没 `status: ready` `hits: 1run`
- 症状: 公的文書で「〜する必要がある（要件 must）」→「〜してください（依頼 please）」は法的・実務的に別物。07-23 f015「破損品はカウンターへ返却する必要がある」→「ご返却ください」は排他的要件が依頼へ格下げ。今回は直前の逆接「が」が排他を担保し pass だったが、担保表現が無い環境では「必須→お願い」の実害（利用者がポスト返却）が出る。
- 出所: 07-23 fidelity-B（run 002）
- 提案: #7 とは別に「拘束力保存」サブチェックを独立化。`必要がある/なければならない/規定文末` → `ください/いただきます` 変換時は、排他・禁止・唯一性を担保する周辺表現（逆接・限定・注意喚起）が同一 span 内に残るか必須確認。担保無しは自動フラグ。
- 影響: `content-fidelity-auditor.md`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **A-8 の 2 分割**: by-passive（〜によって）と **行為者省略受動（agentless passive）**（対策が講じられます／掲載されております／休館とされます）。公的文書で最頻だが `によって` を伴わず現 A-8 に厳密には非該当。★日本語固有。実例: run 002 講じられます/掲載されております/取り扱われるよう。`hits: 1` 出所 detector-B
- **A-6 下位: 官僚的状態化／決定済みモダリティ** 「動詞＋こととなりました／取り扱いとされます」。受動＋状態化の合成で行政文の決定的シグネチャ。「決定した／これから決める」の差が読者の受け止めを左右。実例: run 002 実施されることとなりました/延長される取り扱いとされます。`hits: 1` 出所 detector-B, fidelity-B
- **新カテゴリ K「過剰敬語・依頼定型の反復」** ★日本語固有。「ご了承／ご確認いただきますよう＋お願い申し上げます／いたします」の依頼定型反復。A〜J のどこにも受け皿が無い（設計思想は過剰敬語を重心と明記するのに欠落）。実例: run 002 お願い申し上げます×2/お願いいたします。`hits: 1` 出所 detector-B, naturalness-B
- **A-3b「〜することによって／ことで」手段節** 英語 by doing の直訳。A-3（を通じて）にも A-8 にも厳密に当たらず宙に浮く。実例: run 001 計算することによって/差し込むことで。`hits: 1` 出所 detector-A
- **C 系: redundant restatement**（06-12 起票、継続）叙述と箇条書きの二重記載。`hits: 1` 出所 detector-A(06-12)
- **D-7 ブログ結び呼びかけ公式** / **C-9 導入誘導定型**（06-12 起票、継続）。`hits: 1`

### fidelity チェックリスト追補
- **#14 接続語/フレーズ置換で序列・因果・価値・主張強度が新規付与されていないか** `status: done` `hits: 2run`。06-12 f019（並列→基盤の序列混入）に続き、07-23 f013（重要→不可欠の強度昇格）・f020（進化→普及の別義）で再現。**適用（2026-07-23, run 001）**: content-fidelity-auditor.md に #14 を追加。出所 06-12 fidelity-A ＋ 07-23 fidelity-A
- **削除専用サブチェック（deletion-recall / 真理条件寄与テスト）** `status: ready` `hits: 2run`。削除 span ごとに「読者が知り得なくなる事実」を問う。07-23 fidelity-A が「削除語が命題の真理条件に寄与するか」を operational test 化（可能形/重複ヘッジは削除可、数値/限定詞/行為者/出典は削除不可）。fidelity-B も deletion-recall で全 12 項照合。出所 06-12 fidelity-B ＋ 07-23 fidelity-A, fidelity-B
- **#12 等価近似語の統語的重み付け**: 中核述語（主動詞・主要述部）の置換は微差でも fail 寄り、連用修飾・装飾語の置換は近似許容。実例 f020(述語=危険)/f003 シームレス→滑らか(修飾=安全)。`hits: 1` 出所 07-23 fidelity-A
- **rationale の自己申告を証拠にしない**: diff の rationale に「意味等価・毀損回避」と書かれていても anchoring されず before/after の原文対照のみで判定。実例 f013/f020 は rationale で「回避済み」と主張しつつ実際は毀損。`hits: 1` 出所 07-23 fidelity-A
- **ロールバック後は文(sentence)単位で再照合＋round2以降は fidelity pass でも naturalness 再レビュー必須**。span 局所監査は隣接 span の相互作用が盲点。`hits: 1` 出所 07-23 fidelity(round2 再監査)
- #5論理関係 と #11情報追加 の責任境界を一意化（06-12、継続）。modality 強度を順序尺度化。

### playbook レシピ追補
- **公的文書レシピ（K）**: 受動→能動でも謙譲語尾（いたす/おる/申し上げる）は保持、依頼は「〜ください/〜いただきますよう」の丁寧命令を許容、定型接続（なお/につきましては）は全廃せず密度のみ低減、状態化は 1〜2 回残す下限。`hits: 1` 出所 07-23 rewriter-B
- **A-10 万能動詞の緩和は価値語を固定し動詞のみ入替（強度一致）**: `[価値語]+[万能動詞]` は価値語を一字も動かさず万能動詞だけ非万能動詞へ。実例 重要な役割を果たす→担う（欠かせない へ上げない）。`hits: 1` 出所 07-23 round2 rewriter
- **D-5 擬人化除去は「Nをφする→Nする」で概念語を温存**: 進化を遂げていく→進化していく。名詞ごと入替（進化→広がる）は概念置換で #12 に落ちる。`hits: 1` 出所 07-23 round2 rewriter
- **A-5 分散時は語彙変奏＋可能形ドロップで E-2 に同時対応**（できます連鎖回避に「実現します」等）。`hits: 1` 出所 07-23 rewriter-A
- **B-2 カタカナ開示時の意味衝突ガード**: 開いた和語が本文の他概念と衝突しないか確認（インジェクション→埋め込む は本文のエンベディング＝ベクトル埋め込みと衝突、差し込む を採用）。`hits: 1` 出所 07-23 rewriter-A
- C-5 絵文字削除後の吸収ルール / D 系結びは最小着地文を残す / 機能接続詞は変奏 / 元から推量の D 系は推量保持（06-12、継続）。

### naturalness 判定の精緻化
- **過推敲シグナルに register downgrade（体裁・格式の低下）を独立項目化**: 敬体のまま格式だけ落ちる（詳細につきましては→くわしくはこちら、ご返却ください→返してね）。公的文書で最頻の過推敲。`hits: 1` 出所 07-23 naturalness-B
- **過推敲シグナルの定量閾値化** `status: ready` `hits: 2run`: 二値配列でなく体言止め率/同一文末3連箇所数/削除:挿入比を持たせ、削除≫挿入=パディング剥離=過推敲でない を自動判定。出所 06-12 naturalness-A ＋ 07-23 naturalness-A
- **B-2 検出を語彙リスト照合→「開ける度×密度」の機械判定へ**: 残存レビューでも同一関数を使えば before/after 基準ズレが消える。`hits: 1` 出所 07-23 naturalness-A, detector-A
- クラスタ系降格ルール / E-2 到達ライン緩和 / 絶対残存数ガード（06-12、継続。IMP-008 に統合）。

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 2run`
- ルーティン・モチベーション・データドリブン等の定訳が冗長な語は B-2 から半免責し残差 S3 固定。07-23 で技術ドメインへ拡張が必要と再確認: エンベディング/クエリ/コサイン類似度/ハルシネーション/ベクトル等の**技術概念語は開かない**、アーキテクチャ/プロセスはグレー。ドメイン別免責辞書を references に。出所 06-12 3agent ＋ 07-23 detector-A, rewriter-A, naturalness-A（別 run 再現）

### detector 実装
- **silent-log 方針**: A-1/A-2/A-6 等の S1 パターンは単発でも必ずログに残す（severity は密度で減格可）。残存レビューが「検出漏れ」と「推敲漏れ」を切り分け可能に。実例 run 001 「アプローチにおいては」(A-1/S1) が before/after 双方で拾われず。`hits: 1` 出所 07-23 naturalness-A
- **density の重複は union で数える**と SSOT 明記（overlap span の二重計上回避）。`hits: 1` 出所 07-23 detector-A
- **反復系に `occurrence_count`/`all_positions:[]` フィールド**（密度と反復回数を両立）。`hits: 1` 出所 07-23 detector-A
- start/end 自己検証 / 絵文字正規表現レンジ明示（06-12、継続）。
