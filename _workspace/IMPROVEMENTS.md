# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数（**別 run での再現のみ +1**）。

最終更新: 2026-06-27（run 001 技術解説/ゼロトラスト, 002 公的文書/コンビニ交付）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done(適用 2026-06-27-001/002)` `hits: 2runs`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。
  - 06-12 Sample B 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。Sample A 47.6%。
  - **06-27 再現**: 公的文書 run 002 が 0.504 で `hold_and_report` トリップ（削除245字/挿入97字＝削除が編集予算の72%、純減148字、新情報追加ゼロ、fidelity=pass / 自然度 A/残存0）。硬い敬語定型は 1 span が長く、削除主導で構造的に 50% を超える。技術記事 run 001 は逆に 0.235 と低く出たが「印象は大きく変わった」（短縮主導は指標が過小評価）。
- 追加論点（06-27）: **change_rate の算出法自体が未定義**（difflib opcode 基準 vs edit-span 加算で大きくぶれる。run 002 で 0.504 vs 1.20）。playbook §変更率の数え方が方式を規定していない。
- 出所: rewriter-A/B, naturalness-B（06-12）, rewriter-002, fidelity-002, naturalness-002, rewriter-001（06-27）
- 提案: (a) 削除と挿入を分離計上。(b) `info_loss_rate`（実体情報の純減率）を主指標化し、削除 span が全件ボイラープレート級かつ挿入が言い換えのみなら `deletion_dominant=true`。(c) 50% 中断は「意味改変 edit 比率」基準へ置換。fidelity=pass かつ info_loss_rate≈0 なら閾値超過でも accept 昇格を許可。(d) change_rate の算出法（difflib opcode）を明記。
- **適用（2026-06-27）**: playbook §変更率の数え方を改訂（difflib opcode 基準を明記＋ `deletion_share`/`info_loss_rate` を定義）、rewriter.md の変更率監視手順に削除主導フラグを追加、SKILL.md §総合判定に「change_rate 超過 ∧ fidelity=pass ∧ 自然度A/B ∧ info_loss≈0 → override accept」を明文化。
- 影響ファイル: `rewriting-playbook.md`, `japanese-style-rewriter.md`, `SKILL.md`

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done(適用 2026-06-27 taxonomy v1.1)` `hits: 2runs`
- 症状: 正規化式が SSOT に無く、検出器ごとに分母が変わる。
  - 06-12: 高密度短文で raw が即 100 付近に張り付き（Sample A raw106→92.5）。
  - **06-27 再現（決定的）**: 2 つの検出器が**別々の式**を使った。run 001 は飽和基準 `score=raw/sat*100, sat=(len/40)*5`（→75.4）、run 002 は `score=raw/(count*5)*100`（→47.1）。同じ raw 帯でも run 間・推敲前後で score が比較不能。
- 出所: detector-A/B（06-12）, detector-001, detector-002（06-27）
- 提案: 飽和しにくく**長さ非依存**（推敲で文長が縮んでも before/after 比較が成立する）正規化を SSOT で固定。
- **適用（2026-06-27, taxonomy v1.1）**: 正準式を `severity_weighted_score = 100 * (1 - exp(-raw / 45))`（raw = S1×5 + S2×2 + S3×0.5、K=45 固定）と SSOT に明記。長さ非依存なので before/after を同一基準で比較可能（IMP-003 の sat 基準問題も同時解消）。K=45 は taxonomy 例 raw56→71.5 に較正。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出`

### IMP-003 score_before のフィールド契約が曖昧 `status: done(適用 2026-06-27)` `hits: 2runs`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。
  - 06-12: スキーマ例 71.5 vs 実 92.5。
  - **06-27 再現**: naturalness-001 が「sat=(input_length/40)*5 の分母が推敲で 695→560 と縮み before/after で別値（86.875 vs 70.0）になる」と指摘。score_before の値だけでなく**正規化基準**まで固定しないと improvement_rate が歪む。
- 出所: naturalness-A（06-12）, naturalness-001（06-27）
- 提案: 「score_before = 02_detection.json の meta.severity_weighted_score」かつ「score_after は同一正準式（IMP-002, 長さ非依存 K=45）で再計算」と明文化。
- **適用（2026-06-27）**: naturalness-reviewer.md に score_before/score_after の契約を明記。IMP-002 の長さ非依存式採用で sat 基準ズレは構造的に消滅。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2runs`
- 症状: 絵文字8個・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
  - **06-27 再現**: detector-001 が「E-2 等文書レベル finding の span 表現が未定義。`start:0/end:695/text_span:'（文書全体）'` で表現せざるを得ず推敲役が span を切り出せない」と指摘。
