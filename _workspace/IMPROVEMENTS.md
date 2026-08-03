# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-08-03（run 2026-08-03-001 技術解説, -002 公的文書）。day1 実施。

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。Sample A も 47.6% と高止まり。
- 出所: rewriter-A, rewriter-B, naturalness-B
- **[run 2026-08-03 再現・hits→2]** 001 は change_rate=0.41（挿入ほぼゼロ・削除/1:1語彙置換主導）、002 は 0.3735（difflib 内訳 equal342/replace133/delete12/insert1 の **replace 主導**・純削除 12 字）。両 run とも意味改変 edit ≒0 で 30% 警告が誤発火。両 run とも override accept で処理した。出所追加: rewriter-A(001), rewriter-B(002), naturalness-A(001), naturalness-B(002), fidelity-B(002)。
- 提案: (a) 「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を change_rate から控除。(c) 挿入率を単独併記し、del≫ins の削除主導ケースは中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。**(e) [新] diff スキーマに `edit_type: "substitution"|"deletion"|"restructure"` を持たせ type 別集計。`del≦ins かつ replace 主体`は 30% 超でも警告抑制（rewriter-A/naturalness-B 提案）。**
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done`（適用 run 2026-08-03） `hits: 2run`
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える（Sample A raw106→92.5、taxonomy 例は raw56→71.5 と不整合）。
- 出所: detector-A, detector-B
- **[run 2026-08-03 再現・hits→2]** 両 detector が独自に `100*(1-exp(-raw/k))` を採用したが **k が 45（001）と 40（002）で不一致**。まさに IMP-002 が警告する「detector ごとに数値がブレる」が実測で顕在化。
- 提案: 飽和しにくい正規化を SSOT 明記（例 `100*(1-exp(-raw/k))` か「100字あたり加重和」）。分母（input_length 依存 or 固定 max）を確定。
- **[適用 2026-08-03]** `100*(1-exp(-raw/45))`（raw=5·S1+2·S2+0.5·S3, **k=45 固定**＝taxonomy 例 raw56→71.5 を再現する値）を SSOT 正規化式として確定。`ai-tell-taxonomy.md §検出出力スキーマ` と `ai-tell-detector.md` に明記。density も「検出 span の**和集合（重複除去）**文字数 / input_length」と定義確定。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出`

