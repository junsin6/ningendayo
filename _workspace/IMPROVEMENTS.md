# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-08-29（run 001 技術解説, 002 公的文書）

> **2026-08-29 サイクル要約**: day-1 ジャンル（技術解説記事・公的文書）で2 run 完走。全 P0（IMP-001/002/006）と IMP-003 が別 run で再現し hits≥2 に到達 → **本日 IMP-001・IMP-002・IMP-006(+003) を実適用（status: done）**。run 001=grade A/override accept、run 002=round2 で C→A/accept。

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done` `hits: 2run(6agent)` `applied: 2026-08-29-001/002`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。2026-06-12: Sample B 54.6% で `hold_and_report` 誤発火。**2026-08-29 再現**: run 001 change_rate 0.4116（fidelity=pass・意味改変0・grade A）、run 002 0.363（同）。いずれも削除主導で語句改変率は 0.19/0.14 と低い。
- 出所: rewriter-A/B, naturalness-B（06-12）＋ rewriter-001/002, fidelity-001（08-29）
- **適用済み**: `rewriting-playbook.md §変更率の数え方` を二層化（`change_rate`/`lexical_change_rate`/`delete_rate`/`insert_rate`/`semantic_change_edit_ratio` を分離計上、主判定は lexical と semantic、高密度原文は閾値+10pt 緩和）。`SKILL.md §総合判定` に **override accept** 行を追加（A/B＋fidelity=pass＋総 change_rate のみ30%超は accept 扱い）。
- 残: `japanese-style-rewriter.md` への指標算出明記は未（rewriter は既に diff meta に自発出力しているため優先度低）。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2run(4agent)` `applied: 2026-08-29`
- 症状: 正規化式が SSOT に無く高密度短文で raw が 100 付近に張り付く。**2026-08-29 再現・悪化**: run 001 raw 106.5 が旧 `min(100,raw)` で **100.0 に完全飽和**（解像度ゼロ）、detector-001/002 が明示指摘。
- 出所: detector-A/B（06-12）＋ detector-001/002, naturalness-001（08-29）
- **適用済み**: `ai-tell-taxonomy.md §検出出力スキーマ` と `ai-tell-detector.md §スコア算出` に飽和スコア `100×(1−exp(−raw_density/8))`（raw_density=raw/(input_length/100), K=8）を定義。検算: run001 raw106.5/787字→81.6、run002 raw58/707字→64.1（飽和せず比較可能）。旧 run（92.5/68.3）は非飽和のため回帰なし。taxonomist が v1.1 昇格審査中。

