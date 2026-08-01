# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数（**別 run での再現のみ +1**）。

最終更新: 2026-08-01（run 001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done`（2026-08-01-001/002 で適用）`hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。2026-06-12 run B は 54.6% で誤発火。2026-08-01 でも再現: run 001 は削除 0.226/挿入 0.077、run 002 は削除 0.240/挿入 0.060 と**両 run とも削除支配**で、意味改変ではなく冗長定型の短縮が change_rate を押し上げた。
- 出所: rewriter-A/B（両 run）, naturalness-B
- 提案: (a)「語句改変率（既存語の別語置換）」と「構造/削除率（定型短縮・接続詞削除）」を二軸で分離計上。(b) 装飾・常套句の純削除分を控除。(c) del≫ins の削除主導ケースは中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準へ。(e) round をまたぐ再推敲では 30/50% 閾値を累積後の絶対値で再判定。
- 影響: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`
- **適用（2026-08-01）**: playbook §変更率の数え方を二軸定義（語句改変率／構造・削除率）へ改訂し、削除主導型の中断除外・累積再判定ルールを明記。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done`（2026-08-01 で適用）`hits: 2run`
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える。2026-08-01 で強く再現: run 001 は raw 加重和 120 が 100 にクリップされ**天井到達（改善率が真値 93.75% より過小の 92.5% と表示）**、run 002 は 69.0。両 run の 4 エージェント（detector×2, naturalness×2）が独立に指摘。天井効果で baseline の異なる文書間の改善率が識別不能になる。
- 出所: detector-A/B（両 run）, naturalness-A/B（両 run）
- 提案: `raw_score`（生加重和）を別フィールドで常に保持し、改善率は `(raw_before − raw_after)/raw_before` で算出。表示スコアのみ飽和曲線 `100*(1-exp(-raw/K))` で 0–100 正規化（二層化）。分母の扱いも SSOT 明記。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出`, `naturalness-reviewer.md`
- **適用（2026-08-01）**: taxonomy スキーマに `raw_score` フィールドと二層化（raw 保持＋飽和正規化 `100*(1-exp(-raw/K))`, K=60）・改善率は raw 基準を明記。

### IMP-003 score_before のフィールド契約が曖昧 `status: ready` `hits: 1run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。
- 出所: naturalness-A（2026-06-12）
- 提案: 「score_before = 02_detection.json の meta.severity_weighted_score」と明文化。IMP-002 二層化後は raw/正規化のどちらを基準にするかも合わせて確定。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`
- 補足: 2026-08-01 は orchestrator が「score_before = meta.severity_weighted_score」と明示指示して回避したが、SSOT 未記載のため再発リスクは残る。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run`
- 症状: 絵文字散在・文末単調（E-2）・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく density が過大化。2026-08-01 でも再現: 両 detector が E-2「です・ます単調」を「代表 span 1 つ＋reason に"文書全体に散在"」で運用せざるを得なかった。C-1/C-7/E-1 も同種。
- 出所: detector-A/B（両 run）
- 提案: `span_type: "contiguous"|"scattered"|"document"` と scattered 用 `occurrences: [[s,e],...]` を追加。density は重複・locator を除いた実 AI クセ文字数ベースと定義。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`
- 昇格: **hits 2 到達。次回適用候補（IMP-005 と同じスキーマ節のため併せて実施推奨）**。

### IMP-005 span 重複時の density/カウント規約が無い `status: done`（2026-08-01 で density 定義を適用）`hits: 2run`
- 症状: 1 span が複数カテゴリに該当し、density を単純総和すると二重計上（>1.0 もあり得る）。2026-08-01 で再現: 両 detector が「A-6＋F-1」「A-8＋A-6」等の隣接・連結 finding を union（重複除去）で回避したが、スキーマは「span 総文字数」としか規定せず union 指定が無い。
- 出所: detector-A/B（両 run）, rewriter, naturalness, fidelity（横断的）
- 提案: (a) density は「finding span の**和集合**文字数 / 全体文字数」と明記。(b)「1 span = 主分類 1 finding」を基本とし `secondary_category`/`merged_findings` を許容。category_summary の集計規約も注記。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, 全 .md のスキーマ節
- **適用（2026-08-01）**: taxonomy の `ai_tell_density` 定義を「和集合（重複除去）文字数 / 全体文字数」へ改訂。secondary_category は IMP-004 と併せて次回。

### IMP-006 naturalness-reviewer が検出器を再実行できず score_after が推定 `status: done`（2026-08-01 で適用）`hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だが、**サブエージェントは入れ子でサブエージェントを起動できない**ため naturalness-reviewer から ai-tell-detector を fork 不能。2026-08-01 の両 reviewer が「Task/サブエージェント起動ツールが無く実検出できない、SSOT 同基準で手動再スキャンした」と明記。IMP-006 の元提案（reviewer が detector を呼ぶ）はアーキテクチャ上実現不能と判明。
- 出所: naturalness-A（2026-06-12）, naturalness-A/B（2026-08-01）
- 提案（改訂）: **オーケストレーターが推敲後 `03_rewrite.md` に対し ai-tell-detector を先に再実行**し、その `02b_redetection.json` を naturalness-reviewer に入力として渡す。reviewer は数値を受け取り等級判定に専念。手動再スキャンは禁止から「orchestrator 再検出の受領」へ。
- 影響: `SKILL.md §並列検証`, `naturalness-reviewer.md §処理`, DAILY.md パイプライン
- **適用（2026-08-01）**: SKILL §並列検証と naturalness-reviewer §処理 step1 を「オーケストレーターが推敲後 detector を再実行し再検出 JSON を reviewer へ渡す」経路へ改訂。fork 不能時の手動再スキャンは notes 明記を条件に許容。あわせて fix-induced regression シグナルを step3 に追加。

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **D-7 公的文書 依頼公式の反復** 「〜いただきますようお願い申し上げます」「〜賜りますようお願い申し上げます」「〜におかれましては」。公用文 AI 文の決定的シグネチャで、E-2（文末単調）とは別物（文末変奏不足ではなく依頼公式の丸ごとコピペ反復）。実例: 002 で「いただきますよう〜」5 回・「におかれましては」2 回。`status: ready(候補)` `hits: 1run(detector-B, rewriter-B)`
- **severity のジャンル依存（文脈補正）** A-1/A-2 等 taxonomy 固定 S1 が公的文書では標準官庁文体で「一度で AI 確信」に達しない。両 detector が文脈で S2 へ降格して reason 明記。「pattern 固有 severity × ジャンル係数」または降格可否ルールの新設を提案。`hits: 1run(detector-A/B)`
- **A-8 定義の拡張** 現行は「〜によって」by-passive 限定だが、公的文書の主クセは**行為者を消した agentless passive（実施される/送付される）**。定義を「by-passive + 行為者省略受動」へ拡張要。出所 detector-B。
- **D-3 追記候補「〜が挙げられます」列挙導入** 現行 D-3 の例（大きく三つに/以下のような特徴）に「〜が挙げられます」型が無い。実例 001 で 3 回。出所 detector-A。
- **C 系: redundant restatement**（2026-06-12 起票、継続）叙述と箇条書きの二重記載。`hits: 1`
- **D-1 二重結び** 「いかがでしたでしょうか」＋「〜してみてはいかがでしょうか」の結び 2 連（001 で再現）。既存 D-1 の反復強度指標として記録。

