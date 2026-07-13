# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-07-13（run 2026-07-13-001 技術解説, 002 公的文書）。本日 IMP-001/002/003/006 を適用（status: done）。

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done` `hits: 2runs(8agent)` 適用: 2026-07-13-001/002
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。day0 Sample B は 54.6% で `hold_and_report` 誤発火。**2026-07-13-001（技術解説）で再現＋悪化**: 1次 57.4%、round2 では原意復元のロールバックなのに編集距離が 60.0% へ増加する**逆行現象**を実証（difflib 上「戻す」操作が距離を増やす）。002 も 30.2% で削除主導。
- 出所: rewriter-A/B(day0), rewriter-001/002, naturalness-B(day0)/001, round2-rewriter-001, fidelity-001
- 提案→**適用**: (a) `change_rate` に加え `net_length_delta_rate`（正味長さ変化）と `deletion_share`（削除主導度）を**併記必須化**。(b) 50% 超でも deletion_share>0.6 かつ net 小なら自動 hold_and_report を返さず override 続行。(c) ロールバック edit に `direction: "toward_source"` を付し閾値判定から割引。(d) 中断対象は「挿入主導で意味改変を伴う膨張」に限定。
- 適用ファイル: `rewriting-playbook.md §変更率の数え方(v1.1)`, `japanese-style-rewriter.md 手順5`, `SKILL.md §総合判定`（override 行追加）。
- 残: `direction`/`supersedes` フィールドのスキーマ正式化は未（IMP-004/005 と併せて次回）。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2runs(4agent)` 適用: 2026-07-13-001/002
- 症状: 正規化式が SSOT に無く高密度短文で 100 付近に張り付く。**2026-07-13 で再実証**: 2 検出器が**異なる式**を採用（001: `W/((L/100)*8)`、002: `W/L*1000`）し、001=100.0 飽和・002=96.1 高止まり。式の非統一そのものが根本原因と確定。
- 出所: detector-A/B(day0), detector-001, detector-002
- 提案→**適用**: 単一式 `score = round(100·(1−exp(−W/45)), 1)`（W = 5·S1+2·S2+0.5·S3）に一本化。K=45 は SSOT 例 W56→71.5 をアンカー（→71.2）。検証: W134→94.9, W62→74.8 と飽和せず解像度を保つ。全検出器・レビュアーが同一式を使用。
- 適用ファイル: `ai-tell-taxonomy.md §検出出力スキーマ`（v1.1）, `ai-tell-detector.md 手順5`, `naturalness-reviewer.md`（score_after 同一式）。

