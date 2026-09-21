# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-09-21（run 2026-09-21-001 技術記事, 2026-09-21-002 公的文書）
day-1 で day-0 の複数欠陥が別 run 再現 → hits≥2 に到達。IMP-001 / IMP-002 / IMP-006 を本日適用（status: done）。

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done` `hits: 2run` `applied: 2026-09-21-001/002`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。Sample A も 47.6% と高止まり。
- **day-1 再現**: run 001 change_rate 0.46（rewriter-A・naturalness-A）、run 002 0.35（rewriter-B・naturalness-B）。いずれも純削除主導で fidelity=pass・自然度 A。別 run 再現につき hits=2 到達 → 適用。
- 出所: rewriter-A, rewriter-B, naturalness-A, naturalness-B（2 run 横断）
- 提案: (a) 「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を change_rate から控除。(c) 挿入率を単独併記し、del≫ins の削除主導ケースは中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。
- **適用内容(2026-09-21)**: `rewriting-playbook.md §変更率の数え方` に 総/削除/挿入 の分離・純削除の控除・700字未満の減格免除・意味改変 edit 比率基準を明記。`SKILL.md §総合判定` に「変更率超過の override（fidelity=pass かつ 自然度A/B かつ del≫ins なら accept、理由を summary 明記）」を表下に明文化。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `SKILL.md §総合判定`（`japanese-style-rewriter.md` は次段で挿入率分離出力を検討）

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2run` `applied: 2026-09-21-001/002`
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える（Sample A raw106→92.5、taxonomy 例は raw56→71.5 と不整合）。
- **day-1 再現**: detector-A は飽和型 `100*raw/(raw+K), K=input_length/25`、detector-B は `raw/input_length*1000 cap100` と**別々の式を採用**し score が非互換（78.7 vs 65.9 の基準が揃わない）。別 run で式割れが再現 → hits=2 到達 → 適用。
- 出所: detector-A, detector-B（day-0/day-1 両方）
- 提案: 飽和しにくい正規化を SSOT 明記。分母（input_length 依存 or 固定 max）を確定。
- **適用内容(2026-09-21)**: `ai-tell-taxonomy.md §検出出力スキーマ` で `severity_weighted_score = min(100, round(raw/input_length*1000,1))`（1000字あたり加重密度、上限100、分母は必ず input_length）を一意確定。`raw_score`（長さ不変の加重和）と `s1_count`（等級境界 S1=0 の独立明示）を meta に追加。改善率は raw ベース、推敲前後比較は分母を原文 input_length に固定。density はユニーク被覆文字数で再定義。`ai-tell-detector.md §スコア算出` も同式へ更新。taxonomist が v1.1 で確定。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出`

### IMP-003 score_before のフィールド契約が曖昧 `status: ready(部分解消)` `hits: 1run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score 92.5）。レビュアーごとに数値がぶれる。
- 出所: naturalness-A
- 提案: 「score_before = 02_detection.json の meta.severity_weighted_score」と明文化。
- **進捗(2026-09-21)**: IMP-002 適用で改善率を raw ベースに統一・正規化式を確定したため数値ブレの主因は解消。残りは「score_before の参照元フィールド」を naturalness-reviewer.md に一文で固定する作業（次段で done 化予定）。day-1 のレビュアーは score_before に 02 の severity_weighted_score を正しく採用。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run`
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
- **day-1 再現**: detector-A が E-2/C-1 全体/I-1 密度など文書レベルパターンを代表 span にアンカーせざるを得ず reason で補足（run 001）。density のユニーク被覆定義は IMP-002 で一部前進。span scope 表現は未着手。
- 出所: detector-B, detector-A（day-0/day-1）
- 提案: `span_type: "contiguous"|"scattered"|"document"` と scattered 用 `occurrences: [[s,e],...]` を追加。density は重複・locator を除いた実 AI クセ文字数ベースと定義（density 定義は IMP-002 で適用済み）。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`。**候補欄のスキーマ改善候補に記載済み。taxonomist 審査中（v1.1 では据え置き）。次回以降適用候補。**

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。
- **day-1 再現**: run 001 detector-A が「同一 span が B-2 かつ名詞連結」等の多重ラベル未規定を、run 002 detector-B が「A-8＋A-6」「A-6＋過剰敬語」複合を報告し `secondary_categories[]` を要望。別 run 再現につき hits=2。
- 出所: detector-A, detector-B, rewriter-A/B, naturalness-A, fidelity-A（2 run 横断）
- 提案: 「1 span = 主分類 1 finding」を基本とし、`secondary_categories: [...]` 配列を許容。category_summary は「findings の category 先頭文字を集計」と注記＋サブパターン別集計を併記。
- 影響: 全 .md のスキーマ節。**候補欄のスキーマ改善候補に記載済み。taxonomist 審査中（v1.1 では据え置き）。次回以降適用候補。**

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: done` `hits: 2run` `applied: 2026-09-21-001/002`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。
- **day-1 再現（重大・実装不能が判明）**: run 001/002 の **両 naturalness-reviewer が「サブエージェント内では Task/Agent 等の spawn ツールが使えず ai-tell-detector を実呼び出しできない」と報告**（利用可能は ListAgents/SendMessage のみ）。当初提案「レビュアーが検出器を再呼び出し必須化」は**サブエージェント構造上そもそも実装不能**と判明。設計を反転させて適用。
- 出所: naturalness-A（day-0）, naturalness-A・naturalness-B（day-1、2 run 横断）
- **適用内容(2026-09-21)**: 再検出は**オーケストレーターが事前に `ai-tell-detector` を `03_rewrite.md` に実走査し `05_redetect.json` として渡す**正規経路へ変更。`naturalness-reviewer.md §入力/§処理` を「05_redetect.json を読む／無い場合のみ同一式で暫定照合し notes 明記」に改訂。`SKILL.md §並列検証` に「オーケストレーターが検証前に再検出を実行」を明記。手動照合は暫定フォールバックに限定。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md §並列検証`

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

