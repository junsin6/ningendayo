# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数（別 run での再現のみ +1）。

最終更新: 2026-07-11（run 001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready(部分適用)` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。day0 Sample B 54.6%、day1 run001 も 33.5%（語句改変 21.5% / 削除 11.7% / 挿入 0.3% / net −149字）で 30% 警告線超過だが実体は削除主導・fidelity=pass・自然度 A。
- 出所: rewriter-A/B（2run）, naturalness-A/B
- 提案: (a) 語句改変率 / 削除率 / 挿入率を分離計上。(b) 装飾・常套句の純削除分を change_rate から控除。(c) del≫ins の削除主導は中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。
- **部分適用（2026-07-11）**: `naturalness-reviewer.md` に「削除主導 ∧ fidelity=pass なら `grade_impact:none`・等級を下げない」を明文化。残: `03_rewrite_diff.json` の `separated_metrics`（語句改変/削除/挿入/net）＋ `info_bearing_deletion_rate` を**正式スキーマ化**し、SKILL.md 総合判定を語句改変率基準へ切替。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`, スキーマ

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2run` ✅適用 2026-07-11
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き解像度が消える。day0/day1 双方の検出器・レビュアーが恣意的な λ 逆算を強いられた（run001 raw≈137、run002 raw≈31）。
- 出所: detector-A/B（2run）, naturalness-A/B
- **適用（2026-07-11, run 001/002）**: `ai-tell-taxonomy.md §検出出力スキーマ` に正規化式を SSOT 固定 — `severity_weighted_score = round(100·(1−exp(−raw/K)),1)`, `raw = 5·|S1|+2·|S2|+0.5·|S3|`（scope:document 除外）, `K=45`。`ai_tell_density`（union・document 除外）と `input_length`（改行含む全 code point）の定義も明文化。taxonomist が例値4件を計算検証し v1.1 へ昇格。
- 残: 過去 run（day0）の 92.5 等を新式で遡及再計算し統一（任意）。

### IMP-003 score_before のフィールド契約が曖昧 `status: done` `hits: 2run` ✅適用 2026-07-11
- 症状: naturalness-reviewer がどの値を score_before にするか未固定でレビュアーごとにぶれる。
- 出所: naturalness-A/B（2run）
- **適用（2026-07-11）**: `naturalness-reviewer.md` と `ai-tell-taxonomy.md` に「score_before = 推敲前 `02_detection.json` の `meta.severity_weighted_score`」を明文化。score_after は同式・同 K で再算出。
- 残: 検出器出力側に `score_field` 契約タグ（naturalness-A 提案）は未実装。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run`
- 症状: 絵文字分散・文末単調（E-2）・「まず…最後に」は分散パターン。単一 start/end では広域 locator にせざるを得ず ai_tell_density が過大化。day1 でも E-2 が両 run で代表アンカー方式の妥協を強いられた。
- 出所: detector-A/B（2run）, naturalness-A
- 提案: `scope: "span"|"document"`（＋ scattered 用 `occurrences: [[s,e],...]`）を追加。document scope は `start=0,end=input_length`、text_span はカウント根拠のみ許容。density は union・document 除外（**IMP-002 適用時に density 定義側は成文化済み**、scope フィールド自体は未追加）。E/C 系がこの scope を使う。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリに該当（run002 f002+f003=A-8+A-6 隣接、run001 f031-f033 一文複合、A-10 内包 B-2）。edits/findings が 1:1 前提で category_summary が実態とずれる。
- 出所: detector-A/B, rewriter-A/B, fidelity, naturalness（2run 横断で最多）
- 提案: 「1 span = 主分類 1 finding」を基本とし `merged_findings: [ids]` 配列を許容。rewriter edit スキーマにも `finding_ids: []` と `edit_type: "merged_substitute"` を展開。category_summary は「findings の category 先頭文字を集計、finding は重複可・density は union・document scope 除外」と注記。
- 影響: 全 .md のスキーマ節（**density 側の規約は IMP-002 で成文化済み**、merged_findings 配列は未追加）

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: done` `hits: 2run` ✅適用 2026-07-11
- 症状: 仕様は「検出器を同基準で再走査」だが day0 は手動照合で推定値だった。
- 出所: naturalness-A/B
- **適用（2026-07-11）**: `naturalness-reviewer.md §処理` を「`ai-tell-detector` サブエージェントを Agent ツールで実際に再呼び出し（手動照合禁止）」と必須化。day1 は両レビュアーが実際に再走査し score_after を実測（run001 7.1、run002 1.5）。ネスト subagent 呼び出しが機能することを実証。

---

## P2 — 分類・レシピ・チェックリスト

### fidelity チェックリスト追補 `status: done`（#14/#15 適用 2026-07-11）✅
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** `hits: 2run` — day0 で f019（並列→基盤の序列混入）を検出できず #5/#11 に漏れ込んだ欠陥。**`content-fidelity-auditor.md` に #14 として追加（接続語 edit の主管轄・二分基準 内容語への価値付け=fail / 談話標識加算=pass・borderline_notes 記録）**。day1 run001 で類似構造 f021「も」を pass と正しく切り分け、2run で有効性再現。出所 fidelity-A（2run）
- **#15 削除専用サブチェック（deletion-recall）** `hits: 2run` — 削除 span ごとに読者が失う情報を問い、情報担持削除 vs ボイラープレート削除を二分。**`content-fidelity-auditor.md` に #15 として追加**（`deletion_audit`・`info_bearing_deletion_rate`・推敲役 diff との突合で乖離時 rollback）。出所 fidelity-A/B
- 残（未適用）: modality 強度を順序尺度化（要請/推奨/義務/必須）→ **fidelity-A/B が run002 で `modality_ordinal_analysis` を実装、公的文書は「義務アンカー最低1件存在」を必須ゲート化する提案**。`status: ready` `hits: 2run`。#5論理関係 と #11情報追加 の残る責任境界一意化（接続語は #14 で主管轄化済み）。

### info_bearing_deletion_rate の正式スキーマ化 `status: ready` `hits: 1run(3agent)` — 新規
- 症状: IMP-001 の change_rate 超過を「情報担持削除か否か」で機械免責するには、推敲役 diff の自己申告と監査官の検証値を併記し乖離で rollback する経路が要る。day1 は rewriter が独自に meta に追加、fidelity が独立再計算し突合（両 run とも 0.0 一致）。
- 提案: `03_rewrite_diff.json.meta.separated_metrics.info_bearing_deletion_rate`（必須）＋ `04_fidelity_audit.json.deletion_audit.info_bearing_deletion_rate_verified`。乖離時 auto rollback_required。
- 出所: rewriter-B, fidelity-A, fidelity-B（別 run 再現待ち）

### 反復定型の残置下限ルール（最小着地形を残す）`status: ready` `hits: 2run` — 横断昇格
- D 系結びは削除一択でなく「最小着地文を残す」（day0 B「気軽に始めてみてください」、day1 run001「触れてみてください」）＋ I-3「必要がございます」×N 反復は (N−1) を依頼形へ分散し 1 個を必要性陳述として温存（day1 run002）。「反復パターンは全滅させず 1 個の最小着地形を残す」を D 系・I 系横断で明文化。
- 出所: rewriter-B（2run）, naturalness-B
- 影響: `rewriting-playbook.md`（D 系・I 系）

### playbook レシピ追補（未適用）
- **I-3 敬体反復の処方**: playbook §I-3 は常体「すべきだ」変換のみ。公的文書の「〜する必要がございます」反復処方が欠落。上記「最小着地形」ルールと合わせて明記。出所 rewriter-B
- **C-1 3段公式は3手法（削除/談話標識化/内容溶かし込み）へ分散**し機械均一を避ける。出所 rewriter-A（run001 で実践）
- **機能が必要な接続詞・格助詞は削除でなく変奏**（同一語が機能別に複数必要なとき一方を能動化・別形化し語重複を1回に抑制）。出所 rewriter-A
- **原文が元から推量の D 系は推量を保持**（「断定へ」の一律処方の例外）。出所 rewriter-A
- **C-5 絵文字削除後の文末/区切り吸収ルール**。出所 rewriter-B（day0）
- **定着カタカナ語 B-2 半免責リスト**（ルーティン・モチベーション・データドリブン 等）＋技術ドメイン免責語彙（Kubernetes・ポッド・デプロイ 等）を references に分離し検出・推敲で共有。`status: ready` `hits: 2run` 出所 naturalness-B, fidelity-A, rewriter-A

### naturalness 判定の精緻化
- **E-2 到達ラインの OR 条件化 + 公的文書での体言止め免責** `status: ready` `hits: 2run`: 「体言止め1箇所以上で合格」は公的文書と衝突（格を崩す）。「体言止め **または** 文末形態3種以上の分散で合格」に一般化し、公的文書ジャンルは体言止め免責。day1 run002（体言止め0・文末6種分散で E-2 非検出）が2例目。出所 naturalness-B, rewriter-B
- 過推敲シグナルの定量化（severity/value/threshold/grade_impact フィールド化、敬体/常体混入は文末形態二値カウント）。**naturalness-reviewer に grade_impact:none 規約は適用済み（IMP-001 部分適用）**、フィールド標準化は残。出所 naturalness-A/B
- 絶対残存数ガードを grade 表に組込み（改善率が高くても S1 が1件でも A 不可）。**naturalness-reviewer に「絶対残存数を先行ゲート」記述を追加済み**、SKILL.md 等級表への正式条件追加は残。出所 naturalness-A/B
- クラスタ系 finding（B-2 密集・C-1 列挙）のクラスタ崩壊時 severity 降格ルール。出所 naturalness-A

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）を**出力前ゲートとして仕様化**。day1 は両検出器が Python assert を実施し全 span 一致を確認（detector-A/B で再現）。`status: ready` `hits: 2run`
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B（day1 は該当入力なし）
- **suggested_fix の自己チェック**: 検出器の suggested_fix 自体が別カテゴリの tell に該当しないか taxonomy で検証（run001 g001「欠かせない存在です」= D-4 ハイプ語の二次混入）。出所 naturalness-A `hits: 1run`
- **suggested_fix は text_span 内に閉じる**か超過分は別 finding 化（run002 f006 が span 外「において→で」を含んだ）。出所 rewriter-B `hits: 1run`

### 新パターン候補（taxonomist 審査 — v1.1 拡張候補欄に記載済み）
- **候補 C-α「〜していただく必要がございます」= I-3 敬体・授受動詞変種**: run002 で3回反復（208/345/580）。役所文書では人間も稀に使うため密度条件（同一文書3回以上）を昇格要件に付す方針。次 run 再現で昇格。`hits: 1run` 出所 detector-B, rewriter-B
- **候補 D-α 解説AIの「読者誘導・実況」レジスター**: 「見ていきましょう」「〜していきたいと思います」（run001）。既出 D-1「いかがでしたでしょうか」の拡張。`hits: 1run` 出所 detector-A（day0 C-9「さっそく見ていきましょう」と統合検討）
- **候補 A-α 抽象「機能」主語 + により/によって の道具受動**: run001 2件。A-8/A-10 交差。`hits: 1run` 出所 detector-A
- **公的文書の受動許容ライン明文化**（A-8 ジャンル注記）: 能動化しても情報が増えない受動は残置可（S3）、能動主語に戻すと明確に自然化する受動のみ S2。実例 `確認されております`(S2) vs `予想される`(S3)。`hits: 1run(2agent)` 出所 detector-B, rewriter-B
- **D-7 ブログ結び呼びかけ公式**（day0）「今回は〜ご紹介しました」「〜してみてはいかがでしょうか」。`hits: 1` 出所 detector-B
- **C 系 redundant restatement**（day0）叙述と箇条書きが同内容を二重記載。`hits: 1` 出所 detector-A
