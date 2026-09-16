# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した **run 数**（別 run での再現のみ +1）。

最終更新: 2026-09-16（run 001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-002 severity_weighted_score の正規化が未定義で run 間非比較 `status: done(2026-09-16-001/002)` `hits: 2run`
- 症状: 正規化式が SSOT に無く、検出器ごとに別スケーリング。2026-06-12-001 は raw106→92.5、taxonomy 例は raw56→71.5、**2026-09-16-001 は raw90 をそのまま90.0**、**2026-09-16-002 は raw24 を暫定飽和関数で73.6** と、run 間で score が全く比較できない。
- 出所: detector-A/B(0612), detector-001, detector-002（4 agent・2 run で再現）
- 適用(2026-09-16): taxonomy §検出出力スキーマに正規化式を明文化 →
  `score = round(100*(1 - exp(-raw/42)), 1)`、`raw = 5*S1件数 + 2*S2件数 + 0.5*S3件数`。既存2 run（raw106→92.4, raw56→71.6）を近似再現する k=42 を採用。detector/naturalness 双方がこの式を使用。taxonomist 審査で v1.1 昇格。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md`, `naturalness-reviewer.md`

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run`
- 症状: difflib 文字単位 change_rate が構造編集で膨張・削除主導でも膨張。0612-B は 54.6% で誤 hold。**逆に 0916 の2 run は短縮/置換主体で 16〜22% と低く健全**——閾値（30/50%）は"膨張"前提の数字で、短縮型 run の解釈指針が無い。
- 出所: rewriter-A/B(0612), naturalness-B(0612), rewriter-001, rewriter-002（2 run 再現）
- 提案: (a) 「語句改変率(置換)」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を控除。(c) 短縮主体 run は change_rate が低く出るのが健全というベースライン注記を playbook「変更率の数え方」に併記。(d) 50% 中断は「意味改変 edit 比率」基準へ。
- 影響: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`

### IMP-003 score_before/after のフィールド契約が曖昧・算出法が不明 `status: done(2026-09-16-001/002)` `hits: 2run`
- 症状: score_before にどの値を使うか未固定（0612 は 71.5 vs 92.5 でぶれ）。加えて score_after が「検出器実走査値」か「レビュアー推定値」か区別できず、0916 の両 naturalness も推定値のまま出力（notes に警告）。重み付けも S3=0.5(taxonomy) vs S3=1(naturalness-001) と不整合。
- 出所: naturalness-A(0612), naturalness-001, naturalness-002（2 run 再現）
- 適用(2026-09-16): `naturalness-reviewer.md` と taxonomy に明文化 — 「score_before = 02_detection.json の meta.severity_weighted_score」「重みは S1=5/S2=2/S3=0.5 固定」「score_after は IMP-006 の detector 実走査値を用い、スキーマに `score_after_method: "detector_rerun"|"estimated"` を必須化」。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md §スキーマ`

---

## P1 — 仕様の穴

