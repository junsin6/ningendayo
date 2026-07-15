# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数（別 run 再現のみ +1）。

最終更新: 2026-07-15（run 2026-07-15-001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除・冗長圧縮で機械的に膨張。**2026-07-15-001 で再現**: 31.08%（挿入7.6%/削除23.5%、類似度0.831）と 30% 警告超だが実体は 754→625 字の圧縮で意味追加ゼロ。override accept で処理。002 は 21.4%（削除16.7%主導）。
- 出所: rewriter-001, rewriter-002, naturalness-001（+ 初出 001,002）
- 提案: (a) `net_change_rate`（|len差|/原文）や `insert_rate` を主指標に、difflib 生値は補助。(b) merge_rewrite（置換）が削除+挿入で二重計上される点を補正。(c) 圧縮型ジャンル（技術解説・レポート・公的文書）では 30/50% 閾値を緩和 or 挿入率基準へ。(d) 装飾・常套句の純削除分を控除。
- 影響: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`
- 備考: override accept の運用は機能しているが、指標そのものの再設計は未適用（次の適用候補筆頭）。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2run` `applied: 2026-07-15-001,002`
- 症状: 正規化式が SSOT に無く検出器ごとに任意。**2026-07-15 で深刻再現**: detector-001 は `raw×100/(len×0.2)`、detector-002 は `min(100,raw)` と別式を採用し run 間比較が不能に。
- **適用済み**: SSOT §検出出力スキーマに文長正規化した飽和式 `score = round(100×(1−exp(−(raw/(len/100))/10)),1)`（`sat_k10_per100`）を確定。アドホック正規化を禁止。`ai-tell-detector.md §スコア算出` も同式に更新。
- 出所: detector-001, detector-002（+ 初出 001,002）

