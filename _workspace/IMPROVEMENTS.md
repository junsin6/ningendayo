# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-09-14（run 2026-09-14-001 技術解説, 002 公的文書）
適用済み(v1.1): IMP-001（変更率分離）, IMP-002（スコア正規化 k=40）, IMP-005（span重複規約）, A-13「〜と呼ばれる」注記。

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done`(v1.1, 適用 run 2026-09-14) `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。2026-06-12-002 は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。2026-09-14-001 も 32.8%（内訳 ins 0.074 / del 0.254）で削除主導の膨張が再現。
- 出所: rewriter-A, rewriter-B, naturalness-B（2026-06-12）＋ rewriter-A, naturalness-A（2026-09-14 再現）
- 適用内容: `insertion_rate`/`deletion_rate`/`substitution_rate(≈min(ins,del))` を分離計上（diff に併記）。中断は substitution_rate 50% 超基準へ。change_rate 30〜50%（超も）で削除主導かつ fidelity=pass・自然度 A/B なら override accept を SKILL.md/playbook に明文化。
- 影響ファイル（適用済み）: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`
- 残課題: substitution_rate は min(ins,del) の近似。真の置換量（同一 span 内の文字差分）を span 単位で積算する実装は v1.2 候補。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done`(v1.1, 適用 run 2026-09-14) `hits: 2run`
- 症状: 正規化式が SSOT に無く、run ごとに検出器が独自式を採用。高密度で飽和（2026-06-12-001 raw106→92.5, 2026-09-14-001 raw94）、低密度公的文書で過小（2026-09-14-002 raw32.5、min(100,raw)では過小）と尺度不整合。
- 出所: detector-A, detector-B（2026-06-12）＋ detector-A, detector-B, naturalness-B（2026-09-14 再現・低スコア側も明示）
- 適用内容: `normalized = round(100*(1-exp(-raw/40)), 1)`、raw = S1×5+S2×2+S3×0.5、k=40 固定を SSOT 確定。meta に `raw_score`/`score_formula` 併記。検算: raw94→90.5, raw32.5→55.6, 歴史 raw106→92.9。歴史 run は旧クランプ式で非互換の注記。
- 影響（適用済み）: `ai-tell-taxonomy.md §スコア正規化`, `ai-tell-detector.md`
- 残課題: 歴史的 run の遡及再計算はしない方針。

