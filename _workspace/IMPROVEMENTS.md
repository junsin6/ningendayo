# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数（**別 run での再現のみ +1**）。

最終更新: 2026-06-26（run 001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2runs`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除・**A 系冗長表現の圧縮**で機械的に膨張。06-12 Sample B は 54.6%、06-26 run001 は 40.0%（挿入76/削除206＝圧縮型・意味改変ゼロ）、run002 は 38.1%（削除143/挿入67＝削除主導）で、いずれも fidelity=pass・自然度 A。30〜50% 警告/中断が誤発火しやすい。
- 出所: 06-12 rewriter-A/B, naturalness-B ＋ 06-26 rewriter-001/002, naturalness-001/002（横断的・最多再現）
- 提案: (a)「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を控除。(c)「加筆率＝挿入字数/原文字数」を単独併記（run001 は約0.11と低く過推敲でないと即判定可）。(d) 出力字数<原文字数の圧縮ケースは閾値を緩和。(e) 50% 中断は「意味改変 edit 比率」基準へ置換。スキーマに `insertion_rate` / `output_length` を追加。
- 影響: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`
- 当面の運用: change_rate 超過でも fidelity=pass かつ自然度 A/B なら override accept（既知欠陥として summary に理由明記）。

### IMP-002 severity_weighted_score の正規化が未定義で detector ごとに式がぶれる `status: done(2026-06-26)` `hits: 2runs`
- 症状: 正規化式が SSOT に無く、06-26 では detector-001 が飽和式 `100·raw/(raw+18)`、detector-002 が文長依存 `100·raw/((len/40)·5)` と**別式を即興採用**。score がジャンル横断で比較不能（同種 AI 文でも文長で score が変動）。
- 出所: 06-12 detector-A/B ＋ 06-26 detector-001/002
- 適用: taxonomy §検出出力スキーマ に正規化式を固定明記 → `severity_weighted_score = round(100·(1−exp(−raw/45)), 1)`、`raw = S1×5 + S2×2 + S3×0.5`。文長非依存・単調飽和。SSOT 例（raw56→71.5）を再現。スキーマに `score_raw` / `severity_counts` / `score_formula` を正式項目化。detector.md §スコア算出 も同期。**v1.1 へ taxonomist 審査済み。**

### IMP-003 score_before のフィールド契約が曖昧 `status: ready` `hits: 1run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。
- 出所: 06-12 naturalness-A
- 提案: 「score_before = 02_detection.json の meta.severity_weighted_score」と明文化（06-26 は本値を指示して運用、ぶれ無し）。IMP-002 確定で分母も固定されるため次回適用候補。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: done(2026-06-26)` `hits: 2runs`
- 症状: 絵文字8個・文末単調・文長均一・受動多用は分散/文書レベル。06-26 では detector-001 が E-1/E-2 にダミー全体 span、detector-002 が span=-1 を入れざるを得ず、推敲役の扱い契約も未定義。
- 出所: 06-12 detector-A/B ＋ 06-26 detector-001/002
- 適用: スキーマに `span_type: "contiguous" | "scattered" | "document"` を追加。document/scattered では `start`/`end` を null 許容、`evidence`（数値根拠: stdev・文末分布等）と scattered 用 `occurrences:[[s,e],…]` を許容。`ai_tell_density` は重複区間マージ後の被覆文字数ベースと明記。**v1.1 へ taxonomist 審査済み。**

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2runs`
- 症状: 1 span が複数カテゴリに該当（06-26 run001「ソリューションを提供することができます」= A-10＋A-5＋B-2 の三重）。findings/edits の 1:1 前提が崩れ category_summary・density が歪む。
- 出所: 06-12 detector-A,rewriter-A/B,naturalness-A,fidelity-A ＋ 06-26 detector-001/002,rewriter-001
- 提案: 「1 span = 主分類 1 finding」を基本とし、finding に `co_categories:[…]`、edit に `resolves_findings:[…]`（複数 id, N:M）を許容。category_summary は「findings の主 category 先頭文字を集計」と注記。density は被覆マージ後（IMP-004 と統合）。次回適用候補。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer の検出器再実行を仕様で必須化 `status: ready` `hits: 2runs`
- 症状: 仕様は「検出器を同基準で再走査」だが、強制経路が無く手動照合に落ちうる。06-26 は両 naturalness が指示により ai-tell-detector サブエージェントを実起動し再走査（経路の実現可能性は実証済み）。
- 出所: 06-12 naturalness-A ＋ 06-26 naturalness-001/002
- 提案: `naturalness-reviewer.md §処理` に「ai-tell-detector をサブエージェントとして必ず再呼び出し（手動照合禁止）」を明記。再走査 JSON を `05_*` に同梱。次回適用候補。
- 影響: `naturalness-reviewer.md`, `SKILL.md`

