# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-07-26（run 2026-07-26-001 技術解説, 002 公的文書）

適用サマリ (2026-07-26): IMP-002・IMP-004(partial)・IMP-001 を実装適用（下記各項参照）。新カテゴリ候補 K「過剰敬語」を taxonomy 拡張候補欄へ登録（審査済み・hits=1 で昇格待ち）。

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done` `hits: 2run` `applied: 2026-07-26-001`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。Sample A も 47.6% と高止まり。
- **再現 (2026-07-26-001)**: B-2 カタカナ語 16 件の和語化で raw change_rate 39%。過推敲ではなく除染コスト（例: インフラストラクチャ→基盤で削除8字が丸ごと加算）。fidelity=pass・自然度 A のため override accept。rewriter-A・naturalness-A が独立に指摘。→ hits 2run へ。
- 出所: rewriter-A, rewriter-B, naturalness-B（1st）／rewriter-A(001), naturalness-A(001)（2nd）
- **適用済み**: (a) `semantic_change_rate` と `raw_change_rate` を分離。B-2 等価置換は max(len) 1 回計上・純削除控除・重複解消は `resolves` で二重計上禁止。(b) 閾値判定を semantic 主指標に。(c) raw のみ超過＋semantic 閾内＋fidelity/自然度 A/B は override accept を SKILL.md に明文化。
- 影響ファイル（編集済）: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`
- 残: semantic_change_rate の自動計算を rewriter が確実に算出するか要監視（次 run で回帰確認）。トークン/文節ベース編集距離への発展は将来課題。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2run` `applied: 2026-07-26 (v1.1)`
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える（Sample A raw106→92.5、taxonomy 例は raw56→71.5 と不整合）。
- **再現 (2026-07-26)**: 決定的証拠 — 本日 detector-A が `100*(1-exp(-W/60))`、detector-B が `100*W/(W+45)` と**別式**を採用し score が非可換に。式未定義が実害として顕在化。→ hits 2run。
- 出所: detector-A, detector-B（両 run で再現）
- **適用済み**: 正準式を SSOT 確定 → `W = S1×5+S2×2+S3×0.5`、`severity_weighted_score = round(100*(1-exp(-W/45)),1)`。k=45 は既存例 raw56→71.5 から逆算（実計算 71.2 で整合）。input_length 非依存。旧式は無効と明記。taxonomist 審査済み v1.1。
- 影響ファイル（編集済）: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出`
- 残: 検出器実装が k=45 を守るか（共有定数・回帰テストの一元化）が未保証。次点起票。

### IMP-003 score_before のフィールド契約が曖昧 `status: ready` `hits: 1run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score 92.5）。レビュアーごとに数値がぶれる。
- 出所: naturalness-A
- 提案: 「score_before = 02_detection.json の meta.severity_weighted_score」と明文化。
- **2026-07-26 進捗**: 両 naturalness が score_before=89.9/58.3（＝meta.severity_weighted_score）を正しく採用。運用上は事実上遵守。IMP-002 の正準式確定でぶれ源も縮小。ただし明文化は naturalness-reviewer.md へ未反映のため ready 維持。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

