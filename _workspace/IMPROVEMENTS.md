# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-07-09（run 2026-07-09-001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。Sample A も 47.6% と高止まり。
- **再現(2026-07-09)**: 001 は構造散文化で 0.278（前 run 0.476 より低いが依然 difflib 過大）、002 は**逆方向**——受動→能動・過剰敬語→依頼形の**縮約主導**で 0.222 と実際の改変密度（19 span で語尾・態が可動）より**低め**に出た。difflib は両方向で実態とズレる。
- 出所: (前) rewriter-A/B, naturalness-B ／ (今) rewriter-A(IMP-001再確認), rewriter-B(非対称性=逆方向), naturalness-A(分母問題)
- 提案: (a) 「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を控除。(c) 挿入率を単独併記し del≫ins の削除主導は中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。**(e) `span 単位の実編集語数合計 ÷ 原文字数` を第二指標として meta 併記し、警告判定はこちらを主にする**（縮約主導の過小評価も同時に是正）。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2run` `applied: 2026-07-09-001/002`
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える（Sample A raw106→92.5、taxonomy 例は raw56→71.5 と不整合）。
- **再現(2026-07-09)**: 検出器 4 体が式を各自逆算し **k=45(exp) / raw/(raw+8.6) / N≈61.6** と三者三様の定数を採用、run 002 の score が 69.2 対 86.0 と乖離。run 間比較不能の実害を確認。
- 出所: (前) detector-A, detector-B ／ (今) detector-001(最重要), detector-002(非公開)
- **適用(2026-07-09)**: taxonomy v1.1 §検出出力スキーマに `severity_weighted_score = round(100·(1−exp(−raw/45)), 1)`、`raw = 5·S1 + 2·S2 + 0.5·S3`、k=45 固定 を明記。アンカー raw56→71.2 / raw106→90.5 / raw115→92.2（本日 001 実測 92.2 と一致）で検証。`ai-tell-detector.md §スコア算出` も同式へ書き換え、逆算禁止を明示。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出`

### IMP-003 score_before のフィールド契約が曖昧 `status: done` `hits: 2run` `applied: 2026-07-09`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score 92.5）。レビュアーごとに数値がぶれる。
- **再現(2026-07-09)**: naturalness-001 が「エージェント定義の例値 score_before:71.5 が実 run(92.2) と乖離し誤引用を誘う」と再指摘。
- 出所: (前) naturalness-A ／ (今) naturalness-001
- **適用(2026-07-09)**: taxonomy v1.1 に「score_before = 02_detection.json の meta.severity_weighted_score（再計算禁止）／ score_after = 推敲文へ検出器再走査した同式値」の契約を明文化。`naturalness-reviewer.md` の出力例に「71.5 は形状例示・実 run は 02_detection.json を転記」の注記を追加。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run`
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
- **再現(2026-07-09)**: 両検出器が E-2 文末単調（文書レベル）を単一 start/end に係留せざるを得ず「場当たり」と自己申告。rewriter-001 は「E-2 が単一 span 係留で 1 edit にしか見えず、実際の変奏 5 箇所以上と 1:1 で追えない」と指摘（naturalness の残存計測がずれる）。
- 出所: (前) detector-B, detector-A ／ (今) detector-001, detector-002, rewriter-001
- 提案: `span_type: "contiguous"|"scattered"|"document"`（または `scope:"document"`）と scattered 用 `occurrences: [[s,e],...]` / document 用 `evidence_positions:[]`・`affects_spans:[]` を追加。density は重複・locator を除いた実 AI クセ文字数ベースと定義。※ density の union 化・文書レベル除外は v1.1 で先行適用済み（IMP-002）。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。
- **再現(2026-07-09)**: detector-002「実施されることとなりました=A-8+A-6、ご了承いただく必要がございます=I-3+過剰敬語 → secondary_categories 配列が欲しい」、detector-001「というアプローチです=A-10+A-13+B-2 の三重帰属、primary/secondary 優先順位規則が無いと category_summary がぶれる」、rewriter-001「チェーン編集の before を原文素/連鎖後どちらで書くか未規定 → auditor 原文照合で誤検知しうる（chained_from フィールド提案）」。
- 出所: (前) detector-A, rewriter-A/B, naturalness-A, fidelity-A ／ (今) detector-001, detector-002, rewriter-001
- 提案: 「1 span = 主分類 1 finding」を基本とし `secondary_categories:[...]`（旧 merged_findings）を許容。category_summary は「findings の primary category 先頭文字を集計」と注記。**チェーン編集の diff は `before_raw`（原文素片）と `before_ctx`（連鎖後）を分離、または `chained_from:[finding_id]` を付与**。
- 影響: 全 .md のスキーマ節, `japanese-style-rewriter.md`（diff スキーマ）

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: done` `hits: 2run` `applied: 2026-07-09`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。
- **再現(2026-07-09)**: 本 run では両レビュアーが実際に `ai-tell-detector` をサブエージェント実呼び出しして score_after を得た（001: 92.2→7.4、002: 86.0→0.8）。経路が機能することを実証。002 のレビュアーは子検出器が背景実行で一旦中断→再開で完了、という運用上の注意も判明。
- 出所: (前) naturalness-A ／ (今) naturalness-001, naturalness-002（実走査で実証）
- **適用(2026-07-09)**: `naturalness-reviewer.md §処理` に「検出器をサブエージェントとして実呼び出し・手動照合禁止（IMP-006）」を明記。score_before の再計算禁止も併記（IMP-003）。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