### IMP-003 score_before のフィールド契約が曖昧 `status: done` `hits: 2runs(3agent)` 適用: 2026-07-13-001/002
- 症状: naturalness-reviewer がどの値を score_before にするか未固定でぶれる。今回両レビュアーとも 02 の値を採用したが、契約が明文化されていないと再びぶれ得る。
- 出所: naturalness-A(day0), naturalness-001, naturalness-002
- 提案→**適用**: 「score_before = 02_detection.json の meta.severity_weighted_score をそのまま採用（推定値を作らない）」を SSOT とエージェントに明文化。
- 適用ファイル: `naturalness-reviewer.md 手順2`, `ai-tell-taxonomy.md §検出出力スキーマ`。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2runs(4agent)`
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。**2026-07-13 で再現**: detector-001（E-2/C 文書レベルを代表 span で補完）・detector-002（E-1/E-2 の start/end を代表アンカーで代用、density 計算から手動除外）。両者とも scope 表現の欠如を独立に指摘。
- 出所: detector-A/B(day0), detector-001, detector-002
- 提案: `scope: "span"|"scattered"|"document"` と scattered 用 `occurrences: [[s,e],...]` を追加。density は被覆ベースと定義（v1.1 で density の被覆ベースは明文化済、scope フィールドは未）。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`。次サイクルの適用候補。

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2runs(7agent)`
- 症状: 1 span が複数カテゴリに該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。**2026-07-13 で再現**: detector-001（「メリットを提供することができます」= A-10＋A-5 入れ子で density 二重計上）・detector-002（「導入されることとなっております」= A-8＋A-6 複合、`secondary_category[]` 追加を提案）。round2-rewriter-001 も「round を跨ぐ表層置換で finding:edit が 1:1 にならない」と指摘。
- 出所: detector-A/rewriter-A/rewriter-B/naturalness-A/fidelity-A(day0), detector-001, detector-002, round2-rewriter-001
- 提案: 「1 span = 主分類 1 finding」を基本とし `secondary_category: [...]`（重なり）＋ `supersedes: [finding_id]`（round 跨ぎ置換）を許容。category_summary は主分類先頭文字を集計と注記。
- 影響: 全 .md のスキーマ節。次サイクルの適用候補。

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: done` `hits: 2runs` 適用: 2026-07-13-001/002
- 症状: 仕様は「検出器を同基準で再走査」だが day0 レビュアーは手動照合。**2026-07-13 では両レビュアーとも `ai-tell-detector` サブエージェントを実呼び出しでき、経路が機能することを実証**。
- 出所: naturalness-A(day0), naturalness-001, naturalness-002
- 提案→**適用**: `naturalness-reviewer.md` 手順1で「必ず実呼び出し（手動照合禁止、不能時のみ手動＋明記）」を明文化。
- **新たに判明した追補（要フォロー）**: 検出器は 03 を独立文書として走査するため、02 が finding 化しなかった閾値下 span を新規に拾う。手順1に「02 の finding 台帳と突き合わせて残存を過大計上しない」を追記済（naturalness-001 の指摘）。

