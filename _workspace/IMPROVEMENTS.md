# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-08-04（run 2026-08-04-001, 002 — day1 技術解説/公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B(0612) は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。Sample A(0612) も 47.6% と高止まり。
- **再現(2026-08-04)**: run 002（公的文書）が change_rate **0.40** で警告域。全削減が finding 紐付きの形式敬語圧縮（724字短文×ai_tell_density 0.318）で、fidelity 13/13 pass・自然度 A・過推敲0 → **override accept** で処理。短文×長大形式句ジャンルでは構造的に 30% 超が頻発することを再実証。rewriter-002 も同旨（分母固定で密度高文書ほど膨張）。
- 出所: rewriter-A(0612), rewriter-B(0612), naturalness-B(0612), **rewriter-001(0804), rewriter-002(0804), naturalness-002(0804)**
- 提案: (a) 「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を change_rate から控除。(c) 挿入率を単独併記し、del≫ins の削除主導ケースは中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。(e) **算出アルゴリズムを SSOT 化（difflib 最小編集を正とし共通部分を差引）**（rewriter-001 追加）。(f) 「編集回数≒finding 件数」かつ「削除が finding 紐付き」かつ「内容保存」の3条件成立時は正当削除と再分類（naturalness-002）。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done`（適用 2026-08-04-*） `hits: 2run`
> **適用済(2026-08-04)**: taxonomy §検出出力スキーマ＋ai-tell-detector.md §スコア算出に正準式 `round(min(100, raw/input_length*1000),1)`（raw=S1×5+S2×2+S3×0.5）を確定。naturalness-reviewer.md も同式で score_after を算出。回帰確認: 002 は既にこの式で 69.8 を算出済み（整合）、001 は旧カウント式 80.5→正準式なら94.3 と判明し不整合を是正。
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える（Sample A(0612) raw106→92.5、taxonomy 例は raw56→71.5 と不整合）。
- **再現(2026-08-04)・実害確定**: 同日の2検出器が**互いに異なる式を採用**した — detector-001 は `min(100, S1×5+S2×2+S3×0.5)`=**80.5**（カウント依存・文長無視）、detector-002 は `min(100, raw/input_length*1000)`=**69.8**（密度依存）。正規化未定義により score_before が検出器ごとに非可換となり、改善率の run 間比較が破綻することを実証。
- 出所: detector-A(0612), detector-B(0612), **detector-001(0804), detector-002(0804)**
- 提案: 飽和しにくい・文長正規化された式を SSOT 明記。密度依存 `min(100, raw/input_length*1000)`（＝1000字あたり加重和）を正とし全検出器に強制。分母は input_length。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出`

