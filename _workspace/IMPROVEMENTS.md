# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-09-25（run 001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done` `hits: 2runs` `applied: 2026-09-25-001/002`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除、およびカタカナ語→漢語の縮約置換で機械的に膨張。SequenceMatcher の replace を delete+insert で二重計上するのが主因。
- 再現: 06-12（Sample B 54.6%, A 47.6%）＋ 09-25（run 001 44.4%：delete224/insert64＝カタカナ縮約主体で fidelity 毀損は e004 の 1 件のみ、run 002 29.4%：I-3 冗語圧縮が主因）。**カタカナ濃度が高い良質原文ほど過推敲と誤判定される**ことを 09-25 で実証。
- 出所: rewriter-A/B, naturalness-A/B（06-12）＋ rewriter-001/002, naturalness-001/002, fidelity-001（09-25）
- 適用（2026-09-25）: `rewriting-playbook.md §変更率の数え方` に「語句改変率（lexical_substitution・同義縮約）」と「構造改変率（structural_rewrite・語順/文分割）」の分離計上を規定。delete≫insert の縮約主導は健全と明記。`SKILL.md §総合判定` に **override accept 基準**（fidelity=pass かつ自然度 A/B なら change_rate 超過でも accept、判断材料に semantic_edit_ratio）を追記。
- 残: Levenshtein 切替（replace 二重計上の完全排除）は将来課題として残置。reviewer 側に breakdown 受取契約フィールドを持たせる案も残置。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2runs` `applied: 2026-09-25 (taxonomy v1.1)`
- 症状: 正規化式が SSOT に無く実装依存。09-25 で **2 検出器が別式を採用**（detector-001 は logistic `raw/(raw+K)*100`, detector-002 は raw 加重和の clamp）し、同一 raw でも値が食い違うことを実証。高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える問題も継続。
- 再現: 06-12（raw106→92.5 と taxonomy 例 raw56→71.5 の不整合）＋ 09-25（検出器間で式が割れた）
- 出所: detector-A/B（06-12）＋ detector-001/002, naturalness-001/002（09-25）
- 適用（2026-09-25）: taxonomy §検出出力スキーマに正規化式を明文化 → `severity_weighted_score = 100 × raw / (raw + K)`, K=52, raw = ΣS1×5 + S2×2 + S3×0.5。飽和しにくく文書長非依存、taxonomy 例（raw≈130→71.5）を再現。taxonomist が v1.1 へ昇格。

### IMP-003 score_before のフィールド契約が曖昧 `status: done` `hits: 2runs` `applied: 2026-09-25`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。09-25 で両レビュアーとも「severity_weighted_score を採用したいが算出式が非公開のため improvement_rate は参考値にとどまる」と報告。commensurability を保証できない。
- 再現: 06-12（naturalness-A）＋ 09-25（naturalness-001, 002）
- 出所: naturalness-A（06-12）＋ naturalness-001/002（09-25）
- 適用（2026-09-25）: `naturalness-reviewer.md` と taxonomy に「score_before = 02_detection.json の meta.severity_weighted_score」「score_after は同一正規化式（IMP-002）で再計算」を明文化。detector が meta.scoring_formula を出力する規約を `ai-tell-detector.md` に追記。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2runs`
- 症状: 絵文字分散・文末単調（E-2）・文長均一（E-1）・「まず…最後に」は分散/文書レベルパターン。単一 start/end では代表位置を恣意的に置くしかなく、ai_tell_density も E-2 の数文字しか算入されず過小/過大評価。
- 再現: 06-12（detector-A/B）＋ 09-25（detector-001 が E-1/E-2 を代表位置で暫定表現、detector-002 も E-2 で同問題を報告）
- 出所: detector-A/B（06-12）＋ detector-001/002（09-25）
- 提案: `span_type/scope: "contiguous"|"scattered"|"document"` と scattered 用 `occurrences: [[s,e],...]`、document 用 `metrics`（文末分布・文長SD 等）を追加。density は重複を union 除去した実 AI クセ文字数ベースと定義（09-25 detector-001 が union 算出を実施）。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2runs`
- 症状: 1 span が複数カテゴリに該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。同一トークンの複数出現（A-1×5 等）を個別 finding にするか 1 件＋反復注記にするかで detected_count が大きく変わる。
- 再現: 06-12（5 agent 横断）＋ 09-25（detector-002 が「S1 は個別、S2/S3 反復は 1 件集約」等のルール化を要望）
- 出所: detector-A, rewriter-A/B, naturalness-A, fidelity-A（06-12）＋ detector-002（09-25）
- 提案: 「1 span = 主分類 1 finding」を基本とし `merged_findings: [...]` を許容。反復系は「S1 は個別、S2/S3 は集約＋occurrences」。density は union 算出。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 2runs`
- 症状: 仕様は「検出器を同基準で再走査」だが、09-25 では両レビュアーとも **Agent/Task 経由の detector 起動経路が使えず**、正規表現で自力再検出して代替。基準ドリフト（「することが可能です」を S2/S3 どちらにするか等）を人手で吸収。
- 再現: 06-12（naturalness-A）＋ 09-25（naturalness-001, 002）
- 出所: naturalness-A（06-12）＋ naturalness-001/002（09-25）
- 提案: (a) reviewer から ai-tell-detector を同一基準で回す標準配線、または (b) オーケストレーターが detector を推敲後入力で再走査し `02b_detection_after.json` を reviewer へ渡す。手動照合禁止。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

