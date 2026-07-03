# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-07-03（run 001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done` `hits: 2run` `applied: 2026-07-03-001/002`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除・A-5 定型短縮で機械的に膨張。day0 Sample B 54.6%、day2 run 001 も全文 35.6%（span_only 30.3%）で 30% 警告を超過するが実際は fidelity=pass / 自然度 A。
- 出所: day0 rewriter-A/B・naturalness-B、day2 rewriter-001・naturalness-001（別 run 再現）
- **適用（2026-07-03）**: `rewriting-playbook.md §変更率の数え方` を二指標に分離（`change_rate` 全文=参考 / `change_rate_span_only` 語句改変のみ=主判定、安全な定型短縮テーブルを控除、insertion_rate 併記）。`SKILL.md §総合判定` に「変更率ゲート」を追加（span_only 50%超かつ fidelity fail→hold、30〜50%でも fidelity=pass かつ A/B→override accept・要 summary 明記）。`naturalness-reviewer.md` の過推敲シグナルを span_only 基準へ。
- 残: 「安全な定型短縮テーブル」の網羅拡充は継続（次サイクルで語彙追加）。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2run` `applied: 2026-07-03-001/002`
- 症状: 正規化式が SSOT に無く、run ごとに detector が別式を発明（day2 は detector-001 が `raw/len×1000`＝100張り付き、detector-002 が `raw/(0.15×len)×100`）。day0 の 92.5 とも非可換で run 横断比較不能。
- 出所: day0 detector-A/B、day2 detector-001・detector-002・naturalness-002（別 run 再現）
- **適用（2026-07-03）**: `ai-tell-taxonomy.md §検出出力スキーマ` に正規化 SSOT を固定 — `severity_weighted_score = round(100×(1−exp(−raw/60)),1)`、raw=S1×5+S2×2+S3×0.5、**K=60 固定・input_length 非依存**。`meta.score_formula` を必須化。`ai-tell-detector.md §スコア算出` も同式へ改訂。taxonomy v1.0→v1.1。
- 注: day0 run の旧 score（92.5 等）は新式では別値になる（findings 不変）。回帰ではなく意図的な基準統一。v1.1 節に明記。

### IMP-003 score_before のフィールド契約が曖昧 `status: done` `hits: 2run` `applied: 2026-07-03-001/002`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。
- 出所: day0 naturalness-A、day2 naturalness-001・naturalness-002（両者が「IMP-003 準拠」と明記し契約を実運用）
- **適用（2026-07-03）**: `ai-tell-taxonomy.md` と `naturalness-reviewer.md` に「score_before = 02_detection.json の meta.severity_weighted_score、score_after は同一正規化式(K=60)で再走査」を明文化。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: done` `hits: 2run` `applied: 2026-07-03-001/002`
- 症状: E-2 文末単調・絵文字散在・H-1 文頭接続詞公式は分散パターン。単一 start/end では広域 locator にするしかなく density 過大化。day2 は E-2 を代表 span に逃がし density 過小/過大の両振れ。
- 出所: day0 detector-B/A、day2 detector-002・naturalness-001・naturalness-002（別 run 再現）
- **適用（2026-07-03）**: `ai-tell-taxonomy.md` と `ai-tell-detector.md` に `span_type: "contiguous"|"scattered"|"document"` と `occurrences:[[s,e],...]` を追加。density は occurrences のユニオン被覆で定義（重複・広域 locator を二重計上しない）。start/end は後方互換で先頭出現を温存。

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリに該当（day0 I-4＋B-2＋I-1、day2 f006 A-6＋A-5＋I-1＋敬語 / f007 I-3＋A-11＋敬語）。edits/findings が 1:1 前提で category_summary が実態を過小評価。
- 出所: day0 detector-A・rewriter-A/B・naturalness-A・fidelity-A、day2 detector-002・rewriter-002・fidelity-001（別 run 再現・横断的に最多）
- 提案: 「1 span = 主分類 1 finding」を基本とし `categories:[...]`（複数タグ）＋主カテゴリ指定、または `merged_findings:[...]` を許容。diff スキーマに `merge_group` を足しロールバック単位を明確化。category_summary は「主カテゴリ先頭文字を集計」と注記。
- 影響: 全 .md のスキーマ節。**次サイクルの適用第一候補**。

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: done` `hits: 2run` `applied: 2026-07-03（明文化）`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーが手動照合になりがち。
- 出所: day0 naturalness-A、day2 naturalness-001・naturalness-002（両者「IMP-006 準拠で実走査」と報告）
- **適用（2026-07-03）**: `naturalness-reviewer.md §処理` を「実スキャン（手動照合禁止）」と明文化。day2 は両レビュアーが実走査で score_after を算出済み。サブエージェント再呼び出し経路の必須化は次段階（現状は同一基準の自己再走査で担保）。

### IMP-007 受動→能動化での行為者付与に専用チェックが無い `status: open` `hits: 1run`
- 症状: A-8 能動化で原文が明示しない主語を勝手に確定するリスク。day2 run 002 は全件安全（発話者＝市が一人称告知で一意、動作対象＝利用者で一意）だったが、判定根拠が自然文説明のみで再現可能な基準になっていない。
- 出所: day2 fidelity-002
- 提案: fidelity #9 に3分岐サブチェックを機械化 —(a)付与主語=文書の発話者に一致→安全 (b)付与主語=動作対象で一意→安全 (c)それ以外/複数候補→毀損。公的文書は「発話者＝実施主体」を監査前メタデータ化（挨拶・結び・自称部署名から発話者を先に確定）。
- 影響: `content-fidelity-auditor.md`。

### IMP-008 等級表に change_rate 単独ゲートが無い（非対称） `status: ready` `hits: 1run(強)`
- 症状: day2 run 001 で change_rate 35.6%（span_only 30.3%）が harness の 30% 警告を超えているのに、過推敲シグナル「2個」が C 降格の閾値のため 1個だと A のまま。残存側（S1/S2/改善率）だけが等級を支配し過推敲側が実質1票の非対称。
- 出所: day2 naturalness-001
- 提案: `change_rate_span_only>0.30` を単独で最低 B にキャップ、`>0.50` で強制 hold。IMP-001 の変更率ゲートと統合済み（SKILL 側に反映）だが、等級表本体（naturalness の grade 決定）への織り込みは未。**次サイクル適用候補**。
- 影響: `SKILL.md §品質等級`, `naturalness-reviewer.md §品質等級`。

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査 — v1.1 候補欄へ追記済み）
- **B-4 カタカナ動詞化「〜する / 〜を行う」** `status: ready(2run)` 「登録を行う／アグリゲーションを行う／ドライブする」。B-2（名詞）と別軸のサ変・カタカナ動詞化。実例: day0「ドライブしていく」＋ day2「アグリゲーションを行う」「登録を行っていただく」= **再現 2run で昇格条件充足**。出所 detector-001(cross-run)・rewriter-002・fidelity-002。→ taxonomist 審査で本体昇格を判定中。
- **K. 過剰敬語・二重敬語** `status: candidate(1run3agent)` 「必要がございます／させていただきます／いただけますと幸いです」。★日本語固有。挨拶・依頼・結びの正当な公文定型はホワイトリストで非除去。実例: day2 002。別 run 再現待ち。出所 detector-002・rewriter-002・naturalness-002。
- **A-8 定義拡張（行為者省略受動）** `status: candidate(1run)` by 句なしの「開始される／進められてまいります」。現 A-8 は by-passive 限定。二分割 or 定義拡張案。実例: day2 002。出所 detector-002・fidelity-002。
- **D-4 サブ: ブログ見出しハイプ公式「〜とは何か──…徹底解説」** `status: candidate(1run)` 実例: day2 001 タイトル。出所 detector-001・rewriter-001。
- **C 系: redundant restatement**（day0）叙述と箇条書きが同内容を二重記載。`hits:1` 出所 day0 detector-A。
- **D-7 ブログ結び呼びかけ公式**（day0）「今回は〜ご紹介しました」等。`hits:1` 出所 day0 detector-B。
- **C-9 導入誘導定型**（day0）「さっそく見ていきましょう」式。`hits:1` 出所 day0 detector-B。
- **段落冒頭接続詞公式 C-7 の一般化**（day2）語彙を問わず「まず→また→さらに→このように」4段連続。C-7 は「一方/しかし/結局」限定で受け皿がなく H-1 に寄せた。`hits:1` 出所 detector-001・naturalness-001。

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** `status: ready` `hits: 2run` — day0 f019（並列→基盤の序列混入）＋ day2 fidelity-002「接続詞削除の論理機能が他要素で担保されているか」。**機能の欠落と追加を両面で見る**項目として #5 に統合可。次サイクル適用候補。出所 day0 fidelity-A・day2 fidelity-002。
- **modality を順序尺度化（要請/推奨/義務/必須）** `status: ready` `hits: 2run` — #7 を pass/fail 二値でなく `modality_scale` 順序値の Δ で判定（Δ≥2 fail, Δ=1 warn）。day2 f001/f003 可能→断定、f017 求められる→なければならない が「先例で pass」に頼り主観的。出所 day0 fidelity-A・day2 fidelity-001。
- **#5論理関係 と #11情報追加 の責任境界を一意化** `status: ready` `hits: 2run` — decision-tree（命題が新規抽出可能なら #11、関係語のみなら #5）。day0 f019 は両項 fail で同一事故を二重計上、day2 fidelity-001 も同型指摘。出所 day0・day2 fidelity-001。
- **削除専用サブチェック（deletion-recall test）** `hits: 2run` — 原文の各内容語・関係語が推敲文のどこに写像されたか alignment table（保持/溶解/削除の三値）を必須化し「削除」タグ全件を命題性レビュー。出所 day0 fidelity-B・day2 fidelity-001。
- **borderline 可視化 `status: pass_with_notes` の追加** `hits:1` — pass/fail のみだと「pass だが要注意」が note に埋没。day2 fidelity-001 が4点の borderline を報告。出所 day2 fidelity-001。
- 「情報を含む削除 vs ボイラープレート削除」二分判定（day0 fidelity-B）。
- B-2 近似の含意損失を定量化（含意保存スコア、閾値超過で #12 warn）。day2 f014「ミッションクリティカル→重要度の高い」。出所 day2 fidelity-001。

### playbook レシピ追補
- **定着カタカナ語 B-2 免責リスト＋ジャンル別ホワイトリスト** `status: ready` `hits: 2run` — day0（ルーティン・モチベーション・データドリブン）＋ day2（エッジ/クラウド/ネットワーク/レイテンシ/トラフィック/アーキテクチャ/ワークロード/インフラ/セキュリティ/プライバシー を技術解説ジャンルで保存、逆に テクノロジー→技術/メリット→利点/アドバンテージ→強み/ソリューション→解決策/アプローチ→方法 を置換表へ）。分野別（技術/公文）の保存語・開放語リストを references に。出所 day0 3agent・day2 rewriter-001・naturalness-001。**次サイクル適用候補**。
- **A-8 受動能動化の格変換指針**（が→を の格助詞変換）が playbook に無い。出所 day2 rewriter-002。
- **A-2「につきましては」系の公文サブ表**（につきましては→は/では、にあたっては）。出所 day2 rewriter-002。
- **A-5 が5回超のときの推奨バリエーション順序**（言い切り→できる→名詞化→られる→省略）。出所 day2 rewriter-001。
- **複合パターン表**（〜化が進められる = F-4 名詞化＋A-8 受動）。出所 day2 rewriter-002。
- **C-5 絵文字削除後の文末/区切り吸収ルール**（day0）。出所 day0 rewriter-B。
- **D 系結びは「最小着地文を残す」**（day0）。出所 day0 rewriter-B・naturalness-B。
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**（day0）。出所 day0 rewriter-A。
- **原文が元から推量の D 系は推量を保持**（day0）。出所 day0 rewriter-A。

### naturalness 判定の精緻化
- **E-2 到達可能ラインの明文化＋ジャンル別ルーブリック** `status: ready` `hits: 2run` — 敬体短文書では「ます偏在 S3」が構造的に残る（体言止め・でしょうは公文の格を壊し使えない）。公文向け E-2 は「敬体内バリエーション率（幸いです/存じます/します/です 等）」で評価する別ルーブリック。無限推敲を抑止。出所 day0 naturalness-B・day2 naturalness-001・naturalness-002。**次サイクル適用候補**。
- **公文ジャンル別閾値プロファイル** `status: ready(new)` `hits:1run(2agent)` — 挨拶・結びの定型を E-2/B-2/I-4 の分母から除外、主題カタカナ語（サービス・オンライン・ポータルサイト・アカウント）を免除、severity を一段降格。SKILL 側にジャンル係数を持たせる。出所 day2 rewriter-002・naturalness-002。
- **クラスタ崩壊時の降格ルール明文化** — 部分解消（前半修正・核残存）の降格幅（S1→S2 か S1→S3 か）を構造要素チェックリストで基準化。day2 f009「万能動詞は落ちたが擬人化+受動が残る=1段降格 S2」。出所 day0 naturalness-A・day2 naturalness-001。
- **過推敲の定量化**（体言止め比率・平均文長急落・文数増加率の両側閾値）。出所 day0 naturalness-A・day2 naturalness-001。
- **S3 残存密度の副次ゲート**（S1=0・S2=0 でも S3 多数の短文を等級式が拾えない）。出所 day2 naturalness-002。
- 絶対残存数ガードを grade 表に組込み（day0）。出所 day0 naturalness-A/B。

### detector 実装
- **start/end 自己検証**（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない） `status: done` `applied: 2026-07-03` — `ai-tell-detector.md` に明記。day2 両 detector が自己検証済み。出所 day0 detector-A・day2 detector-001/002。
- **offset_basis の明示**（先頭からの Python str index・改行/タイトル含む） `status: done` `applied: 2026-07-03` — detector.md に追記。出所 day2 detector-001。
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`（day0）。出所 day0 detector-B。
- J-3 二倍ダッシュの見出し用途を過検出しない但し書き（day2 見出し「──」は約物）。出所 day2 detector-001。
