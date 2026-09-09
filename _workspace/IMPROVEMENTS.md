# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-09-09（day1: run 2026-09-09-001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。Sample A も 47.6% と高止まり。
- **day1 再現**: 001 は削除主導（削除152:挿入50）で cr 0.276 が実質縮約、002 は語順入替・文分割で cr 0.259 が表層膨張。いずれも fidelity=pass・grade A。指標が編集の質を区別できない欠陥を再確認。
- 出所: rewriter-A, rewriter-B, naturalness-B（day0）＋ rewriter-001, rewriter-002, fidelity-002, naturalness-001, naturalness-002（day1）
- 提案: (a) 「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を change_rate から控除。(c) 挿入率を単独併記し、del≫ins の削除主導ケースは中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。(e) **net 変更率 |挿入−削除|/原文 と置換率を併記し、膨張系(挿入>削除)に厳しく縮約系に緩い二軸しきい値**（day1 rewriter 提案）。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`
- メモ: hits=2 到達。次回サイクルの Step4 適用候補（今回は IMP-002/004/005 を優先適用）。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done (applied 2026-09-09-001,002)` `hits: 2run`
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える（Sample A raw106→92.5、taxonomy 例は raw56→71.5 と不整合）。
- **day1 再現＝決定打**: 検出器2体が別式を採用（001 は raw をそのまま 90.5、002 は raw/input_length×1000 で 33.1）。同一入力に同一式が保証されない契約欠陥を実証。
- 出所: detector-A, detector-B（day0）＋ detector-001, detector-002, naturalness-001（day1）
- **適用**: taxonomy v1.1 §検出出力スキーマ ＋ ai-tell-detector.md に `severity_weighted_score = min(100, weighted_sum/input_length×1000)`（1000字あたり加重量）を確定。改善率契約（before/after 同一式）も明記。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出`

### IMP-002b（後方確認）: 旧 run（day0）の score は旧式のため v1.1 スコアと直接比較不可。回帰ではなく前方適用。以後の run は v1.1 式で統一。

### IMP-003 score_before のフィールド契約が曖昧 `status: done (applied 2026-09-09 via IMP-002 clause)` `hits: 1run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score 92.5）。レビュアーごとに数値がぶれる。
- 出所: naturalness-A
- **適用**: taxonomy v1.1 の改善率契約節に「score_before = 02_detection.json の meta.severity_weighted_score、score_after は同一式で再算出」と明文化（IMP-002 と同一編集で解消）。day1 は両 naturalness がこの契約どおり 90.5 / 33.1 を採用し数値ぶれなし。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`
- 残: naturalness-reviewer.md 本体への相互参照追記は次回（SSOT 側で確定済みのため機能上は解消）。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: done (applied 2026-09-09-001,002)` `hits: 2run`
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
- **day1 再現**: 両検出器が E-1（文長均一）を start=0/end=0 の locator で代用し density から手動除外。文書レベル finding が構造的に表現不能なことを再確認。
- 出所: detector-B, detector-A（day0）＋ detector-001, detector-002（day1）
- **適用**: taxonomy v1.1 に `span_type`（contiguous/scattered/document）・`scope`・`occurrences[]` を追加。`scope:"document"` を density 分子から除外。index 基準（改行含む生文字列）も明記。ai-tell-detector.md の文書レベルスキャン手順にも反映。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: done (applied 2026-09-09-001,002)` `hits: 2run`
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。
- **day1 再現**: 002「行われる予定となっております」= A-8+A-6、「申請していただくことが求められます」= I-4+I-1、001 f009×f021 等。1span 主分類寄せで category_summary 過小評価を再確認。
- 出所: detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A（day0）＋ detector-002, rewriter-001（day1）
- **適用**: taxonomy v1.1 に `merged_findings: [...]` 規約を追加。「1 span = 主分類 1 finding、追加分類は merged_findings に列挙、category_summary は主分類のみ集計、severity 加重は 1 回」を明文化。
- 影響: 全 .md のスキーマ節（taxonomy に確定。個別 .md への波及は必要時）
- 派生（rewriter 由来）: diff の `combined_with`（隣接 finding の一括修正）を正式化しロールバック粒度を span 単位に。`status: ready` `hits: 1`（rewriter-001, rewriter-002）

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。
- **day1 再現**: naturalness-001 が「検出器を呼ぶ実行経路がなく手動再走査で score_after を推定」と明示再指摘。
- 出所: naturalness-A（day0）＋ naturalness-001（day1）
- 提案: `ai-tell-detector` をサブエージェントとして再呼び出しする経路を必須化（手動照合禁止）。IMP-002 で score 式が確定したので、再走査結果を同一式に通せば before/after が機械整合する。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`
- メモ: hits=2 到達。次回 Step4 適用候補（オーケストレーター側で naturalness→detector 再呼び出しを配線）。

