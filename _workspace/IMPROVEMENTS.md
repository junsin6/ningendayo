# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-06-24（run 001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。06-12 Sample B 54.6% で誤発火、06-24 でも rewriter-001/002・naturalness-001 が再現（001 は挿入33/削除116、002 は挿入44/削除118 と削除主導）。
- 出所: rewriter-A/B（06-12, 06-24）, naturalness-B（06-12）, naturalness-001（06-24）
- **適用（2026-06-24-001/002）**: playbook §変更率の数え方を v1.1 化。`insertions`/`deletions` を分離計上し、過推敲の主指標を **`rewrite_intensity`（replace 置換文字数/原文）** に変更。中断（hold_and_report）は rewrite_intensity 50% 超で発火、char_change_rate は警告のみ。`net_compression_ratio` を併記。SKILL.md §総合判定・rewriter.md・rewriter 出力スキーマも同期。
- 影響ファイル: `rewriting-playbook.md`✓, `japanese-style-rewriter.md`✓, `SKILL.md`✓

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2run`
- 症状: 正規化式が SSOT に無く、検出器ごとに値がぶれる（06-12 detector-A/B、06-24 detector-001 raw66.5→70.0 を「件数×5」分母で算出・detector-002 は別分母で 22.9）。
- 出所: detector-A/B（06-12）, detector-001/002（06-24）
- **適用（2026-06-24）**: taxonomy §検出出力スキーマで確定。`raw=Σ(S1×5+S2×2+S3×0.5)`、`score=round(100*(1-exp(-raw/K)),1)`、**K=40 固定**（飽和型・文書間可比）。`meta.weight_formula`/`meta.normalization_K` を必須化。detector.md §スコア算出も同期。既存例 71.5≈raw50 で整合。taxonomist 審査済み（v1.1）。
- 影響: `ai-tell-taxonomy.md`✓, `ai-tell-detector.md`✓

### IMP-003 score_before のフィールド契約が曖昧 `status: done` `hits: 2run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（06-12 で 71.5 vs 92.5 のぶれ）。06-24 でも reviewer が K を逆算する必要があった。
- 出所: naturalness-A（06-12）, naturalness-001（06-24）
- **適用（2026-06-24）**: naturalness-reviewer.md に「score_before = 02_detection.json の meta.severity_weighted_score」「score_after は同じ K を継承」と明文化（IMP-006 と同時適用）。
- 影響: `naturalness-reviewer.md`✓

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run`
- 症状: 絵文字・文末単調・「まず…最後に」・A-5/B-2 の散在は分散パターン。単一 start/end では広域 locator にするしかなく density が過大化。06-24 detector-001（A-5 6箇所を reason に文字列で列挙）・detector-002（E-1/E-2）で再現。
- 出所: detector-B/A（06-12）, detector-001/002（06-24）
- 提案: `span_type: "contiguous"|"scattered"|"document"` と `occurrences: [[s,e],...]` を追加。density は文書レベル span を除外（detector.md には除外規則を暫定記載済み、スキーマ正式化は未）。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`
- 次回適用候補（P0 が片付いたので次点）。

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリに該当（06-24-001 f001 A-10＋f002 A-6 が入れ子で A が 16 に膨張、002 「改定されることとなりました」が A-8＋A-6）。rewriter もオフセット競合で同一文を複合処理。
- 出所: detector-A/rewriter-A/B/naturalness-A/fidelity-A（06-12）, detector-001/002・rewriter-001/002（06-24）
- 提案: 「1 span = 主分類 1 finding」を基本とし `secondary_categories: [...]` 配列を許容。category_summary は主分類で集計。rewriter 仕様に「文単位バッチ適用→適用後オフセット再マッピング」を明記。
- 影響: 全 .md のスキーマ節。次回適用候補。

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: done` `hits: 2run`
- 症状: 仕様は再走査だが手動照合で推定値化。
- 出所: naturalness-A（06-12）, naturalness-001（06-24、K を逆算）
- **適用（2026-06-24）**: detector が `weight_formula`/`normalization_K` を必須出力、naturalness は再計算せず同じ K を継承し検出器再実行で残存を数える、と naturalness-reviewer.md / detector.md に明文化。
- 影響: `naturalness-reviewer.md`✓, `ai-tell-detector.md`✓

---

## P2 — 分類・レシピ・チェックリスト

### fidelity チェックリスト #14（接続語・様態の混入）`status: done` `hits: 2run`
- 症状: 接続語/順序語/様態副詞の置換・追加で原文に無い序列・因果・価値・様態が混入。06-12 f019（並列→基盤の序列）、06-24-001 e018「選定が求められます」→「**慎重に**選ばなければなりません」（様態副詞追加）。
- 出所: fidelity-A（06-12）, fidelity-001（06-24）
- **適用（2026-06-24）**: content-fidelity-auditor.md に #14 を追加（13項→14項）。description・判定例も同期。
- 影響: `content-fidelity-auditor.md`✓

### modality を順序尺度化（必須/依頼/推量の保存）`status: done` `hits: 2run`
- 症状: #7 modality が二値で、昇格（推量→断定）と降格（必須→依頼）を同一に潰す。06-24-002 で 4 件中 3 件が modality 逸脱（v01 期待→断定、v02/v03 必須→依頼）。06-12 でも fidelity-A が順序尺度化を提案。
- 出所: fidelity-A（06-12）, fidelity-001/002（06-24）
- **適用（2026-06-24）**: content-fidelity-auditor.md に modality 順序尺度（断定＞義務＞要請＞推奨＞依頼＞可能＞推量・期待）を追加。epistemic/deontic 2 軸、1 段以上の移動を毀損計上、`requirement-strength-preservation`（公的文書で必須性マーカー保持）を明記。
- 影響: `content-fidelity-auditor.md`✓

### naturalness 等級ガード（絶対残存数 + 低スコア起点）`status: done` `hits: 2run`
- 症状: 改善率だけで等級を決めると、短文・低スコア起点で逆転（06-24-002 改善率67.25%<70% だが S1=0/S2=1 で実質 A）。06-24-001 は S2=4 で改善率87%でも A 不可（B）を絶対残存数ガードが捕捉。
- 出所: naturalness-A/B（06-12）, naturalness-001/002（06-24）
- **適用（2026-06-24）**: naturalness-reviewer.md に `grade=min(改善率ベース, 絶対残存数ベース)` の AND ガードと、`score_before<30` での改善率閾値緩和ガードを明記。`residual_total` を JSON 記録。
- 影響: `naturalness-reviewer.md`✓

### taxonomy 拡張（A-6「こととなりました」/ I-4 公的文書分岐 / 定型敬語）`status: done` `hits: 1run(3agent)`
- 症状: 公的文書で「改定されることとなりました」（A-6 変化叙装い）、「求められます」を依頼形に落とすと必須性降格、定型敬語（お願い申し上げます 等）を AI クセと誤検出しうる。
- 出所: detector-002/rewriter-002/naturalness-002（06-24）
- **適用（2026-06-24, v1.1）**: A-6 に「こととなりました」サブ例、I-4 に公的文書ジャンル分岐＋定型敬語ホワイトリスト注記を追加。taxonomist 審査済み。
- 影響: `ai-tell-taxonomy.md`✓

### deletion-recall test（削除専用サブチェック）`status: ready` `hits: 2run`
- 症状: 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う機構がチェックリストに無い。06-24-002 e004 で因果語「踏まえ」削除が #5 で人手検出されたが自動 recall が無い。
- 出所: fidelity-B（06-12）, fidelity-002（06-24）
- 提案: #10 の手順として「原文の事実ユニット列挙→推敲文に全 recall」を明文化。論理・因果マーカー（踏まえ/ため/ので/が）の削除を diff から自動 recall。次回適用候補。

### 情報含む削除 vs ボイラープレート削除の二分 `status: ready` `hits: 2run`
- 削除 span に (a)数値/固有名詞/日付 (b)条件/因果節 (c)固有の例示 を含めば情報欠落、挨拶/CTA/装飾/自己言及のみならボイラープレート。06-12 fidelity-B、06-24 fidelity-001（「と言えるでしょう」削除は許容 vs「慎重に」追加は不可）で再現。次回 fidelity チェックリストに明文化候補。

### クラスタ崩壊時の severity 降格 `status: ready` `hits: 2run`
- クラスタ依存 finding（A-13「という」, B-2 密集, C-1 列挙）は、母集団クラスタが推敲で壊滅したら寄与重みを減衰（0.5→0.25）。06-12 naturalness-A、06-24 naturalness-001（A-13 が翻訳調クラスタ崩壊後に孤立）で再現。次回適用候補。

### 過推敲の定量化 `status: ready` `hits: 2run`
- 文末形態エントロピー（種類数/文数）・平均文長前後差分・最短文比率を over_polish_signals に数値化。06-12 naturalness-A、06-24 naturalness-001 で再現。E-2 到達ライン（文末種類数≤2 かつ文数≥8 で発火、体言止め/〜でしょう を最低1箇所で合格）も併せて明文化候補。

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 1run(3agent)`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。06-12。06-24 では未再現（技術標準語の維持は検出側で適切に処理された）。

### 新パターン候補（taxonomist 審査・再現待ち、taxonomy 拡張候補欄に記載済み）
- **G-1「〜傾向がある」** 観測型文末。実例: 001「増大する傾向があります」。`hits: 1`
- **A-5 サブ型** A-5a 可能の冗長 / A-5b 可能+となる二重冗長（「することが可能となる」）。実例: 001 f004。`hits: 1`
- **「〜ております/ておりません」過剰丁寧進行形** 密度＋文末比率の二条件で閾値化。実例: 002 3回。`hits: 1`
- **politeness_downgrade（公的文書の格・丁寧さ低下）** naturalness の over_polish_signal 候補。能動化・短文化で命令調に振れる検知。出所 naturalness-002。`hits: 1`

### detector 実装（既出・継続）
- start/end 自己検証（regex マッチ位置と text_span 一致を assert）→ 06-24 両 detector が実施済み（運用定着）。
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。
