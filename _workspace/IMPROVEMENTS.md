# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-07-20（run 001 技術解説/K8s, 002 公的文書/図書館休館）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。2026-06-12-002 は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。**2026-07-20-001 で計数方式依存の 3 倍ブレを実証**: 同一テキストで edit 単位素朴加算=0.567（50%中断誤発火）／LCS 整合=0.337／レーベンシュタイン=0.249。round2 累積では 0.401。
- 出所: rewriter-A, rewriter-B, naturalness-B（06-12）＋ rewriter-001, naturalness-001（07-20）
- 提案: (a) 「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を change_rate から控除。(c) 挿入率を単独併記し、del≫ins の削除主導ケースは中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。(e) **計数は「原文↔最終文の全文 LCS 整合ベース」に固定し edit 単位素朴加算を禁止**（07-20-001 実証）。(f) **多ラウンド時は累積 change_rate でゲート判定**（增分基準だと累積 50% 超を見逃す）。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`

### IMP-002 severity_weighted_score の正規化が未定義で run 間比較不能 `status: done(2026-07-20-001/002)` `hits: 2run`
- 症状: 正規化式が SSOT に無く各 run で場当たり算出。06-12-001 は raw106→92.5（×0.87 拡大）、06-12-002 は raw61.5→68.3（×1.11）、07-20-001 は raw87→76.4（×0.88 縮小）と係数が不整合で run 間比較が成立しない。detector-001/002 が独立に飽和式を逆算し同じ問題を指摘。
- 出所: detector-A, detector-B（06-12）＋ detector-001, detector-002, naturalness-001（07-20）
- 提案: 飽和式 `score = 100·raw/(raw+K)` を SSOT 明記（raw = 5·S1+2·S2+0.5·S3）。K は 06-12-002 を再現する **28.5** に固定。長さ非依存・飽和・再現可能。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出`
- **適用済み 2026-07-20**: taxonomy §スキーマに正規化式・定数 K=28.5・raw 定義を明記、detector.md にスコア算出手順を追記。過去 adhoc スコアは式導入前の値として注記。

### IMP-003 score_before のフィールド契約 `status: ready` `hits: 2run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。
- 出所: naturalness-A（06-12）＋ naturalness-001, naturalness-002（07-20、両者とも detection の値を採用し機能を確認）
- 提案: 「score_before = 02_detection.json の meta.severity_weighted_score」と明文化。**score_before は絶対基準（round をまたいでも固定）、change_rate は累積、と基準が非対称**な点も明記（naturalness-001）。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

### IMP-007 detector が高密度シグナルに引かれ低頻度 S1 を取りこぼす `status: watch` `hits: 1run(2agent)`
- 症状: 2026-07-20-001 の第1文 A-1「開発**において**不可欠な」（SSOT で S1 確定）が推敲前 detection の 27 件に入らず、A-5・B-2 の高密度シグネチャに埋もれた。round1 の naturalness 再スキャン（IMP-006 経路）で初めて表面化し grade を C に落として round2 を強制。手動照合なら S1=0 と誤判定していた。
- 出所: naturalness-001, rewriter-001（round2）
- 提案: detector に「S1 確定カテゴリ（A-1/A-5/A-6/A-10/D-6）を走査後に必ず全数突き合わせる **S1 スイープ**フェーズ」を追加。A-1 は「において/における/に関して/について」を正規表現的に全数拾い、冒頭文・段落頭を重み付け。
- 影響: `ai-tell-detector.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない＋density 定義曖昧 `status: done(2026-07-20-001/002)` `hits: 2run`
- 症状: 絵文字分散・文末単調・E-2/H-1 は分散/文書レベルパターン。単一 start/end では広域 locator になり ai_tell_density が過大化。density「span 総文字数/全体」は重複で 1 を超えうる（06-12-002 は単純和=1773>len）。
- 出所: detector-B, detector-A（06-12）＋ detector-001, detector-002（07-20、両者とも union で回避）
- 提案: `span_type: "contiguous"|"scattered"|"document"` と scattered 用 `occurrences: [[s,e],...]` を追加。density は「重複を除いた被覆文字の**和集合** / input_length」と定義。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`
- **適用済み 2026-07-20**: taxonomy §スキーマに span_type/occurrences/density 和集合定義を追記、detector.md に反映。

### IMP-005 span 重複時の finding/edit カウント規約＋category_summary の閉鎖性 `status: done(2026-07-20-002)` `hits: 2run`
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1、A-6＋A-8 等）に該当。edits/findings が 1:1 前提で category_summary が過小評価。さらに **category_summary が A〜J 固定**で、07-20-002 の新カテゴリ K を append せざるを得ずスキーマ逸脱。suggested_fix が隣接 finding の span と衝突する例も（rewriter-001: f013/f002/f011 のクラスタ干渉）。
- 出所: detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A（06-12）＋ detector-002, rewriter-001（07-20）
- 提案: 「1 span = 主分類 1 finding」を基本とし `secondary_category`（または `merged_findings: [...]`）を許容。category_summary は「findings の主 category 先頭文字を集計」と注記し **拡張カテゴリ（K 等）を許容する open-ended 形**に。suggested_fix に「隣接 finding 干渉フラグ」or 推敲側「span クラスタ統合処理」を手順化。
- 影響: 全 .md のスキーマ節
- **適用済み 2026-07-20**: taxonomy §スキーマに secondary_category・category_summary 集計規約・拡張カテゴリ許容を追記。

