# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-07-29（run 001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done` `hits: 2run` `applied: 2026-07-29-001/002`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。06-12 Sample B 54.6%、07-29 run 001 も 46.5%（実質改変 substitution 31.0%）で誤中断の恐れ。
- 出所: rewriter-A/B, naturalness-A/B（06-12 + 07-29 の2run で再現）
- **適用（2026-07-29）**: 二軸方式を導入。`substitution_rate`（主指標・中断判定）/ `pure_deletion_rate`（別掲）/ `deletion_led`（削除主導フラグ）を分離計上。50% 中断は substitution_rate 基準。char-level change_rate は参考値に降格。SKILL.md §総合判定に `override accept`（change_rate 超過でも fidelity=pass・自然度A/B・deletion_led なら accept）を条文化。
- 編集: `rewriting-playbook.md §変更率の数え方`(v1.1), `japanese-style-rewriter.md`, `SKILL.md §総合判定`
- 実証: run 001 は本規則で override accept（change_rate 45.7% / substitution 31.0% / deletion_led=true / fidelity=pass / 等級A）。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2run` `applied: 2026-07-29-001/002`
- 症状: 正規化式が SSOT に無く、検出器ごとに恣意的係数（550・min(100,raw) 等）を使用。短文で飽和、長文で膨張、比較不能。
- 出所: detector-A/B, naturalness-B, rewriter-B（2run で再現）
- **適用（2026-07-29）**: `severity_weighted_score = min(100, (S1×5 + S2×2 + S3×0.5) / input_length × 1000)`（1000字あたり加重和・100クリップ・文書長非依存）を SSOT に確定。検出器は使用式を `meta.score_formula` に明記。ai_tell_density は重複排除の実クセ文字数ベースに精緻化。
- 編集: `ai-tell-taxonomy.md §検出出力スキーマ`（taxonomist v1.1）, `ai-tell-detector.md §スコア算出`

### IMP-003 score_before のフィールド契約が曖昧 `status: done` `hits: 2run` `applied: 2026-07-29-001/002`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。
- 出所: naturalness-A（06-12）, naturalness-A/B（07-29 は指示で固定運用）
- **適用（2026-07-29）**: 「score_before = 02_detection.json の meta.severity_weighted_score」を taxonomy スキーマ節に明文化。IMP-002 と同時適用。
- 編集: `ai-tell-taxonomy.md`（taxonomist v1.1）, 運用は naturalness プロンプトで固定済み。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: done` `hits: 2run` `applied: 2026-07-29-001/002`
- 症状: 絵文字分散・文末単調・文長均一は単一 start/end で表せず ai_tell_density が過大化。両 run の検出器が暗黙拡張（span_type/occurrences）で対処。
- 出所: detector-A/B（2run で再現）
- **適用（2026-07-29）**: finding に `span_type: "contiguous"|"scattered"|"document"` と `occurrences: [[s,e],...]` を正式追加。contiguous 以外は start/end を null 許容。density は重複排除・locator 除外で定義。
- 編集: `ai-tell-taxonomy.md §スキーマ`（taxonomist v1.1）, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリ（I-4＋B-2, A-5＋A-6, A-10＋D-4 等）に該当。findings/edits の 1:1 前提で category_summary とスコアが実態とずれ、二重計上/取りこぼしリスク。07-29 も detector-A/B・rewriter-A/B・fidelity-A で再現。
- 出所: detector-A/B, rewriter-A/B, fidelity-A（2run 横断で最多）
- 提案: (a) finding に `secondary_categories: []`、スコアは主カテゴリのみ加算・density は span 重複排除。(b) diff に `finding_ids: []` と `merged_with`（統合 edit 追跡）。※ diff の finding_ids は 07-29 に rewriter.md へ暫定追記済み。次回スキーマ本体へ正式化。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。07-29 も naturalness-A/B が手動照合を自認。
- 出所: naturalness-A（06-12）, naturalness-A/B（07-29）
- 提案: (a) `ai-tell-detector` をサブエージェントとして再呼び出しする経路を必須化、または (b) 検出ロジックを共有スクリプト `scripts/detect.py` 化し検出器・レビュアーが同一コードを走らせる（naturalness-A 提案）。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`, （新規）`scripts/detect.py`

### IMP-007 公的文書ジャンルの定型敬語 allowlist / ジャンル別 severity 補正が無い `status: open` `hits: 1run(002, 4agent)`
- 症状: 「におきましては／におかれましては／につきましては／お願い申し上げます／させていただいております」は A-1/A-2 上は翻訳調だが自治体文書では準定型。detector は密度過多として finding 化、reviewer は妥当残存として救済 → **detector と reviewer で判定が非対称**。保存すべき最小量と反復閾値が未定義。
- 出所: detector-B, rewriter-B, naturalness-B, fidelity-A（run 002）
- 提案: taxonomy に「公的文書ジャンルでの定型敬語 allowlist（1文書あたり許容回数）」と「ジャンル別 severity 補正（例: 公的文書では敬語変種の A-1/A-2 を1段階減じ密度3回以上でのみ finding 化）」を規定。playbook にも公的文書レシピ節を追加。
- 影響: `ai-tell-taxonomy.md`, `rewriting-playbook.md`, `ai-tell-detector.md`, `naturalness-reviewer.md`

### IMP-008 fidelity 監査の語彙・尺度・責任境界の未整備 `status: ready` `hits: 2run`
- 症状: (a) verdict 語彙が agent 定義 `pass|rollback_required` とタスク `pass|fail` で不一致。(b) #5論理関係と#11情報追加、#9行為者と#11情報追加が重複し主因帰属が曖昧（f025「だからこそ」/f027「企業は」が両項に跨る）。(c) modality に順序尺度が無く推量→断定と程度escalationを同じ fail で括る。
- 出所: fidelity-A（06-12 f019 + 07-29 f025/f027/f018/f023）
- 提案: verdict 語彙統一。#9 を「行為者の新規特定/削除」に一本化し #11 は命題・例・数値追加に限定。「接続語由来の含意混入」を独立チェック項目化。modality を順序尺度（推量3/要請4/断定5/義務・必須…）にし原文値との差分で自動フラグ。S1=無条件差し戻し/S2=オーケストレーター裁量の権限分界を明文化。
- 影響: `content-fidelity-auditor.md`, `ai-tell-taxonomy.md §modality`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査 → 07-29 に v1.1 拡張候補欄へ起票）
- **B-4 和語＋カタカナ二重併記** 「帯域幅（バンド幅）」「攻撃対象領域（アタックサーフェス）」。B-1/B-2 と異なる独自クセ。実例: 001。`hits: 1` 出所 detector-A
- **D-7 メタ導入公式** 「本記事では〜わかりやすく解説できればと思います」。ブログAI冒頭の自己言及前置き。実例: 001。`hits: 1` 出所 detector-A
- **公的文書型 硬い敬語結び句の機械反復** 「〜いただきますようお願い申し上げます」の段落末完全一致反復（3回以上が識別点）。実例: 002。`hits: 1` 出所 detector-B, naturalness-B
- **I-4 拡張「無主体の期待」** 「活用されることが期待されております」。要請でなく期待だが行為者不在。実例: 002。`hits: 1` 出所 detector-B
- **C系 redundant restatement**（叙述と箇条書きの二重記載）実例: 001(06-12)。`hits: 1` 出所 detector-A(06-12)
- **D-7 ブログ結び呼びかけ公式**（「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」）実例: B(06-12)。`hits: 1` 出所 detector-B(06-12) ※メタ導入 D-7 と番号衝突、taxonomist が最終採番
- **C-9 導入誘導定型**（「さっそく見ていきましょう」）実例: B(06-12)。`hits: 1` 出所 detector-B(06-12)

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019/f025 で再現。`status: ready` `hits: 2` 出所 fidelity-A（06-12, 07-29）
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。削除 span に情報種別タグ（gloss/connective/redundant-modal/propositional）を推敲役が付与すれば #10 が機械検証可能。`status: ready` `hits: 2` 出所 fidelity-A/B
- 「情報を含む削除 vs ボイラープレート削除」二分判定。出所 fidelity-B(06-12)
- **item 8（時制・相）に「予定日の有無を先に確認」前提を追加**: 「開始されることとなりました」→「開始されました」は予定日記載のある文書では未稼働を稼働済みと断定する誤りになりうる。`hits: 1` 出所 fidelity-B(07-29)
- **敬語簡略化の情報欠落リスク区別**: 「におかれましては/につきましては」削除は情報無害、「させていただいております」等の許諾・条件を含む敬語簡略化は情報欠落リスク高 → item 10 の重点監視対象。`hits: 1` 出所 fidelity-B(07-29)

### playbook レシピ追補
- **C-5 絵文字削除後の文末/区切り吸収ルール**。出所 rewriter-B(06-12)
- **D 系結びは削除一択でなく「最小着地文を残す」**。出所 rewriter-B, naturalness-B(06-12)
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**という例外則。H 系削除は率目標より「1段落あたり接続詞1個まで許容」の上限規定が実務的。出所 rewriter-A（06-12, 07-29 再現）`hits: 2`
- **原文が元から推量の D/G 系は推量を保持**（断定へ一律処方の例外）。f023 でも再確認。出所 rewriter-A, fidelity-A `hits: 2`
- **中立形（主題「は」等）への収束は反復にカウントしない例外**。出所 rewriter-B(07-29)
- **B-1 読者層（専門/一般）をメタに持たせ併記保持数を条件分岐**。出所 rewriter-A(07-29)

### naturalness 判定の精緻化
- 過推敲シグナルの定量化（敬体/常体混入は文末二値カウントで機械検出）。文体崩れ指標を正式昇格推奨。出所 naturalness-A（06-12, 07-29）`hits: 2`
- クラスタ系 finding は連続量（変奏率）で S2→S3 降格。親 finding が消えたら重畳依存の S3 も自動降格。出所 naturalness-A/B `hits: 2`
- **E-2 到達ライン**: 敬体ブログの自然域を「非ます/です終止 15〜20%」と暫定提案（体言止め等で到達）。出所 naturalness-B(06-12), naturalness-A(07-29) `hits: 2`
- **絶対残存 S1 ガードを grade 表に組込み**（S1 が1件でも C 以下）→ **07-29 SKILL.md に条文化済み**。出所 naturalness-A/B
- 公的文書の「砕けすぎ」（定型敬語削りすぎで事務体裁喪失）も過推敲として計上。文末敬語レベルの下限をジャンル別設定。出所 naturalness-B(07-29)

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 2run`
- ルーティン・モチベーション・データドリブン・ネットワークコスト 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。07-29 でも「ネットワークコスト」等が残置。出所 naturalness-B(06-12), naturalness-A(07-29)

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert）。occurrences 内 offset も同様に検証。出所 detector-A/B（両 run で実際にミス→修正を報告）`hits: 2`
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B(06-12)