### IMP-006 naturalness-reviewer が検出器を実行せず score_after が推定 `status: ready` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だが 0612・0916 とも手動照合 → score_after が推定値。検出器の重み・density 定義を再現できず run 間非比較。
- 出所: naturalness-A(0612), naturalness-001, naturalness-002（2 run 再現）
- 提案: `ai-tell-detector` をサブエージェントとして rewrite に必須再呼び出し（手動照合禁止）。得た meta.severity_weighted_score を score_after とし `score_after_method="detector_rerun"` を記録。IMP-003 と併せて適用予定（次サイクル候補）。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run`
- 症状: 絵文字分散・文末単調・文長均一（E-1/E-2）は本来 span を持たない文書メトリクスだが、start/end 必須のため代表 span にアンカーせざるを得ず他 finding と重なり density 過大。0916 の両 detector も E-1/E-2 を独立 finding 化できず reason に畳み込み。
- 出所: detector-A/B(0612), detector-001, detector-002（2 run 再現）
- 提案: `scope: "span"|"document"` を追加し文書レベルは start/end を null 許容。scattered 用 `occurrences: [[s,e],...]`。density は重複除外の被覆文字数ベースと定義。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリに該当（0612 の I-4＋B-2＋I-1、0916-001 の f007↔f011・f008↔f012↔f018 等）。edits/findings が 1:1 前提で category_summary が実態を過小評価、density も overlap 二重計上（union で回避）。
- 出所: detector/rewriter/naturalness/fidelity 横断(0612), detector-001, rewriter-001（2 run 再現）
- 提案: 「1 span = 主分類 1 finding」を基本、`merged_findings: [...]` を許容。「edit ログは finding 単位・change_rate と density は全文/union から」を agent 定義に明文化。density 定義を「重複除外の被覆文字数/全体」に修正。
- 影響: 全 .md のスキーマ節, `ai-tell-taxonomy.md`

### IMP-007 checks スキーマに finding_id / severity / edit 追跡が無い `status: ready` `hits: 2run`
- 症状: 04_fidelity_audit の checks は status(pass/fail)のみで、(a)どの check がどの edit を評価したか、(b)「意味毀損」型と「ブライトライン侵犯」型（0916-001 の f005 鉤括弧内改変）の区別ができない。0612 の f019 も単一 edit 複数 check fail で対応付けが散文頼り。
- 出所: fidelity-A(0612), fidelity-001, fidelity-002（2 run・別 run で再現）
- 提案: 各 check に `finding_id: [...]`（評価対象 edit）と `severity: "meaning_corruption"|"bright_line_violation"` を追加。`watch_edits: [{finding_id, reason}]`（今回 pass だが境界事例）を rollback_edits と分離。
- 影響: `content-fidelity-auditor.md §スキーマ`, `ai-tell-taxonomy.md`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）

- **K 過剰敬語（Over-honorification）** ★日本語固有・公的文書ジャンルの主役クセ `status: candidate` `hits: 1run(2agent)`
  - 実例(0916-002): `させていただく＋こと＋となる` の三重積層（実施させていただくこととなりました）、`〜いただきますようお願い申し上げます` 結び定型の4反復、二重敬語・過剰謙譲。現状 E-2（文末単調）へ寄せて分類せざるを得ず主役クセを表現できない。
  - サブパターン案: K-1「〜させていただく濫用」/ K-2「結び定型（お願い申し上げます）の反復」/ K-3「二重敬語・過剰謙譲」。playbook に「謙譲連鎖の段階的減層（させていただく→いたします→します）」「結び定型は文書内1回に集約」「依頼形の分散表（ください／いただければ幸いです／お願いいたします／賜りますよう）」。
  - 出所: detector-002, rewriter-002。**別 run で再現すれば hits:2 で昇格**（次の day1 サイクルで再検証）。
- **鉤括弧の分類: 直接引用 vs 強調カギ括弧** `status: ready` `hits: 1run(3agent)`
  - 実例(0916-001): f005 で推敲役が「強調カギ括弧だから編集可」と独自判断し鉤括弧内「特定することができる」→「特定できる」を改変 → fidelity fail・round_2 ロールバック。禁忌「鉤括弧内引用文の変更禁止」が引用種別を区別せず推敲役に独断余地を残す。
  - 提案: playbook/agent に「鉤括弧内は外部引用/著者言い換えの別を問わず span 編集対象から機械的に除外」ブライトラインを明記。A-5 冗長短縮は括弧外で吸収。推敲役側にプリチェックを設ける（fidelity-first は推敲段階で守る方が手戻り少）。
  - 出所: fidelity-001, naturalness-001, rewriter-001(round_2)。同一 run 内3 agent 収束・実害ありのため P2 内で優先。
- **C 系: redundant restatement**（叙述と箇条書きの二重記載）実例: 0612-001。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式**「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型**「さっそく見ていきましょう」。 `hits: 1` 出所 detector-B

### detector の suggested_fix 品質
- **suggested_fix がハイプ語を温存する**（D-4） `status: ready` `hits: 1run(2agent)`: f020 の suggested_fix「運用に欠かせない」が除去対象「欠かせない」を残し S1 温存 → round_2 発生。D-4 は「構文圧縮」でなく「語彙置換」を必須アクションに紐づけ、fix にハイプ語（欠かせない/不可欠/極めて重要）が残らないか自己検査。出所 naturalness-001, rewriter-001。
- **suggested_fix が文体（常体/敬体）を破る** `status: ready` `hits: 1run`: 0916-001 で detector の fix に常体（蓄積する・わかる）混入、推敲役が手動補正。fix は meta.style に整合させるルールを taxonomy に追記。出所 rewriter-001。
- **suggested_fix の副作用改変を明示**: `fix_scope: span|context` を追加し span のみ置換か文脈整形込みか区別。出所 rewriter-001。
- start/end 自己検証（regex 一致 assert）。絵文字レンジ明示 `\U0001F300-\U0001FAFF`＋`☀-➿`。出所 detector-A/B(0612)。

### A-8 受動の判定境界
- **無行為者受動（〜される・〜られている）が拾えない** `status: ready` `hits: 1run`: A-8 が「によって後置」限定で、公文書多発の行為者省略受動（定められており/義務付けられております 等6箇所）を finding 化できず1件のみ。密度ベースの「行為者省略受動偏重」サブ条件を追加。出所 detector-002。

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← 0612 f019 型。`status: ready` `hits: 1` 出所 fidelity-A。
- **敬語依頼の modality 強度スケール** `status: ready` `hits: 1run`: 〈命令/要請(義務付け・ねばならない) ＞ 依頼(ください・お願い申し上げます) ＞ 願望表明(いただければ幸いです) ＞ 告知〉を reference 化し「同階層内移動=pass／階層跨ぎ=要精査」。免除表現（〜必要はない/ことはない/には及ばない）の等価判定例もサンプル化。出所 fidelity-002。
- 削除専用サブチェック（deletion-recall）／「情報を含む削除 vs ボイラープレート削除」二分判定。出所 fidelity-B(0612)。

### playbook レシピ追補
- **C-5 絵文字削除後の文末吸収ルール**／**D 系結びは最小着地文を残す**／**機能が必要な接続詞は削除でなく変奏**／**原文が元から推量の D 系は推量保持**。出所 rewriter(0612)。
- **公文書トーン保持のジャンル別変奏許容レンジ**（公文書は ください／幸いです まで、体言止めは見出しのみ）。register を落とすと不適切。出所 rewriter-002。

### naturalness 判定の精緻化
- **ジャンル別 severity 補正テーブル** `status: ready` `hits: 1run`: 公文書では無行為者受動・結び敬語を S1→S2 相当に自動ディスカウント。出所 naturalness-002。
- **残存 severity は 02 の原判定を継承し共起消滅で降格しない**（厳格再走査ルール）。grade A↔C を跨ぐ分水嶺。出所 naturalness-001。
- **過推敲シグナルの定量化**: 敬語階層スコア（申し上げます>いたします>です・ます>ください）の原文差分で register_drop を機械検出。severity(minor/major)を定義し major のみ C 判定にカウント。敬体/常体混入は文末二値カウント。出所 naturalness-001/002/A(0612)。
- **`rewrite_round_2` に `scope: targeted|full`** を追加し局所残存なら targeted を渡す。出所 naturalness-001。
- **`cross_flags`**: reviewer が気づいた fidelity 疑義を auditor へ引き継ぐフィールド（0916-001 で naturalness が f005 鉤括弧改変を検知）。出所 naturalness-001。
- 絶対残存数ガード（改善率が高くても S1 1件で C 以下）。0916-001 で実発火（93.3%改善でも S1×1 で C）。出所 naturalness-A/B(0612), naturalness-001。

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 1run(3agent)`
- ルーティン・モチベーション・データドリブン等の定訳。加えて **ジャンル別維持カタカナ語ホワイトリスト**（技術記事: オブザーバビリティ・メトリクス・トレース・OpenTelemetry 等）を references に。出所 naturalness-B(0612), detector-001。