### IMP-003 score_before のフィールド契約が曖昧 `status: done`（適用 2026-08-04-*・co-located） `hits: 1run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score 92.5）。レビュアーごとに数値がぶれる。
- 出所: naturalness-A
> **適用済(2026-08-04)**: IMP-002 適用時に co-located で naturalness-reviewer.md §処理2 に「score_before = 02_detection.json の meta.severity_weighted_score、score_after は正準式で算出」を明文化。IMP-002 の正準式確定と対で score 契約が固まった。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run`
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
- **再現(2026-08-04)**: E-2 文末単調（文書レベル finding）が span 単位 diff と粒度不整合。個別 edit へ分散すると before/after が代表値化する（rewriter-002）。`affected_sentences: []` 配列の要望が再提起。
- 出所: detector-B(0612), detector-A(0612), **rewriter-001(0804), rewriter-002(0804)**
- 提案: `span_type: "contiguous"|"scattered"|"document"` と scattered 用 `occurrences: [[s,e],...]`（文書レベルは `affected_sentences: []`）を追加。density は重複・locator を除いた実 AI クセ文字数ベースと定義。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: done`（適用 2026-08-04-*） `hits: 2run`
> **適用済(2026-08-04)**: taxonomy §スキーマ＋ai-tell-detector.md に `secondary_categories: []` を追加。「1 span=主分類1 finding、従カテゴリは配列列挙、category_summary は主のみ集計」を明文化。
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。
- **再現(2026-08-04)**: 「欠かせないコンポーネントとなっています」= A-6＋B-2＋D-4 の共起（001）、「送付される予定となっております」= A-8＋A-6 共起（002）。両検出器が独立に `secondary_categories[]` を提案。重複により A-6 の反復回数が過小計上される実害を確認。
- 出所: detector-A(0612), rewriter-A(0612), rewriter-B(0612), naturalness-A(0612), fidelity-A(0612), **detector-001(0804), detector-002(0804), rewriter-001(0804)**（横断的に最多）
- 提案: 「1 span = 主分類 1 finding」を基本とし、`secondary_categories: []` 配列を許容。category_summary は「findings の主 category 先頭文字を集計」と注記。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: done`（適用 2026-08-04-*） `hits: 2run`
> **適用済(2026-08-04)**: naturalness-reviewer.md §処理に「ai-tell-detector をサブエージェントとして実起動、手動照合は原則禁止」を明記し、実起動不能時のフォールバックを `detector_rerun.method: "subagent"|"manual_fallback"` として schema 化。manual_fallback 時は grade に `(manual-fallback)` を付す。※実起動経路そのものの提供（ランタイム制約）は残課題。
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。
- **再現(2026-08-04)**: 両 naturalness-reviewer とも当該ランタイムで Agent/Task ツールが使えず（サブエージェント内サブエージェント不可）、`ai-tell-detector.md`＋taxonomy の同一基準で手動再走査にフォールバック。IMP-006 が是正対象とする穴そのものが両 run で発火。
- 出所: naturalness-A(0612), **naturalness-001(0804), naturalness-002(0804)**
- 提案: (a) `ai-tell-detector` をサブエージェントとして再呼び出しする経路を必須化。(b) **実起動不能時のフォールバックを明示化**: スキーマに `detector_rerun: {method: "subagent"|"manual_fallback", ...}` を追加し、manual_fallback 時は grade に注記を義務化。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

### IMP-007 confidence フィールドがスキーマ本体に未定義 `status: done`（適用 2026-08-04-*・co-located） `hits: 1run(2agent)`
> **適用済(2026-08-04)**: IMP-002/005 でスキーマを触る際に co-located で `confidence: 0.0〜1.0` を finding に正式追加（taxonomy＋detector.md）。hits:1 だが zero-risk 追加フィールドかつ運用で既に必須化していたため前倒し適用。
- 症状: 運用上 confidence 付与を必須化しているが、taxonomy の「検出出力スキーマ」にも detector.md の例にも confidence フィールドが無い。検出器が独自に付与しており契約が非公式。
- 出所: **detector-001(0804), detector-002(0804)**
- 提案: SSOT スキーマの finding に `confidence: 0.0〜1.0` を正式追加。S1 でも単発・レジスター依存で確信度を下げられるよう `severity_context` 併記も検討（下記 IMP-008 と連動）。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md`

### IMP-008 S1 に密度・レジスター変調がなく「無条件除去」と「過検出禁止」が衝突 `status: open` `hits: 1run`
- 症状: A-1「において」/A-2「については」は taxonomy 上 S1 固定だが、公的通知では単発なら人間も使う許容表現。「S1 は無条件除去」原則と「単発を過検出しない」原則が S1 で衝突。detector-002 は confidence を 0.70〜0.75 に落として表現。
- 出所: **detector-002(0804)**
- 提案: S1 にも「単発時は confidence/severity を文脈で下げる」ルール、または `severity_context` フィールド追加。
- 影響: `ai-tell-taxonomy.md §深刻度の基準`, `ai-tell-detector.md §密度判定`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
> **2026-08-04 更新**: 下記 0804 由来の5候補は taxonomist が審査し taxonomy v1.1 §拡張候補欄に実例つきで記録済み（番号未付与＝同一 run 単一由来のため昇格保留、次 run で 2run 再現が取れ次第 v1.2 で番号付与）。所見: 可能の状態化→A-5 サブ / 定義口調→secondary_categories 捕捉で新設不要 / 確定事実の伝聞化→G-1 サブ or 新 G-3 / 主題提示の過丁寧化→A-2 敬体バリアント / K 官庁敬語→新設保留。

- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 001(0612)。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B
- **A-5/A-6 複合: 可能の状態化「〜が可能になります／〜できるようになります」** 単なる「〜できます」を状態変化に見せる AI 特有形。実例2件(0804-001): 「セマンティックな検索を実現することが可能になります」「生成することができるようになります」。 `hits: 1` 出所 detector-001
- **A-13＋B-2 複合: 定義口調「〜という＋抽象カタカナ名詞」** 概念導入を毎回「XというY」で処理。実例2件(0804-001): 「ベクトルデータベースというテクノロジー」「類似度検索というコンセプト」。 `hits: 1` 出所 detector-001
- **G 系: 確定事実の伝聞化「〜とされております」** 制度上確定した事実まで伝聞（G-1）×最上級敬語で処理する公文 AI 固有クセ。実例2件(0804-002): 「65歳となる方とされております」「望ましいとされています」。 `hits: 1` 出所 detector-002
- **A-1/A-2 敬語硬化形: 主題提示の過丁寧化「〜につきましては／におかれましては」** 実例2件(0804-002): 「詳細につきましては」「対象となる方におかれましては」。現行 A-1/A-2 は普通体想定で公文バリアント未収載。 `hits: 1` 出所 detector-002
- **K. 官庁敬語の冗長（新カテゴリ候補）** 「〜していただく必要がございます／〜することが求められます／〜いただきますようお願い申し上げます」等の公文特有の義務・要請テンプレ。現状 I-3/I-4/A-8 に分散して拾うため行為者取り違えリスク。実例(0804-002 多数)。 `hits: 1` 出所 rewriter-002

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019（並列→基盤の序列混入）はこの項が無く #5/#11 へ漏れ込んだ。`status: ready` `hits: 1` 出所 fidelity-A(0612)
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。**再現(0804)**: fidelity-002 が change_rate 0.40 案件で原文18要素を全数照合し欠落ゼロを確認、high-change-rate 案件での標準手順化の有効性を実証。fidelity-001 も after="" 完全削除 edit の命題性チェック項の必要を指摘。`status: ready` `hits: 2` 出所 fidelity-B(0612), fidelity-001+002(0804)
- **[新] #7 modality の段階判定（modality-band 照合）** 「ヘッジ除去可否」だけでなく原文モダリティの強度バンド（可能/助言/推奨/必要/義務）を跨いでいないかを判定。公文は「望ましい/必要がある/求められる」を制度上の効力差として使い分けるため一本化で平準化リスク。実例(0804-002) f015「望ましい→ください」。`status: open` `hits: 1` 出所 fidelity-002
- **[新] #9/#11 隙間: 行為者明示化の妥当性（agent-insertion check）** A-8 能動化で非明示行為者に新規主体を挿入する際、原文の帰属範囲を超えないか（国policy/厚労省の一般推奨を市に誤帰属しない）。`status: open` `hits: 1` 出所 fidelity-002
- **[新] #7 修辞ヘッジ vs epistemic ヘッジの判別基準** D-1 常套結び（除去は推敲役任務）と命題の不確実性を表すヘッジ（fidelity で保護）を区別する共有ルール。実例(0804-001) f024「と言えるでしょう」削除がこの継ぎ目に乗る。`status: open` `hits: 1` 出所 fidelity-001
- **[新] N/A と pass の区別** 対象不在の pass（#1/#3/#13）と対象ありで合格の pass を status で区別（`status:"n/a"`）。`status: open` `hits: 1` 出所 fidelity-001
- 「情報を含む削除 vs ボイラープレート削除」二分判定: 削除 span に (a)数値/固有名詞/日付 (b)条件/因果節 (c)固有の例示 を含めば情報欠落、挨拶/CTA/装飾/自己言及のみならボイラープレート。出所 fidelity-B
- #5論理関係 と #11情報追加 の責任境界を一意化（主因項目を 1 つに正規化）。出所 fidelity-A
- modality 強度を順序尺度化（要請/推奨/義務/必須）。出所 fidelity-A

### playbook レシピ追補
- **[新] A-8 手段系「によって」の分散候補表** playbook A-8 は「政府が定めた（行為者主語化）」のみで、無生物・変換等の手段の「によって」の受け皿が薄い。「で／により／ことで／すれば」を追記。`status: ready` `hits: 1` 出所 rewriter-001
- **[新] IT 技術記事向けカタカナ変換辞書＋維持ホワイトリスト** テクノロジー→技術/アプローチ→手法/プロセス→処理/コンセプト→概念/パフォーマンス→性能/スケーラビリティ→拡張性/アドバンテージ→強み/ナレッジ→知識/レスポンス→応答。維持: コンテキスト/パイプライン/クエリ/インデックス/エンベディング等の技術文脈語。`status: ready` `hits: 1` 出所 rewriter-001
- **[新] A-8 能動化の主語復元対応表（公的文書）** 「助成が行われる→市が助成／送付される→市が送付／持参が求められる→対象者が持参」。行為者誤りは公文で意味毀損に直結。`status: ready` `hits: 1` 出所 rewriter-002
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
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。出所 detector-A
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B
