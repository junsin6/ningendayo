# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。
`hits` = これまでに指摘した run 数（**別 run での再現のみ +1**。同一 run 内の複数エージェント指摘は 1 run 扱い）。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。

最終更新: 2026-09-19（run 001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除/等価置換」と「過推敲」を区別できない `status: done` `hits: 2run` `applied: 2026-09-19-001/002`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除、**および B-2 カタカナ語→和語の等価置換**で機械的に膨張。
  - day0: Sample B 54.6% で hold 誤発火（fidelity=pass/自然度 A）。
  - 2026-09-19: run 001 は B-2 和語化 12 件（≈101字＝全変更の1/3）で change_rate 0.372、run 002 は高密度クセ解体で 0.328。いずれも純削除主導ではなく等価置換/構文解体で、fidelity 無毀損・情報欠落ゼロ。両 run とも 30% 警告帯だが真の過推敲ではない。
- 出所: rewriter-A/B, naturalness-A/B, fidelity-B（day0 + 001/002 で横断再現）
- 提案（適用済み）: playbook §変更率の数え方 を「純削除率 / 等価置換率 / 意味改変率」の 3 分割に改訂。50% 中断は**意味改変 edit 比率**基準に置換し、等価置換（B-2 和語化等）と装飾/常套句の純削除は中断対象から控除。diff meta に `change_rate_note`（内訳）と `polish_type: dismantling|over_polish` を必須化。
- 残提案（未適用）: warning 閾値を density 連動（期待変更率 ≒ density×係数）にする案は IMP-008 と併せて次回検討。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`(done), `japanese-style-rewriter.md`(done), `SKILL.md §総合判定`(done)

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2run` `applied: 2026-09-19-001/002`
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える。detector 間・run 間で score が非互換。
  - 2026-09-19: detector-001 は raw=117 を独自に `100*(1-exp(-raw/80))`=76.8、detector-002 は「文数×5 を分母」で 76.4 と、**別方式なのに近い値**に。式が未定義ゆえの偶然一致で、再現性が担保されていないことを実証。
- 出所: detector-A/B（day0）, detector-001/002, naturalness-001（2026-09-19）
- 提案（適用済み）: **飽和正規化 `score = round(100*(1-exp(-raw/K)),1)`, K=80 固定**を taxonomy SSOT に明記。分母を入力長非依存に固定。`meta.normalization`（例 `"sat_exp_k80"`）を必須フィールド化。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`(done, taxonomist), `ai-tell-detector.md §スコア算出`(done)

### IMP-003 score_before のフィールド契約が曖昧 `status: done` `hits: 1run` `applied: 2026-09-19`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。
- 提案（適用済み）: 「score_before = 02_detection.json の meta.severity_weighted_score」と naturalness-reviewer.md に明記。運用でも本 run から両レビュアーが同値を採用。
- 影響: `naturalness-reviewer.md`(done)

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: done` `hits: 2run` `applied: 2026-09-19-001/002`
- 症状: 絵文字・文末単調（E-2）・まず…最後に は分散/文書全体パターン。単一 start/end では広域 locator にせざるを得ず ai_tell_density が過大化。推敲役はどの文を変奏するか裁量になり「検出のない区間は触らない」原則と衝突。
  - 2026-09-19: 両 detector が E-2 を代表 span 1 点に紐付け reason で「全16文中13文」等と補足。rewriter-001/002・naturalness-001 が「文書レベル finding の手術対象が選べない」を再指摘。
- 出所: detector-A/B（day0）, detector-001/002, rewriter-001/002, naturalness-001
- 提案（適用済み）: `span_type: "contiguous"|"scattered"|"document"`（既定 contiguous）＋ scattered 用 `occurrences: [[s,e],...]` を追加。density は重複・locator を除いた実 AI クセ文字数ベースと定義。
- 影響: `ai-tell-taxonomy.md §スキーマ`(done, taxonomist), `ai-tell-detector.md`(done)

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリに該当（I-4＋B-2＋I-1、A-10＋D-1、D-4＋B-2、A-6＋A-8 等）。edits/findings が 1:1 前提で category_summary・change_rate カウントが実態とずれる。
  - 2026-09-19: rewriter-001「f011(A-10)＋f027(D-1) が同一 span、edits_count 36 と実操作 33 がずれる」、detector-001「secondary_categories が欲しい」、detector-002「composite タグ」、fidelity-001「same-span 統合で edit 単位ロールバックが困難」。
