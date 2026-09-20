# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-09-20（run 2026-09-20-001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done`（適用 run 2026-09-20）`hits: 3run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。Sample A も 47.6% と高止まり。**再現(2026-09-20)**: rewriter-001 は既定 difflib(autojunk=True) で 0.925 と過大計上（実質 0.376）、rewriter-002 も削除主導で 33.6%。両者とも fidelity 影響なしを確認。
- 出所: rewriter-A, rewriter-B, naturalness-B（2026-06-12）／ rewriter-001, rewriter-002, naturalness-001（2026-09-20 再現）
- 提案: (a) 「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を change_rate から控除。(c) 挿入率を単独併記し、del≫ins の削除主導ケースは中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。**+ (e) difflib は autojunk=False 必須（反復語での過大計上防止）。(f) 分母=本文実文字数を diff.meta に明記。**
- **適用(2026-09-20)**: `rewriting-playbook.md §変更率の数え方` を全面改訂（autojunk=False・insert_rate/delete_rate 分離・削除主導 override・50% 一律中断撤廃→意味改変 edit 比率基準）。`SKILL.md §推敲` の変更率監視文を同期更新。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`（適用済）, `SKILL.md`（適用済）, `japanese-style-rewriter.md`（次回: 実装注記の追記余地）

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done`（適用 run 2026-09-20, taxonomy v1.1）`hits: 2run`
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える（Sample A raw106→92.5、taxonomy 例は raw56→71.5 と不整合）。**再現(2026-09-20)**: detector-001 は raw112 を raw/(count×5) と解釈し 70.0、detector-002 は min(100,raw) で 67.0 と、正規化解釈が依然バラついた。naturalness-001/002 も再現性欠如を指摘。
- 出所: detector-A, detector-B（2026-06-12）／ detector-001, detector-002, naturalness-001, naturalness-002（2026-09-20 再現）
- **適用(2026-09-20 / taxonomist 審査済 v1.1)**: `ai-tell-taxonomy.md §検出出力スキーマ` に正規化式を確定 — `severity_weighted_score = min(100, round(raw / input_length × 500, 1))`（100字あたり深刻度加重和×5、上限100、汚染密度指標）。ai_tell_density の除外規則と「detector/naturalness 同一式」注記も明文化。
- **残課題（taxonomist 提起, 次回候補）**: input_length の計数規約（Markdown 記号・空白・改行の扱い）と document スコープ finding の raw/density 横断カウント規約が未確定。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`（適用済）, `ai-tell-detector.md §スコア算出`（次回: 式参照の明記余地）

### IMP-003 score_before のフィールド契約が曖昧 `status: done`（適用 run 2026-09-20）`hits: 2run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score 92.5）。レビュアーごとに数値がぶれる。**再現(2026-09-20)**: naturalness-001/002 とも score_after の算出基準（正規化式・絶対残存ガードの SSOT 未収載）を問題として再提起。
- 出所: naturalness-A（2026-06-12）／ naturalness-001, naturalness-002（2026-09-20 再現）
- **適用(2026-09-20)**: `naturalness-reviewer.md §処理` に「score_before = 02_detection.json の meta.severity_weighted_score」「score_after は同一正規化式で算出」を明文化。あわせて**絶対残存ガード（S1 が 1 件でも C 以下）**を等級節に収載し、`residual_findings` スキーマを `{S1,S2,S3}` に統一（明細は residual_findings_detail 併記）、文体崩れの二値カウント検出も明記。
- 影響: `naturalness-reviewer.md`（適用済）, `ai-tell-taxonomy.md`（正規化式は IMP-002 で確定済）

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run`
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。**再現(2026-09-20)**: detector-001/002 は E-2/E-1 を代表アンカーで回避、rewriter-001/002 は文書レベル finding を rhythm_notes に別記、naturalness-001/002 は「段階的改善（S2→S3）を格納する場が無い」と指摘。6 エージェント横断で最多再現。
- 出所: detector-A, detector-B（2026-06-12）／ detector-001, detector-002, rewriter-001, rewriter-002, naturalness-001, naturalness-002（2026-09-20 再現）
- 提案: `scope: "span"|"scattered"|"document"` と scattered 用 `occurrences: [[s,e],...]`、document 用 `spans:[...]` を追加。density は重複・locator を除いた実 AI クセ文字数ベースと定義。**+ naturalness 側に `residual_severity`/`partial_resolution`（S2→S3 の段階改善）フィールド。**次回の適用最優先候補。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`, `naturalness-reviewer.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。**再現(2026-09-20)**: detector-001「複合 span（B-2+A-10+A-6 連続）を分割か重複許容かで detected_count/density が変わる」、rewriter-001「1文が複数 finding を含むと before/after が二重計上、finding_ids[] が要る」。
- 出所: detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A（2026-06-12）／ detector-001, rewriter-001（2026-09-20 再現）
- 提案: 「1 span = 主分類 1 finding」を基本とし、`merged_findings: [...]` / edit 側 `finding_ids: [...]` 配列を許容。category_summary は「findings の category 先頭文字を集計」と注記。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。**再現(2026-09-20)**: naturalness-001/002 とも「サブエージェントから ai-tell-detector を spawn するツールが露出せず規則ベース手動再走査で代替」と報告。環境制約のため経路必須化だけでは解けない。
- 出所: naturalness-A（2026-06-12）／ naturalness-001, naturalness-002（2026-09-20 再現）
- 提案: (a) `ai-tell-detector` を呼べる環境では必須化。(b) **呼べない環境向けに検出ロジックを共有スクリプト（scripts/ 配下の関数）化**し、reviewer からも同一コードで再走査できる経路を用意する。`naturalness-reviewer.md §処理` には暫定で「呼べない場合は同一 taxonomy 基準で規則ベース再走査＋notes 明記」を収載済（IMP-003 適用時）。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`, `scripts/`（検出ロジック共有化の新規）

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
> ⚠️ **スラッグ整合注記(2026-09-20)**: taxonomy v1.1 の §拡張候補欄が候補スラッグの正となる。v1.1 は **C-9 = 中黒N項並列** を予約したため、下記の旧 informal「C-9 導入誘導定型」はスラッグ衝突。次回 taxonomist 審査で別スラッグ（例 C-10）へリネームすること。
- **K. 過剰敬語・定型儀礼句の濫用**（★日本語固有・想定S2）taxonomy v1.1 候補欄に登録済。実例(run 2026-09-20-002): ①「〜ようお願い申し上げます」結びが本文5回反復、②儀礼語彙（賜り／厚く御礼申し上げます／所存でございます）積層。設計思想 4大重心の「(2)過剰敬語」に対応する独立カテゴリが A〜J に無い構造的穴の補完。`hits: 1run(3agent)` 出所 detector-002, rewriter-002, naturalness-002。**別ジャンル run で再現(計2run)すれば v1.1 本項目へ昇格。**
- **C-9 中黒（・）による機械的N項並列**（想定S2）taxonomy v1.1 候補欄に登録済。実例(run 2026-09-20-001):「パフォーマンス・コスト・セキュリティ」。A-11(助詞欠落/の連鎖)にも C-8(二項対立)にも収まらない別機序。`hits: 1run` 出所 detector-001。
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 001。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B
- **（旧 C-9）導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。※要スラッグ変更。 `hits: 1` 出所 detector-B