### IMP-007 公的文書ジャンルの免責層が無い `status: ready` `hits: 1run(3agent)`
- 症状: taxonomy は A-1「において」を一律 S1、過剰敬語・E-2 を無条件計上するが、自治体通知では「下記の期間において」「お願い申し上げます」「賜りますよう」は AI 固有でない正当な officialese。SSOT 厳守だと A-1×3 だけで等級が D に落ちる。
- 実測(2026-07-09-002): 検出器は口頭指示で定型敬語を除外して A 判定に到達したが、除外がプロンプト依存で毎回口頭指示するのは危険。
- 出所: detector-002, rewriter-002, naturalness-002（同一 run 3 agent＝hits は 1run 扱い、次 run 再現で ready 昇格見込み）
- 提案: (a) taxonomy に `genre_exempt` フラグ／ジャンル別 severity 補正（public_document では A-1・過剰敬語を S2/S3 に減格）。(b) 「文書の開閉部（挨拶・結び）に位置し実質情報を運ばない」定型句のホワイトリスト（位置条件付き）。(c) 除外語辞書を web-service-spec 相当のジャンル表に持たせる。
- 影響: `ai-tell-taxonomy.md`, `ai-tell-detector.md`, `naturalness-reviewer.md`, 新規ジャンル表

### IMP-008 鉤括弧の「引用/強調」判定主体が未定義（#3 の責任境界） `status: ready` `hits: 1run`
- 症状: fidelity #3 は項目名「直接引用」だが判定基準は「鉤括弧内一字一句保存」。この隙間で推敲役が「外部引用でない強調鉤括弧だから改変可」と単独自己判定できてしまう。run 001 f004「…対応することができる」→「…できる」で顕在化（監査は precautionary fail、オーケストレーターが強調句と裁定し override）。
- 出所: fidelity-001, rewriter-001
- 提案: (a) #3 を「外部出典の直接引用（不可）」と「筆者定義・強調の鉤括弧（可・ただし意味等価が条件）」に二分。(b) いずれにせよ鉤括弧内編集は**監査役／オーケストレーターの事前承認を要す**と明文化（推敲役の単独判断を禁止）。playbook に J-2 鉤括弧 3 分類（外部引用/筆者定義/強調）を追加。
- 影響: `content-fidelity-auditor.md §#3`, `rewriting-playbook.md`, `SKILL.md §禁忌`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 001。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B
- **A-5b 可能変種「〜することが可能になる/可能となる」** 可能＋状態化の複合。実例(2026-07-09-001):「可視化することが可能になります」「対処することも可能となります」。想定 S1。 `hits: 1` 出所 detector-001 ／ **taxonomist 判定: 候補（有望・A-5 の独立サブ、再現2回目で即昇格推奨）**。taxonomy 拡張候補欄に登録済み。
- **A-6b 官僚的決定叙述「〜こととなりました/こととなります」** 受動(A-8)＋状態化(A-6)の複合。実例(2026-07-09-002):「更新作業が実施されることとなりました」。想定 S2（公的文書で人間も慣用のため S1 にしない）。 `hits: 1` 出所 detector-002 ／ **taxonomist 判定: 候補**。登録済み。
- **「〜ていく」冗長進行形** 英語 progressive 直訳疑い。実例(2026-07-09-001)「解説していきます」／(2026-06-12-001)「ドライブしていく」= **異なる run で 2 回出現**。ただし想定 S3・人間使用率が極めて高く、**taxonomist 判定: 昇格させない方が安全（誤検出温床）**。昇格するなら「予告定型」限定が条件。登録済み。
- **I-3a/I-3b（儀礼依頼 vs 実行義務要請）** 「ご了承ください」（儀礼＝簡潔化フリー）と「申請を済ませてください」（実行義務＝根拠事実の同段保持が必須）。 `hits: 1` 出所 detector-002, fidelity-002 ／ **taxonomist 判定: 分類昇格ではなく監査/playbook のルール化**（AIっぽさの強度差でなく fidelity 上の扱い差のため。分類純度を保つ一般原則）。→ IMP-005 系ではなく auditor 運用へ。

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019（並列→基盤の序列混入）はこの項が無く #5/#11 へ漏れ込んだ。`status: ready` `hits: 2run` 出所 (前)fidelity-A ／ (今)fidelity-001 で**再現**（run 001 f019「システムは…大きく寄与する」→「システムほど…高まる」で比例・相関を混入。#14 が #5/#6/#14 と三つ巴に多重発火）。→ **#14 を構文置換由来毀損の主因ラベルに正規化し、#5/#6 を「#14 の内訳」として従属マーク**する従属関係をスキーマに持たせる（fail の重複計上でスコアが歪むため）。
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。`status: ready` `hits: 2run` 出所 (前)fidelity-B ／ (今)fidelity-002 が縮約主導 run で全削除 span に適用し接続詞・待遇ラッパーのみと確認。→ **度合い・量の修飾語（「大きく」等）を「情報側」に明示追加**（現二分判定では程度副詞がボイラープレート側に誤分類され得る。run 001「大きく」欠落がこの穴。出所 fidelity-001）。
- **構造/待遇編集に紛れた modality 軟化の検査**（#14 の対サブ項目）: 「必要がございます→ください」等の modality 一段軟化を、順序尺度＋根拠事実の同段保持で判定。`status: ready` `hits: 1` 出所 fidelity-002（run 002 で pass 境界を精査）, fidelity-001（#14 対概念として提案）。
- 「情報を含む削除 vs ボイラープレート削除」二分判定: 削除 span に (a)数値/固有名詞/日付 (b)条件/因果節 (c)固有の例示 **(d)度合い・量の修飾語** を含めば情報欠落、挨拶/CTA/装飾/自己言及のみならボイラープレート。出所 fidelity-B, fidelity-001
- #5論理関係 と #11情報追加 の責任境界を一意化（主因項目を 1 つに正規化）。出所 fidelity-A
- modality 強度を順序尺度化（要請/推奨/義務/必須）。I-3 依頼形化の判定は「①実行行動が不変 ②必要性の根拠事実が近接 span に保持 ③レジスター上『てください』が指示として機能」の 3 条件 AND に規格化。出所 fidelity-A, fidelity-002

