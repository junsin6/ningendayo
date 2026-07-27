# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-07-27（run 001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done` `hits: 2runs` `applied: 2026-07-27-001`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。Sample A も 47.6% と高止まり。
- **2026-07-27 再現（別 run）**: run 001（技術解説・ai_tell_density 0.53）で 43 finding の 1:1 語句置換のみで change_rate 0.50 に到達。rewriter-001 が lexical 0.43 / structural 0.07 の二軸分離を実装し「密度由来の見かけ高変更率」と実証。naturalness-001 も not_over_polish と判定。→ hits 2runs で昇格・適用。
- 出所: rewriter-A, rewriter-B, naturalness-B（day0）＋ rewriter-001, naturalness-001（2026-07-27）
- **適用内容**: (1) `rewriting-playbook.md §変更率の数え方` を二軸（`lexical_substitution_rate`／`structural_delete_rate`）に改訂、総変更率50%超でも語句置換主導なら中断せず override へ。(2) `japanese-style-rewriter.md` の変更率監視を二軸化、純総変更率での `hold_and_report` 廃止。(3) `SKILL.md §総合判定` に `override accept` 行を追加。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2runs` `applied: 2026-07-27`
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える（Sample A raw106→92.5、taxonomy 例は raw56→71.5 と不整合）。
- **2026-07-27 再現（別 run）**: detector-001 と detector-002 が独立に有理飽和式 `100×raw/(raw+K)` を採用したが、**K が run 間で不統一（001=60, 002=34）**。naturalness-002 が「K が違うと improvement_rate を run 横断で比較できない」と指摘。→ 昇格・適用。
- 出所: detector-A, detector-B（day0）＋ detector-001, detector-002, naturalness-002（2026-07-27）
- **適用内容**: `ai-taxonomy.md §検出出力スキーマ` に式を固定 — `score = 100×raw/(raw+50)`、**K=50 固定**（run 間で不変、文書長で動かさない）。density はユニオン被覆に定義。`ai-tell-detector.md §スコア算出` も同式に更新。taxonomist が v1.1 で追認。

### IMP-003 score_before のフィールド契約が曖昧 `status: done` `hits: 1run` `applied: 2026-07-27`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score 92.5）。レビュアーごとに数値がぶれる。
- 出所: naturalness-A
- **適用内容**: IMP-002 の schema 改訂に同梱 — 「`score_before = 02_detection.json の meta.severity_weighted_score`、score_before/score_after は同一 K=50 を用いる」を `ai-tell-taxonomy.md` に明文化。2026-07-27 の両 run で naturalness-reviewer が実際にこの契約に従い数値ブレなし。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2runs`
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
- **2026-07-27 再現（別 run）**: detector-001（E-2 文書レベルを代表 span "となっています" にアンカー）と detector-002（E-2 を代表オカレンスにアンカーし反復位置を reason に列挙）がともに「document スコープの start/end が未規定」と再指摘。→ hits 2runs で `status: ready`。次回適用候補。
- 出所: detector-B, detector-A（day0）＋ detector-001, detector-002（2026-07-27）
- 提案: `scope: "span"|"scattered"|"document"` を追加、document は start/end を null 許容 or 全文範囲。density はユニオン被覆（IMP-002 で density 側は定義済、scope フィールドは未適用）。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2runs`
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。
- **2026-07-27 再現（別 run）**: detector-001（A-10 節内に B-2/A-2 が入れ子）・detector-002（A-6＋A-8 の二重）が「同一 span の主従ルール／副タグ配列が要る」と再指摘。density のユニオン被覆定義は IMP-002 で適用済だが、**finding 副タグ（co_categories[]）は未適用**。→ hits 2runs で `status: ready`。次回適用候補。
- 出所: detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A（day0）＋ detector-001, detector-002（2026-07-27）
- 提案: 「1 span = 主分類 1 finding」＋ `co_categories: [...]` 副タグ配列を許容。density はユニオン被覆（適用済）。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 1run`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。
- 出所: naturalness-A
- 提案: `ai-tell-detector` をサブエージェントとして再呼び出しする経路を必須化（手動照合禁止）。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`
- 注: 2026-07-27 の naturalness-001/002 は taxonomy 基準の自走査＋一部 detector 再呼び出しで対応。方法を meta.rescan_method に明記する運用が定着。

### IMP-007 公的文書ジャンルの処方・免責リストが playbook に不在 `status: open` `hits: 1run(3agent)`
- 症状: playbook は主にコラム/レポート/ブログ向け。公的文書（お知らせ・通知）の A-6/A-8 二重複合（「〜される＋〜となっております」）、I-3「〜いただく必要がございます」→依頼形化、受動→能動化に伴う助詞復元（が→を/は）のレシピが無い。定型敬語（何卒〜賜りますよう/お願い申し上げます/ございます反復）を E-2・敬語過剰検出から免責する明示リストも無い。
- 出所: rewriter-002, detector-002, naturalness-002（2026-07-27・同一 run 3 agent）
- 提案: `rewriting-playbook.md` に「K. 公的文書」節を新設（変換表＋能動化の助詞復元は意味不変操作として許容と明記）。references に「公的文書 register 定型ホワイトリスト」を追加し detector/reviewer が免責参照。
- 影響: `rewriting-playbook.md`, `ai-tell-taxonomy.md（ジャンル別免責）`, `ai-tell-detector.md`, `naturalness-reviewer.md`
- 昇格: 別 run（次の cycle_day 1 = 公的文書再登場）で再現したら ready。

### IMP-008 modality 強度の順序尺度（ラダー）が未整備 `status: ready` `hits: 2runs`
- 症状: fidelity check 7「modality」が二値判定しかできず、「必要がございます→ください」等が〈義務/要請/推奨/依頼〉のどのレベル移動か定量化できない。公的文書では強度差が実務的意味を持つ。
- 出所: fidelity-A（day0 の P2 note「modality 強度を順序尺度化」）＋ fidelity-001, fidelity-002（2026-07-27）
- 提案: taxonomy に modality ラダー（命令>義務>要請>推奨>依頼>許可 の順序値）を定義し、Δ1段まで許容・Δ2段以上で毀損フラグ、という閾値を fidelity check 7 に組込む。相（確定度: 決定済み/予定）も独立軸化を検討。
- 影響: `ai-tell-taxonomy.md`, `content-fidelity-auditor.md §check7`
- 次回適用候補（3件枠の都合で本日は IMP-001/002/003＋fidelity#14 を優先）。

### IMP-009 過推敲シグナルがジャンル非依存で符号が固定 `status: open` `hits: 1run`
- 症状: naturalness の過推敲チェックは全ジャンル一律・二値。公的文書では口語化/敬体常体混入/要請弱化を厳格検出すべき（register 破壊が致命）一方、ブログでは口語化はむしろ正常方向で「口語化しすぎ＝減点」は誤検出を生む。E-2 単調も公的文書では文体由来で免責、変奏しすぎを逆に減点すべき。シグナルに強度（S1〜S3 相当）が無く「register 破壊1件」と「軽微口語化1件」を同列カウント。
- 出所: naturalness-002（2026-07-27）
- 提案: `over_polish_signals` をジャンル別プロファイル化（各項目に register 依存の閾値・符号）。シグナルに重みを付け、public_notice の register 破壊は単独でも C/D へ落とせるように。residual_detail に `register_note`（免責寄り/真の残存）を必須化。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md（ジャンル別プロファイル）`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 001。 `hits: 1` 出所 detector-A（day0）
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B（day0）
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B（day0）
- **B-2b 定訳途上テック語**（初出のみ日本語グロス併記して以後カタカナ維持。純 B-2 と処方が別）。実例「エンベディング（埋め込み）」「スループット（処理量）」。※グロスが原語を狭める場合は fidelity 違反（e024「ハルシネーション（事実誤り）」で実証）。 `hits: 1` 出所 detector-001, rewriter-001（2026-07-27）→ taxonomist が候補欄登録
- **A-5b 〜を可能にする**（enable/make it possible の直訳使役可能形。be able to=A-5 と英語原型が別）。実例「トレードオフをコントロールすることを可能にします」。 `hits: 1` 出所 detector-001 → 候補欄登録
- **A-6b 受動＋こと＋となる 三重状態化**（公的文書特有。A-6＋A-8＋I-1 複合）。実例「停止されることとなりました」「延長される措置が取られることとなっております」。 `hits: 1` 出所 detector-002 → 候補欄登録
- **I-3b 〜いただく必要がございます**（I-3 の丁寧最上位変種。依頼を回りくどく義務化）。実例「ご了承いただく必要がございます」。 `hits: 1` 出所 detector-002 → 候補欄登録
- **A-8b 行政受動「措置が取られる」**（無主語で行為者＝当局を消す二重受動）。実例「延長される措置が取られる」。 `hits: 1` 出所 detector-002 → 候補欄登録
> いずれも 2026-07-27 が初出（hits:1）。次の同ジャンル run で再現したら v1.1 本文へ昇格。

### fidelity チェックリスト追補
- **#14 主張の同一性（claim identity）＋序列/因果/価値の新規付与禁止** `status: done` `hits: 2runs` `applied: 2026-07-27-001`
  - day0 f019（並列→基盤の序列混入）＋ 2026-07-27 e017（D-2 ハイプ除去「注目を集めている」→「広がっている」で〈注目〉→〈普及〉すり替え、fidelity-001 が検出しロールバック）で 2 run 再現。
  - **適用**: `content-fidelity-auditor.md` を 14 項に拡張。#14「主張の同一性」を新設（近縁別主張へのすり替え禁止・接続語/順序語の序列付与もここで捕捉）。#11 に「グロス（括弧補足）追加禁止」（e024 由来: 原文にない定義的補足は情報追加＋意味縮小）、#12 にカタカナ概念矮小化の注記を追加。
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
