# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-06-20（run 2026-06-20-001 技術解説 / -002 公的文書）。本日 IMP-001/002/003/005 を適用（status: done）。

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done` `hits: 2run(7agent)` `applied: 2026-06-20-001/002`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。Sample A も 47.6% と高止まり。**2026-06-20 で再現**: run 001（技術解説）の change_rate 32.7% は delete 179 字 ≫ insert 60 字の削除主導で、純装飾削除のみ・意味改変ゼロ（fidelity=pass / 自然度 A）。run 002 も削除主導 19.97%。
- 出所: rewriter-A, rewriter-B, naturalness-B（day0）/ rewriter-001, naturalness-001, fidelity-001, fidelity-002（2026-06-20）
- 提案: (a) 「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を change_rate から控除。(c) 挿入率を単独併記し、del≫ins の削除主導ケースは中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。
- **適用（2026-06-20）**: `delete_rate`/`replace_rate`/`insert_rate` を分離計上し、中断判定を `replace_rate`（語句改変率）基準へ変更。削除主導は中断対象外と明記。`rewriting-playbook.md §変更率の数え方`・`japanese-style-rewriter.md`（手順5＋diff スキーマ）・`SKILL.md`（推敲監視＋override 注記）を編集。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2run(4agent)` `applied: 2026-06-20-001/002`
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える（Sample A raw106→92.5、taxonomy 例は raw56→71.5 と不整合）。**2026-06-20 で再現**: detector-001/002 が各自バラバラの暫定式（K=input_length/100×5 vs raw/length×1000）を発明。naturalness-001/002 は推敲で input_length が縮むと K も縮み score_after が上振れする分母可変バイアスを指摘。
- 出所: detector-A, detector-B（day0）/ detector-001, detector-002, naturalness-001, naturalness-002（2026-06-20）
- **適用（2026-06-20）**: SSOT に固定式を明記 — `raw=ΣS1×5+S2×2+S3×0.5`、`K=max(input_length,1)/100×5`、`score=round(100×raw/(raw+K),1)`。**再計測（score_after）は score_before と同じ K（原文長由来）を使用**し短文化バイアスを除去。`ai-tell-taxonomy.md §検出出力スキーマ`・`ai-tell-detector.md §スコア算出` を編集。taxonomist が v1.1 へ昇格・整合性検証済み。