### IMP-007 fidelity 13項が「意味が静かに動く」変換を捕捉しきれない `status: ready` `hits: 1run(2agent)`
- 症状: 敬語・受動・カタカナ→漢語・A-10 視点主語化で意味が微移動する箇所を、二値チェックでは拾えない。09-25 で以下を実証:
  - **発話行為シフト**: 「確認する必要があります（義務陳述）」→「確認してください（直接依頼）」。#7 modality 強度軸では拾えない。法令/契約では法的効果が別物。
  - **modality の mood 横滑り**: 「期待されております（願望）」→「考えております（判断）」。断定/推量/義務のどれでもない。
  - **技術用語の精度低下（同義域内の含意減衰）**: リトリーブ→取得（探索含意減衰）、トレードオフ→兼ね合い（相互排他→単なるバランス軟化）、インジェクト→埋め込む（エンベディングと語衝突）。check12 が二値のため全 pass にせざるを得ない。
  - **主張の主体/範囲移動**: A-10「このアプローチは提供します」→「この手法ではできます」で受益者/主体の枠づけが移動。check9（受動→能動の行為者）ではカバー外。
- 出所: fidelity-001, fidelity-002（09-25）
- 提案: #7 に「発話行為タイプ」「願望↔判断 mood」の副軸、#12 に「12b 技術用語精度低下＋用語衝突」＋severity ラベル、#9 に「主張の主体/範囲移動（視点主語化・無主語化）」を拡張し I-4 系と統合。監査官が `semantic_edit_ratio`（意味に触れた edit 数/全 edit 数）を出力。
- 影響: `content-fidelity-auditor.md`, fidelity チェックリスト

