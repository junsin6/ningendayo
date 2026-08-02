# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数（別 run での再現のみ +1）。

最終更新: 2026-08-02（run 2026-08-02-001, 002）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run`
- 症状: difflib 文字単位 change_rate が構造編集・純削除で機械的に膨張。2026-06-12-002 は 54.6% で誤発火。**2026-08-02 で再現**: rewriter-002 が「difflib は構造再整列で暴れ、span 編集合計と乖離する」と再指摘（今回は語句手術のみで 0.19 と実態一致、逆に構造編集時のブレを裏づけ）。rewriter-001 も round1 0.266 と自メトリック 0.226 の乖離を報告。
- 出所: rewriter-A/B(0612), naturalness-B(0612), **rewriter-002(0802), rewriter-001(0802)**
- 提案: change_rate を「difflib 全体値」と「span 編集文字数の単純合計/原文」の 2 本立てで記録し、30/50% 閾値判定は後者（編集量ベース）で行う。装飾・常套句の純削除分を控除、del≫ins の削除主導は中断対象から除外。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`
- 備考: Step4 未適用（メトリック定義の統一が要り、ドキュメントだけでなく rewriter 実装の合意が必要なため次サイクル候補）。

### IMP-002 severity_weighted_score の正規化式が未定義で run 間再現不能 `status: done(applied 2026-08-02-001/002)` `hits: 2run`
- 症状: 正規化式が SSOT に無く detector ごとに式がぶれる。**2026-08-02 で決定的に再現**: 同一ハーネスの detector-001 が `min(100,raw)`=62.0、detector-002 が `100(1-e^(-raw/40))`=59.8 と**別式を採用**し、同一 run 内で不整合。naturalness-002 も「正規化係数不透明で再現不能」と指摘。
- 出所: detector-A/B(0612), **detector-001/002(0802), naturalness-002(0802)**
- 適用: 正準式を `score = 100×(1 − exp(−raw/40))`（raw = 5·S1 + 2·S2 + 0.5·S3）に確定し taxonomy §スキーマ・ai-tell-detector.md に明記。τ=40 は既存 run と整合（raw106→92.9≈記録92.5、raw36.5→59.8）。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md`

### IMP-003 score_before のフィールド契約が曖昧 `status: ready` `hits: 1run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。
- 出所: naturalness-A(0612)
- 提案: 「score_before = 02_detection.json の meta.severity_weighted_score」と明文化。
- 備考: 2026-08-02 は運用側でオーケストレーターが基準値を明示指定して回避（暫定）。SSOT 明文化は未了。影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: done(applied 2026-08-02-001/002)` `hits: 2run`
- 症状: 反復・分散・文書レベルパターン（絵文字散在・文末単調・受動連鎖・N回反復カタカナ）は単一 start/end で表せず、代表 span を置くしかない。**2026-08-02 で全員再現**: 推敲役が「reason 本文をパースして追加 span を拾う必要があり機械処理に脆い」（rewriter-001）、「E-2 の代表 span が残すべき定型を指し span-grounded 原則と衝突」（rewriter-002）、両 detector が `scope:"document"` / `evidence_offsets[]` / `related_spans[]` を要望。
- 出所: detector-A/B(0612), **detector-001/002(0802), rewriter-001/002(0802), naturalness-002(0802)**
- 適用: finding に任意フィールド `scope: "contiguous"|"scattered"|"document"`（既定 contiguous）と `related_spans: [[s,e],...]`（反復・分散の全出現位置）を追加。ai_tell_density は union（重複除去）で数えると明記。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`, `japanese-style-rewriter.md`, `naturalness-reviewer.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: done(applied 2026-08-02-001/002)` `hits: 2run`
- 症状: 1 span が複数カテゴリに該当し、edits/findings 1:1 前提で件数・density がぶれる。**2026-08-02 で再現**: 「削減できるという点です」に A-5+A-13+I-1 が凝縮（detector-001）、rewriter-001 が「edit 件数と実変更箇所数が乖離、`span_overlap` フラグが欲しい」、fidelity-002 が「checklist 起点と edit 起点の突合方法が未定義」。
- 出所: detector-A/rewriter-A/B/naturalness-A/fidelity-A(0612), **detector-001/rewriter-001/fidelity-002(0802)**
- 適用: 「1 span = 主分類 1 finding」を基本とし、任意 `merged_categories: [...]` を許容。category_summary は「findings の主 category 先頭文字を集計」と注記。fidelity の rollback 対象は `rollback_edits` を正本とする。
- 影響: 各 .md のスキーマ節, `content-fidelity-auditor.md`

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 1run`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーが手動照合になりがち。
- 出所: naturalness-A(0612)
- 備考: 2026-08-02 は両 naturalness に「検出器を実測せよ」と明示指示し実走査で回避。SSOT で経路を必須化する明文はまだ。影響: `naturalness-reviewer.md §処理`, `SKILL.md`

### IMP-007 fidelity 13項に「述語概念の置換」を受ける独立項目が無い `status: done(applied 2026-08-02)` `hits: 2run`
- 症状: 動詞・述語レベルの意味すり替えが #10(欠落) と #11(追加) の複合で、どちらにも半分ずつかかり分類がぶれる。**2026-08-02 の両 run の唯一の fidelity fail がまさにこの型**: 001 f011「加速していく(rate)→広がっていく(scope)」、002 f011「予定(計画モダリティ)→確定コミット」。ともに「文体目的（A-10/A-6 解消）は正当だが過程で述語概念/モダリティを差し替えた」境界事例。
- 出所: **fidelity-001, fidelity-002(0802 両方)**
- 提案: チェックリストに **#14「述語・主張内容の等価性（動詞概念・モダリティ強度の保存）」** を新設。または #7 modality の定義に「確実性・計画（予定/見込み/場合がある）の順序尺度」を、#10 に「述語概念のすり替えによる含意変化」を明記。モダリティ保持必須リスト（予定・見込み・場合がある・可能性）を playbook Do-NOT 付近へ。
- 影響: `content-fidelity-auditor.md §チェックリスト`, `rewriting-playbook.md §Do-NOT`

### IMP-008 「意味語＋AIクセ」の混合 span を分解する前処理規約が無い `status: ready` `hits: 1run(2agent)`
- 症状: 「予定となっております」は意味語『予定』＋クセ『となっております』の混合体。rewriter が A-6 として一括除去し意味語まで落とした（002 f011 の直接原因）。「有効なソリューションである」も B-2+A-10 の交差。
- 出所: fidelity-002, rewriter-002(0802)
- 提案: rewriter は除去前に span を「意味語｜クセ層」に分解し、クセ層のみ剥がすルールを playbook に明記。detector 側で混合 span に `mixed: true` を付ける案も。

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **K「過剰・破格敬語」新カテゴリ候補** ★日本語固有: 設計思想は「過剰な丁寧体・敬語」を4本柱の一つに挙げるのに A〜J に敬語専用枠が無い。K-1 二重敬語（差し上げられる＝謙譲＋受身/尊敬られる）/ K-2 謙譲・尊敬の混線 / K-3 クッション語過多（賜りますよう・何卒・いただきますよう連発）。実例2件: 「ご連絡が差し上げられる予定」「ご来館いただきますようお願い申し上げます」。 `hits: 1run(2agent)` 出所 detector-002, rewriter-002
- **A-8b「無主語受動の濫用」** ★日本語固有寄り: 現 A-8 は「〜によって」限定だが公的文書の最頻出 AI 受動は無主語（実施される/停止される/対応が行われます/推奨される）。実例2件: 「サービスの一部が停止されることとなりました」「窓口にて対応が行われますが」。 `hits: 1run(2agent)` 出所 detector-002, rewriter-002
- **A-14「〜すること/ことによって（手段・原因の機械反復）」**: `by doing X` の直訳的手段表現。受動でないため A-8 に収まらない。実例: 001 で「採用することによって/実施することによって/処理することによって」3反復。 `hits: 1run` 出所 detector-001
- **A-6 のシグネチャに「〜こととなりました／こととなります」を追記**: 形式名詞を挟む状態叙述（意思決定主体をぼかす公的常套）。実例: 002 で3回（122,160,480）。 `hits: 1run` 出所 detector-002
- **A-10 に「抽象主語＋一般叙述/自動詞（〜である・〜していく）」サブ枝**: 万能動詞（示す/提供する/もたらす）を伴わない無生物主語も翻訳調。D-5 との切り分け基準（動詞が擬人化的か否か）を明文化。実例: 001「活用は加速していく」「有効なソリューションである」。 `hits: 1run` 出所 detector-001
- **観測動詞「予想されます/見込まれます/期待されます」の扱い**: A-6/G 系の無主体・状態叙述に近い。残す/断定化する条件が未収録。実例: 001「高まっていくことが予想されます」（未修正で残存 S2）。 `hits: 1run` 出所 rewriter-001, naturalness-001
- （継続）C 系 redundant restatement, D-7 ブログ結び, C-9 導入誘導定型（0612 起票、再現待ち）

### fidelity チェックリスト追補
- **#14 述語概念・モダリティ強度の保存**（IMP-007 参照）: 2run で fail 実証済み、昇格。
- **モダリティ確実性スケール**: 連絡する/した/する予定/する見込み/する場合がある を順序尺度化し、ヘッジ削除時の保持必須リスト化。出所 fidelity-002
- **迂回要請除去の許容判定テスト**: 「削除語が命題内容（真理条件）に影響するか、発話内効力の包装にすぎないか」を #7 手順に成文化（002 で「必要がございます」除去=許容 vs 「予定」除去=非許容の線引き）。出所 fidelity-002
- **公的文書の責任主体×確実性の二軸チェック**（ジャンル専用サブチェック）。出所 fidelity-002
- **「考えられています」の主語（著者/外部）を検出器がタグ付け**し modality 強化可否を機械判断。出所 fidelity-001
- （継続 0612）#14 接続語/順序語の序列混入, 削除専用サブチェック, 情報含む削除 vs ボイラープレート二分。

### playbook レシピ追補
- **二重敬語ねじれ変換表**: 差し上げられる→いたします、させていただけます→いたします 等。K カテゴリと対。出所 rewriter-002
- **A-8 無主語受動→無主語能動＋謙譲**（対応が行われます→対応いたします）。出所 rewriter-002
- **B-2 カタカナ「保持ライン」語彙リスト**（フィルタリング・アップロード・トラフィック・データセンター・リモート等の準定着語）＋ finding に `katakana_verdict: open|keep|borderline`。ジャンル別（技術/コラム/公的）許容密度も。出所 rewriter-001, naturalness-001, fidelity-001
- **並列・対句の非対称和語化ルール**: 一方だけ和語化・他方カタカナ保持は人間的で正。両方きれいに和語化は過推敲シグナル候補。出所 naturalness-001
- **A-8「することによって」分散変換の注意**: 「すれば」は反実仮想にも読めるため必要十分条件を主張する文では避ける。出所 fidelity-001
- **C-1 溶かした後の段落冒頭バリエーション**指針（順序語除去後に名詞始まりへ寄り単調化する副作用）。出所 rewriter-001
- （継続 0612）C-5 絵文字後の文末吸収, D 系最小着地文, 機能接続詞は変奏, 元推量の D 系は保持。

### naturalness 判定の精緻化
- **等級 A の内部帯（A+/A-）**: 短め文書で全消しすると改善率が98%超に張り付き「圧勝」と「辛勝」を区別できない。改善90%+ かつ 残存0 を A+ 等。出所 naturalness-002
- **`residual_source: {original_missed, newly_exposed, introduced}`**: 元 finding 取りこぼしと推敲で露出した素の残存を区別。newly_exposed は検出器へフィードバック。実例: 001「予想されます」。出所 naturalness-001
- **過推敲シグナルの数値化**: severity＋該当span＋文末多様度（distinct-ending 数）・平均文長偏差を meta 常設フィールド化。出所 naturalness-002, naturalness-A(0612)
- **ジャンル別「反復許容定型句ホワイトリスト」と許容反復回数**（公的文書＝末尾定型は E-2 で減点しない等）。出所 naturalness-002, detector-002
- （継続 0612）クラスタ崩壊時 severity 降格, E-2 体言止め合格ライン, 絶対残存数ガードを grade 表へ, 定着カタカナ B-2 免責。

### detector 実装
- ai_tell_density は多カテゴリ重複 span を **union で計上**（IMP-004 で明文化済）。出所 detector-001
- 「文末・締め文」走査の強化（締めに抽象主語＋ヘッジが残りやすい）。出所 naturalness-001
- （継続 0612）start/end 自己検証, 絵文字レンジ明示。
