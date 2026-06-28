# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-06-28（run 001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。06-12 Sample B は 54.6% で誤発火。06-28 では rewriter-001/002 が「統合編集（3 finding を1 span で解消）が difflib 上は小さく出る一方、再配置は削除+挿入で二重計上される」非対称を再指摘（今回は 21.7%/27.8% で閾値内に収まり実害なし）。
- 出所: rewriter-A/B（06-12）, rewriter-001/002（06-28）
- 提案: (a) 語句改変率と構造/削除率を分離計上。(b) 装飾・常套句の純削除分を控除。(c) **diff JSON に `findings_resolved` カウントを併記し「解消率」を change_rate と独立に出す**（06-28 で 2 エージェントが新規提案）。(d) 50% 中断は「意味改変 edit 比率」基準へ。
- 影響: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`
- 備考: 適用は次サイクル候補（指標再設計は影響範囲が広く、回帰検証を厚めにしてから着手）。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done(2026-06-28-001/002)` `hits: 2run`
- 症状: 正規化式が SSOT に無く、検出器ごとにスコアがブレた。06-28 で**実証**: detector-001 は raw 75 を素通しで 75.0、detector-002 は `raw/(raw+62.73)` で 28→29.7 と**別式を使用**（文書長を跨いだ比較不能）。
- **適用（v1.1）**: `raw = S1×5+S2×2+S3×0.5`、`severity_weighted_score = round(100×(1−exp(−raw/41)),1)` に固定。K=41 は検証 run 2026-06-12-001（raw≒106→既定 92.5）を再現するよう校正。検証アンカー raw 28→49.5 / 75→83.9 / 106→92.5。回帰: 参照 run の 92.5 を完全再現、A〜J 本文不変。
- 影響: `ai-tell-taxonomy.md §スキーマ`（done）, `ai-tell-detector.md §スコア算出`（done）
- 残: 検出器実装がこの式を守るかの**回帰チェック未整備** → IMP-008 へ。

### IMP-003 score_before のフィールド契約が曖昧 `status: done(2026-06-28)` `hits: 2run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。06-28 でも naturalness-002 が三系統（スキーマ例値・detector 算出値・指示値）併存を再指摘。
- **適用（v1.1）**: 「score_before = 当該 run の `02_detection.json#meta.severity_weighted_score`（唯一ソース、独自再計算で上書き禁止）」を taxonomy スキーマ節と `naturalness-reviewer.md §処理` に明文化。
- 影響: `naturalness-reviewer.md`（done）, `ai-tell-taxonomy.md`（done）

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready(布石適用)` `hits: 2run`
- 症状: 絵文字・文末単調・文長均一は文書レベル。単一 start/end で広域 locator にすると ai_tell_density が過大化（06-28 002 は f014 一件で density +0.088）。
- 出所: detector-A/B（06-12）, detector-001/002・rewriter-001（06-28）
- **布石適用（v1.1）**: finding に `scope: "span"|"document"` 任意フィールドを追加、density は document スコープ・重複 span を控除と注記。完全適用（density 算出ロジック・diff スキーマ `scope` 連動）は次サイクル。
- 影響: `ai-tell-taxonomy.md §スキーマ`（布石 done）, `ai-tell-detector.md`, `japanese-style-rewriter.md`（diff scope 未）

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready(布石適用)` `hits: 2run`
- 症状: 1 span が複数カテゴリに該当（I-4＋B-2 等）。edits/findings 1:1 前提で過小評価。06-28 でも rewriter-001（supersedes/merge_group 要望）・rewriter-002（f011→f003 等3件の従属統合）・naturalness-002（区間重複の density 二重計上）・fidelity-002 が横断指摘。
- **布石適用（v1.1）**: finding に `merged_findings: [...]` 任意フィールド追加（統合元 id 保持）。主 finding に従属をぶら下げる運用。完全適用（category_summary 集計規約・rewriter diff の merged 連動）は次サイクル。
- 影響: 全 .md のスキーマ節（布石 done）

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: 運用緩和` `hits: 1run`
- 06-28 はオーケストレーター指示で「taxonomy 基準の機械走査（手動推定禁止）」を明示し、両レビュアーが regex 走査で score_after を算出。エージェント定義への恒久反映（再走査経路の必須化）は IMP-008 と併せ検討。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

### IMP-007 過推敲検出に「新規 AI クセ混入（detection-introduced）」のカテゴリがない `status: done(2026-06-28-001)` `hits: 1run（実害観測）`
- 症状: 06-28 001 で rewriter が A-6「重要なポイントとなります」を消すため D-2「見逃せないのが…です」へ置換 → **AI クセを別カテゴリへ転位**。現行の過推敲シグナル（口語化/文体崩れ/希薄化/変更率）では捕捉できず、新規混入があっても A 等級が出る。
- 出所: naturalness-001（#1,#2）
- **適用**: `naturalness-reviewer.md` に「推敲後に新規出現した finding を過推敲シグナルに 1 件でも計上」「A 等級に『新規混入 0 件』を必須条件、1 件で A→B 降格」を追記。
- 影響: `naturalness-reviewer.md`（done）。taxonomy 側の過推敲シグナル定義への反映は次サイクル。

### IMP-008 正規化式の回帰チェック／score 突き合わせが未整備 `status: open` `hits: 1run`
- 症状: IMP-002 の式を検出器実装が守っているか検証する仕組みがない。
- 提案: 各 run で naturalness の `score_before` と `02_detection.json#meta.severity_weighted_score` の一致を assert する軽い回帰チェックを不変条件に追加（IMP-003 契約の実効担保）。
- 出所: taxonomist（06-28）