### IMP-007 公的文書ジャンルの敬語/定型許容ラインが未定義 `status: ready` `hits: 1run` 🆕
- 症状: taxonomy は「公的文書は一定の硬さが許容」と述べるが**具体的閾値が無い**。06-26 run002 で「賜り/申し上げます/ございます」を AI クセと標準定型に分ける基準（回数閾値・冒頭末尾の二重使用判定）、I-4「求められております」を締め定型「お願いいたします」との対比で S1 判定する根拠を、検出器・推敲役が即興で決めており再現性が低い。
- 出所: 06-26 detector-002, rewriter-002, fidelity-002, naturalness-002（単一 run だが 4 エージェント横断）
- 提案: taxonomy に `genre_thresholds` 表を新設（例「最上級敬語は1文書1回まで定型許容／冒頭+末尾の二重使用で S2」「公的文書の締めは『お願いいたします』が定型、『求められております』非人称は S1」「逆方向過推敲＝砕けすぎも naturalness の減点対象」）。**次回別 run で再現すれば ready 確定 → 適用。**
- 影響: `ai-tell-taxonomy.md`, `ai-tell-detector.md`, `naturalness-reviewer.md`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。実例: 06-12 run001。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。 `hits: 1` 出所 06-12 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 06-12 detector-B
- **A-5/A-6 複合「可能＋状態化の二重冗長」** 🆕 「〜することが可能となっています」「〜することもできるようになります」。可能冗長(A-5)と状態叙述(A-6)が一句に重畳。実例2件: 06-26 run001。 `hits: 1` 出所 detector-001, rewriter-001
- **過剰敬語の独立カテゴリ（K 系 or F サブ）** 🆕 「賜り/お願い申し上げます/ございます」の最上級敬語飽和。現状 F-2 に間借りで所属が曖昧。 `hits: 1` 出所 06-26 detector-002

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** `status: done(2026-06-26)` `hits: 2runs` ← f019（並列→基盤の序列混入）対策。06-26 fidelity-001 が「並列(また/さらに)↔序列(まず/次に)↔因果↔逆接 の相互変換」専用判定を要望し再現。**fidelity-auditor.md に第14項として追加・適用済み。**
- **削除専用サブチェック（deletion-recall test）** `status: ready` `hits: 2runs` 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。06-26 fidelity-001/002 が再現（run002 で全依頼事項の保存表を作成）。次回適用候補。出所 06-12 fidelity-B ＋ 06-26 fidelity-001/002
- 「情報を含む削除 vs ボイラープレート削除」二分判定: (a)数値/固有名詞/日付 (b)条件/因果節 (c)固有の例示 を含めば情報欠落、挨拶/CTA/装飾/自己言及のみならボイラープレート。`hits: 2runs` 出所 06-12 fidelity-B ＋ 06-26 fidelity-002
- #5論理関係 と #11情報追加 の責任境界を一意化（順序・因果の新規付与=#11、既存論理の破壊=#5）。`hits: 2runs` 出所 06-12 fidelity-A ＋ 06-26 fidelity-001
- modality 強度を順序尺度化（断定>見込み(はず)>推量(でしょう)>ヘッジ(と言える)、±N段差分で判定）。`hits: 2runs` 出所 06-12 fidelity-A ＋ 06-26 fidelity-001

### playbook レシピ追補
- **C-5 絵文字削除後の文末/区切り吸収ルール**。出所 06-12 rewriter-B
- **D 系結びは削除一択でなく「最小着地文を残す」**。出所 06-12 rewriter-B, naturalness-B
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**という例外則。出所 06-12 rewriter-A
- **原文が元から推量の D 系は推量を保持**。出所 06-12 rewriter-A
- **ジャンル別カタカナ語ホワイトリスト** 🆕 技術解説では維持（レイテンシ/ワークロード/ボトルネック/パラダイム/スループット）、一般コラムでは開く。edit reason に `katakana_decision` を強制記録。`hits: 1` 出所 06-26 rewriter-001
- **edit に `action: applied|retained|rolled_back`** 🆕 「検出妥当だが意図的に保持」（06-26 run001 f003「というアーキテクチャ」）を記録できず、検証役が「未修正」と誤検知する。`hits: 1` 出所 rewriter-001

### naturalness 判定の精緻化
- 過推敲シグナルの定量化（敬体/常体混入は文末形態の二値カウントで機械検出）。`hits: 2runs` 出所 06-12 naturalness-A ＋ 06-26 naturalness-001/002
- クラスタ系 finding（B-2 密集・C-1 列挙・E-2 単調・A-13）はクラスタ崩壊時に個別 severity を S2→S3 降格。`hits: 2runs` 出所 06-12 naturalness-A ＋ 06-26 naturalness-001
- E-2 文末単調の到達可能ライン緩和（体言止め1箇所以上で合格）。出所 06-12 naturalness-B
- 絶対残存数ガードを grade 表に組込み（改善率が高くても S1 が1件でも C 以下）。`hits: 2runs` 出所 06-12 naturalness-A/B ＋ 06-26 naturalness-002
- **公的文書の逆方向過推敲＝砕けすぎ検出** 🆕 砕けすぎ・格の崩れも over_polish_signal に計上。出所 06-26 naturalness-002

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 2runs`
- ルーティン・モチベーション・データドリブン・リアルタイム・アーキテクチャ 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。出所 06-12 naturalness-B,fidelity-A,naturalness-A ＋ 06-26 naturalness-001,rewriter-001。playbook の例外維持リスト拡充で次回適用候補。

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert）。`hits: 2runs` 出所 06-12 detector-A ＋ 06-26 detector-001/002（両者とも自己検証を実施）
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 06-12 detector-B
- **前処理規約の明文化** 🆕 タイトル行を検出対象に含めるか、文体/文長統計を本文のみで算出するか、detector.md に明記。出所 06-26 detector-001
