# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数（**別 run での再現のみ +1**）。

最終更新: 2026-07-19（run 2026-07-19-001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2runs`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。06-12 Sample B は 54.6%、07-19 run001 は初版 38.5%（finding 外の裁量波及はわずか 2.99%）。過推敲でないのに warning/hold が誤発火。
- 出所: rewriter-A(0612), rewriter-B(0612), naturalness-B(0612) ／ **再現: rewriter-001(0719), naturalness-001(0719), rewriter-002(0719)**
- 提案（07-19 で具体化）: **過推敲の主指標を change_rate から「finding 外変更率」へ置換**する。finding 外変更率 = 検出 span に紐づかない改変文字数 / 原文字数。さらに分子から「文法上強制の波及（される→する等の態変換に伴う不可避調整）」と「detector の suggested_fix 準拠削除」を除外し、**裁量的波及のみ**を数える。閾値は裁量的 finding 外率 3% 目安、全体 change_rate は warning の参考値に降格。等級 C の過推敲発火も change_rate 単独でなく finding 外率で定義。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`, `naturalness-reviewer.md`
- **適用方針**: 次サイクルで適用（IMP-002 のスコア正規化と同日に触ると change_rate×score の二重変更で回帰切り分けが困難なため、07-19 は IMP-002/004/006 を先行適用し本項は保留）。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done`（適用 2026-07-19-001/002）`hits: 2runs`
- 症状: 「0〜100 に正規化」とだけあり分母・式が SSOT に無い。min(100, 加重和) では長さの項がなく、短い高密度文書と長い低密度文書が比較不能。加重和は文書が長いほど際限なく増える。件数ベースのため推敲後に反復が単発化するとゼロへ急落し楽観的に振れる。
- 出所: detector-A(0612), detector-B(0612) ／ **再現: detector-001(0719), detector-002(0719), naturalness-001(0719)**。両 run の検出器が独立に同じ密度飽和式を提案。
- **適用（v1.1）**: `severity_weighted_score = round(100 * (1 - exp(-k * W / L)), 1)`。W = S1×5 + S2×2 + S3×0.5、L = input_length（本文文字数, 改行・空白を除く）、k = 23（W/L=0.10 の高密度 AI 文が ≈90 になるよう較正）。分母 L は改行・空白を除いた実文字数で固定。→ `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出` に明記。
- 影響: `ai-tell-taxonomy.md`, `ai-tell-detector.md`

### IMP-003 score_before のフィールド契約が曖昧 `status: done`（適用 2026-07-19、IMP-006 と同時）`hits: 2runs`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。分母（推敲前後で文字数が変わる）も未規定で improvement_rate がぶれる。
- 出所: naturalness-A(0612) ／ **再現: naturalness-001(0719), naturalness-002(0719)**（分母固定の未明文化を両者が指摘）
- **適用**: `naturalness-reviewer.md` に「score_before = 02_detection.json の meta.severity_weighted_score」「改善率算出時の分母 L は原文 input_length に固定（推敲後も同一 L を使い before/after を可比化）」を明記。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: done`（適用 2026-07-19-001/002）`hits: 2runs`
- 症状: 絵文字分散・文末単調・受動氾濫・文頭接続密度など E/C/H 系は文書全体の性質で単一 start/end に馴染まない。代表アンカー span で埋めると誤解を招き density も歪む。
- 出所: detector-B(0612), detector-A(0612) ／ **再現: detector-001(0719), detector-002(0719)**。両 run が独立に `scope: "span"|"document"` を提案。
- **適用（v1.1）**: finding に任意フィールド `scope: "span" | "scattered" | "document"`（既定 span）を追加。document/scattered では `text_span`/`start`/`end` を任意化し、`occurrences: [[s,e],...]`（scattered 用）と `metric`（例: 文末反復率・受動比率・文頭接続率）を持てる。density は重複を除いた union 文字数ベースで数えると契約に明記。→ `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`
- 影響: `ai-tell-taxonomy.md`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 1run`
- 症状: 1 span が複数カテゴリ該当。edits/findings 1:1 前提で category_summary が過小評価。
- 出所: detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A（0612 横断）
- 提案: 「1 span = 主分類 1 finding」＋ `merged_findings: [...]` 許容。category_summary は先頭文字集計と注記。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: done`（適用・実証 2026-07-19-001/002）`hits: 2runs`
- 症状: 仕様は「検出器を再走査」だが 0612 は手動照合で推定値だった。
- 出所: naturalness-A(0612) ／ **実証: naturalness-001(0719), naturalness-002(0719) がともに Agent ツールで `ai-tell-detector` を 03_rewrite.md に再実行し、自己再スキャンと reconcile して score_after を確定**。経路が機能することを実証。
- **適用**: `naturalness-reviewer.md §処理` に「検出器の再実行は Agent ツールで `ai-tell-detector` サブエージェントを呼ぶ（手動照合は不可、困難時のみ自己再スキャンで代替し notes 明記）」を必須化。再スキャン結果の受け渡し契約（`sub_threshold_observations` 欄・分母固定）も追記。
- 影響: `naturalness-reviewer.md`, `SKILL.md`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **K 系: 過剰敬語・二重敬語（★日本語固有・公的文書シグネチャ）** 「格別のご理解とご協力を賜り、厚く御礼申し上げます」「皆様におかれましては」「お問い合わせいただきますようお願い申し上げます」。公的文書では定型として正当だが高密度・同一結び定型の連続で AI-tell 化。taxonomy に該当コードが無く severity 判断メモに逃がしている。genre 条件付き許容表＋しきい値（同一結び定型の連続は2文まで 等）を持つ新カテゴリ K を提案。実例2件確認。 `hits: 1run(0719-002)` 出所 detector-002, rewriter-002, fidelity-002
- **A-8 の by 二種分離＋「することによって」手段構文** 行為者の「によって」（業者によって＝除去対象）と手段/原因の「によって・することによって」（導入によって・処理することによって＝許容）を区別。detector が手段 by-Ving を A-8 受動へ誤寄せ、playbook にも区別注記が無い。 `hits: 2runs`（detector-001 が手段 by-Ving を、rewriter-002 が によって二種を独立に指摘）→ **昇格条件充足。次サイクルで playbook A-8 に「手段の によって は触らない」注記＋検出側の分離を適用候補**。 出所 detector-001, rewriter-002
- **A-14 候補: 「〜ようになります／〜できるようになる」変化・到達叙述** 英語 come to / will be able to 直訳。A-6 状態化とは別に「変化・到達を無駄に演出」。実例2件（「削減することができるようになります」「高めていく」系）。 `hits: 1run(0719-001)` 出所 detector-001
- **ジャンル別 severity 減免（genre-modifier）** 「S1 は無条件除去」と CLAUDE.md「公的文書は定型を一定許容」が衝突。公的文書では A-6/A-8/I-3 を −1 段階、技術記事では B-2 許容語彙を拡張、等をジャンル補正表として明文化しないと検出器間でブレる。 `hits: 2runs`（0719-001 技術記事の B-2 境界／0719-002 公的文書の A-6・A-8 減免を独立に要請）出所 detector-001, detector-002, naturalness-002
- **C-1 派生: 孤立順序語** 対応語を欠く単独「まず」等はどの finding にも該当せず放置。C-1 の派生として独立パターン化の余地。 `hits: 1run(0719-002)` 出所 rewriter-002
- **C 系: redundant restatement**（0612 起票）叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。 `hits: 1` 出所 detector-A(0612)
- **D-7 ブログ結び呼びかけ公式**（0612 起票）「今回は〜ご紹介しました」「素敵な〜ライフを応援しています」。 `hits: 1` 出所 detector-B(0612)
- **C-9 導入誘導定型**（0612 起票）「さっそく見ていきましょう」式。 `hits: 1` 出所 detector-B(0612)

