# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-07-21（run 001 技術解説, 002 公的文書 / day-1）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。
- 再現（2026-07-21）: rewriter-001 は高密度入力（density 0.319・S1×12）で S1 を全除去しただけで change_rate 0.29 に到達（「良い推敲ほど閾値に触れる」逆相関）。**round2 の A-10 修正は 6→3 字の単一置換で情報増減ゼロなのに sum-metric が 0.30 の警告線に到達**。rewriter-002 は insert 44 / delete 145 の削除偏重で 0.278（健全な過剰敬語削除が中断線へ近づく）。編集距離ベースなら 001 は ≈0.20 で乖離。
- 出所: rewriter-A/B(day0), rewriter-001/002/001round2(day1)
- 提案: (a) 「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を change_rate から控除。(c) insert/delete を二軸併記し del≫ins の削除主導ケースは中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。(e) sum-metric ではなく区間マージ後の文字レベル LCS（編集距離）で算出、と明文化。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`
- **→ 本 run で適用（Step4, applied: 2026-07-21-001/002）**

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2run(4agent)` `applied: 2026-07-21`
- 症状: 正規化式が SSOT に無く、検出器・レビュアーが run ごとに別基準を即興。detector-001 は cap100 の生和で 92.0、detector-002 は密度基準で 66.7、reviewer 群は `raw/input_length*1000` を採用。**同一ハーネス内で score のスケールが不一致 → run 間・推敲前後の「改善率」判定が成立しない**。
- 検証: 提案式 `min(100, raw/input_length*1000)` は taxonomy の既存スキーマ例（input_length 1820）と後方互換。taxonomist 監査により例を **71.4**（raw≈130）へ是正（旧 71.5 は式導入前の概数で 0.5 刻み加重和では厳密に生成不能）。
- 出所: detector-A/B(day0), detector-001/002・naturalness-001/002(day1)
- 適用内容: `ai-tell-taxonomy.md §検出出力スキーマ` に `severity_weighted_score = min(100, round(raw / input_length * 1000, 1))` を明記。`ai-tell-detector.md §スコア算出` と `naturalness-reviewer.md` に同式と「score_before = 02_detection.json の meta.severity_weighted_score」（IMP-003 併合）を追記。