### IMP-007 ジャンル依存 severity の減衰レイヤーが無い `status: watch` `hits: 1run(3agent)`
- 症状: detector は入力ジャンル（公的文書/コラム/ブログ）を受け取らず、A-6「こととなりました」・受動「設けられております」を一律 S1 扱い。公的文書では正当な公用文体だがコラムでは AI 兆候。day1-002 では手動で S1→S2/S3 に緩和したが、その判断が reason 文中にしか残らず下流が機械的に読めない。
- 出所: detector-002, fidelity-002, naturalness-002（day1、横断）
- 提案: (a) `meta.genre`（public_document/column/blog/report...）を導入。(b) finding に `severity_raw` と `severity_adjusted` ＋ `adjust_reason` を分離。(c) modality/受動/状態叙述の許容帯をジャンル条件付きに（public は strict、blog は loose）。(d) fidelity 側も genre 条件付きトレランス＋「義務は動詞 or 残存条件節で保持」を必須ルール化。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`, `content-fidelity-auditor.md`
- メモ: 別 run（コラム/ブログ系）で再現すれば ready 昇格。

### IMP-008 modality の順序尺度化と方向ログ `status: ready` `hits: 2run`
- 症状: fidelity が modality を holistic 判定し、方向（強化/弱化）と累積ドリフトを機械捕捉できない。day1-001 で f006（可能→断定・強化）と f016（断定→可能・弱化）が同一文書内で逆方向、day1-002 で必要/求められる→ください が3件同方向に軟化。個別 minor でも累積で法的レジスタが「要件→依頼」へ移るリスク。
- 出所: fidelity-A（day0 の「modality 強度を順序尺度化」）＋ fidelity-001, fidelity-002（day1）
- 提案: `必須>義務>必要>要請>推奨>依頼` を順序符号化し、edit ごとに Δ（降格段数）と direction を算出。文書単位で Σ|Δ|・同方向降格連鎖をしきい値管理。rewriter に modality edit の `direction`＋正当化根拠を必須 annotation。
- 影響: `content-fidelity-auditor.md`, `japanese-style-rewriter.md`, diff スキーマ
- メモ: hits=2 到達。次回 Step4 適用候補。

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 001。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B
- **A-6 拡張: 「〜ている/ています」状態叙述** 現 A-6 は「〜となっている/となります」限定。「ています」形の状態化が日本語 AI 文で非常に多い。実例2件で昇格条件充足（day1）: 「課題も存在しています」「可能になります」(001) ／「なっております」「設けられております」(002)。 `hits: 1(2例)` 出所 detector-001, detector-002 → **A-6 定義拡張 or A-6b 新設を提案**
- **硬い断定コピュラ「〜ものであります／〜ものです」** 単なる「実施します」で足りる箇所を古風な断定に膨らませる公文・AI 双方の常套。実例:「実施されるものであります」(002)。 `hits: 1` 出所 detector-002
- **中黒カタカナ並列** 中黒(・)でカタカナ名詞を3語以上並べる技術文の強いクセ。B-2(語彙)でも A-11(「の」連鎖)でも正面から拾えない。実例:「認証・データストア・メッセージングといったコンポーネント」(001)。 `hits: 1` 出所 detector-001 → B系 or C系サブパターン新設検討

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

## day1 追加（2026-09-09 / run 001,002）

### playbook レシピ追補（day1）
- **E-1 短文は新規挿入でなく既存文の分割で作る**。短い定型文書（公文等）では E-1 を部分達成=許容とし、分割点が無い段落は E-1 を fidelity/ジャンル免除に。`status: ready` `hits: 2`（rewriter-001, rewriter-002, naturalness-001, naturalness-002 が横断的に「E-1 と意味不変鉄則の構造的競合」を指摘）→ 次回 Step4 候補。
- **文体アダプタ（ジャンル別 文末変奏 許可リスト）**: 技術解説で体言止め=コラム調逸脱、「でしょう」=断定の推量化（意味毀損）。ジャンル別に許容変奏を持たせ、E-2 到達ラインもジャンル別目標に。出所 rewriter-001, naturalness-001 `hits: 1`
- **行為者が原文から復元不能な受動は能動化せず接続の軟化に留める**（例「提案されており」→「提案されていて」）。捏造回避の例外則。出所 rewriter-001, fidelity-001 `hits: 1`
- **公用文コアフレーズ保護ホワイトリスト**（賜り/御礼申し上げます/お願い申し上げます/におかれましては/につきましては 等）を明文化し、能動化の行き過ぎで事務連絡調へ痩せるのを防ぐ（最小着地文の公文版）。出所 rewriter-002, naturalness-002 `hits: 1`

### fidelity チェックリスト追補（day1）
- **削除 recall テスト**（既出 day0 と再現）: 削除トークン（特に modal/scope 語「予定」「経由ニュアンス」）が推敲文に対応するか自動照合。因果接続詞（これにより/したがって）が唯一のマーカーなら保持 or 補償構造を必須。`hits: 2`（fidelity-B day0 ＋ fidelity-001, fidelity-002 day1）→ 次回 Step4 候補。
- **因果接続詞の削除は 1 finding = 1 connector に分離**（加算/因果/逆接/条件で論理機能タグ付け、因果削除に厳格 scrutiny）。出所 fidelity-001 `hits: 1`
- **rationale を `fidelity_impact` と `style_rationale` に分離**（監査官と naturalness の関心分離。現状 diff が文体根拠を fidelity edit に混在）。出所 fidelity-001 `hits: 1`
- **span-level edit と document-level edit でスキーマ分離**（前者テキスト差分検証、後者構造検証。f025/f027/f028 が before/after にメタ記述を格納し span-grounded 監査が機能しない）。出所 fidelity-001 `hits: 1`。IMP-004 の適用と整合させて次段で。
- **削除 char 数の finding 別内訳を diff に含める**（削除主導 edit がボイラープレートか情報かを監査官が確認可能に）。出所 fidelity-001 `hits: 1`

### naturalness 判定の精緻化（day1）
- **grade 表に score_after 絶対値上限を併置**（改善率だけで A に届くのを抑える二重ガード。短文で改善率が振れやすい）。出所 naturalness-001 `hits: 1`（day0 の「絶対残存数ガード」と同系）
- **密度系残存 S3（A-9「ため」等）は共起環境の解消度で重み付け**し、孤立残存を grade 減点から外す。出所 naturalness-002 `hits: 1`
- **過推敲の定量化**（口語度スコア・敬体一貫率・意味密度・文末変奏インデックスを数値化しジャンル別上限で自動フラグ）。`hits: 2`（naturalness-A day0 ＋ naturalness-001, naturalness-002 day1）→ 次回 Step4 候補。

### detector 実装（day1）
- **I-3/I-4 等の活用形・敬体変異を正規表現化**（「必要がある」だけでなく「必要がございます」「必要があります」「求められます」を捕捉。素朴な文字列一致では漏れる）。出所 detector-002 `hits: 1`
- **B-2 exempt 判定語を finding に残す**（`exempt: true` 行 or meta の除外語リスト。下流が「なぜ FaaS/サーバーレスを触らないか」を追え、誤修正を防ぐ）。出所 detector-001 `hits: 1`
