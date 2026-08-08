# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-08-08（run 001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample 2026-06-12-B は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。
- 再現: 2026-08-08 の両 run で裏取り。**run 001**（rewriter-A）: 体言止め化 f002 の語順再構成だけで削除 121 字計上、挿入 51 と非対称。**run 002**（rewriter-B）: 純語句置換のみ（構造編集なし）で del 107≫ins 31 の削除主導にもかかわらず change_rate 0.207 と正直な値に収束 → 「膨張は C 系構造編集・広域削除に固有」という診断を別ジャンルで確証。
- 出所: rewriter-A/B(0612), rewriter-A/B(0808)
- 提案: (a)「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を change_rate から控除。(c) 挿入率を単独併記し del≫ins の削除主導ケースは中断対象外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。(e) diff スキーマに edit ごとの before/after 文字数合計を併記し difflib 値との乖離を可視化。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: ready` `hits: 2run` → **適用: 2026-08-08-001/002**
- 症状: 正規化式が SSOT に無く run 間で score がぶれる。
- 再現: **detector-A(0808)** が式不在のため独自に `100*(1-exp(-raw/44.6))`（taxonomy 例 raw56→71.5 から逆算）を採用。さらに **naturalness-B(0808)** が run002 で before raw=19 → 式適用 34.7 なのに meta が 37.1（差+2.4）と不一致を発見。検出器側が ai_tell_density を加算している疑い。**score_before と score_after を同一式で出さないと改善率が歪む**。
- 出所: detector-A/B(0612), detector-A(0808), naturalness-B(0808)
- 適用内容: `ai-tell-taxonomy.md §検出出力スキーマ` と `ai-tell-detector.md §スコア算出` に式 `raw = ΣS1×5 + ΣS2×2 + ΣS3×0.5`, `severity_weighted_score = round(100*(1-exp(-raw/44.6)), 1)`（density は加算しない）を確定。

### IMP-003 score_before のフィールド契約が曖昧 `status: ready` `hits: 2run` → **適用: 2026-08-08-001/002**
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 が誤引用リスク）。
- 再現: **naturalness-A(0808)** がスキーマ例のダミー 71.5 を誤引用する恒常リスクを再指摘。今回は指示で meta.severity_weighted_score=75.6/37.1 を採用。
- 出所: naturalness-A(0612), naturalness-A(0808)
- 適用内容: 「score_before = 02_detection.json の meta.severity_weighted_score」を SSOT・naturalness-reviewer.md に明文化。スキーマ例のダミー値に「（例示値・実運用では meta を引く）」注記。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run`
- 症状: 分散パターンを単一 start/end で代表位置に固定するしかなく density が歪む。
- 再現: **detector-A(0808)** で E-2（文末単調・13文全て）と H-1（しかし/これにより/このように 分散）が該当。
- 提案: `span_type: "contiguous"|"scattered"|"document"` と scattered 用 `occurrences: [[s,e],...]`。density は重複・locator を除いた実 AI クセ文字数ベース。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリに該当し category_summary が過小評価。
- 再現: **detector-A(0808)**「実現することができます」が A-5＋A-10 同時該当、主分類 A-10 一本化で A-5 密度を 1 件過小評価。
- 提案: 「1 span = 主分類 1 finding」を基本とし `merged_findings: [...]` を許容。category_summary は「findings の category 先頭文字を集計」。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だがサブエージェントは sub-subagent を起動できず手動再適用 → 閾値未満パターンの計上可否で raw が ±2〜3 揺れる。
- 再現: **naturalness-A(0808)** で再現。手動 taxonomy 再適用で raw を積算。
- 提案: (a) オーケストレーター側で `ai-tell-detector` を推敲後テキストに実走査し score_after を確定する経路を必須化（reviewer は残存内訳と過推敲判定に専念）。(b) 少なくとも正規化式（IMP-002 適用済み）を共有し手動再適用の揺れを縮小。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

### IMP-007 A-8 能動化に随伴する span 外の助詞変更が規約化されていない `status: ready` `hits: 1run(2agent)`
- 症状: A-8 受動→能動（f003/f009/f014）は検出 span が述語のみでも、文法上ほぼ必然的に主語助詞「が→を」を span 外で変更する。span-grounded 規約にこの「文法的に随伴する隣接編集」を許容する明文が無く、fidelity 監査で「span 外改変」と誤指摘される恐れ。
- 出所: rewriter-B(0808), fidelity-B(0808)（run002 で 3 件再現、横断 2 エージェント）
- 提案: `edit` に `grammatical_entailment`（随伴する最小限の隣接変更）を許容する注記。fidelity #9 に「能動化後の動作主が文脈・丁重体と整合するか」の assert 手順を追加。
- 影響: `japanese-style-rewriter.md`, `content-fidelity-auditor.md`, スキーマ節

---

## P2 — 分類・レシピ・チェックリスト

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** `status: ready` `hits: 2run` → **適用: 2026-08-08-001**
  - f019（並列→基盤の序列混入, 0612）で顕在化。**fidelity-A(0808)** が「f019 型 edit の有無を毎回明示的に確認したが、#14 が独立項目でないと監査痕跡が #5/#11 の pass note に埋没する」と再指摘。#5論理関係 と #11情報追加 の責任境界問題の根本解でもある。適用形＝13→14 項へ昇格。