### playbook レシピ追補
- **C-5 絵文字削除後の文末/区切り吸収ルール**（句点で吸収 or 削除のどちらか明記）。出所 rewriter-B
- **D 系結びは削除一択でなく「最小着地文を残す」**（減らしすぎ下限）。実例: B の「気軽に始めてみてください」。出所 rewriter-B, naturalness-B
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**という例外則。出所 rewriter-A
- **原文が元から推量の D 系は推量を保持**（「断定へ」の一律処方の例外）。出所 rewriter-A
- **A-10/A-6 は「主語だけ触り述語構造（格・量化・因果方向）は温存」**。程度副詞を保持したまま万能動詞を開くレシピを明示（例: 大きく寄与する→大きく貢献する／支える。比例構文「ほど〜」へ逃げない）。実例: run 001 f019 の毀損。`status: ready` `hits: 1` 出所 rewriter-001, fidelity-001
- **複数 finding が 1 文末に重なる場合は「最小侵襲の finding を単独先行適用」**（run 001 は D-1 の語尾だけ直せば足りたのに A-10 まで動かして毀損。D-1 単独処理なら初版時点で毀損ゼロ）。`status: ready` `hits: 1` 出所 rewriter-001
- **A-8 能動化の例外「行為者が住民・法令の受動は保持」**（(a) 主語化で責任所在が変わる「申請が受理されます」、(b) 制度・法令主語の非情物受動「条例により定められています」）。併せて頻出の**「Xが〜される→Xを〜する」格転換（が→を）能動化**を A-8 独立エントリ化。`status: ready` `hits: 1` 出所 rewriter-002
- **E-2 敬体変奏の選択肢に「依頼形（〜ください）」を追加**（現状は でしょう／体言止め／ます のみ。公的文書では依頼形が最有効の変奏）。`status: ready` `hits: 1` 出所 rewriter-002
- **A-10 の置換先を複数用意し近接反復を回避**（「このアプローチ」も「本手法」も一律「この方法」に畳むと H-3 誘発。この方法／この考え方／固有名詞回帰 に分散）。**B-2 漢語+「的」置換の F-4 誘発**にも注意（同一語を 2 箇所以上で漢語+的にすると F-4 クラスタ発生。片方を「いまの/現在の」等へ分散）。`status: ready` `hits: 1` 出所 naturalness-001, rewriter-001

