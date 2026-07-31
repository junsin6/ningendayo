# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-07-31（run 001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done` `hits: 2run` 適用: 2026-07-31-001/002
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・冗長構文の純削除で機械的に膨張。06-12 Sample B は 54.6% で誤発火。07-31-002 も 0.317 で 30% 超警告（実際は del 0.226/ins 0.091 の削除主導・fidelity=pass・自然度 A）。
- 出所: rewriter-A/B, naturalness-B（06-12）＋ rewriter-B, naturalness-B（07-31 再現）
- 提案: (a) del率/ins率を分離計上。(b) del≫ins の削除主導は中断対象から除外。(c) 50% 中断は「意味改変 edit 比率」基準へ。
- **適用（2026-07-31）**: `rewriting-playbook.md §変更率の数え方` に del/ins 分離とジャンル注記、`SKILL.md §総合判定` に override accept 行を追記。`japanese-style-rewriter.md` に diff meta へ del_rate/ins_rate 分離記録を必須化。
- 影響ファイル: `rewriting-playbook.md`, `SKILL.md`, `japanese-style-rewriter.md`

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2run` 適用: 2026-07-31-001/002
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き解像度が消える。07-31-001 は raw 87 → 105.7 で 100 に飽和、改善率の絶対比較が不能。
- 出所: detector-A/B（06-12）＋ detector-A/B, naturalness-A/B（07-31 再現）
- 提案: 飽和しにくい正規化を SSOT 明記。分母を確定。raw_weighted_score を併記。
- **適用（2026-07-31）**: taxonomy §検出出力スキーマ に正規化式 `severity_weighted_score = round(100*(1-exp(-raw/K)), 1)`（K=60）を明記、`meta.raw_weighted_score`（正規化前 raw）を必須フィールド化。`ai-tell-detector.md §スコア算出` に式と K を反映。IMP-003 も本適用で解消（score_before 契約明記）。
- 影響: `ai-tell-taxonomy.md`, `ai-tell-detector.md`, `naturalness-reviewer.md`

### IMP-003 score_before のフィールド契約が曖昧 `status: done` `hits: 1run` 適用: 2026-07-31（IMP-002 と同時）
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。
- 出所: naturalness-A（06-12）
- **適用（2026-07-31）**: `naturalness-reviewer.md` に「score_before = 02_detection.json の meta.severity_weighted_score」「score_after は同じ正規化式・同じ K で算出」を明記。両 naturalness agent は 07-31 で既に meta.severity_weighted_score を使用しており実務追認。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: done` `hits: 2run` 適用: 2026-07-31-001/002
- 症状: 絵文字分散・文末単調・まず…最後に・接続詞連鎖は文書レベルパターン。単一 start/end では locator が歪み、推敲役へ「この数文字を直せ」と誤シグナル。
- 出所: detector-A/B（06-12）＋ detector-A/B, rewriter-A, fidelity-A（07-31 再現、横断的）
- 提案: `scope: "span"|"document"` と `occurrences: [[s,e],...]` を追加。density は重複除去後のユニーク被覆文字数と定義。
- **適用（2026-07-31）**: taxonomy §スキーマ に `scope`（既定 "span"）と任意 `occurrences[]` を追加。`scope:"document"` の finding は span を代表アンカーとし、推敲役は reason/occurrences が列挙する全 span を改変対象とする旨を detector/rewriter に明記。ai_tell_density を「ユニーク被覆文字数 / 全体」と定義。
- 影響: `ai-tell-taxonomy.md`, `ai-tell-detector.md`, `japanese-style-rewriter.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリに該当（I-4＋B-2＋I-1、A-5＋A-10＋B-2 等）。edits/findings が 1:1 前提で category_summary が実態とズレ、重複 span で density も不安定。反復系（同一構文×5）を 5 finding に個別化すると detected_count が反復回数で膨張。
- 出所: detector-A, rewriter-A/B, naturalness-A, fidelity-A（06-12）＋ detector-A/B（07-31 再現）
- 提案: 「1 span = 主分類 1 finding」を基本、`merged_findings:[...]` を許容。反復系は `repetition_group` id で束ね代表 finding＋occurrences 化。detected_count は「独立問題数」と「span 総数」を分離表示。category_summary は findings の category 先頭文字集計と注記。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だが、サブエージェントからサブエージェントを起動する経路が無く、両 naturalness agent とも手動照合に退行（07-31 で明確に再現）。score_after は正規化式逆算の推計値。
- 出所: naturalness-A（06-12）＋ naturalness-A/B（07-31 再現）
- 提案: (a) オーケストレーターが推敲後に `ai-tell-detector` を別ステップで `03_rewrite.md` に対し再実行し `05_*` の score_after を確定させる（reviewer は判定に専念）。(b) IMP-002 の raw_weighted_score 併記で改善率のスケール不変性を担保。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md §並列検証`
- 備考: ハーネス構造の制約のため、次回 run でオーケストレーター側にワークフロー変更として適用予定。