### IMP-003 score_before のフィールド契約が曖昧 `status: done` `hits: 2run` `applied: 2026-07-21`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。
- 再現（2026-07-21）: 明示指示により両レビュアーが meta.severity_weighted_score を採用し数値が安定（001: 92.0, 002: 66.7）。契約を明文化すれば指示なしでも再現可能。
- 適用: IMP-002 と同じ編集内で「score_before = 02_detection.json の meta.severity_weighted_score」を SSOT / naturalness-reviewer.md に明記。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: done` `hits: 2run(4agent)` `applied: 2026-07-21`
- 症状: E-1/E-2 文末単調・受動連鎖・絵文字散在は文書全体現象。単一 start/end しか持てず、便宜的に `start:0,end:766` とすると density が ≈1.0 に暴発する。detector は union で逃げたが式は「総文字数」としか規定せず、reviewer のロールバック照合も不安定。
- 出所: detector-A/B(day0), detector-001/002・rewriter-001/002(day1)
- 適用内容: `ai-tell-taxonomy.md §スキーマ` に `span_type: "contiguous"|"scattered"|"document"` と scattered 用 `occurrences: [[s,e],...]` を追加。`ai_tell_density` を「検出 span の **union** 文字数 / 全体（重複区間は二重計上せず、`span_type:"document"` は分子から除外）」と再定義。`ai-tell-detector.md` に反映。

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run` 
- 症状: 1 span が複数カテゴリに該当（I-4＋B-2＋I-1／A-10＋A-5＋A-1＋B-2 等）。edits/findings 1:1 前提で category_summary が実態を過小評価。**重複区間で推敲役が浅い方（A-5冗長）だけ処理し深層の S1（A-10骨格）を残す「半解け」**が発生（001 round1 の A-10 残存）。
- 再現（2026-07-21）: detector-001, rewriter-001（severity降順処理の必要性）, naturalness-001（半解けの実例）。
- 出所: detector-A・rewriter-A/B・naturalness-A・fidelity-A(day0), detector-001・rewriter-001・naturalness-001(day1)
- 提案: 「1 span = 主分類 1 finding」を基本とし `merged_findings: [...]` を許容。density は union（IMP-004 で一部適用済）。playbook に「重複 span は severity 降順で処理し S1 骨格の除去を A-5 冗長解消より優先」を追記。
- 影響: 全 .md のスキーマ節, `rewriting-playbook.md`

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合になりがち。
- 再現（2026-07-21）: 明示指示で両レビュアーが `ai-tell-detector` を実呼び出しし score_after を実測（001 round2: 0.0 / 002: 1.72）。**ただし子検出器を起動したレビュアーが2回とも「子の完了待ち」で途中終了し、親からの再開指示が必要だった** — 経路は有効だが、非同期子エージェントの待機ハンドリングが脆い。
- 出所: naturalness-A(day0), naturalness-001/002(day1)
- 提案: `ai-tell-detector` 再呼び出しを必須化（手動照合禁止）。加えて「子検出器は同期実行 or 親が子完了を待って集計する」手順を naturalness-reviewer.md に明記。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **K 系: 過剰敬語（敬語累積）** `hits: 1(day1, 3agent)` — 二重敬語・使役謙譲濫用（させていただいております）・冗長謙譲（賜りますよう〜申し上げます）・継続敬語。taxonomy の設計思想は「過剰な丁寧体・敬語」を日本語固有4大重心の一つに挙げるのに A〜J に受け皿が無く、公的文書 run で支配的 tell（f015 等）を **I-3 へ暫定分類せざるを得なかった**。実例: 002。専用カテゴリ **K. 過剰敬語** 新設を提案。出所 detector-002, rewriter-002, naturalness-002。→ 拡張候補欄へ登録済み（taxonomist）。
- **予測・推量マーカーの受動誤認** `hits: 1(day1, 2agent)` — 「〜が予想される／見込まれる／考えられる／とされる」は受動形をとる epistemic hedge で、A-8（非人称受動）の能動化対象ではない。断定化すると推量 modality が消え原意超過（002 f004+f009 の fidelity 毀損）。playbook に「これらは A-8 能動化から除外し敬体化のみ」除外則。出所 rewriter-002, fidelity-002。
- **C 系: redundant restatement**（叙述 まず/次に/最後に と箇条書きが同内容を二重記載）`hits: 1(day0)` 出所 detector-A。
- **D-7 ブログ結び呼びかけ公式**「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」`hits: 1(day0)` 出所 detector-B。
- **C-9 導入誘導定型**「さっそく見ていきましょう」式 `hits: 1(day0)` 出所 detector-B。
- **A-5 変種「〜ことが可能だ／可能です」** `hits: 1(day1)` — A-5 の例が「することができる」のみで「ことが可能」が明記されず分類が迷う（002 f006/001 f006）。A-5 に変種例を追加。出所 detector-001。
- **手段の「〜によって」** `hits: 1(day1, 2occ)` — A-8 は by-passive 限定、A-3 は「を通じて」限定で、手段の instrumental「によって」（活用することによって／選定によって）に受け皿が無い。A-3 か A-8 にサブ項目化。出所 detector-001。
- **A-6/I-3 境界（必要となる）** `hits: 1(day1)` — 「必要となります」は A-6(状態叙述) と I-3(要請) の両方に該当。判定規則（動詞が「なる」なら A-6 優先 等）を SSOT 明文化。出所 detector-002。

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** `status: ready` `hits: 1(day0)` 出所 fidelity-A。
- **item 7 modality の方向性ルール＋許可軸** `status: ready` `hits: 2run` — 現行 item 7 は断定/推量/義務の軸のみで **許可（permission）軸が無い**。「認められる（許可・要承認）↔ できる（可能）↔ 求められる（義務）」の相互置換を検査対象に追加。かつ「可能形→断定は可能性が意味的に負荷を担う場合のみ毀損／根拠節を伴う冗長除去は pass」の下位規則を明記。day0 の「modality 強度を順序尺度化」を再現・具体化。出所 fidelity-A(day0), fidelity-001/002・rewriter-001/002(day1)。
- **item 11 に格助詞・とりたて助詞（も/こそ/さえ/だけ）の増減チェック** `hits: 1(day1)` — 「場合がございます→場合もございます」の 1 字追加で「〜も(also)」の追加含意が発生（002 f006）。語彙 span 単位だと網に掛からない。出所 fidelity-002。
- **item 12 に狭義化/広義化（hyponym 置換）サブチェック** `hits: 1(day1)` — 「リソース→手間」「コストの最適化→コストを抑える」は別義でなく広義→狭義で一般性が失われるが現行 item 12（別義置換のみ）が素通し。出所 fidelity-001。
- **削除専用サブチェック（deletion-recall test）** `status: ready` `hits: 1(day0)` 出所 fidelity-B。
- 「情報を含む削除 vs ボイラープレート削除」二分判定。出所 fidelity-B(day0)。
- **敬語簡略化 edit は item 10（欠落）より先に item 7（modality）を疑う**ヒューリスティック — 過剰敬語削除の主リスクは情報欠落でなく modality 変質に集中（day1 で実証）。出所 fidelity-002。

