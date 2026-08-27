# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-08-27（run 2026-08-27-001 技術解説, -002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。Sample A も 47.6% と高止まり。
- 再現(2026-08-27-001): 「解決することが可能となっています(14字)→解決できます(4字)」の等価圧縮で del+ins 合算 combined 0.35（片側換算 0.20）。純圧縮を二重計上し 30% 警告が誤発火。rewriter-A/naturalness-A/fidelity-A が横断的に「片側換算を既定に昇格せよ」と再指摘。
- 出所: rewriter-A, rewriter-B, naturalness-B（day0）／ rewriter-A, naturalness-A, fidelity-A（2026-08-27-001）
- 提案: (a) 「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を change_rate から控除。(c) 挿入率を単独併記し、del≫ins の削除主導ケースは中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done(2026-08-27-001)` `hits: 2run`
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える（Sample A raw106→92.5、taxonomy 例は raw56→71.5 と不整合）。
- 再現(2026-08-27): detector-001 は raw 106.5 を「100字あたり加重和クリップ」だと score 13.3（14件S1が「クリーン」誤表示）→ 暫定 REF=15 で 89.0 を運用。detector-002 は raw/長×1000 で 48.9 と別式を採用し**run 間非互換が実証**。
- 適用(2026-08-27-001): taxonomy §検出出力スキーマに正規化式 `score = min(100, (raw/文字数×100) / REF × 100)`（**REF=15**＝100字あたり加重和15点で満点）を明文化。ai-tell-detector.md にも同式を記載。REF は day0/今日の実データで暫定較正、要再較正フラグ付き。
- **審査所見(taxonomist)**: 初回適用稿は REF=0.15 で両 run が 100 に飽和し saturate 不具合を再導入していた（factor-100 単位取り違え）。taxonomist が per100 基準の REF=15 に訂正、検算(89.0/32.6)を SSOT に常設。→ スコア節に「較正値に一致する worked example を常設し検出器に per100 と最終値の両方を記録させる」CI 的自己検証を次サイクル課題として起票。taxonomy は v1.0.1 に記録。
- 出所: detector-A, detector-B（day0）／ detector-001, detector-002（2026-08-27）
- 提案: 飽和しにくい正規化を SSOT 明記（例 `100*(1-exp(-raw/k))` か「100字あたり加重和」）。分母（input_length 依存 or 固定 max）を確定。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出`

### IMP-003 score_before のフィールド契約が曖昧 `status: done(2026-08-27-001)` `hits: 2run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score 92.5）。レビュアーごとに数値がぶれる。
- 再現(2026-08-27): naturalness-001/002 とも「score_before=meta.severity_weighted_score を継承」で運用（89.0 / 48.9）。契約が未明文ゆえオーケストレーター指示で補った＝仕様欠落が再現。
- 適用(2026-08-27-001): naturalness-reviewer.md に「score_before = 02_detection.json の meta.severity_weighted_score を厳密継承」を明記。score_after も同一正規化係数を適用する旨を追記。
- 出所: naturalness-A（day0）／ naturalness-001, naturalness-002（2026-08-27）
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run`
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
- 再現(2026-08-27): detector-001 は A-5 6回/A-6 4回/A-8 4回/E-2 を単一 span で 23 個の独立 finding に分割（実体は数パターンの反復、category_summary A=23 が過大表示）。detector-002 は E-2/受動リズムを start:0,end:685 の全文 span で代用し density 破綻を手動回避。両 run で `scope:"document"` と `scattered spans:[]` 追加を要求。**次サイクルの最優先適用候補**。
- 出所: detector-B, detector-A（day0）／ detector-001, detector-002, rewriter-A（2026-08-27）
- 提案: `span_type: "contiguous"|"scattered"|"document"` と scattered 用 `occurrences: [[s,e],...]` を追加。density は重複・locator を除いた実 AI クセ文字数ベースと定義。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。
- 再現(2026-08-27): detector-001 で f020「解決することが可能となっています」が A-5＋A-6 重複 → density を区間マージ長 329字 で算出し回避。rewriter-001 で隣接4組（f013/f014 等）が区間重複し `merged_into`/`merged_spans` フィールドを要求。density は「マージ長で計算」を SSOT 明記すべきと再確認。
- 出所: detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A（day0）／ detector-001, rewriter-001（2026-08-27）
- 提案: 「1 span = 主分類 1 finding」を基本とし、`merged_findings: [...]` 配列を許容。category_summary は「findings の category 先頭文字を集計」と注記。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: done(2026-08-27-001)` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。
- 再現(2026-08-27): naturalness-001/002 とも「サブエージェントからの ai-tell-detector ネスト起動が不可」で `detector_rerun.path = manual_criteria_match` を明示採用。仕様の「検出器再実行必須」がサブエージェント階層では物理的に実行不能と実証。
- 適用(2026-08-27-001): 仕様を現実に合わせ、naturalness-reviewer.md §処理 に「① 可能ならネスト起動 ② 不可の場合は同一基準の手動照合を行い `detector_rerun.path` フィールド（`nested_agent`|`manual_criteria_match`）に必ず記録」を明文化。手動時の一貫性ガード（元検出の非フラグ語を再フラグしない）も規定。
- 出所: naturalness-A（day0）／ naturalness-001, naturalness-002（2026-08-27）
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 001。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B
- **A-6b 受動＋「こととなる/なっている」二重責任回避 [S1]**（公的文書固有）「停止されることとなりました」「延長される措置が取られることとなっております」。A-8受動と A-6状態叙述が必ず連結し決定・実行主体を完全に消す最強シグネチャ。現 taxonomy は両者を別項目で扱い深刻度が分解され過小評価。実例2件(2026-08-27-002 f002,f009)。 `hits: 1` 出所 detector-002, fidelity-002。→**次サイクルで detector-A 系の再現が付けば昇格**。
- **A-5 変種「〜することが可能（です/となっています）」** A-5「することができる」と同義の可能冗長形。実例「解決することが可能となっています」「実現することが可能です」(2026-08-27-001)。A-5 のシグネチャ例文に明示追加を提案。 `hits: 1` 出所 detector-001
- **D 系 導入公式「本記事では〜解説します/今回は〜について解説します」** D-1 の締め公式（いかがでしょうか）と対称の「AIブログ冒頭公式」。C-6 案内文ボックスとは別物。実例(2026-08-27-001 L1)。 `hits: 1` 出所 detector-001, rewriter-001