### IMP-007 ジャンル別 severity 補正・敬語下限ガードが無い `status: open` `hits: 1run(2agent)`
- 症状: 公的文書では A-1/A-2/I-3 が一定密度まで自然（格式）だが、taxonomy は一律 S1/S2。002 で A-2「につきまして」を機械的に S1 計上すると S1×3 で grade D に誤落。逆に「敬語を削りすぎてぞんざい化」する下限側の過推敲を検出する仕組みも無い（現行の過推敲シグナルは口語化＝上限側のみ）。naturalness-001 でも「A-1 は severity ラベル[S1]と density 処方[2回以下許容]が矛盾」と同型の指摘。
- 出所: naturalness-002, naturalness-001
- 提案: (a) taxonomy にジャンル別 severity 補正表（公的文書で A-1/A-2/I-3 を一定密度まで S1→S2 降格）。(b) density-aware severity（A-1 は 3 回目以降 S1、1〜2 回は S3）。(c) 敬語下限割れ（依頼形・締め語の欠落＝ぞんざい化）を過推敲シグナルに追加。
- 影響: `ai-tell-taxonomy.md`, `naturalness-reviewer.md`。**hits 1（002＋naturalness-001 で同型だが別 run 再現は次回）。昇格待ち。**

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: day0-001。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B
- **I-3b 敬語版「〜（て）いただく必要がございます」定型ブロック**（★日本語固有・公的文書）: I-3 の敬語版で、動詞だけ差し替えた完全平行反復として量産。実例（07-13-002 内 2 件）「ご確認いただく必要がございます」「ご了承いただく必要がございます」。人間の職員はこの定型を 3 連発しない。 `hits: 1(run002内2例)` 出所 detector-002, rewriter-002。**別 run 再現で昇格候補**。
- **A-13 系「〈固有名詞〉という＋類概念語（テクノロジー/ソリューション/コンセプト）」同格導入**: 英語 `a technology called X` 直訳臭。実例（07-13-001 内 2 件）「エッジAIコンピューティング**というテクノロジー**」「推論を実行するアーキテクチャを**指す概念です**」。 `hits: 1(run001内2例)` 出所 detector-001。
- **A-2 系「〜に関する〜につきましては」二重形式化主題**（公的文書）: 1 句に主題枠を二重に被せる。実例「本件に関するお問い合わせにつきましては」。 `hits: 1` 出所 detector-002, rewriter-002。
- **A-6 系「〜運びとなりました」儀礼的状態化**（公的文書）: 単発でも露見度が高い儀礼定型。実例「実施される運びとなりました」。A-6 の例文追加候補。 `hits: 1` 出所 detector-002, rewriter-002。
- **A 系「当該（期間／機能）」官庁調反復**: 公的文書 AI 文で「当該」多用が準・翻訳調シグナル。実例（07-13-002 で3回）。 `hits: 1` 出所 rewriter-002, naturalness-002（過推敲シグナルとしても計上）。
- **B-2 系「同一概念のカタカナ・和語ちゃんぽん反復」**: 同一文書で同一概念を複数語で言い換え密度化。実例「レイテンシ／タイムラグ／遅延」（07-13-001）。B-2 下位の密度シグナル候補。 `hits: 1` 出所 detector-001。

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019（並列→基盤の序列混入）はこの項が無く #5/#11 へ漏れ込んだ。`status: ready` `hits: 1` 出所 fidelity-A
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。`status: ready` `hits: 1` 出所 fidelity-B
- 「情報を含む削除 vs ボイラープレート削除」二分判定: 削除 span に (a)数値/固有名詞/日付 (b)条件/因果節 (c)固有の例示 を含めば情報欠落、挨拶/CTA/装飾/自己言及のみならボイラープレート。出所 fidelity-B
- #5論理関係 と #11情報追加 の責任境界を一意化（主因項目を 1 つに正規化）。出所 fidelity-A
- modality 強度を順序尺度化（要請/推奨/義務/必須）。出所 fidelity-A
- **#15 主張強度・主張種別の変更を独立項に新設** ← 07-13-001 で「注目を集めている→広がってきた」（関心→採用の格上げ）が #4極性でも #11情報追加でも捉えにくく隙間に落ちた。「可能性→事実」「関心→採用」「提案→断定」型の *命題の格上げ* を独立検出。`status: ready` `hits: 1` 出所 fidelity-001
- **modality tier 尺度の具体化＋±2 段ルール**: `可能性/かもしれない(1) < だろう/でしょう/と言える(2) < はず/傾向(3) < である/する(4)`。原文 tier から +2 段以上の移動を毀損とする。07-13-001 f040（可能性 tier1→はず tier3=+2）で fail 機械判定できた。`status: ready` `hits: 1` 出所 fidelity-001
- **複合削除の文単位再合成テスト**: 単一 span では無害でも束ねると命題を変質させる（07-13-001 f040「可能性」削除＋f042「革新的な」削除の結合）。deletion-recall を span 単位に加え *文単位* でも 1 回回す。出所 fidelity-001
- **能動化による行為者の新規前景化チェック**（公的文書）: 原文が意図的に行為者を伏せる緩衝表現（「対応がなされます」）を能動化すると主体が新規顕在化し、責任・約束の含意を追加し得る。#9 にサブチェック追加。出所 fidelity-002

