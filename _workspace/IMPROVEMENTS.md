# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-09-06（run 2026-09-06-001 技術解説, -002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: DONE(2026-09-06-001)` `hits: 2runs`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。Sample B は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。Sample A も 47.6% と高止まり。
- **再現(2026-09-06)**: run 001 で change_rate 37%（語句 32.3%＋構造 4.4%、B-2 カタカナ 15 件の正当な和語化が主因）だが fidelity=pass・自然度 A・過推敲シグナル 0 → override accept。run 002 も 24.6%（削除 107≫挿入 44 の純減型＝敬語冗長圧縮）。単一指標なら run 001 は警告誤発火。rewriter-001/002・naturalness-001/002 が横断再現。
- 出所: rewriter-A, rewriter-B, naturalness-B（+ 2026-09-06 全 rewriter/naturalness）
- 提案: (a) 「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を change_rate から控除。(c) 挿入率を単独併記し、del≫ins の削除主導ケースは中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。(e) 計算法（Levenshtein 近似 or 単純和）を playbook に明記。結合 edit の二重計上を排除。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`
- **適用(2026-09-06)**: playbook「変更率の数え方」を分離計上へ全面改訂・SKILL.md §総合判定に override accept を明文化。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: ready` `hits: 2runs`
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える（Sample A raw106→92.5、taxonomy 例は raw56→71.5 と不整合）。
- **再現(2026-09-06)**: detector-001 は raw 加重和を 0–100 cap（80.5）、detector-002 は `min(100, raw/input_length×1000)`（60.5）と**別式を採用**＝正規化未定義がそのまま検出器間の非互換として顕在化。706 字で raw 80.5 は S1 数件で 100 飽和が目前。
- 出所: detector-A, detector-B（+ 2026-09-06 detector-001/002）
- 提案: 飽和しにくい正規化を SSOT 明記（例 `100*(1-exp(-raw/k))` か「100字あたり加重和」）。分母（input_length 依存 or 固定 max）を確定。検出器間で式を統一。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出`

### IMP-003 score_before のフィールド契約が曖昧 `status: DONE(2026-09-06-002)` `hits: 2runs`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score 92.5）。レビュアーごとに数値がぶれる。
- **再現(2026-09-06)**: naturalness-002 が「score_before = meta.severity_weighted_score(60.5)、score_after も同一 input_length・同一正規化式で算出」と契約通り運用し比較可能性を確保。契約が明文化されていれば検出器間の式不一致（IMP-002）とも整合。
- 出所: naturalness-A（+ 2026-09-06 naturalness-002）
- 提案: 「score_before = 02_detection.json の meta.severity_weighted_score、score_after は同一正規化式・同一 input_length で算出」と明文化。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`
- **適用(2026-09-06)**: naturalness-reviewer.md §処理 と taxonomy §検出出力スキーマ に契約を明記。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2runs`
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
- **再現(2026-09-06)**: detector-001 は E-2 を便宜的に 0–706（文書全体）・H-1 を代表 span、detector-002 は E-2/D-6 を代表 span＋reason に実位置列挙（57/190/421/574）で逃がした。両者とも単一 start/end に収まらず推敲役が全出現を確実に処理できない。
- 出所: detector-B, detector-A（+ 2026-09-06 detector-001/002）
- 提案: `scope: "span"|"scattered"|"document"` と scattered 用 `occurrences: [[s,e],...]` を追加。density は重複・locator を除いた実 AI クセ文字数ベース（union）と定義。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: PARTIAL(2026-09-06 v1.1)` `hits: 2runs`
- **適用(2026-09-06)**: taxonomy v1.1 で density=union（重複排除）定義・document-level 除外・任意 `overlaps:[id]` を明文化。**残**: rewriter 側の変更率における結合 edit のカウント規則・`scope` フィールドの構造化は次サイクル。
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。
- **再現(2026-09-06)**: detector-001 で「イノベーションをドライブする」が B-2(f022)＋D-5(f010)＋A-6「存在となる」の三つ巴重複＝naive 合計 density 0.364 vs union 0.324。rewriter-001 も結合 edit（f009+f018）で finding 単位加算だと二重計上。detector-002 も document-level(E-2)と span-level の重複を density から除外して回避。density=union 定義の明文化が要る。
- 出所: detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A（+ 2026-09-06 detector-001/002・rewriter-001）
- 提案: 「1 span = 主分類 1 finding」を基本とし、`merged_findings: [...]`／`overlaps: [id]` を許容。density は union（重複排除）と明文化。document-level は density から除外。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 2runs`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。
- **再現(2026-09-06)**: naturalness-002 が推敲文を独立再走査し、原検出 f001-f016 に無かった**見落としパッシブ「断水が実施される時間帯」**を残存 S2 として捕捉。消し込み照合では原理的に捕捉不能＝再走査経路が「消し込み確認」と「新規残存検出」の両方を担う根拠を実証。
- 出所: naturalness-A（+ 2026-09-06 naturalness-002）
- 提案: `ai-tell-detector` をサブエージェントとして再呼び出しする経路を必須化（手動照合禁止）。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。本文書で最も人間離れ。実例: 001。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。実例2件で昇格条件充足。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。 `hits: 1` 出所 detector-B
- **A-8 無主語受動（agentless passive）サブパターン** 現 A-8 は「〜によって」by-passive 限定だが、公用文の主クセは *「によって」を伴わない無主語受動*（「工事が実施される」「立ち入りが制限される」）。run 002 で 5 件すべて によって無し。★日本語固有寄り・公的文書 S2。 `hits: 1(2026-09-06-002)` 出所 detector-002, rewriter-002。**公的文書ジャンル再走時に再現すれば昇格**。
- **I-3 敬語ヴァリアント「〜必要がございます」** I-3 の丁寧体変種（〜必要がございます／〜いただく必要がございます）。run 002 で 4 回反復。I-3 シグネチャへ追記候補。 `hits: 1(2026-09-06-002)` 出所 detector-002
- **A-6「〜こととなりました／こととなりますので」** 官僚調の状態叙述変種（現 A-6 は「となっている/となります」のみ）。run 002 で 3 回。register-appropriate のため S2 減格運用込み。 `hits: 1(2026-09-06-002)` 出所 detector-002
- **新カテゴリ K「過剰敬語・定型儀礼の反復」（★日本語固有・公的文書）** 「お願い申し上げます」×3・「賜り」×3・「何卒」×3、敬語＋必要の積み上げ（「ご了承いただく必要がございます」）。A〜J に受け皿が無く D-6 で近似したが適合が弱い。1 文書で 3 系統そろい候補要件充足。 `hits: 1(2026-09-06-002)` 出所 detector-002。**taxonomist へ K 新設 or D 系拡張を審査依頼**。
- **句レベルカタカナ（副詞/形容詞＋動詞のカタカナ連結）** 「ディープにインテグレート」「イノベーションをドライブする」は単語表で引けず句ごと和語化が要る。playbook B-2 変換表は単語単位のため穴。 `hits: 1(2026-09-06-001)` 出所 rewriter-001
- **近接同義カタカナの二重（メリット／アドバンテージ）** 近接同義カタカナは一方を述語/形容詞へ吸収するレシピ。 `hits: 1(2026-09-06-001)` 出所 rewriter-001
- **副詞・呼応表現の反復（あらかじめ×3 等）** 接続詞ではないが副詞レベルの反復は E-2/H の網から漏れる。検出粒度追加候補。 `hits: 1(2026-09-06-002)` 出所 rewriter-002

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019（並列→基盤の序列混入）はこの項が無く #5/#11 へ漏れ込んだ。`status: ready` `hits: 1` 出所 fidelity-A
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。`status: ready` `hits: 2runs` 出所 fidelity-B（+ 2026-09-06 fidelity-002: 純減 63 字の公用文で「情報 vs ボイラープレート」二分判定が正当な冗長削減の誤検知を防いだ最有効項）
- 「情報を含む削除 vs ボイラープレート削除」二分判定: 削除 span に (a)数値/固有名詞/日付 (b)条件/因果節 (c)固有の例示 を含めば情報欠落、挨拶/CTA/装飾/自己言及のみならボイラープレート。`hits: 2runs` 出所 fidelity-B（+ fidelity-002）
- **#15 事態の現実性（realis/irrealis）保存 `status: ready` `hits: 1(2026-09-06-001)`** 「期待/見込み ↔ 進行/実現」「予定 ↔ 完了」の越境検査。時制でも modality 語でもなく「その事態が現実に起きたか否か」を独立に見る軸。**今回 f028「応用が期待されています→進んでいます」を的確に捕捉し rollback を発火**（run 001 で唯一の毀損）。出所 fidelity-001。実運用で毀損を止めた実績があるため高優先。
- **技術語の外延（denotation scope）保存** カタカナ技術語の和語化で指示対象の外延が縮小/拡大していないか（インフラストラクチャ→設備＝縮小、アーキテクチャ→仕組み＝拡大の恐れ）。`hits: 1(2026-09-06-001)` 出所 fidelity-001
- **語彙強度の順序尺度（#7 を語彙へ拡張）** 動詞/形容詞のカタカナ→和語で強度・agentivity が変わる例を尺度化（ドライブ/drive=強→後押し=中）。「牽引/推進/後押し/支援」を強度順に並べ原語相当段へ着地したか判定。`hits: 1(2026-09-06-001)` 出所 fidelity-001
- **agentivity-preservation（非人称性の保存）** 原文が意図的に主体をぼかす（責任回避・非確定）のを能動化で確定させていないか。公用文は主体秘匿が仕様のこともある。`hits: 1(2026-09-06-002)` 出所 fidelity-002
- **蓋然性語の許容置換マップ（#7 付属）** 可能性／場合／恐れ／おそれ の等価表。「場合」は蓋然性等価だが「恐れ」はネガ含意で価値付与。`hits: 1(2026-09-06-002)` 出所 fidelity-002
- #5論理関係 と #11情報追加 の責任境界を一意化（主因項目を 1 つに正規化）。出所 fidelity-A
- modality 強度を順序尺度化（要請/推奨/義務/必須）。**隣接1段以内は等価許容／2段以上跳躍で毀損**のしきい値運用が run 002 で pass/rollback を原理的に切り分けた。`hits: 2runs` 出所 fidelity-A（+ fidelity-002）

### playbook レシピ追補
- **C-5 絵文字削除後の文末/区切り吸収ルール**（句点で吸収 or 削除のどちらか明記）。出所 rewriter-B
- **D 系結びは削除一択でなく「最小着地文を残す」**（減らしすぎ下限）。実例: B の「気軽に始めてみてください」。`hits: 2runs` 出所 rewriter-B, naturalness-B（+ 2026-09-06 rewriter-002: 公用文で末尾「重ねてお願い申し上げます」を 1 回温存し register を保持）
- **ジャンル別 register 下限（新規 `hits: 1(2026-09-06-002)`）** 公的文書＝結び 1 回・「お願い/申し上げ」系を全滅させない・ご/お＋ください形を維持しだ体化しない。D 系削減に下限を設けないと register が壊れる。出所 rewriter-002
- **同カテゴリ反復の異形分散則** I-3「必要がございます」×4 を「確保しておいてください/お流しください/ご了承ください/ご注意ください」と N 個を別形へ分散＝機械均一回避。playbook レシピ表に「反復時は N 個を異形へ分散」列を明示。`hits: 1(2026-09-06-002)` 出所 rewriter-002
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**という例外則。出所 rewriter-A
- **原文が元から推量の D 系は推量を保持**（「断定へ」の一律処方の例外）。出所 rewriter-A

### naturalness 判定の精緻化
- 過推敲シグナルの定量化（敬体/常体混入は文末形態の二値カウントで機械検出）。出所 naturalness-A
- クラスタ系 finding（B-2 密集・C-1 列挙）はクラスタ崩壊時に個別 severity を降格するルール。出所 naturalness-A
- E-2 文末単調の到達可能ライン緩和（体言止め1箇所以上で合格、文体維持制約下の過推敲回避）。出所 naturalness-B
- 絶対残存数ガードを grade 表に組込み（改善率が高くても S1 が1件でも C 以下）。出所 naturalness-A, naturalness-B

### 定着カタカナ語 B-2 免責リスト `status: DONE(2026-09-06-001)` `hits: 2runs`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B, fidelity-A, naturalness-A
- **再現(2026-09-06)**: rewriter-001 が playbook L55 の例外列挙（Transformer・API・SDK・トークン・GPU のみ）に**エッジAI・IoT・クラウド・データ・ネットワーク・デバイス・サーバー・アーキテクチャ・リアルタイム性・モビリティ**が無く指示で補完。naturalness-001 も「業界標準カタカナを非 tell 保持」が B-2 狙い撃ちの鍵と定量裏付け。免責リストが playbook に無いと推敲役ごとにブレる。
- **適用(2026-09-06)**: playbook B-2 の例外維持リストに一般 IT 定着語群を正式収録＋境界事例（リアルタイム性・モビリティ）の判断基準を注記。

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。出所 detector-A
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B
