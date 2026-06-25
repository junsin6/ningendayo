# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-06-25（run 2026-06-25-001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done` `hits: 2run(8agent)` `applied: 2026-06-25-001/002`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B(06-12) は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。
- 再現(06-25): rewriter-A 001 span 0.36 vs naive 0.54、rewriter-B 002 span 0.277 vs naive 0.432、naturalness-A/B も同構造を指摘。**別 run で再現したため ready→done へ昇格・適用**。
- 出所: rewriter-A, rewriter-B, naturalness-A, naturalness-B（2 run 横断）
- **適用内容(v1.1)**: 主指標を `span_grounded_change_rate`（finding 紐付き span の実改変文字数／原文長）に変更、`naive_diff_change_rate` を参考に降格。強制中断は `substitution_rate`（意味改変比）> 0.50 のときのみ。純削除主導は `override_candidate` で委ねる。diff meta に 4 指標を出力。
- 編集ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`（すべて適用済み）

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2run(4agent)` `applied: 2026-06-25-001/002`
- 症状: 正規化式が SSOT に無く、各エージェントが場当たり係数を使用。
- 再現(06-25): detector-A 001 は線形 K=119.8 逆算で 88.9、detector-B 002 は exp 式で 82.6、naturalness-B 002 は線形 raw×1.62 で 82.6 と**同一文書を別式で算出**。指標が再現不能であることを実証。**別 run で再現したため適用**。
- 出所: detector-A, detector-B, naturalness-A, naturalness-B
- **適用内容(v1.1)**: 飽和型 `score = round(100×(1−exp(−raw/K)),1)`, `K = max(20, input_length/100×5)`（原文長固定・before/after 再利用）を taxonomy §スキーマで確定。detector は `raw_weighted_sum`/`normalization_K`/`score_formula` を meta 必須出力。taxonomist が v1.1 として審査・承認（OK 判定）。
- 編集ファイル: `ai-tell-taxonomy.md §検出出力スキーマ`（v1.1）, `ai-tell-detector.md §スコア算出`（適用済み）

