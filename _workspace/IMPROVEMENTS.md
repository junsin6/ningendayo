# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数（別 run での再現のみ +1）。

最終更新: 2026-09-15（run 001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready`（部分適用 done）`hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。2026-06-12 Sample B 54.6% で誤発火。2026-09-15 も run 001=39.4%（del28.5≫ins10.9）、run 002=19.9%（del14.3≫ins5.7）と全 run で削除主導を再現。
- 出所: rewriter-A/B, naturalness-B（06-12）＋ rewriter-001/002, fidelity-002, naturalness-001（09-15）
- **適用済み（2026-09-15-001/002）**: (a) insert_rate/delete_rate/delete_driven を diff `meta` に分離計上（`japanese-style-rewriter.md`）。(b) delete_driven かつ意味改変 edit ゼロなら 50% 超でも中断せず、fidelity=pass・自然度 A/B で **override accept**（`rewriting-playbook.md §変更率の数え方`, `SKILL.md §総合判定`）。
- **残（未適用）**: 50% 中断を「意味改変 edit 比率」の定量基準へ完全置換（現状は delete_driven ヒューリスティック）。次段で `japanese-style-rewriter.md` に意味改変 edit 比率を算出させる。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done`（適用 run 2026-09-15, taxonomy v1.1）`hits: 2run`
- 症状: 正規化式が SSOT に無く、各検出器が個別逆算。2026-06-12 と 2026-09-15 の全4検出で再現。
- 出所: detector-A/B（06-12）＋ detector-001/002, naturalness-001（09-15）
- **適用済み**: `ai-tell-taxonomy.md §検出出力スキーマ` に `raw=Σ(S1×5+S2×2+S3×0.5)`／`score=100×(1-exp(-raw/45))`／k=45 を明記（v1.1）。アンカー整合を検算（raw95→87.89, raw42→60.68, raw56→71.19）。
- **フォロー**: 旧 run raw106 は式上 90.52 で旧記録 92.5 と約2pt ズレ（taxonomist 指摘）。旧値が別正規化由来の可能性。raw106 系が再現したら k 再校正の要否を確認。

### IMP-003 score_before のフィールド契約が曖昧 `status: ready`（運用回避を実証）`hits: 1run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。
- 出所: naturalness-A（06-12）
- 提案: 「score_before = 02_detection.json の meta.severity_weighted_score」と `naturalness-reviewer.md` へ明文化。
- 09-15 追記: 今 run はオーケストレーターが score_before を明示指定して数値ぶれ消失を実証（naturalness-001/002）。次段で agent .md に明文化すれば `done`。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run`
- 症状: 絵文字・文末単調・文頭接続詞・カタカナ密集は分散パターン。単一 start/end では広域 locator となり ai_tell_density が過大化。09-15 run 001 は density 0.384 と過大、E-2 を末尾段落へ押し込む妥協が再発。
- 出所: detector-A/B（06-12）＋ detector-001/002（09-15）
- 提案: `span_type: "contiguous"|"scattered"|"document"` と `occurrences: [[s,e],...]` を追加。09-15 追記: density 定義の厳密化（重複除去・locator 除外）は taxonomy v1.1 に先行適用済み。span_type スキーマ本体は未適用。
- 隣接候補（NEW, 09-15 detector-001）: A-10 抽象主語+万能動詞は span 長大化するため `anchor`（述語のみ）と `context_span` を分離。

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリに該当。09-15 も「実施されることとなりました」=A-8+A-6、「というテクノロジー」=A-13+B-2 が重畳し、検出器ごとに分割/併合がぶれる。
- 出所: 06-12 全5役 ＋ 09-15 detector-001/002, rewriter-001/002, fidelity-002
- 提案: 「1 span = 主分類 1 finding」を基本とし `merged_findings: [...]` を許容。category_summary は先頭文字集計と注記。taxonomist も「候補の複合偏りは IMP-005 と密接、昇格前に集計規約を決めよ」と指摘。

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だがサブエージェント再呼び出し経路が未整備で手動照合に退避。09-15 も両レビュアーで再現。
- 出所: naturalness-A（06-12）＋ naturalness-001/002（09-15）
- 提案: `naturalness-reviewer.md §処理` に `ai-tell-detector` をサブエージェント再呼び出しする経路を必須化。

---

## P2 — 分類・レシピ・チェックリスト

### 適用済み
- **fidelity チェックリスト #14「接続語/順序語の置換で序列・因果・価値が新規付与」** `status: done`（適用 run 2026-09-15, `content-fidelity-auditor.md`）`hits: 2run`。f019（06-12 並列→基盤の序列混入）＋ f030（09-15 中立「これにより」→受益「おかげで」）で異 run 再現。削除専用サブチェック（deletion-recall test）と情報 vs ボイラープレート二分判定も同時に #14 節へ追記。出所 fidelity-A/B, fidelity-001/002, naturalness-001。

### fidelity チェックリスト追補（未適用）
- **#5論理関係 と #11情報追加 の責任境界を一意化**（主因項目を1つに正規化）。09-15 f030 が #5/#11/#14 に跨り再発。`hits: 2` 出所 fidelity-A, fidelity-001。
- **modality 強度を順序尺度化（要請/推奨/義務/必須）** `hits: 2run` 出所 fidelity-A, fidelity-001/002。09-15 で I-3「義務→依頼」「義務+ヘッジ→断定」の強度判定に必要。
- **【新規】評価度の順序尺度（不可欠>重要>有用…）** 上記は要請系のみ。程度形容詞（優れた/高い/欠かせない/重要な）の目盛りが別途必要。実例 f024（不可欠性↔重要性のダウングレード）。`hits: 1` 出所 fidelity-001。
- **【新規】自己行為への「義務+ヘッジ」複合の断定化許容境界** #7 サブ条項として「命題内の未確定要素が別 span で保存されている場合に限り pass」。実例 f016/f017（09-15-002）。`hits: 1` 出所 fidelity-002, rewriter-002。
- **【新規】A-8 受動→能動化の行為者妥当性チェック**（発信主体 vs 上位機関の含意差）を公的文書用サブチェック化。`hits: 1` 出所 fidelity-002。
- **【新規】watchlist 欄** pass だが将来 fail 化しうる境界 edit を次 run へ引き継ぐ `watchlist: [...]` を監査スキーマに追加。実例 f012/f013/f027。`hits: 1` 出所 fidelity-001。

### playbook レシピ追補
- **C-5 絵文字削除後の文末/区切り吸収ルール**。出所 rewriter-B。
- **D 系結びは削除一択でなく「最小着地文を残す」**（減らしすぎ下限）。出所 rewriter-B, naturalness-B。
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**。出所 rewriter-A。
- **原文が元から推量の D 系は推量を保持** `hits: 2run` 出所 rewriter-A ＋ rewriter-001（f027 で必須だった）。
- **【新規】D-4 ハイプ除去と主張強度保持の下限**: essential/indispensable 系（欠かせない・不可欠）は誇張でなく命題強度語 → 平叙化対象外。「原文が元から推量の D 系は保持」と同型の例外。実例 f024。`hits: 1` 出所 fidelity-001, rewriter(round2)。
- **【新規】H-3/H-1 変奏の valence-neutral 制約**: 指示反復・文頭接続詞の除去/変奏で恩恵・因果の色がつく語（おかげで 等）を避け、中立語（この仕組みで/こうして/これで）へ。実例 f030。`hits: 1` 出所 naturalness-001, rewriter(round2), fidelity-001。
- **【新規】suggested_fix は単独最適であり隣接 finding 適用後の語彙重複は推敲役が最終調整**。実例 f030「これにより→この仕組みで」が f021 の「仕組み」と近接反復。`hits: 1` 出所 rewriter-001。
- **【新規】playbook B-2 変換表に技術系カタカナ語を追補**: プロセス→処理/工程、マッピング→対応づけ、コンテキスト→文脈、パフォーマンス→性能、アーキテクチャ→仕組み、ナレッジベース→知識ベース（ジャンル注記つき）。`hits: 1` 出所 rewriter-001。
- **【新規】公的文書 A-8 受動敬語→能動謙譲の丁寧度保持レシピ**（ぶっきらぼう化回避、「D 系最小着地文」と同型）。`hits: 1` 出所 rewriter-002。

### naturalness 判定の精緻化
- 過推敲シグナルの定量化（敬体/常体は文末形態の二値カウント） `hits: 2run` 出所 naturalness-A ＋ naturalness-001（適用運用済み）。
- クラスタ系 finding はクラスタ崩壊時に個別 severity を降格 `hits: 2run` 出所 naturalness-A ＋ naturalness-002（f004 A-9）。
- E-2 文末単調の到達可能ライン緩和（体言止め1箇所以上で合格） `hits: 2run` 出所 naturalness-B ＋ naturalness-001。**但し書き（新規）**: 体言止めはジャンル依存。公的告知では格を崩すため除外し、文末形態の分散で合格とする。出所 naturalness-002。
- 絶対残存数ガードを grade 表に組込み（S1 が1件でも C 以下） `hits: 2run` 出所 naturalness-A/B ＋ naturalness-001。
- **【新規】語彙反復由来の E-2 残差**: A-5「することができる」を一律「実現します」へ畳むと同一述語が反復し文末単調が語彙面で再発。畳み込み後の語彙変奏を要求。実例 run 001（実現します×3）。`hits: 1` 出所 naturalness-001。
- **【新規】公的文書の politeness floor 定量**: 能動化のあまり「します/ください」だけへ落とさない。敬体公的文書は文末命令形（〜ください）比率が過半で過推敲警告。`hits: 1` 出所 naturalness-002。
- **【新規】A-6「ことになりました」の残差扱い**: detector が suggested_fix に採用した正規着地点（こととなりました→ことになりました）を残存 A-6 と二重計上しない旨を明記。`hits: 1` 出所 naturalness-002。

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 2run`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 半免責で残差 S3 固定。09-15 で detector-001 が エンベディング/アルゴリズム/データセット/アプリケーション を標準語寄りとして免責し再現。出所 naturalness-B, fidelity-A, naturalness-A ＋ detector-001。

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert） `status: 運用定着` `hits: 2run` 出所 detector-A ＋ detector-001/002（全 span assert 一致を実施）。
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B。
- **【新規】B-1 括弧併記は「2回目以降のみ対象」を実装**: 初出1回を除外する出現回数カウントを detector に。実例 f023（ANN 初出1回を S2 化し推敲役が no-op を強いられた）。`hits: 1` 出所 rewriter-001。

### 新パターン候補（taxonomy 拡張候補欄へ登録済み・A〜J 昇格は再現2回目以降）
taxonomy v1.1 §拡張候補欄に実例・出所つきで登録（いずれも `hits: 1` 候補どまり）:
1. **行為者省略の受動連鎖（passive-chaining）** ★日本語固有・公的文書頻出。A-8 は by-passive 限定で「によって」なしの される/られる 連鎖を拾えない。実例 09-15-002。出所 detector-002。
2. **過剰敬語・行政定型（候補カテゴリ K）** ★日本語固有。「お願い申し上げます」「賜りますよう」高密度に受け皿なし。公的文書ジャンル継続投入で hits:2 到達が K 新設の前提（taxonomist）。出所 detector/rewriter/naturalness-002。
3. **自己行為の義務化/推量化**（I-3＋G-1 複合）。実例 09-15-002。出所 detector/rewriter/fidelity-002。
4. **A-13＋B-2「概念名＋という＋カタカナ語」定型**。実例 09-15-001（本文3回）。出所 detector-001。
5. **「〜できるようになります」A-5×A-6 複合の二重冗長**。実例 09-15-001。出所 detector-001。