- 出所: detector-A(day0), rewriter-A/B, fidelity-A, naturalness-A, detector-001/002, rewriter-001, fidelity-001
- 提案: 「1 span = 主分類 1 finding」を基本とし `secondary_categories: [...]`（または `overlaps: ["f0xx"]` / `composite: [...]`）配列を許容。diff に span 単位の最終 before/after 統合ビューを持たせロールバック単位を span に正規化。category_summary は「主分類の先頭文字を集計」と注記。
- 影響: 全 .md のスキーマ節（次回 Step4 候補）

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: mitigated` `hits: 1run`
- 症状: 仕様は「検出器を同基準で再走査」だが day0 は手動照合で推定値。
- 対応: 2026-09-19 は両 naturalness-reviewer に「taxonomy 基準で再走査（手動照合禁止）」を明示し実行。運用で緩和。恒久化には naturalness-reviewer.md への「ai-tell-detector 再呼び出し経路」明記が残課題。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

### IMP-008 ジャンル別 protected-pattern / 許容カタカナ語リストが無い `status: ready` `hits: 2run`
- 症状: 「触ってはいけない/開いてよい」の線引きがジャンル依存かつ detector/rewriter/reviewer でアドホック判断。
  - run 001（技術）: 「エンベディング/パイプライン/インデックス/ハルシネーション/データセット」は維持、「データストア/コンテキスト/レスポンス」は和語化——境界が主観的。
  - run 002（公的文書）: 「御礼申し上げます/賜りますよう/におかれましては/電話による受付（連体のによる）」は AI クセ形状に一致するが**触ってはいけない保護 span**。毎回アドホックに severity 減衰。
- 出所: detector-001, rewriter-001, fidelity-001, detector-002, rewriter-002, naturalness-002
- 提案: `references/` に (a) ドメイン別カタカナ許容語リスト（技術記事は英略語許容度↑）、(b) ジャンル別 protected-pattern リスト（公的文書の定型敬語）を新設。detector が初期段階で severity 減衰、reviewer が残存カウントから自動除外。finding に `genre_adjustment` / `baseline_allowed`（許容回数）フィールド追加も検討。
- 影響: `references/`（新規ファイル）, `ai-tell-detector.md`, `naturalness-reviewer.md`, `ai-tell-taxonomy.md §B-2`

### IMP-009 modality 強度が順序尺度化されておらず義務度の毀損を機械判定できない `status: ready` `hits: 2run`
- 症状: 「必要がある→ください/すべき」等の書き換えで義務度が変わっても、fidelity 監査が「等価/毀損」の二値でしか扱えず属人的。
  - run 002: fidelity が f011「購入していただく必要がある→ご購入いただく（義務標識削除, minor）」と f007「必要がある→ください（1段降格）」を同じ土俵で判断。義務標識の削除は「情報欠落」チェックからも漏れやすい。
  - day0: fidelity-A が「modality 強度を順序尺度化」を既に提起。
- 出所: fidelity-A(day0), fidelity-001, fidelity-002, naturalness-002
- 提案: 義務度 4 段尺度（義務 must ＞ 要請 should ＞ 勧告 please ＞ 任意 may）を taxonomy に定義。diff の各 edit に `modality_before/after`、受動↔能動 edit に `actor_before/after`（市・窓口・利用者・不特定 の enum）を記録。監査は「1 段以内=minor、2 段以上 or 義務→任意=critical」で機械線引き。fidelity チェックに「規範情報（義務・条件・期限・資格要件）の保存」独立項を追加。
- 影響: `content-fidelity-auditor.md`, `japanese-style-rewriter.md`, `ai-tell-taxonomy.md`

---

## P2 — 分類・レシピ・チェックリスト

### IMP-007 過剰敬語・二重敬語スタック の独立カテゴリ K 新設 `status: candidate` `hits: 1run(3agent)`
- 症状: 設計思想は「過剰な丁寧体・敬語」を日本語 AIクセ4大重心の一つに挙げるのに、対応する独立カテゴリが A〜J に無い。「ご準備いただく必要がございます」「ご利用いただくことが可能となっております」のような **謙譲＋可能/必要＋となる のスタック**が行き場を失い F-2/I-3/A-6 へ finding ごとにブレて分類される。
- 出所: detector-002, rewriter-002, naturalness-002（すべて run 002）
- 提案: 新カテゴリ **K「過剰敬語・二重敬語スタック」★日本語固有** を提案。推敲役向けに「謙譲は 1 段だけ残す」下限規則。※現状 hits:1run のため昇格保留。**次回 day-1 の公的文書 run で再現すれば ready へ昇格**（実例は下の候補欄に記録）。
- 影響: `ai-tell-taxonomy.md`（新カテゴリ）, `rewriting-playbook.md`

### IMP-010 suggested_fix の非拘束性・助詞調整が未規定 `status: ready` `hits: 2run`
- 症状: (a) suggested_fix が意味を変える置換を提案する場合の優先順位が未明文（run 001 f011「可能性→用途」・f029「検討→試す」は fidelity 優先で退けた）。(b) suggested_fix が span 内で閉じず助詞調整が必須（run 002 f003「システムが→を」が無いと非文）。
- 出所: rewriter-001, rewriter-002
- 提案: playbook 冒頭に「suggested_fix は候補であり拘束しない。意味等価が最優先」を明記。detector 出力に `needs_particle_adjustment: true` フラグ。
- 影響: `rewriting-playbook.md`, `ai-tell-detector.md`

### IMP-011 過推敲の「下限」メトリクスが無い（公的文書で事務メモ化リスク） `status: candidate` `hits: 1run`
- 症状: 鉄則は上限（30/50%）のみ監視し、定型敬語・挨拶・留意喚起を消しすぎて格を損なう下振れを検知できない。
- 出所: rewriter-002, naturalness-002, fidelity-002（run 002）
- 提案: register 維持率（定型敬語の保持/必要保持比）を過削除の下限メトリクスに。公的文書は「開頭御礼／末尾依頼を各1回は残す」等の保持下限リスト（IMP-008 と連動）。
- 影響: `SKILL.md §総合判定`, `naturalness-reviewer.md`, `rewriting-playbook.md`

### IMP-012 再現カウントを機械可読 2 軸で記録 `status: candidate` `hits: 1run`
- 症状: 「異なる run で 2 回」と「同一 run で複数エージェントが同意」が口頭で混同されやすい（K候補審査で顕在化）。
- 出所: taxonomist（2026-09-19）
- 提案: detection meta に `run_id` を、拡張候補に `hits: {distinct_runs: N, agent_votes: M}` の 2 軸を分離記録。昇格判定は `distinct_runs>=2` を必須・`agent_votes` は参考値としてスキーマ上で強制。
- 影響: `ai-tell-taxonomy.md §拡張候補欄/§スキーマ`, `ai-tell-detector.md`

### 新パターン候補（taxonomist 審査待ち）
- **C 系: redundant restatement**（day0）叙述と箇条書きが同内容を二重記載。実例 001(day0)。 `hits: 1`
- **D-7 ブログ結び呼びかけ公式**（day0）「今回は〜ご紹介しました」等。実例2件。 `hits: 1`
- **C-9 導入誘導定型**（day0）「さっそく見ていきましょう」式。 `hits: 1`
- **D-1 サブ: 勧誘型結び「（ぜひ）〜してみてはいかがでしょうか」** ブログ AI が末尾で多用、人間の技術記事ではまず出ない S1 級。実例 2026-09-19-001。 `hits: 1` 出所 detector-001
- **A-5 サブ: 可能の名詞化「〜が可能になる/〜が可能だ」** be able to の名詞化形で A-5 明示例に無い。実例 2026-09-19-001「生成することが可能になります」。 `hits: 1` 出所 detector-001
- **A-8 除外規約: 自然な連体修飾の「による」** 「電話による受付」型は誤検出しない旨を A-8 定義に明記。実例 2026-09-19-002。 `hits: 1` 出所 naturalness-002

### fidelity チェックリスト追補（day0 起票、継続）
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか**（f019 型）。`status: ready` `hits: 1`
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を問う。`status: ready` `hits: 1`
- **規範情報の保存チェック**（義務・条件・期限・資格要件の削除は数値欠落と同格）← IMP-009 と連動。実例 run 002 f011。`hits: 1` 出所 fidelity-002
- 削除の二分判定（情報を含む削除 vs ボイラープレート削除）。出所 fidelity-B(day0)
- 接続詞削除が担う論理関係を detector 側でタグ付けし監査が機械照合（実例 run 001 f031「これにより」）。出所 fidelity-001

### playbook レシピ追補
- **受動＋こととなる/となっている の複合解体レシピ**（A 節に新設行）: ①行為者を主語に復帰 ②能動断定 or 能動可能形。助詞（が→を 等）の同時調整を明記。実例 run 002 f003「導入されることとなりました→導入します」。 `status: ready` `hits: 1` 出所 rewriter-002
- **敬体×技術文書向け E-2 サブレシピ**: 体言止め・のです・分裂文（〜のが〜です）を優先、「でしょう」は推量箇所限定（断定文で使うとヘッジ増）。実例 run 001。出所 rewriter-001
- C-5 絵文字削除後の文末吸収ルール（day0）。出所 rewriter-B
- D 系結びは「最小着地文を残す」下限（day0）。出所 rewriter-B, naturalness-B
- 機能が必要な接続詞（しかしながら）は削除でなく変奏（day0）。出所 rewriter-A
- 原文が元から推量の D 系は推量を保持（day0）。出所 rewriter-A

### naturalness 判定の精緻化
- **E-2 は絶対比率でなく「連続ラン長（3連続以上）」で判定**。短文・低文数だと比率が不安定（実例 run 001「ます 8/14」）。 `hits: 1` 出所 naturalness-001, naturalness-B(day0)
- **改善率90%超のときこそ過推敲監査を強める**（装飾殲滅バイアスで天井に張り付く。改善率高＝良推敲とは限らない）。実例 run 001 改善率97.4%。 `hits: 1` 出所 naturalness-001
- **等級 A 判定は「残存 S1=0 かつ S2≤2」を主条件、改善率を従**とする（短文で改善率が出にくいケースに備え優先順位を明文化）。出所 naturalness-002
- 過推敲シグナルの定量化（敬体/常体混入は文末形態の二値カウント）（day0）。出所 naturalness-A
- クラスタ系 finding のクラスタ崩壊時 severity 降格（day0）。出所 naturalness-A
- 絶対残存数ガードを grade 表に組込み（S1 が1件でも C 以下）（day0）。出所 naturalness-A/B

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 1run(3agent)` → IMP-008 に統合
- ルーティン・モチベーション・データドリブン等の定訳が冗長になる語は半免責し残差 S3 固定（day0）。IMP-008（ジャンル別許容カタカナ語リスト）に吸収。

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。**2026-09-19 の両 detector が実行済み（全 span assert 通過）**。運用で定着。出所 detector-A(day0), detector-001/002
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`（day0）。出所 detector-B
- **許容として不検出にした定型を suppressed リストに残し監査性を上げる**（レビュアーが検出漏れと誤認しないため）。実例 run 002。 `hits: 1` 出所 detector-002