- **削除専用サブチェック（deletion-recall test）** `status: ready` `hits: 2run`
  - **fidelity-A(0808)** が f006/f007 で 2 回目の実適用。f007 型（同義反復副詞の削除）は「情報 vs ボイラープレート」二分の中間ケース。二分判定に「(d) 直前後の語と同義反復の修飾語＝ボイラープレート扱い」を追加提案。
- **modality 強度を順序尺度化（不要＜依頼＜推奨＜必要＜必須）** `status: ready` `hits: 2run`
  - **fidelity-B(0808)** が run002 で 2 例目。f011（必須→依頼形）f007（義務→依頼）の弱化、f012（推量→断定）の強化、f001「求められます」の逆変換が #7 の粗い pass/fail では区別できない。「原値との段差 ±1 まで許容、±2 以上は毀損」等の閾値化を提案。
- **#15 発話類型（illocution）保存** `status: candidate` `hits: 1`
  - **fidelity-B(0808)**: 公的文書で「必要がございます」（要件の通知）→「ください」（依頼）へ移すと発話類型がシフト。今回は含意保存で pass だが、要件通知を単なるお願いへ落とすと citizen の遵守インセンティブが変わりうる。#7 に「発話類型が反転していないか」を明記 or #15 新設。
- **#7 行政/公的主体の断定化＝法的含意生成の副チェック** `status: candidate` `hits: 1`
  - **fidelity-B(0808)**: f012 は G-1 婉曲除去だが、行政主体が主語のとき推量（〜と考えております＝期待表明）→断定（〜いただけます＝品質保証）へ変換すると達成義務を負わない期待を保証に変えうる。「公的主体の断定化は原文が推量・希望・見込みの場合に限り毀損候補」の主体依存サブルールを提案。
- **技術文書 B-2「安易に開くと別義化する危険語」ウォッチリスト** `status: candidate` `hits: 1`
  - **fidelity-A(0808)**: `アーキテクチャ→構造` は設計思想(architecture)と物理/論理構造(structure)が別概念になりうる境界語。定着カタカナ語免責リスト（開いてよい）とは逆向きの「開くと危険な語」（アーキテクチャ/プラットフォーム/モデル/エンジン 等）を #12 付帯リストに。
- **A-5 可能形連鎖の書き分けガード（達成状態 vs 潜在能力）** `status: candidate` `hits: 1`
  - **fidelity-A(0808)**: 「可能となっています（達成済み状態）」と「できる（潜在能力）」を書き分ける原著意図がありうる。#7 modality/#8 相のサブ観点に「達成状態と潜在能力の書き分けが原文で機能していないか」を明文化。

### playbook レシピ追補
- **C-5 絵文字削除後の文末/区切り吸収ルール**（句点吸収 or 削除を明記）。出所 rewriter-B(0612)
- **D 系結びは削除一択でなく「最小着地文を残す」**。出所 rewriter-B(0612), naturalness-B(0612)
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**。出所 rewriter-A(0612)
- **原文が元から推量の D 系は推量を保持**。出所 rewriter-A(0612)
- **E-2「敬体を保つ体言止め」の変換コスト区別** `status: candidate` `hits: 1`
  - **rewriter-A(0808)**: 「文末だけ触る低コスト体言止め」と「語順再構成が要る高コスト体言止め」を playbook に区別例示。後者は change_rate を膨張させる（IMP-001 と連動）。
- **公的文書の過推敲下限（register floor）** `status: candidate` `hits: 1`
  - **rewriter-B(0808), naturalness-B(0808)**: 自治体お知らせで残す下限＝「お願い申し上げます／賜りますよう／ご了承ください／ご持参ください／場合がございます／いたします」。除去対象の AI クセ敬語＝「〜いただく必要がございます(I-3)／〜ものと考えております(G-1)／〜することとなりました(A-6)／〜が行われております(A-8)」。二分ヒューリスティック: **「敬意の格を上げる語」は残し、「行為主体を消す/要請を回りくどくする装飾」は AI クセ**。
- **suggested_fix はヒント、意味等価を害する平板化より最小補正を優先** `status: candidate` `hits: 1`
  - **rewriter-A(0808)**: f017「となりつつある(becoming)」を detector 提案「です」で平板化すると変化ニュアンスを失う。playbook A-6 但し書き「になっている（変化を言う時のみ）」を根拠に「になりつつあります」を採用。detector の suggested_fix と fidelity（鉄則1）の競合時の優先順位を明記すべき。

### naturalness 判定の精緻化
- 過推敲シグナルの定量化（敬体/常体混入は文末形態の二値カウントで機械検出）。出所 naturalness-A(0612), 再現 naturalness-A/B(0808)（文末型分散を実カウント）
- クラスタ系 finding（B-2 密集・C-1 列挙）はクラスタ崩壊時に個別 severity を降格するルール。出所 naturalness-A(0612)
- **E-2 到達可能ラインの genre 条件化** `status: ready` `hits: 2run`
  - naturalness-B(0612)「体言止め1箇所以上で合格」に対し **naturalness-B/rewriter-B(0808)** が公的文書では体言止めが register 違反になりうると指摘。**公的文書では体言止めでなく「依頼形/丁重体の相互変換」1件で E-2 合格**とする genre 例外が必要。
