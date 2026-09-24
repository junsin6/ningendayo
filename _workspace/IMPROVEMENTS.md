# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-09-24（run 001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。2026-06-12: Sample B 54.6% で誤発火。2026-09-24: run 002 が 35.5%（A-6状態叙述→能動断定・A-8 by-passive→能動化・I-3→指示形化の**節構造組み替え主導**で膨張。削除主導でない新型）、run 001 も 30.0% と警告域直下。いずれも fidelity=pass / 自然度 A。
- 出所: rewriter-A/B, naturalness-A/B（2026-06-12・2026-09-24 の両 run で再現）
- 提案: (a)「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を控除。(c) 挿入率を単独併記し del≫ins は中断対象外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。**(e/新) A-6→能動断定・A-8→能動化・I-3→指示形化のような「意味等価な節変換」を change_rate から控除する項を追加**（2026-09-24 で削除主導でない膨張が確認され、提案(c)では捕捉不能）。(f) 類似度ベース乖離 1-ratio の併記（run001 で 0.164 と実改変小を実証）。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`, `03_rewrite_diff.json` スキーマ

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2run` `applied: 2026-09-24-001/002`
- 症状: 正規化式が SSOT に無く、detector ごとに k を自作（2026-09-24 は detector-A が k=50、detector-B が k=42）→ run 間で score 非互換。
- 出所: detector-A/B, naturalness-A/B（両 run で再現）
- **適用（2026-09-24, taxonomy v1.1）**: `score = round(100×(1−exp(−raw/50)),1)`（k=50 固定・入力長非依存、`raw = S1×5+S2×2+S3×0.5`）を `ai-tell-taxonomy.md §検出出力スキーマ` に確定。`ai-tell-detector.md §スコア算出` にも同式を明記し「独自の k を発明しない」を追加。参考値: raw56→67.4 / raw69→74.8 / raw87.5→82.6 / raw106→88.0。

### IMP-003 score_before のフィールド契約が曖昧 `status: done` `hits: 2run` `applied: 2026-09-24`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定でぶれる。
- 出所: naturalness-A（2026-06-12）。2026-09-24 は naturalness-A/B とも自主的に meta.severity_weighted_score を採用（契約どおり運用され再現的に確認）。
- **適用（2026-09-24, taxonomy v1.1）**: IMP-002 と同じスキーマ節に「score_before = 02_detection.json の meta.severity_weighted_score をそのまま採用、score_after も同一式(k=50)で算出」を明記。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run`
- 症状: 絵文字分散・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく density が過大化。2026-09-24 も E-2 文末単調を代表 anchor に押し込み、run 002 の density=0.461 が連文フル span 計上で過大化。
- 出所: detector-A/B（両 run で再現）
- 提案: `span_type: "contiguous"|"scattered"|"document"` と scattered 用 `occurrences: [[s,e],...]` を追加。density は重複・locator を除いた実 AI クセ文字数ベースと定義。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリに該当。2026-09-24 は A-6＋A-8 の同一 span 重複（提出されることとされています）、A-10＋A-5（することを可能にします）、A-6＋D-1（となっている〜ではないでしょうか）が多発。category_summary が実比率を潰す。
- 出所: detector-A/B, rewriter-A/B, fidelity-A（横断的に最多、両 run で再現）
- 提案: 「1 span = 主分類 1 finding」を基本とし、`merged_findings: [...]` 配列を許容。category_summary は「findings の category 先頭文字を集計」と注記。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だが、**レビュアー自身が subagent として起動されるため Agent/Task ツールを持たず、ai-tell-detector を再呼び出しできない**（2026-09-24 の naturalness-A/B とも構造的に不可能で手動照合に留まった）→ score_after が推定値。
- 出所: naturalness-A（2026-06-12）, naturalness-A/B（2026-09-24）
- 提案（**方向を修正**）: 当初案「サブエージェント再呼び出し必須化」はレビュアー subagent 化構造では成立しない。代替: (a) **オーケストレーターが naturalness 起動前に 03_rewrite.md へ detector を実走査し score_after を 05 に渡す**、または (b) レビュアーに検出処理をインライン同梱。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md §並列検証`