### fidelity チェックリスト追補
- **#14 並列圧縮・接続語/順序語の置換で序列・因果・価値・極性が新規付与/反転していないか** `status: ready` `hits: 2run` — f019(2026-06-12: 並列→基盤の序列混入)に続き、**f029(2026-09-20-001: 中黒3項を単一述語「高められる」へ配分し「コストを高める」で極性反転)** で再現。並列を助詞(も/や/と)で散文化し単一述語を複数項へ配分する編集(A-11/C-9 解消)では、各「項×述語」ペアが独立に極性・valence を保つか検証する項目が必須。**次回の適用最優先候補（13項に第14項として正式昇格）。** 出所 fidelity-A（2026-06-12）, fidelity-001（2026-09-20）
- **敬語modality の等価判定基準（#7 を命題modality/対人modalityに二分）** `status: ready` `hits: 1run` — 公的文書で「必要があります→してください（許容）」「お願い申し上げます→いただけると幸いです（任意化=降格リスク S2）」等の依頼型変換が発生。方向・必須性ランク(must/should/may)・格の温存の3軸で判定。出所 fidelity-002, naturalness-002（2026-09-20）
- **watch_edits レーンをスキーマに追加** `status: ready` `hits: 1run` — pass 判定だが境界の edit を後段（naturalness-reviewer）へ構造的に申し送る枠が無く checks[].note に埋没。pass/rollback の二値に watch レーンを追加。出所 fidelity-002（2026-09-20）
- **rollback スキーマが「複数 finding の共同毀損」を表現できない** `hits: 1run` — f026+f029 のように単独無害・結合毀損の依存や、完全ロールバック vs 述語だけ再構成の粒度を記述できない。`rollback_directives[]`(joint_cause, defect種別, instruction)を提案。各 check に evidence/severity/defect_type も。出所 fidelity-001（2026-09-20）
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。`status: ready` `hits: 1` 出所 fidelity-B
- 「情報を含む削除 vs ボイラープレート削除」二分判定: 削除 span に (a)数値/固有名詞/日付 (b)条件/因果節 (c)固有の例示 を含めば情報欠落、挨拶/CTA/装飾/自己言及のみならボイラープレート。出所 fidelity-B
- #5論理関係 と #11情報追加 の責任境界を一意化（主因項目を 1 つに正規化）。出所 fidelity-A
- modality 強度を順序尺度化（要請/推奨/義務/必須）。出所 fidelity-A