### playbook レシピ追補
- **重複 span は severity 降順処理**（A-10 を含む区間は A-5 短縮で満足せず述語を自動詞化する手術まで踏み込む）`hits: 1(day1)`。A-10 解法パターン「主語は温存、目的語＋万能動詞を自動詞述語へ」（発揮します→役立ちます）。出所 rewriter-001, naturalness-001。
- **公用文ジャンルの丁重さ下限**（ございます等を全滅させず冒頭挨拶・結び依頼・丁寧命令を温存）`hits: 1(day1)` 出所 rewriter-002, naturalness-002。
- **C-5 絵文字削除後の文末/区切り吸収ルール** 出所 rewriter-B(day0)。
- **D 系結びは削除一択でなく「最小着地文を残す」** 出所 rewriter-B, naturalness-B(day0)。
- **機能が必要な接続詞（しかしながら）は削除でなく変奏** 出所 rewriter-A(day0)。
- **原文が元から推量の D 系は推量を保持** 出所 rewriter-A(day0)。
- **見出し行の文体扱い**（表題の体言止め化を E-2 変奏と両立させるが敬体判定・混在誤検出の対象外にする明示ルール）`hits: 1(day1)` 出所 rewriter-001, fidelity-001。

### naturalness 判定の精緻化
- **等級ルールの conditional-A サブルール** `hits: 1(day1)` — 「S1=1 かつ 改善≥85% かつ 過推敲=0」は該当 span のみ限定 round2 とし、フル再実行の過推敲リスクを避ける。001 round1（1 span を除けば完全 A）で顕在化。出所 naturalness-001。
- 過推敲シグナルの定量化（敬体/常体混入は文末形態の二値カウント）出所 naturalness-A(day0)。
- クラスタ系 finding（B-2 密集・C-1 列挙）のクラスタ崩壊時 severity 降格。出所 naturalness-A(day0)。
- E-2 文末単調の到達可能ライン緩和（体言止め1箇所以上で合格）出所 naturalness-B(day0)。
- 絶対残存数ガードを grade 表に組込み（S1 1件でも C 以下）出所 naturalness-A/B(day0)。
- register 標準語彙のジャンル別サプレッション（公用文「ございます」等は文末変奏回復時に S3 減点外）`hits: 1(day1)` 出所 naturalness-002。

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 2run`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定（day0）。
- 再現（day1）: 技術解説で維持すべき業界標準語（サーバーレス/レイテンシ/コールドスタート等）と変換対象（メリット/タスク/リソース）の線引きが検出器裁量頼み。**維持すべき技術用語のホワイトリスト（分野タグ）を references 化**しないと run 間で B-2 ラインがぶれる。加えて同語異義（「リソース」＝手間 vs 技術資源）に対し finding へ `gloss`＋`keep_spans` を持たせ推敲役の誤変換を防ぐ。出所 naturalness-B・fidelity-A・naturalness-A(day0), detector-001・rewriter-001(day1)。

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert）出所 detector-A(day0)。
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿` 出所 detector-B(day0)。