### IMP-007 ジャンル別の許容度（レジスタ）を表す仕組みが無い `status: ready` `hits: 1run(4agent)`
- 症状: 公的文書では受動(A-8)・状態叙述(A-6「とされ」)・定型敬語が正規レジスタなのに、SSOT は A-6 を S1（無条件除去）と規定し衝突。detector は許容度を reason 本文に埋めるしかなく下流が機械的に読めない。run 002 で顕在化。
- 出所: detector-B, rewriter-B, fidelity-B, naturalness-B（同一 run で 4 エージェントが独立提起）
- 提案: `meta.genre`（column|report|blog|official|tech…）＋ genre×category の severity 修飾表（例: official では A-8 手段/原因用法・A-6「とされ」系を S2→S3 降格、E-2 は敬体維持前提でライン緩和、口語化しすぎは逆に過推敲シグナル計上）。fidelity #7 modality の合否閾値も genre 依存に（公的文書では義務降格を毀損候補フラグ）。
- 影響: `ai-tell-taxonomy.md`, `ai-tell-detector.md`, `naturalness-reviewer.md`, `content-fidelity-auditor.md`, `SKILL.md`
- 備考: 次サイクルの最有力適用候補（2 run 目の再現で ready 昇格見込み）。

---

## P2 — 分類・レシピ・チェックリスト

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** `status: done` `hits: 2run` `applied: 2026-09-24-001`
  - 2026-06-12-001 の f019（並列→基盤の序列混入でロールバック）＋ 2026-09-24-001（同型編集で混入なしを明示確認）の 2 run 再現で正式項目化。`content-fidelity-auditor.md` に第14項＋序列・価値マーカー語彙リスト（土台/基盤/前提/最重要/肝心/中核 等）を追加。#5/#11 の二重計上を解消。
- **#15 万能動詞の直接叙述化（A-10: 求める/可能にする→する）で modality・可能性含意・行為主体が変質していないか** `status: ready` `hits: 1run` 出所 fidelity-A（2026-09-24）
- **#16 修辞疑問・状態叙述の断定化（D-1/A-6: 〜ではないでしょうか／となっている→です）で推量 modality を原意超過で強化していないか**（「修辞疑問は断定化可・真正推量は保持」の二分を #7 サブ判定に） `hits: 1run` 出所 fidelity-A（2026-09-24）
- **#17 法令/公的文書特有チェック（legal-register test）** `status: ready` `hits: 1run(2agent)` 出所 fidelity-A/B（2026-09-24）
  - (a) 「〜によって」の行為者/原因/手段/根拠 4 用法弁別が正しいか、(b) 「に基づいて/に従って/に則って」等 法令準拠表現の相互変換が概念差を生まないか、(c) 義務レジスタ（しなければならない/必要がある/原則として/ものとする）の強度保存を #7 とは別立てで公的文書時のみ厳格判定。
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。`status: ready` `hits: 1run` 出所 fidelity-B
- 「情報を含む削除 vs ボイラープレート削除」二分判定。2026-09-24-002 で削除ゼロ運用の好例により妥当性裏付け。出所 fidelity-B
- #5論理関係 と #11情報追加 の責任境界を一意化（接続語起因は #14 を主因とする規約で確定済み。他要因は要整理）。出所 fidelity-A（2 run 再現）
- **modality 強度を順序尺度化（真正推量＜修辞疑問＜状態叙述＜断定／要請＜推奨＜義務＜必須）** `status: ready` `hits: 2run` 出所 fidelity-A（2026-06-12）, fidelity-A/B（2026-09-24）
  - #7 の pass/fail を定量化。公的文書では義務降格を 1 段階でも毀損候補フラグにする genre 連動（IMP-007 と連結）。
- **modality 境界の fidelity/naturalness 責任分担を SKILL.md §総合判定で規約化** 提案: 意味の真偽が変われば fidelity 主管、真偽不変で語調のみ過剰なら naturalness 主管。`hits: 1run` 出所 fidelity-A（2026-09-24）

### playbook レシピ追補
- **A-8「によって」用法弁別レシピ** `status: ready` `hits: 1run(3agent)` 出所 detector-B, rewriter-B, fidelity-B（2026-09-24）
  - playbook A-8 は「政府によって定められた→政府が定めた」の行為者ケースしか示さない。3〜4 分岐を明文化: 行為者→能動化／手段→「で」／原因→「により」／根拠→「に基づき」。taxonomy A-8 にもサブタグ(agent/means/cause/basis)を提案。
- **過剰・二重敬語の段階的軽量化レシピ** `status: ready` `hits: 1run(2agent)` 出所 detector-B, rewriter-B（2026-09-24）
  - 「いただく＋必要＋ございます」等の敬語重畳を格を保ちつつ一段階だけ下げる段階表。挨拶ボイラープレート（賜り厚く御礼〜/お願い申し上げます）は公的文書の定型として保持。新カテゴリ（K系 or I 追補「過剰・二重敬語」）候補として taxonomist 審査へ。
- **推敲副作用ガード: 「の」3連チェック** `status: ready` `hits: 1run` 出所 naturalness-B（2026-09-24）
  - A-1/A-2 を属格「の」化で解消すると A-11「の」連鎖を新規誘発（run 002「本市の個人情報の開示請求の手続き」）。推敲後に「の」3連を走査し、連鎖時は 1 箇所を動詞句/別助詞で崩すガードを A-1/A-2 レシピに追加。