### IMP-007 ジャンル条件付き severity 軸が無い（genre-conditional severity）`status: ready` `hits: 2run`
- 症状: taxonomy の severity は「一般散文で単発でも決定的か」で固定（A-1/A-2/A-5=S1）。しかし公的文書では「支給額については」「ホームページにおいても」の単発は標準表現で S1 の定義「一度で AI 確信」が成立しない。detector が場当たりで severity を上書きせざるを得ず、レビュアーと基準がズレる。SEO ブログでは逆に絵文字・CTA が正常。
- 出所: detector-B, naturalness-B（07-31）＋ 06-12 の「クラスタ崩壊時の severity 降格」「定着カタカナ B-2 半免責」と同根
- 提案: taxonomy に `genre` 軸（column / report / blog / public / tech）を導入し severity をジャンル条件付きに（例: A-2 は public では単発 S3、3回+ で S2）。ジャンル別「正常パターン表」（public の ください／ございません、blog の絵文字/CTA）を SSOT 化。naturalness も同表で genre-normal を非減点に。
- 影響: `ai-tell-taxonomy.md §深刻度`, `ai-tell-detector.md`, `naturalness-reviewer.md`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **A-14 「〜のではなく、〜」対比構文（not A but B 翻訳調）** 英語 `not A but B` の直訳。実例1: 「クラウドに送信する**のではなく**、…エッジで処理を行う」(07-31-001)。`hits: 1` 出所 detector-A。※実例2 を次 run で収集（翻訳調濃いめのジャンルで再現待ち）。
- **A-15（候補）受動＋形式名詞＋状態化の三重冗長「〜されることとなっております／〜されることとなりました」** 公的文書 AI の決定的シグネチャ。A-6＋A-8＋I-1 の合成。実例1「支給されることとなりました」実例2「支給されることとなっております」(共に 07-31-002)。`hits: 1(2実例)` 出所 detector-B。
- **「〜のです／〜のである」説諭文末** 解説記事系 AI に頻出、教え諭すトーン。実例「削減することができる**のです**」(07-31-001)。`hits: 1` 出所 detector-A。E/G とは別軸。
- **D-8（候補）「ぜひ、この機会に〜してみては」読者誘導 CTA** D-1「いかがでしょうか」と共起するブログ/解説 CTA 定型。実例「**ぜひ、この機会に**エッジ…触れてみては」(07-31-001)。`hits: 1` 出所 detector-A。既存 D-7 候補（ブログ結び）と統合検討。
- **I-3 public 亜種「〜いただく必要があります」指示回避** 相手の行為の必要性を客観描写して指示責任を回避。人間の自治体文書は「ご確認ください」と直接指示。実例「ご確認いただく必要があります」「ご返送していただく必要があります」他計5回(07-31-002)。`hits: 1(5実例)` 出所 detector-B, rewriter-B。I-3 に public 注記で対応可。
- **C 系 redundant restatement** 叙述と箇条書きが同内容を二重記載。実例: 06-12-001。 `hits: 1` 出所 detector-A。
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「〜してみてはいかがでしょうか」。 `hits: 1` 出所 detector-B（06-12）。
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式。 `hits: 1` 出所 detector-B（06-12）。

### fidelity チェックリスト追補
- **要請強度の保存＝帰結節保持の原則** `status: ready` `hits: 1(2実例)` 出所 fidelity-B（07-31）: 「〜する必要がある → ください」変換は、不利益結果の帰結節（「受け取れない場合があります」等）が残れば実務的義務強度は不変とみなし pass。帰結節ごと削除して ください 化したら毀損。法的義務語・罰則を伴う要請の ください 化は別基準（毀損寄り）。→ 項目 7(modality) にサブ基準として昇格候補。
- **行為者補完の是非＝一意確定テスト** `status: ready` `hits: 1` 出所 fidelity-B（07-31）: A-8 能動化は発出主体が文脈上一意に確定する受動のみ許容。複数主体が介在しうる受動の能動化は毀損。担当課名等、原文に無い固有の行為者名を補うのは項目 11 違反。
- **verdict/status の enum 未定義** `status: ready` `hits: 1` 出所 fidelity-A（07-31）: checks[].status に pass 以外の語彙（fail/warn 等）が未定義。enum 明記＋ボーダーライン用に `pass_with_note` とトップレベル `watch_edits[]`（毀損ではないが要監視 finding_id）を追加すべき。rollback_edits/finding_id のキー名不一致も統一（rollback_finding_ids）。
- **評価語 vs 事実語の切り分け基準** `status: ready` `hits: 1` 出所 fidelity-A（07-31）: D 系ハイプ語・F 系程度副詞の除去は taxonomy 上サンクションされるが、厳密適用すると check 6/7/10 で機械的に毀損判定されうる。「除去対象が事実・数値・固有名詞・引用・論理・要請強度に該当するか」を毀損の必要条件として定義に明文化。
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019。`status: ready` `hits: 1` 出所 fidelity-A（06-12）。
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」。`status: ready` `hits: 1` 出所 fidelity-B（06-12）。
- 文書レベル finding（scope:document）の監査手順が未定義。span 突合になじまないため論理関係(check 5) への波及観点で検証手順を追記。出所 fidelity-A（07-31）。

