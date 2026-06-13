# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-06-13（run 2026-06-13-001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done(部分)` `hits: 2run` 適用: 2026-06-13-001/002
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・純削除で機械的に膨張。06-12-002 は 54.6% で誤発火。**06-13 で再現確認**: 同じ C-1 解体でも再構成版 0.476 / 最小短縮版 0.169 と約3倍ぶれる（rewriter-001 が同根欠陥を実証）。06-13-002 も change_rate 0.324 警告だが fidelity=pass/自然度 A。
- 出所: rewriter-A, rewriter-B, naturalness-B（06-12）＋ rewriter-001, fidelity-002, naturalness-002（06-13・別 run 再現）
- **適用済(2026-06-13)**: `rewriting-playbook.md §変更率の数え方` を改訂し `insert_rate`/`delete_rate`/`edit_char_sum`/`semantic_edit_ratio` を diff meta 併記必須化。中断は change_rate でなく `semantic_edit_ratio` 50% 基準へ。削除主導+fidelity pass+自然度A/B は `override accept`。`SKILL.md §総合判定` に override 行を追加。
- 残: `japanese-style-rewriter.md` 側の実装（edit_char_sum 算出スクリプトの参照実装固定）は次サイクル。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2run` 適用: v1.1（2026-06-13）
- 症状: 正規化式が SSOT に無く runner ごとに値がぶれる（06-13 でも detector-001/002 が両 run で再現指摘。逆算係数 1.084 を流用せざるを得ず再現性が低い）。
- 出所: detector-A, detector-B（06-12）＋ detector-001, detector-002（06-13・別 run 再現）
- **適用済(2026-06-13)**: japanese-ai-tell-taxonomist が `ai-tell-taxonomy.md` を v1.1 へ改訂し正規化式・係数 k・分母を確定。IMP-003（score_before 明文化）も同時反映。

### IMP-003 score_before のフィールド契約が曖昧 `status: done` `hits: 2run` 適用: v1.1（2026-06-13）
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。
- 出所: naturalness-A（06-12）＋ naturalness-001/002 が detector 再走査基準で算出（06-13）
- **適用済(2026-06-13)**: 「score_before = 02_detection.json の meta.severity_weighted_score」を v1.1 で明文化（IMP-002 と統合）。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 1run(2agent)`
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
- 出所: detector-B, detector-A
- 提案: `span_type: "contiguous"|"scattered"|"document"` と scattered 用 `occurrences: [[s,e],...]` を追加。density は重複・locator を除いた実 AI クセ文字数ベースと定義。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready(density部分のみ適用)` `hits: 2run`
- 症状: 1 span が複数カテゴリに該当。06-13 でも detector-001（本モデル＋ことができる重複）/detector-002（A-8 f002 と A-6 f012 が同一 span 170-179）で再現。
- 出所: detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A（06-12）＋ detector-001, detector-002（06-13）
- **density 部分のみ適用済(2026-06-13)**: `ai-tell-detector.md` に「重複 span は union を取り二重計上しない」を明記。残: `merged_findings: [...]` 配列許容と category_summary 集計規約（全 .md スキーマ節）は次サイクル。

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready(運用穴あり)` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」。06-13 では naturalness-001/002 が ai-tell-detector を実呼びでき良好に機能（手動照合フォールバック不要）。だが**再走査エージェントが原検出と異なる severity を付ける**穴が露見（naturalness-002 が D-6/A-6 を S3→S2 に厳格化し score_after/改善率が原検出基準とずれた）。
- 出所: naturalness-A（06-12）＋ naturalness-001, naturalness-002（06-13）
- 提案: 経路必須化は済。**付帯ルール**「再走査時の severity 付与は原検出 02_detection.json の基準に整合させる（レビュアー側で正規化）」を IMP-006 に追加して `naturalness-reviewer.md` へ明記。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