---

## P2 — 分類・レシピ・チェックリスト

### fidelity チェックリスト（06-28 適用分）
- **#14 順序語・序列の新規混入** `status: done(2026-06-28)` `hits: 2run`: 接続語/順序語を内容語へ置換した際の序列・階層・基盤・価値の新設を、原文 span への逐語照合で機械判定。`content-fidelity-auditor.md` に正式項目化（06-28 f014 pass / 06-12 f019 damaged の分岐基準を明記）。
- **#10 除外規定** `status: done`: 定量根拠のない強意副詞（飛躍的・劇的 等）の削除は情報欠落でない。context-carried（別文に残存する義務）も欠落でない＋`deletion_recall: "carried_by:..."` で明示。出所 fidelity-001/002。
- **#11 助詞レベル含意付与サブチェック** `status: done`: 係助詞・取り立て詞（は/も/こそ/さえ）の新規挿入が追加列挙・対比・限定を持ち込まないか（f018「俊敏性も」）。出所 fidelity-001。
- **`overall_verdict` キー統一＋`borderline_notes` 正式化** `status: done`: verdict 語彙を `overall_verdict: pass/damaged`（旧 `verdict/rollback_required` はエイリアス）に統一。境界所見の申し送りフィールドを正式化。出所 fidelity-001。
- modality 順序尺度（要請/推奨/義務/必須）に**依頼形「ください/お願いいたします」マッピング**を追加し義務性の上下を機械判定。`status: ready` `hits: 2run`（06-12・06-28 fidelity）。次サイクル適用候補。
- #5論理関係 と #11情報追加 の責任境界を一意化（評価順序: 義務系削除は #10 で確定→残存なら #7 自動 pass）。`status: ready` `hits: 2run`。出所 fidelity-001/002。

