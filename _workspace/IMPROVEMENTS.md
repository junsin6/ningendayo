# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-09-03（day 1: run 001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run(6agent)`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。Sample A も 47.6% と高止まり。
- 再現（2026-09-03）: rewriter-001/002 が「(挿入+削除)/原文 は純削除に鈍感、net_length_delta と deletion_only_ratio を分離すべき」と再提起。今回は両 run とも純減主導で change_rate 0.24/0.246 と偶々閾値内だったため誤発火せず（＝欠陥は潜在したまま）。
- 出所: rewriter-A, rewriter-B, naturalness-B（day0）＋ rewriter-001, rewriter-002（day1）
- 提案: (a) 「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を change_rate から控除。(c) 挿入率を単独併記し、del≫ins の削除主導ケースは中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。(e) diff meta に `net_length_delta`・`deletion_only_ratio`・削除主導フラグを正式スキーマ化。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`
- 注: hits≥2 到達。**次回 day で適用候補（構造的変更のため単独 run で慎重に）**。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done`（適用 2026-09-03-001/002）`hits: 2run(6agent)`
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える。分母（input_length or 固定 max）も未規定でエンジン間比較不能。
- 再現（2026-09-03）: detector-001/002・naturalness-001/002 の4エージェントが独立に `min(100, raw/input_length×1000)`（＝1000字あたり加重密度）へ収束。input_length は改行込み生全文字数で start/end と一致させた。
- 出所: detector-A, detector-B（day0）＋ detector-001/002, naturalness-001/002（day1）
- **適用内容**: `ai-tell-taxonomy.md §検出出力スキーマ` に「スコア・密度・span の算出規約」節を新設し `score = min(100, raw/input_length×1000)`・input_length 定義・density=union被覆/input_length を確定。`ai-tell-detector.md §スコア算出` を同式へ更新。`meta.score_formula` を必須出力に。

