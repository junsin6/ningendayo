# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-06-19（run 2026-06-19-001 技術解説／-002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done` `hits: 2run` ✅2026-06-19 適用
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。day0 Sample B は 54.6% で `hold_and_report` 誤発火。**2026-06-19 再現**: 001 が 40.3%（削除219:挿入68）、002 が 35.2%（削除153:挿入49）でいずれも削除主導・fidelity=pass・自然度Aだが 30% 警告に張り付き。
- 出所: rewriter-A, rewriter-B, naturalness-A（day0 含め 3 agent × 2 run）
- **適用内容（2026-06-19, run 001/002）**: `delete_rate` / `insert_rate` を分離計上。中断判定は `insert_rate`（挿入主導＝意味改変）を主指標化。`insert_rate` ≤ 0.20 の高 change_rate は冗長剥がしとして警告のみで続行。`change_rate` 50% 超 **かつ** `insert_rate` 25% 超のみ `hold_and_report`。複数ラウンドは最終文対原文で全体再計算。SKILL §総合判定に override accept 行を追加。
- 影響ファイル（編集済）: `rewriting-playbook.md §変更率の数え方`(v1.1), `japanese-style-rewriter.md`, `SKILL.md §総合判定`

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2run` ✅2026-06-19 適用
- 症状: 正規化式が SSOT に無く高密度短文で raw が 100 付近に飽和。**2026-06-19 再現かつ悪化**: 2 つの検出器が**別々の式**を独自採用（detector-A `100×(1-exp(-0.18×per100))`=87.3 / detector-B `min(100,per100/8×100)`=63.0）。同一基準が無く再現性ゼロを実証。
- 出所: detector-A, detector-B（day0 含め 2run）
- **適用内容（2026-06-19, taxonomy v1.1）**: §検出出力スキーマに唯一の正規化式を確定（per100=100字あたり加重和、`score=100×(1−exp(−per100/K))`、K 固定）。`meta` に `s1_count/s2_count/s3_count` を追加し品質等級ゲートを score から独立化。
- 影響ファイル（編集済）: `ai-tell-taxonomy.md §検出出力スキーマ`(v1.1)、（要追従）`ai-tell-detector.md §スコア算出`

### IMP-003 score_before のフィールド契約が曖昧 `status: ready` `hits: 2run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。
- **2026-06-19 状況**: 両レビュアーへ「score_before = meta.severity_weighted_score（87.3 / 63.0）」を指示し正しく運用された（IMP-003 の処方が有効と再確認）。ただし `naturalness-reviewer.md` への明文化は未実施＝プロンプト依存のまま。
- 出所: naturalness-A（day0）, naturalness-A/B（2026-06-19）
- 提案: `naturalness-reviewer.md` に「score_before = 02_detection.json の meta.severity_weighted_score」を明記（次回適用候補。1行で済む durable 化）。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: done` `hits: 2run` ✅2026-06-19 適用
- 症状: 文末単調・文長均一・絵文字分散は単一 start/end で表せない。**2026-06-19 再現**: 両検出器が E-1/E-2 で start/end=-1 や代表 span を苦慮（detector-B は明示的に「scope フィールドが要る」と報告）。
- 出所: detector-B, detector-A（day0 含め 2run）
- **適用内容（2026-06-19, taxonomy v1.1）**: finding スキーマに `scope: "span"|"scattered"|"document"` を追加。scattered 用 `occurrences:[[s,e],...]`、document は start/end 不要。文書レベル finding は ai_tell_density 分子に算入しない旨を明記。
- 影響ファイル（編集済）: `ai-tell-taxonomy.md §スキーマ`(v1.1)、（要追従）`ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い（多重ラベル）`status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリに該当。**2026-06-19 再現**: 001 で「レジリエンスを提供する」が A-10＋B-2、002 で f003 が A-5＋A-6＋A-8 三重。naturalness-A は「f008 が B-2 だけ直し A-10 を取りこぼした部分修正」を S1 残存として検出（多重ラベルが無いと残存がすり抜ける実害が出た）。
- 出所: detector-A, detector-B, rewriter-A, naturalness-A, fidelity-A（横断的・2run）
- 提案: finding に `secondary_categories: []` を許す多重ラベルを正式採用。category_summary は主分類で集計。推敲役は多カテゴリ span の全カテゴリ消化を逐一照合。
- 影響: 全 .md のスキーマ節（次回適用最有力）

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合になりがち。
- **2026-06-19 状況**: プロンプトで「taxonomy 基準で再走査（可能なら detector 再呼び出し）」を指示し改善。ただし `naturalness-reviewer.md` 本体への経路明記は未実施。
- 出所: naturalness-A（day0）, naturalness-A/B（2026-06-19）
- 提案: `naturalness-reviewer.md §処理`に ai-tell-detector サブ呼び出し経路を必須化として明記。
- 影響: `naturalness-reviewer.md`, `SKILL.md`

### IMP-007 fidelity の status が pass/fail 二値で「毀損未満ドリフト」を表現できない `status: open` `hits: 1run(1agent)`
- 症状: 001 の自動詞化（高める→高まる、向上させる→上がる）は「行為→状態変化」で能動的因果がわずかに背景化するが毀損ではない。fidelity-A は独自に `fail_soft` を導入したがスキーマ逸脱で下流が解釈不能。
- 出所: fidelity-A（2026-06-19）
- 提案: `status: pass` + `severity: minor_drift` の構造化フィールド、または `pass|minor_drift|fail` の3値化。自動詞化の判定3条件（①行為者が同一/直前文に残る ②主張が現象へ縮退しない ③効果の確定性が下がらない）を項目7/9のサブ基準に明文化。
- 影響: `content-fidelity-auditor.md`, `ai-tell-taxonomy.md §スキーマ`

### IMP-008 span 外波及 edit（out_of_span）の運用規約が無い `status: open` `hits: 1run(2agent)`
- 症状: 002 で推敲役が検出 finding の無い「変更されることをお知らせいたします」→「変更いたします」を独断修正（f005a）。fidelity=pass だったが鉄則2（span-grounded）違反のグレーゾーン。検出器が A-6/A-8 複合「〜されることを〜いたします」を取りこぼした検出側の穴でもある。
- 出所: rewriter-B, fidelity-B（2026-06-19・2agent）
- 提案: (a) 厳格運用＝span 外は触らず検出器へ差し戻して finding 化、または (b) `out_of_span: true` フラグ＋隣接 finding_id を必須記載し監査官が個別審査。warnings 記載は good practice なのでスキーマ昇格。
- 影響: `japanese-style-rewriter.md`, `content-fidelity-auditor.md`, `03_rewrite_diff` スキーマ

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査）
- **A-6 サブ「〜こととなる/こととなりました」** ✅2026-06-19 taxonomy v1.1 へ A-6 例追記。公的文書 002 で4回（導入されることとなりました／行われることとなります／おかけすることとなりますが／となっております）。`hits: 1run(detector-B)` だが公的文書の決定的クセとして実例昇格。
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。実例: day0-001。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「〜してみてはいかがでしょうか」。実例 day0-002。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式。 `hits: 1` 出所 detector-B
- **A-10×B-2 複合（カタカナ抽象名詞＋万能動詞）** 「高いスケーラビリティとレジリエンスを提供する」「アジリティを向上させる」。A-10 単独でも B-2 単独でも捉えきれない複合シグネチャ（技術記事）。`hits: 1run(2例)` 出所 detector-A → 候補欄に記載、再現待ち。
- **結語「ますます〜していく」未来逓増（D-7 候補）** 「そのプレゼンスはますます増大していく」。`hits: 1` 出所 detector-A → 候補欄、再現待ち。
- **I-3 最上級敬語×need-to「〜していただく必要がございます」** 公的文書 002 で3回。`hits: 1` 出所 detector-B → 候補欄、再現待ち。

### fidelity チェックリスト追補
- **発話行為・規範強度の保存（要請/義務/許可の illocution と must→please 希薄化）** ← 002 f005/f007/f010 で「原則として…必要がございます（要件規定の義務）」→ 依頼形（ください）で義務性が一律後退。事実層は pass だが規範強度は別軸。modality 項(7)から分離した独立項目化を提案。`status: ready` `hits: 1run` 出所 fidelity-B
- **助詞による含意変化（並列「も」等の追加）** ← 001「可用性を高める」→「可用性も高まる」「俊敏さも上がる」で原文にない並列助詞「も」が混入。項目6/11 で捌けず。サブ項目6b。`hits: 1` 出所 fidelity-A
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか**（day0 f019 由来）。`status: ready` `hits: 1`
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実」を逐一問う。`status: ready` `hits: 1` 出所 fidelity-B(day0)
- 「情報を含む削除 vs ボイラープレート削除」二分判定。出所 fidelity-B(day0)
- 自動詞化の判定3条件の成文化（IMP-007 に統合）。出所 fidelity-A
- 責任境界: 「情報の凝縮」が fidelity か naturalness か（命題が残れば fidelity=pass、文言削減量は naturalness 側で計測）。出所 fidelity-A
- diff の start/end オフセット機械照合（触っていない区間を触った検出の網羅）。出所 fidelity-A

### playbook レシピ追補
- **A-5 反復は最低3形に分散**（短縮/断定/自動詞化/二文割り）。二択（できる/する）だけでは単調回避不能。実例: 001 の5回→4形。`status: ready` `hits: 1` 出所 rewriter-A
- **自動詞化のトレードオフ明記**（分散の自由度 vs 意味等価。fidelity ロールバックリスク）。出所 rewriter-A
- **I-3 依頼形変奏テーブル**（敬体・公的文書: ご〜ください／お〜ください／お済ませください）。三反復の自然分散用。`status: ready` `hits: 1` 出所 rewriter-B
- **公的文書は規範形を最低1回温存**（I-3「必要がある」の要件規定義務を全廃しない閾値）。`status: ready` `hits: 1` 出所 fidelity-B, rewriter-B
- **B-2 変換表に文脈分岐エントリ**（provisioning→割り当て[リソース]／用意[環境]）。出所 rewriter-A
- **重複 span（A-10＋B-2 等）の合成処方ガイド**。出所 rewriter-A（IMP-005 と関連）
- C-5 絵文字削除後の文末/区切り吸収ルール。出所 rewriter-B(day0)
- D 系結びは「最小着地文を残す」。出所 rewriter-B, naturalness-B(day0)
- 機能が必要な接続詞（しかしながら）は削除でなく変奏。出所 rewriter-A(day0)
- 原文が元から推量の D 系は推量を保持。出所 rewriter-A(day0)

### naturalness 判定の精緻化
- **過推敲シグナルの数値化に「削除偏重比（del/ins）＋固有名詞保存率」を追加**（構造削除と情報削除を区別）。`status: ready` `hits: 1run(2agent)` 出所 naturalness-A/B（2026-06-19）
- **near-A（A-pending）ステータス**: 改善 A 水準＋S1 単発残存＋局所修正で到達可能なケースに、full rewrite でなく 1-span patch を促す中間判定。実例: 001 round1（C→1span patch→A）。`hits: 1` 出所 naturalness-A
- 敬体/常体混入は文末形態の二値カウントで機械検出。出所 naturalness-A(day0)
- クラスタ系 finding はクラスタ崩壊時に個別 severity 降格。出所 naturalness-A(day0)
- E-2 到達ラインの緩和（体言止め1箇所以上で合格）。出所 naturalness-B(day0)
- 絶対残存数ガードを grade 表に組込み（S1 1件でも C 以下）。✅運用中（001 round1 で機能）。出所 naturalness-A/B

### ジャンル別ルール
- **公的文書ジャンルの severity 上書き**: I-3/I-4・硬い敬語（におかれましては/賜りますよう）は単発許容、N≧3 反復のみ finding 化。change_rate 警告もジャンル別緩和。`status: ready` `hits: 1run(detector-B+rewriter-B)` 出所 detector-B, rewriter-B
- 正規化基準 K のジャンル別参照値化（キャリブレーションデータ蓄積後）。出所 detector-A/B

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 2run`
- ルーティン・モチベーション・データドリブン（day0）＋ スケーラビリティ・コンテナオーケストレーション・Kubernetes・デプロイ（2026-06-19）等の定着語/業界標準語は B-2 から免責し残差 S3 固定。検出器が機械可読な `exempted_spans` 欄に残せると再現性が上がる。出所 naturalness-B, fidelity-A(day0), detector-A（2026-06-19）

### detector 実装
- **`repetition_group` / `variation_budget` フィールド**: 同カテゴリ反復（A-5×5 等）を束ねて推敲役へ「何形に散らすか」を渡す。分散計画の機械化。`hits: 1` 出所 rewriter-A
- **`exempted_spans` 欄**（業界標準語の手動除外を JSON に残す）。出所 detector-A
- start/end 自己検証（regex マッチ位置と text_span 一致を assert）。✅2026-06-19 両検出器が実施。出所 detector-A
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B(day0)
