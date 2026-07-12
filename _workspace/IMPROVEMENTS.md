# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数（別 run での再現のみ +1）。

最終更新: 2026-07-12（run 001 技術記事, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。06-12 Sample B 54.6% で誤発火。**07-12-001（技術記事）で再現**: churn の 75%（212/282字）が純削除なのに change_rate 0.333 と出て 30% 警告を誤って焚いた（実際は fidelity=pass・自然度 A）。
- 出所: rewriter-A(06-12), rewriter-B(06-12), naturalness-B(06-12), **rewriter-001(07-12), naturalness-001(07-12)**
- 提案: (a)「語句改変率（置換のみ）」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を控除。(c) 挿入率を単独併記し del≫ins の削除主導ケースは中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`
- 備考: 指標ロジック自体の変更（コード/式）が要るため未適用。次点の適用候補。

### IMP-002 severity_weighted_score の正規化式が未定義で detector 間不整合 `status: done`（適用 2026-07-12-001/002）`hits: 2run`
- 症状: 正規化式が SSOT に無く、**07-12 で detector-001 と detector-002 が独立に別式を逆算**（001: 有理式 raw/(raw+8.6)、002: 指数式 100(1−e^(−raw/41))）。両者とも 06-12 の 92.5 を再現するが、他点で乖離（有理式は raw=26 で 75、指数式は 47）。高密度短文で saturate する欠陥も併発。
- 出所: detector-A(06-12), detector-B(06-12), **detector-001(07-12), detector-002(07-12)**
- **適用**: taxonomy §検出出力スキーマに確定式 `score = 100·(1 − exp(−raw/41))`（raw = 5·S1+2·S2+0.5·S3、K=41）を明記。2 参照点（raw=106→92.5, raw=26→47.0）を同時再現することを検証済み。飽和型採用理由も明記。detector.md にも反映。
- 影響: `ai-tell-taxonomy.md`(→v1.1), `ai-tell-detector.md`

### IMP-003 score_before / weight_scheme のフィールド契約が曖昧 `status: done`（適用 2026-07-12-001/002）`hits: 2run`
- 症状: score_before にどの値を使うか未固定。加重式が meta に保存されず手動確定でスコアが再現不能。
- 出所: naturalness-A(06-12), **naturalness-001/002(07-12)**
- **適用**: 「score_before = 02_detection.json の meta.severity_weighted_score」を naturalness-reviewer.md と taxonomy に明文化。`meta.weight_scheme` の記録を必須化。score_before 低文書は絶対残存数を一次指標にする注記も追加。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: done`（適用 2026-07-12-001/002）`hits: 2run`
- 症状: 絵文字散在・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく density が過大化。**07-12 でも両 detector が E-2（です・ます単調）を強制 span 化できず非計上を選ばざるを得なかった**。
- 出所: detector-B(06-12), detector-A(06-12), **detector-001/002(07-12)**
- **適用**: taxonomy に `scope: "contiguous"|"scattered"|"document"`、scattered 用 `occurrences:[[s,e],…]`、document 用 null 位置許容を追加（後方互換）。detector.md に反映。density は locator 重複を除いた実文字数と定義。
- 影響: `ai-tell-taxonomy.md`(→v1.1), `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 1run(5agent)`
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。
- 出所: detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A（06-12 横断）
- 提案: 「1 span = 主分類 1 finding」を基本とし `merged_findings:[...]` を許容。category_summary は「findings の category 先頭文字を集計」と注記。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer の検出器再実行経路が未整備 `status: done`（部分適用 2026-07-12-001/002）`hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だが、**07-12 で両 naturalness-reviewer が detector サブエージェントを background 起動したまま停止し 05 を書けず、コーディネーターの再開指示で手動確定した**。再実行経路が実運用で詰まることを実証。
- 出所: naturalness-A(06-12), **naturalness-001/002(07-12)**
- **適用（部分）**: naturalness-reviewer.md に「手動照合は原則禁止、ただし残存が S2/S3 数件に収束し grade が確定的なら手動可・その旨 notes 明記。C グレード境界に近い run は検出器実走査を必須」という閾値ベース分岐を明文化。
- 残課題: サブエージェント再帰起動が停止する harness 挙動への恒久対策（同期実行の強制 or オーケストレーター側での再走査代行）。
- 影響: `naturalness-reviewer.md`, `SKILL.md`

---

## P2 — 分類・レシピ・チェックリスト

### 適用済み
- **B-2 分野標準レジスタ語の免責リスト** `status: done`（適用 2026-07-12-001/002）`hits: 2run`
  - 06-12 の「定着カタカナ語（ルーティン・モチベーション・データドリブン）」＋07-12-001 の検索/LLM 標準語（エンベディング・ベクトル・クエリ・レイテンシ・リコール・RAG・ANN・HNSW・IVF・ハルシネーション）を統合。過剰和訳（→埋め込み等）は過推敲シグナルと明記。playbook §B-2 と taxonomy B-2 に反映。出所: detector-001, rewriter-001, fidelity-001, naturalness-001 ＋ 06-12 naturalness-B/fidelity-A。

### 新パターン候補（taxonomist 審査待ち／審査中）
- **手段・原因の「によって」** → **A-3b として v1.1 本項化（done, 2026-07-12 taxonomist 審査済み）**。A-3(通じて)にも A-8(行為者後置受動)にも当てはまらない「普及によって」「更新によって」「〜することによって」型を新設。A-8 に弁別注記（受動＋行為者=A-8 / 手段・原因=A-3b）。単独 S1 化しない密度ベース運用も明記。`hits: 2run` 出所 detector-001, detector-002。
- **I-6 過剰謙譲・冗長敬語（★日本語固有）** 「させていただく」「所存であります」「いただく必要がございます」。公的文書ジャンルの最強クセ。`hits: 1run(002 で3インスタンス)` 出所 detector-002, rewriter-002。→ taxonomist 審査へ。
- **ジャンル別「儀礼定型 allowlist」** 公的文書の「お詫び申し上げます／賜りますよう／何卒よろしく」等を過検出しない仕組み（taxonomy か detector 設定）。`hits: 1run(002 で4agent)` 出所 detector-002, rewriter-002, fidelity-002, naturalness-002。→ taxonomist 審査へ。

### fidelity チェックリスト追補
- **#11 語義併記・定義グロスの判定ルーブリック** 既出専門語への丸括弧注釈（例「ハルシネーション（事実と異なる生成）」）が情報追加か可読化か。基準案: (i)既出語 (ii)注記が事実として正確 (iii)新主張/例/数値を含まない の3条件全充足で pass。`status: ready` `hits: 2run`（06-12 f019 の #5/#11 境界 ＋ 07-12-001 f026）出所 fidelity-A, fidelity-001。
- **modality「予定/見込み」ヘッジ除去の保存基準** 「案内する予定でございます→案内します」で計画性マーカー脱落。除去可は当該行為が原文他所でも確定扱いの場合のみ。単独ヘッジは保持優先。`status: ready` `hits: 1run` 出所 fidelity-002。※過推敲（文末反復解消）が modality 保存より優先された疑いも記録。
- **agentless-passive 能動化の条件** 主体非明示の受動（「措置が講じられる」）の能動化は、発信主体＝実施主体が文脈で保証される場合に限る。by-passive（主体明示）とはリスクが本質的に異なる。`status: ready` `hits: 1run` 出所 fidelity-002。
- （既出・06-12）#5論理関係 と #11情報追加 の責任境界を一意化（構造編集が関係を壊した→#5 / 新しい価値付けを足した→#11）。`hits: 2run` 出所 fidelity-A, fidelity-001。
- （既出・06-12）削除専用サブチェック（deletion-recall test）、情報削除 vs ボイラープレート削除の二分判定。出所 fidelity-B。

### playbook レシピ追補
- **A-10 万能動詞→具体動詞 変換表** 担う→中核にある/最適化する、可能にする→できる/する、もたらす→両立させる/実現する。抽象主語＋万能動詞の行為者復元処方。`status: ready` `hits: 1run` 出所 rewriter-001。→ taxonomist にも回付。
- **工程叙述では受動を無理に能動化しない** パイプライン列挙（計算されます/ランキングされ/返却されます）は能動化すると行為者を勝手に確定させ意味を足す危険。`hits: 1run` 出所 rewriter-001。
- （既出・06-12）C-5 絵文字削除後の文末吸収ルール、D 系結びの「最小着地文を残す」下限、機能が必要な接続詞（しかしながら）は変奏、原文が推量の D 系は推量保持。

### naturalness 判定の精緻化
- **儀礼保持率／減らしすぎ下限の指標化** 公的文書必須トークン（お詫び申し上げます/賜りますよう/お願い申し上げます）のチェックリスト化。保持率が閾値（例 80%）を下回れば「減らしすぎ」シグナル。現状は残存ゼロ高評価の片側バイアスで削りすぎを構造的に検出できない。`status: ready` `hits: 2run`（06-12 naturalness-B の下限指摘 ＋ 07-12-002）出所 naturalness-B, naturalness-002。
- **ジャンル別フロア score** 技術記事はカタカナ機能語化で score_after を 0 にできない（実質下限 2〜5）。improvement_rate だけ見ると誤った 2 次推敲要求が出る。`hits: 1run` 出所 naturalness-001。
- **E-2 文末変奏の機械指標** distinct-ending 比率・同一末尾の最大連続数・文末エントロピー。境界事例の主観揺れを抑制。`hits: 1run` 出所 naturalness-002。
- （既出・06-12）過推敲シグナルの定量化（敬体/常体混入の二値カウント）、クラスタ系 finding のクラスタ崩壊時 severity 降格、絶対残存数ガードを grade 表へ。`hits: 2run`。

### detector 実装
- **B-2 の finding 化件数基準** 技術記事で置換可能カタカナが十数語密集し全件出すと B が突出（07-12-001 で 14 件）しスコアが歪む。「同一カテゴリ代表 N 件＋density を reason に集約」or 被覆率メトリック化。`status: ready` `hits: 2run`（06-12 の絵文字8個 density 過大 ＋ 07-12-001 B-2 14件）出所 detector-B, detector-001。
- **id 採番順の契約** start 昇順 or カテゴリ順を SSOT で固定（再計測時の diff 安定）。`hits: 1run` 出所 detector-001。
- （既出・06-12）start/end 自己検証 assert、絵文字正規表現レンジ明示。