## day-1（2026-09-21）新規起票

### 新パターン候補（taxonomy 拡張候補欄へ実例つき追記済み・taxonomist 審査中）
- **過剰謙譲「〜させていただく／させていただきます」**（公文書系・最有力）: 新カテゴリ K or I 系追加候補。rewriter の span-grounding 衝突（f007 のみ検出され L5 据え置き）の根本原因。実例2件 run 002。`hits: 1` 出所 detector-B, rewriter-B
- **「〜こととなる／こととなっております」名詞化状態叙述**: A-6 サブ拡張。実例3件 run 002。`hits: 1` 出所 detector-B
- **分裂文 cleft「〜のは〜だ/です」形式主語**（A-14 候補）: A-10 と別。短文内2回反復で S3。実例2件 run 001＋推敲後残存。`hits: 1` 出所 detector-A, naturalness-A
- **「〜できるようになります」複合 tell**（A-5＋A-6）: 実例 run 001。`hits: 1` 出所 detector-A, rewriter-A
- **依頼定型「〜いただきますよう（お願い申し上げます）」反復**: E-2 サブ拡張。実例 run 002。`hits: 1` 出所 detector-B, rewriter-B

### fidelity チェックリスト追補（day-1）
- **枠づけ名詞（framing noun）専用チェック** `status: ready` `hits: 1run`: 「Xという{アプローチ/手法/仕組み/考え方/概念}」型のカテゴリ付与名詞の削除を独立項目化。B-2（カタカナ削減）と情報欠落が衝突する典型。今回 f021/f019 で実害（ロールバック発生）。出所 fidelity-A
- **modality 強度の順序尺度を明文化** `status: ready` `hits: 2run`: 「必須＞義務＞要請＞推奨＞依頼＞任意」を定義し、何段降格までを pass とするか閾値化。今回 f006（必須→依頼=2段以上降格）でロールバック発生。day-0 でも modality 順序尺度化が起票済み → hits=2。出所 fidelity-A(day0), fidelity-B(day1)
- **「必要がございます」多義の自動判別**: 前段が因果/条件節を伴えば助言寄り、単独事実叙述なら必須寄り。playbook に追記し推敲役の依頼形化ミスを未然防止。出所 fidelity-B
- **行為者責任の所在シフト チェック**（新項目候補）: 受動→能動化で義務の主体が当館↔利用者へ反転していないか。公文書で重大毀損になりうる。出所 fidelity-B
- **modality 相殺判定基準**: 同一命題内で強化 edit×弱化 edit が相殺するケース（f025×f026）の可否ルール明文化。出所 fidelity-A
- **概念語の外延の広狭チェック**: 上位語→下位語（同義だが外延が狭まる、例 アイデンティティ→本人確認）を要注視フラグに。出所 fidelity-A
- **文体一致（敬体/常体）を正式 #14 に昇格**（鉄則3 Tone Match 対応、現13項に無い）。出所 fidelity-A

### playbook レシピ追補（day-1）
- **A-13「という」命名用法の除外規定**: 「XというY（Y=カテゴリ名詞）」は正当な命名で翻訳調でない。一律削除は Y の情報欠落リスク（今回 f021 の遠因）。命名用法は残す/別語に開く分岐をレシピに。出所 rewriter-A, fidelity-A
- **C-1 三段並列の順序性変奏**: 「まず・次に・最後に」全削除で手順の順序性が薄れる場合、1つは自然な接続へ変奏（今回「さらに」）。出所 rewriter-A
- **B-2 ドメイン別変換表の拡充**: セキュリティ/IT 頻出（ステータス・レイヤー・コンセプト・シフト・アイデンティティ・チェック）が変換表に未収載で都度判断。ジャンル別変換表を。出所 rewriter-A, detector-A
- **公的文書 I-3 依頼形テーブル** `status: ready` `hits: 1run`: 敬体公文書の「〜する必要がございます→ご〜ください/お願いいたします」変換パターンが表に無い。ただし必須性を保つ例外（f006 型）も併記。出所 rewriter-B, fidelity-B
- **E-2 敬語定型の変奏在庫リスト**: ご了承ください/お願いします/くださいますよう〜/体言止め 等、反復を崩す代替候補集を playbook に。出所 rewriter-B
- **公文書トーン保持ガイド**: どこを断定し、どこに敬語を残すかの基準（断定化しすぎると事務的に寄る）。出所 rewriter-B, naturalness-B
- **能動化に伴う最小限の格助詞調整は許容**（鉄則2「span のみ」との整合を明記）。出所 rewriter-B

### naturalness 判定の精緻化（day-1）
- **絶対残存ガードを等級に併用** `status: ready` `hits: 2run`: A/B が改善率のみで分岐し score_after 絶対閾値が無い。案「score_after<15=A可, 15-30=B, >30=再推敲」。day-0 でも同趣旨起票 → hits=2。出所 naturalness-A/B（両 day）
- **過推敲シグナルに severity(low/mid/high) を付与**し「mid以上2 or high1でC」。change_rate は IMP-001 で除外する旨を規則本文に明記。出所 naturalness-A
- **公文書トーン保持フラグ**: genre=公文書 の敬語定型（につきましては/させていただきます）は残存カウントから除外する明示ルール。出所 naturalness-B
- **E-2 到達可能ライン緩和（再掲・hits増）**: 文末変奏は文体判断を要し手術的推敲では下限。S2以下1件残置を A 許容ラインに。出所 naturalness-A(day1), naturalness-B(day0/1)
