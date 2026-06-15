# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-06-15（run 001 技術記事 / 002 公的文書）。day1 ローテで A-8 受動・I-3・B-2・A-10 を再現。

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。Sample A も 47.6% と高止まり。
- 再現(2026-06-15): 001 でカタカナ和語化の純縮約が del_rate 0.185≫ins_rate 0.090 を生み「削除主導」を再確認（健全側）。002 も del 90字≫ins 26字。両 run とも del/ins 分離併記で正しく続行できた＝IMP-001(c) 提案の妥当性を裏づけ。
- 出所: rewriter-A, rewriter-B, naturalness-B（+2026-06-15 rewriter-001/002, naturalness-002）
- 提案: (a) 「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を change_rate から控除。(c) 挿入率を単独併記し、del≫ins の削除主導ケースは中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: ready` `hits: 2run`
- 再現(2026-06-15): detector-001 raw65.0(727字)・detector-002 raw45.0(621字)。前 run 92.5(784字)と文長非依存の raw 和のままで run 間横比較が依然不能。density は union マージで二重計上回避。
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える（Sample A raw106→92.5、taxonomy 例は raw56→71.5 と不整合）。
- 出所: detector-A, detector-B
- 提案: 飽和しにくい正規化を SSOT 明記（例 `100*(1-exp(-raw/k))` か「100字あたり加重和」）。分母（input_length 依存 or 固定 max）を確定。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出`

### IMP-003 score_before のフィールド契約が曖昧 `status: done(2026-06-15-001/002)` `hits: 2run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score 92.5）。レビュアーごとに数値がぶれる。
- 再現(2026-06-15): naturalness-001/002 とも score_before を 02_detection.json の severity_weighted_score に固定して算出（002 では detector 改訂前の 35 を使用し改訂後 45 とズレ＝契約明文化の必要性を実証）。
- 出所: naturalness-A（+2026-06-15 naturalness-001/002）
- 提案: 「score_before = 02_detection.json の meta.severity_weighted_score」と明文化。
- **適用済み**: `naturalness-reviewer.md` の処理2・出力スキーマ・原則に score_before 契約を明記（run 2026-06-15）。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run`
- 再現(2026-06-15): detector-002 が結語反復・文末単調を個別 finding で列挙し reason 相互参照で document レベルを近似（span 単体では表現不能を再確認）。detector-001 も A-10+A-5 の文書レベル「機能カタログ化」を span 列挙で近似。
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
- 出所: detector-B, detector-A
- 提案: `span_type: "contiguous"|"scattered"|"document"` と scattered 用 `occurrences: [[s,e],...]` を追加。density は重複・locator を除いた実 AI クセ文字数ベースと定義。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 再現(2026-06-15): detector-002 が A-8 受動と A-6 状態化の複合 span を「主カテゴリ1＋reason に副カテゴリ」で処理し category_summary が複合を取りこぼすと報告（`secondary_categories[]` 追加提案）。detector-001 も A-10「アドバンテージをもたらす」⊃B-2「アドバンテージ」の重複を density union で回避。
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。
- 出所: detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A（横断的に最多）
- 提案: 「1 span = 主分類 1 finding」を基本とし、`merged_findings: [...]` 配列を許容。category_summary は「findings の category 先頭文字を集計」と注記。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 2run`
- 再現(2026-06-15): naturalness-002 は推敲文を再走査して `05_redetect.json` を生成し score_after を確定（手動照合でなく検出基準の実走査）。naturalness-001 も同基準再適用。経路の必須化（中間 redetect 成果物の標準化）が望ましいことを実証。
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。
- 出所: naturalness-A
- 提案: `ai-tell-detector` をサブエージェントとして再呼び出しする経路を必須化（手動照合禁止）。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 001(06-12)。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B
- **A-6b「〜こととなる/こととなりました」状態化（受動述語＋形式名詞こと＋となる の三項複合）** 公的・ビジネス AI 文で決定的に頻出。人間は「実施します／延長します」と書く。実例(2026-06-15-002): 「実施されることとなりました」「延長されることとなります」「おかけすることとなりますが」。 `hits: 1` 出所 detector-002（taxonomist 審査推奨・A-6 のサブパターンとして昇格余地）
- **A-10b 技術主体の機能カタログ化（A-10 万能動詞＋A-5 ことができる の合流／文書レベル）** 抽象主語が機能を能力主語化して列挙。実例(2026-06-15-001): 「Kubernetes は複数のコンテナを統合的に管理することができる」「ワーカーノードは…環境を提供します」。 `hits: 1` 出所 detector-001（文書レベルパターン）

