# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-09-02（day1 run 001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。Sample A も 47.6% と高止まり。
- 2026-09-02 再現: 002 は挿入 43／削除 152 の削除偏重が合算 0.283 に埋もれた（rewriter-002）。001 は主語移動（f006）が del+ins で二重計上され「見かけ 0.28・実改変はより低い」（rewriter-001）。fidelity-002 は「変更率 21%表層に対し意味変化ほぼゼロ」と change_rate と fidelity の無相関を実証。
- 出所: rewriter-A, rewriter-B, naturalness-B ／ 2026-09-02: rewriter-001, rewriter-002, fidelity-002
- 提案: (a) 「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を change_rate から控除。(c) 挿入率を単独併記し、del≫ins の削除主導ケースは中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。(e) 語順移動（move）は Levenshtein で 1 回計上とする補正。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done(2026-09-02-001/002)` `hits: 2run`
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える（Sample A raw106→92.5、taxonomy 例は raw56→71.5 と不整合）。
- 2026-09-02 再現: detector-001 は 821字/25件で raw=84.5 が **100.0 に完全飽和**（S1×13）。detector-001/002 とも仕様に式が無いため**各自が独自に `raw/60*100 cap` を発明**し値がエージェント依存に。naturalness-001/002 も同じ /60 を逆算採用。「かなりAI」と「壊滅的AI」を区別不能。
- 出所: detector-A, detector-B ／ 2026-09-02: detector-001, detector-002, naturalness-001, naturalness-002
- 適用(2026-09-02): taxonomy §検出出力スキーマに正規化式 `score = 100*(1-exp(-raw/40))` を明記、`ai-tell-detector.md` に反映。v1.0→v1.1。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出`

### IMP-003 score_before のフィールド契約が曖昧 `status: ready` `hits: 1run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score 92.5）。レビュアーごとに数値がぶれる。
- 出所: naturalness-A
- 提案: 「score_before = 02_detection.json の meta.severity_weighted_score」と明文化。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: done(2026-09-02-001/002)` `hits: 2run`
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
- 2026-09-02 再現: detector-001 で C-1「まず・次に・最後に」が 527/549/585 の**3 離散 span**に散在するが単一 start/end に固定せざるを得ず、推敲役が残り 2 span を span-grounded に触れない懸念。E-2 文末単調は文書全体の性質で便宜上 start=0/end=821 とし density から手動除外して回避。
- 出所: detector-B, detector-A ／ 2026-09-02: detector-001
- 適用(2026-09-02): schema に `scope: "span"|"document"`（document は density 計算対象外）と scattered 用 `text_spans: [[s,e],...]` を追加。density は span 和集合文字数で計算と明記。v1.1。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。
- 2026-09-02 再現: rewriter-001（統合 edit に `edit_group` 要望）、rewriter-002（`merged_with` フィールド要望）、fidelity-001/002（統合 edit の部分ロールバックを finding_id 単位で局所化できない）。
- 出所: detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A ／ 2026-09-02: rewriter-001, rewriter-002, fidelity-001, fidelity-002
- 提案: 「1 span = 主分類 1 finding」を基本とし、`merged_findings: [...]`／edit 側 `edit_group`・`merged_with` を許容。category_summary は「findings の category 先頭文字を集計」と注記。監査官が統合 edit の部分ロールバックを finding_id 単位で指定できる構造に。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: done(2026-09-02-001/002)` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。
- 2026-09-02 再現: naturalness-001/002 とも「ai-tell-detector サブエージェントを Agent/Task で実呼び出しする手段が本環境に露出していない」ため手動再走査に。妥当化のため両者とも(a)初回と同一スコア式、(b)初回 finding span の推敲文からの消失をプログラム全数照合、で担保した。
- 出所: naturalness-A ／ 2026-09-02: naturalness-001, naturalness-002
- 適用(2026-09-02): サブエージェント spawn が使えない環境を前提に、`naturalness-reviewer.md` に**サンクションされた手動再走査手順**（同一スコア式の固定・全 finding span 消失のプログラム照合・`rescan_method`/`rescan_note` の必須記録）を明記。将来 spawn 可能になれば実呼び出しを優先。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 001。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B
- **A-5 変異形「〜することが可能です／可能になります」** を A-5 サブシグネチャに明記。実例(001): 「実現することが可能です」「取得することができるようになります」(可能+ようになる二重冗長)。現行例文「〜ことができる」だけだと「ことが可能」を取りこぼす。 `hits: 1` 出所 detector-001
- **A-6 進行相「〜になっていく（become 進行）」** を A-6 に追記。実例(001): 「コンポーネントになっていく」。技術記事の結びで頻出。 `hits: 1` 出所 detector-001
- **公的文書の過剰敬語シグネチャ（新カテゴリ候補）** 「対応させていただきます」「賜りますよう」「お願い申し上げます」連発・二重敬語。現状 F-2 重複修飾へ暫定収容だが専用分類が要る。実例(002) 多数。 `hits: 1` 出所 rewriter-002, naturalness-002

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019（並列→基盤の序列混入）はこの項が無く #5/#11 へ漏れ込んだ。`status: ready` `hits: 1` 出所 fidelity-A
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。`status: ready` `hits: 1` 出所 fidelity-B
- 「情報を含む削除 vs ボイラープレート削除」二分判定: 削除 span に (a)数値/固有名詞/日付 (b)条件/因果節 (c)固有の例示 を含めば情報欠落、挨拶/CTA/装飾/自己言及のみならボイラープレート。出所 fidelity-B
- #5論理関係 と #11情報追加 の責任境界を一意化（主因項目を 1 つに正規化）。出所 fidelity-A
- modality 強度を順序尺度化（要請/推奨/義務/必須）＋**モダリティ極性の保存を 13 項の正式1項に固定**。`status: ready` `hits: 2run`。2026-09-02 再現: fidelity-002 が I-3「必要がある→依頼形」を PASS だが ADVISORY として下流へ申し送り、「モダリティ保存が独立項目として無い（A-5できる・I-3必要・G-1ヘッジが主戦場）」と指摘。fidelity-001 も f005/f021 の強調微増を `severity_delta`/`borderline_notes` で暫定記録。出所 fidelity-A ／ 2026-09-02 fidelity-001, fidelity-002
- **fidelity 判定を PASS/ADVISORY/FAIL の三値化 ＋ checks に `not_applicable` 追加** `status: ready` `hits: 2run`。2026-09-02: fidelity-002 が中間（ロールバック不要だが下流必須申し送り）を表す語彙が無く ADVISORY を独自追加。fidelity-001 が「直接引用・出典が原文に存在しない項」を pass で塗ると照合合格と対象なしを区別不能と指摘し not_applicable を要望。出所 fidelity-001, fidelity-002
- 保護トークンは substring 存在一致だけでなく**係り先（役割ラベル）まで照合**すべき（電話番号が別用途に移されても存在すれば PASS になる）。出所 fidelity-002