### IMP-007 score_before/after は同一 detector・同一 recall で算出すべき `status: ready` `hits: 1run(1agent)`
- 症状 (2026-07-26-001): naturalness-A の独立走査 (score≈4.9) と子検出器 (7.2) で 2.5pt ぶれ。かつ推敲前 02_detection.json が軟カタカナ（コンテンツ/ニュアンス等）を過小計上しており baseline 89.9 自体に recall ムラ。前後の recall が違うと improvement_rate が過大評価される。
- 出所: naturalness-A
- 提案: 「推敲前後の検出は同一 detector プロセス・同一しきい値で走らせ、1 コミットに束ねる」を運用ルール化。IMP-006（再走査の必須化）と統合検討。
- 影響: `naturalness-reviewer.md`, `SKILL.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: partial-done` `hits: 2run` `applied: 2026-07-26 (v1.1, 部分)`
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
- **再現 (2026-07-26)**: detector-A が E-1/E-2 を代表位置アンカーで無理に起票、detector-B が E-2 で同様。両者が「meta.notes がスキーマ外」とも指摘（スコア式明記のため独自追加を強いられた）。→ hits 2run。
- 出所: detector-B, detector-A（両サイクルで再現）
- **適用済み（部分）**: finding に `scope: "span"|"document"` を追加（document は start/end を代表アンカー可と明記）、meta.notes・category_label を正式フィールド化。taxonomist v1.1。
- **残（未適用）**: scattered 用 `occurrences: [[s,e],...]`、density を重複・locator 除外の実クセ文字数ベースに再定義、document-scope finding の W への重み寄与ルール（taxonomist 指摘: E-2 1 件を span 1 件と同列に S2 算入してよいか未定義）。→ 次サイクルで適用候補。
- 影響: `ai-tell-taxonomy.md §スキーマ`(部分済), `ai-tell-detector.md`(scope 反映済)

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run` （edit 側は partial-done）
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。
- **再現 (2026-07-26)**: rewriter-A が「革新的なソリューションをもたらす」に f016(A-10)+f025(B-2)+f039(D-4) の三重該当を報告、rewriter-B が f005/f008・f007/f012 を `merged_with` で処理、fidelity-B/detector-A も指摘。→ hits 2run。
- 出所: detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A（1st）／rewriter-A, rewriter-B, fidelity-B, detector-A（2nd）
- **部分適用 (2026-07-26)**: rewriter の diff スキーマに `resolves: [...]` を追加し change_rate 二重計上を禁止（IMP-001 と併せて）。
- **残**: 検出側の「1 span = 主分類 1 finding + merged_findings 配列」規約、category_summary の集計注記は未適用。taxonomist も「finding は 1 span 1 カテゴリ」の排他ルール追記を次点提案。→ 次サイクル。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready(実証進捗)` `hits: 1run`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。
- 出所: naturalness-A
- 提案: `ai-tell-detector` をサブエージェントとして再呼び出しする経路を必須化（手動照合禁止）。
- **2026-07-26 進捗**: naturalness-001 が実際に ai-tell-detector を子タスクとして spawn し score_after=7.2 を権威値として採用（手動照合と一致）。002 も同基準再走査。運用として実証されたが、naturalness-reviewer.md への「必須化」明文はまだ未反映のため ready 維持。IMP-007（前後 recall 統一）と統合して次サイクル適用候補。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **【登録済 v1.1 拡張候補欄】K 過剰敬語・二重敬語** ★日本語固有・想定 S2。K-1 二重敬語（謙譲＋受身/可能）「ご連絡が差し上げられることとなります」/K-2 過丁寧緩衝「〜ものと考えております」/K-3 くどい定型反復「お願い申し上げます」多用。`hits: 1run(3agent: detector-B, rewriter-B, naturalness-B)` 公的文書ジャンルで再現性高。**2 run 目の公的文書で再現すれば v1.2 昇格**。昇格時は G との判定優先順位（二重計上防止）と「敬体維持＋変奏で崩す」処方の明記が必須（taxonomist 指摘）。
- **A-6b 「〜ようになっている/〜ようになります」変化＋状態の複合** 実例「注目を集めるようになっています」「カバーすることができるようになります」（001, 2件）。A-6 のサブ昇格候補。`hits: 1run` 出所 detector-A
- **B-2 サブ分割 (B-2a 名詞カタカナ / B-2b カタカナ動詞化)** 「トランスフォーム/キャプチャ」等サ変欠落の動詞カタカナ化は名詞カタカナより露見度が別格。IT 記事では一般名詞カタカナ許容度が高く動詞カタカナだけ浮く。`hits: 1run` 出所 detector-A
- **A-10 万能動詞リスト拡充** 「発揮する」を追加候補（「ポテンシャルを発揮する」を今回 A-5 側で拾った）。`hits: 1run` 出所 detector-A
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 001(6/12)。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B