### playbook レシピ追補
- **過剰敬語結びの削減レシピ（新規・候補K対応）** `status: ready` `hits: 1run(2agent)` — playbook の E-2 は「文末変奏」しか無く、公的文書頻出の過剰敬語定型結び（〜ようお願い申し上げます/賜りますよう/所存でございます/厚く御礼申し上げます）への専用レシピが皆無。ルール案: 同一結び3回以上で除去対象、文書全体で1〜2個は格として温存（削除一択にせず勧告文/体言止め/「幸いです」へ分散）、最小着地文の下限を守る。出所 rewriter-002, naturalness-002（2026-09-20）
- **A-11 / C-9 中黒N項並列の散文化レシピ**（playbook A 表に行が無い） — 中黒3項を助詞で散文化する際、単一述語を全項へ一律配分せず、**項ごとに述語の極性(valence)が保てるか確認**（f029 の再発防止、fidelity #14 と対）。例「A・B・Cを高める」→ C の極性が逆なら「AとBを高め、Cを抑える」へ分割。出所 rewriter-001, fidelity-001（2026-09-20）
- **能動化に伴う span 外の連動格助詞変更**（が→を 等）を edit 本体に含める枠（allowed_context_shift）。ロールバック時の取りこぼし防止。出所 rewriter-002（2026-09-20）
- **C-5 絵文字削除後の文末/区切り吸収ルール**（句点で吸収 or 削除のどちらか明記）。出所 rewriter-B
- **D 系結びは削除一択でなく「最小着地文を残す」**（減らしすぎ下限）。実例: B の「気軽に始めてみてください」。出所 rewriter-B, naturalness-B
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**という例外則。出所 rewriter-A
- **原文が元から推量の D 系は推量を保持**（「断定へ」の一律処方の例外）。出所 rewriter-A

### naturalness 判定の精緻化
- 過推敲シグナルの定量化（敬体/常体混入は文末形態の二値カウントで機械検出）。`status: done`（naturalness-reviewer.md に収載, 2026-09-20）出所 naturalness-A, naturalness-001
- クラスタ系 finding（B-2 密集・C-1 列挙）はクラスタ崩壊時に個別 severity を降格するルール。出所 naturalness-A
- E-2 文末単調の到達可能ライン緩和（体言止め1箇所以上で合格、文体維持制約下の過推敲回避）。出所 naturalness-B
- 絶対残存数ガードを grade 表に組込み（改善率が高くても S1 が1件でも C 以下）。`status: done`（naturalness-reviewer.md に収載, 2026-09-20 / IMP-003 同時適用）出所 naturalness-A, naturalness-B, naturalness-001, naturalness-002
- **ジャンル別 register floor（保持すべき定型敬語ホワイトリスト）** `status: ready` `hits: 1run(2agent)` — 公的文書の「平素より〜賜り厚く御礼申し上げます／所存でございます／何卒〜賜りますようお願い申し上げます」は格の下限で必須。一律 S2 で拾うと過検出→誤減点。許容は「同一定型の反復回数」で判定（例 5回=除去/1〜2回=register 許容）。候補 K（過剰敬語）と対で設計する。出所 naturalness-002, fidelity-002（2026-09-20）
- **過推敲シグナルに「依頼強度の低下」「注意喚起/義務句の脱落」を追加**（公的文書では拘束力・注意義務が意味の一部）。出所 naturalness-002（2026-09-20）

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 1run(3agent)`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B, fidelity-A, naturalness-A

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。`status: 実運用中`（2026-09-20 の detector-001/002 は全 span 自己検証パスを報告）出所 detector-A
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B
- **ジャンル別カタカナ許容閾値テーブル** `status: ready` `hits: 1run(2agent)` — アーキテクチャ/レイテンシ/ボトルネック/センシティブ等の「技術解説では半ば専門語だが日本語化も可能」な中間語の扱いが未定義で検出器の裁量に流れる。ジャンル別（技術解説では技術カタカナの許容度up）の閾値テーブルを B-2 に付す。出所 detector-001, naturalness-001（2026-09-20）
- **input_length の計数規約**（Markdown 記号・連続空白・改行を含むか）を確定。正規化式(IMP-002)の分母再現性に直結。出所 taxonomist（2026-09-20）