### IMP-003 score_before のフィールド契約が曖昧 `status: done` `hits: 2run(3agent)` `applied: 2026-06-25-001/002`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。レビュアーごとに数値がぶれる。
- 再現(06-25): naturalness-A 001 は K=119.8、naturalness-B 002 は k≈1.62 を**逆算**して整合を取った（自走時は再現不能）。
- 出所: naturalness-A, naturalness-B
- **適用内容(v1.1)**: 「score_before = 02_detection.json の meta.severity_weighted_score（唯一の出所）」を明文化。score_after は推敲前の `meta.normalization_K` を**再利用**（逆算禁止）。IMP-002 と同じ K 固定で before/after を同一基準化。
- 編集ファイル: `naturalness-reviewer.md §処理`, `ai-tell-taxonomy.md`（適用済み）

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run(4agent)`
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
- 再現(06-25): detector-A/B とも E-1/E-2 を代表1文の span に「借用」せざるを得ないと報告（document スコープ未対応）。**昇格条件充足、次サイクルで適用候補**。
- 出所: detector-B, detector-A（2 run）
- 提案: `scope: "span"|"document"`（document は start/end=null 許容）と scattered 用 `occurrences: [[s,e],...]` を追加。density は重複・locator を除いた実 AI クセ文字数ベースと定義。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run(8agent)`
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 / A-5＋A-6 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。
- 再現(06-25): detector-B 002「取得することが可能となります」が A-5/A-6 で同一範囲 178-185 を二重計上、rewriter-A/B も入れ子 finding の統合に `finding_ids[]`/`merged_into` を要望、fidelity-A も no-op edit 混在を指摘。
- 出所: detector-A/B, rewriter-A/B, naturalness-A, fidelity-A（2 run 横断・最多）
- 提案: 「1 span = 主分類 1 finding」を基本とし、`finding_ids: [...]`（多対一 edit）と `overlaps: [id]` を許容。no-op（before==after）は `preserved_findings` に分離。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: done(partial)` `hits: 2run` `applied: naturalness-reviewer.md 明文化(2026-06-25)`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。
- 再現(06-25): naturalness-A/B とも今回は detector を再走査して数値を出したが、シード/基準ドリフト管理が無く category 定義バージョンの固定が必要と報告。
- 出所: naturalness-A, naturalness-B
- 適用(部分): naturalness-reviewer.md §処理に「手動推定禁止＝検出器再走査」を明記。残課題: 走査時の taxonomy version 固定記録（次サイクル）。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

---

## P2 — 分類・レシピ・チェックリスト

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
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。出所 detector-A `hits: 2`（06-25 両 detector が全件 assert 実施）
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B

---

## 2026-06-25 追加（run 001 技術解説 / 002 公的文書）

### 新パターン候補（taxonomy 拡張候補欄に記入済み・昇格は再現2回待ち）
- **C-001 過剰丁寧の公的儀礼定型** 「賜り／厚く御礼申し上げます／所存でございます／〜していただきますようお願い申し上げます」。公的文書 AI の決定的シグネチャ。**人間の実務家も使うため昇格時も S2 止まり・単独 S1 禁止**。D-1（ブログ結び）とは別物、昇格時は D-7 以降 or I-6 として新設。実例: 002。`hits: 1` 出所 detector-B, taxonomist
- **C-002 「〜つつある」進行相ヘッジ** 「崩壊しつつある／スタンダードになりつつある／基盤となっていく」。A-6（静的状態叙述）と軸が違う動的進行相の婉曲。G 系候補。実例: 001。`hits: 1` 出所 detector-A
- **C-003 「〜とされています」伝聞・証拠性ヘッジ** 出典/行為者を曖昧にした受動伝聞。**断定への格上げが fidelity 毀損 f035b を誘発**。昇格時の処方は「断定化」でなく「留保保持＋出典明示」。`fidelity_risk: true` マーク推奨。実例: 001。`hits: 1` 出所 detector-A, fidelity-A

### fidelity チェックリスト追補（新規・今回実害ありで起票）
- **#15 証拠性・主張帰属（evidentiality）** 伝聞/推定/引用された主張を著者の直接断定に格上げしていないか。現 check7（modality 強度）と別軸。**f035b（とされています→断定）で実際の rollback を誘発**。`status: ready` `hits: 1` 出所 fidelity-A
- **#16 開放集合マーカー（等・など・その他）の保存** 「なりすまし等」→「なりすまし」のように列挙の開放性を縮小していないか。**f009 で実際の rollback を誘発**。公的・法令文書で適用範囲縮小に直結。`status: ready` `hits: 1` 出所 fidelity-B
- **#17 要請の名宛人・拘束力レベル** I-3/I-4 軟化時に義務の主体（行政/住民）と強度（義務/勧告/依頼）が保たれるか。`hits: 1` 出所 fidelity-B
- **#18 並列条件・列挙要素の個数照合** 「年末年始およびメンテ期間中」等の並列条件の脱落を計数検出。`hits: 1` 出所 fidelity-B

### playbook レシピ追補（新規）
- **B-2 技術記事カタカナ変換表の追補** ソリューション→仕組み/解決策、スタンダード→標準、ロードマップ→道筋/工程表、バズワード→流行語、インテグレーション→連携、レガシー→旧来、エンタープライズ→企業、リモートワーク→在宅勤務、リアルタイム→即時。＋「業界標準語の維持境界（定訳の有無・専門度）」明文化。`status: ready` `hits: 1` 出所 rewriter-A
- **D-1 公的文書サブルール（儀礼削除の下限）** 冒頭挨拶・末尾結びは各1文まで保持（消すと過軟化＝過推敲）。「賜り/申し上げます」は計2回まで許容、3回目以降を緩和。`status: ready` `hits: 1` 出所 rewriter-B, naturalness-B
- **丁寧度保持マップ** I-3/I-4 軟化は「〜してくださいますよう」→「〜してください」までで止め、公的文書では命令形「〜しろ」へ落とさない。`hits: 1` 出所 rewriter-B
- **A 系手段表現の分散則** 同一段落で A-3「を通じて」と A-8「によって」の fix が「で」に集中しないよう別形へ分散（E 系の分散原則を A 系へ適用）。`hits: 1` 出所 rewriter-A

### naturalness 判定の精緻化（一部 2026-06-25 適用済み）
- **過推敲シグナルの hard/soft 二層化** hard（文体崩れ・口語化・意味希薄化＝1個で C 降格）／soft（変更率30%超＝単独では報告のみ）。`status: done` `applied: naturalness-reviewer.md(2026-06-25)` 出所 naturalness-A, naturalness-B
- **名詞止め・体言止めは文体崩れに非該当** 敬体内の体言止めを style_break と誤判定しない除外規則。`status: done` `applied: naturalness-reviewer.md(2026-06-25)` 出所 naturalness-B
- **grade は絶対残存数・hard 過推敲を主、改善率を従** A/B に「hard 過推敲 0 個」を AND 条件追加。`status: done` `applied: naturalness-reviewer.md(2026-06-25)` 出所 naturalness-A, naturalness-B
- **ジャンル別自然度プロファイル（public_document）** 儀礼を一定残すのが自然。「結び全体の50%超軟化で儀礼過削シグナル」等の数値ライン。`status: ready` `hits: 1` 出所 naturalness-B

### taxonomist 提案（次版）
- 拡張候補に構造化フィールド `hits: N`/`runs: [...]` を導入し昇格判定を自動化。出所 taxonomist
- fidelity 連動パターンに `fidelity_risk: true` マークを付与し rewriter/auditor がスキーマから直接読めるように。出所 taxonomist
