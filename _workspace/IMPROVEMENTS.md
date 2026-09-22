# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-09-22（run 2026-09-22-001, 002。day-1: 技術解説記事 / 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。Sample A も 47.6% と高止まり。
- **再現(2026-09-22-001)**: replace opcode が削除側＋挿入側を両方計上するため、正味縮約でも語句改変率が膨らむ。実例 f013「フォールトアイソレーション」(13字)→「障害の隔離」(5字) は net -8字なのに 13+5=18字分カウント。カタカナ語→漢語の縮約ほど change_rate 悪化＝正しい推敲がペナルティを受ける。run 001 は change_rate 36.5%（>30%警告）だが insert率0.6%・縮約主導で過推敲ではなかった（自然度A）。
- 出所: rewriter-A, rewriter-B, naturalness-B（day0）; rewriter-001（day1 再現）
- 提案: (a)「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を change_rate から控除。(c) 挿入率を単独併記し、del≫ins の削除主導ケースは中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。(e) 語句改変率は net編集距離(Levenshtein) or replace区間 max(len_a,len_b) で数え、両側加算をやめる。閾値(30/50%)も再校正。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`

### IMP-002 severity_weighted_score の正規化が未定義で検出器ごとに式が割れる `status: DONE(2026-09-22-001,002)` `hits: 2run`
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える（Sample A raw106→92.5、taxonomy 例は raw56→71.5 と不整合）。
- **再現(2026-09-22)**: 決定的証拠。**同一パイプラインで検出器2機が別式を採用**した — detector-001 は `min(100, raw)` で raw=105 が 100 に飽和（S1×11 と S2×25 の差が潰れた）、detector-002 は `100×raw/(raw+30)` を採用し raw=74→71.2。同一 run バッチでスコアが比較不能。naturalness-001/002 も別々に式を再定義。
- 出所: detector-A, detector-B（day0）; detector-001, detector-002, naturalness-001, naturalness-002（day1 再現＝式の実分岐を観測）
- 提案→**適用**: SSOT に `score = 100 × raw/(raw+k)`, `k=30`, `raw = S1×5 + S2×2 + S3×0.5` を固定（飽和せず taxonomy 例 raw≈75→71.5 とも整合）。detector・naturalness-reviewer は必ずこの式を使い、`meta.score_raw`（正規化前）も併記。改善率は uncapped raw ベース。
- 適用 run: 2026-09-22-001, 002（taxonomy §検出出力スキーマ・ai-tell-detector.md・naturalness-reviewer.md を編集、taxonomist が v1.1 昇格審査）。

### IMP-003 score_before のフィールド契約が曖昧 `status: ready` `hits: 1run+副作用`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score 92.5）。レビュアーごとに数値がぶれる。
- 出所: naturalness-A
- **補足(2026-09-22-001)**: 契約自体は両レビュアーが meta.severity_weighted_score を採用し安定。ただし `min(100,raw)` キャップ下では改善率の分子分母が真の除去量(raw差103)を反映せず、高密度原文ほど改善率が過小評価される副作用（IMP-002 と連動）。→ IMP-002 適用で uncapped raw 併記により緩和。
- 提案: 「score_before = 02_detection.json の meta.severity_weighted_score」と明文化＋改善率は uncapped raw で算出。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: DONE(2026-09-22-001,002)` `hits: 2run`
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
- **再現(2026-09-22)**: detector-001 は E-2（です・ます単調・全12文）を代表位置「集めています」に無理に固定、reason に【文書レベル】と明記して回避。detector-002 も E-2 を代表 span に無理アンカー。両者とも「span 必須スキーマが文書レベルパターンと噛み合わない」と独立に報告。
- 出所: detector-B, detector-A（day0）; detector-001, detector-002（day1 再現）
- 提案→**適用**: `scope: "span"|"scattered"|"document"` を追加。document は start/end を null 許容。scattered は `occurrences: [[s,e],...]`。density は occurrences/scope を考慮した実 AI クセ文字数の union ベースと定義（重複・locator 除外）。
- 適用 run: 2026-09-22-001, 002（taxonomy §スキーマ・ai-tell-detector.md、taxonomist v1.1 審査）。

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 1run(5agent)`
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。
- 出所: detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A（横断的に最多）
- **補足(2026-09-22-001)**: A-10 文単位 span が B-2/F-5 span を内包（例「多くのメリットをもたらす」⊃「メリット」）。density を「span 総文字数」で数えると二重計上。detector-001 は union 面積で 0.382 を算出したが SSOT に計算法明記なく検出器依存。→ IMP-004 の density 定義（union）で一部解消。
- 提案: 「1 span = 主分類 1 finding」を基本とし、`merged_findings: [...]` 配列を許容。density は union 面積と明記。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: DONE(2026-09-22-001,002)` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。
- **再現・確定(2026-09-22)**: naturalness-001・002 とも、**subagent 実行環境に Agent/Task ツールが露出せず ai-tell-detector を spawn 物理不可能**と独立に報告。仕様（IMP-006 の「サブエージェント再呼び出し必須化」）と実行環境が矛盾。両者やむなく手動同基準再走査で score_after を算出。
- 出所: naturalness-A（day0）; naturalness-001, naturalness-002（day1 確定）
- 提案→**適用**: レビュアーに孫 spawn を求めない。**オーケストレーターが検証段で ai-tell-detector を 03_rewrite.md に対して直接呼び、`05_detection_after.json` を生成してレビュアーに入力として渡す**。レビュアーは判定に専念（手動再走査禁止）。
- 適用 run: 2026-09-22-001, 002（naturalness-reviewer.md §処理・SKILL.md §4 を編集）。

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 001。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B
- **K 系（新分類）: 過剰敬語・敬語の畳みかけ** ★日本語固有。公的文書 AI 頻出。実例(2026-09-22-002): 「皆様**におかれましては**」「方**におかれましては**」（×2）、「〜**いただきますようお願い申し上げます**」の畳みかけ、「ございます」連発。A〜J に受け皿なく E-2 に寄せざるを得なかった。 `hits: 1` 出所 detector-002
- **A-14 候補「〜することによって／〜によって（手段の by-ing 直訳）」** A-8(受動)とは別系の手段・条件の冗長直訳。実例(001): 「マイクロサービスを採用する**ことによって**」→「採用すると／採用すれば」。 `hits: 1` 出所 detector-001
- **A-6 サブ or 新「〜が存在します」= there is/exist 直訳** 「ある」で足りる存在叙述の英訳直訳。実例(001): 「考慮すべきポイントが**存在します**」。A-6/A-10 に綺麗に入らず取りこぼし。 `hits: 1` 出所 detector-001
- **A-13 サブ「〜のことを指しています／を指す」= 定義の語り出し定型** AI 解説記事の冒頭定義に高頻度。実例(001) 2件: 「分割するアーキテクチャスタイルの**ことを指しています**」「マイクロサービス**とは**、…**を指しています**」。 `hits: 1` 出所 detector-001
- **A-8 サブ分割 A-8a（による/によって＝手段）/ A-8b（される/なされる＝行為者秘匿の純受動）** 処方（行為者復元 vs 手段句解体）が異なるため密度カウントも粗い。実例(002) 両型が各5件前後。 `hits: 1` 出所 detector-002

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019（並列→基盤の序列混入）はこの項が無く #5/#11 へ漏れ込んだ。`status: ready` `hits: 2run`。**再現(001)**: f033「これにより（因果）」を削除し助詞「も（追加）」へ置換 → 因果が並列に変質し rollback_and_rewrite。→ **新副項 #5b「接続表現の論理種別保存」**（因果／並列／逆接／追加／条件の各マーカーが別種別へ置換されていないか）として昇格候補。H-1 多用の本ハーネスで頻発しやすい穴。出所 fidelity-A（day0）, fidelity-001（day1 再現）
- **modality 等価クラス表を references に整備** `status: ready` `hits: 2run`。義務性・確信度のグラデーション（求められる／必要がある／すべき／しなければならない／断定）を順序尺度化し「同一クラス内移動は pass、クラス跨ぎは fail」。加えて**文書レベルの modality 分布のずれ**（span 単位だけでなく義務表現群の総体強度が原文と釣り合うか）を項7副項に。実例: f025 要請→義務(001)、f010/f015/f019 義務系の分散柔化(002)。出所 fidelity-A（day0）, fidelity-001・fidelity-002（day1 再現）
- **行為含意動詞の含意保存（項12 追記 or 独立副項）** 判定・認定・承認・認可などの行為含意動詞を含意を欠く一般動詞に置換していないか。実例(002): f017「認められた」→「あった」で審査ニュアンス減衰。法令・審査を伴う公的文書で手続き意味の変化になりうる。`hits: 1` 出所 fidelity-002
- **能動化に伴う主語補完は項11（情報追加）で必ず再チェック（交差参照ルール）** A-8 能動化で原文に無い主語を補うと項9(行為者)と項11(追加)の双方に抵触しうる。実例(002): 今回は `が→を` 目的語化で回避できたが主体不在の受動が多い run では見落としリスク。`hits: 1` 出所 fidelity-002
- **substantive_checks を meta に追加** 該当要素なしの vacuous pass（数値・引用・出典が原文に無い等）を除いた実質監査項数を記録。実例(002): 「13項 pass」でも実質10項。`hits: 1` 出所 fidelity-002
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。`status: ready` `hits: 1` 出所 fidelity-B
- 「情報を含む削除 vs ボイラープレート削除」二分判定: 削除 span に (a)数値/固有名詞/日付 (b)条件/因果節 (c)固有の例示 を含めば情報欠落、挨拶/CTA/装飾/自己言及のみならボイラープレート。出所 fidelity-B
- **訳語化による「意味範囲の縮小/拡大」を捕捉する #12b** 別義への置換(#12)は見るが、resilience→回復力（耐障害性ニュアンスの一部脱落）のような同義方向だが意味範囲が縮むケースを拾えない。ジャンル別許容閾値つき。`hits: 1` 出所 fidelity-001
- **条件節の新規付与チェック** 断定→条件化（f009「このアーキテクチャは〜もたらす」→「この仕組みなら」）／条件→断定化を明示的に見る項目。`hits: 1` 出所 fidelity-001