### playbook レシピ追補
- **公的文書ジャンルのレシピ不在** `status: ready` `hits: 1(横断)` 出所 rewriter-B, naturalness-B（07-31）: 「残すべき定型敬語リスト（ございません/当日消印有効/お願いいたします/におかれましては）」と「崩すべき冗長構文リスト（〜とされております/〜取り扱いとなります）」の切り分け表が無い。過推敲で定型敬語まで削ると格が壊れる。IMP-007 と連動。
- **I-3 反復崩しの「別形分散」バリアント** `status: ready` `hits: 1` 出所 rewriter-B（07-31）: I-3 は「すべきだ or 具体勧告」の1択で、公的文書では ください に全滅収束し新たな機械反復を生む。「ご確認ください/ご返送ください/お願いいたします/くださいますようお願いいたします」へ分散するバリアント表が要る。
- **I-4 行為者不在時の但し書き** `status: ready` `hits: 1` 出所 rewriter-A（07-31）: I-4「主語・動詞で具体化」は、原文に行為者が無い技術解説では主語補完が新情報追加になり鉄則違反。「行為者が原文に無い場合は断定形（〜必要だ/〜要る）への変換に留め、主語補完は禁止」を追記。
- **D-3 列挙予告公式のレシピ欠落** `hits: 1` 出所 rewriter-A（07-31）: 「〜について整理します／次のように整理できる → 予告を削除し直接列挙 or 項目数を叙述」を D 表に追加。
- **A-8 能動化での行為者補完指針** `hits: 1` 出所 rewriter-B（07-31）: 発行主体が原文に無い場合、擬似主語を足さず謙譲能動（「お送りします」）で処理する例を追記。
- **B-1 併記削除でタイトル/見出し既出を初出カウントに含めるか** `hits: 1` 出所 rewriter-A（07-31）。
- **E-2 体言止めのジャンル可否注記** `hits: 1` 出所 rewriter-B（07-31）: 公的文書では体言止めが硬すぎ/稚拙に振れるため断定「です」で変奏。ジャンル別可否をE-2に注記。
- **変更率の約物カウント規約** `hits: 1` 出所 rewriter-A（07-31）: 読点・記号の増減を del/ins に含めるか明文化＋difflib 補助スクリプトで再現性向上。
- C-5 絵文字削除後の文末/区切り吸収ルール。出所 rewriter-B（06-12）。
- D 系結びは「最小着地文を残す」。出所 rewriter-B, naturalness-B（06-12）。
- 機能が必要な接続詞（しかしながら）は削除でなく変奏。出所 rewriter-A（06-12）。
- 原文が元から推量の D 系は推量を保持。出所 rewriter-A（06-12）。

### naturalness 判定の精緻化
- **residual_findings に category+span を必須化** `status: ready` `hits: 1` 出所 naturalness-A（07-31）: 現行は S1/S2/S3 のカウントのみで、round_2 推敲役が「どのクセが残ったか」を特定できない。`residual_detail[]`（category, span）を必須に。
- **I-4/I-3 同族置換は残存扱い** `status: ready` `hits: 1` 出所 naturalness-A（07-31）: 「求められる→必要」の同一 taxonomy 族内置換は残存とカウントすべき（今回 S3 に計上）。playbook/detector に注記。
- **grade に S3 絶対残存数ガード** `status: ready` `hits: 2run` 出所 naturalness-A/B（06-12）＋ naturalness-A（07-31 再現）: S1/S2 0 でも S3 多数なら A になり得るのは定義矛盾。S3 密度ガードを grade 表へ。
- **grade の過推敲シグナル重み付け＋del主導減免** `status: ready` `hits: 2run` 出所 naturalness-A（06-12）＋ naturalness-B（07-31）: change_rate 30%超が自動で over-polish 1個に数えられるが del 主導圧縮を減免する条項が無い（IMP-001 を naturalness 側で吸収）。文体崩れ1件と change_rate 超を同一重みで数えるのは粗い。
- grade D「深刻な過推敲」の閾値未数値化。B と C が同時成立時の優先順位ルール無し。出所 naturalness-B（07-31）。
- クラスタ系 finding のクラスタ崩壊時 severity 降格ルール。出所 naturalness-A（06-12）。
- E-2 文末単調の到達可能ライン緩和（体言止め1箇所以上で合格）。出所 naturalness-B（06-12）。

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 2run`
- ルーティン・モチベーション・データドリブン・メリット 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B, fidelity-A, naturalness-A（06-12）＋ naturalness-A（07-31「メリット」2回残存として再現）。IMP-007 の genre 表と統合可。

### detector 実装
- raw_weighted_score（正規化前）併記 → IMP-002 で適用済み。
- category_summary は全10キー必須（キー欠落を 0 とみなすか未評価か曖昧）。出所 detector-A（07-31）。→ IMP-002/004 適用と同時にスキーマ例で全キー明示。
- start/end 自己検証（regex マッチ位置と text_span 一致を assert）。出所 detector-A（06-12）。
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B（06-12）。