### IMP-003 score_before のフィールド契約が曖昧 `status: done`（適用 run 2026-08-03） `hits: 2run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score 92.5）。レビュアーごとに数値がぶれる。
- 出所: naturalness-A
- **[run 2026-08-03 再現・hits→2]** 本 run では両 naturalness に「score_before = meta.severity_weighted_score（86.5 / 78.0）」を明示指定して回避したが、SSOT に契約が無いままだと指定漏れで再発する。
- 提案: 「score_before = 02_detection.json の meta.severity_weighted_score」と明文化。
- **[適用 2026-08-03]** `naturalness-reviewer.md §処理` と `ai-tell-taxonomy.md §検出出力スキーマ` に契約を明記。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run`
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
- 出所: detector-B, detector-A
- **[run 2026-08-03 再現・hits→2]** 001 の E-2 文末単調・B-2 カタカナ密集、002 の A-8 受動10箇所クラスタ・A-6×4・I-3×3・E-1/E-2 がいずれも scattered/document。E-2 を代表アンカー1点に潰さざるを得ず、rewriter-A も「文書レベル finding の anchor_span（根拠位置）と applied_spans[]（実施位置）が乖離する」と指摘。出所追加: detector-A/B, rewriter-A, naturalness-A/B。
- 提案: `span_type: "contiguous"|"scattered"|"document"` と scattered 用 `occurrences: [[s,e],...]` を追加。density は重複・locator を除いた実 AI クセ文字数ベースと定義。**[新] 文書レベル edit の diff は `anchor_span` と `applied_spans[]` を分離（rewriter-A）。**
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`, `japanese-style-rewriter.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。
- 出所: detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A（横断的に最多）
- **[run 2026-08-03 再現・hits→2]** 001「レバレッジされています」=B-2＋A-8、「アドバンテージとなっています」=B-2＋A-6、para5末尾に4 finding 集中。002「処理されることが可能となります」=A-8＋A-5＋A-6 の三重該当。加えて rewriter-A が「edit の逐次適用で後続 edit の before が前 edit の after を前提とする」ため diff に依存フィールドが要ると指摘。出所追加: detector-A/B, rewriter-A/B, fidelity-B。
- 提案: 「1 span = 主分類 1 finding」を基本とし、`merged_findings: [...]` 配列を許容。category_summary は「findings の category 先頭文字を集計」と注記。**[新] diff の edits に `applies_after: ["f012"]` の依存フィールド、または「edits は逐次適用順を保証する順序配列」と明文化（rewriter-A）。**
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。
- 出所: naturalness-A
- **[run 2026-08-03 再現・hits→2]** 両 naturalness が「サブエージェントはサブエージェントを spawn できず（agent 間ツールが SendMessage のみ）ai-tell-detector を実起動できなかった」と報告。SSOT 同基準・同式で in-process 再走査して代替（数値は実照合ベース）。**構造的制約**: オーケストレーター（親）が推敲後テキストに detector を実走査させ、その 02-like レポートを naturalness に渡す設計へ変更するのが現実的。出所追加: naturalness-A/B。
- 提案: `ai-tell-detector` をサブエージェントとして再呼び出しする経路を必須化（手動照合禁止）。または上記の親経由 re-detect 設計。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

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

### 定着カタカナ語 B-2 免責リスト＋技術固有語ホワイトリスト `status: ready` `hits: 2run`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B, fidelity-A, naturalness-A
- **[run 2026-08-03 再現・hits→2]** 001 で技術固有語の線引きが detector 依存でブレた（「フレームワーク」は置換・「リトリーバル」は残置）。**技術ドメイン別の固有語ホワイトリストを SSOT 化**する要望: RAG/LLM/ベクトル/エンベディング/ハルシネーション/チャンキング/リトリーバル/トークン/Transformer/API/SDK/GPU。半免責（境界語）: アーキテクチャ/システム/ドキュメント/パラメータ。出所追加: detector-A, rewriter-A, fidelity-A(001)。免責/置換表として `ai-tell-taxonomy.md B-2` にドメイン別で持たせる。

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。出所 detector-A。**[2026-08-03 再現・実装済]** 両 detector が assert を実装し mismatch 0。手順を `ai-tell-detector.md` に正式化推奨。hits→2。
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B
- サブパターンの正規表現を活用・付属語のゆらぎ（〜て/〜ては/〜ましては、〜される/〜されて/〜された）を吸収する形で SSOT 登録。現状は例文のみで regex 無し。出所 detector-B(002)

---

## 2026-08-03 新規起票（day1: 技術解説 / 公的文書）

### 【最優先・P1 taxonomy 正確性】A-8 が裸受動「〜される」を扱えない `status: ready(要 taxonomist 審査)` `hits: 1run(2agent)`
- 症状: taxonomy A-8 は *by-passive（〜によって後置）* だけを定義するが、公的文書 AI 文の主兵装は **「〜される」単独の無生物受動**（図られる/実施される/行われる/処理される/引き継がれる…002 で計10箇所）。タスク前提（「A-8 受動〜される」）と SSOT 定義が乖離。
- 出所: detector-B(002), rewriter-B(002)
- 提案: **A-8 を A-8a 裸受動（〜される）/ A-8b by-passive（〜によって）に分割**、または新項目 A-14「無生物主語の受動叙述の連鎖」[S1相当]。→ 本日 taxonomist 審査で v1.1 昇格を実施。

### 【P2 playbook】A-8 脱受動の 4 パターン決定表 `status: ready` `hits: 1run(2agent)`
- 症状: 裸受動の脱受動は「行為者が誰か」を span 外から補って初めて形が決まる。playbook A-8 は「政府によって定められた→政府が定めた」の1例のみ。
- 実例(002): 行為者=市→純能動「改善が図られる→改善する」/ 行為者=読者→可能形「処理される→処理できます」/ 連体化「使用されていた→お使いの」/ 助詞化「〜によって→〜で」。加えて rewriter-A(001): 格助詞連動（対象格 は→を＋受動接辞除去）が必須で、detector の suggested_fix は語句断片でなく最小完結節を返す規約に。
- 出所: rewriter-B(002), rewriter-A(001)
- 提案: playbook A-8 に「脱受動4パターン決定表（能動/可能/連体/自動詞）＋行為者同定を先行させる手順＋格助詞連動書き換え」を追補。

### 【P1 taxonomy】過剰敬語カテゴリ（分類 K）が存在しない `status: candidate(要 taxonomist 審査)` `hits: 1run`
- 症状: taxonomy 設計思想は「過剰な丁寧体・敬語」を 4 大重心の一つに挙げながら A〜J に敬語専用カテゴリが無い。「いただく必要がございます」×2/「お願い申し上げます」×2/「賜りますよう」等が E-2 と I-3 に分散して漏れる。
- 出所: detector-B(002)
- 提案: 新分類 K「過剰敬語・二重敬語」新設。ただし公用文の正当な定型敬語との線引きルール（下記「公用文結辞ホワイトリスト」）と対で必要。実例2件目が集まれば昇格。

### 【P2 playbook】I-3/I-4 は敬体で融合し「勧告形（〜ください/お願いします）」に収束 `status: ready` `hits: 1run(2agent)`
- 症状: 常体の「すべきだ」を敬体に機械適用すると硬すぎ・命令的。敬体では I-3「必要がある」/ I-4「求められる」が実質統合。
- 実例(002): 「必要がございます」×3 →「ご了承ください/お願いします/ご注意ください」に分散。
- 出所: detector-B(002), rewriter-B(002)
- 提案: playbook I-3/I-4 に「敬体変換テーブル: 必要がある→ください/お願いします、が求められる→していただけますようお願いします」を追補。

### 【P2 playbook】公用文の結辞・前置き敬語の「除去対象外ホワイトリスト」（減らしすぎ下限・公用文版）`status: ready` `hits: 2run`
- 既存 IMP「D 系ブログ結びは最小着地文を残す（減らしすぎ下限）」の公用文ジャンル版。I-3/A-8 を大量除去しても結辞は敬度を下げない/能動化しない。
- 実例(002): 「ご理解とご協力を賜りますよう、よろしくお願い申し上げます」「ご不明な点がございましたら」「お知らせいたします」を温存し下限を保持（良好例）。
- 出所: rewriter-B(002), naturalness-B(002)（＋既存 rewriter-B/naturalness-B のブログ版）
- 提案: playbook に「ブログ版/公用文版」2 レシピを分岐記載。判定則=結辞パラグラフ最終文は敬度を下げない。

### 【P2 naturalness】E-2 合格判定のジャンル別二段化 `status: ready` `hits: 2run`
- 既存「体言止め1箇所以上で合格」は硬い敬体・公用文に適用不能（体言止め自体が文体崩れ）。
- 実例(002): 体言止め0だが文末終止形6種以上・3連続反復なしで実質合格。
- 出所: naturalness-B(002)（＋既存 naturalness-B）
- 提案: (a) コラム/エッセイ/ブログ=体言止め・常体変奏1箇所以上。(b) 硬い敬体/公用文=「文末終止形4種以上 かつ 同一終止形3連続なし」で合格（体言止め不要）。

### 【P2 fidelity】modality に確信度／証拠性の別軸を追加 `status: ready` `hits: 2run`
- 既存「modality 強度を順序尺度化」は義務軸（要請/推奨/義務/必須）のみ。今回の f026 は確信度軸（推量 でしょう < 蓋然 だろう < 断定 です/だ）で捕捉不能。
- 実例(001): f026「と言えるでしょう→です」で推量→断定の毀損→ロールバック。
- 出所: fidelity-A(001)（＋既存 fidelity-A）
- 提案: 義務軸に加え確信度軸の順序尺度を SSOT 化。「推量→断定 は finding が『原文＝修辞的断定』を立証しない限り毀損」。既知例外則「D 系推量は保持」を auditor 判定基準へ落とし込む。#7 が全 modality を専管、#11 は命題内容の追加のみ、と責任境界を正規化。

### 【P2 fidelity チェックリスト追補】3 件（新規・要審査）`hits: 1run`
- **#7a 程度・強調副詞の degree-shift**: 「きわめて/非常に/大幅に」の削除は評価強度を下げるが #6(量化)・#7(確信度)どちらも非カバー。評価文なら要 finding 根拠。実例(001) f025「きわめて有効→有効」。出所 fidelity-A。
- **#12 hypernym→hyponym 意味狭化**: #12 は別義置換を見るが上位語→下位語の狭化を見ない。実例(001) f027「進化(evolution)→改良(improvement)」。出所 fidelity-A。
- **削除判定に (d) term-of-art グロスか を追加**: 同義グロス削除（「生成AI（ジェネレーティブAI）」）は安全だが専門術語グロス（「セマンティック」）は残余語が概念フルカバーする場合のみ boilerplate。実例(001) f011 安全 / f024 境界。出所 fidelity-A, fidelity-B。
- **#9a 受動能動化の行為者スペクトラム＋曖昧性保存**: 隠れ行為者が (a)発信主体(市)(b)受信主体(市民)(c)第三者/システム のいずれか一意なら誤帰属を毀損。原文が2者以上に読める曖昧述語は「曖昧性の保存」を pass 条件とし、一方に確定させたら PLAUSIBLE で note 必須。実例(002) f010「別々に行われていた各種手続き」。出所 fidelity-B。
- **希薄動詞の能動置換許容表**: 図る・行う・実施する・推進する は目的語別に等価能動動詞が変わる。特に「図る」は確保系(守る/確保する)と増進系(高める/向上させる)で分岐。状態名詞(安全/保護)への増進系置換は原文に「より一層」等の程度副詞が既存の場合のみ許容。実例(002) f016「保護がより一層図られる→高めます」=適格（「より一層」既存）。出所 fidelity-B。

### 【P2 分類候補・要 taxonomist 審査】detector 由来 `hits: 1run`
- **B-1 サブ「同義カタカナの二重グロス」**: 「生成AI（ジェネレーティブAI）」のように和訳＋同義カタカナ音写を括弧併記。既存 B-1(和訳＋英略語)と F-2(同義重複)の中間。実例(001) f011。出所 detector-A。
- **A-5 サブ「〜することが可能になる(のです)」**: A-5「することができる」と別語形だが同じ can 直訳。regex を分ける必要。実例(001) f006。出所 detector-A。
- **A-10 万能動詞に「与える」追加**: A-10 は shows/provides/brings/means を列挙するが give(与える) が欠落。実例(001)「大きなインパクトを与えます」。出所 detector-A。
- **A 系サブ「〜することで」手段節**: by-doing 直訳の弱シグネチャ。反復時にリズム均一化。実例(001) 残存「計算することで/参照することで」。playbook に「1つは連用中止（〜し、）へ開く」。出所 naturalness-A。

### 【P2 playbook 但し書き】I-4 主語補完と Fidelity First の衝突 `status: ready` `hits: 1run`
- 症状: playbook I-4「主語・動詞で具体化」だが、原文が意図的に行為者を伏せている場合、主語補完は原文にない主体情報の追加（鉄則1違反）。
- 実例(001): f028/f029「求められます→必要です/期待されます→期待できます」で主体不在構造を温存する最小変換に留めた（安全側）。
- 出所: rewriter-A(001)
- 提案: I-4 レシピに「原文が行為者を明示していない場合は主語補完せず modality のみ自然化」の但し書き。確信度軸尺度化と接続。
