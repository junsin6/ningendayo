# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数（別 run での再現のみ +1）。

最終更新: 2026-09-13（run 001 技術解説・敬体, run 002 公的文書・敬体）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done` `hits: 3run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。2026-06-12-B は 54.6% で hold 誤発火（実 fidelity=pass/A）。2026-09-13-001 も 37.4%（削除186/挿入69）、002 も 30.8%（削除147/挿入45）で、いずれも削除主導かつ fidelity=pass・自然度 A の健全推敲なのに 30% 警告を踏んだ。
- 出所: rewriter-A/B(0612), rewriter-001/002・naturalness-001/002(0913)
- 提案: (a) 語句改変率と構造/削除率を分離計上。(b) 装飾・常套句の純削除分を控除。(c) 削除主導ケースを中断対象から除外。(d) 50% 中断を「意味改変 edit 比率」基準へ。
- **適用(2026-09-13)**: `rewriting-playbook.md §変更率の数え方` に insert_rate/delete_rate 分離計上、削除主導（delete≫insert かつ insert<20%）の純削除除外、50%超でも fidelity=pass かつ A/B かつ削除主導なら override accept の規則を明記。判定本体を「意味改変 edit 比率」と定義。※ difflib 実装側の metric 算出自動化は未（diff に insert_rate/delete_rate フィールドを実際に出力させる運用を次段で）。
- 影響ファイル: `rewriting-playbook.md`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`

### IMP-002 severity_weighted_score の正規化が未定義で検出器ごとにブレる `status: ready` `hits: 2run`
- 症状: 正規化式が SSOT に無い。2026-09-13 も detector-001 は `min(100,100*raw/(N*0.25))`（k=0.577 相当）、detector-002 は `min(100, raw/input_length*1000)` と**各自が別式を暫定採用**。score が検出実行ごとに非互換。
- 出所: detector-A/B(0612), detector-001/002(0913)
- 提案: 飽和しにくい正規化を SSOT 明記（例 `100*(1-exp(-raw/k))` か「100字あたり加重和」）。分母（input_length 依存 or 固定 max）と短文下限文字数を確定。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出`