### naturalness 判定の精緻化
- 過推敲シグナルの定量化（敬体/常体混入は文末形態の二値カウントで機械検出）。出所 naturalness-A
- クラスタ系 finding（B-2 密集・C-1 列挙）はクラスタ崩壊時に個別 severity を降格するルール。出所 naturalness-A
- E-2 文末単調の到達可能ライン緩和（体言止め1箇所以上で合格、文体維持制約下の過推敲回避）。出所 naturalness-B
- 絶対残存数ガードを grade 表に組込み（改善率が高くても S1 が1件でも C 以下）。`status: ready` `hits: 2run` 出所 (前)naturalness-A/B ／ (今)naturalness-002（短文・定型文で改善率が過大に出るため「public_document は絶対残存 S1=0 かつ S2≤1 を A の必須条件」と再提案）。
- **E-2 文末バリエーション比の数値指標化**（ユニーク文末型/総文数）。閾値超過時のみ S2、境界域は S3 へ自動降格する連続スコアリングで等級ブレを削減。`status: ready` `hits: 1` 出所 naturalness-002
- **依頼形（〜ください）は敬体として扱う**を敬体判定に固定ルール化（義務叙述→依頼形の正当な自然化を「くだけ過ぎ」と誤検知しないため）。→ taxonomy v1.1 §style に先行明記済み。出所 naturalness-002
- 検出器の**共起見逃し**: run 001 で「欠かせない要素となっています」を初回 A-6 のみ拾い D-4 ハイプ「欠かせない」を見逃し（再走査で顕在化）。→ 状態叙述と共起するハイプ語彙は別 finding として二重計上。出所 naturalness-001

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 1run(3agent)`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B, fidelity-A, naturalness-A

### rewriter diff スキーマ追補
- **`revision` と `rollbacks[]` を 03_rewrite_diff.json の正式スキーマに昇格**（監査後にどの edit が撤回・差し替えされたかを naturalness-reviewer/オーケストレーターが追える）。run 001 のロールバック再推敲で rewriter が暫定追加した（trigger・failed_checks・resolution を保持）。`status: ready` `hits: 1` 出所 rewriter-001

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。`status: ready` `hits: 2run` 出所 (前)detector-A ／ (今)両検出器が全 offset を raw と突き合わせ検証（001「全 offset verified」・002「All 19 offsets verified」）＝実運用で機能。
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B
- **B-2 の業界標準語ホワイトリストがジャンル依存で主観的**（オブザーバビリティ/メトリクス/トレーシング/テレメトリ/レイテンシ等を除外したが SSOT 例外は Transformer/API/SDK/トークンのみ）。ジャンル別許容カタカナ辞書が必要。`status: ready` `hits: 1` 出所 detector-001（IMP-007 と連動）
