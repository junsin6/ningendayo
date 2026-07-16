# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数（別 run での再現のみ +1）。

最終更新: 2026-07-16（run 001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除・**B-2 カタカナ漢字化の多数**で機械的に膨張。day0-B 54.6%、day1-001 は高密度原文（34件/682字）で round1 44.4%・round2 48.2% と高止まり（いずれも fidelity=pass / 自然度 A）。
- 出所: (day0) rewriter-A, rewriter-B, naturalness-B / (day1) rewriter-001, naturalness-001, round2-rewriter-001
- 提案: (a) 「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を change_rate から控除。(c) 挿入率を単独併記し del≫ins の削除主導ケースは中断対象外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。(e) **change_rate に finding 密度を同時提示**して「高密度ゆえの正当削除」を機械判定可能に（naturalness-001 実証）。
- 追加サブ論点 **IMP-001b（difflib ブロック移動の二重計上）**: round2-rewriter-001 が文順入替（意味不変）を difflib が「削除＋挿入」で二重計上し 0.53>50% 中断域へ誤押上げ。→ 文アライン後の文内編集距離和へ変更、または difflib と併記して過大計上を可視化。`hits: 1run`
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`
- 備考: 本 P0 は 3 ファイル横断で判定ロジックを変えるため回帰リスクが高く、今日は適用せず据置（今日の 001 累積 48.2% は 50% 未満で override 発火せず＝実害なし）。次 run で分離計測式を playbook に限定適用する方針。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done`（適用 2026-07-16、taxonomy v1.1） `hits: 2run`
- 症状: 正規化式・分母が SSOT に無く、検出器ごとに恣意的に発散。day1 実測で detector-001 は raw107→78.3（独自 /0.20/length）、detector-002 は raw31→44.3（per-1000字）と**別式を使用**。高密度短文で 100 付近に張り付き解像度が消える。
- 出所: (day0) detector-A, detector-B / (day1) detector-001, detector-002
- **適用内容**: taxonomy §検出出力スキーマ に length 正規化 + ソフトキャップの canonical 式を明記（`d1000 = (S1×5+S2×2+S3×0.5)/input_length×1000`, `score = 100×(1−exp(−d1000/80))`）。detector.md §スコア算出 も同式に同期。今回 run はプレ v1.1 スコアを使用（値の遡及修正はせず版で切替）。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出`

### IMP-003 score_before のフィールド契約が曖昧 `status: done`（適用 2026-07-16、naturalness-reviewer.md） `hits: 2run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 92.5）。
- 出所: (day0) naturalness-A /（day1）両 naturalness-reviewer が meta.severity_weighted_score を採用し一致（契約提案の妥当性が再現確認）。
- **適用内容**: naturalness-reviewer.md に「score_before = 02_detection.json の meta.severity_weighted_score」と明文化。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: done`（適用 2026-07-16、taxonomy v1.1） `hits: 2run`
- 症状: 絵文字分散・文末単調（E-2）・段落頭反復（C-4）・まず…最後に は分散/文書レベル。単一 start/end では広域 locator にせざるを得ず ai_tell_density が過大化。day1-001 の E-2/C-4 は文書レベルで、round2 まで残存を持ち越した。
- 出所: (day0) detector-B, detector-A / (day1) detector-001, detector-002, naturalness-001
- **適用内容**: taxonomy §スキーマ に `span_type: "contiguous"|"scattered"|"document"`、scattered 用 `occurrences: [[s,e],…]`、および ai_tell_density を「重複除去した union 被覆文字数 / 全体文字数」と定義。detector.md にも文書レベルテーブル（文末形ヒストグラム・段落開始形テーブル）の出力を追加（IMP-007 予防を兼ねる）。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1、A-10＋A-5「実現することができます」等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。day1-001 も `実現することができます`（A-10＋A-5）等で再現、rewriter-002 は f008 が保持対象（延長される）と除去対象（措置が取られます）を 1span に含み分解を要した。
- 出所: (day0) detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A /（day1）detector-001, rewriter-002
- 提案: 「1 span = 主分類 1 finding」を基本とし `merged_findings: [...]` を許容。category_summary は「findings の category 先頭文字を集計」と注記。**検出器が保持/除去の混在 span を分離出力する**（rewriter の誤ロールバック予防）。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: done`（適用 2026-07-16、naturalness-reviewer.md） `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だが day0 レビュアーは手動照合で推定値。
- 出所: (day0) naturalness-A /（day1）両 naturalness-reviewer が `ai-tell-detector` サブエージェント再実行に成功し推定を回避（経路の実効性が再現確認）。
- **適用内容**: naturalness-reviewer.md §処理 で「`ai-tell-detector` をサブエージェントとして再呼び出しし同基準再検出する」ことを**必須**化（手動照合のみは禁止、不可時は notes 明記）。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

### IMP-007 文書レベルクセを 1 次で拾えず 2 次へ持ち越す `status: ready` `hits: 1run(3agent)`
- 症状: E-2 文末単調・C-4 段落頭反復は個々の span を直しても発生する**集約特性**。文単位 finding を全除去した副作用で文末が「ます一色」に揃い、C-1「まず/次に」除去後に段落頭反復が露呈。day1-001 は round2 でこれを潰して初めて A 到達。
- 出所:（day1）round2-rewriter-001, naturalness-001, naturalness round2
- 提案: (a) 検出器に文書レベル走査（文末形ヒストグラム・段落開始形テーブル）を**1 次から必須出力**化（→ IMP-004 適用で detector.md に着手済み、次段で rewriter 側の自己検査を追加）。(b) rewriter に「span 修正後の文書レベル自己検査 1 パス」を義務化し round 消費を減らす。
- 影響: `ai-tell-detector.md`, `japanese-style-rewriter.md`, `SKILL.md`

### IMP-008 rewriter の edit が別の AI クセを自己誘発する `status: ready` `hits: 1run`
- 症状: round1 f031「となることが期待されます」→「大きな期待が寄せられています」で新たな A-8 無主語受動＋D-4 ハイプ＋「大きな」情報付加を自己誘発。round2 f038 で原文回帰して回収。
- 出所:（day1）naturalness round2, round2-rewriter-001, fidelity round2（f038 が check11 情報追加リスクを解消と評価）
- 提案: rewriter に「edit 後ミニ再検出フック」（置換結果が別カテゴリを生んでいないか自己確認）を義務化。
- 影響: `japanese-style-rewriter.md`, `rewriting-playbook.md`

---

## P2 — 分類・レシピ・チェックリスト

### 昇格済みパターン

- **A-14 手段の by/through 型「〜することによって / 〜することで」** `status: done`（適用 2026-07-16、taxonomy v1.1 へ昇格） `hits: 2run`
  - 定義: 英語 by/through の直訳的手段表現。A-3（を通じて）でも A-8（by 受動）でも厳密には拾えない中間帯。日本語の書き手は「〜すれば」「〜すると」「〜することで（軽め）」を使うため露見度が高い。
  - 実例: (day0-B) `質の高い睡眠を確保することによって` / (day1-001) `データをローカルで処理することによって`＠270・`ローカルで完結させることによって`＠452。
  - 処方: 「〜すれば」「〜すると」「〜することで」へ分散。反復時は S2。

### 新パターン候補（taxonomist 審査待ち・hits 1）
- **K 系: 過剰敬語カテゴリの新設** 設計思想は「過剰な丁寧体・敬語」を日本語固有の重心と明記するのに A〜J に対応コードが無く finding 化できない。公的文書では大半の敬語定型はボイラープレートとして保持すべきで、二重敬語・過剰謙譲（「ご返却を予定されている」の ご＋される 等）のみ候補。公的文書では既定 severity を1段下げる/白リスト併設案。実例: 002。`hits: 1` 出所 detector-002
- **A-8 サブフラグ: 主動作受動 vs 被行為者受動** 行為者（当館/市）が一意特定でき告知の主動作＝除去可（実施されることとなりました→実施します）。被行為者（利用者・資料）を主語化する自然受動＝保持（返却期限が延長される・検索機能が改善される）。detector が span を分離出力すれば誤ロールバック減。実例: 002。`hits: 1` 出所 detector-002, rewriter-002, fidelity-002
- **IMP-009 severity reconciliation の明文化** 同一 span で D-6（S3⇄S2）・B-2 テクノロジー（S2⇄S3）が round1 レビューと round2 検出器で割れた。クラスタ崩壊時の降格ルールを taxonomy に単一基準化。実例: 001。`hits: 1` 出所 naturalness-001, naturalness round2

### 品質等級 rubric の穴
- **rubric gap「S1=0 かつ S2>4」の未規定** 等級表は C を「S1 1〜2 or 過推敲2」で発火させるが、day1-001 round1 は S1=0 かつ S2=5 で A/B/C いずれの明示トリガーも正面から拾わない中間帯。accept 不可＝2次推敲要の運用意図から C に着地させた。等級表に「S1=0 だが S2>4 → C/rewrite_round_2」を明記すべき。`hits: 1` 出所 naturalness-001, round2-rewriter-001

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019 型。`status: ready` `hits: 1`（day1 では該当なし＝孤児化なし pass）出所 (day0)fidelity-A, (day1)fidelity-001
- **#14 程度・強調語の無根拠な増減チェック** f031「期待されます→大きな期待が寄せられています」の「大きな」付加は #6量化・#7modality・#11追加のいずれにも属し切らず pass に落ちやすい。独立項化。`hits: 1` 出所 fidelity-001
- **義務強度（modality）の順序尺度化** `必要がある(4)>ねばならない(4)>ください(3)>お願いいたします(2)>幸いです(1)>任意(0)`。Δ≧2段緩和 or 指示帯(3)→要請帯(2)以下越境を要注意フラグに。公的文書 f010 が 4→2 の2段降下（passだが境界）。`hits: 1` 出所 fidelity-002, fidelity-001
- **行為者一意性判定（#9 拡張）** 能動化後の主語が原文の受動態から一意復元可能か（無主語受動の能動化は主体を発明し得る）を独立サブチェック化。`hits: 1` 出所 fidelity-002
- **削除専用サブチェック（deletion-recall）/ 情報 vs ボイラープレート二分** `status: ready` `hits: 1`（day1-001 削除200字は全ボイラープレートで pass 再現）出所 (day0)fidelity-B, (day1)fidelity-001

### playbook レシピ追補
- **公的文書ボイラープレート白リスト節の新設** 「賜りますよう/させていただきます/申し上げます/ご愛顧/ご高配/ご理解とご協力」等を保持対象として明文化。detector 側でも白リスト語を検出除外。`hits: 1` 出所 rewriter-002
- **E-2 のジャンル別分岐** 公的文書=独立変奏せず累積依存・体言止め禁止／コラム=積極変奏。`hits: 1` 出所 rewriter-002, naturalness-002
- **E-1 は「挿入」ではなく分割/結合で緩急**（新情報ゼロ制約下の手順）。`hits: 1` 出所 rewriter-001
- **B-2 免責リストのジャンル条件付きフラグ** 一般解説=開く／技術仕様書=保持。`hits: 1` 出所 rewriter-001
- (day0 継続) C-5 絵文字削除後の文末吸収ルール / D 系結びは最小着地文を残す / 機能が必要な接続詞は削除でなく変奏 / 原文が元から推量の D 系は推量保持。

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 2run`
- ルーティン・モチベーション・マインドフルネス・データドリブン・クラウド・データ・セキュリティ・ネットワーク・アーキテクチャ・テクノロジー・エンジニア 等の定訳が冗長/不自然になる語は B-2 から半免責し残差 S3 固定。day1-001 で「テクノロジー/レスポンス」残存を S2→S3 降格した実例。出所 (day0)naturalness-B, fidelity-A, naturalness-A /（day1）naturalness-001
- **昇格候補**: 次 run で再現すれば playbook に免責リスト節を新設して done 化。

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert）。day1-001 で全 34span 自己検証通過を実施済み。出所 (day0)detector-A, (day1)detector-001
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 (day0)detector-B
- density の分母（タイトル行・改行を含むか）を明記。day1 は全文（改行含む）基準。出所 (day1)detector-001