### IMP-003 score_before のフィールド契約が曖昧 `status: done` `hits: 1run` `applied: 2026-06-20-001/002`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score 92.5）。レビュアーごとに数値がぶれる。
- 出所: naturalness-A
- **適用（2026-06-20）**: IMP-002 と同時に SSOT へ「score_before = 02_detection.json の meta.severity_weighted_score」を明文化。本日の naturalness-001/002 は実際にこの契約どおり 76.8 / 46.6 を基準に算出し、運用で検証済み。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run(3agent)`
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。**2026-06-20 で再現**: 両 run の E-2（文末単調）が文書レベル finding として広域 span で表現され、detector-001 は A-5 反復・C-1 を locator span 化。density 過大の懸念が継続。
- 出所: detector-B, detector-A（day0）/ detector-001, detector-002（2026-06-20）
- 提案: `span_type: "contiguous"|"scattered"|"document"` と scattered 用 `occurrences: [[s,e],...]` を追加。density は重複・locator を除いた実 AI クセ文字数ベースと定義。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`
- **次回適用候補**（hits≥2 達成）: IMP-005 の also_matches と整合する形で span_type を追加すると schema 改訂が一度で済む。

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: done` `hits: 2run(7agent)` `applied: 2026-06-20-001/002`
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。**2026-06-20 で再現**: detector-001 が「可能となっています」(A-6＋A-5)・「ソリューションを提供します」(A-10＋B-2)・末尾「予想されると言えるでしょう」(D-1＋G-2) を多数報告、rewriter-001 が multi-finding edit の紐付け方針を自己裁量で決定。
- 出所: detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A（day0）/ detector-001, rewriter-001（2026-06-20）
- **適用（2026-06-20）**: finding に `also_matches: []` を追加。「1 span = 主 finding 1 件（最深刻カテゴリ採用）、副は also_matches、集計は主 category のみで二重計上しない」を SSOT に明記。multi-finding を 1 edit で解消した場合のみ `finding_ids: []` 配列を許容。`ai-tell-taxonomy.md`・`ai-tell-detector.md` を編集、taxonomist が v1.1 で整合性検証済み。

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: verified` `hits: 1run`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。
- 出所: naturalness-A
- 提案: `ai-tell-detector` をサブエージェントとして再呼び出しする経路を必須化（手動照合禁止）。
- **運用検証（2026-06-20）**: naturalness-001/002 がともに ai-tell-detector を実サブエージェント呼び出しで再走査でき、同一正規化式を引き渡せた（手動フォールバック不要）。**経路は安定**。残るは `naturalness-reviewer.md` への「再走査必須・手動照合禁止」の明文化（次回適用候補、軽微）。

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 001。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B
- **（新）進行アスペクト「〜していく / 〜していきます」濫用** 動作に不要な進行・継続相を付与。実例「解説していきます」「高まっていく」（2026-06-20-001）。A-5/E-2 近接だが独立シグネチャ。A 群に「アスペクト/テンス操作」サブ群新設の余地。 `hits: 1run` 出所 detector-001。taxonomist が v1.1 拡張候補欄へ記録済（別 run 再現で昇格）。
- **（新）公的文書お願い定型反復「〜いただきますようお願い申し上げます/いたします」** 依頼文末を一律処理。D-6 の公的文書版。実例: 2026-06-20-002 に複数。 `hits: 1run` 出所 detector-002, rewriter-002。
- **（新）敬語スタック「ご＋動詞＋いただく必要がございます」** 行為者を曖昧にしたまま敬語で要請を重畳。実例「ご承知いただく必要がございます」「ご注意いただく必要がございます」（2026-06-20-002）。I-3 の公的文書サブ型候補。 `hits: 1run` 出所 detector-002, rewriter-002, fidelity-002。
> taxonomist 申し送り: 上記は「同一 run 内反復」のため**別 run での再現を昇格条件**とする（同一文書内反復は独立試行でない）。昇格候補欄に「密度しきい値」「ジャンル限定」フィールドを定型化すべき。

### 2026-06-20 新規（公的文書・技術記事 run 由来）
- **modality 種別の質的すり替えを #7 が捕捉できない** `status: ready` `hits: 1run` 出所 fidelity-002。「必要がございます（必要性叙述）」→「お願い申し上げます／ください（依頼・命令）」の変換を #7 は強度一次元しか見ず、義務の様態（義務／必要／依頼／命令／注意）の質的変化を見逃す。公的文書では行政的ニュアンスが変わりうる。#7 に「modality 種別の保存」サブ軸を追加。IMPROVEMENTS の既出「modality 強度を順序尺度化」と統合可。
- **公的文書「連絡経路 AND 全保存」専用チェックの欠如** `status: P2` `hits: 1run` 出所 fidelity-002。変更時告知「市HP **および** 広報車」の two-channel、避難/問い合わせ経路などは AND 関係で全保存が必須。#10（情報欠落）は汎用すぎて担保しない。公的文書ジャンル専用チェックを追加。
- **ジャンル依存の準術語免責が #12 に無い** `status: P2` `hits: 1run` 出所 fidelity-001。一般語に開いた語（approach→やり方、seamless→そのまま）が当該ジャンルで準術語化している場合の含意脱落（例 seamless＝無停止性）を #12 が捕捉できない。入門記事は免責、API/SLA 文書では毀損になりうる。
- **告知文の完了形→現在形の文脈補正が #8 に無い** `status: P2` `hits: 1run` 出所 fidelity-002。「実施されることとなりました→実施します」は決定告知特有で毀損なしだが #8 が機械的に過去→現在で減点しがち（過剰 rollback リスク側の欠陥）。

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