### IMP-008 反復系 S1 の「無条件除去」と「密度で S1 昇格」が taxonomy 内で矛盾 `status: ready` `hits: 1run`
- 症状: A-6/A-1 等は字義上「一度でも S1（無条件除去）」だが、実際に S1 とされる根拠は「文書内 N 回反復」という密度。反復が解消されて残った単発定型（09-25 run 002「必要となります」1 箇所）を、字義通り S1 とすると grade C→2次推敲、密度基準だと S2→grade A となり、**レビュアー間で grade が A↔C に割れる**。
- 出所: naturalness-002（09-25。同 run のオーケストレーターは micro-fix で回避）
- 提案: A-6/A-1 等の反復系パターンに「N 回以上で S1、単発は S2」の密度閾値を明文化。単発残存は micro-fix（変更率余地内の 1 トークン修正）で解消し 2 次推敲を回さない運用を SKILL.md に追記。
- 影響: `ai-tell-taxonomy.md`（A-1/A-6 等）, `SKILL.md`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **A-8b 手段の「〜することによって / 〜することで」（by-doing・能動）** 現行 A-8 は受動 by-passive 専用、A-3 は 通じて/通して 専用で、能動・手段の「によって/ことで」に受け皿が無い。実例（09-25 run 001）:「マッピングすることによって距離を計算する」「インジェクトすることによって生成する」。**再現 2 回（同 run 内 2 例）＋ rewriter/detector 双方が同一提案**。→ A-8 を「A-8a 受動 by / A-8b 手段 by-doing」に分割提案。playbook にも「によって→ことで/連用形」行を独立させる。`hits: 1` 出所 detector-001, rewriter-001
- **D 導入定型（オープナー）** 「近年、〜が広がる中で」「〜が大きな注目を集めています」。D は結び（D-1/D-6）が厚いが書き出し側が未収載。「注目を集める」も D-2 ハイプ語に無い。実例（09-25 run 001）。`hits: 1` 出所 detector-001
- **冗長敬語・二重敬語（新カテゴリ K もしくは I-6）** 「〜方におかれましても」「賜りますようお願い申し上げます」「ご確認いただく必要がございます（いただく＋必要＋ございます 三重敬語）」。A〜J に受け皿が無い。**儀礼定型（許容）と機能語の敬語二重化（検出）を区別する判定基準**が必要。実例 2 件以上（09-25 run 002）。`hits: 1` 出所 detector-002, rewriter-002
- **A-6 変種「〜運びとなりました」** 公的告知の常套かつ A-6 でもある両義的表現。儀礼定型として温存すべきか能動化すべきか基準欠落。実例（09-25 run 002）。`hits: 1` 出所 detector-002, rewriter-002
- **「〜につきましても/におかれましても」硬い係り受け（譲歩）** 公的文書 AI の頻出。実例 2 件（09-25 run 002）。`hits: 1` 出所 detector-002
- **ご＋動詞連用＋いただく の反復** 敬語依頼の機械的反復（本文 5 回）。I-3/A-5 と絡む。実例（09-25 run 002）。`hits: 1` 出所 detector-002
- （既存）**C 系 redundant restatement** 叙述と箇条書きの二重記載。実例 001（06-12）。`hits: 1` 出所 detector-A
- （既存）**D-7 ブログ結び呼びかけ公式**「今回は〜ご紹介しました」等。実例 2 件（06-12）。`hits: 1` 出所 detector-B
- （既存）**C-9 導入誘導定型**「さっそく見ていきましょう」式。実例 002（06-12）。`hits: 1` 出所 detector-B

### 検出器 A-6 パターン補強 `status: ready` `hits: 1run`
- 「必要となる/必要となります」を A-6（状態叙述）に追加。09-25 run 002 で「カードリーダーが必要となりますので」が となる系 4 回目なのに検出漏れ → orchestrator が micro-fix で救済。出所 rewriter-002, naturalness-002

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019 型。序列マーカーを含む文書に限り発動する条件付き項として追加が費用対効果高（09-25 fidelity-002 も同旨）。`status: ready` `hits: 2`（06-12 fidelity-A + 09-25 fidelity-002）
- **削除専用サブチェック（deletion-recall test）** diff の全 delete/insert スパンを列挙し 1 件ずつ「読者が知り得なくなる事実は何か」を問う手続きを #10/#11 に必須化。`status: ready` `hits: 2`（06-12 fidelity-B + 09-25 fidelity-002）
- 「情報を含む削除 vs ボイラープレート削除」二分判定（06-12 fidelity-B）。
- #5論理関係 と #11情報追加 の責任境界一意化、modality 強度の順序尺度化（→ IMP-007 に統合）。

