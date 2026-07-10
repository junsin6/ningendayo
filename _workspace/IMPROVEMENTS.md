# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-07-10（run 001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done(2026-07-10)` `hits: 2run`
- 症状: difflib 文字単位 change_rate が B-2 一括和訳・C-1/C-2 構造編集・純削除で機械的に膨張。day0 Sample B は 54.6% で誤発火。**day1 run 001 は B-2 カタカナ17件の表層置換だけで change_rate 33% と 30% 警告を超過**（意味改変 edit は3件のみ）＝別 run で再現。
- 出所: rewriter-A/B, naturalness-B（day0） + rewriter-001（day1）
- **適用済み（2026-07-10, run 001）**: `rewriting-playbook.md §変更率の数え方` を v1.1 化。`total_change_rate` / `surface_substitution_rate` / `semantic_edit_rate` を分離計上し、**警告閾値は semantic_edit_rate に掛ける**。`SKILL.md §総合判定` に override accept 規約を明記。diff に `edit_kind: surface|semantic` を付す運用。
- 回帰確認: run 001 で override accept が正しく発火（fidelity=pass, 自然度 A）。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done(2026-07-10)` `hits: 2run`
- 症状: 正規化式が SSOT に無く detector 実装ごとに式を発明。**day1 は同一推敲文の再走査で score 2.0 vs 3.5（findings 3 vs 5）と割れ**、検出器間の再現性欠如を実証。
- 出所: detector-A/B（day0） + detector-001/002・自然度再走査（day1）
- **適用済み（2026-07-10, run 001/002）**: `ai-tell-taxonomy.md §検出出力スキーマ` に正規化式 `score = min(100, raw×400/input_length)` を SSOT 唯一の定義として確定。全検出器・自然度再走査で同一式を強制。taxonomist が v1.1 として審査。
- 残: 係数 400 は暫定。v1.0 例（1820字/71.5）との厳密整合は taxonomist 追認結果を次回反映。

### IMP-003 score_before のフィールド契約が曖昧 `status: done(2026-07-10)` `hits: 2run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。
- 出所: naturalness-A（day0） + naturalness-001/002（day1）
- **適用済み（2026-07-10）**: `ai-tell-taxonomy.md §検出出力スキーマ` に「score_before = 02_detection.json の meta.severity_weighted_score、score_after は推敲文へ同一式適用」と明文化（IMP-002 と同じ編集で吸収）。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run`
- 症状: E-2 文末単調・E-1 文長・C 構造は文書全体パターンだが単一 start/end しか持てず、rewriter が「その1span だけ直せばよい」と誤読する緊張。density も過大化。
- 出所: detector-A/B（day0） + detector-001/002・rewriter-001（day1、横断再現）
- 提案: `scope: "span" | "document"` フィールド追加。document スコープでは start/end 任意化（-1）。density は document スコープを除外。E 系は「文書単位 warning、rewriter は任意複数 span で対応可」と明記し rule「finding のある span のみ触る」との緊張を解消。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`, `japanese-style-rewriter.md`
- **次回 Step4 の最有力適用候補（hits=2 到達）。**

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリに該当（I-4＋B-2＋I-1／基盤インフラ=B-2+F-2／進化を遂げる=A-10+D-5／スキルとなる=B-2+A-6）。edits/findings 1:1 前提で category_summary が実態を過小評価。統合 edit の before/after 表記規約も無い。
- 出所: detector-A, rewriter-A/B, naturalness-A, fidelity-A（day0） + detector-001, rewriter-001, fidelity-001, detector-002（day1）
- 提案: 「1 span = 主分類 1 finding」を基本とし `secondary_categories: []` を任意追加。統合 span は 1 単位として before/after 全体で監査（rollback 指示の finding_id を一意化）。
- 影響: 全 .md のスキーマ節
- **次回 Step4 適用候補（hits=2 到達）。**

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 → 実行経路が破綻 `status: ready` `hits: 2run`
- 症状: day0 は手動照合で推定値。**day1 は run 001 の reviewer がサブエージェント検出器を起動したまま background-child デッドロックに陥り、05 JSON を書けず 2 回とも「I'll wait…」で停止**（オーケストレーターが引き取り別 detector を回して確定）。「検出器を再走査せよ」の経路が運用上機能していない。
- 出所: naturalness-A（day0） + naturalness-001（day1、致命的に再現）
- 提案: (a) reviewer が同期的に検出器結果を受け取れる呼び出し規約を確立（子検出を待てないなら、オーケストレーターが推敲後検出を回して reviewer へ渡す2段構成へ変更）。(b) reviewer は「必ず 05 をファイルに書く」を終了条件に。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`
- **P0 級運用障害。次回 Step4 最優先候補。**

### IMP-007 公用文（kokuyobun）ジャンルの許容ライン・プロファイルが未定義 `status: watch` `hits: 1run`
- 症状: 公的文書で「定型敬語（御礼申し上げます／賜りますよう／いただきますよう）＝人間も使う正当表現」と「A-6 こととなる／A-8 受動の機械反復＝AI クセ」の境界が taxonomy/playbook に無い。今回は検出側 meta に `non_detected_genre_conventional` を自前追加し推敲側も手動配慮で凌いだ。
- 出所: detector-002, rewriter-002, fidelity-002, naturalness-002（day1、4agent 横断）
- 提案: taxonomy に genre allow-list 節、検出器 meta に `genre` + `non_detected_genre_conventional[]`、カテゴリ固有 severity のジャンル補正テーブル、playbook に公用文レシピ節（残す定型のホワイトリスト）。
- 影響: `ai-tell-taxonomy.md`, `ai-tell-detector.md`, `rewriting-playbook.md`, `naturalness-reviewer.md`
- 注: 単一 run だが 4 エージェントが独立に指摘。別ジャンルでは出ないため hits は公的文書 run 再登場時に +1。拡張候補欄に記載済み。

---

## P2 — 分類・レシピ・チェックリスト

### modality 強度の順序尺度化 `status: done(2026-07-10)` `hits: 2run`
- 症状: fidelity チェック項目7が二値で、義務→依頼の弱化（f006）や推量の確信度上昇（ことでしょう→はず）を機械判定できない。
- 出所: fidelity-A（day0） + fidelity-001/002（day1）
- **適用済み（2026-07-10）**: `content-fidelity-auditor.md` 項目7に順序尺度 `義務・必要＞指示・依頼＞推奨＞可能・許容＞可能性` と推量尺度 `でしょう＜はず＜に違いない＜である` を明記。1段=flag / 2段以上=rollback の閾値化。

### per-edit の flag（中間ステータス）新設 `status: done(2026-07-10)` `hits: 2run`
- 症状: pass/rollback 二値では「情報保存だが精度低下（マルチモーダル→複数種類の）／強度微変化」を捌けない。fidelity-001/002 が独自に flag を導入して報告。
- 出所: fidelity-A（day0「ニュアンス痩せ」議論） + fidelity-001/002（day1）
- **適用済み（2026-07-10）**: `content-fidelity-auditor.md` に pass/flag/rollback の3値と `per_edit`/`flag_edits` を出力スキーマへ追加。flag は verdict:pass のまま記録。

### 過推敲シグナルの定量化（件数＋根拠span 配列） `status: ready` `hits: 2run`
- 症状: 「シグナル2個でC」だが各シグナルの計上基準が未数値化でレビュアー間再現性なし。
- 出所: naturalness-A（day0） + naturalness-001/002（day1）
- 提案: `over_polish_signals` を件数＋根拠span 配列で出力。閾値（敬体→常体混入=1件で即計上、ございる系過剰削除=定型必須語欠落数、change_rate 二段）を定義。非0時のスキーマも明示。
- 影響: `naturalness-reviewer.md`, `05` スキーマ。**次回 Step4 適用候補（hits=2 到達）。**

### 公用文 grade の「砕けすぎ」検出 `status: watch` `hits: 1run`
- naturalness-002: 残存0でも定型敬語の過剰削除・軽口化で格が下がる劣化を grade 表が捕捉できない。`formal_register_retention`（定型敬語保持率）を必須指標化、公用文では保持率未満で過推敲シグナル+1。IMP-007 と同時適用が望ましい。

### 短文の絶対残存数ガードを grade 表へ `status: ready` `hits: 2run`
- 症状: grade 表が改善率%のみで、短文は残存1件でも%が跳ねる／改善率が出にくい二重問題の救済・厳格化ルールがない。
- 出所: naturalness-A/B（day0） + naturalness-002（day1）
- 提案: grade 表に「絶対残存数」列（例 A=S1 0 かつ 総残存≤2 かつ 改善70%+）。反復系クセは反復解消率（before回数→after回数）も指標化。
- 影響: `SKILL.md §品質等級`, `naturalness-reviewer.md`

### B-2 業界標準語ホワイトリスト＋発火閾値 `status: ready` `hits: 2run`
- 症状: 「密度が閾値を超えたら」の具体閾値がなく、標準語（RAG/HNSW/ベクトル/エンベディング/クラウド/オープンソース）とグレー語（セマンティックサーチ/マルチモーダル/ストレージ/レイテンシ）の線引きが検出器の主観。B-2 修正が副次的に F-5「〜性」残存を生む連鎖も観測（拡張性）。
- 出所: naturalness-B/fidelity-A（day0 の定着カタカナ免責） + detector-001/rewriter-001（day1）
- 提案: taxonomy B-2 に保存/開放の判定リスト（ホワイトリスト＋グレーゾーン注記）と「文書内カタカナ比率 X% 超で発火」の数値閾値。「定義・初出説明を伴う概念語は初出1回に限り除外」。playbook に「B-2 置換で近傍重複が出たら指示対象を統合」「置換後の F-5 副作用チェック」。
- 影響: `ai-tell-taxonomy.md B-2`, `rewriting-playbook.md`

### fidelity チェックリスト追補（day0 由来・継続） `status: ready` `hits: 1run`
- #14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか（f019 型）。削除専用サブチェック（deletion-recall test）。情報を含む削除 vs ボイラープレート削除の二分判定。公用文キーワード（確保・徹底・維持・推進）脱落 watchword（fidelity-002 の f002「確保」脱落で再補強）。行為者マトリクス（主体・行為・受け手）の before/after 突合を公用文で独立項化（fidelity-002）。指標語の極性方向チェック（レイテンシ↔応答速度、fidelity-001）。
- 出所: fidelity-A（day0） + fidelity-001/002（day1 で複数補強）

### playbook レシピ追補（day0 由来・継続） `status: ready` `hits: 1run`
- C-5 絵文字削除後の文末吸収ルール／D 系結びは「最小着地文を残す」下限／機能が必要な接続詞は変奏／原文が元から推量の D 系は推量保持。
- **A-6「〜こととなる／こととなっております」の処方欠落（day1 新規・強）**: playbook A-6 は「〜となっている→〜だ」のみで公用文の「こととなる」型（受動＋こと＋状態化の二重クセ）が未収載。処方例「配布されることとなっております→お配りします」「お知らせが行われることとなります→お知らせします」を追加提案。出所 rewriter-002。
- **公用文ジャンル専用レシピ節が不在**（IMP-007 と連動）。出所 rewriter-002。

### detector 実装（day0 由来・継続） `status: ready` `hits: 1run`
- start/end 自己検証（regex マッチ位置と text_span 一致を assert）＝day1 は両検出器が実施し全件一致を報告（有効性確認）。絵文字正規表現レンジ明示。

### 新パターン候補（taxonomist 審査中 / 拡張候補欄へ記載済み）
- **A-6 サブ例「〜こととなる／こととなっております」** 実例 002 で5回。`hits:1` 出所 detector-002/rewriter-002。
- **A-9「〜ことによって」手段節濫用** 実例 001 で2回。`hits:1` 出所 detector-001/naturalness再走査。
- **技術記事の楽観的予測結び「〜が広がっていくことでしょう／〜になりつつあります」** 実例 001。`hits:1` 出所 detector-001。
- **genre allow-list（プロファイル層）** IMP-007 参照。`hits:1`。