### IMP-006 naturalness-reviewer の検出器再実行経路 `status: ready` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合になりがち → 数値が推定値。
- 出所: naturalness-A（06-12）＋ naturalness-001, naturalness-002（07-20）
- **実証（07-20-001）**: 系統再スキャンにしたことで、検出漏れの A-1 S1（IMP-007）を捕捉し grade を正しく C へ。手動照合なら見逃していた。IMP-006 の価値が確定。
- 提案: `ai-tell-detector` をサブエージェントとして再呼び出しする経路を必須化（手動照合禁止）。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

### IMP-008 多ラウンド推敲の差分スキーマにラウンド帰属・base_version が無い `status: watch` `hits: 1run(2agent)`
- 症状: 07-20-001 は grade C → round2 を実行。`03_rewrite_diff.json` の edits[] がフラットで round 帰属が無く、round1 出力を基準にした round2 の before/after と検出器基準の finding_id 体系が混在。change_rate が「増分か累積か」も曖昧。
- 出所: rewriter-001（round2）, naturalness-001
- 提案: edit に `round` と `base_version`（どの版のテキストに対する before/after か）を付与。diff・05 双方に `change_rate_basis: "cumulative_vs_source"` を追加し增分も併記。fidelity 再監査は `audit_scope: round2_reaudit` / `reaudited_edits` で範囲明示（fidelity-001 が実務確立）。ゲートは累積 change_rate で判定。
- 影響: `japanese-style-rewriter.md`, `content-fidelity-auditor.md`, `ai-tell-taxonomy.md §スキーマ`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **★カテゴリ K「過剰敬語（硬い敬語）」** `hits: 1run(4agent)` 出所 detector-002, rewriter-002, naturalness-002, fidelity-002 — v1.0 の A〜J に硬い敬語濫用の枠が無い。公的文書/お知らせジャンルの AI 最頻クセ。実例（07-20-002、同一文書内2型）: 「させていただく」使役＋受益の二重敬語×2（お知らせをさせていただきます／臨時休館とさせていただきます）、「申し上げます」×3（お詫び／お願い×2）、「ご愛顧賜りますよう」。サブパターン案: **K-1 させていただく濫用 / K-2 申し上げます反復 / K-3 二重敬語（お〜いただく＋必要がございます）**。**重要な特性**: A〜J の「消すほど自然」単調減少と異なり **U 字型の適正帯**を持つ（K-core=無条件圧縮 vs K-frame=結び/お詫びの定型は保持しないと失礼）。評価式案 `K_score = max(0, actual−ceiling) + max(0, floor−actual)`（両側ペナルティ、naturalness-002）。→ 別 run（次の day1 公的文書枠）で再現すれば v1.1 昇格。
- **A-5 亜種「〜することが可能になる／可能です」** `hits: 1run` 出所 detector-001 — A-5 より硬く技術 AI 文に頻出。実例①「デプロイすることが**可能になります**」②「実現することが**可能です**」。A-5 の明示サブ変種として追記候補。
- **A-10 動詞リスト拡張「〜に貢献する／寄与する」** `hits: 1run` 出所 detector-001 — A-10 の万能動詞例（提供/もたらす/示す/意味する）に貢献/寄与が漏れ。実例「このアプローチは…削減することに**貢献します**」。
- **D-6/I-4 亜種「〜が期待されます／期待される」結び** `hits: 1run` 出所 detector-001 — 行為者不在の受動的期待による締め。実例「さらなる進化を遂げていくことが**期待されます**」。
- **C 系 redundant restatement** 叙述と箇条書きの二重記載。実例: 06-12-001。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式**「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」。 `hits: 1` 出所 detector-B
- **C-9 導入誘導定型**「さっそく見ていきましょう」式。 `hits: 1` 出所 detector-B

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** `status: ready` `hits: 2run` 出所 fidelity-A（06-12 f019）＋ fidelity-001（07-20、序列/手順順序の保存項目の欠如を技術文書で再指摘）。
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。`status: ready` `hits: 2run` 出所 fidelity-B（06-12）＋ fidelity-001（07-20、手続きの明文化が無いと削除主導 run で条件節脱落を見逃すと指摘）。
- **capability（提供）／agency（実行）の主語意味論** `hits: 1run` 出所 fidelity-001 — A-10 主語交換で「基盤が能力を持つ」と「基盤が自動実行する」を等価化するリスク（07-20-001 r002/f008）。A-10 変換専用の検査観点。
- **概念幅の上位語↔下位語ドリフト** `hits: 1run` 出所 fidelity-001 — レジリエンス→耐障害性で概念幅縮小（resilience/availability/durability/fault-tolerance の区別）。check12 に幅の目盛りを付記。
- **使役/可能/受動の縮約による態の曖昧化** `hits: 1run` 出所 fidelity-001 — 「収束させられます」の多義。check9 に態明示性を追補。
- **modality 強度の順序尺度化（要請>依頼>義務）** `status: ready` `hits: 2run` 出所 fidelity-A（06-12）＋ fidelity-002（07-20、I-3「必要がございます」→「お願いいたします」で義務→依頼の平坦化を指摘。義務係り語尾に「義務性タグ」を付与し推敲側の依頼形化を条件分岐）。
- 「情報を含む削除 vs ボイラープレート削除」二分判定。出所 fidelity-B
- **受動能動化の行為者責任: 行為者が原文から一意確定できる場合のみ能動化** `status: ready` `hits: 2run` 出所 fidelity-B（06-12）＋ fidelity-002, rewriter-002（07-20、「委託業者によって行われる」→能動化 OK／主体不定「業務が停止される」は残置が正解）。