### playbook レシピ追補
- **B-2 和語化時は "性／的／化" 密度を再評価（相互制約）** `status: ready` `hits: 1run+`。B-2 のカタカナ語を潰すと F-5「〜性」連鎖を新規生成する典型トレードオフ。実例(001): スケーラビリティ→拡張**性**・アジリティ→機動**性** が "性" を2件新規導入し、正味4回で F-5 無改善（自然度A だが残存 S2）。detector の suggested_fix が他カテゴリを悪化させないかの相互チェックが必要。出所 naturalness-001
- **A-8 受動→能動: 主語が原文に無い場合は目的語化・連用化で受動だけ外し、新規主語は補わない** `status: ready` `hits: 1run`。playbook の A-8 例「政府によって定められた→政府が定めた」は主語既出の例のみ。実例(002): 「システムが導入される」→〈市が〉ではなく「システムを導入する」で insert率0.000。出所 rewriter-002
- **従属節（〜ので／〜ため）内の I-3 は文末勧告化せず名詞述部の縮約に留める** `status: ready` `hits: 1run`。実例(002): f019「ご対応いただく必要がございます**ので**、ご了承ください」に suggested_fix「ご対応ください」を貼ると「ので＋ご了承ください」が脱落。「ことになりますので」へ留めた。出所 rewriter-002
- **公的文書の敬体レジスタ表（一般敬体 ています／公的謙譲 ております・いたします・ご案内する）** `status: ready` `hits: 1run`。「文体維持」を desu_masu 一段で扱うと公的文書で格落ち誤補正。A-8 能動化の After に謙譲形を選べるようレジスタ軸を追加。出所 rewriter-002
- **E-2 は他 finding 修正で誘発される二次的多様化を第一手段とし、強制変奏は最小に（特に公的文書）** `status: ready` `hits: 1run`。体言止め・でしょう は公的お知らせでは概ね不適。実例(002): 仕組みです・予定です・行ってください で文末が自然分散。出所 rewriter-002, naturalness-002
- **detector の suggested_fix は「文法的に閉じた span」を返す規約、または rewriter が外縁補正してよい旨を playbook に明記** 実例(001): f005 span「状態となっており」だけ置換で非文、f003「というアプローチ」→「手法」で非文。出所 rewriter-001
- **C-5 絵文字削除後の文末/区切り吸収ルール**（句点で吸収 or 削除のどちらか明記）。出所 rewriter-B
- **D 系結びは削除一択でなく「最小着地文を残す」**（減らしすぎ下限）。実例: B の「気軽に始めてみてください」。出所 rewriter-B, naturalness-B
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**という例外則。出所 rewriter-A
- **原文が元から推量の D 系は推量を保持**（「断定へ」の一律処方の例外）。出所 rewriter-A