### fidelity チェックリスト補強（modality/強度ラダー系が今回強く再現）
- **modality/約束強度ラダーの新設** `status: ready` `hits: 2runs` — 現行 check7 が「断定化したか否か」の二値になりがち。「期待されております→期待できます」は断定化しないが同一様相内で強度が上がる。`報告様相 > 予定/期待様相 > 可能様相 > 断定様相` の順序尺度を定義し、1段上昇で S3 フラグ、断定域到達で rollback。公的文書では「予定・努力義務・条件付きが確約へ昇格していないか」を見る **check#14 コミットメント強度** を genre 限定で追加。0612 の「modality 強度を順序尺度化」を具体化。 出所 fidelity-001(0719 modality family 方向), fidelity-002(0719 ladder/commitment), rewriter-002(0719 load-bearing hedge) ／ 0612 fidelity-A
- **#15 修飾強度の保存** `status: ready` `hits: 1run` — F-1 程度副詞除去・D-4 ハイプ抑制（爆発的→急速、極めて/ますます削除）は「主張」でないため現行13項を素通りするが原文の熱量・断定強度は下がる。1文書あたり強度減衰 N 件までの閾値を設ける。 出所 fidelity-001(0719)
- **順序保存を独立チェック化** `status: ready` `hits: 1run` — 段落順・例示順の保存が13項の独立項目になく check5/#11 に漏れ込む。 出所 fidelity-001(0719)
- **span 外改変の独立検算** `status: ready` `hits: 1run` — diff の finding 外変更率は推敲役の自己申告。auditor が非 flagged span の改変を独立検算する項目が無い。IMP-001 の finding 外率運用と対で必要。 出所 fidelity-001(0719)
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか**（0612）`status: ready` `hits: 1` 出所 fidelity-A(0612)
- **削除専用サブチェック（deletion-recall test）**（0612）`status: ready` `hits: 1` 出所 fidelity-B(0612)
- 「なお」等の付帯注記削除が注記の重要度シグナルを下げていないか（公的文書 check5 の穴）。出所 fidelity-002(0719)
- 完了相（〜ました／済み）が担う確定度情報の欠落を check8 に補記。出所 fidelity-002(0719)