### IMP-003 score_before のフィールド契約 `status: ready` `hits: 2run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。2026-09-13 はオーケストレーターが「meta.severity_weighted_score」と明示指定して統一できたが、仕様側は未明文のまま（指定がないとぶれる）。
- 出所: naturalness-A(0612), naturalness-001/002(0913)
- 提案: 「score_before = 02_detection.json の meta.severity_weighted_score」を `naturalness-reviewer.md`・`ai-tell-taxonomy.md` に明文化。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run`
- 症状: 絵文字分散・文末単調(E-2)・構造(C) は分散/文書レベル。単一 start/end では代表 span に便宜アンカーするしかなく機械照合しづらい。2026-09-13 も detector-001/002 が E-2 を 1 文末へ便宜アンカー。
- 出所: detector-B/A(0612), detector-001/002(0913)
- 提案: `scope:"contiguous"|"scattered"|"document"` と scattered 用 `occurrences:[[s,e],...]`／document 用 `evidence:[index,...]` を追加。density は重複・locator を除いた union 文字数と定義。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント＋ロールバック単位規約が無い `status: ready` `hits: 2run(多agent)`
- 症状: 1 span が複数カテゴリ該当（A-13＋B-2、I-4＋B-2＋I-1 等）。edits/findings 1:1 前提で category_summary が過小評価。さらに merged span の従属 edit（after に「（f00Xで削除）」）は**単独ロールバック不能**で、fidelity の finding_id 指定差し戻しと相性が悪い。
- 出所: detector-A・rewriter-A/B・fidelity-A・naturalness-A(0612), detector-001・rewriter-001・fidelity-001・detector-002(0913)
- 提案: 「1 span = 主分類 1 finding」を基本に `merged_findings:[...]`／diff に `merged_into` を許容。merged span は「親 finding_id のみがロールバック単位」と明記し、`after:"（f00Xで削除）"` の非テキスト値を機械可読化。
- 影響: 全 .md のスキーマ節, `japanese-style-rewriter.md` 出力スキーマ

### IMP-006 naturalness-reviewer が検出器を再実行できず score_after が推定 `status: done` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だが、**この実行環境ではサブエージェント（naturalness-reviewer）からさらに ai-tell-detector を起動する Agent/Task ツールが使えない**。2026-09-13 は naturalness-001/002 が両方とも規格整合の内製再走査へフォールバックした。
- 出所: naturalness-A(0612), naturalness-001/002(0913)
- **適用(2026-09-13)**: `naturalness-reviewer.md §処理1` に「サブエージェント起動不能な環境では同一 SSOT・同一スコア式・同一正規化係数で内製再走査し、score_after が推定値である旨と係数を notes に必ず明記」するフォールバック条項を追加。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

### IMP-007 ハイプ削除と modality（可能・推量・留保）保存の区別が無い `status: done` `hits: 2run`
- 症状: A-10/D-4/G のハイプ・翻訳調・婉曲削除が、命題の modality を担う述語まで巻き込み断定化し、真理条件を変える（fidelity #7 modality 毀損）。2026-09-13 の**両 run でロールバック発火**: run 001 f033「変革していく大きな可能性を秘めている」→「変えていきます」（potential→certainty）、run 002 f021「提供が実現されるものと考えております」→「提供できるようになります」（留保→断定）。
- 出所: fidelity-001・naturalness-001・rewriter-001, fidelity-002・rewriter-002(0913)
- **適用(2026-09-13, run 001/002)**:
  - `ai-tell-taxonomy.md` を **v1.0→v1.1** へ。A-10 節に「modality 保存ルール」＋判別テスト＋ロールバック実例2件を正式追加（taxonomist 審査済み）。
  - `rewriting-playbook.md §A` に modality 保存ルール（A-10/A-5/D-4/G 共通）と○×例を追記。
  - `content-fidelity-auditor.md` に #7/#10 帰属ルール＋#7 累積方向性チェック＋#9 アクター表突合を追加。
- 影響: `ai-tell-taxonomy.md`, `rewriting-playbook.md`, `content-fidelity-auditor.md`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査済み・拡張候補欄に登録・再現待ち）
- taxonomy v1.1 の「拡張候補欄」に以下 6 件を実例付きで登録（**いずれも 1 run 再現のため昇格保留**）:
  - **A-2 敬体「〜につきましては」** 主題提示の丁寧化反復（002、同一文書3回）`hits:1`
  - **I-4 複合「〜していただく必要がございます」** 二重敬語＋義務化（002、4回）`hits:1`（敬体系で最有力）
  - **A-6 公的「〜こととなりました／こととなる」** 受動＋状態化で決定主体ぼかし（002、3例）`hits:1`
  - **A-14 候補「基盤となるのが〜です」** 倒置提示構文（001、1例）`hits:1`（実例不足）
  - **D-4 追補「大きな注目を集めています」** 導入部ハイプ（001、1例）`hits:1`
  - **「〜ていく／ていくことでしょう」** 未来進行＋婉曲（001、2例）`hits:1`（単独「ていく」は誤検出大）
- 昇格条件: 別 run（特にもう 1 件の公的文書 run）での再現。次回公的文書回で I-4 複合・A-2 敬体が 2 回到達見込み。

### 旧・新パターン候補（2026-06-12 由来・再現待ち）
- **C 系 redundant restatement**（叙述と箇条書きが同内容を二重記載）実例 0612-001 `hits:1`
- **D-7 ブログ結び呼びかけ公式**（「今回は〜ご紹介しました」「〜してみてはいかがでしょうか」）実例 0612-002 `hits:1`
- **C-9 導入誘導定型**（「さっそく見ていきましょう」）実例 0612-002 `hits:1`

### taxonomist からの構造的提案（審査報告・未適用）
- **敬体/常体の文体軸を各カテゴリに直交化**（敬体特有クセ＝二重敬語義務化・につきましては等を受け止める枠が無い）。`hits:1` 出所 taxonomist(0913)
- **modality を横断次元として独立セクション化**（A-10 だけでなく A-5/A-12/D-4/G に関わる「推敲が触れてはいけない意味次元」）。IMP-007 は A-10 ローカル注記で暫定対応、将来は横断化。`hits:1`
- **密度閾値フィールドを severity と別に持たせる**（密度依存パターンの誤検出管理）。`hits:1`
- **新カテゴリ増設 vs サブ例吸収の判断基準を昇格ワークフローへ明記**。`hits:1`

### fidelity チェックリスト追補
- **#7/#10 帰属ルール**（modality/ヘッジ削除→#7、事実命題削除→#10）`status: done`（2026-09-13 適用、IMP-007 の一部）。出所 fidelity-A(0612)・fidelity-001/002(0913)
- **#7 累積方向性チェック**（同カテゴリ一律置換で義務/確信が一方向ドリフトしていないか）`status: done`（2026-09-13 適用）。出所 fidelity-002(0913)
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか**（f019 型）`status: ready` `hits:1` 出所 fidelity-A(0612)
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実」を逐一問う `status: ready` `hits:1` 出所 fidelity-B(0612)
- **#8 連体修飾の完了→非過去変換**（「指定された金融機関」→「指定する金融機関」）は指示対象集合が不変なら pass、変動なら要確認。`hits:1` 出所 fidelity-002(0913)
- modality 強度を順序尺度化（要請/推奨/義務/必須）。出所 fidelity-A(0612)

### playbook レシピ追補
- **C-5 絵文字削除後の文末/区切り吸収ルール** 出所 rewriter-B(0612)
- **D 系結びは削除一択でなく「最小着地文を残す」** 出所 rewriter-B・naturalness-B(0612)
- **機能が必要な接続詞（しかしながら）は削除でなく変奏** 出所 rewriter-A(0612)
- **原文が元から推量の D 系は推量を保持**（IMP-007 で modality 保存ルールとして昇格・適用済み）出所 rewriter-A(0612)
- **B-2 定着度テスト＋IT分野の維持/開放実例表**（アーキテクチャ・ユースケース・レスポンス・インデックス等の中間層の線引き）`status: ready` `hits:2run` 出所 rewriter-001・naturalness-001(0913)・（0612 の定着カタカナ免責と合流）
- **A-8 受動の限定条件**（話題連続性を保つ受動は能動化対象外、by格で行為者を伏せた型のみ能動化）`status: ready` `hits:1` 出所 rewriter-001(0913)
- **A-13 総称名詞削除 vs 限定名詞保持の判定フロー**（テクノロジー/パラダイム等の framing 総称は削除可、対比を生む限定名詞は削除不可）`status: ready` `hits:1` 出所 rewriter-001・fidelity-001(0913)
- **I-3 敬体バリエーション表**（いただきます／ください／いただきますようお願いします、命令調に傾けない配分）`status: ready` `hits:1` 出所 rewriter-002(0913)
- **連鎖調整の分散規則を定量化**（同形は文書内2回まで、3回目から別形強制）`status: ready` `hits:1` 出所 rewriter-002(0913)

### naturalness 判定の精緻化
- 過推敲シグナルの定量化（churn 内訳＝削除/置換/追加比、文末エントロピー、体言止め率の機械フィールド化）`status: ready` `hits:2run` 出所 naturalness-A(0612)・naturalness-001/002(0913)
- **E-2 敬体専用の到達可能ライン**（敬体は文末変奏の選択肢が狭い。「文末バリエーション3種以上 or 同一語尾連続4文以下で passing」等の敬体上限）`status: ready` `hits:2run` 出所 naturalness-B(0612)・naturalness-001/002(0913)
- クラスタ系 finding はクラスタ崩壊時に個別 severity を降格。出所 naturalness-A(0612)
- 絶対残存数ガードを grade 表に組込み（S1 が1件でも C 以下）。出所 naturalness-A/B(0612)
- **ジャンル係数**（公的文書は敬体均一性が様式上不可避＝E-2 を過剰減点しない。「ください/いただきます」配分の高圧度メトリクス）`status: ready` `hits:1` 出所 naturalness-002(0913)

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 2run`
- ルーティン・モチベーション・データドリブン（0612）＋ アーキテクチャ・ユースケース・レスポンス・インデックス・データベース（0913）等、和語化で情報が痩せる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B・fidelity-A(0612)・naturalness-001(0913)

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert）`status: done-in-practice`（0913 は両 detector が self-verify 一致を実施・報告）。出所 detector-A(0612)
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B(0612)
- **category_label の正準文字列を taxonomy 見出しから表で固定**（検出器ごとの表記揺れ防止）`status: ready` `hits:1` 出所 detector-001(0913)
- **meta に severity_counts / subcategory_summary を追加**（等級判定の S1/S2 件数・密集サブパターンの即把握）`status: ready` `hits:1` 出所 detector-002(0913)
- **ai_tell_density の重複 span は union を取ると明記**（二重計上防止）`status: ready` `hits:2run` 出所 detector-001・detector-002(0913)
- **Do-NOT に「公的文書/ビジネスの儀礼的定型句（御礼・お願い・平素より）」を明記** `status: ready` `hits:1` 出所 detector-002(0913)