### fidelity チェックリスト追補
- **#11b claim-substitution（主張のすり替え）新設** `status: ready` `hits: 2run` — 「追加」でも「欠落」でもない“同一スロットの命題差し替え”を捕捉する専用項目。実例: 001 e002「大きな注目を集めています→広がっています」（注目の増大→普及の拡大）は #10/#11 の狭間に落ちた。2026-06-12 の #5/#11 境界一意化と同根。出所 fidelity-A（両 run 系統）。
- **modality 強度の順序尺度化** `status: ready` `hits: 2run` — 義務強度を順序尺度（L4 必ず＋必要 / L3 必要がございます / L2 必ず＋ください / L1 ください 等）で数値化し、差 +1 段は warn・+2 段以上は rollback。実例: 002 f007/f014 が L3→L1（2 段降下）だが distributed-obligation で救済。2026-06-12 fidelity-A ＋ 2026-08-01 fidelity-A/B。
- **distributed-obligation（義務の分散担保）チェック** `status: ready` `hits: 1run` — 個別文で弱化しても別段落の条件節（例: 受診拒否条項）が必須性を補うケースの正式サブチェック。義務対象ごとに「必須性を明示する span が最低 1 つ残存するか」を突合。出所 fidelity-B。
- **脱ハイプ D-4 の線引き** `status: ready` `hits: 1run` — 「修飾語の削除のみ許可・動詞/事象語の置換は fidelity レビュー必須」。e002（事象語置換=毀損）と e035（修飾語ずれ=許容）が同カテゴリで毀損度が違う点が示す。出所 fidelity-A。
- **強調副詞削除（F-1）を独立項目化** 「大変/極めて/非常に」の削除は #6量化・#7modality のどちらにも属しにくい。程度・強調の増減を独立項目に。出所 fidelity-B。
- **保護語（protected token）連携** 義務文中の `必ず` を検出・推敲側で protected token とマークし E-2/F-1 で削らせない。出所 fidelity-B。
- **削除専用サブチェック（deletion-recall）** `status: ready` `hits: 2run`（両 run で有効に機能）— 削除 span ごとに「読者が知り得なくなる事実は何か」。情報を含む削除 vs ボイラープレート削除の二分判定。出所 fidelity-A/B。
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** `status: ready` `hits: 2run`（001 で C-1「第一に→まず/最後に」を検査し pass を確認、有効性実証）。出所 fidelity-A。

