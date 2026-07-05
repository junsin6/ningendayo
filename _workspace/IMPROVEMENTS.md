# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-07-05（run 001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done` `hits: 2run` 適用: 2026-07-05
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除・**カタカナ→漢語の1対1置換（挿入+削除で二重計上）**で機械的に膨張。06-12 Sample B は 54.6% で誤 hold、07-05-001 は difflib 0.48（similarity 0.73＝正味差27%、実体は削除主導）。
- 出所: rewriter-A(0612), rewriter-B(0612), naturalness-B(0612), **rewriter-001(0705), rewriter-002(0705), fidelity-001(0705)**
- **適用内容（0705）**: playbook §変更率の数え方を二軸運用へ改訂（`change_rate`/`lexical_change_rate`(置換をmax(before,after)で1回)/`deletion_rate`/`similarity_ratio`/`meaning_edit_rate`）。強制中断を `meaning_edit_rate` 50% 基準に置換。素朴 change_rate 単独では中断しない。`japanese-style-rewriter.md` の diff meta・監視手順、`SKILL.md §総合判定`に override accept 規約を明記。
- 残: 実際の `meaning_edit_rate` 自動算出は推敲役の自己申告依存。将来 diff スキーマに meaning フラグを機械付与したい。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2run` 適用: 2026-07-05
- 症状: 正規化式が SSOT に無く、検出器ごとに分母が違いスコアが 52〜90 で再現不能。07-05 では detector-001 が `400×raw/L`（73.3）、detector-002 が `raw/L×1000`（89.5）と別式を採用。naturalness-001 は式を復元できず改善率を推定。
- 出所: detector-A(0612), detector-B(0612), **detector-001(0705), detector-002(0705), naturalness-001(0705)**
- **適用内容（0705）**: taxonomy §スキーマに `severity_weighted_score = min(100, round(400×raw/L, 1))`（係数400固定・変更禁止）を確定。`L=score_denominator_length`（02_=原文長、05_も同じ原文長を流用）を meta 必須フィールド化。`ai_tell_density` を「ユニーク被覆率・文書レベルfinding除外」と再定義。`ai-tell-detector.md §スコア算出`・`naturalness-reviewer.md`（score_before/after 契約 + score_denominator_length）を同期。→ IMP-003/IMP-006 も同時に解消方向。

### IMP-003 score_before のフィールド契約が曖昧 `status: done` `hits: 2run` 適用: 2026-07-05
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。06-12 でぶれ、07-05 でも分母定義が無く naturalness-001 が固定分母を自前復元。
- 出所: naturalness-A(0612), **naturalness-001(0705)**
- **適用内容（0705）**: `naturalness-reviewer.md` に「score_before = 02_detection.json の meta.severity_weighted_score」「score_after は同式・L は 02_ の score_denominator_length を流用」を明文化（IMP-002 と一体で適用）。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run`
- 症状: 絵文字分散・文末単調・まず…最後に・文長均一 は文書全体の統計量で、単一 start/end に紐づかない。07-05 も detector 両名が E-1/E-2/C-1 を代表 span に無理押しし density 膨張・「この1文だけ直せ」誤読リスクを報告。
- 出所: detector-B(0612), detector-A(0612), **detector-001(0705), detector-002(0705)**
- 提案: `scope: "span"|"document"|"multi_span"` と `spans: [[s,e],...]`／`metric`（stdev等）／`representative_span` を追加。density は scope=span のみ算入。
- 部分対応済（0705）: density の「文書レベル除外」は IMP-002 で taxonomy に明記済み。残りは scope フィールドの正式スキーマ化。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリに該当（I-4＋B-2＋I-1／D-2＋F-1／A-6＋G 等）。単一 category 前提で category_summary が下位カテゴリを 0 に見せる。07-05-001 で detector が secondary_categories の必要性を再指摘。
- 出所: detector-A/rewriter-A/rewriter-B/naturalness-A/fidelity-A(0612), **detector-001(0705)**
- 提案: 「1 span = 主分類 1 finding」＋ `secondary_categories: []`（or `merged_findings`）。category_summary は主カテゴリ集計と注記。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: done` `hits: 2run` 適用: 2026-07-05
- 症状: 仕様は「検出器を再走査」だが 06-12 は手動照合で推定値。
- 出所: naturalness-A(0612), **naturalness-001(0705)=実際に ai-tell-detector 再走査に成功しIMP-006を実証**
- **適用内容（0705）**: `naturalness-reviewer.md §処理` に「ai-tell-detector を同基準で再走査（手動照合のみで済ませない）」を明記。0705 両 naturalness とも検出器再走査を実施済み。

---

## P2 — 分類・レシピ・チェックリスト

### 適用済み（0705）

- **定着カタカナ語 B-2 免責リスト → 3段判定辞書に昇格** `status: done` `hits: 2run` 適用: 2026-07-05
  - 06-12（ルーティン・モチベーション・データドリブン）＋07-05（シャーディング・レプリケーション・クエリ・プロンプト・スタック等の境界語で A↔B が反転）で再現。
  - 適用: taxonomy B-2 に「3段判定（maintain/replace/context）辞書＋`katakana_tier` フィールド＋複合語最長一致＋grade で context 語 0.5 換算」を追記。
  - 出所: naturalness-B/fidelity-A/naturalness-A(0612), detector-001/rewriter-001/naturalness-001(0705)

### 昇格候補（hits 加算・未適用）

- **modality（義務強度）を順序尺度化** `status: ready` `hits: 2run`
  - `must>should>依頼>想定>任意` の順序で delta 記録、1段以内 pass。06-12 fidelity-A ＋ 07-05 fidelity-002（I-3「必要があります」→「ください」delta0、f019「必要となる」→「いただく」delta-1）。
  - 影響: `content-fidelity-auditor.md` チェックリスト。
- **過推敲シグナルの定量化（両側閾値）** `status: ready` `hits: 2run`
  - 敬体/常体混入 = `min(敬体文,常体文)≥1`、体言止め率レンジ 0.05〜0.30（下限割れ=E-2残存/上限超え=過推敲）。06-12 naturalness-A ＋ 07-05 naturalness-001。
- **E-2 文末単調の到達可能ライン（純敬体はジャンル注記）** `status: ready` `hits: 2run`
  - 純敬体本文に体言止めを強制すると常体感が混じり過推敲。語尾語彙分散・文長変奏を主手段とし体言止めは任意。06-12 naturalness-B ＋ 07-05 rewriter-001/naturalness-001。
  - 影響: playbook E-2 レシピにジャンル注記。

### 新規起票（0705・hits:1 候補）

- **公的文書ジャンルの playbook 節が無い（受動許容・敬語配分・接続詞許容）** `status: candidate` `hits: 1`
  - (a) A-8 受動: 「主語が動作対象／行為者が自明でない告知」は受動維持が正文体。行為者=発信主体が明確な叙述のみ能動化。(b) 過剰敬語: 結びの最上位敬語（お願い申し上げます）は1回残し他を一段軽い丁寧形へ配分（格でなく回数を削る）。(c) C-1 と H-1 は同一段落で連動評価（まず/次に削除後に残る「なお/また」が浮く）。
  - 出所: rewriter-002, naturalness-002, fidelity-002(0705)。playbook に「公的文書（お知らせ・通知）」節を新設するのが最優先。
- **genre 別 severity/grade 補正** `status: candidate` `hits: 1`
  - 公的文書では正当な受動・結び敬語が構造的に数件残る。grade 判定前に「行為者復帰不能の受動」「結びの定型敬語」を残存カウントから控除する前処理。meta に genre と減衰係数。
  - 出所: detector-002, naturalness-002(0705)。
- **推敲役の「近接文脈 語彙衝突チェック」手順** `status: candidate` `hits: 1`
  - finding を独立に直すと近接 span で新たな反復を生む（f019「お願いする場合」＋直後「お願いする場合」の二重）。推敲後に近接反復スキャンを追加。
  - 出所: rewriter-002(0705)。
- **I-4→I-3 横移動（lateral move）を grade で減点** `status: candidate` `hits: 1`
  - suggested_fix が別カテゴリの同深刻度パターンを生む場合（求められる→必要がある：曖昧行為者の芯が残る）は消えたと数えない。
  - 出所: naturalness-001(0705)。

### fidelity チェックリスト追補

- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** `status: ready` `hits: 1`（0612 f019）。※ 07-05 では該当型の混入なし＝回帰なしを確認。
- **評価・強調強度（intensity）の保存を独立項へ** `status: candidate` `hits: 1`
  - 「欠かせない→重要」「非常に重要→重要」は量化でも modality でもない評価強度の軟化。「事実命題か評価命題か／極性不変か／一段階以内か」の3判定フロー。出所: fidelity-001(0705)。
- **`semantic_delta` フィールド（none/minor/context-restored/loss）** `status: candidate` `hits: 1`
  - カタカナ日本語化の意味減衰を可視化。トレードオフ→兼ね合い（単独 loss だが文脈で復元＝context-restored）。出所: fidelity-001(0705)。
- **形容詞→動詞・名詞→動詞への含意吸収は欠落ではない（除外規定）** `status: candidate` `hits: 1`
  - 「高い可用性をもたらす→可用性を高める」の字面 diff 誤検出防止。出所: fidelity-001(0705)。
- **指示語化による削除は参照先の実在確認後に pass** `status: candidate` `hits: 1`
  - 「セマンティックな検索→こうした検索」は前方参照が実在して初めて情報保存。出所: fidelity-001(0705)。
- **手続き情報保存チェックを独立項に（公的文書）** `status: candidate` `hits: 1`
  - procedural_checklist 配列で条件を逐条1対1照合。「語（措置）は消えても手続き実体は残る」ケースと「条件が落ちる」ケースを区別。出所: fidelity-002(0705)。
- **敬語格の毀損は advisory（keigo_grade_note）として自然度へ委譲** `status: candidate` `hits: 1`
  - fidelity は判定せず「全体の丁寧度が毀損していないか」だけ検知し naturalness へ引き継ぐ。出所: fidelity-002(0705)。
- 削除専用サブチェック（deletion-recall test）`status: ready` `hits: 1`（0612）。
- 「情報を含む削除 vs ボイラープレート削除」二分判定 `hits: 1`（0612）。

### playbook レシピ追補（0612 由来・据え置き）
- C-5 絵文字削除後の文末/区切り吸収ルール。D 系結びは「最小着地文を残す」。機能が必要な接続詞（しかしながら）は削除でなく変奏。原文が元から推量の D 系は推量を保持。

### 新パターン候補（taxonomist 審査）
- **A-14「〜という流れになっている/という流れです」プロセス名詞化 [S2案]** 手順の締めを機械的に名詞化。実例 07-05-001「回答を生成するという流れになっています」。現状 A-6＋A-13 合成で拾える。`hits: 1` 出所 detector-001。
- **K. 過剰敬語・二重敬語 [新大分類案]** 「〜いただきますようお願い申し上げます」依頼マトリョーシカ、「ご提示をお願いする」＋「ご了承いただく」連鎖。設計思想の4大重心なのに A〜J に受け皿なし。実例 07-05-002。`hits: 1` 出所 detector-002/rewriter-002/naturalness-002。
- **A-6 に「〜こととなりました/こととなります」副例追加** 公的文書 AI 頻出。実例 07-05-002。`hits: 1` 出所 detector-002。
- （0612 由来）C系 redundant restatement、D-7 ブログ結び公式、C-9 導入誘導定型。

### インフラ / 運用
- **並列サブエージェントがスクラッチパッドを共有し中間ファイル（build.py）が衝突** `status: candidate` `hits: 1`
  - 07-05 で detector 2 名が同名スクリプトを上書き。最終 JSON は run 別ディレクトリで無事だが、各エージェントに run_id 付きユニークファイル名を強制すべき。出所: detector-001(0705)。
- start/end 自己検証（0612）→ 07-05 両 detector が実施し不一致0を報告＝定着。絵文字正規表現レンジ明示（0612）据え置き。
