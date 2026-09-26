# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-09-26（run 001 技術解説記事, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B(0612) は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。
- 再現(0926): rewriter-001 が B-2 の等長置換（パフォーマンス5字→性能2字 等）で delete が過大計上される傾向を再指摘。今回は語句置換中心のため 0.275/0.210 と実感に近く hold は不発火だったが、指標の構造的偏りは同一。
- 出所: rewriter-A(0612), rewriter-B(0612), naturalness-B(0612), rewriter-001(0926)
- 提案: (a)「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を change_rate から控除。(c) 挿入率を単独併記し del≫ins の削除主導ケースは中断対象から除外（今回 rewriter は insert/delete/rate を meta に併記済み＝この運用を標準化）。(d) 50% 中断は「意味改変 edit 比率」基準に置換。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`

### IMP-002 severity_weighted_score の正規化が未定義で値が run 間・agent 間でぶれる `status: done`（適用 run 2026-09-26-001/002）`hits: 2run`
- 症状: 正規化式が SSOT に無く、各 agent が係数を独自に逆算。0926 では detector-001 が指数飽和 100×(1−e^(−raw/40)) で raw92→90.0、detector-002 が線形 raw×100/66 で raw30→45.5 と**別式を採用**し、reviewer は score_after を確定できず推定値に留まった（IMP-006 の遠因）。
- 出所: detector-A/B(0612), detector-001/002(0926), naturalness-001/002(0926)
- **適用(0926)**: `ai-tell-taxonomy.md §検出出力スキーマ` に正規化式を SSOT として固定（飽和関数 `score = 100×(1−e^(−raw/40))`, raw = S1×5+S2×2+S3×0.5）。参照 raw106→92.9(≈92.5) / raw92→90.0 と整合。`ai-tell-detector.md` にも同式を明記。以後の detector は全てこの式で算出。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出`

### IMP-003 score_before のフィールド契約が曖昧 `status: ready` `hits: 1run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score）。
- 補足(0926): reviewer 呼び出し時に「score_before = 02_detection.json の meta.severity_weighted_score」を明示指示し、両 reviewer とも準拠（90.0 / 45.5）。SSOT 明文化は IMP-002 適用に同梱するのが最小コスト。運用では機能しているため P0 内で優先度は低。
- 出所: naturalness-A(0612)
- 提案: 「score_before = 02_detection.json の meta.severity_weighted_score」を naturalness-reviewer.md に明文化。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