### playbook レシピ追補
- **カタカナ語変換表の拡充**（09-25 rewriter-001）: マッピング→対応づけ/写像、スケーラビリティ→拡張性、レイテンシ→遅延、トレードオフ→兼ね合い/二律背反、レスポンス→応答/回答、パフォーマンス→性能、アーキテクチャ→構成/仕組み、アプローチ→手法、ナレッジベース→知識ベース、コンテキスト→文脈、インフラストラクチャ→基盤。**動詞化カタカナ欄（リトリーブする/インジェクトする/マッピングする）**を別建て。技術固有語の保持/開く判定基準（定訳定着か/英略語か）明文化。`status: ready` `hits: 1`
- **ジャンル別ホワイトリスト**（儀礼定型: お願い申し上げます/賜りますよう/努めてまいります、技術固有カタカナ: プロンプト/クエリ/エンベディング）を playbook に新設。同表現でもジャンルで検出可否を切替。`status: ready` `hits: 1`（rewriter-002, naturalness-001）
- **A-8 単純受動の残し方**（行為者自明の単純受動は残す/二重受動・by-passive のみ能動化）を playbook 本体に明記（現在ジャンル申し送りのみ）。出所 rewriter-002
- **A-10 レシピ拡充**: 擬人化された技術/概念主語（発揮する/担う/実現する）の行を追加し D-5 との使い分けを注記。視点主語化（この手法では〜できます）を解として追加。出所 rewriter-001
- **A-5 分散指針の定量化**: 「同一語尾は連続 2 回まで、3 回目から別形」。出所 rewriter-001
- **E-1 と過推敲禁止の衝突**: 「E-1 は変更率に余裕がある時のみ完全対応、逼迫時は体言止め・既存文の短文化で代替」の優先順位ルール。出所 rewriter-001, naturalness-001
- **E-2 敬体変奏候補の拡充**: 「〜います/〜いたします/〜ております/〜ください」等を追加（公的文書では「でしょう」不可）。ただし I-3 一律「ください」化で「ください」反復の新単調が生じないよう注意。出所 rewriter-002, naturalness-002
- （既存）C-5 絵文字削除後の文末吸収ルール、D 系結びの最小着地文、機能接続詞（しかしながら）の変奏例外、推量保持の例外則。

### naturalness 判定の精緻化
- **公的文書の「格式維持」評価軸**: grade は S1/S2 件数＋改善率のみで「敬体維持 ≠ 格式維持」を区別できない。儀礼緩衝の保持率・依頼形の直接度を over-polish サブ指標に。出所 naturalness-002 `status: ready` `hits: 1`
- **E-2 到達ラインの定義＋「単調の付け替え」検出**: 同一文末の許容反復回数を定義し、「1 つの単調を消して別の単調（ください4回）を作る」を検出。出所 naturalness-002, naturalness-001
- 絶対残存数ガード（改善率が高くても S1 が 1 件でも C 以下）、クラスタ系 finding のクラスタ崩壊時 severity 降格、体言止め 1 箇所以上で E-2 合格。（06-12 由来、継続）

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 2runs`
- ルーティン・モチベーション・データドリブン（06-12）＋ プロセス・プロンプト・クエリ・エンベディング（09-25 技術ジャンル）等、定訳が冗長/衝突する語は B-2 から半免責し残差 S3 固定。ジャンル別保持カタカナ白名单と統合。出所 naturalness-B, fidelity-A, naturalness-A（06-12）＋ naturalness-001（09-25）

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert）。09-25 は両検出器とも実施済み（mismatch 0）。出所 detector-A（06-12）, detector-001/002（09-25）
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B（06-12）
- ai_tell_density は重複区間を union 除去して算出（1.0 超回避）。出所 detector-001（09-25）`status: ready` `hits: 1`
