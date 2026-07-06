# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-07-06（run 001 ベクトルDB技術解説, 002 公的お知らせ）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B(0612) は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。
- 出所: rewriter-A/B(0612), naturalness-B(0612), rewriter-001/002(0706)
- 0706 追記: 両 rewriter が自発的に **分離報告（語句改変率 / 構造・削除率 / 挿入率 / similarity）** を実施。001=19.8%(語14.6/削4.7/挿0.5)、002=22.3%(語11.7/削8.6/挿1.9) といずれも 30% 未満で誤発火せず。分離指標の有効性を再確認。ただし**分母定義が未統一**（001 は 845字=本文＋タイトル、002 は 741字=空白除外、naturalness は 738/697字）で前後比較がぶれる。
- 提案: (a) 分離報告（lexical/deletion/insertion）を **03_rewrite_diff.json の正式スキーマに昇格**。(b) 50% 中断は「意味改変 edit 比率」基準に置換。(c) 分母定義（本文のみ／空白・改行・タイトルの扱い）を SSOT で一本化。
- 影響: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`

### IMP-002 severity_weighted_score の正規化が未定義で監査官ごとに非互換 `status: done`（適用 2026-07-06-001/002, taxonomy v1.1）`hits: 2run`
- 症状: 正規化式が SSOT に無く、検出器ごとに独自式を採用 → **スコアが run 間で非互換**。0706 では detector-001 が飽和関数 `100×(1−exp(−d/50))`（→89.2）、detector-002 が密度基準 `加重和/字数×1000`（→59.8）と別式を採用。0612 も raw106→92.5 と例 raw56→71.5 が不整合。
- 出所: detector-A/B(0612), detector-001/002・naturalness-001/002(0706)
- 適用（v1.1）: `severity_weighted_score = 100×(1−exp(−W/K))`, W=Σ(S1×5+S2×2+S3×0.5), **K=40 固定**, 分母は input（タイトル含む本文, 末尾改行除外）。飽和により高密度短文でも解像度を保ち、長さ非依存。taxonomy §検出出力スキーマ・ai-tell-detector.md に明記。
- 残: 過去 run の 92.5/71.5 は旧アドホック値。今後は v1.1 式で算出。

### IMP-003 score_before のフィールド契約が曖昧 `status: done`（適用 2026-07-06-001/002）`hits: 2run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 92.5）。
- 出所: naturalness-A(0612), naturalness-001/002(0706 はいずれも 89.2 / 59.8 と meta 値に固定して報告)
- 適用: 「score_before = 02_detection.json の meta.severity_weighted_score」を `naturalness-reviewer.md` と taxonomy に明文化。0706 は両レビュアーが既にこの契約で運用しており回帰なし。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: done`（適用 2026-07-06-001/002, taxonomy v1.1）`hits: 2run`
- 症状: 絵文字分散・文末単調(E-2)・まず…最後に(C-1) は分散/文書レベル。単一 start/end では広域 locator にせざるを得ず、代表 anchor では start/end が現象範囲を表さない。
- 出所: detector-A/B(0612), detector-001/002(0706 ともに E-2/C-1 の anchor 運用に苦慮と報告)
- 適用（v1.1）: finding に `span_type: "contiguous"|"scattered"|"document"`（省略時 contiguous）と、scattered 用 `occurrences: [[s,e],...]` を追加。document レベルは代表 anchor + `span_type:"document"` を許容し density 計算から除外。taxonomy §スキーマ・ai-tell-detector.md に明記。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリに該当（0612: I-4＋B-2＋I-1／0706: A-6＋I-4「必要となりますので」, A-5＋G-1「引き出すことが可能」, A-8＋G「推奨されます」）。category_summary が実態を過小/過大表示。
- 出所: detector-A/rewriter-A/B/naturalness-A/fidelity-A(0612), detector-001/002・fidelity-001/002(0706)
- 提案: 「1 span = 主分類 1 finding」を基本とし `merged_findings:[...]` または副カテゴリ欄を許容。category_summary は「主分類の先頭文字を集計」と注記。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」。0706 は naturalness-001 が自己適用（実 detector 未走）、naturalness-002 は子 detector を呼んだが `run_in_background:false` 指定でも非同期化し、完了前に返って **オーケストレーターが SendMessage で催促・再開**する二度手間が発生。
- 出所: naturalness-A(0612), naturalness-001/002(0706)
- 提案: (a) レビュアー内で regex 一次スイープ→子 detector は cross-check に限定、の運用フローを明文化。(b) 子 detector を synchronous 前提にできない環境向けに「レビュアーが最終 JSON を必ず自力で書き切る」ことを必須化（0706 で顕在化）。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

### IMP-007 過剰敬語・敬度に専用カテゴリが無い `status: candidate` `hits: 1run`
- 症状: CLAUDE.md・taxonomy 序文は「(2) 過剰な丁寧体・敬語」「硬い過剰敬語」を日本語固有の重心・ターゲットに挙げるが、A〜J に受け皿サブ項目が存在しない。0706-002 で「〜いただく＋必要＋ございます」の二重敬語や「賜りますよう」型の結びが行き場を失い、I-3 へ寄せる／検出見送りの折衷になった。公文書では敬度が「要請の公式度」という準・意味情報を帯びる（fidelity-002 も指摘）。
- 出所: detector-002, fidelity-002(0706)
- 提案: 過剰敬語の専用カテゴリ（例 K/敬語過多）または I 系サブ項目（I-6 二重敬語・過剰敬体）を新設。fidelity ↔ naturalness の「敬度=意味」受け渡しルールも併せて定義。**再現待ち（別 run で 2 回目を確認し次第 ready）**。
- taxonomist 審査(0706): taxonomy 拡張候補欄に **候補 K-01** として実例 2 件付きで登録済み。hits=1run のためサブ項目昇格は保留。

### IMP-008 A-8 の定義が「によって」by-passive に限定され agentless 受動を含まない `status: candidate` `hits: 1run`
- 症状: taxonomy A-8 は「〜によって」を伴う受動に限定。実データで最頻出なのは **行為者省略の agentless 受動**（実施されます／掲載される予定です／図られる、いずれも「によって」無し）。0706-002 の A-8 5 件は全て agentless。公文書では agentless 受動が自然な場合もあり S1/S2 閾値・過検出境界も曖昧。
- 出所: detector-002, naturalness-002(0706)
- 提案: A-8 定義に「行為者省略受動（agentless passive）」を明記して包含。ジャンル（公的文書）での許容度に応じた severity 調整注記を付す。**再現待ち**。
- taxonomist 審査(0706): taxonomy 拡張候補欄に **候補 A-8ext** として実例 2 件付きで登録済み（A-8 の新設ではなく定義拡張として）。hits=1run のため昇格は保留。

---

## P2 — 分類・レシピ・チェックリスト

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019(0612) 由来。`status: ready` `hits: 1`
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。`status: ready` `hits: 1`（0706 の「まず／そのため」削除は情報欠落なしと確認され本手法の有効性は追認）
- **#15 強度弱化（degradation）専用判定** ← **0706 新規・cross-agent**。現行 13 項は「強化しすぎ」を主に見るが、(a) 義務/推奨マーカーの一律削除・軟化（fidelity-002: 必要→ください）(b) 評価的強調語(intensifier)の削除（fidelity-001: 欠かせない削除）による **claim strength の低下** を測る受け皿が無い（#7 modality は断定/推量/義務、#6 量化は量化子に限定）。義務・推奨・評価強度の低下を独立サブ項目化し、条件節による任意性の担保有無をセットで判定。`status: ready` `hits: 1run(2agent)` 出所 fidelity-001/002
- **evidential（証拠性）項目** 「有用性が示されている（実証）」→「役立っている（直接断定）」は証拠性ニュアンスの喪失を伴うが #7 にも #13 にも収まらない。`status: candidate` `hits: 1` 出所 fidelity-001
- **span 重複時は合成後テキストで再検証** 複数 edit が同一 span を処理した場合、重畳後の最終文で原意保持を再確認するステップを明示。`status: candidate` `hits: 1` 出所 fidelity-001
- 「情報を含む削除 vs ボイラープレート削除」二分判定（0612）。#5論理関係 と #11情報追加 の責任境界一意化（0612）。modality 強度を順序尺度化（0612）。

### playbook レシピ追補
- **C-5 絵文字削除後の文末/区切り吸収ルール**（0612）。
- **D 系結びは削除一択でなく「最小着地文を残す」**（0612）。
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**（0612）。
- **原文が元から推量の D 系は推量を保持**（0612）。
- **D-4 ハイプ語の削除 vs 情報欠落の線引き** 「欠かせない／極めて重要」等の評価的強調語は、削除＝ハイプ除去（命題保存なら可）、ただし残余リスクを note 記録。追加(捏造)と削除(減衰)で毀損閾値が非対称である旨を原則に明記。`status: ready` `hits: 1` 出所 rewriter-001/fidelity-001(0706)
- **公的文書ジャンルの依頼表現フロア** I-3/A-8 を「ください」に開くと命令寄りになる。公的お知らせでは文末に依頼定型（〜いただきますよう等）を 1 つ以上維持する下限を例示。`status: candidate` `hits: 1` 出所 rewriter-002/naturalness-002(0706)

### naturalness 判定の精緻化
- **クラスタ系 finding（B-2 密集・C-1 列挙）はクラスタ崩壊時に個別 severity を降格するルール** `status: ready` `hits: 2run`。0706 追認: naturalness-001 が E-2 を変奏導入後 S2→S3 降格、detector-002 が単発「まず」を C-1 の S1→S2 格下げ。**降格の可否基準（変奏を何件入れれば降格可／単発時の severity）が属人的**なので数値ルール化。出所 naturalness-A(0612), naturalness-001/detector-002(0706)
- 過推敲シグナルの定量化（敬体/常体は文末形態の二値カウント）。ます終止率の指標化（0706 naturalness-001: 15/17≒88%、体言止め箇所数の閾値未定義）。出所 naturalness-A(0612), naturalness-001(0706)
- E-2 文末単調の到達可能ライン緩和（体言止め1箇所以上で合格）。出所 naturalness-B(0612)
- 絶対残存数ガードを grade 表に組込み（S1 が1件でも C 以下）。出所 naturalness-A/B(0612)

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 1run(3agent)`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B/fidelity-A/naturalness-A(0612)

