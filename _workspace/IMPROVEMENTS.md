# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-09-12（run 2026-09-12-001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B(06-12) は 54.6% で `hold_and_report` 誤発火。**再現(09-12)**: run 001=30.5%・run 002=31.6% がいずれも純削除主導（del≫ins, 挿入は各 41〜67字）で 30% 警告を微超だが fidelity=pass/自然度 A。削除主導では 30% 超が構造的に起きる。
- 出所: rewriter-A/B(06-12), rewriter-001/002・naturalness-001/002(09-12)
- 提案: (a) 「語句改変率(置換率)」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を change_rate から控除。(c) 挿入率を単独併記し、del≫ins の削除主導ケースは中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`
- 注: P0 だが redesign が SKILL/playbook/rewriter 横断で大きいため今回は未適用（override 運用継続）。次回、置換率分離の最小適用を優先候補とする。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: partial`（式の形のみ適用 2026-09-12, taxonomy v1.2）`hits: 2run`
- 症状: 正規化式が SSOT に無く、高密度短文で raw が張り付き深刻度の解像度が消える。**再現(09-12)**: 両検出器が独立に係数を恣意設定（001 は 5.0 校正で 71.1、002 は raw/input_length*500 で 69.2）。係数がハードコードで score がぶれる問題を再確認。
- 出所: detector-A/B(06-12), detector-001/002(09-12)
- **適用（式の形のみ）**: taxonomy v1.2 §検出出力スキーマに `severity_weighted_score = min(100, round(raw/input_length*500,1))` を明記。`meta.score_formula`・検算用 `meta.severity_weighted_raw` 併記を規定。`ai-tell-detector.md §スコア算出` も同式に更新。
- **taxonomist 審査で判明した重大点**: 旧スキーマ例 `71.5` は本式で数学的に到達不可能（S1×37 でも上限 50.8）→ 例を `raw=110→30.2` に訂正済。係数 500 では 0〜100 の上半分がほぼ死に、直感的「濃厚に AI≒70」と乖離。→ **係数校正は未確定 = IMP-002b(OPEN)** として分離。
- 影響（適用済）: `ai-tell-taxonomy.md §検出出力スキーマ・§バージョン管理`, `ai-tell-detector.md §スコア算出`

