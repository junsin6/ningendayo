# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-06-30（run 001 WebAssembly技術解説 / 002 図書館お知らせ公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。Sample A も 47.6% と高止まり。
- **2026-06-30 再現**: run 001（33.2%, del203≫ins70）run 002（34.2%, del187≫ins65）とも削除主導で 30% 警告超過。両 run とも fidelity=pass・自然度 A・過推敲シグナル 0〜1 で、語句改変率は実質 1 割未満。指標が削除を改変と同等加算する欠陥を再実証。出所 rewriter-A/B, naturalness-A。**次の Step4 候補（P0、未適用）**。
- 出所: rewriter-A, rewriter-B, naturalness-B（+2026-06-30 rewriter-A/B, naturalness-A）
- 提案: (a) 「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を change_rate から控除。(c) 挿入率を単独併記し、del≫ins の削除主導ケースは中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2run` ✅適用 2026-06-30-001/002
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える（Sample A raw106→92.5、taxonomy 例は raw56→71.5 と不整合）。
- **2026-06-30 決定的再現（4 agent）**: 同一パイプライン内で式が三者三様に分岐。detector-001/naturalness-001 は k=44.6（taxonomy 例から逆算）で run001 raw109→91.3、detector-002 は **k=18** で run002 raw15→56.5、naturalness-002 は **線形重み 16.5/8/2**(指数ですらない)→10.0。同じ raw が agent ごとに別 score になる欠陥を実データで証明。
- 出所: detector-A, detector-B（+2026-06-30 detector-A/B, naturalness-A/B）
- **適用内容（2026-06-30）**: SSOT に式を確定 → `raw = 5·S1+2·S2+0.5·S3`、`score = round(100·(1−exp(−raw/44.6)),1)`、**k=44.6 固定（基準例 raw56→71.5 から逆算）・input_length 非依存**。検算 raw56→71.5/109→91.3/15→28.6 一致。編集: `ai-tell-taxonomy.md §検出出力スキーマ`＋§バージョン管理 v1.1、`ai-tell-detector.md §スコア算出`、`naturalness-reviewer.md §処理`。taxonomist 審査済み。

### IMP-003 score_before のフィールド契約が曖昧 `status: done` `hits: 2run` ✅適用 2026-06-30-001/002
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score 92.5）。レビュアーごとに数値がぶれる。
- 出所: naturalness-A（+2026-06-30 naturalness-A）
- **適用内容（2026-06-30）**: IMP-002 と同一編集で契約明文化 — `score_before = 02_detection.json の meta.severity_weighted_score`（再算出禁止）、`score_after` は同一式・同一 k=44.6・同一重みで算出。`ai-tell-taxonomy.md`・`naturalness-reviewer.md` に記載。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run`
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
- **2026-06-30 再現**: run001 E-2「14文中13文」を冒頭19字 locator に流用、run002 A-6(6か所)/A-8(7か所)/I-3(4か所)/D-6(5か所)/E-2(全文) を単一 start/end で代表させ reason に位置列挙で凌いだ。f006 は start0/end748 全文 locator で density 手動除外が必要に。**次の Step4 最有力（P1、未適用）**。
- 出所: detector-B, detector-A（+2026-06-30 detector-A/B）
- 提案: `span_type: "contiguous"|"scattered"|"document"` と scattered 用 `occurrences: [[s,e],...]` を追加。density は重複・locator を除いた実 AI クセ文字数ベースと定義。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。
- **2026-06-30 再現**: run001 で A-10 の長節の内側に A-5・B-2 が入れ子（A:14 のうち A-5/A-10 が同一文を二重計上気味）。rewriter-A は f011/f003/f004/f028 等を同一編集へ統合する merged 運用を手で実施。**IMP-002 の score 式が「主分類1 finding 正規化後の件数」を前提にする以上、本件の規約確定は次点で重要**。
- 出所: detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A（+2026-06-30 detector-A, rewriter-A）
- 提案: 「1 span = 主分類 1 finding」を基本とし、`merged_findings: [...]` 配列を許容。category_summary は「findings の category 先頭文字を集計」と注記。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready(部分対応)` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。
- **2026-06-30 再現**: naturalness-A が検出器サブエージェントを実行できず手動照合で score_after を推定（桁・方向は機械カウントで担保と注記）。
- **部分対応（2026-06-30）**: `naturalness-reviewer.md §処理` に「可能なら ai-tell-detector をサブエージェントとして実呼び出し、手動照合時はその旨明記し推定値と断る」を追記。ただしオーケストレーターからの nested agent 経路の保証は未実装のため status は ready 据え置き（本対応は緩和策）。
- 出所: naturalness-A（+2026-06-30 naturalness-A）
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

### IMP-007 検出器に公的文書 formal-register プロファイルが無く取りこぼす `status: new` `hits: 1run`
- 症状: run002（図書館お知らせ）で detected_count が 6 と少なく、公的文書頻出の AI クセを取りこぼした疑い。具体: ①「とさせていただく」連鎖（休館とさせていただく／対応とさせていただく）、②「におかれましては」「賜りますよう」級の重ね敬語が D-6 1span にしか乗らない、③「下記の期間において」の「において」(A-1) が未検出（category A=3 のまま）。
- 出所: rewriter-B, naturalness-B（2026-06-30-002）
- 提案: detector に「公的文書 formal-register プロファイル」を追加し、させていただく連鎖・におかれましては・において 等を S2/S3 で拾う。ジャンル検出と連動。
- 影響: `ai-tell-detector.md`, `ai-tell-taxonomy.md`（I-3 サブ/新 D-7 候補と連動）

### IMP-008 fidelity 出力スキーマに minor 階層が無い（pass/rollback の2値のみ）`status: new` `hits: 1run`
- 症状: 「新事実ではないが含意強度を変える助詞・副詞の追加」（run001 f027「〜まで」）を pass/minor/rollback のどこに置くか、出力スキーマが status=pass/rollback の2値しか持たず minor を記録できない。タスクは minor 判定を要求するのにスキーマが表現不能。
- 出所: fidelity-A（2026-06-30-001）
- 提案: per-edit verdict 欄に "minor" を追加、または rollback_edits とは別に minor_notes[] を設ける。
- 影響: `content-fidelity-auditor.md §出力スキーマ`, `04_fidelity_audit.json` 形

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 001。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019（並列→基盤の序列混入）はこの項が無く #5/#11 へ漏れ込んだ。`status: ready` `hits: 1` 出所 fidelity-A
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。`status: ready` `hits: 1` 出所 fidelity-B
- 「情報を含む削除 vs ボイラープレート削除」二分判定: 削除 span に (a)数値/固有名詞/日付 (b)条件/因果節 (c)固有の例示 を含めば情報欠落、挨拶/CTA/装飾/自己言及のみならボイラープレート。出所 fidelity-B
- #5論理関係 と #11情報追加 の責任境界を一意化（主因項目を 1 つに正規化）。出所 fidelity-A
- modality 強度を順序尺度化（要請/推奨/義務/必須）。出所 fidelity-A
- **modality decision rule（再現待ち）**: 「することができる」の断定化可否＝「常態的動作特性の叙述（許容）」か「契約的・限定的可能性（保持必須）」かで決める判定規則。taxonomy 候補欄 区画2 にも起票。`hits: 1` 出所 fidelity-A（2026-06-30-001）
- **監査の独立性条項**: 検出器の suggested_fix の存在を fidelity pass の根拠に使わない（検出器は自然さ最適化であって fidelity 保証者ではない）。`hits: 1` 出所 fidelity-A（2026-06-30-001）

### playbook レシピ追補
- **C-5 絵文字削除後の文末/区切り吸収ルール**（句点で吸収 or 削除のどちらか明記）。出所 rewriter-B
- **D 系結びは削除一択でなく「最小着地文を残す」**（減らしすぎ下限）。実例: B の「気軽に始めてみてください」。出所 rewriter-B, naturalness-B
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**という例外則。出所 rewriter-A
- **原文が元から推量の D 系は推量を保持**（「断定へ」の一律処方の例外）。出所 rewriter-A
- **A-8 受動の公文書例外**: 公的文書では責任主体をぼかす儀礼受動が許容される面がある。発行主体が自明なら能動化、責任回避の儀礼受動は1〜2回まで許容、というジャンル例外注記を A-8 に追加。`hits: 1` 出所 rewriter-B（2026-06-30-002）
- **E-2 体言止めのジャンル不適合**: 公的文書/お知らせでは体言止めが格を崩す。当ジャンルでは体言止めを避け文末形態の分散で変奏する旨を E-2 に明記（既存の「体言止め1箇所以上で合格」緩和と矛盾するためジャンル条件付きに）。`hits: 1` 出所 rewriter-B, naturalness-B（2026-06-30-002）
- **A-10 格変換の明文化**: 「この技術は（主題）」→「使えば（条件/手段）」のような主題→条件格変換は意味等価なら可、と A-10 レシピに 1 文追加（fidelity #5/#14 との境界安定化）。`hits: 1` 出所 rewriter-A（2026-06-30-001）

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

### taxonomy 運用（taxonomist 審査由来 2026-06-30）
- **hits セマンティクス確定（部分適用）**: 「再現した独立 run 数」と定義し、同一 run 内の複数出現は実例として列挙。候補欄ヘッダに明記済み。昇格条件＝独立 run 2 つ以上で再現 かつ 実例 2 件以上。出所 taxonomist。
- **候補欄を 2 区画化（適用済み）**: 「分類昇格候補（A〜J 新サブ/新番号）」と「規則・処方改善候補（再現条件不要）」を分離。modality rule 等が再現待ちキューに滞留しないように。出所 taxonomist。
- **正規化 k=44.6 の再較正（将来）**: k は単一基準点 raw56→71.5 からの逆算で根拠点が1つ。実 run の raw 分布が偏ったら（例 raw 常時 80-120）等級境界 A:70%+ との相性が崩れうる。数 run 蓄積後に実分布で再較正するか「決定性のための恣意定数」と割り切る旨を明記すべき。出所 taxonomist。