### IMP-003 score_before のフィールド契約が曖昧 `status: done`（IMP-002 適用に内包 / 2026-09-03）`hits: 2run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。レビュアーごとに数値がぶれる。加えて input_length の 787(改行込) vs 778(改行除) 揺れで score 母数がぶれる（day1 で再確認）。
- 出所: naturalness-A（day0）＋ naturalness-001（day1: 長さ基準揺れ）
- **解決**: IMP-002 適用で「input_length=改行込み生全文字数」「score は前後同一係数で比較可能」を SSOT 確定。score_before は 02_detection.json の `meta.severity_weighted_score`（同式）で一意化。naturalness 両者が実際にこの基準を採用し 72.4→4.9 / 59.25→0.8 を再現。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: done`（適用 2026-09-03-001/002）`hits: 2run(5agent)`
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
- 再現（2026-09-03）: detector-001/002・rewriter-001 が「E-2・C-7・H-1 を単一 span で無理に指し、diff が 1 finding=1 edit を強制する歪み」を再提起。
- 出所: detector-A, detector-B（day0）＋ detector-001/002, rewriter-001（day1）
- **適用内容**: taxonomy §算出規約に `span_type: "contiguous"|"scattered"|"document"` ＋ scattered 用 `occurrences: [[s,e],…]` ＋ document 用 `scope` を新設。density は occurrences の union のみ算入と明記。`ai-tell-detector.md §検出手順` にも反映。
- 残: diff 側 `edits[]` の 1 finding:N edit 化（rewriter が要望）は未適用 → IMP-007 として起票。

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run(7agent)`
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1、A-5＋A-6、A-8＋A-6 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。
- 再現（2026-09-03）: detector-001（A-5+A-6, A-5+B-2 共起）・detector-002（A-8+A-6, A-8+I-3 共起）が `secondary_categories[]` を要望。
- 出所: detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A（day0）＋ detector-001, detector-002（day1）
- 提案: 「1 span = 主分類 1 finding」を基本とし、`secondary_categories: [...]` 配列を許容。category_summary は「findings の主 category 先頭文字を集計」と注記。
- 影響: `ai-tell-taxonomy.md §スキーマ`, 全 .md のスキーマ節
- 注: hits≥2 到達。**次回適用候補**。

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready(環境制約)` `hits: 2run(3agent)`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーはサブエージェント spawn 不可（Task ツール未露出、SendMessage は既存エージェント宛のみ）→ 検出器 rubric を in-process 適用で代替。
- 再現（2026-09-03）: naturalness-001/002 の両者が「ネスト spawn 経路が無い」と報告。手動照合ではなく rubric 実行だが「別プロセス実呼び出し」は担保されず。
- 出所: naturalness-A（day0）＋ naturalness-001/002（day1）
- 提案: **オーケストレーター側で** 推敲後に `ai-tell-detector` を再実行し再計測 JSON をレビュアーへ渡す設計へ変更（reviewer 内 spawn を前提にしない）。これはファイル編集だけでなくパイプライン制御の変更 → SKILL.md §並列検証 と naturalness-reviewer.md の責務再定義が必要。
- 影響: `SKILL.md §並列検証`, `naturalness-reviewer.md §処理`

### IMP-007 diff スキーマが 1 finding=1 edit 前提で位置情報・統合 edit を表現できない `status: ready` `hits: 1run(4agent)`
- 症状: `03_rewrite_diff.json` に start/end が無く監査官が原文照合しづらい。文書レベル finding（C-7「また削除＋さらに削除」）を 1 エントリに詰める歪み。隣接 finding の統合手術（f013+f014→「本工事で」）の表現手段が無く before を重複記載で回避。
- 出所: rewriter-001, rewriter-002, fidelity-001, fidelity-002（day1・横断）
- 提案: edit に `start`/`end`、`finding_ids: []`（1:N・N:1 許容）、`merged_with`、`semantic_delta: ["modality","voice","agent",...]` フラグ、`net_length_delta`/`deletion_only_ratio` を追加。semantic_delta があると監査官が「装飾のみ」と「意味成分に触れる」edit を機械抽出でき、f007/f017 型の要注意 edit 検出が高速化。
- 影響: `japanese-style-rewriter.md §出力`, `content-fidelity-auditor.md`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **A-8b 行為者省略の受動** `status: done`（v1.1 昇格・2026-09-03）: run 001(技術)・002(公的)で実例2件以上、taxonomist が A-8 を A-8a/A-8b に分割し制度主語の保持例外を明記。出所 detector-001/002, rewriter-002。
- **候補K 過剰敬語・定型結語** ★日本語固有: 「お願い申し上げます」「〜いただく必要がございます」「くださいますよう」の反復（公的文書）。taxonomy 拡張候補欄に追記済み。 `hits: 1`（公的文書がもう1 run 回れば昇格） 出所 detector-002。
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 001。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B

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

### 定着カタカナ語 B-2 免責リスト＋訳出辞書 `status: done`（適用 2026-09-03-001）`hits: 2run(5agent)`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B, fidelity-A, naturalness-A（day0）
- 再現（2026-09-03）: detector-001「維持/訳出の線引きが検出者判断依存、語彙辞書を references に」／rewriter-001「resilient・handling・focus・provisioning・overhead が変換表に無い」。
- **適用内容**: `rewriting-playbook.md §B-2` に **訳出リスト**（レジリエント→回復力のある、プロビジョニング→準備、フォーカス→集中、ハンドリング→処理、オーバーヘッド→負荷、ビジネスバリュー→事業価値、アジェンダ→課題 等を追加）と **維持リスト**（HTTP・GPU・スケールアウト・アーキテクチャ・リソース・ワークロード・トリガー・イベントドリブン・クラウドネイティブ 等）＋ 3 段の判断規約（定訳1語で意味不変→訳出／原語標準or訳が冗長→維持／迷えば S3 保持）＋「同一表層語は文書内で開/非開統一」を明記。

### E-2「できます／です」3連禁止ルール（playbook）`status: ready` `hits: 1run(2agent)`
- 症状: rewriter が「できます反復」を事前警告 → naturalness が実際に S2 残存として検出（警告→残存の閉ループ未成立）。敬体で体言止め/でしょうは副作用があり変奏手段が乏しい。
- 出所 rewriter-001, naturalness-001。
- 提案: playbook E-2 に「敬体で同一文末（できます/です）3連続禁止」「代替変奏＝連用中止での文結合・のです・名詞述語・体言止め（1文書1〜2回まで）」「事実断定文に でしょう を付けない」を明記。

### 公的文書ジャンル別レシピ（playbook）`status: ready` `hits: 1run(2agent)`
- 症状: playbook のサンプルがビジネス/エッセイ調のみで、行政定型（原則として立ち会いは〜／ご了承いただきますよう）の置換表・レジスター上限（どこまで砕くか）が無い。
- 出所 rewriter-002, naturalness-002。
- 提案: ジャンル別レシピ節を新設し、公的文書は「敬体維持＋謙譲/尊敬水準維持、〜です可・口語不可」を明記。meta.style を `{form, honorific_level}` へ拡張する案も併記。

### fidelity チェックリスト #15「idiom/アスペクト含意の付加」`status: ready` `hits: 1run`
- 症状: 「〜する一方だ」「〜つつある」等、事実は変えないが単調増加・継続・傾向の含意を足す慣用表現が、現行13項の #7(modality)と #11(情報追加)の狭間に落ちる（f017「加速しています→加速する一方です」）。
- 出所 fidelity-001。#14（接続語/順序語の序列付与）と同系で、次回まとめて auditor に追加候補。

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。出所 detector-A
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B
- 同一表層語の全出現グルーピング（`span_group`/`occurrences[]`）— 片方だけ開く不整合を防ぐ。出所 rewriter-001。
- targeted_patterns（run で狙ったクセの命中/不発）を meta に記録し taxonomy 網羅性評価へ還元。出所 detector-001（A-10 が厳密形で不発だった）。

### taxonomy 精緻化（v1.2 候補・出所 taxonomist 2026-09-03）
- **カテゴリ優先規約**: A-8b と A-2/I-3/I-4 が重なる span の primary category 選択ルール未定義。density 二重計上で score 膨張の懸念。`status: ready` `hits: 1`（IMP-005 と統合検討）。
- **反復閾値の密度統一**: A-8b・E-2・F-4・F-5・I-5 に散在する「3回以上」を、v1.1 の正規化式を活かし**密度（per 1000字）基準へ統一**。短文誤爆・長文見逃しを防ぐ。`hits: 1`
- **A-8b 保持例外のホワイトリスト化**: 「義務付けられている／定められている／規定されている」等、制度主語受動の保持対象語リストを候補欄に蓄積し将来機械判定へ。`hits: 1`
- **保留候補の集計分離**: `provisional_subpattern` 任意フィールドで候補K を E-2 density から分離（E-2 統計の濁り防止）。`hits: 1`
- **ジャンル別基準線**: 昇格が run 001/002(レポート/公的)偏り。コラム・ブログの受動データ未収集で A-8b 密度閾値が偏る可能性。`hits: 1`