### playbook レシピ追補（候補）
- **公的文書の定型結び E-2 ジャンル別許容** `status: ready` `hits: 2run`: 「お詫び申し上げます／お願い申し上げます」は様式。1〜2 回許容、3 連続のみ変奏。出所 rewriter-002, naturalness-002。次サイクル適用候補。
- **逆方向の過推敲（口語化しすぎ）検出** `status: ready` `hits: 1run`: 公的文書での「ですね/しちゃう/ちょっと」等カジュアルマーカーを S2 シグナル化。下限の言語化（「ご了承ください」が崩しの下限）。出所 naturalness-002。
- **短文化は既存文の分割・言い切りで作り、新規文は挿入しない** `status: ready` `hits: 1run`: E-1「短文を挟む」が fidelity 鉄則（情報を足さない）と矛盾しないよう明記。出所 rewriter-002。
- **敬度フロア（公的文書）**: 謙譲「いたします」を下限、命令的「ください」連発は 2 回まで。出所 rewriter-002。
- **C-1 解体時に誇張語を置換先に選ばない**（IMP-007 予防）: 「次に、」→「見逃せないのが」のように D-2 誇張語へ振らせない。出所 naturalness-001。`hits: 1run`。
- C-5 絵文字削除後の文末/区切り吸収ルール（06-12 由来・未適用）。
- D 系結びは「最小着地文を残す」/ 機能が必要な接続詞は変奏 / 原文が元から推量の D 系は推量保持（06-12 由来・未適用）。

### naturalness 判定の精緻化（候補）
- **E-2 文末エントロピー指標** `status: ready` `hits: 2run`: 敬体/常体の二値では「敬体内で です/ます 二形に集中」を拾えない。敬体内の文末形態の種類数/エントロピー（体言止め・でしょう 等）を別指標化。出所 naturalness-001（06-28）, naturalness-A/B（06-12）。次サイクル適用候補。
- 正規化が非線形のため改善率と絶対残存数が乖離: 等級閾値（70/50%）を正規化スコアで見るか raw で見るか明文化。出所 naturalness-002。→ IMP-008 と関連。
- 絶対残存 S1 数 0 を A の必須条件として固定（短文で改善率が出にくいケースの誤評価防止）。出所 naturalness-001。
- クラスタ系 finding はクラスタ崩壊時に個別 severity を降格（06-12 由来）。

### 定着カタカナ語 B-2 免責 / ジャンル別ホワイトリスト `status: ready` `hits: 2run`
- 06-12: ルーティン・モチベーション・データドリブン等の定訳を半免責し残差 S3 固定。
- 06-28: **技術記事ジャンルの維持リスト**（マイクロサービス・アーキテクチャ・デプロイ・スケールアウト・オブザーバビリティ・モノリシック 等）と置換リスト（アジリティ→俊敏性）を分離。ジャンル別ホワイトリストが無いと過検出と取りこぼしが両立。出所 detector-001。次サイクル適用候補。

### detector 実装（候補）
- start/end 自己検証（regex 位置と text_span 一致を assert）。06-12 由来。06-28 は両検出器が自己検証済み。
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。06-12 由来。
- C-4「topic sentence 公式」を文頭マーカー（このように/結論として）で機械検出。出所 detector-001（実例 f020「このように、」）。

### 新パターン候補（taxonomist 審査済み・v1.1 拡張候補欄に記録、再現 2run 目で本文昇格）
- **A-14 受動状態化公式「〜されることとなりました」** [S1 相当]: 実例 002「停止されることとなりました」「実施されることに伴い」。受動＋形式名詞＋状態化の三重結合。公的文書の決定的シグネチャ。`hits: 1run`。最有力昇格候補。
- **A-5b「〜ことが可能だ／可能になる」**: 実例 001。A-5 可能冗長の別表層形。A-5 を「可能冗長クラスタ（表層形リスト）」へ再構成する案。`hits: 1run`。
- **A-8 サブ: 名詞化受動「〜がなされる」**: 実例 002「対応がなされます」。`hits: 1run`。
- **I-6 過剰敬語連結（依頼の要請化）**: 実例 002「行っていただく必要がございます」「ご持参いただくことが求められます」。I-4 を文体別（敬体の要請化）に分岐記述する案と接続。`hits: 1run`。
- **変化相冗長「〜ようになります」＋可能**: 実例 002「お探しいただけるようになります」。`hits: 1run`。
- **C-1 代替トリガ（2 点＋平行構文支配）**: 実例 001「まず→次に」2 点。3 点未満でも平行構文が段落を支配なら S1 相当。昇格時は「平行構文支配」を必須にし単独 2 点列挙を S1 にしない歯止め。`hits: 1run`。
- **C 系 redundant restatement / D-7 ブログ結び公式 / C-9 導入誘導定型**（06-12 由来・候補継続）。