### naturalness 判定の精緻化
- **過推敲シグナルの定量基準を定義（grade C の穴）** `status: ready` `hits: 2run`。C 基準「過推敲シグナル2個」だが 1個の重み・mild/severe 閾値・「述語省略のぶつ切り」を1シグナルに数えるかが未規定でレビュアー裁量依存。実例(001): 「考慮すべき点がいくつか。」の述語省略ぶつ切りを mild 1件計上。敬体中の副詞句止め vs 体言止め(E-2変奏・許容)の線引きも要る。シグナル種別（文体崩れ/原意脱落/リズム破壊/過度な口語化）ごとに severity と計数規則を定義。出所 naturalness-A（day0）, naturalness-001（day1 再現）
- **公的文書ジャンルは定型挨拶・定型結びの保持を非減点と grade 基準に明文化** `status: ready` `hits: 1run`。実例(002): 「運びとなりました」「におかれましては」は A-6/形式表現に形が似るが定型として非減点。出所 naturalness-002
- **密度で発火した finding が単発まで減った残存は S2 計上＋「閾値未満」フラグ** 実例(002): 「なお」元3件→1件。非 finding 扱いだと score_after=0/改善100% と過大評価になる。出所 naturalness-002
- **間接化の由来判定**: 間接化が敬意由来なら適正、行為者ぼかし由来なら A-8/I-4 残存計上。実例(002): f019「ことになります」。出所 naturalness-002
- クラスタ系 finding（B-2 密集・C-1 列挙）はクラスタ崩壊時に個別 severity を降格するルール。出所 naturalness-A
- E-2 文末単調の到達可能ライン緩和（体言止め1箇所以上で合格、文体維持制約下の過推敲回避）。出所 naturalness-B
- 絶対残存数ガードを grade 表に組込み（改善率が高くても S1 が1件でも C 以下）。出所 naturalness-A, naturalness-B

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 1run(3agent)`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B, fidelity-A, naturalness-A
- **技術ドメイン語のホワイトリスト（維持語）とグレー語の判断基準** `status: ready` `hits: 1run`。実例(001): 維持=マイクロサービス/デプロイ/レイテンシ/オブザーバビリティ、開く=レジリエンス/ケイパビリティ/アジリティ/メリット。フォールトアイソレーションは専門度次第でグレー。読者層タグ（専門/一般）で挙動を切り替える指示が playbook B-2 変換表に無い。出所 detector-001, rewriter-001

### スキーマ検算・実装の頑健化（taxonomist v1.1 審査由来） `status: ready` `hits: 1`
- **scattered / span の切り分け規則が未明文**: 反復パターンを「N 個の span finding」にするか「1 個の scattered」にするかの基準がなく、検出器ごとに割れると IMP-002 型（スコア比較不能）が再発しうる。推定ルール（一律削除系＝scattered、位置ごとに個別 suggested_fix が要る＝各 span）の明文化を推奨。出所 taxonomist
- **score 自己整合バリデーション**: 検出器出力に `|100·raw/(raw+30) − severity_weighted_score| ≤ 0.05` の assert を入れれば、今回の 71.5→71.4 型のずれを機械的に弾ける。出所 taxonomist
- **density union の共通ユーティリティ化**: 重複区間マージは実装が非自明。各検出器が独自実装すると union 面積が割れて density が再び比較不能になる。共通化を推奨。出所 taxonomist
- 丸め規則の全体明文化（score 以外の meta 値の桁統一）。出所 taxonomist

### ジャンル適合性のスキーマ化 `status: ready` `hits: 1run`
- finding に `genre_tolerance`/`do_not_touch` フラグ、meta に `genre` フィールドを追加し「許容/要修正」を構造化して rewriter に渡す。現状はジャンル判断が reason の散文にしか残らず、rewriter が機械的に全 finding を潰すと過推敲（挨拶定型破壊）を招く。出所 detector-002
- 検出手順: タイトル/見出しのハイプ語は本文と別閾値（過検出回避）。実例(001): タイトル「その本質を徹底解説」。出所 detector-001

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。出所 detector-A（day0）; 全 detector が今回実施し不一致0を報告（定着）
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B