### IMP-003 score_before のフィールド契約が曖昧 `status: done` `hits: 2run` `applied: 2026-07-15-001,002`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定でレビュアーごとにぶれる。
- **適用済み**: 「`score_before` = 02_detection.json の `meta.severity_weighted_score`、`score_after` = 03_rewrite.md を同一式で再走査した値。findings 再合算や density 混在は禁止」を SSOT と `naturalness-reviewer.md` に明文化。
- 出所: naturalness-001, naturalness-002（+ 初出 naturalness-A）

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run`
- 症状: 絵文字分散・文末単調（E-2）・文頭接続詞3回（C/H）・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく density が歪む。**2026-07-15 再現**: detector-001 は E-2 を text_span:"" start:0 end:754 で暫定表現し density から除外（span一致検証を通せず回避2つを要した）、detector-002 も代表末尾1箇所を locator に流用。
- 出所: detector-001, detector-002（+ 初出 detector-A,B）
- 提案: `scope: "span"|"scattered"|"document"` と scattered 用 `occurrences: [[s,e],...]`／document 用 `evidence` を追加。density は scope=document を除外 or 実クセ文字ベースで定義。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/density カウント規約が無い `status: done` `hits: 2run` `applied: 2026-07-15-001,002`
- 症状: 1 span が複数カテゴリに該当（B-2⊂A-10⊂A-13 の三重重複など）。**2026-07-15-001 で 8 ペア再現**（メリット/ソリューション/アドバンテージ等が上位 span に内包）、naive density 0.447 vs union 0.395 と乖離。
- **適用済み**: SSOT に「density = 区間 union（重複除去カバー文字数）/全体、naive は補助値 `ai_tell_density_naive`」「重複 span は主分類1 finding＋`merged_findings` 配列、category_summary は主分類のみ集計」を明文化。JSON 例に `merged_findings`/`score_formula`/`ai_tell_density_naive` を追加。`ai-tell-detector.md` も同期。
- 出所: detector-001, detector-002, rewriter-001（+ 初出 5agent 横断）

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だが実運用が手動照合になりがち。**2026-07-15 再現**: naturalness-001 は当初 ai-tell-detector をサブエージェント呼びして待機したまま自ターン終了→JSON 未生成で再開が必要だった（サブ呼び経路が不安定）。一方 naturalness-002 と再開後の 001 は手動＋タクソノミ再適用で完遂し、001 は検出器再適用で「求められる→欠かせない」の tell-swap（D-4）を捕捉できた（手動照合単独では見落とす実例）。
- **部分緩和**: `naturalness-reviewer.md §処理` に「手動照合ではなく再検出で新規クセ／tell-swap を確認」を明記。ただしサブエージェント呼び経路の安定化は未解決。
- 出所: naturalness-001, naturalness-002（+ 初出 naturalness-A）
- 提案: レビュアー自身が同一正規化式でインライン再検出する運用を正式手順化し、サブ呼びは任意に。

---

## P2 — 分類・レシピ・チェックリスト

### 定着カタカナ語 B-2 免責リスト `status: done` `hits: 2run` `applied: 2026-07-15-001,002`
- **適用済み**: taxonomy §B-2 と playbook §B に「定着カタカナ語 半免責リスト」を追加。技術文脈（アーキテクチャ/エコシステム/デプロイ/ユースケース/パフォーマンス/スケーラブル/パラダイムシフト/レイテンシ）＋一般（ルーティン/モチベーション/データドリブン）を S3 固定で残置。leverage/seamless/solution/insight/merit/advantage は平明訳ありゆえ免責しない。component→「構成要素」推奨。
- 出所: rewriter-001（8語提示・検出器も未flagで一致）, naturalness-002, fidelity-001（+ 初出 3agent）

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** `status: ready` `hits: 2run`
  - **2026-07-15 再現**: fidelity-001 で「また→も／さらに→でも／しかしながら→だが」が序列混入ゼロの**良い実装**として、fidelity-002 で f014「が→。」が儀礼緩衝の非毀損ケースとして。両者とも 13 項に接続語専用項が無く #5/#11 へ手動振り分けを要した。→ **次の適用候補**（content-fidelity-auditor.md を 14 項化）。出所 fidelity-001, fidelity-002。
- **接続助詞（が・けれど・ものの）句点化の二段判定** `status: ready` `hits: 1run` — (1)真理条件的逆接=毀損リスク大 (2)儀礼的緩衝・前置き=文体変更に留まる。#5 のサブ項目化。出所 fidelity-002。
- **削除の情報/ボイラープレート二分に第三区分** `status: ready` `hits: 1run` — 「評価語・抽象上位語」（メリット/中心的役割/リアルタイム性）はどちらにも属さず。「(d)評価/様態修飾＝文脈回復可能なら準ボイラープレート」を追加。出所 fidelity-001。
- **#11 に over-specification（上位概念→下位概念の限定）サブ項** `status: candidate` `hits: 1run` — 「リアルタイム性→応答」「インパクト→変える」は捏造でないため pass に落ちるが射程縮小の芽。実例2件確保。出所 fidelity-001。
- **modality を順序尺度化 + 行為完了度軸** `hits: 1run` — 要請/推奨/義務/必須 に加え「提示/試行/達成」軸（提供→解決の微移動を測る）。出所 fidelity-001。
- **deletion-recall test**（削除 span ごとに読者が知り得なくなる事実を逐一問う）`status: ready` `hits: 2run` — fidelity-001/002 とも本番適用し有効性確認（002 は原文側から13ユニット逆向き照合で全保存を担保）。運用手順として auditor.md 明記が候補。出所 fidelity-001, fidelity-002。

### 新パターン候補（taxonomist 審査待ち）
- **D-8 公的文書の過剰儀礼定型** `hits: 1run` — 「運びとなりました／賜りますよう／ご愛顧いただきますよう／〜いただきますようお願い申し上げます」。AI 生成公的文書に濃いが人間の役所も使うため過検出注意。深刻度 S2（3回+反復で AI 臭）。※ただし「発話行為（依頼・謝罪・感謝）」を担う敬語は正当様式ゆえ**残さない=毀損**（fidelity-002 の発話行為ベース二分と連動）。実例: 2026-07-15-002。番号は既存 D-7候補（ブログ結び）と衝突回避のため D-8。出所 detector-002, rewriter-002。
- **A-13「といった」例示型** `hits: 1run` — 「〜といった観点／〜といったコンポーネント」。「という」の近縁だが翻訳調度は弱く例示列挙用法。閾値規定が無い。実例: 001（2件）。出所 detector-001。
- **G/D「〜ことでしょう/〜はずです」結び常套** `hits: 1run` — 断定回避の推量語尾。ブログ/解説 AI の結び。実例: 001（与えることでしょう／となっていくはずです）。出所 detector-001。
- **使役万能動詞「可能にする/実現する」の分類確定** `hits: 1run` — 「実行することを可能にします」は A-5 とも A-10 とも取れ一意に定まらない。A-10 か A-5 のサブに明示。出所 detector-001, rewriter-001。
- **C 系: redundant restatement**（叙述と箇条書きの二重記載）`hits: 1` 実例 001(6/12)。出所 detector-A。
- **C-9 導入誘導定型**（「さっそく見ていきましょう」）`hits: 1` 実例 002(6/12)。出所 detector-B。
- **D-7 ブログ結び呼びかけ公式**（「今回は〜ご紹介しました」「〜してみてはいかがでしょうか」）`hits: 1` 実例 002(6/12)。出所 detector-B。

### playbook レシピ追補
- **A-10 主語保存×動詞だけ具体化のサブレシピ** `hits: 1run` — 「エッジは（抽象主語）…提供します→解決します」のように主語を残し万能動詞のみ差替。現行 playbook A-10 は主語残す例のみで動詞側処方が未整備。出所 rewriter-001。
- **情報語を巻き込む結び常套句は「ハイプ動詞のみ平明化・目的語は保存」** `hits: 1run` — 「可能性を切り開く→広げる」（可能性は保存）。D 表の削除原則が強すぎる例外。出所 rewriter-001。
- **公的文書の正当な儀礼敬語は不変（Do-NOT ホワイトリスト）** `hits: 1run` — 賜りますよう/ご愛顧/お願い申し上げます を誤って砕けさせると格が崩れる。出所 rewriter-002, fidelity-002。
- **C-5 絵文字削除後の文末/区切り吸収ルール**。出所 rewriter-B（6/12）。
- **D 系結びは「最小着地文を残す」**（減らしすぎ下限）。出所 rewriter-B, naturalness-B（6/12）。
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**。出所 rewriter-A（6/12）。

### naturalness 判定の精緻化
- **E-2 のジャンル別合格線** `status: ready` `hits: 2run` — 公的文書は敬体一本が正しく体言止め混入は逆に過推敲。「体言止め≥1」ではなく「**文末語尾が3形以上に分散**」を合格線に。技術解説でも「できます」5文の局所反復は S3 止まり。出所 naturalness-002（公的）, naturalness-001（技術, できます反復）（+ 初出 naturalness-B）。
- **儀礼敬語をクセと誤検出しないジャンル分岐** `hits: 1run` — detector に `genre=public_notice` を渡し、賜る/ご愛顧/お願い申し上げます/につきまして/何卒/以下のとおり を A-1・過剰敬語判定から除外。無いと score_before 水増しで改善率が歪む。「につきましては」は A-1「においては」と別語。出所 naturalness-002, detector-002。
- **絶対残存数ガードを grade 表に組込み**（改善率が高くても S1 1件で C 以下）。出所 naturalness-001,002（+ 初出）。
- **tell-swap（クセ交換）検知**: 「求められる（I-4）→欠かせない（D-4）」のようにカテゴリを越えた置換を残存として検出器再走査で捕捉。出所 naturalness-001。

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert）。**2026-07-15 両 run で全 span assert 検証を実施済み**。出所 detector-001,002（+ 初出 detector-A）。
- 敬体バリアントのシグネチャ併記 `hits: 1run` — taxonomy の例文が常体形のみ（〜する必要がある/〜となっている）。敬体形（必要がございます/となっております）を各パターンに併記すべき。出所 detector-002。
- 単発でもクラスタ共起時は拾う規約の明文化 `hits: 1run` — A-3/A-9/A-8 が単発でも「手段・目的格の翻訳調3種共起」で finding 化。出所 detector-002。
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B（6/12）。