### playbook レシピ追補
- **C-5 絵文字削除後の文末/区切り吸収ルール**（句点で吸収 or 削除のどちらか明記）。出所 rewriter-B
- **D 系結びは削除一択でなく「最小着地文を残す」**（減らしすぎ下限）。実例: B の「気軽に始めてみてください」。出所 rewriter-B, naturalness-B
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**という例外則。出所 rewriter-A
- **原文が元から推量の D 系は推量を保持**（「断定へ」の一律処方の例外）。出所 rewriter-A
- **公的文書のジャンル別「下限敬語ライン」**: (1) 依頼は「〜ください/お願いいたします」まで下げてよいが「〜して」まで下げない、(2) 呼称・一次的儀礼（ご案内申し上げます）は残す、(3) 削るのは二重敬語・冗長定型（いただく必要がございます/求められております）のみ。I-3 の After「すべきだ/具体勧告」は常体レポート想定で敬体お知らせには失礼。`status: ready` `hits: 1` 出所 rewriter-002
- **I-3 敬語版レシピ**: 「ご確認いただく必要がございます」→「ご確認ください」／「ご確認をお願いいたします」。「必要がある」の事実叙述と実質「依頼」の 2 用法を区別（お知らせは後者）。出所 rewriter-002
- **A-6＋A-8 複合レシピ**: 「新機能が導入されることとなっております」→「新機能を導入します」。受動＋状態化の二重シグネチャを行為者主語の能動断定で一挙解消。出所 rewriter-002
- **I-4 結語レシピ**: 「皆様のご理解とご協力が求められております」→「〜をお願いいたします」。行政/ビジネス AI 文の最頻出結語。出所 rewriter-002
- **A-2 二重主題レシピ**: 「本件に関するお問い合わせにつきましては」→「本件のお問い合わせは」。出所 rewriter-002
- **A-7×A-13 複合レシピ**: 「帯域幅を最適化するというメリットも有しています」→「帯域幅も最適化できます」（という＋メリット＋有する を一括で動詞述語へ）。出所 rewriter-001
- **A-6×A-5 複合レシピ**: 「継続することが可能となっています」→「続けられます」（状態叙述＋可能冗長を一手で可能動詞へ）。出所 rewriter-001
- **D-2/D-5 意義強調の首尾呼応は非対称化**: 冒頭「注目を集めている」と結び「注目に値する」の呼応は両方消さず、片方を実態叙述・片方を弱い評価に散らす。出所 rewriter-001
- **D-2/D-5 脱ハイプ×敬体維持の着地形レシピ**: 擬人化主語で fidelity が命題（可能性）保持を要求するケースの推奨形「今後の広がりが注目されています」「暮らしの中で使われる場面が増えていきそうです」。常体『だろう』へ落とさない。出所 round2-rewriter-001
- **同一語の未検出反復の語彙統一**: detector が代表 finding 1 つにしか span を張らない反復語（07-13-001「インファレンス」）は、代表 finding 配下で全出現を統一してよい／すべきと明文化（または detector 側で全 span 列挙）。出所 rewriter-001

### naturalness 判定の精緻化
- 過推敲シグナルの定量化（敬体/常体混入は文末形態の二値カウントで機械検出）。出所 naturalness-A
- クラスタ系 finding（B-2 密集・C-1 列挙）はクラスタ崩壊時に個別 severity を降格するルール。出所 naturalness-A
- E-2 文末単調の到達可能ライン緩和（体言止め1箇所以上で合格、文体維持制約下の過推敲回避）。出所 naturalness-B
- 絶対残存数ガードを grade 表に組込み（改善率が高くても S1 が1件でも C 以下）。出所 naturalness-A, naturalness-B

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 1run(3agent)`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B, fidelity-A, naturalness-A

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。出所 detector-A。**07-13 で両検出器が実装し 0 mismatch を達成**（反復語は occurrence 番号指定で分離）。
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B
- **index 基準の契約化**: start/end は「ファイル全文（タイトル行・改行含む）のコードポイント 0 基点」で統一。推敲役が本文のみ基準を使うとオフセットずれ。出所 detector-002
- **category_label 定訳辞書の SSOT 化**: ラベルが検出器ごとに表記揺れ。SSOT にラベル辞書を持たせる。出所 detector-001

### スキーマ追補（round・重なり表現）— 次サイクル適用候補
- `secondary_category: [...]`（1 span 複数カテゴリの重なり）＝ IMP-005。出所 detector-002
- `scope: "span"|"scattered"|"document"` ＋ scattered 用 `occurrences: [[s,e],...]` ＝ IMP-004。出所 detector-001/002
- `supersedes: [finding_id]` / `superseded_by`（round を跨ぐ表層置換の連結）＋ rewrite edit の `direction: "toward_source"`（ロールバック）＝ IMP-001/005。出所 round2-rewriter-001