### IMP-002b score 正規化の係数校正が未確定 `status: open` `hits: 1run(taxonomist)`
- 症状: 係数 500 は run 001/002 採点済みだが、ヘビー AI 文でも score が 30 台に留まり scale 上半分が死ぬ。ヘビー AI を 70 台に置くなら係数 ≈1100〜1200 が必要（taxonomist 試算）。
- 出所: taxonomist(v1.2 審査)
- 提案: オーケストレーター／チームで anchor（ヘビー AI の目標 score）を合意 → 係数確定 → **全 run 再採点**。それまで 500 は暫定運用（絶対値でなく同一係数内の相対比較に使用）。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md`, 過去 run の 02_detection.json 再採点

### IMP-003 score_before のフィールド契約が曖昧 `status: ready` `hits: 1run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score 92.5）。レビュアーごとに数値がぶれる。
- 出所: naturalness-A
- 提案: 「score_before = 02_detection.json の meta.severity_weighted_score」と明文化。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: done`（適用 2026-09-12-001/002）`hits: 2run`
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。**再現(09-12)**: 両検出器が E-2/F-4/H-1 の文書横断 finding を「代表1箇所に錨付け＋reason に密度記載」で運用せざるを得ず、scope 規約の不在を再指摘。
- 出所: detector-A/B(06-12), detector-001/002・rewriter-001(09-12)
- **適用**: taxonomy v1.1 に `scope: "span"|"document"` と `occurrences:[[s,e],...]` を追加。density は occurrences の重複・広域 locator を実 AI クセ文字数へ正規化と定義。`ai-tell-detector.md §スキーマ規約` にも反映。
- 影響（適用済）: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: done`（適用 2026-09-12-001/002）`hits: 2run`
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。**再現(09-12)**: rewriter-001 が f014/f019・f005/f028・f013/f022・f011/f025 の 4 組で span 重複を報告、1 手術が複数カテゴリを解消し diff が 1:1 にならない問題を再確認。
- 出所: detector-A, rewriter-A/B, naturalness-A, fidelity-A(06-12), rewriter-001(09-12)
- **適用**: taxonomy v1.1 に「1 span = 主分類 1 finding」＋従属分類 `merged_findings:[...]`、category_summary は主分類のみ集計、density は非重複・複合分割を規定。`ai-tell-detector.md §スキーマ規約` にも反映。
- 影響（適用済）: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md`

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。**再現(09-12)**: naturalness-001/002 とも「サブエージェントから別サブエージェントを新規起動できない」環境制約で self_scan_estimate に。JSON に rescan_method を明記して運用。
- 出所: naturalness-A(06-12), naturalness-001/002(09-12)
- 提案: **オーケストレーター(main)側**が推敲文 03_rewrite.md に対し ai-tell-detector を再実行し、その severity_weighted_score を naturalness へ渡す設計へ変更（sub→sub 起動不可のため naturalness 内での再呼び出しは非現実的）。score_after を絶対残存数（S1/S2/S3 件数）と必ず併読する規約も明記。
- 影響: `SKILL.md §総合判定`（オーケストレーター手順に「推敲後 detector 再走査」を追加）, `naturalness-reviewer.md §処理`
- 注: 環境依存の構造課題。次回オーケストレーター手順の最小改訂候補。

### IMP-007 受動一律能動化が証拠性ヘッジを毀損する `status: ready` `hits: 1run(2agent)`
- 症状: 公的文書で A-8 受動を一律能動断定化すると、証拠性ヘッジ（〜とされる/〜と見られる/〜とされてきた）まで事実断定へ格上げしてしまう。run 002 で「聞き取りにくいとされていた→かった」が fidelity=fail（S2, 市が自らの旧設備不良を客観事実として断定）。round2 で「とされてきた」へロールバック復旧。
- 出所: detector-002, fidelity-002, rewriter-002（同一 run 3 エージェント）
- 提案: (a) 検出段階で「証拠性ヘッジ保護タグ」— 自己役務品質・責任記述に隣接する伝聞受動は断定化禁止。(b) fidelity checklist に「他動受動→自動詞化で行為者(責任主体)が消えていないか」を独立フラグ化（run 002 の停止される→停止する は無害だったが文脈次第で責任回避の含意）。(c) I-3/I-4 の要請強度チェックを双方向化（弱化だけでなく強化=推奨→指示も監査。run 002 e021）。
- 影響: `ai-tell-taxonomy.md A-8`, `ai-tell-detector.md`, `content-fidelity-auditor.md`, `rewriting-playbook.md A-8`
- **適用（taxonomy v1.2）**: taxonomist が安全修正として即適用。A-8 を「by-passive + 行為者省略受動（〜される）」に定義拡張し、**証拠性ヘッジ（〜とされる/〜と見られる/〜とされてきた）を保護タグ=断定化禁止**として本体に明記（run 002 の再発防止）。単発受動は自然として密度反復ゲートも明記。
- 残（未適用）: fidelity checklist への「他動受動→自動詞化フラグ」「I-3/I-4 強度双方向監査」は content-fidelity-auditor.md 側で次回適用候補。

### IMP-008 定義文の被定義項核名詞を I-5 で開いて毀損 `status: done`（適用 2026-09-12-001）`hits: 1run`
- 症状: I-5「能力/力を動詞へ開く」処方が、「〜とは〜を指す」型定義文の被定義項核まで削除。run 001 で「推測する能力を指す→推測することを指す」が fidelity=fail（能力(属性)→こと(行為)へ質的ズレ）。round2 で「能力」復元。
- 出所: fidelity-001, rewriter-001
- **適用**: `rewriting-playbook.md I-5` に例外規定「定義文の被定義項核（能力/可能性/度合い/性質/手法 等）は開かない、冗長は『〜のこと』だけ削る」を追記。
- 追加提案（未適用）: fidelity 13 項に **#15「定義文・言い換え文の中核語保存」** を独立追加（fidelity-001）。「〜とは〜を指す/である」型で述語核名詞を保護対象に明示。次回適用候補。
- 影響: `rewriting-playbook.md I-5`（適用済）, `content-fidelity-auditor.md`（#15 未適用）

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 001(06-12)。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B
- **新カテゴリ K「過剰敬語・官公庁定型」** 賜り/賜りますよう/お願い申し上げます/認識しております/ご迷惑をおかけする場合がございます。公的文書 AI 模倣の決定的兆候。実例 run 002(09-12) で 2 エージェント再現。taxonomy 拡張候補欄に記載済。 `hits: 1run(2agent)` 出所 detector-002, rewriter-002
- **H-1 亜種: 段落メタ橋渡し語** 「具体的には/これにより/このように」が各段落の論理接続を機械的に担う。実例 run 001。 `hits: 1` 出所 detector-001
- **過剰確信クロージング** 「〜に違いありません/〜に他ならない」締めだけ断定を誇張（G の逆）。D-6 隣接。実例 run 001。 `hits: 1` 出所 detector-001
- **C-8 単発版「単なる〜ではなく、〜だ」対比フレーム** AI コラム結びの頻出。1 回でも S3 化する案。実例 run 001。 `hits: 1` 出所 detector-001

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
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。出所 detector-A → **適用済 v1.1**（ai-tell-detector.md §スキーマ規約）
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B
- **suggested_fix は meta.style（敬体/常体）に合わせて生成**（run 001 で f024/f026 が敬体入力に常体 fix を提案、文体維持則と衝突）。出所 rewriter-001 → **適用済 v1.1**（taxonomy §スキーマ, ai-tell-detector.md）
- **A-10 推敲テンプレは万能動詞の除去に留め、原文にない目的語・効果を補完しない**（run 001 f014 suggested_fix「大きなメリットをもたらす→負担を減らす」が原文にない主張を追加、rewriter が正しく不採用）。出所 rewriter-001, fidelity-001。次回 playbook A-10 に明記候補。
- B-1 単独初出併記（1 回のみ）は検出しない閾値を入れると過検出減。出所 rewriter-001
- A-6 playbook 行に敬体版 After 例（〜です/〜になります/〜のです）を併記。出所 rewriter-001
- modality 変換の許容閾値を fidelity checklist 7 に明文化（主張核保持＋強度変化が原文確信度レンジ内なら pass）。出所 fidelity-001