### 新規 IMP（2026-08-27 起票）
- **IMP-007 modality 5軸尺度化** 可能/断定/推量/義務/必要 を軸化し「軸移動＝fail・同軸内±1段＝pass＋caveat」の階梯を定義。check7 の定性判定が f026(可能→断定=軸越え=fail) と f022(求められる→欠かせない=必要軸内=pass) を同物差しで裁けない問題を解消。`status: ready`（day0「modality 順序尺度化」と合流し 2run 相当）`hits: 2run` 出所 fidelity-A(day0), fidelity-001(2026-08-27)。影響 `ai-tell-taxonomy.md`, `content-fidelity-auditor.md`
- **IMP-008 敬体ジャンルの「主語省略能動化」レシピ** playbook A-8 の After は行為者を主語に立てる例のみ。公的お知らせでは主体自明で主語明示は「当館が更新し当館が停止し…」の慇懃な主語連呼＝過推敲を招く。今回全A-8を主語省略＋動詞能動化で処理。playbook A-8 に変種レシピ追記。`status: ready` `hits: 1run(rewriter-002,naturalness-002)` 出所 2026-08-27-002
- **IMP-009 I-3 敬体変種の処方テーブル** I-3 は常体前提（すべきだ）のみで「必要がございます」の着地先がない。二系統: 読者に動作を促す→尊敬語依頼「〜ください」／事務案内→「〜いただきますようお願いいたします」。playbook I-3 に敬体行追加。`status: ready` `hits: 1run(rewriter-002,fidelity-002)` 出所 2026-08-27-002
- **IMP-010 過推敲シグナル「不要な主語明示（主語連呼）」（公的文書ジャンル固有）** 受動→能動化が主語連呼を誘発しやすいジャンルで専用ガードが要る。naturalness の過推敲定義に追加。`hits: 1` 出所 naturalness-002
- **IMP-011 文末語尾 unique 種類数/文数 を E-2 補助指標に** 語尾 n-gram の種類数で「敬体維持のまま単調解消」を機械判定、常体混入による偽の多様化と切り分け。`hits: 1` 出所 naturalness-002
- **IMP-012 A-2「について/につきまして」の網羅列挙フロー** 1つだけ拾って他を落とすと推敲後に「消し残し」S3 が残る（2026-08-27-002 で原検出が f012 のみ拾い2件取りこぼし→再走査で顕在化）。文書全体をスパン網羅列挙してから密度判定すべき。`hits: 1` 出所 detector-002, naturalness-002

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
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。出所 detector-A
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B