- **A-10 enable/require 直訳 専用行** `status: ready` `hits: 1run(2agent)` 出所 detector-A, rewriter-A, fidelity-A（2026-09-24）
  - 「〜を可能にする（enable）／〜を求める（require）」は A-10 の頻出定型。「行為主体を主語に戻すか直接叙述化」の専用行を playbook A-10 に追加。
- **敬体での文末変奏 許可リスト（E-2）** `status: ready` `hits: 1run(2agent)` 出所 rewriter-A, naturalness-A（2026-09-24）
  - 敬体で使える変奏: です／でしょう／ません／ました／体言止め(=名詞終止のみ)／ましょう。**平叙の常体終止(〜る/〜だ)は敬体違反**、「だ」の敬体等価は「です」。ます系終止は敬体の構造的下限があり、体言止め 1 箇所以上で合格ラインとする（過推敲回避）。
- **C-5 絵文字削除後の文末/区切り吸収ルール**。出所 rewriter-B（2026-06-12）
- **D 系結びは削除一択でなく「最小着地文を残す」**。出所 rewriter-B, naturalness-B（2026-06-12）
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**。出所 rewriter-A（2026-06-12）
- **原文が元から推量の D 系は推量を保持**。出所 rewriter-A（2026-06-12）
- **B-2 訳語重複の分散**: 同一訳語が近接3回以上（コンセプト/アプローチ→ともに「考え方」）になる場合の代替語提示を変換表に注記。`hits: 1run` 出所 rewriter-A（2026-09-24）

### naturalness 判定の精緻化
- 過推敲シグナルの定量化（敬体/常体混入は文末形態の二値カウントで機械検出）。2026-09-24 で naturalness-A/B とも実施（敬体14/常体0 等）。出所 naturalness-A/B
- クラスタ系 finding（B-2 密集・C-1 列挙）はクラスタ崩壊時に個別 severity を降格。出所 naturalness-A
- E-2 文末単調の到達可能ライン緩和（体言止め1箇所以上で合格）。2 run で再現。出所 naturalness-B（2026-06-12）, naturalness-A（2026-09-24）
- 絶対残存数ガードを grade 表に組込み（改善率が高くても S1 が1件でも C 以下）。出所 naturalness-A/B
- **公的文書ジャンルの残存許容ライン**: (a) 行為者が文脈自明な agentless 受動は減点対象外、(b) 定型主題提示(につきましては)・表題慣行(について)は 1〜2 回まで免責、(c) 口語化・くだけ過ぎは公的文書の格毀損として過推敲シグナル計上。`hits: 1run` 出所 naturalness-B（2026-09-24, IMP-007 と連結）

### 定着カタカナ語 B-2 免責リスト `status: done` `hits: 2run` `applied: 2026-09-24`
- ルーティン・モチベーション・データドリブン・リモートワーク・クラウド 等の定訳が冗長になる定着語を B-2 から半免責し残差 S3 固定。
- 出所: naturalness-B, fidelity-A, naturalness-A（2026-06-12）, detector-A（2026-09-24 再現）
- **適用（2026-09-24, taxonomy v1.1 + playbook）**: `ai-tell-taxonomy.md B-2` に半免責リスト＋判定基準(a)(b)、`rewriting-playbook.md B` に「開かない定着カタカナ語」注記を追加。

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。**2026-09-24 の detector-A/B が全 finding で実施し ai-tell-detector.md §スコア算出 に必須化を明記済み**。出所 detector-A
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B
- `base_severity` と `applied_severity`＋降格理由フィールドを設け、密度基準の severity 降格（J-3 単発→S3 等）を機械可読に。`hits: 1run` 出所 detector-A（2026-09-24）

### 新パターン候補（taxonomist 審査待ち）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。実例: 2026-06-12-001。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「〜してみてはいかがでしょうか」。実例 2 件。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式。 `hits: 1` 出所 detector-B
- **A/E 系: 無生物主語の同型構文連鎖** 「Xは…できます／Yは…できます／Zは…可能にします」と主語＋述語の型まで一致した連発（C-1 とも E-1/E-2 とも別軸の「構文テンプレ反復」）。実例: 2026-09-24-001 第4段（4連）。 `hits: 1` 出所 detector-A
- **A-5/A-10 交差: 〜することを可能にする（enable 直訳）** 実例: 2026-09-24-001。 `hits: 1` 出所 detector-A
- **K 系（新）or I 追補: 過剰・二重敬語** 「格別のご理解とご協力を賜り厚く御礼申し上げます」「ご確認いただく必要がございます」。公的文書では S3 固定・くだけた AI 文では S2 の genre 連動。実例 2 件: 2026-09-24-002。 `hits: 1` 出所 detector-B, rewriter-B
