# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-07-30（run 2026-07-30-001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done`（適用 2026-07-30-001/002）`hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。day0 Sample B は 54.6% で `hold_and_report` 誤発火。**2026-07-30-001 でも再現**: change_rate 0.447（round2 0.404）が 30% 超だが削除200/挿入71 の削除主導で、fidelity=pass・自然度 A。今回も override accept を要した。
- 出所: rewriter-A/B(day0), naturalness-B(day0), rewriter-001(0730), naturalness-001(0730)
- **適用内容（2026-07-30）**: change_rate を `deletion_rate` / `insertion_rate` / `substitution_churn_rate` / `edit_profile` に分離。中断・警告の主軸を `substitution_churn_rate` に変更（churn 30%警告/50%中断、削除主導は総 change_rate 高でも非中断）。SKILL §総合判定に override accept 行を明文化（削除主導＋fidelity=pass＋等級A/B）。
- 適用ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md §変更率監視+schema`, `SKILL.md §3/§5`。
- 残: churn の正確な算出（LCS ベース min(挿入,削除)）は実装依存。E系リズム操作（文分割）を分子から減衰させる補正は次段。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done`（適用 2026-07-30-001/002）`hits: 2run`
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える。**2026-07-30-001 で再現**: raw=107 が 100 にクリップされ弁別不能（detector-001）。detector-002 は raw=36.5 が長さ非正規化でそのまま score 化。
- 出所: detector-A/B(day0), detector-001/002(0730)
- **適用内容**: taxonomy v1.1 §検出出力スキーマに三段式を確定 — `raw_weighted_sum` → `density_raw = raw/(input_length/100)` → `severity_weighted_score = 100*(1-exp(-density_raw/K))`, K=8。文長非依存・非飽和。detector.md §スコア算出も同期。meta に raw_weighted_sum/density_raw/severity_weights/normalization を出力必須化。
- 適用ファイル: `ai-tell-taxonomy.md`（v1.1, taxonomist審査済）, `ai-tell-detector.md §スコア算出+schema`。
- 残: K=8 は 2run の density_raw 実測に基づく暫定。ジャンル依存（公文書は儀礼定型で raw 高）の最適 K ずれは要観察。

