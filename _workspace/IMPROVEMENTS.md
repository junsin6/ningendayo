# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-07-01（run 001 WebAssembly技術解説, 002 図書館公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done(2026-07-01-001/002)` `hits: 2run(6agent)`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。Sample A も 47.6% と高止まり。
- **再現(2026-07-01)**: 001 change_rate 45.9%（del264≫ins121, char_delta -143=実質-17%）、002 40.6%（del188≫ins78, char_delta -110）。**両 run とも override accept が発火**し、指標が構造的欠陥であることを再実証。rewriter-A/B が「圧縮率であって改変率ではない」と独立に自己申告。
- 出所: rewriter-A, rewriter-B, naturalness-B（+2026-07-01: rewriter-A, rewriter-B, fidelity-B）
- 提案: (a) 「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を change_rate から控除。(c) 挿入率を単独併記し、del≫ins の削除主導ケースは中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。
- **適用(2026-07-01)**: `rewriting-playbook.md §変更率の数え方` に `net_change_rate=|char_delta|/orig` と `weighted_change_rate=(ins+del*0.5)/orig` を定義、中断判定を net/weighted 基準へ移行。`SKILL.md §総合判定` に「del主導かつ fidelity=pass かつ 自然度A/B は change_rate 単独で hold にしない」を明文化。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done(2026-07-01, v1.1)` `hits: 2run(4agent)`
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える（Sample A raw106→92.5、taxonomy 例は raw56→71.5 と不整合）。
- **再現(2026-07-01)**: 001 は raw92 が飽和し **score=100.0 に完全張り付き**（detector-A の式 `raw/(0.06×len)` で 183%超）。002 は detector-B が `raw/(len/50×5)` の密度連動式を採用し 74.2 だが「短文書ほどスコアが跳ねる／同raw でも文書長でスコアが変わり比較不能」と指摘。**検出器ごとに式が違い数値が非可換**であることを実証。改善率(等級判定の70%+)が測れない致命傷。
- 出所: detector-A, detector-B（+2026-07-01: detector-A, detector-B）
- 提案: 飽和しにくい正規化を SSOT 明記（例 `100*(1-exp(-raw/k))` か「100字あたり加重和」）。分母（input_length 依存 or 固定 max）を確定。
- **適用(2026-07-01)**: `ai-tell-taxonomy.md §検出出力スキーマ` に正規化式 `score = round(100*(1-exp(-raw_per_1000/K)), 1)`（raw_per_1000 = 加重和×1000/input_length, K=40）を SSOT 確定。文書長非依存かつ非飽和。`ai-tell-detector.md §スコア算出` に手順を明記。taxonomist 審査で v1.0→v1.1 昇格。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出`