### B-2 業界標準語 vs 不要カタカナ の境界表 `status: candidate` `hits: 1`
- 0706-001: アーキテクチャ／レコメンド／チューニング等がグレー。例外リスト（Transformer/API/SDK/トークン）だけでは判断しきれない。ドメイン別許容リストか判定粒度を taxonomy に用意。出所 detector-001

### ジャンル別「定型ホワイトリスト」 `status: candidate` `hits: 1`
- 0706-002: 公文書では A-2「について」「なお」「必要があった」等が正当な定型なのに AI クセ語形と表層一致。過検出禁止（密度閾値・object marker 判定・suggested_fix 一致除外）をジャンル別に効かせる。出所 detector-002/naturalness-002

### detector 実装
- start/end 自己検証（0612・0706 とも全 span で実施し不一致 0 を達成、有効性確認）。出所 detector-A(0612), detector-001/002(0706)
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`（0612）。
- カテゴリ多重該当時の主/副分類ルール（IMP-005 と連動、category_summary 過小表示を回避）。出所 detector-001/002(0706)

### 新パターン候補（taxonomist 審査待ち, 0612 起票）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。`hits: 1` 出所 detector-A(0612)
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」等。`hits: 1` 出所 detector-B(0612)
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式。`hits: 1` 出所 detector-B(0612)