### playbook レシピ追補
- **C-5 絵文字削除後の文末/区切り吸収ルール**（句点で吸収 or 削除のどちらか明記）。出所 rewriter-B
- **D 系結びは削除一択でなく「最小着地文を残す」**（減らしすぎ下限）。実例: B の「気軽に始めてみてください」。出所 rewriter-B, naturalness-B
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**という例外則。出所 rewriter-A
- **原文が元から推量の D 系は推量を保持**（「断定へ」の一律処方の例外）。出所 rewriter-A
- **公的文書・お知らせ専用の敬語トーンダウン表** `status: ready` `hits: 2run`。「対応させていただきます→対応いたします」「賜りますよう→いただきますよう」「より一層→より」「〜ますようお願い申し上げます→具体依頼/命令形」等、格を保つ許容範囲つき。playbook v1.0 に過剰敬語カテゴリが無く rewriter 裁量に依存し再現性が低い。出所 rewriter-002, naturalness-002（同一 run のため hits は暫定 2、次の day1 サイクルで別 run 確認）
- **I-4 の「求められる除去」と「行為者明示」を分離**。原文に主体記述が無い一般解説では主語補完が未裏付けの追加（鉄則違反）になるため、"主体が原文に無い場合は必要性語彙（欠かせません等）へ退避" の分岐を明記。出所 rewriter-001
- **B-2「シームレスに解決」型の空虚な強調副詞用法**は「滑らかに」だと不自然。連続性／空虚強調で 2 訳を分けるか後者は削除許容と注記。出所 rewriter-001

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
- **ジャンル別 B-2 許容カタカナ辞書** を references に追加。技術記事で「置換すべき(ソリューション/シームレス/アプローチ)」と「維持すべき業界標準語(RAG/HNSW/エンベディング/レイテンシ/クエリ/プロンプト/トークン)」の線引きが検出器裁量に依存し過検出/取りこぼしの元。出所 detector-001

### rewriter diff スキーマ
- **`sentence_ending_variety`（文末形の異なり数）** を 03_rewrite_diff に持たせ、E-2 変奏の過小を naturalness 再検出前に自己検知。出所 rewriter-001
- **削除率と挿入率を分離報告**し、削除率が閾値超のとき fidelity-auditor へ重点監査フラグ（IMP-001 と連動）。出所 rewriter-002