### IMP-003 score_before のフィールド契約が曖昧 `status: ready` `hits: 1run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score 92.5）。レビュアーごとに数値がぶれる。
- 出所: naturalness-A
- 提案: 「score_before = 02_detection.json の meta.severity_weighted_score」と明文化。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run(4agent)`
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
- **再現(2026-07-01)**: detector-A(001) が E-1/E-2 を density 分子から除外して回避、detector-B(002) は E-2 が字句 span を丸ごと内包し「単純合計 density 0.36 vs 重複排除 0.247」の二値ブレを実証。両者とも `scope:"span"|"document"` フィールドと density 定義の明確化を独立提案。
- 出所: detector-B, detector-A（+2026-07-01: detector-A, detector-B）
- 提案: `span_type: "contiguous"|"scattered"|"document"`（または `scope`）と scattered 用 `occurrences: [[s,e],...]` を追加。density は「文書レベル span を除外した字句 span の重複排除カバレッジ」と定義。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run(9agent)`
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。
- **再現(2026-07-01)**: detector-B(002) が「開始されることとなりました＝A-6+A-8+I-1 が同一 span」で二重計上せざるを得ず detected_count/density を歪めると指摘。rewriter-A は `span_group_id`、rewriter-B は `resolves:[f009,f010]`（1物理編集が複数 finding を解決）、fidelity-B は `rollback_findings:[...]` 配列を各々独立に提案。**002 の f009/f010 は実際に同一 span で、ロールバック指示が finding_id 配列でないと曖昧になる問題が顕在化**。
- 出所: detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A（+2026-07-01: detector-B, rewriter-A, rewriter-B, fidelity-B）
- 提案: 「1 span = 主分類 1 finding」を基本とし、`merged_findings: [...]` 配列を許容。edit 側は `resolves:[finding_id...]`、violation 側は `rollback_findings:[finding_id...]` を持たせる。category_summary は「findings の category 先頭文字を集計」と注記。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 1run`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。
- 出所: naturalness-A
- **2026-07-01 進展**: 両レビュアーとも `ai-tell-detector` を実サブエージェント呼び出しで再走査でき、経路自体は機能した（score_after が推定でなく実測に）。ただし下記 IMP-007 の新規欠陥が露見。
- 提案: `ai-tell-detector` をサブエージェントとして再呼び出しする経路を必須化（手動照合禁止）。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

### IMP-007 naturalness-reviewer が 05 JSON を書かずチャット返答で終える `status: ready` `hits: 1run(2agent)`
- 症状: 2026-07-01 の naturalness-A/B は検出器再走査後、完全な等級A判定・residual JSON を**最終メッセージにインラインで出力したが `05_naturalness_review.json` を Write しなかった**。オーケストレーターが報告文から手動で materialize する必要があった（両 run で発生）。fidelity-A/B・detector・rewriter は全員ファイル出力しており、naturalness だけ副作用（ファイル書き込み）を省略する傾向。
- 出所: naturalness-A, naturalness-B（2026-07-01）
- 提案: `naturalness-reviewer.md` の手順末尾に「**必ず Write ツールで 05_naturalness_review.json を保存してから返答する**。返答はファイルの要約のみ」を明記。サブエージェント再走査を挟むと最終出力ステップを飛ばしやすいので、順序を「①再走査 → ②JSON確定 → ③Write → ④要約返答」と固定。
- 影響: `naturalness-reviewer.md §出力`, `SKILL.md §4`

### IMP-008 公的文書ジャンルの「義務→依頼形」変換レシピが playbook に欠落 `status: ready` `hits: 1run(2agent)`
- 症状: playbook の I-3/I-4/D 処方は常体前提の変換先しか示さず、public × desu_masu での変換先が無い。002 で「登録を行っていただく必要があります」→ 高圧な「登録すべきです」は不適、正解は依頼形「登録をお願いいたします」だが処方に無く rewriter の裁量に依存（再現性なし）。D-1 結び定型（幸いに存じます／お願い申し上げます）も公的文書では一部が正当なフォーマリティで全削除不可、残置下限が未定義。
- 出所: rewriter-B, fidelity-B（2026-07-01）
- 提案: playbook に「ジャンル×文体マトリクス」を追加。`public × desu_masu` 列に「義務(必要がある/しなければ)→依頼形(お願いいたします)」「無行為者受動の規定文→丁寧な断定(です/ます)」「結び儀礼定型は1つまで残置」の許容レンジを明記。
- 影響: `rewriting-playbook.md`, `japanese-style-rewriter.md`

### IMP-009 無行為者受動への「主体注入」が最頻出 fidelity 毀損だがチェック項目が無い `status: ready` `hits: 1run(2agent)`
- 症状: 002 で「返却処理がなされる仕組みとなっております」→「**システムが**自動的に返却処理を行います」と、原文が意図的にぼかす主体を推敲が確定注入（item9 行為者＋item11 情報追加にまたがり判定漏れしやすい）。実際に verdict=fail(S2)→ロールバックした。公的文書で処理主体の明示は手続き解釈上の含意を持つため毀損。
- 出所: fidelity-B, rewriter-B（2026-07-01。rewriter 側も「補完の可否が未規定」と自己申告）
- 提案: fidelity チェックリストに専用項目「**無行為者性の保存**: 原文が主体を明示しない受動・自動表現に、新たな行為主体を特定・断定していないか」を追加。playbook A-8 に「行為者が原文の論理から一意に決まる場合のみ補完可」但し書き。
- 影響: `content-fidelity-auditor.md §チェックリスト`, `rewriting-playbook.md §A-8`

### IMP-010 スコア式/重み変更時にスキーマの worked-example を再計算する手順が無い `status: ready` `hits: 1run(taxonomist)`
- 症状: 2026-07-01 の v1.1 でスコア式を変えたが、§検出出力スキーマの数値例（旧 71.5）を更新し忘れており taxonomist が検算で不整合を発見・訂正（71.7 へ）。検出器はこの worked example に較正するため、放置は較正誤りの温床。あわせて凡例の hits 定義（「異なる run 数」vs「同一 run 内複数実例＝密度証拠」）が読み手依存、S1/S2 割当に「人間ベースライン一言」が任意になっている点も指摘。
- 出所: japanese-ai-tell-taxonomist（2026-07-01 審査）
- 提案: taxonomist 昇格ワークフローに「式・重みを変えたらスキーマ数値例を必ず再計算し一致確認」を必須手順化。凡例に hits の二区分を明記。各サブパターンの `注意（誤検出回避）` 行の有無を審査必須項目に。
- 影響: `japanese-ai-tell-taxonomist.md`, `ai-tell-taxonomy.md §凡例/スキーマ`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 001(06-12)。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。実例追加(2026-07-01-001)「見ていきましょう／見ておきましょう」の guided-tour 反復。 `hits: 2` 出所 detector-B(06-12), detector-A(07-01) — **昇格済 `status: done(v1.1, 2026-07-01)`**。taxonomy C セクションに S2・反復条件(同一文書2回以上)付きで追加。誤検出回避のため単独出現は非S1。
- **A-14 過剰敬語の均一適用 ★日本語固有**（新規） 最上級敬語を全箇所へ機械的に均一適用。実例(2026-07-01-002)「おきましては」「〜していただく必要がございます」「幸いに存じます」「お願い申し上げます」が一文書に密集。人間の実務公文書はどれか一つに抑える。公的文書AI文の決定的シグネチャ。 `hits: 1` 出所 detector-B(07-01)
- **A-6 拡張「〜こととなりました／運びとなりました」**（既存 A-6 のシグネチャ例追加提案） 〈こと＋となる＋敬語〉複合。実例(2026-07-01-002)「開始されることとなりました」。A-6 と I-1 の中間で分類が揺れた。 `hits: 1` 出所 detector-B(07-01)
- **行政テンプレ名詞化「〜を図る／を実施する」** 〈抽象名詞＋を図る〉のサ変名詞化。実例(2026-07-01-002)「利便性の向上を図るため」「拡充が図られていく」の2件。F-4/A-9 で部分的に拾えるが〈お役所定型×AI〉の複合。 `hits: 1` 出所 detector-B(07-01)
- **「〜といった＋列挙」such-as 例示構文**（A-13 近縁の列挙専用） 英語 such as / like の直訳例示。実例(2026-07-01-001)「C++やRustといった言語」「動画編集やゲーム、画像処理といった」の2件（同一 run 内2回）。 `hits: 1` 出所 detector-A(07-01)
- **技術ハイプ動詞「真価を発揮する／本領を発揮する」**（D-5×D-4 交差） 技術を主語に擬人化ハイプ。実例(2026-07-01-001)「その真価を発揮します」。技術解説AI文の頻出。 `hits: 1` 出所 detector-A(07-01)
- **タイトル公式「〜とは何か——徹底解説／次世代の〜」**（C 系 タイトル定型・既存 C-9 導入誘導とは別物） B-1括弧併記＋J-3ダッシュ＋D-4「徹底/次世代」が凝縮。実例(2026-07-01-001)「WebAssembly（Wasm）とは何か——次世代のWeb技術を徹底解説」。 `hits: 1` 出所 detector-A(07-01)
- **「ますます〜していく」漸進誇張**（D-4 下位） 将来の拡大を無根拠に強調する結び常套。実例(2026-07-01-001)「ますます拡大していく」。 `hits: 1` 出所 detector-A(07-01)

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019（並列→基盤の序列混入）はこの項が無く #5/#11 へ漏れ込んだ。`status: ready` `hits: 1` 出所 fidelity-A
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。`status: ready` `hits: 1` 出所 fidelity-B
- 「情報を含む削除 vs ボイラープレート削除」二分判定: 削除 span に (a)数値/固有名詞/日付 (b)条件/因果節 (c)固有の例示 を含めば情報欠落、挨拶/CTA/装飾/自己言及のみならボイラープレート。出所 fidelity-B
- #5論理関係 と #11情報追加 の責任境界を一意化（主因項目を 1 つに正規化）。出所 fidelity-A
- modality 強度を順序尺度化（要請/推奨/義務/必須）。出所 fidelity-A
- **#4b 主張タイプの保存**（claim-type の同一性）: 同じ肯定でも「重要性/有益性/必要性/優位性」の別が横滑りしていないか。実例(2026-07-01-001) f020「非常に重要」→「大きく役立つ(有益性＋推量)」。極性/強度/量化のどれでも捕捉できず項7へ漏れた。`status: ready` `hits: 1` 出所 fidelity-A(07-01)
- **verdict 三値化 `pass / pass_with_notes / fail`**: 「毀損ではないが要注視(S3 caution)」の受け皿。fidelity-A は独自に cautions[] を増設した（01も3件記録）。スキーマ標準化が必要。`status: ready` `hits: 1` 出所 fidelity-A(07-01)
- **modality 弱化サブ判定**: 「必要がある→依頼(お願いします)」で義務性が弱まり利用者が任意と誤解するリスク（公的文書で最大の毀損類型）。item7 は強化例のみで弱化を問わない。出所 fidelity-B(07-01)
- **procedural_requirements チェック（ジャンル=公的文書で有効化）**: who/when/where/what/condition の各保存を boolean 明示し削除 span 審査の網羅性を担保。出所 fidelity-B(07-01)
- **rollback_findings 配列の必須化**: violations の差し戻し指示を自由文字列でなく finding_id 配列に（→ IMP-005 と統合）。出所 fidelity-B(07-01)

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

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 2run(4agent)`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B, fidelity-A, naturalness-A
- **再現(2026-07-01)**: naturalness-B(002) が「スマートフォン／タブレット端末／リクエスト／カウンター／ペナルティ／タイトル／システム」を Do-NOT 相当の業界標準・外来定着語と判定（濫用ではない）。技術系(001)では WebAssembly/JavaScript/C++/Rust/ブラウザ/コンパイル/モジュール/ランタイム が同様に保存対象。**免責リストをジャンル別に整備すべき**（技術定着語 vs 生活外来語）。出所 naturalness-B(07-01), rewriter-A(07-01)

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。出所 detector-A
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B