### severity/scope 補正ルール候補（2026-07-26）
- **ジャンル別 severity 補正**: A-1/A-2 は公用文では標準表現でもあり、一律 S1 は公的文書で過検出。公的文書では密度ベース S2 へ降格する補正を検出手順に明記。`hits: 1run` 出所 detector-B
- **二重受動の severity 加点**: 「延長される措置が取られます」「図られることが期待されております」は単独受動より AI らしさ強。A-8 に二重受動 → S1 相当への格上げ補正。`hits: 1run` 出所 detector-B
- **A-6 例示に「〜こととなる/こととなりました」を追加**: A-6 定義例は「となっている/となります」中心で形式名詞＋となる が欠落。公的文書の最頻出状態叙述。`hits: 1run` 出所 detector-B
- **E-1 SD 数値閾値の規定**: 「40〜60字集中」に SD 具体閾値なし。`SD < 15` 等の数値トリガー化で再現性向上。`hits: 1run` 出所 detector-A

### fidelity チェックリスト追補
- **#15 評価語・誇張語（革新的/画期的/最先端）の削除は fidelity 上の欠落に当たらない、と明文化** 現行 13 項は #10欠落 とも #11追加 とも切り分けられずグレー。監査官裁量依存。実例 f039「革新的な」削除(001)。`status: ready` `hits: 1` 出所 fidelity-A(001)
- **とりたて助詞（も/まで/だけ/こそ/しか）の増減を独立チェック項目化** 「を→まで」の含意シフト（f004, 001）は #6量化 でギリギリ。「関連概念まで」が「関連概念だけ」なら極性近い毀損だが専用項目なし。`status: ready` `hits: 1` 出所 fidelity-A(001)
- **modality の文書レベル累積シフト検査** 個別 span は許容でも文書全体で断定/確信方向へ系統シフトするとトーン変質（f002+f040+f038 が全て断定化, 001）。check#7 に文書レベル観点追加。`hits: 1` 出所 fidelity-A(001)
- **check#7 modality 二分基準**: ヘッジ除去が「能力・状態の言い切り」に留まれば pass、「保証・約束」に転じれば rollback（公的文書は法的含意ありうる）。実例 f013「期待→見込み」/f020「〜ものと考えております→いただけます」(002)。`hits: 1` 出所 fidelity-B(002)
- **公的文書 A-8 能動化の fidelity 安全則**（rewriter/playbook 側）: 明示主語「当図書館が」を補わず謙譲語の含意で主体を暗示。主語補充は原文がぼかした主体を断定＝#11 違反リスク。実例 f011「延長いたします」(002)。`status: ready` `hits: 1` 出所 fidelity-B, rewriter-B(002・同一 run 2agent)
- **merged_with/resolves 統合 edit の「統合後 span 意味等価」サブチェック** 複数 finding が同一 span を上書きするケースの追跡が 13 項にない。`hits: 1` 出所 fidelity-B(002)
- **borderline_notes を 04 スキーマの正式フィールド化** 監査官が独自追加した境界注記を次工程が機械的に読めるよう標準化。`hits: 1` 出所 fidelity-A, fidelity-B（両 run で独自追加）
- **接続詞削除による論理明示性低下**を fidelity/naturalness どちらが扱うか SKILL.md で役割分界を一意化。実例 f041/f042(001)。`hits: 1` 出所 fidelity-A(001)
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019（並列→基盤の序列混入）はこの項が無く #5/#11 へ漏れ込んだ。`status: ready` `hits: 1` 出所 fidelity-A
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。`status: ready` `hits: 1` 出所 fidelity-B
- 「情報を含む削除 vs ボイラープレート削除」二分判定: 削除 span に (a)数値/固有名詞/日付 (b)条件/因果節 (c)固有の例示 を含めば情報欠落、挨拶/CTA/装飾/自己言及のみならボイラープレート。出所 fidelity-B
- #5論理関係 と #11情報追加 の責任境界を一意化（主因項目を 1 つに正規化）。出所 fidelity-A
- modality 強度を順序尺度化（要請/推奨/義務/必須）。出所 fidelity-A

