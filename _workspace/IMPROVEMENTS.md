# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-06-18（run 001 エッジ技術解説, 002 公的文書）。06-12 起票の P0/P1 群が別 run で再現し hits=2run へ到達 → **IMP-002/004/005 を本日適用（taxonomy v1.1）**。

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。06-12 Sample B は 54.6% で `hold_and_report` 誤発火。**06-18 で再現**: run001 は cleft化（A-10構文組替）で diff=0.38 vs span積算=0.23 と乖離、run002 は削除主体編集（挿入43/削除136字）で 28% と体感より高止まり。両 rewriter が「span積算を主・diffを補助上限とする二指標方式」を要望。
- 出所: rewriter-A, rewriter-B, naturalness-A, naturalness-B（06-12: rewriter-A/B, naturalness-B）
- 提案: (a) 「語句改変率(span積算)」を主指標、diff値を補助上限として併記の二指標を正式採用。(b) 装飾・常套句の純削除分を控除。(c) del≫ins の削除主導ケースは中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。(e) どちらを正規閾値とするかを SSOT/SKILL に明文化。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done(2026-06-18 / taxonomy v1.1)` `hits: 2run`
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き解像度が消える。**06-18 で決定的に再現**: detector-A が raw 加重和 78 → **正規化 100.0 に飽和（上限到達）**。detector-B は K=1.538 を裁量採用し 74.6、naturalness 両者は K を逆算して一貫適用。検出器間でスコア比較不能だった。
- 出所: detector-A, detector-B, naturalness-A, naturalness-B（06-12: detector-A/B）
- 適用（v1.1）: `severity_weighted_score = min(100, (5·#S1 + 2·#S2 + 0.5·#S3) / input_length × 1000)` を SSOT に確定。document スコープ finding は分子の raw 加重和に含めるが density 分母には算入しない。100 到達は飽和（cap）と明記し、文書間比較には ai_tell_density を併用。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出`

### IMP-003 score_before のフィールド契約が曖昧 `status: ready` `hits: 2run`
- 症状: score_before の出所が未固定でレビュアーごとにぶれる。**06-18 では我々が「= meta.severity_weighted_score」を明示指示**したため両 naturalness が 100.0 / 74.6 を正しく採用。IMP-002 の式確定により値は一意化するが、契約文言の明文化はまだ未適用。
- 出所: naturalness-A, naturalness-B（06-12: naturalness-A）
- 提案: 「score_before = 02_detection.json の meta.severity_weighted_score」を naturalness-reviewer.md と taxonomy に明記。IMP-002 適用に続けて次回適用候補。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: done(2026-06-18 / taxonomy v1.1)` `hits: 2run`
- 症状: 絵文字8個・文末単調・まず…最後に は分散/文書レベルパターン。単一 start/end では広域 locator にするしかなく density 過大。**06-18 で再現**: 両 detector が E-2 文書単調を表現できず、detector-A は全文 span を当て density 計算から除外する特例、detector-B は `start=end=0` ＋自己検証(text[start:end]==span)が必ず失敗する例外対応を強いられた。
- 出所: detector-A, detector-B, naturalness-A（06-12: detector-A/B）
- 適用（v1.1）: finding に `scope: "point" | "scattered" | "document"`（省略時 point）と scattered 用 `occurrences: [[s,e],...]` を追加。document スコープは `start=end=0` を許容し自己検証(text[start:end]==text_span)を免除。density は point/scattered の実 AI クセ文字数のみで算出し document スコープを分母汚染させない。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: done(2026-06-18 / taxonomy v1.1)` `hits: 2run`
- 症状: 1 span が複数カテゴリに該当（06-12: I-4＋B-2＋I-1）。**06-18 で再現**: run001 で A-5＋A-10 が同一文末「提供することができる」に重畳、run002 で A-5＋A-8 が「可能とされておりました」に重畳。rewriter は 24件→実質22編集／19件を連結処理し対応がずれ、naturalness-A は detected_count と findings 実数の不整合を観測。
- 出所: detector-A, detector-B, rewriter-A, rewriter-B, naturalness-A（06-12: 5agent 横断）
- 適用（v1.1）: 「1 span = 主分類 1 finding」を基本とし finding に `secondary_categories: [...]`（任意）を追加。重畳区間は主カテゴリ1件のみ density 文字数に算入（二重計上禁止）。category_summary は「findings の主 category 先頭文字を集計（secondary は数えない）」と注記。`detected_count == len(findings)` を契約として明記。
- 影響: `ai-tell-taxonomy.md §スキーマ`, 各 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だが従来は手動照合 → 推定値。**06-18 で実証的に解決可能と確認**: 両 naturalness が推敲文に検出ロジックを再走査し score_after を実測（run001 5.13 / run002 1.5）、IMP-002 の正規化係数を一貫適用できた。仕様化（手動照合禁止＋再走査必須）はまだ未適用。
- 出所: naturalness-A, naturalness-B（06-12: naturalness-A）
- 提案: `naturalness-reviewer.md §処理` に「推敲文へ taxonomy 同一基準で再検出し score_after を実測。手動推定禁止」を明記。IMP-002 と整合する正規化式を参照させる。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

### IMP-007 ジャンル別の着地点・許容床が未定義（公的文書で顕在化）`status: ready` `hits: 1run(3agent)`
- 症状: playbook の処方（I-3「する必要がある」→「すべきだ／具体勧告」、D 系結びの削除）は常体・エッセイ前提で、**公的文書では「ございます／賜りますよう／申し上げます」等の儀礼敬語が AI クセではなく正当な作法**。run002 では I-3 の正解が「ご確認ください」等の依頼形であり、儀礼挨拶は最小着地で維持すべきだった（オーケストレーター指示で補完）。検出器が儀礼定型を過検出すると score が不当に上振れし等級が下がる危険。
- 出所: rewriter-B, fidelity-B, naturalness-B, detector-B（run002 横断）
- 提案: (a) playbook にジャンル別着地点テーブル（コラム/レポート/ブログ/公的文書）。(b) taxonomy に「公的文書の許容敬語床」Do-NOT を明記し検出器・レビュアーで共有。(c) 床の定量規則（同一儀礼定型が文書内 N 回までは結びの慣習として許容、超過で E-2/I-3 計上）。(d) ジャンル別変更率閾値（公的文書は 20% で警告 等）。
- 影響: `rewriting-playbook.md`, `ai-tell-taxonomy.md §Do-NOT`, `ai-tell-detector.md`, `naturalness-reviewer.md`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 06-12-001。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B
- **A-5/A-10 重畳の優先カテゴリ規則** 「（万能動詞）することができる」が A-5（可能の冗長）と A-10（抽象主語＋提供/もたらす）の両方に該当。判定者でカテゴリが揺れる。「万能動詞＋することができる は A-10 を主・A-5 を secondary」等の優先規則を提案。実例: 06-18-001「提供することができるのです」。 `hits: 1` 出所 detector-A, rewriter-A
- **I-3 と I-4 の境界（行為者の明示有無）** 「ご確認いただく必要がございます」は行為者明示で I-3、「見直しが行われる必要が生じた」は行為者曖昧で I-4 寄り。境界基準を taxonomy に一行追加。実例: 06-18-002。 `hits: 1` 出所 detector-B, fidelity-A
- **A-6 の正当な becoming 免責** 「無料制→予約制」のような真の状態変化を述べる「必要となります／〜になる」は A-6 ではなく正当。機械反復との切り分け基準。実例: 06-18-002。 `hits: 1` 出所 naturalness-B

### fidelity チェックリスト追補
- **#14 評価・価値付けの強度保存（modality と分離した独立軸）** ← 06-12 f019（並列→基盤の序列混入）に加え、**06-18-001 で再現**: e022「欠かせない要素（不可欠な一要素）→核心（中核そのもの）」の役割昇格は modality（断定/推量/義務）とは別軸の評価強度（emphasis/valuation）。fidelity-A が「項14 を modality から分離して新設」を要望。`status: ready` `hits: 2run` 出所 fidelity-A（×2run）
- **ヘッジ除去の許容ルール** 「能力記述（〜できる）の断定化は許容、不確実性予測（〜でしょう）のヘッジ除去は毀損」。06-18-001 で e009（可能→断定=pass）と e022（推量でしょう→断定ます=fail）の線引きが監査官裁量に依存。明文化を要望。`status: ready` `hits: 1run` 出所 fidelity-A
- **同義対句 vs 別概念の判別デフォルト規則** 「並列修飾語の一方削除は、両語が真に同義（言い換え可能）でない限り情報欠落とみなす」。06-18-002 e017「効率的かつ持続可能な→持続可能な」で rewriter は同義扱い・auditor は別概念と判定。fidelity-first の具体化。`status: ready` `hits: 1run` 出所 fidelity-B
- **公的文書の能動化での責任主体含意** check9 を「行為者が誤っていないか」だけでなく「原文が行為者を伏せた意図的含意を歪めていないか」まで拡張。複数主体（国/県/市/委託業者）が関与する文では能動化が誤帰属＝重大毀損になりうる。06-18-002 は市一意確定で無害だった。`status: ready` `hits: 1run` 出所 fidelity-B
- **diff の note は監査対象であって証拠ではない** auditor は rewriter の自己申告 note を鵜呑みにせず原文直読で検証（e017 の「同義対句」申告を退けられた）。agent 定義に原則明記。出所 fidelity-B
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。`status: ready` `hits: 2run` 出所 fidelity-B（06-18 でも有効に機能）
- 「情報を含む削除 vs ボイラープレート削除」二分判定: 削除 span に (a)数値/固有名詞/日付 (b)条件/因果節 (c)固有の例示 を含めば情報欠落、挨拶/CTA/装飾/自己言及のみならボイラープレート。出所 fidelity-B
- #5論理関係 と #11情報追加 の責任境界を一意化（主因項目を 1 つに正規化）。出所 fidelity-A
- **modality 強度を順序尺度化（要請動詞の強度ランク表）** 「必要がございます／ください／してください／しなければならない／するものとする」に階段がある。公的文書向けに reference 化すると判定が再現可能。`status: ready` `hits: 2run` 出所 fidelity-A, fidelity-B

### playbook レシピ追補
- **C-5 絵文字削除後の文末/区切り吸収ルール**（句点で吸収 or 削除のどちらか明記）。出所 rewriter-B
- **D 系結びは削除一択でなく「最小着地文を残す」**（減らしすぎ下限）。実例: B の「気軽に始めてみてください」。出所 rewriter-B, naturalness-B
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**という例外則。出所 rewriter-A
- **原文が元から推量の D 系は推量を保持**（「断定へ」の一律処方の例外）。出所 rewriter-A

### naturalness 判定の精緻化
- **過推敲シグナルの定量化（文末形態の二値カウント）** 敬体（ます/です）vs 常体（だ/である/動詞終止）の混入を機械検出。**06-18-001 で実証**: 15文中1文が常体終止「分散させる。」＝混入1件として検出。`status: ready` `hits: 2run` 出所 naturalness-A（×2run）
- **E-2「同一文体内変奏」と「文体不変」の境界明文化** 体言止め・〜でしょう・〜のです は敬体両立形（変奏=可）、**動詞の常体終止形（分散させる。）は文体崩れ（不可）**。06-18-001 で rewriter が変奏意図の「分散させる。」を入れ naturalness が文体崩れと判定。playbook E-2 に1行明記を要望。`status: ready` `hits: 1run` 出所 rewriter-A, naturalness-A
- **等級ルーブリックの優先順位の2段階化** 「残存数で上限等級を決める→過推敲シグナルで引き下げる」の順を明文化。06-18-001 は「数値ならA・シグナル2個でC」の境界ケースで or 条件が並列で曖昧だった。`status: ready` `hits: 1run` 出所 naturalness-A
- クラスタ系 finding（B-2 密集・C-1 列挙）はクラスタ崩壊時に個別 severity を降格するルール。出所 naturalness-A
- E-2 文末単調の到達可能ライン緩和（体言止め1箇所以上で合格、文体維持制約下の過推敲回避）。出所 naturalness-B
- 絶対残存数ガードを grade 表に組込み（改善率が高くても S1 が1件でも C 以下）。出所 naturalness-A, naturalness-B
- **公的文書の過推敲定量化** ①儀礼定型の削除率（公的文書は 0〜低位が正解）、②能動化による行政主語の露出回数（過剰だと責任主体が前に出すぎ硬化）を計測し閾値超で signal 化。出所 naturalness-B

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 2run`
- ルーティン・モチベーション・データドリブン（06-12）に加え、**06-18-001 で再現**: ポテンシャル・センシティブ（→機微）・データセンター・ネットワーク・デバイス等の定着語/業界標準語の Do-NOT 境界が曖昧。検出器が拾うべきか開かず残すかの線引きを taxonomy 例外欄に「定着カタカナ語ホワイトリスト」として整備。出所 naturalness-B, fidelity-A, naturalness-A（06-12）／detector-A, rewriter-A, naturalness-A（06-18）

### taxonomist 審査由来（v1.1 適用時に発見 / v1.2 候補）
- **IMP-008 短文での score 飽和を運用ルール化** `status: ready` `hits: 1run(taxonomist+detectors)`: v1.1 式でも 〜800字の短文は raw が大きく 100 に貼り付く（06-12/06-18 とも実は飽和100）。等級判定が改善率依存なら、係数1000の見直し or 「短文時は ai_tell_density を主指標へ切替」の明示ルールが必要（現「併用」は努力規定）。出所 taxonomist, detector-A
- **point 自己検証の退化 document ガード**: scope 未指定でも start=0/end=L/text_span=全文だと自己検証を偶然パスする（06-18 f024）。「end-start が input_length の一定割合(例50%)超なら scope=document 必須・point 禁止」を契約に追加すると旧データの誤分類も自動是正。出所 taxonomist
- **secondary_categories の発火閾値を数値化**: 06-18 f009 は A-5 と重なる A-10 を別 finding 計上（span superset で合法）。「span 重複率 N% 以上は別 finding 禁止・secondary 化必須」と数値定義すれば検出器間の再現性が上がる。出所 taxonomist
- **occurrences と category_summary の集計単位を規定**: scattered finding が複数 occurrences を持つとき summary が出現数か finding 数か未明記。現状 scattered は実質未使用（06-12 は A-1 を6件に分割）。集計単位を契約化。出所 taxonomist

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。**06-18 でも両 detector が全 span 自己検証を実施**。ただし document スコープでは検証が必ず失敗するため IMP-004 の免除規則が必要だった。出所 detector-A, detector-B
- **detected_count == len(findings) の整合 assert** naturalness-A が detector の detected_count と findings 実数の不整合（重複含む誤集計→自己訂正）を観測。スキーマ契約に明記（IMP-005 で適用）。出所 naturalness-A
- **category_label 正準辞書を SSOT に持たせる** 各サブパターンの公式ラベル文字列が無く検出器が独自命名 → rewriter と表記揺れ。出所 detector-A
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B
