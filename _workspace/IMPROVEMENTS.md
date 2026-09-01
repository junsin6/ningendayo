# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数（**別 run での再現のみ +1**）。

最終更新: 2026-09-01（run 001 エッジAI技術解説, 002 図書館お知らせ）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done(2026-09-01-001/002)` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除・A系節単位書換えで機械的に膨張。
- 2026-06-12: Sample B 54.6% で hold 誤発火（実際 fidelity=pass/自然度A）。
- 2026-09-01 **再現**: run001 総合44.6%（語句34.4%/削除構造10.2%）— A系節書換えが difflib『replace』一括計上で膨張。run002 総合29.9%（語句4.6%/削除構造25.3%）— 過剰敬語パディング縮約が headline を押し上げ。両 run で rewriter/fidelity/naturalness が横断再現。過推敲シグナル「変更率>30%」の偽陽性を直接発火。
- 出所（累計）: rewriter-A/B, naturalness-A/B, fidelity-A/B（両日）
- **適用（2026-09-01）**: playbook §変更率の数え方 と SKILL §総合判定 に「語句改変率／削除・構造率の分離計上」を正式指標として明記。50% 中断・override は語句改変率基準に置換。→ 下記 Step4 適用ログ参照。
- 残: token/文節単位の正規化距離、語句改変率の「等価言い換え vs 情報改変」二分は将来課題（P1 へ降格して継続）。

### IMP-002 severity_weighted_score の正規化が未定義で saturate/不整合 `status: done(2026-09-01 taxonomy v1.1)` `hits: 2run`
- 症状: 正規化式が SSOT に無く、detector ごとに式がぶれる。
- 2026-06-12: 高密度短文で raw が 100 付近に張り付き解像度が消える。
- 2026-09-01 **再現・悪化**: 同じ「ほぼ全文が tell」の 2 サンプルで detector-002 は D_max=0.11 式で 93.8、detector-001 は K=350 式で 59.1 と**大きく不整合**（001 の方が密度高なのにスコア低）。before/after 比較が detector 依存で破綻。
- 出所: detector-A/B（両日）
- **適用（2026-09-01）**: taxonomy SSOT に単一の飽和正規化式を明記。`score = 100×(1−exp(−(raw/L)/c))`, `raw=5·S1+2·S2+0.5·S3`, `L=input_length`, `c=0.05`。単調・有界・張り付き回避。→ Step4 適用ログ参照。

### IMP-003 score_before のフィールド契約が曖昧 `status: done(慣行確立)` `hits: 2run`
- 症状: score_before にどの値を使うか未固定だった。
- 2026-09-01 **確認**: 両 naturalness-reviewer が「score_before = 02_detection.json の meta.severity_weighted_score」を明示採用（59.1 / 93.8）。慣行として定着。
- **適用済**: naturalness-reviewer.md に既記載の想定。IMP-002 の式確定で score の意味も安定化。クローズ。

---

## P0.5 — 実行基盤の欠陥（今日発覚・最優先で修正必要）

### IMP-006 naturalness-reviewer が検出器を実呼び出しできない `status: ready` `hits: 2run` ⚠️昇格
- 症状: 仕様（＋今回の指示）は「ai-tell-detector をサブエージェントとして実呼び出しし再走査」だが、**サブエージェント実行環境に Agent/Task ツールが無く**、両 naturalness-reviewer が実呼び出し不能。フォールバックで taxonomy 基準の自前再走査に退避（各自 JSON に明記）。
- 2026-06-12: 手動照合で数値が推定（hits 1run）。
- 2026-09-01 **再現・原因特定**: 環境的にサブエージェントは他サブエージェントを起動できない（ToolSearch で SendMessage 等のみ確認）。→ 手動照合が構造的に不可避。
- 出所: naturalness-A/B（両日）
- 提案: (a) score_after 再計測は**オーケストレーター層**で detector を再呼び出しし、その結果をレビュアーに渡す設計へ変更（責務移管）。(b) もしくは detector ロジックを両者が共有する軽量スクリプト化。naturalness-reviewer.md と SKILL.md のパイプライン記述を「再走査はオーケストレーターが担当」に改訂。
- 影響: `naturalness-reviewer.md`, `SKILL.md §4並列検証`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run`
- 症状: E-1/E-2/C-1 は文書横断パターンで単一 start/end に収まらない。
- 2026-09-01 **再現**: run002 で E-1/E-2 を start=0/end=L の丸ごと指定で回避、run001 で C-1 を「まず」位置代表＋他2語を reason 退避、rewriter は finding_id を重複させ 3 行展開。rewriter が「どこを直せば消えるか」を機械取得できない。
- 出所: detector-A/B, rewriter-A, fidelity-B（両日横断）
- 提案: finding に `scope: "span"|"sentence"|"document"` と `evidence_spans: [[s,e],…]`（複数 span 配列）を追加。density は union で計算。edit スキーマ側に `edit_group`（1 finding→複数 edit の親子）。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`, diff スキーマ

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリに該当し edits/findings が乖離、density 二重計上。
- 2026-09-01 **再現・実例**: run001 で `もたらすインパクト`=A-10+B-2、`リアルタイム性が求められる`=I-4+B-2(+F-5)、`ランタイム…サポート`=A-10+B-2 等 3〜6 箇所。detector は素朴合計 258 字 vs union 実 253 字。rewriter は diff に `overlaps_with` 欄が無く rationale へ手記録。
- 出所: detector-A, rewriter-A/B, naturalness-A, fidelity-A（両日横断・最多）
- 提案: (a) density は **union で定義**（SSOT 明記）。(b) edit スキーマに `overlaps_with:[finding_id]` と `edit_type: lexical|deletion|structural` を追加。(c) 「1 span=主分類1 finding＋merged_findings[]」規約。
- 影響: 全 .md のスキーマ節, diff スキーマ

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **K. 過剰敬語（Excessive Keigo）★日本語固有・公的文書** `hits: 1run(002/3agent)` — 昇格条件（別 run 再現）待ちだが実例2件以上を run002 内で充足。detector-B・rewriter-B・naturalness-B が独立提案。実例（全て本文）:
  - K-1 させていただく濫用: 「休館とさせていただく」「お知らせさせていただく」→「休館します／お知らせする」
  - K-2 二重敬語・冗長謙譲: 「ところでございます」「予定となっております」
  - K-3 必要叙述の敬体化: 「〜する必要がございます」→勧告「〜ください」（I-3 の敬体特化）
  - 注: 公的定型（お願い申し上げます・ご案内・お詫び）は残す＝最小着地文原則を敬語文脈へ。
  - **次 run（公的文書ジャンル再訪 day1）で再現すれば K カテゴリとして v1.1 昇格審査。**
- **A-8b 無主語受動（実施される/図られる/行われる）** `hits: 1run(002)` — A-8 が「によって」限定のため行為者省略の無主語受動を拾えない。サブ項目化候補。出所 detector-B。
- **A-14 「〜を可能にする」（enable 直訳）** `hits: 1run(001)` — 「デプロイすることを可能にします」。A-5 と A-10 に半分ずつ該当し専用項なし。出所 detector-A。
- **F-1 拡張: 漸増副詞（ますます／より一層／いっそう）** `hits: 1run(001)` — 「ますます重要」「ますます拡大」（2回）。現行 F-1 は程度副詞のみ。例示追加候補。出所 detector-A。
- **D-4 例示追加「可能性を秘める」** `hits: 1run(001)` — 「大きな可能性を秘めています」。出所 detector-A。
- **C 系: redundant restatement**（叙述と箇条書きの二重記載） `hits: 1run(001,6/12)` 出所 detector-A。
- **D-7 ブログ結び呼びかけ公式** `hits: 1run(6/12)` 出所 detector-B。
- **C-9 導入誘導定型「さっそく見ていきましょう」** `hits: 1run(6/12)` 出所 detector-B。

### ジャンル別 severity 補正 `status: candidate` `hits: 1run(001+002)`
- A-2「〜につきましては」は公的文書で慣用度が高く、単発なら過検出。ジャンル別 severity 補正表（公的文書では A-2 を S2 扱い）を検出手順に。出所 detector-B。
- 定着カタカナ語（フレームワーク/ニューラルネットワーク/アプリケーション等）は技術解説で借用可、一般文で開く。→ 下記 B-2 免責 allowlist と統合。

### fidelity チェックリスト追補
- **item7 に「可能」軸を明示（可能→断定の過変換は毀損）** `status: ready(緊急)` `hits: 1run(001)` — 実例 f020「向上させることができます」→「向上します」を**実捕捉**。推敲役が「A-5 冗長簡約」と称し合法化しやすい。姉妹 edit f007/f027 は可能保持で内部不整合。**実害ありのため次 run 待たず適用推奨**。出所 fidelity-A。
- **modality 強度の順序尺度化（要請<推奨<義務<必須）＋敬語強度差分** `status: ready` `hits: 2run` — 6/12 fidelity-A で起票、9/1 fidelity-B で再現（義務→依頼の一段軟化が個別合格でも累積3箇所を捕捉できず）。before/after をステップ値化し run 内総軟化量に閾値を。実例 f004/f007/f014。
- **削除専用サブチェック（deletion-recall）型別3分類** `status: ready` `hits: 2run` — 6/12 fidelity-B 起票、9/1 fidelity-A 再現。(a)英語併記削除→用語同定可能性 (b)序列語削除→列挙構造 (c)程度副詞削除→強度。fidelity-A は JSON 内に暫定実装。
- **#5論理 vs #11情報追加 の境界（条件/因果接続語の二重判定）** `status: ready` `hits: 2run` — 6/12 起票、9/1 fidelity-A 再現（f032「進化すれば」新規条件導入が #5/#11 で宙づり）。新規導入接続語は両項で二重判定。
- **能動化に伴う主体断定の専用項** `hits: 1run(002)` — 無主格→顕在主語変換を独立項でログ化し主体一意性を判定。今回自明ゆえ pass だが多候補文で誤帰属リスク。出所 fidelity-B。
- **指示詞・ゼロ主語の具体化に antecedent 一意性チェック** `hits: 1run(001)` — 「この技術→エッジAI」型は直近文脈で antecedent 一意なら pass、曖昧なら情報追加。出所 fidelity-A。
- **item6 に程度副詞（強度）軸を追補** `hits: 1run(001)` — intensifier 削除（ますます等 F-1）を評価できるよう。出所 fidelity-A。

### playbook レシピ追補
- **C-5 絵文字削除後の文末/区切り吸収ルール**（6/12, rewriter-B）。
- **D 系結びは「最小着地文を残す」**（6/12 起票, 9/1 rewriter-B が敬語文脈で再現＝「ご協力をお願いいたします」等を残置） `hits: 2run`。
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**（6/12, rewriter-A）。
- **原文が元から推量の D 系は推量を保持**（6/12, rewriter-A）。
- **E-2 の敬体バリエーション交替表**（〜ください/です/があります/いたします/申し上げます）を敬体向けに追記 `hits: 1run(002)` 出所 rewriter-B。公的文書で「でしょう」が使いにくい問題。
- **E-2 体言止めの敬体安全域**（開幕文の体言止めは常体印象を招く。文中位置による可否ガイド） `hits: 1run(001)` 出所 rewriter-A。

### naturalness 判定の精緻化
- **クラスタ崩壊時の severity 降格ルール** `status: ready` `hits: 2run` — 6/12 naturalness-A 起票、9/1 naturalness-A 再現（フレームワーク f022: 周辺13語解消で B-2 発火条件崩壊も残存1語をフル S2 で二値カウント）。推敲後に反復回数が閾値割れした密度依存 finding は severity 再計算。
- **絶対残存数ガード／短文の改善率 precedence** `status: ready` `hits: 2run` — 6/12 起票、9/1 naturalness-A 再現（519字短文で raw 微差が改善率を極端化。800字未満は絶対残存 S1/S2 件数を主判定に）。
- **終端形態素エントロピー測定（E-2 false-resolved 防止）** `hits: 1run(001)` — 語尾変奏だけの浅い解消を検出。出所 naturalness-A。
- 過推敲シグナルの定量化（敬体/常体混入の二値カウント）（6/12, naturalness-A）。
- E-2 到達可能ライン緩和（体言止め1箇所以上で合格）（6/12, naturalness-B）。

### 定着カタカナ語 B-2 免責リスト → SSOT allowlist へ `status: done(2026-09-01 taxonomy v1.1)` `hits: 2run`
- 6/12: ルーティン・モチベーション・データドリブン等（hits 1run, 3agent）。
- 2026-09-01 **再現**: naturalness-A が「detector が フレームワーク を B-2 フラグする一方 playbook は技術文脈維持を許容＝同一語が finding にも免責にも」の矛盾を指摘。ニューラルネットワーク/アプリケーション等の定着語は暗黙免責で不整合。
- 出所: naturalness-A/B, fidelity-A（両日）
- **適用（2026-09-01）**: taxonomy B-2 に「定着カタカナ語 allowlist（ジャンル別）」を明記。技術解説での framework/deploy は borderline（残差 S3）、一般文では開く。→ Step4 適用ログ参照。

### detector 実装
- start/end 自己検証（両日 detector が実装・不一致0件で稼働）。
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF`＋`☀-➿`（6/12, detector-B）。

---

## Step4 適用ログ（v1.x へ反映済み）

| 日付 | IMP | 適用先 | run |
|---|---|---|---|
| 2026-09-01 | IMP-002 正規化式確定 | ai-tell-taxonomy.md §検出出力スキーマ（v1.1） | 001/002 |
| 2026-09-01 | IMP-001 変更率分離計上 | rewriting-playbook.md §変更率の数え方 + SKILL.md §総合判定 | 001/002 |
| 2026-09-01 | B-2 免責 allowlist | ai-tell-taxonomy.md B-2（v1.1） | 001/002 |
