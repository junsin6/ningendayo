# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-07-25（run 001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。day0 Sample B 54.6%、本日 001 は 42.1%（純削除 20.4%+語句改変 21.8%）・002 は 32%（純削除 25%+語句改変 7%）と、良質な削除主導の推敲ほど数値が悪化する構造欠陥を再実証。
- 出所: (day0) rewriter-A/B, naturalness-B / (2026-07-25) rewriter-001, rewriter-002, naturalness-001 — 別 run で再現し hits 2。
- **適用（2026-07-25）**: `rewriting-playbook §変更率の数え方` を v1.1 化。`change_rate`（総・参考値）／`lexical_change_rate`（語句改変）／`structural_deletion_rate`（純削除）に分離。過推敲判定は**実質改変率＝語句改変率＋正味挿入**に対して行い、純削除は除外。純削除主導で総率のみ高いケースは override accept。`japanese-style-rewriter.md`（diff に `type: lexical|structural`・3 率を出力）と `SKILL.md §総合判定`（override accept 明文化）へ反映。両 run はこの規則で override accept とした。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2run`
- 症状: 正規化式が SSOT に無く、検出器ごとに式が割れる。本日 detector-001 は `raw×0.6`、detector-002 は「100 クリップ」を独自採用し、同じ枠組みでも算出方式が不一致だった（改善率判定が破綻するリスク）。
- 出所: (day0) detector-A/B / (2026-07-25) detector-001, detector-002 — hits 2。
- **適用（2026-07-25, taxonomy v1.1）**: `ai-tell-taxonomy.md §検出出力スキーマ` に唯一の式 `severity_weighted_score = round(100·(1 − exp(−raw/95)), 1)`（raw = 5·S1+2·S2+0.5·S3）を確定。k=95 は参照例 raw≈119→71.5 にアンカー。非飽和・単調・文長非依存。線形式・100 クリップを禁止。`ai-tell-detector.md §スコア算出` にも反映。

### IMP-003 score_before のフィールド契約が曖昧 `status: done` `hits: 2run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。
- 出所: (day0) naturalness-A / (2026-07-25) detector-001 も改善率破綻リスクとして再指摘 — hits 2。
- **適用（2026-07-25, taxonomy v1.1）**: 「`score_before = 02_detection.json の meta.severity_weighted_score` を独自再計算せず使用」を taxonomy と `naturalness-reviewer.md` に明文化。`score_after` は同一式を推敲後テキストへ適用。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run`
- 症状: 絵文字・文末単調・受動反復・E-2/H-1 は分散パターン。単一 start/end では広域 locator になり ai_tell_density が過大化。本日も detector-001（E-2/E-1/C 系の代表 span 錨付けで density 膨張）・detector-002（E-2・H-1 の代表 span 便宜錨付け）が再指摘。
- 出所: (day0) detector-B, detector-A / (2026-07-25) detector-001, detector-002 — hits 2。
- 提案: `span_type: "contiguous"|"scattered"|"document"` と scattered 用 `occurrences: [[s,e],...]`、`scope: "sentence"|"document"` を追加。density は文書レベル finding を除外。**次回適用候補（本日は採点契約 3 件を優先）**。

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: partially_done` `hits: 2run`
- 症状: 1 span が複数カテゴリに該当（本日 002「実施されることとなりました」= A-6＋A-8 の入れ子、001「可能となっています」= A-5＋A-6、「と言えるでしょう」= D-1＋G-1）。1:1 前提で category_summary が過小評価。
- 出所: (day0) detector-A, rewriter-A/B, naturalness-A, fidelity-A / (2026-07-25) detector-001, detector-002, rewriter-001, fidelity-001 — hits 2。
- **一部適用（2026-07-25）**: taxonomy に「density は重複 span を union で計上」を明記（二重計上の過大化を解消）。**残**: `merged_findings`/`secondary_category` 配列の導入と category_summary の集計規約は未適用（次回候補）。

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: done` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーが手動照合 → 数値が推定。
- 出所: (day0) naturalness-A / (2026-07-25) 本日は両レビュアーが自己再検出を実行し I-4→D-4 の「クセをクセで置換」等を捕捉（実効性を再確認）。
- **適用（2026-07-25）**: `naturalness-reviewer.md §処理` に「手動照合で数値を推定しない・score_after は再走査結果に確定式を適用」を明記。

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち — 本日 run で新規/再現）

- **A-8 無主語受動ギャップ（最重要・公的文書固有）** `status: candidate` `hits: 1run(3agent)`
  現行 A-8 は「〜によって」by-passive 限定。行政お知らせ主流の**行為者ゼロ受動**（実施される・停止される・変更される・周知が行われる・掲載が行われる）を定義文どおりには拾えない。A-8 を by-passive と無主語受動（A-8b）へ分割する提案。実例5件。出所 detector-002, rewriter-002, fidelity-002。**再現 2 run で v1.1 昇格候補筆頭。**
- **過剰謙譲・定型結語（公的文書固有）** `status: candidate` `hits: 1run(3agent)`
  「〜所存でございます」「賜りますようお願い申し上げます」「〜してまいります」の機械的反復。D-6 は「すべき時だ」系で謙譲結語をカバーせず。D 系新設 or 公的文書サブセクション。実例2件。出所 detector-002, rewriter-002, naturalness-002。
- **二重敬語迂遠「〜していただく必要がございます」** `status: candidate` `hits: 1run(2agent)`
  I-3 の敬語重ねで依頼を極端に迂遠化。I-3 に敬語形バリアントとして例示。実例2件。出所 detector-002, rewriter-002。
- **A-1/A-2 敬語派生形の表記ゆれ辞書** `status: candidate` `hits: 1run`
  におかれましては/におきまして/につきまして が原型正規表現で漏れる。A・I 群に敬語派生形辞書を添付。実例4件。出所 detector-002。
- **X-1「〜つつある / 加速している」進行相の濫用** `status: candidate` `hits: 1run(同run2例)`
  英語 is increasingly / is becoming 直訳の「進行中感の水増し」。実例「提供されつつある」「加速している」「ポテンシャルを秘めた」。出所 detector-001。
- **X-2「〜を秘めた / 潜在性の誇張修飾」** `status: candidate` `hits: 1run` D-4 近縁。出所 detector-001。
- **X-3「〜というのが現状です / 実情だ」締め定型** `status: candidate` `hits: 1run` A-13＋I-1 合成の段落末着地。出所 detector-001。
- （前日候補で継続監視）C 系 redundant restatement / D-7 ブログ結び公式 / C-9 導入誘導定型。

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** `status: ready` `hits: 1run` 出所 fidelity-A(day0)。本日 fidelity-001 も #4「接続詞削除は代替 edit 保持頼みで機械照合不能」を指摘（論理機能を担う削除 edit に代替 edit_id をリンクさせる提案）。
- **modality 強度の順序尺度化（義務＞要請＞推奨＞任意の4段）** `status: ready` `hits: 2run`
  本日 fidelity-001（伝聞→断定の epistemic 上昇）・fidelity-002（必要がございます→してください、ものと考えております→断定 の 1 段移動を pass/fail どちらに落とすか曖昧）が同時指摘。「±1 段は case-by-case、±2 段以上は原則 rollback」の閾値化。**次回適用候補**。出所 (day0) fidelity-A / (2026-07-25) fidelity-001, fidelity-002 — hits 2。
- **敬語丁寧度の下限ガード（公的文書）** `status: candidate` `hits: 1run(2agent)`
  敬体内部の丁寧度低下（におかれましては→には、必要がございます→してください）を測る尺度が不在。下限を「〜ください／〜です・ます」に置き、下限以上なら過推敲シグナルを立てない。出所 fidelity-002, naturalness-002。
- **予定/見込み表現の断定化追跡** `status: candidate` `hits: 1run`
  公的文書で未確定事項（予定・可能性）を断定化すると「確約」と受け取られる。確定事実／予定／可能性ラベルの保存を追う専用項目。出所 fidelity-002。
- **G-1/D-1 除去と fidelity 項目7 の定義衝突** `status: candidate` `hits: 1run`
  「加速していると言われています→加速しています」は伝聞→断定で項目7 に抵触するが、G-1/D-1 は除去対象 AI クセ。設計思想と監査項目が構造矛盾。項目7 に「命題不変なら pass、意図的な他者帰属なら fail」の例外則。出所 fidelity-001。
- （継続）削除専用サブチェック / 情報含む削除 vs ボイラープレート二分 / #5・#11 責任境界一意化。

### playbook レシピ追補
- **E-2 敬体専用の文末変奏表** `status: ready` `hits: 1run(2agent)`
  playbook は「敬体でも体言止め」と指示するが体言止めは事実上常体化し文体維持と衝突。敬体で使える変奏（です／ます／でしょう／のです／ません／過去形＋短文分割）の具体リストを E-2 に追記。出所 rewriter-001, naturalness-001。**次回適用候補**。
- **A-8/A-10 能動化の但し書き** `status: candidate` `hits: 1run(2agent)`
  「行為者が原文で自明なら能動化、不明なら自動詞化（〜になる）に留め主語を新設しない」。敬体では能動化に敬語補助動詞（〜いたします）が必須で常体前提の例が使えない。出所 rewriter-002, rewriter-001, fidelity-001/002。
- **公的文書の結語処理レシピ** `status: candidate` `hits: 1run(2agent)`
  定型結語は意味的切れ目ごとに 1 回まで許容、所存/次第の重複は解体可、冒頭挨拶（平素より〜）は不可侵。出所 rewriter-002, naturalness-002。
- **敬体 I-3 の丁寧度ラダー** `status: candidate` `hits: 1run` お〜ください＜〜してください＜〜くださいますようお願いいたします。出所 rewriter-002。
- **A-1/A-2 を「で」直結時の助詞自然さ検算** `status: candidate` `hits: 1run` 「手続きに関して→手続きで」の微 awkward を 1 回検算するサブステップ。出所 naturalness-002。
- （継続）C-5 絵文字削除後の吸収ルール / D 系「最小着地文を残す」/ 機能接続詞の変奏例外 / 元から推量の D 系は推量保持。

### カタカナ B-2 判定
- **ジャンル別「維持カタカナ」許容リスト** `status: ready` `hits: 1run(3agent)`
  技術記事のオーケストレーション・アーキテクチャ・オブザーバビリティ等は準標準語。開くと nuance 減損（本日 f032 が fidelity ロールバックに）。ジャンル別維持リスト＋文脈依存判定フローを SSOT 参照ファイルに。出所 detector-001, rewriter-001, fidelity-001。**次回適用候補**。
- （継続）定着カタカナ語 B-2 免責リスト（ルーティン・モチベーション等、残差 S3 固定）。

### naturalness 判定の精緻化
- **リズム系（E-1/E-2）専用 sub-score** `status: candidate` `hits: 1run`
  改善率が S1 除去に過剰報酬を出し、span で捉えにくい E 系リズムが数値上「解消」に見えて読むと一本調子。E カテゴリ専用の残存指標を分離。出所 naturalness-001。
- **定型結語の残存許容ライン** `status: candidate` `hits: 1run`
  「お願い申し上げます」等の慣用敬語結語は、他の文末変奏が最低1種あれば S3 以下、変奏ゼロの反復のみ S2 再発火。出所 naturalness-002。
- （継続）過推敲シグナル定量化 / クラスタ finding の severity 降格 / E-2 到達ライン緩和 / 絶対残存数ガード。

### detector 実装
- start/end 自己検証 assert / 絵文字レンジ明示（継続）。