### IMP-007 diff ログと実テキストの同期欠落 `status: ready` `hits: 1run`
- 症状: 06-13-001 round1 で f013/f014/f015 の diff.after と実テキストが乖離（f014: log「ことも欠かせません」 vs 実「あとは…していく。」）。監査官が log を信じると毀損を見逃す。round2 では一致。推敲役が「ログ先書き→実テキスト差し替え忘れ」を起こす。
- 出所: fidelity-001（06-13）
- 提案: rewriter 側で edit 適用後に log.after==実テキスト span を必須突合、またはオーケストレーターが log↔実テキストの機械チェック工程を追加。
- 影響: `japanese-style-rewriter.md`, `SKILL.md`

### IMP-008 fidelity #7 が modality の「弱化方向の欠落」を拾えない `status: ready` `hits: 1run`
- 症状: #7 は「強度が原意を超えて変わる（過強化）」に重心。06-13-001 f014 の必要性述語の純消失（弱化方向）は副次的にしか拾われない。
- 出所: fidelity-001（06-13）
- 提案: #7 に「ヘッジング/要請/必要性 述語の除去で主張強度が原意を下回っていないか」を判定軸として明記。C-1 公式解体は順序語のみ対象とし各手順の modality 述語は独立保存（分離原則）。
- 影響: `content-fidelity-auditor.md §13項`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- ~~**A-8a 行為者ぼかしの単純受動「〜される」**（行政文・規約文）~~ → **v1.1 昇格済(2026-06-13)**。実例 13-001(1)+13-002(6)で別 run 再現。detector 側 A-8/A-8a 分岐も `ai-tell-detector.md` に明記済。
- **叙述→指示の illocution 変換** 「分別されることとなります（事実叙述）→分別してください（指示）」。行為者すり替えでも modality でもない第3の軸。fidelity #9 の note 観点 or rewriter span 外波及ログにフラグ。 `hits: 1` 出所 fidelity-002（13-002）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 06-12-001。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B

### P1/P2 新規（2026-06-13 起票）

#### IMP-009 低スコア文書（S1ゼロ儀礼文）の改善率指標が不安定 `status: ready` `hits: 1run` P1
- 症状: score_before=24.9 のような低密度儀礼文では分母が小さく、残存をどの severity で読むかで改善率が 70〜88% と振れる（同じ accept なのに）。改善率を単独ゲートにすると誤判定の温床。
- 出所: naturalness-002。提案: `score_before < 30` のジャンルでは改善率を主ゲートから外し「絶対残存数 S1/S2 ＋過推敲チェック」を主ゲートに。影響 `naturalness-reviewer.md`, `SKILL.md §品質等級`。

#### IMP-010 公的文書の逆方向過推敲（砕けすぎ・儀礼毀損）検出基準が未定義 `status: ready` `hits: 1run` P1
- 症状: レビュアー仕様に「儀礼性毀損＝逆過推敲」「register 低下（〜してね 式）」の明示チェックが無く手動確認。
- 出所: naturalness-002, fidelity-002（register低下）。提案: over_polish_signals に `ceremonial_erosion`（冒頭挨拶・結語の儀礼枠の削除）と `register_drift_down`（公的文書での砕けすぎ）を正式サブシグナル化、genre=public_notice で必須評価。影響 `naturalness-reviewer.md`。

#### IMP-011 E-2 敬体の許容変奏ライン（用言言い切り＝常体混入＝過推敲） `status: done` `hits: 1run` 適用: 2026-06-13-001
- 症状: 13-001 round1 で「最適化していく。」と用言終止形で言い切り、敬体本文へ常体混入（過推敲 S1 級）。「体言止め（名詞終止）」と「言い切り（用言終止形）」の混同。
- 出所: naturalness-001。**適用済**: `rewriting-playbook.md §E-2` に敬体許容ライン（〜でしょう/体言止め/〜ます のみ。用言言い切りは不可）を明記。round2 で本欠陥を解消・grade A。