### IMP-003 score_before のフィールド契約が曖昧 `status: ready` `hits: 1run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score 92.5）。レビュアーごとに数値がぶれる。
- 出所: naturalness-A
- 提案: 「score_before = 02_detection.json の meta.severity_weighted_score」と明文化。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`
- 2026-09-14 注記: 本 run はオーケストレーターが両 reviewer に「score_before=meta 値(94.0/32.5)」を明示指示したため問題化せず（＝自然再現とはカウントせず hits 据え置き）。仕様固定はまだ未適用。次点で `naturalness-reviewer.md` に1行明記すれば済む軽微適用。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run`
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。2026-09-14 でも E-2 敬体単調・F-4「〜的」散在・「必要がございます」3連が分散表現できず、代表span＋reason 列挙または finding 分割で回避（再現）。
- 出所: detector-B, detector-A（2026-06-12）＋ detector-A, detector-B（2026-09-14 再現）
- 提案: `span_type: "contiguous"|"scattered"|"document"` と scattered 用 `occurrences: [[s,e],...]` を追加。density は重複・locator を除いた実 AI クセ文字数ベースと定義。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`
- 2026-09-14 メモ: v1.1 で density は「和集合被覆」と文言定義済み（IMP-005）だが、scattered を機械表現する構造フィールドは未実装。hits=2 到達・status ready のため**次回適用の最有力候補**（v1.2）。

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: done`(v1.1, 適用 run 2026-09-14) `hits: 2run`
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。2026-09-14 でも A-5×A-6・A-5×I-1・B-2×C-1・A-6×D-1 の重複が再現。
- 出所: detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A（2026-06-12）＋ detector-A, detector-B, rewriter-A（2026-09-14 再現）
- 適用内容: 「1 span = 主分類 1 finding」を基本、任意フィールド `merged_findings:[従カテゴリ]` を許可。`category_summary` は主 category 先頭文字のみ集計、`ai_tell_density` は和集合被覆（重複は一度だけ）と再定義。taxonomy §span重複規約 + detector.md に明記。
- 影響（適用済み）: `ai-tell-taxonomy.md`, `ai-tell-detector.md`

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは検出器プロセスを実呼び出しできず手動再走査 → レビュアーの手動走査と検出器出力に系統差の穴。
- 出所: naturalness-A（2026-06-12）＋ naturalness-A（2026-09-14: 「detector エージェントのプロセス実呼び出し経路が利用できず、同一重み式で手動再走査」と再現報告）
- 提案: `ai-tell-detector` をサブエージェントとして再呼び出しする経路を必須化。当面はオーケストレーターが推敲後テキストで detector を再走査し score_after を確定する運用に切替（reviewer 手動照合の禁止をレビュアー .md に明記）。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`
- hits=2 到達・status ready。次回適用候補（オーケストレーター経路の明文化は低リスク）。

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **「〜と呼ばれる」定義連結の反復** → `status: done`(v1.1) A-13 の注記として適用（2026-09-14）。実例: 2026-09-14-001 でエンベディング／ANN／RAG の 3 連続。定義初出は保持・反復/修飾過多時のみ対象。出所 detector-A, rewriter-A
- **I-6 過剰謙譲連鎖「させていただく/いただく」** taxonomy 拡張候補欄に留置（1 run のみ・公用敬語と誤検出リスク）。実例: 2026-09-14-002「休館とさせていただく／ご利用いただく／行っていただく／確認いただいた」。次 run（公的/ビジネス文書）再現で I-6 昇格。 `hits: 1` 出所 detector-B, rewriter-B
- **英語術語の逐語移植テクニカル名詞句** unstructured data/high-dimensional vector space を語順そのまま「非構造化データ／高次元ベクトル空間」と連結。A-11 と B-2 の中間。技術解説ジャンル特有。 `hits: 1` 出所 detector-A
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 001。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B

### fidelity チェックリスト追補
- **#15 評価語・度合い語の強度保存** 重要/不可欠/必須/主要/画期的/大幅 等のスカラー強度が原文の目盛りからずれていないか（削除・追加・強度移動を一括捕捉）。判定基準案「順序尺度で1目盛り以上ずれたら fail、同位パラフレーズ（重要↔大きな）は pass」。← 2026-09-14-001 の f011（重要→不可欠へ強化）・f023（不可欠削除で減衰）は #7 と #10 に分裂計上され責任境界が曖昧だった。round2 で解消。`status: ready` `hits: 1(2round連続)` 出所 fidelity-A（両ラウンドで一貫要望）
- **diff 横断のネット効果チェック** 同義・類義語の削除と追加が別 span で相殺/移動していないか diff 全体を1パス見る。edit 単位では見えない意味の位置ずれ（語幹重複回避が誘発する連鎖毀損）を拾う。← 2026-09-14-001 で f011 の「欠かせない」導入が f023 の「不可欠」削除を誘発。`status: ready` `hits: 1` 出所 fidelity-A, rewriter(round2)
- **#14(公的文書) 敬語・丁寧度レジスタの保存** ございます→あります／いたす適用可否／接頭語「ご」等の丁寧度低下を意味等価とは別軸で判定。公的/接客文書では丁寧度低下自体が情報（敬意）の毀損。`status: ready` `hits: 1` 出所 fidelity-B
- **modality 義務⇔依頼/勧告の段階基準** 必須/不可欠＞重要＞有用＞補助 の必要性軸と 義務→丁寧命令(ください)→依頼(お願い)→勧告(いただければ幸い) の弱化スケールを明示尺度化。「1段以内かつ指示対象行為不変なら pass、2段以上/期限・必須性喪失なら fail」。特に期日を伴う必須手続きの依頼形化を警告対象に。`status: ready` `hits: 1` 出所 fidelity-B
- **audit 出力に `source_inconsistencies` フィールド** 原文由来の不整合（例 2026-09-14-002 タイトル「蔵書点検」が本文欠落）を推敲毀損（rollback対象）と分離し機械可読に記録。`hits: 1` 出所 fidelity-B
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019（並列→基盤の序列混入）はこの項が無く #5/#11 へ漏れ込んだ。`status: ready` `hits: 1` 出所 fidelity-A
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。`status: ready` `hits: 1` 出所 fidelity-B
- 「情報を含む削除 vs ボイラープレート削除」二分判定: 削除 span に (a)数値/固有名詞/日付 (b)条件/因果節 (c)固有の例示 を含めば情報欠落、挨拶/CTA/装飾/自己言及のみならボイラープレート。出所 fidelity-B
- #5論理関係 と #11情報追加 の責任境界を一意化（主因項目を 1 つに正規化）。出所 fidelity-A
- modality 強度を順序尺度化（要請/推奨/義務/必須）。出所 fidelity-A

### playbook レシピ追補
- **重複回避 < 原意保存の優先則** 反復分散のための語彙変更が原文の評価語・modality 語を削除/強化する場合、重複回避を放棄し原意保存を優先。重複はまず別 span 側を原意等価な別語に振って発生させない。← 2026-09-14-001 の連鎖毀損の教訓。`status: ready` `hits: 1` 出所 rewriter(round2), fidelity-A
- **評価語の「削除 vs 置換」判定＋復元テスト** 削除候補の評価語を消した文を単独で読み、原文の主張が復元できなければ削除でなく置換（B-2 和語化と D-4 削除を分離。例「不可欠なインフラストラクチャ」→和語化のみで「不可欠な基盤」）。`status: ready` `hits: 1` 出所 rewriter(round2), fidelity-A
- **K. ジャンル別保持則（公的文書・法律文書等）** 正当な定型敬語は保持し、AI 的機械定型（I-3 の n 連反復・A-8 翻訳調受動・A-5 可能冗長）のみ除去する二段構え。I-3 敬体分散テーブル {自敬=いたします／依頼=お願いいたします・くださいますよう／勧告=ください} と A-8 能動化ガード（主体が文脈から自然に補える告知のみ能動化、補えなければ受動維持）を収録。`status: ready` `hits: 1` 出所 rewriter-B, detector-B
- **A-5 分散レシピの表化** 「することができる」多発時: (a)可能動詞 (b)断定 (c)述語直叙 の3系へ分散。実例 2026-09-14-001 で4回を機械均一なく処理。出所 rewriter-A
- **B-2 並列カタカナ二連は句単位で開く**（スケーラビリティとパフォーマンス→拡張性と性能）。出所 rewriter-A
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