### IMP-006 naturalness-reviewer が検出器をサブエージェントとして再実行できない `status: done`（適用 run 2026-09-26-001/002）`hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だが、reviewer 自身がサブエージェントのため detector を spawn する Task 系ツールが無く（0926 で naturalness-001/002 の**両者が実証**）、score_after が推定値に落ちる。
- 出所: naturalness-A(0612), naturalness-001/002(0926)
- **適用(0926)**: サブエージェントは別サブエージェントを起動できないという環境制約を前提に `SKILL.md §4` を改訂——「オーケストレーターが推敲文に対し ai-tell-detector を 6 回目として実走査し、その結果を naturalness-reviewer に渡す」経路を正とした。reviewer 側が spawn 不能な場合は同一基準の正規表現/機械照合で代替し `score_after_method: "estimated"` を必須記録（実走査時は `"detector_measured"`）とスキーマ拡張。`naturalness-reviewer.md` に手順を明記。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md §4`, `ai-tell-taxonomy.md §出力スキーマ(05)`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run`
- 症状: 絵文字分散・文末単調(E-2)・まず…最後に(C-1) は分散/文書レベル。単一 start/end では便宜的に start=0/end=input_length を充てるしかなく text_span が実テキストと不一致になり、rewriter が「その1箇所だけ直せばよい」と誤読しうる。
- 再現(0926): detector-001（E-2 に start=0/end=841 を便宜充当）, detector-002（同 point 6）, rewriter-002（E-2 は複数 edit にまたがり 1finding=1edit と相性が悪い）, naturalness-001（residual_detail に S3 由来が追えない）。
- 出所: detector-B/A(0612), detector-001/002・rewriter-002・naturalness-001(0926)
- 提案: `scope: "span"|"scattered"|"document"` と scattered 用 `occurrences: [[s,e],...]` を追加。文書レベル finding は density 計算から除外と規定。diff 側は「文書レベル finding は複数 edit にまたがる/代表 edit 1件へ集約」の標準を決める。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`, `japanese-style-rewriter.md`

### IMP-005 span 重複時の finding/edit・density カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリに該当（I-4＋B-2＋I-1 等）。edits/findings 1:1 前提で category_summary が過小評価。density も重複区間の単純和で 1.0 超・二重計上しうる。
- 再現(0926): detector-001 が「A-6×B-2 隣接・A-10×B-2 重複」で density を union（和集合）で算出した旨を報告し、SSOT に「重複は和集合で数える」明記を要請。
- 出所: detector-A・rewriter-A/B・naturalness-A・fidelity-A(0612), detector-001(0926)
- 提案: 「1 span = 主分類 1 finding」を基本とし `merged_findings: [...]` を許容。density は「検出 span の**和集合**文字数 / 全体」と SSOT 明記。
- 影響: 全 .md のスキーマ節, `ai-tell-taxonomy.md §スキーマ`

---

## P2 — 分類・レシピ・チェックリスト

### taxonomy 昇格候補（taxonomist 審査）

- **D-7 結びの呼びかけ/勧誘公式** 「今回は〜ご紹介しました」「〜してみてはいかがでしょうか」「素敵な〜を応援しています」。`status: done`（v1.1 昇格、適用 run 2026-09-26）`hits: 2` 出所 detector-B(0612「いかがでしたでしょうか」型), detector-001(0926「検討してみてはいかがでしょうか」)。→ D-1 の署名例へ勧誘型を追加し taxonomist が v1.1 化。
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。実例: 001(0612)。 `hits: 1` 出所 detector-A(0612)
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B(0612)
- **A-8b 無主語受動の連鎖（agentless passive stacking）** [新] 行為者マーカー無しの受動が主節述語を 3 文以上占める（技術記事「変換され/実行されます/渡されることになります」・公的文書「実施されます/行われる/確認された」）。現行 A-8 は「〜によって/より」の by-passive 限定で無主語受動を拾えない。 `status: candidate` `hits: 1(3agent)` 出所 detector-001・detector-002・rewriter-002(0926)。実例 run 001/002 に多数。→ A-8 定義に「(b) 行為者省略の無主語受動連鎖」を追記＋能動化レシピ（主体を補って能動化 / 自然受動は残す）を提案。
- **K（またはE-4）過剰敬語・定型敬語の過積層** [新] 「賜り」「〜ております」「におかれましては」「申し上げます」「ご確認いただく必要がございます」（尊敬＋謙譲＋硬い存在動詞の積層）。taxonomy 設計思想は「過剰な丁寧体・敬語」を 4 大重心の一つに挙げるのに専用カテゴリが無く、I-3/E-2/A-8 へ分散している。 `status: candidate` `hits: 1(2agent)` 出所 detector-002・rewriter-002(0926)。実例 run 002。深刻度は密度ベース S2、公的文書では単発許容の注記付き。要 taxonomist 審査。
- **I-3 の敬語変種「〜する必要がございます」** [新] I-3 の例は常体「〜する必要がある」のみ。公的文書 AI 文では敬語化変種が高頻度反復（run 002 で 4 回）。 `status: candidate` `hits: 1(2agent)` 出所 detector-002・rewriter-002(0926)。→ I-3 の例・処方に敬語変種と「敬体を保った依頼形（〜ください/お願いいたします）への変奏」を追記。

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019(0612) はこの項が無く #5/#11 へ漏れ込んだ。`status: ready` `hits: 1` 出所 fidelity-A(0612)
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。`status: ready` `hits: 2` 出所 fidelity-B(0612), fidelity-002(0926: 「なお」削除・I-3 依頼形化で計104字削除、公的文書は"触れられていない=免責されない"含意が命のため削除リコールを明示ステップ化すべき)。
- **要請 modality の強度保存（義務/必要/依頼/推奨の階層移動チェック）** [新] #7 は「原意を超える強化」主眼だが、公的文書では逆方向「義務→依頼への過剰軟化」も監査対象。 `hits: 1` 出所 fidelity-002・fidelity-A(0612 modality 順序尺度化)。
- **能動化後の暗黙主語の含意一致** [新] #9 は誤った行為者付与を見るが、能動化で主語省略時に「読者(住民)が主体と誤読される」リスクを見る観点が薄い。 `hits: 1` 出所 fidelity-002(0926)
- **第14〜16項候補: 文体/丁寧度・焦点構造・語用論的機能の保持** [新] 敬体/常体・硬度、分裂文の焦点移動、勧誘/警告など発話行為タイプの等価性。 `hits: 1` 出所 fidelity-001(0926)
- 「情報を含む削除 vs ボイラープレート削除」二分判定。出所 fidelity-B(0612)
- #5論理関係 と #11情報追加 の責任境界を一意化。出所 fidelity-A(0612)

### playbook レシピ追補
- **B-2 変換表の欠落語を昇格** [新] テクノロジー→技術／コンテンツ→内容／パフォーマンス→性能／ナレッジ→知識／アウトプット→出力／クリティカル→重要／コア→中核／インフラストラクチャ→基盤。現行表はシームレス・ソリューション等のみ。 `status: ready` `hits: 1(但し高実用)` 出所 rewriter-001(0926)。低リスクで即適用可。
- **A-13×B-2 合流レシピ** 「というテクノロジー」→複合名詞化（ベクトルデータベース技術）。A-13 の After は単純削除だけでなく (a)削除 (b)複合名詞化 (c)括弧化 (d)「と呼ばれる」化 の選択肢。 `hits: 1` 出所 rewriter-001(0926)
- **A-10 抽象主語解体で最上級・程度限定を副詞化保持** 「最大の」→「何より/最も」で情報欠落を防ぐ。 `hits: 1` 出所 rewriter-001(0926)
- **F-2 二重修飾は真の同義かを確認、概念が異なれば削除せず軟化に留める** 「安全かつ安定的な」= 水質の安全 と 供給の安定 の別概念。片方削除は情報損失。 `status: ready` `hits: 1(2agent)` 出所 rewriter-002・fidelity-002(0926)
- **公的文書ジャンルのレシピ節が丸ごと欠如** 冒頭御礼・結び依頼の定型は格として温存、本文中の反復のみ整理。E-2 で「変えてよい文末/触れてはいけない定型結句」の線引きが要る。 `status: ready` `hits: 1(2agent)` 出所 rewriter-002・naturalness-002(0926)
- **体言止めは politeness 中立（敬体文中で使用可）を E-2 に明記** 監査での「常体化=文体違反」誤判定を防ぐ。 `hits: 1` 出所 rewriter-001(0926)
- **C-5 絵文字削除後の文末/区切り吸収ルール**。出所 rewriter-B(0612)
- **D 系結びは削除一択でなく最小着地文を残す**。出所 rewriter-B・naturalness-B(0612)
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**。原文が元から推量の D 系は推量を保持。出所 rewriter-A(0612)

### naturalness 判定の精緻化
- **過推敲シグナルの定量閾値化** 体言止め率>15%・平均文長<20字・敬体文書での常体混入率>0%・口語マーカー出現数・文末 n-gram 分散。現状は定性語のまま reviewer 主観依存。 `status: ready` `hits: 2` 出所 naturalness-A(0612), naturalness-001(0926)
- **等級表: 絶対残存数と改善率の優先規則** 短文で改善率が乱高下/過大(99.4%)に出るケース、S1=0∧S2≤2 なら改善率不問で A、等の絶対数優先ルールと S3 件数の等級への反映が未規定。 `status: ready` `hits: 2` 出所 naturalness-A/B(0612), naturalness-001/002(0926)
- **S2→S3 降格の密度閾値を SSOT 化** 「反復3回未満で S2→S3」等。属人的降格の再現性リスク。 `hits: 1` 出所 naturalness-001(0926)
- **residual_detail を正式スキーマへ昇格**（finding_id と「解消/降格/未対応」の対応）。 `hits: 1` 出所 naturalness-001(0926)
- **ジャンル×パターンの finding 免除ホワイトリスト** 公的文書の定型（御礼申し上げます等）がコラム基準の D-1/E-2 と外形一致。genre 別免除表が要る。 `hits: 1` 出所 naturalness-002(0926)
- E-2 文末単調の到達可能ライン緩和（体言止め1箇所以上で合格）。出所 naturalness-B(0612)

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 2run`
- ルーティン・モチベーション・データドリブン等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。維持リスト（アーキテクチャ・スケーラビリティ・ユースケース・API・SDK・トークン・GPU 等）を taxonomy B-2 に明示列挙し、reviewer が同一基準で残存を数えられるようにする。 出所 naturalness-B・fidelity-A・naturalness-A(0612), naturalness-001・detector-001(0926)

### severity の genre 依存 `status: candidate` `hits: 1`
- A-2「について/につきまして」は S1 だが公的文書では単発自然で S1 適用は過検出。「基準値＋genre補正」の二層、または各パターンに genre 別許容注記。 出所 detector-002(0926)

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert）。0926 で detector-001/002 とも全 span 自己検証を実施＝運用定着。出所 detector-A(0612), detector-001/002(0926)
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B(0612)
- **B-2 発火の二条件化** 「日本語代替語が自然に存在」かつ「文書内カタカナ密度が閾値超」。記事ジャンル差（技術記事は許容度高）に応じた過検出制御。 `hits: 1` 出所 detector-001(0926)