### playbook レシピ追補
- **公的文書ジャンル別セクションの新設** `status: ready` `hits: 1run` — 現 v1.0 はコラム/エッセイ/レポート想定。公用文の格式マーカー（ご持参ください／賜りますよう〜／におかれましては）を「残すべき正規定型」として明示し、「機能する定型は 1 件残す」「依頼文末は 3 種以上に分散・同一語尾は連続 2 段落まで」を規定。出所 rewriter-B。
- **suggested_fix の文体整合** `status: ready` `hits: 1run` — 検出器の suggested_fix が常体（手法だ 等）で提示され、そのまま採ると文体維持違反。「suggested_fix は文体非依存の骨子、推敲役が meta.style に合わせ文体を付与」と明記、または検出器側で style 整合。出所 rewriter-A。
- **B-2 変換表の複合語/短語ガイド** 定着複合語（〜コスト・〜サイクルは維持）と、文脈で語を補う短語（ポイント→要点/勘所）を区別。出所 rewriter-A。
- **E-2 敬体専用の変奏インベントリ** 〜ものです／〜わけです／連用中止＋体言止め／問いかけ 等。敬体単独文書は変奏余地が構造的に狭い。出所 rewriter-A。
- **C-5 絵文字削除後の文末/区切り吸収ルール**（2026-06-12 継続）。
- **D 系結びは「最小着地文を残す」**（2026-06-12 継続）。
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**（2026-06-12 継続）。

### naturalness 判定の精緻化
- **fix-induced regression チェック新設** `status: ready` `hits: 1run` — 「一つのクセを消して別のクセを生む」検出。実例: 002 で依頼公式除去の副作用で「〜ください」が 8 文末に集中（E-2 を E-2 で再発）。(a) 修正で導入された文末語尾を集計し同一語尾が文末の 40% 超で E-2 を再発火、(b) rewriter diff から「置換先語彙の集中度」を算出し reviewer へ。出所 naturalness-B。
- **accept_with_micro_fix 等級の新設** `status: ready` `hits: 1run` — S1 residual ≤1 かつ fix が単一 span なら、フル rewrite_round_2 と C の間に「局所差し戻し」区分。実例: 001 は A-5 単発 1 件で C 判定だがフル再推敲は過剰だった。出所 naturalness-A。
- **過推敲シグナルの定量化** `status: ready` `hits: 2run` — 各シグナル（口語化・文体崩れ・意味痩せ・体言止め過多）の計測式と閾値が非明示でレビュアー裁量。例:「逆文体文末 ≥1=文体崩れ」「体言止め比率>30%=過多」「変更率 30–50%=1・50%超=中断」。2026-06-12 naturalness-A ＋ 2026-08-01 naturalness-A。
- **過推敲シグナルへの weight/severity 導入** 1 個でも深刻なシグナル（修正対象カテゴリの再発=fix-induced regression）は「S1 級シグナル 1 個で C」等の減点条項に。改善率が高くても残存に修正対象カテゴリが含まれれば自動 1 段階降格。出所 naturalness-B。
- クラスタ系 finding のクラスタ崩壊時 severity 降格ルール（2026-06-12 継続）。
- 絶対残存数ガードを grade 表に組込み（S1 が 1 件でも C 以下）（2026-06-12 継続、001 で実適用）。

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 1run(3agent)`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。（2026-06-12 起票、継続）

### taxonomy 運用（taxonomist 審査 2026-08-01 由来）
- **severity と weight の二層分離**: 固定 severity（S1/S2/S3）は taxonomy が持ち、可変 weight/ジャンル降格は検出器設定へ分離する境界を明文化すべき。ジャンル依存降格を導入すると SSOT が「固定severity」と「実効weight」に二層化する。出所 taxonomist。
- **finding へジャンルタグ（col/rep/blog/gov）軸を追加**: D-7 等ジャンル特化パターンをカテゴリを増やさず管理でき、severity ジャンル降格とも接続。カテゴリ D 肥大化の回避策。出所 taxonomist。
- **昇格条件の明文化**: 「再現2回以上」を「**独立した 2 run 以上での再現**」と定義に一行追加（同一 run 内反復と区別）。D-7 は同一 run 内5回でも 1run 扱いで候補止まりとした。出所 taxonomist。
- **改善率のゼロ除算ガード**: `raw_before=0`（AIクセ未検出）時は improvement=0 と定義（taxonomy スキーマ節に追記済み）。

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert）`hits: 2run`（両 run で detector が assert 実装・有効）。出所 detector-A（両 run）。
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`（2026-06-12 継続）。