### playbook レシピ追補
- **B-2 技術標準語ホワイトリスト（独立セクション化）** `hits: 1run` 出所 rewriter-001 — 現状は本文中に例外 5 語が散在。アーキテクチャ/インフラストラクチャ/コントロールプレーン/プロビジョニング/ミドルウェア/コンポーネント/ワークロード/スケーリング/クラウドネイティブ 等の境界が推敲役の裁量任せで再現性低。文脈で訳語が割れる語（レジリエンス→耐障害性/回復力）の指針も。
- **A-5 圧縮と E-2 変奏の連動ルール** `hits: 1run(2agent)` 出所 rewriter-001, naturalness-001 — A-5「することができる」を機械的に「できます」へ均すと できます 連発で E-2 を新規悪化（07-20-001 で できます×5連）。「3件以上連続時は 断定『します』・自動詞化・体言止め・『〜のです』へ分散」。detector 側は A-5 finding に `endform_after_fix` を付与し事前予測。
- **A-10 主語保持型 vs 主語交換型の既定を明記** `hits: 1run` 出所 rewriter-001 — 述語だけ実動詞化（保守）か主語ごと人・チームへ交換（fidelity リスク高）か既定が無い。
- **公的文書の敬語圧縮下限規約** `status: ready` `hits: 1run(3agent)` 出所 rewriter-002, fidelity-002, naturalness-002 — (i) お詫び・結びの「申し上げます」は最低1回・全体で2±1、(ii) 依頼は「〜てください」以上の丁寧度を維持し裸命令に落とさない、(iii)「させていただく」→「いたします」まで可・「します」まで崩さない、(iv) 敬語トークン密度を原文≈1.6→1.0〜1.2帯に着地。
- **E-2×公的文書=体言止め禁・語尾機能分化を第一選択** `hits: 1run` 出所 naturalness-002 — 通知=いたします/決定事実=されます/依頼=ください/可能=いただけます/謝罪結び=申し上げます に語尾を割る。受動終止3回超のときのみ館側主語の能動化を検討。
- **C-5 絵文字削除後の文末/区切り吸収ルール**。出所 rewriter-B（06-12）
- **D 系結びは削除一択でなく「最小着地文を残す」**。出所 rewriter-B, naturalness-B（06-12）
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**。出所 rewriter-A（06-12）
- **原文が元から推量の D 系は推量を保持**。出所 rewriter-A（06-12）

### naturalness 判定の精緻化
- **絶対残存数ガードを grade 表に明示**（改善率がしきい値超でも S1>0 なら A/B 不可）`status: ready` `hits: 2run` 出所 naturalness-A/B（06-12）＋ naturalness-001（07-20、改善率74.7%=A相当だが S1×1 で C へ正しく降格を実証）。
- 過推敲シグナルの定量化（敬体/常体混入は文末形態の二値カウント）。出所 naturalness-A
- クラスタ系 finding の severity 降格ルール。出所 naturalness-A
- E-2 文末単調の到達可能ライン緩和（体言止め1箇所以上で合格）。出所 naturalness-B
- **検出器のカテゴリ拡大解釈による過検出補正** `hits: 1run` 出所 naturalness-001 — 検出器が「無生物主語＋具体動詞」を A-10 S1 に拡大適用（SSOT の A-10 中核は万能動詞）。「万能動詞リスト外の動詞は A-10 と数えない」境界注記を detector に。

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 1run(3agent)`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B, fidelity-A, naturalness-A（06-12）

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert）。`status: ready` `hits: 2run` 出所 detector-A（06-12）＋ detector-001, detector-002（07-20、両者とも自己検証を実行し mismatch 0 を報告）。
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B（06-12）