### fidelity チェックリスト追補
- **#14 接続語/順序語・受動化の置換で序列・因果・価値・行為者が新規付与されていないか** ← f019（並列→基盤の序列混入）はこの項が無く #5/#11 へ漏れ込んだ。`status: done(2026-06-15-001/002)` `hits: 2run` 出所 fidelity-A（+2026-06-15 fidelity-001/002）
  - 再現(2026-06-15): fidelity-001 が A-5 格変換（向上させることができます→高まります）を #14 補助検査で「保存操作」と判定。fidelity-002 が A-8 受動→能動の行為者補完を #14 で検査し「補完先＝既出主題／span内明示／発話主体の3類型のみ許容」を運用。
  - **適用済み**: `content-fidelity-auditor.md` に独立チェック項目 #14 を追加し、受動化の行為者補完許容基準を明記（run 2026-06-15）。
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。`status: ready` `hits: 2run` 出所 fidelity-B（+2026-06-15 fidelity-001/002 が両 run で実適用）
- 「情報を含む削除 vs ボイラープレート削除」二分判定: 削除 span に (a)数値/固有名詞/日付 (b)条件/因果節 (c)固有の例示 を含めば情報欠落、挨拶/CTA/装飾/自己言及のみならボイラープレート。出所 fidelity-B
- #5論理関係 と #11情報追加 の責任境界を一意化（主因項目を 1 つに正規化）。出所 fidelity-A
- modality 強度を順序尺度化（要請/推奨/義務/必須）。出所 fidelity-A

### playbook レシピ追補
- **C-5 絵文字削除後の文末/区切り吸収ルール**（句点で吸収 or 削除のどちらか明記）。出所 rewriter-B
- **D 系結びは削除一択でなく「最小着地文を残す」**（減らしすぎ下限）。実例: B の「気軽に始めてみてください」。出所 rewriter-B, naturalness-B
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**という例外則。出所 rewriter-A
- **原文が元から推量の D 系は推量を保持**（「断定へ」の一律処方の例外）。出所 rewriter-A
- **B-2 和語化の三択基準（開く/短縮/維持）** 主表記を1つ選び括弧併記は捨てる。例: ワークロード→処理、インフラストラクチャ→インフラ。`hits: 1` 出所 rewriter-001
- **A-10 万能動詞別の置換レシピ** もたらす→与える/〜になる、提供する→（場所）です/動かす（行為者復帰・直接叙述）。`hits: 1` 出所 rewriter-001
- **A-5 格変換の許容則** 他動詞可能形→自動詞断定に開く際、意味保存の範囲で主語格を調整してよい（向上させることができます→高まります＋この技術を使えば）。fidelity が #5/#11 で誤検出しないよう「意味保存操作」と明示。`hits: 1` 出所 rewriter-001, fidelity-001
- **A-8 行為者補完ルール** 行為者が span 内に無い受動は直近の文脈主語/発話主体を能動主語に立てる。特定不能時のみ受動維持。`hits: 1` 出所 rewriter-002, fidelity-002
- **敬体 I-3 の着地形** 敬体文脈の「する必要がある」は「〜ください」「〜いたします」へ（常体の「すべきだ」処方を敬体に適用しない）。`hits: 1` 出所 rewriter-002
- **公的文書 E-2 変奏は敬語強度差で** 申し上げます/いたします/します の段階差で変奏。推量(でしょう)・体言止めは公的告知で浮くため注入しない（ジャンル別合格基準）。`hits: 1` 出所 rewriter-002, naturalness-002
- **過剰敬語是正の下限（honorific_floor）** 結句敬語は反復の山を1段崩すに留め、各段落末の最大級敬語は体裁として保持。`hits: 1` 出所 rewriter-002, naturalness-002

### naturalness 判定の精緻化
- 過推敲シグナルの定量化（敬体/常体混入は文末形態の二値カウントで機械検出）。出所 naturalness-A
- クラスタ系 finding（B-2 密集・C-1 列挙）はクラスタ崩壊時に個別 severity を降格するルール。出所 naturalness-A
- E-2 文末単調の到達可能ライン緩和（体言止め1箇所以上で合格、文体維持制約下の過推敲回避）。出所 naturalness-B
- 絶対残存数ガードを grade 表に組込み（改善率が高くても S1 が1件でも C 以下）。出所 naturalness-A, naturalness-B

### 定着カタカナ語 B-2 免責リスト `status: done(2026-06-15-001)` `hits: 2run`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B, fidelity-A, naturalness-A
- 再現(2026-06-15): rewriter-001/naturalness-001 が技術ジャンルの準業界語「クラウドネイティブ」「マニフェスト」を維持判断（クラスタ崩壊で実効 S3）。detector-001 も B-2 例外の判定主体が曖昧と報告。
- **適用済み**: `rewriting-playbook.md §B-2` に「定着カタカナ語 半免責リスト」と維持/開く/併記の三択基準を追加、`ai-tell-taxonomy.md §B-2` に半免責ノートを追記し taxonomist 審査で **v1.1** へ昇格（run 2026-06-15）。

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。出所 detector-A
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B