### playbook レシピ追補
- **A-13「という」の命名用法は例外**: 「Xというアルゴリズム」等 term＋カテゴリ名は自然。全消しでなく 1 個まで許容 or「と呼ばれる」へ変奏。実例 f018/f019(001)。`hits: 1` 出所 rewriter-A
- **A-10＋B-2 複合（万能動詞＋カタカナ目的語）の手順**: 「ソリューションをもたらす」は「行為者＋具体動詞」へ再構成し両方一掃。playbook に複合パターン節。`hits: 1` 出所 rewriter-A
- **E-1 短文は「分割」で作る（新規挿入で作らない）**: 「短文を混ぜる」指示と「情報を足さない」鉄則の衝突回避。既存文の分割（「〜クエリに対して」→体言止め「〜クエリ。」）で対応。`hits: 1` 出所 rewriter-A
- **敬体・公的文書の E-2 変奏手札**: 「でしょう/体言止め」が使えない格の文書では、依頼形の変奏（お願い申し上げます/いたします/ください/お問い合わせください）で単調を崩す。`hits: 1` 出所 rewriter-B
- **A-8 能動化: 行為者秘匿型は topic-comment＋謙譲語で主体を暗示**（「措置が取られます→延長いたします」）。明示主語を立てると公的文書で不自然かつ #11 リスク。`hits: 1` 出所 rewriter-B（fidelity-B が fidelity 安全性を確認）
- **H-1「70%削除」から逆接を除外**: 逆接（ただし/しかし）は論理分岐点で、削ると例外条項が並列に誤読される。「また/なお」は削除、「ただし」は保持。`hits: 1` 出所 rewriter-B
- **C-5 絵文字削除後の文末/区切り吸収ルール**（句点で吸収 or 削除のどちらか明記）。出所 rewriter-B
- **D 系結びは削除一択でなく「最小着地文を残す」**（減らしすぎ下限）。実例: B の「気軽に始めてみてください」。出所 rewriter-B, naturalness-B
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**という例外則。出所 rewriter-A
- **原文が元から推量の D 系は推量を保持**（「断定へ」の一律処方の例外）。出所 rewriter-A

### naturalness 判定の精緻化
- **E-2 文末単調を「同一文末形の最大連続数」で指標化** 全体平均では変奏済みでも局所連続を見落とす。実例: 001 para4-5 で「ます」4 連続（残存 S2 の実体）。連続3→S3, 4→S2。`hits: 1` 出所 naturalness-A(001)
- **等級に `ai_tell_density_after` 上限を追加** 現行 A/B は S1/S2 件数＋改善率のみで絶対残存密度を見ず、短文で「改善率高いが残存密度高」を A に通しうる。例 A は density_after ≤ 0.05。`hits: 1` 出所 naturalness-A(001)
- **over_polish に「同一/枠づけ助詞の近接反復」「接続詞削除に伴う因果リンク減少」を弱シグナル(S3)追加** 実例: 001「では/には」近接、f041/f042 削除。`hits: 1` 出所 naturalness-A(001)
- **change_rate の段落別ホットスポット監視** 全体率が閾内でも局所集中を早期検知（002 は第2-4段落に除去集中）。`hits: 1` 出所 naturalness-B(002)
- **score_after=0.0 の解釈注意を notes 必須化** 「閾値未満」であって「完全な人間らしさの証明」ではない。improvement_rate=1.0 に引きずられない。`hits: 1` 出所 naturalness-B(002)
- 過推敲シグナルの定量化（敬体/常体混入は文末形態の二値カウントで機械検出）。出所 naturalness-A
- クラスタ系 finding（B-2 密集・C-1 列挙）はクラスタ崩壊時に個別 severity を降格するルール。出所 naturalness-A
- E-2 文末単調の到達可能ライン緩和（体言止め1箇所以上で合格、文体維持制約下の過推敲回避）。出所 naturalness-B
- 絶対残存数ガードを grade 表に組込み（改善率が高くても S1 が1件でも C 以下）。出所 naturalness-A, naturalness-B

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 1run(3agent)`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B, fidelity-A, naturalness-A

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。出所 detector-A
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B