### playbook レシピ補強
- **E-2 変奏メニューのジャンル分離** — playbook の E-2 例示（体言止め・でしょう）は公的文書の敬体レジスターに不適。公的文書向けメニュー（ください／いたします／能動ます／可能ます 等、格を保つ選択肢）を分離。 `hits: 1run` 出所 rewriter-002(0719)
- **load-bearing ヘッジの保持例外** — G/A-6 の一律「断定へ」処方に、意味を担うヘッジ（期待・見込み・傾向）は保持する例外則。0612 の「原文が元から推量の D 系は推量を保持」を一般化。 `hits: 2runs` 出所 rewriter-A(0612), rewriter-002(0719)
- C-5 絵文字削除後の文末/区切り吸収ルール（0612）出所 rewriter-B
- D 系結びは「最小着地文を残す」（減らしすぎ下限）（0612）出所 rewriter-B, naturalness-B
- 機能が必要な接続詞（しかしながら）は削除でなく変奏（0612）出所 rewriter-A

### naturalness 判定の精緻化
- **等級のジャンル補正＋絶対残存数を主指標に** `status: ready` `hits: 2runs` — 等級A（改善70%+）は絶対値基準だが公的文書は score_before が低め（0719-002 は 46.0）に出て改善率が振れる。絶対残存数（S1/S2 件数）を主、改善率を従とする明示ルール。0612 の「絶対残存数ガード」を具体化。 出所 naturalness-A/B(0612), naturalness-002(0719)
- **レジスター逸脱（過推敲）の定量化** — 「砕けすぎ/事務的すぎ」を敬体/常体二値でなく文末の敬語レベル分布で捕捉。過推敲シグナルの定量化（0612）と同系。 出所 naturalness-002(0719), naturalness-A(0612)
- **sub_threshold_observations 欄の正式化** — 閾値未満で非 finding とした残存（I-4「求められる」単発・A-13「という」単発）を residual と別欄で可視化し次段推敲へ引き継ぐ。 `hits: 1run` 出所 naturalness-001(0719)
- クラスタ系 finding のクラスタ崩壊時 severity 降格（0612）出所 naturalness-A
- E-2 到達ライン緩和（体言止め1箇所以上で合格）（0612）出所 naturalness-B
- **文書レベルパターンの部分改善が score に乗らない** — E-1 文長分布が許容域まで回復しても finding 化されず改善が無視される死角。段階評価指標が要る。 `hits: 1run` 出所 naturalness-001(0719)

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 2runs`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長な語は B-2 半免責で残差 S3 固定。技術記事ではアーキテクチャ/トラフィック/ローカル/リスク 等の許容語彙を拡張（ジャンル別許容リスト）。0612 の免責リストに 0719-001 のジャンル別拡張要請が重なった。 出所 naturalness-B/fidelity-A/naturalness-A(0612), detector-001/rewriter-001(0719)

### detector/スキーマ実装
- **input_length と ai_tell_density の分母定義の明文化** `status: ready` `hits: 2runs` — 改行込み/除きが未規定（0719-001 は 769 vs 778）。density の分母もこれに依存。再スキャン時（本文のみ）と初回（全体）で分母が変わり density が非可比。「input_length＝改行・空白を除く本文文字数、density は重複除去 union」を契約固定。 出所 detector-A(0612), detector-001(0719), naturalness-001(0719)
- 密度依存 finding の severity 昇格閾値表（同カテゴリ N 回以上で S3→S2）を SSOT に。 `hits: 1run` 出所 detector-001(0719)
- start/end 自己検証（regex 位置と text_span 一致を assert）（0612）出所 detector-A
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`（0612）出所 detector-B