#### IMP-012 公的文書ジャンルの儀礼敬語ハンドリングが playbook 未文書化 `status: done(taxonomy側)` `hits: 1run` 適用: v1.1
- 症状: playbook D 系「原則削除」と公的文書の様式保持が衝突、rewriter がアドホック上書き。
- 出所: rewriter-002, fidelity-002, detector-002（13-002 横断）。**適用済(taxonomy)**: v1.1 §ジャンル別 severity 補正で公的文書の頭尾儀礼敬語を S3・除去非推奨に。残: `rewriting-playbook.md` への専用節（処方レシピ側）は次サイクル。

#### IMP-013 detector suggested_fix が含意（到達「ようになる」/望ましくない「てしまう」）を落とす `status: ready` `hits: 1run` P2
- 症状: f007 の suggested_fix「構築できる」が「ようになります」（段階的到達）を落とす案。playbook A-5 表が冗長形除去と意味成分脱落の境界を示さない。
- 出所: rewriter-001, fidelity-001。提案: playbook に「可能形短縮時も到達・含意助動詞（ようになる/てしまう）は保持」注記。suggested_fix を「最小修正案」と「推奨修正案」に二分。C-1 解体は順序語のみ対象とし modality 述語は独立保存（IMP-008 と連動）。

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019（並列→基盤の序列混入）はこの項が無く #5/#11 へ漏れ込んだ。`status: ready` `hits: 1` 出所 fidelity-A
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。`status: ready` `hits: 1` 出所 fidelity-B
- 「情報を含む削除 vs ボイラープレート削除」二分判定: 削除 span に (a)数値/固有名詞/日付 (b)条件/因果節 (c)固有の例示 を含めば情報欠落、挨拶/CTA/装飾/自己言及のみならボイラープレート。出所 fidelity-B
- #5論理関係 と #11情報追加 の責任境界を一意化（主因項目を 1 つに正規化）。出所 fidelity-A
- modality 強度を順序尺度化（要請/推奨/義務/必須）。出所 fidelity-A

### playbook レシピ追補
- **C-5 絵文字削除後の文末/区切り吸収ルール**（句点で吸収 or 削除のどちらか明記）。出所 rewriter-B
- **D 系結びは削除一択でなく「最小着地文を残す」**（減らしすぎ下限）。実例: B の「気軽に始めてみてください」。出所 rewriter-B, naturalness-B
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**という例外則。出所 rewriter-A
- **原文が元から推量の D 系は推量を保持**（「断定へ」の一律処方の例外）。出所 rewriter-A

### naturalness 判定の精緻化
- 過推敲シグナルの定量化（敬体/常体混入は文末形態の二値カウントで機械検出）。出所 naturalness-A
- クラスタ系 finding（B-2 密集・C-1 列挙）はクラスタ崩壊時に個別 severity を降格するルール。出所 naturalness-A
- E-2 文末単調の到達可能ライン緩和（体言止め1箇所以上で合格、文体維持制約下の過推敲回避）。出所 naturalness-B
- 絶対残存数ガードを grade 表に組込み（改善率が高くても S1 が1件でも C 以下）。出所 naturalness-A, naturalness-B

### 定着カタカナ語 B-2 免責リスト `status: done` `hits: 2run` 適用: 2026-06-13
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語＋分野準固有語（例 セキュリティポスチャ）は B-2 から半免責し和訳併記 or 残差 S3 固定。出所 naturalness-B, fidelity-A, naturalness-A（06-12）＋ detector-001, rewriter-001（06-13・別 run 再現）。
- **適用済(2026-06-13)**: `rewriting-playbook.md §B-2` に「定着カタカナ語・分野準固有語の半免責」を追記。taxonomy v1.1 §B-2 にも注記。

### detector 実装
- ~~start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）~~ → **適用済(2026-06-13)** `ai-tell-detector.md §検出手順5` に明記。出所 detector-A＋detector-002（13 で再現）
- ~~ai_tell_density の overlap union 計上~~ → **適用済(2026-06-13)** detector §検出手順5 に「重複 span は union」を明記（IMP-005 の density 部分）。出所 detector-001/002
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B