- 出所: detector-B, detector-A（06-12）, detector-001（06-27）
- 提案: `span_type: "contiguous"|"scattered"|"document"` と scattered 用 `occurrences: [[s,e],...]` を追加。density は重複・locator を除いた実 AI クセ文字数ベースと定義。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2runs`
- 症状: 1 span が複数カテゴリに該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。density も二重計上。
  - **06-27 再現**: detector-001 が「f004『新たなソリューションを提供します』(A-10) と f005『ソリューション』(B-2) が同一テキスト上で正当に重なる。density を単純合算すると重複区間を二重計上し過大評価」。rewriter-001 が edit スキーマに `secondary_categories` を提案。
- 出所: detector-A, rewriter-A/B, naturalness-A, fidelity-A（06-12）, detector-001, rewriter-001（06-27）
- 提案: 「1 span = 主分類 1 finding」を基本とし `merged_findings: [...]` / edit に `secondary_categories` を許容。density は重複区間を**和集合**で数える。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行する経路が .md で未必須化 `status: ready` `hits: 2runs`
- 症状: 仕様は「検出器を同基準で再走査」だが naturalness-reviewer.md にサブエージェント再呼び出しが必須として書かれておらず、手動照合に落ちうる。
  - **06-27**: 両 naturalness をオーケストレーターがプロンプトで明示指示して初めて検出器を実走査した（001/002 とも実行）。naturalness-001 が「推敲文パス・score_formula・span 規約を毎回手書きで渡しておりズレ事故源。`ai-tell-detector` に再計測モード（before の meta を継承）フラグを設けるべき」と指摘。
- 出所: naturalness-A（06-12）, naturalness-001（06-27）
- 提案: naturalness-reviewer.md §処理に「ai-tell-detector をサブエージェントとして実呼び出し（手動照合禁止）」を必須化。ai-tell-detector に再計測モード入力契約を追加。
- 影響: `naturalness-reviewer.md §処理`, `ai-tell-detector.md`, `SKILL.md`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **冒頭の予告・自己言及公式（昇格候補・実例2runで条件充足）** 「本記事では〜について解説していきます／していきたいと思います」「徹底的に解説していきます」式の記事冒頭の自己言及型予告。D-1（結び）でも C-6（見出し直後案内）でも当たらない独立パターン。実例: 06-12 run002「徹底的に解説していきたいと思います」(当時 D-2 へ寄せ), 06-27 run001「本記事では、その仕組みについて徹底的に解説していきたいと思います」(当時 D-1 へ寄せ)。`hits: 2` 出所 detector-001。→ taxonomist が v1.1 で正式採番を審査。
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」「〜してみてはいかがでしょうか」。`hits: 1`（06-12 のみ。ブログ枠の次回 day0 で再現待ち）出所 detector-B
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式の導入→本論ブリッジ。`hits: 1` 出所 detector-B

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** `status: ready` `hits: 2`（06-12 f019＋06-27 fidelity-001 が「具体的には/また 等の順序語言い換えで存在しない序列を混入させていないか専用チェックが13項に無い」と再指摘）出所 fidelity-A, fidelity-001
- **削除専用サブチェック（反実仮想テスト / deletion-recall）** 削除 span ごとに「その語を原文に戻すと新情報が増えるか？増えれば実体＝欠落」。`status: ready` `hits: 2`（06-12 fidelity-B＋06-27 fidelity-002 が公的文書の純削除245字を反実仮想で全件ボイラープレートと検証、構造化を提案）出所 fidelity-B, fidelity-002
- **modality 強度の順序尺度化** 「断定>命令>必要(must/need)>依頼(please)>提案>許可」。各 edit に modality_before/after を記録し隣接1段の軟化は pass、2段以上 or 強化方向は要審査。`status: ready` `hits: 2`（06-12 fidelity-A＋06-27 fidelity-001/002）出所 fidelity-A, fidelity-001, fidelity-002
- **A-8 行為者不定時の処方** 行為者が(1)文脈で一意確定 or (2)既出固有名のときのみ主語化を許可、それ以外は能動化せず自動詞/属性叙述化（「設定されております」→「同額です」）。「一意に復元できないなら能動化しない」を A-8 の安全弁に。`status: ready` `hits: 1`（06-27 run002 で複数 agent）出所 rewriter-002, fidelity-002
- 「情報を含む削除 vs ボイラープレート削除」二分判定（数値/固有名詞/日付・条件/因果節・固有の例示を含めば情報欠落）。出所 fidelity-B
- #5論理関係 と #11情報追加 の責任境界を一意化／register（語の格・抽象度）変化は fidelity でなく naturalness 側、という分担明文化。出所 fidelity-A, fidelity-001

### playbook レシピ追補
- **A-10「可能にする」enable 型の置換レシピ** 「X は Y を可能にする → X で Y できる／X が Y を実現する」を A-10 行に追加。カタカナ語が万能動詞の目的語のときは語単独置換でなく節再構成、という横断ルールも。`status: ready` `hits: 1`（06-27 run001 で detector-001＋rewriter-001）出所 detector-001, rewriter-001
- **I-3/I-4 反復分散ストック** 公的文書では要請が多反復。分散先（必要があります／〜ください／〜いただきます／〜ことになります／お願いいたします）を処方に常備。`status: ready` `hits: 1`（06-27 run002）出所 rewriter-002
- **公的文書の格式結語は「保存必須スロット」** 冒頭挨拶・末尾結語（「御礼申し上げます」「賜りますよう…お願い申し上げます」）は各1回まで定型反復を許容し、本文中の同型反復のみ変奏。3回以上反復時のみ D-1 計上。`status: ready` `hits: 1`（06-27 run002 で rewriter/fidelity/naturalness 3agent）出所 rewriter-002, fidelity-002, naturalness-002
- **同カテゴリ反復分散の上限明文化** A-5/B-2 等が3回以上のとき「同一形は文書内2回まで、3回目以降は別の自然形へ」を taxonomy の S2 ルール（3回+で除去）と整合させ playbook に明記。`status: ready` `hits: 1` 出所 rewriter-001
- **C-5 絵文字削除後の文末/区切り吸収ルール** / **D 系結びは最小着地文を残す** / **機能が必要な接続詞は削除でなく変奏** / **原文が元から推量の D 系は推量を保持**。出所 rewriter-B, rewriter-A（06-12）

### naturalness 判定の精緻化
- **過推敲シグナルの定量化** 「常体文末の混入数>0」「平均文長<N字かつ体言止め比率>X%」等の機械判定トリガを定義しシグナルごとに count を持たせる。`status: ready` `hits: 2`（06-12 naturalness-A＋06-27 naturalness-001）出所 naturalness-A, naturalness-001
- **絶対残存数ガードを grade 表に組込み** 改善率が高くても S1 が1件でも C 以下。短文では改善率がアーティファクト化するため `absolute_residual_guard` を出力に明示。`status: ready` `hits: 2`（06-12＋06-27 naturalness-001/002）出所 naturalness-A/B, naturalness-001, naturalness-002
- **公的文書プロファイル** naturalness-reviewer に評価軸（敬体維持は減点しない・格式結語の1回出現は正当・過度な平易化による格喪失を逆方向の過推敲シグナルとして計上）を常設。`status: ready` `hits: 1`（06-27 run002）出所 naturalness-002
- **E-2 文末単調の到達ライン数値化** 敬体維持下で『〜ます。』比率 ≤ X%（例70%）で E-2 解消とみなす。体言止め乱発（過推敲）を誘発しない下限も。出所 naturalness-B, naturalness-001
- クラスタ系 finding（B-2 密集・C-1 列挙）はクラスタ崩壊時に個別 severity を降格するルール。出所 naturalness-A

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 2`（06-12＋06-27 run001 でセキュリティ/ネットワーク/クラウド/アクセス等の技術定着語を維持）
- ルーティン・モチベーション・データドリブン・セキュリティ・ネットワーク・クラウド・アクセス・デバイス・リソース・テクノロジー 等の定訳が冗長/別義になる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B, fidelity-A, naturalness-A, rewriter-001, fidelity-001

### detector 実装
- **start/end の単位を SSOT に明記**（Python len＝コードポイント基準。UTF-16/バイトと混同しない。JS フロントとの整合）。`status: ready` `hits: 1` 出所 detector-001
- **category_summary 総和 == detected_count == findings 数の自己検証を必須化**（06-27 は両検出器とも category_summary を誤記し検証スクリプトで修正。出力前の機械チェックを SKILL.md に組込む）。`status: ready` `hits: 1` 出所 detector-001, detector-002
- start/end 自己検証（regex マッチ位置と text_span 一致を assert、不一致なら JSON 出さない）。出所 detector-A
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B