- 絶対残存数ガードを grade 表に組込み（改善率が高くても S1 が1件でも C 以下）。出所 naturalness-A/B(0612), 再現 naturalness-A/B(0808)
- **等級表: S1 の再格付け一発で accept/rewrite が反転する（規則欠如）** `status: candidate` `hits: 1`
  - **naturalness-A(0808)**: 原 f009 は A-10 を S1 で立てたが suggested_fix は冗長可能形の除去のみで抽象主語構文は残存。厳密再走査で A-10 が再発火し得るが決定的増幅子（ことができる）消失で S1 性喪失と判断し S1→S2 降格。S1 のままなら grade C / rewrite_round_2 に反転。1 span の主観的重み付けが accept と再推敲を分ける。降格可否の規則を等級表に定義すべき。
- **発火閾値割れ item を S3 と 0 のどちらで数えるか規則欠如** `status: candidate` `hits: 1`
  - **naturalness-A(0808)**: A-8「による」3→2 残存、H 系文頭 3→2 は発火閾値(3)割れ。今回リズム残り香として S3 計上したが 0612 run は閾値割れ B-2 を「保守的に S2」と処理しておりポリシーがブレる。閾値割れの扱いを SSOT で固定すべき。
- **公的文書ジャンルの口語化下限メトリクス** `status: candidate` `hits: 1`
  - **naturalness-B(0808)**: 過推敲シグナルは「敬体/常体混入」中心で下限（くだけ過ぎ）を測る指標が無い。丁重体 marker の下限密度、または依頼形が命令調/タメ口へ逸脱していないかの二値チェックを over_polish に追加。

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 2run`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B(0612), fidelity-A(0612)。**detector-A(0808)** が run001 で RAG/LLM/エンベディング/インデックス/クエリ/ANN の除外根拠が taxonomy 1 行のみで運用者依存と再指摘 → **免責語彙リストのファイル化**を要望。
- **公用文ホワイトリスト（detector⇔reviewer 共有）** `status: candidate` `hits: 1`
  - **naturalness-B(0808)**: 「につきましては／を通じて（一部）／当該／ならびに／にて」等の正当定型を detector と reviewer が同一基準で除外できるよう taxonomy に注記。今回は 02_detection.json の reason を人手で読んで非計上にしたため再走査自動化時に過検出リスク。

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。出所 detector-A(0612), 実施 detector-A/B(0808)（全 span 検証済み）
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B(0612)
- **反復系 finding は全 occurrence を flag する運用へ** `status: candidate` `hits: 1`
  - **detector-A/rewriter-A(0808)**: f001「テクノロジー2回反復」と reason に書きつつ 1 個所しか anchor せず、rewriter が未 flag の 2 個所目を波及正規化した（surgical 原則との齟齬）。H-1「しかし」のみ flag・A-8「による」1個所のみ flag も同型で、削除後に残り occurrence が残存。反復系は全数 flag するか `occurrences[]`（IMP-004）で持つべき。
- **隣接する別カテゴリ finding の連結ヒント `adjacent_group_id`** `status: candidate` `hits: 1`
  - **detector-A(0808)**: 欠かせない|コンポーネント|となりつつある が連続語のとき、推敲役が同一句を一括自然化しやすくなる。IMP-005 の merged とは別軸。

### 新パターン候補（taxonomist 審査待ち）
- **A-14 候補「〜ことによって / 〜ことで」手段節の冗長化** `hits: 1`（実例3回で昇格条件充足間近）
  - **detector-A(0808)**: run001 に「本技術を活用する**ことによって**」「LLM に渡す**ことで**」「採用する**ことで**」の 3 回反復。英語 `by ~ing` の直訳。A-3「を通じて」A-8「によって」に近いが動詞+ことによって/ことで は別シグネチャ。処方: 連用中止形「〜して」へ（活用して/渡して）。**次 run で再現すれば A-14 として v1.1 昇格候補。**
- **A-5 拡張「ことが可能になる / ことが期待できる」変種** `hits: 1`
  - **detector-A(0808)**: 「取得する**ことが可能になります**」「返す**ことが可能となっています**」「低減する**ことが期待できます**」。現行 A-5 は「ことができる」中心で変種が定義文に無く拾い漏れやすい。A-5 定義に変種明記を提案。
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。実例: 0612-001。`hits: 1` 出所 detector-A(0612)
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「〜してみてはいかがでしょうか」。実例 0612-002 + 0808-001（「触れてみてはいかがでしょうか」）。`hits: 2` → **`status: done` taxonomist 審査で v1.1 昇格（S2）。適用: 2026-08-08。** D-1（空虚な結び）/D-6（硬い号令）から CTA 機能で分離。playbook D 表にもレシピ追加済み。
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式。実例 0612-002。`hits: 1` 出所 detector-B(0612)