### IMP-003 score_before のフィールド契約が曖昧 `status: done`（適用 2026-07-30-001/002）`hits: 2run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定でぶれる。**0730 両 run で再現**: 検出器を再実行できず severity 重みを逆算・推定。
- 出所: naturalness-A(day0), naturalness-001/002(0730)
- **適用内容**: 「score_before = 02_detection.json の meta.severity_weighted_score をそのまま用い再計算しない」を naturalness-reviewer.md に明文化。飽和時は raw ベース改善率も併記。severity_weights/normalization.K を detection meta に出力必須化し逆算不要に（IMP-002 と連動）。
- 適用ファイル: `naturalness-reviewer.md §処理+schema`, `ai-tell-taxonomy.md`（重み明示）。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run`
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。**0730 再現**: A-5×8/B-2 が散在、E-1/E-2/H-1 は文書レベルで start=end=0 の代表点しか持てず、レビュアー/推敲役が1点だけ直す危険。
- 出所: detector-B/A(day0), detector-001/002(0730)
- 提案: `span_type: "contiguous"|"scattered"|"document"`（or `scope`）と scattered 用 `occurrences: [[s,e],...]`、文書レベル E系用 `metrics`（文長SD・文末反復率）。density は union 被覆ベース（IMP-005 で ai_tell_density を union 定義済＝部分適用）。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`
- 次回適用候補（hits≥2 到達）。

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリに該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。density の二重計上。**0730 再現**: A-6＋A-8 重畳（run002 f001-f004）、A-7⊃メリット・D-5⊃ポテンシャル・A-10×A-5 重畳（run001）。
- 出所: detector-A/rewriter-A/B/naturalness-A/fidelity-A(day0), detector-001/002/rewriter-002(0730)
- 部分適用（0730）: `ai_tell_density` を「重複を排した union 被覆」と detector.md に定義（二重計上を防止）。
- 残提案: 「1 span = 主分類 1 finding、重畳は reason 注記 or `merged_findings: [...]`」を全 .md スキーマ節へ。category_summary の集計規約明記。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。**0730 両 run で再現**: naturalness-001/002 とも Agent/Task ツールが無くサブ検出器を spawn できず taxonomy 基準の自力再走査で代替。
- 出所: naturalness-A(day0), naturalness-001/002(0730)
- 部分適用（0730）: `detector_rerun.subagent_invoked` フィールドを 05 スキーマに追加し、手動照合時は false 明記を義務化（透明化）。
- 残提案: オーケストレーターが検出器を再走査して結果をレビュアーへ渡す経路、またはレビュアーに detector spawn 権限を付与。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md §4`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 001。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B

#### 2026-07-30 起票（taxonomy v1.1 候補欄に実例つきで登録済・hits=1 のため未昇格）
- **K「過剰敬語・儀礼定型の累積」★日本語固有（新大分類候補）** 賜り／御礼申し上げます／所存でございます／お願い申し上げます 等の儀礼語の高密度累積。設計思想の「(2)過剰な丁寧体・敬語」に A〜J の受け皿が無い。**但し単発は register 相応（自治体職員も書く）→「密度・機械反復のみ tell、単発不検出、原則 S3、削りすぎ=register 破壊を下限ガード」を必須但し書き**。実例2件（run 002）。 `hits: 1` 出所 detector-002, rewriter-002, naturalness-002（1run3agent）。昇格には別 run 再現＋人間反例チェック。
- **A-5b「〜ことを可能にする / 可能にしている」(enable/make-possible 型)** 現 A-5 は「することができる」冗長縮約限定で enable 型使役構文が射程外。断定化すると可能性 modality と使役・因果が同時消失（run001 f012 の毀損原因）。処方「可能・使役を保持して常套句だけ除去」。 `hits: 1` 出所 detector-001, rewriter-001, fidelity(round2)-001。
- **A-8b「行為者省略の翻訳受動（〜される/された）＋ 手段・原因の によって」** 現 A-8 は by-passive 明示型限定。公文書は行為者省略受動が主流、「によって」は行為者/手段/原因の多義。実例（run001/002）。 `hits: 1` 出所 detector-001, detector-002, rewriter-002。
- 構造課題（taxonomist 指摘）: 各サブパターン定義が「英語ソース構文起点」で狭く固定されているため同一日本語表層の別変種を取りこぼす（A-5b/A-8b がその実例）。定義を「日本語表層パターン起点」へ棚卸しする再設計を将来候補として記録。

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019（並列→基盤の序列混入, day0）。**0730 再現**: run001 f013「進むほど」が改変内で比例相関を新規混入。`status: ready` `hits: 2` 出所 fidelity-A(day0), fidelity-001(0730)。→ #5 を「論理関係の破壊・追加・強化の両方向」を対象と明記する形で次回適用候補。
- **#15 併合 edit の隠れ欠落監査** 複数 finding を1 edit に併合した際、before の全概念語が after に保存されているか語単位照合。run001 f013 は B-2(語彙・低リスク)＋A-10(構文・高リスク)併合で「革新」「さまざまな」脱落が隠蔽された。`status: ready` `hits: 1` 出所 fidelity-001, rewriter(round2)-001。
- **modality 強度の順序尺度化＋逆方向（義務→推奨/任意への緩和）** `断定>可能>推量>二重婉曲` と `必須>義務>要件>勧告>依頼>任意` の順序尺度で「原意より N 段強い/弱い」を数値化。現 #7 はヘッジ除去過剰（推量→断定）方向のみで、逆方向の要請弱化を扱えない。`status: ready` `hits: 2` 出所 fidelity-A(day0), fidelity-001(modality過断定)/fidelity-002(要請緩和 f008-f010)(0730)。→ **次回適用の最優先候補**。
- **checks に中間値 `pass_with_note`（warn）を追加** 「毀損ではないが緩和・明示性低下が起きた」ケース（run002 f010 要件→依頼）を note に押し込まず記録。`status: ready` `hits: 1` 出所 fidelity-002。
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。`status: ready` `hits: 1` 出所 fidelity-B
- 「情報を含む削除 vs ボイラープレート削除」二分判定。出所 fidelity-B
- #5論理関係 と #11情報追加 の責任境界を一意化。出所 fidelity-A
- カタカナ→漢語の語義ズレ判定「指示対象が同一なら許容、概念が別義化したら毀損」の明文化。出所 fidelity-001（ボトルネック→滞り の境界判断）。

### playbook レシピ追補
- **C-5 絵文字削除後の文末/区切り吸収ルール**（句点で吸収 or 削除のどちらか明記）。出所 rewriter-B
- **D 系結びは削除一択でなく「最小着地文を残す」**（減らしすぎ下限）。実例: B の「気軽に始めてみてください」。出所 rewriter-B, naturalness-B
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**という例外則。出所 rewriter-A
- **原文が元から推量の D 系は推量を保持**（「断定へ」の一律処方の例外）。出所 rewriter-A
- **A-5b レシピ「ことを可能にする → 〜できるようにする／〜を可能にする」**（可能・使役を保持、断定化してよいのは元が可能・使役を含まない場合のみ）。`status: ready` `hits: 2` 出所 rewriter-001, fidelity(round2)-001（run001 で毀損→ロールバックで実証）。→ 次回適用候補（playbook A 表＋taxonomy A-5b 連動）。
- **二重婉曲（G-2）の適正除去段数**「2層→1層で止める。原文が推量を含む場合は推量層を優先保持（可能形を落とす）。0層＝断定化は原文が既に断定調のときのみ」。`status: ready` `hits: 2` 出所 rewriter-001(f011 過断定), fidelity-001。→ 次回適用候補。
- **A-10 概念保存の境界線**「主語・動詞構文のみ手を入れ、目的語の概念語・量化語・元の論理関係は保存」。run001 f013 で目的語「革新」まで巻き込み毀損。`hits: 1` 出所 rewriter(round2)-001, fidelity-001。
- **公文書 register 用レシピ節（新規）**: 儀礼骨格（賜り／御礼申し上げます）は保持し過剰装飾（厚く 等）のみ剥ぐ。要請3連（必要がございます×3）は「ください／〜ておいてください／お願いいたします」へ非同型ローテーション。「〜される」でも主体が制度・行政側で自明なら保持可。`hits: 1` 出所 rewriter-002。

### naturalness 判定の精緻化
- 過推敲シグナルの定量化（敬体/常体混入は文末形態の二値カウントで機械検出）。出所 naturalness-A
- クラスタ系 finding（B-2 密集・C-1 列挙）はクラスタ崩壊時に個別 severity を降格するルール。出所 naturalness-A
- E-2 文末単調の到達可能ライン緩和（体言止め1箇所以上で合格、文体維持制約下の過推敲回避）。出所 naturalness-B
- **絶対残存数ガードを grade 表に組込み**（改善率が高くても S1 が1件でも C 以下。または score_after 絶対値の上限で A 判定を絞る）。`status: ready` `hits: 2` 出所 naturalness-A/B(day0), naturalness-001(0730)。→ 次回適用候補。
- **ジャンル別の残存許容閾値**（新規）: E-1/E-2/H-1 の削減目標を全ジャンル一律にすると公文書で過検出→矯正すれば register 破壊。ジャンル別に S3 格下げ閾値を設ける。`hits: 1` 出所 naturalness-002。
- **register 破壊（過推敲・下限側）を grade 減点要因に明記**（硬い敬語を削りすぎて自治体文書として不自然＝過推敲）。`hits: 1` 出所 naturalness-002。

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 1run(3agent)`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B, fidelity-A, naturalness-A

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。出所 detector-A, detector-001/002(0730 実践済)
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B
- **タイトル・見出しをスキャン範囲に含める**（run001 タイトル「エッジAIがもたらす…」の A-10 が未検出・未推敲で残存）。`hits: 1` 出所 naturalness-001。
- **severity 動的降格ルール**「S1 パターンでも単発かつ反復閾値以下 or register 相応なら S2/S3 へ降格可」。A-1 が2回ちょうど・A-2 が公文書で単発のケースで検出器裁量が割れ再現性欠如。`status: ready` `hits: 2` 出所 detector-001(A-1), detector-002(A-2)。→ 過検出抑制に有効、次回適用候補。
- **C-1 の閾値明記**（3語「まず・次に・最後に」揃いで S1、2語の半列挙は S3 等）。`hits: 1` 出所 detector-002。
- B-2 カタカナ語の置換可否ホワイト/ブラックリスト拡充（検出器間の再現性確保）。`hits: 1` 出所 detector-001。