### IMP-003 score_before のフィールド契約が曖昧 `status: done` `hits: 2run` `applied: 2026-08-29`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。**2026-08-29**: naturalness-001 が score_before=100.0（飽和クリップ）を採り改善率の分母が実悪度を反映しない問題を再指摘。
- 出所: naturalness-A（06-12）＋ naturalness-001（08-29）
- **適用済み**: `naturalness-reviewer.md` と `SKILL.md §4` に「score_before = 02_detection.json の meta.severity_weighted_score」を明文化。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready(部分適用)` `hits: 2run(4agent)`
- 症状: 絵文字/文末単調/受動反復は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。**2026-08-29 再現**: run 001 の A-5×6・A-10 並列3文・E-2 全14文、run 002 の A-8 受動8回・「につきましては」5回・お願い定型4回。detector-001 は density を union 被覆で 0.431→0.339 に是正して回避。
- 出所: detector-B/A（06-12）＋ detector-001/002, rewriter-002, fidelity-002（08-29）
- **部分適用 (2026-08-29)**: density 定義を「文書レベル代表 span 除外の union 被覆」へ明文化（taxonomy/detector）。**残**: `occurrences: [[s,e],...]` / `scope:"sentence"|"document"` の**スキーマ追加は未適用**（次サイクル最優先。反復系 finding を1件で複数 span 束ねられるようにする）。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複／束ね型 finding の finding/edit カウント規約が無い `status: ready` `hits: 2run(7agent)`
- 症状: 1 span が複数カテゴリに該当。加えて**束ね型 finding**（1 finding が reason に複数出現位置を列挙し span 外の同型反復まで推敲対象化）が span-grounded 原則と衝突。**2026-08-29 再現**: run 002 の f005/f009/f018 が束ね型で、fidelity-002・rewriter-002 が「監査が span 外調整を毎回個別確認せざるを得ない」構造欠陥として指摘。
- 出所: detector-A, rewriter-A/B, naturalness-A, fidelity-A（06-12）＋ fidelity-002, rewriter-002（08-29）
- 提案: 「1 span = 主分類 1 finding」＋ `merged_findings:[...]`。反復系は出現ごとの個別 finding か 1 finding の `spans[]` 配列で発行し推敲役の編集権限を明示化。IMP-004 のスキーマ拡張と同時適用が効率的。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を spawn できず score_after が自己採点になる `status: done` `hits: 2run(3agent)` `applied: 2026-08-29`
- 症状: 仕様は「検出器を同基準で再走査」だが、**サブエージェント naturalness-reviewer には Agent/Task 起動系ツールが配布されず ai-tell-detector を spawn 物理不能**。手動照合フォールバックが黙って通り score_after が推定値化。**2026-08-29 で構造的欠陥として確定**: naturalness-001/002 とも ToolSearch で確認のうえ実行不能を報告、round2 再レビューでも再現。
- 出所: naturalness-A（06-12）＋ naturalness-001/002（08-29、3 レビュー横断）
- **適用済み**: オーケストレーターが detector を `03_rewrite.md` に再実行し `05_rescan.json` を生成して reviewer に渡す経路を正規化（`SKILL.md §4`）。reviewer は spawn 不能環境では手動再走査し `meta.rescan_method`（agent_rescan/manual_taxonomy_rescan）を**必須記録**（黙って通るのを防止）。`naturalness-reviewer.md` の入力・処理・出力スキーマを更新。

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

---

## 2026-08-29 サイクル 新規起票（day-1: 技術解説・公的文書）

### 新パターン候補（taxonomist 審査済 → v1.1 拡張候補欄に記録。正式昇格は cross-run 再現後）
- **A系複合「抽象主語＋可能形」3連** → **採用 C-2026-08-01**（同型3連の平行反復ゲート付き複合タグ A-5×A-10 / A-14 案。単独 S1 は禁止）。実例(001)「メトリクスを使えば…可視化できます／ログには…残ります／トレースをたどれば…追跡できます」。`hits: 1` 出所 detector-001
- **公的文書 過剰敬語連鎖「〜におかれましては」前置き** → **却下 R-2026-08-01**（実務公文書・儀礼文で人間が普通に使う定型敬語。「人間がほぼ使わない」要件に抵触。再提案は二重敬語の高密度反復≥3 等の分離条件を設計できた場合のみ）。出所 detector-002
- **公的文書 依頼定型の全段落反復「〜いただきますようお願い申し上げます」** → **採用 C-2026-08-02**（密度≥3の機械反復ゲート付き）。実例(002)4回。`hits: 1` 出所 detector-002
- **受動＋状態叙述複合「〜とされております」** → **採用 C-2026-08-03**（新項目でなく A-6×A-8×敬体の共起タグ）。実例(002)3件。`hits: 1` 出所 detector-002
- **D系 severity の反復段階化** → **採用 C-2026-08-04**（D-1 の severity カウント則追補: 単発=S2/≥2=S1。推敲役の「クセ付け替え」を捕捉）。実例(001) 受動除去の過程で D-1 を新規混入。`hits: 1` 出所 naturalness-001

### fidelity チェックリスト追補（2026-08-29）
- **#7b 可能・能力法の保存**（potential/capability mood）: 「保持できる」→「残る」等、可能法の消失で「できる」という主張自体が消えていないか。現行 #7 modality は断定/推量/義務のみで可能法を扱わない。`status: ready` `hits: 1` 出所 fidelity-001
- **#5b 条件節・前件の新規付与検査**: 無条件命題「Xは〜できる」に「Xを使えば」等の前件を挿入していないか。#5 は削除側しか想定せず挿入を検査しない。`status: ready` `hits: 1` 出所 fidelity-001
- **#7a 要件標識の保存（public_notice/legal）**: 「必要／要する／前提」等 deontic 標識が依頼形（お願いします/ください）へ縮約されていないか。ジャンル=公的文書/法律のとき S1 昇格。実例(002) f011 で毀損→round2 修復。`status: ready` `hits: 1` 出所 fidelity-002
- **束ね型 finding の span 一致検証**: finding.span と実改変位置の一致を監査側でも二重検出（IMP-005 と連動）。出所 fidelity-002

### playbook レシピ追補（2026-08-29・公的文書ジャンル）
- **結辞（最終文）は文末変奏の対象外／改まり度を一段上げて締める**: E-2 分散が締めの一文まで命令形「ご活用ください」に落とし過推敲化（002 round1）。`status: ready` `hits: 1` 出所 rewriter-002, naturalness-002
- **ジャンル×敬度の下限表**: public_notice の依頼下限=「お願いいたします」、結辞=「お願い申し上げます」許容。「お願いします」混入を防ぐ。出所 rewriter-002
- **主題助詞-文末述語の敬語整合チェック**: 「皆様には…ください」の係り受け崩れ（`〜には`は要請構文を呼ぶ）。同一文にまたがる複数 edit の相互作用を検査。出所 rewriter-002
- **平行 finding のクラスタ統一処理**: 同カテゴリ・同構文の finding（例 f011/f014 の窓口手続き）は処理方針を統一（両方とも義務標識保存）。出所 rewriter-002
- **ジャンル別 net_length_retention 下限ガード**: public_notice は 0.80 未満で警告（様式的重みの削りすぎを推敲段階で早期検知）。change_rate 閾値内でも過縮約は起こる（002: 24%減で閾値内）。`status: ready` `hits: 1` 出所 rewriter-002, naturalness-002

### naturalness 判定の精緻化（2026-08-29）
- **同一敬体内のレジスター（改まり度）低下を検出する軸が無い**: 現行は敬体/常体の混入のみが文体崩れ判定で、「お願い申し上げます→ください」の一律置換（AI クセ除去としては満点）で公文書の改まりが崩れても無警告通過。ジャンル別「下限レジスター」を定義。`status: ready` `hits: 1` 出所 naturalness-002
- **依頼形「〜ください」の一本調子**を E-2 検出網に追加（「です・ます単調」だけでなく）。出所 naturalness-002
- **過推敲下限ガードの不在**（上限30/50%はあるが下限が無い）。純長さ減少率下限・様式マーカー保持数をジャンル別に。出所 naturalness-002
