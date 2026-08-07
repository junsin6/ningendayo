# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数（別 run での再現のみカウント）。

最終更新: 2026-08-07（run 001 サーバーレス技術解説, 002 水道お知らせ公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done` `hits: 2runs`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。001 は char 0.356（insert 0.096・delete 0.26 の削除主導）、002 は char 0.302（−19% 圧縮）でいずれも 30% 警告帯に入るが実態は fidelity=pass / 自然度 A。**両 run で override が必要になり再現を実証**。
- 出所: 06-12 run(2agent) / 08-07 rewriter-001, rewriter-002, naturalness-001, naturalness-002
- **適用済み（2026-08-07-001,002）**: `lexical_change_rate`（語句改変率）を主指標に格上げ、`reduction_rate`/`insert_rate`/`delete_dominant` を分離計上。char_change_rate は参考値化し、`delete_dominant=true` なら閾値超過でも中断せず override accept。→ `rewriting-playbook.md §変更率の数え方 v1.1` / `SKILL.md §総合判定`（override 行追加）/ `japanese-style-rewriter.md`（diff スキーマ・監視手順）。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2runs`
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える。001 は raw 116.5 / uncapped 135 が 100 に飽和し「非常に AI」と「極端に AI」を区別不能に。
- 出所: 06-12 run(2agent) / 08-07 detector-001, naturalness-001
- **適用済み（2026-08-07, taxonomy v1.1）**: 長さ非依存の飽和関数 `100*raw/(raw+K)`（K=60 暫定・要校正）を SSOT に明記。`raw_weighted_sum`・`score_formula` を正式スキーマへ昇格。

### IMP-003 score_before のフィールド契約が曖昧 `status: done` `hits: 2runs`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定でレビュアーごとに数値がぶれる。
- 出所: 06-12 naturalness-A / 08-07 naturalness-001, naturalness-002（今回はプロンプトで明示指定して回避）
- **適用済み（2026-08-07, taxonomy v1.1）**: 「score_before = 02_detection.json の meta.severity_weighted_score（正規化後）」を SSOT に明文化。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: done` `hits: 2runs`
- 症状: 絵文字・文末単調・カタカナ濫用・まず/次に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。001 は B-2 を 10 点 finding に分解、E-2 を末尾 1 点にアンカー。002 も E-1/E-2 が他 finding と span 重複。
- 出所: 06-12 detector(2agent) / 08-07 detector-001, detector-002
- **適用済み（2026-08-07, taxonomy v1.1）**: `span_type: contiguous|scattered|document` と scattered 用 `occurrences: [[s,e],...]` を追加。density を「重複・locator を除いた実 AI クセ文字数ベース」と定義。

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2runs`
- 症状: 1 span が複数カテゴリに該当（A-5＋I-1、A-5＋A-6/A-1 の入れ子）。edits/findings が 1:1 前提で category_summary が実態を過小評価。今回 001 は I-1 を発火させず A-5 優先で回避したが規約が無く再現性が担保されない。
- 出所: 06-12 run(5agent) / 08-07 detector-001, rewriter-001（対句 finding のペア問題として再現）
- 提案: 「1 span = 主分類 1 finding」を基本とし `merged_findings: [...]` を許容。category_summary は「findings の category 先頭文字を集計」と注記。**次回適用候補**。

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 2runs`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 数値が推定値。001/002 とも手法 manual_reapply、文字列頻度のみ補助スクリプトで機械計測、E 系文書レベル判定は主観残り。
- 出所: 06-12 naturalness-A / 08-07 naturalness-001, naturalness-002
- 提案: `ai-tell-detector` をサブエージェントとして再呼び出しする経路を必須化（手動照合禁止）。**次回適用候補**（オーケストレーター側で naturalness 前に detector を再実行し 05 に添付する運用でも代替可）。

### IMP-007 検出器の suggested_fix が文体を無視し span-grounded を破る `status: open` `hits: 1run`
- 症状: 001 で suggested_fix が軒並み常体（「仕組みだ」「テクノロジーだ」）で提示され敬体維持と衝突。推敲役が毎回敬体へ翻訳し直す運用は事故のもと。さらに f004/f015 の fix が「メリット→利点」と B-2 finding のない語まで書き換え、検出器自身が span-grounded 原則を破っていた。
- 出所: rewriter-001
- 提案: (a) detector に「meta.style を継承して fix を出す」規約を追加、または playbook にカテゴリ別 after を敬体版/常体版で併記。(b) suggested_fix は finding の span 内語のみ対象と明記。
- 影響: `ai-tell-detector.md`, `rewriting-playbook.md`

### IMP-008 対句・並列 finding がペア単位でない `status: open` `hits: 1run`
- 症状: 001 で C-1「第一に／第二に」の対のうち finding は「第一に」だけ。playbook C-1 fix は両方の書換えを指示するのに片側に finding が無く、span-grounded と playbook が矛盾。今回は隣接 A-13 finding に相乗りさせて解消。
- 出所: rewriter-001（IMP-005 と同根の親子 span 問題）
- 提案: 対句・並列は「ペア単位の finding」または親 finding に子 span を紐づける構造（`child_spans`）。

### IMP-009 playbook に公的文書ジャンルのレシピが実体として無い `status: ready` `hits: 2agent/1run＋設計上明白`
- 症状: 現行 playbook 4 ジャンル記載だが公的文書（お知らせ・通知）専用レシピが無い。002 で必要だったのは (a) 敬語を「格として残す span」と「反復として崩す span」の判別基準、(b) 定型敬語の変奏カタログ（お願い申し上げます／お願いいたします／ください／ご了承ください／のほどお願いいたします）、(c) ジャンル別変更率キャリブレーション。
- 出所: rewriter-002, naturalness-002, fidelity-002（002 run 内で 3 agent が独立に指摘）
- 提案: playbook に「公的文書プロファイル」節を新設。**次回適用の最有力候補**（002 の実推敲が事実上の処方サンプルになっている）。

### IMP-010 severity・grade にジャンル別プロファイルが無い `status: ready` `hits: 2agent/複数`
- 症状: 公的文書では丁寧語の反復自体はジャンル要件で正当、拾うべきは「同一定型フレーズの機械反復」だけ。しかし現行 taxonomy/grade は一律で、(a) 敬語存在を過検出しかねず (b) 逆に「格の喪失」（賜り・締め定型の削除しすぎ）を過推敲として捕捉できない。002 で naturalness は「格保持を A の必須条件に」と提案。
- 出所: detector-002, fidelity-002, naturalness-002
- 提案: ジャンル別 severity プロファイル＋「反復依存型パターンは出現回数で severity 段階化（1回=S3/2回=S2/3回+=S1）」を SSOT に導入。公的文書では格保持チェックを grade に接続。A-1 の「定義 S1 vs 処方 2回許容」矛盾もこれで解消。**次回適用候補**（taxonomy v1.1 候補欄に段階化案を登録済み）。

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査中 / taxonomy v1.1 候補欄に登録）
- **公的文書 signature「〜いただきますようお願い申し上げます」定型連結の過剰反復** ★日本語固有。実例(002): ご確認／ご了承／ご連絡／お問い合わせ が全同一末尾で 4〜5 回。人間は 1〜2 回。D-7 or E-2 下位候補。`hits: 1`（002 で detector/rewriter/naturalness）出所 detector-002 ほか
- **「見ていきましょう / 解説していきます」勧誘・進行形メタ叙述**。実例(001): 見ていきましょう／解説していきます／解説します の 3 反復。C-6 の文中型。`hits: 1` 出所 detector-001
- **「〜のです / のである」説明強調の連鎖**。実例(001): 活用できるのです／削減できるのです。E-2 と別軸の文末クセ。`hits: 1` 出所 detector-001
- **「〜ため、〜」因果従属節の機械的多用**（英語 so that/because 直訳）。実例(001): 調整されるため…／課金されるモデルのため…。A 系サブ候補。`hits: 1` 出所 detector-001
- **redundant restatement**（叙述＋箇条書きの二重記載）。実例: 06-12-001。`hits: 1` 出所 detector-A（前回）
- **D-7 ブログ結び呼びかけ公式**（今回は/ご紹介しました/してみてはいかが）。`hits: 1` 出所 detector-B（前回）
- **C-9 導入誘導定型**（さっそく見ていきましょう）。`hits: 1` 出所 detector-B（前回）※ 001 のメタ叙述候補と統合検討

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** `status: ready` `hits: 2runs`。06-12 の f019 で発生、08-07-001 では f016「第一に→一つは」が中立列挙に留まり**再発せず**（#14 が有効に機能）。→ #14 を正式項目化する価値を再確認。出所 fidelity-A(前回), fidelity-001
- **削除の二分判定 factual_deletion / boilerplate_deletion タグ必須化** `status: ready` `hits: 2runs`。#10 に埋没している判定を明示二分岐に。001「徹底/非常に/まさに」・002「こととなっております/必要がございます」は全て boilerplate と確認。出所 fidelity-B(前回), fidelity-001, fidelity-002
- **modality の順序尺度化** `status: ready` `hits: 2runs`。#7 の 3 クラス二値判定では同一クラス内の強度差（に他ならない→です の強調降格、必要がある→ください の義務→依頼）を捕捉不能。強度スコア化し「クラス跨ぎ=毀損疑い/クラス内降格=border_note」。出所 fidelity-A(前回), fidelity-001, fidelity-002
- **用語の短縮を #2 の毀損から除外**（新）。「サーバーレスアーキテクチャ→サーバーレス」等、既出完全形あり・指示同一なら短縮可と #2 に明記。`hits: 1` 出所 fidelity-001
- **敬語変奏が依頼の向き（誰が誰に）を保存しているか**を独立チェック項目化（新）。#7 丁寧度と #9 行為者に跨るため。`hits: 1` 出所 fidelity-002
- **公的文書プロファイルの削除 recall 必須項目**（新）: 連絡先/受付時間/部署名の部分欠落・費用負担の主体・留保語（原則として/万一/場合により）。`hits: 1` 出所 fidelity-002

### playbook レシピ追補
- **E-2 敬体向け変奏カード不足** `status: ready` `hits: 2runs`。敬体は「です/ます/でしょう/体言止め」に限られ振り幅が出ない。「〜ものです／〜わけです／名詞止め＋。」等を追記。出所 rewriter-A(前回 相当), rewriter-001, naturalness-001
- **変奏先の単調反復リスク**（新）: I-3「必要がございます」を一律「ください」に開くと ください×8 の新単調を生む。動詞語幹を散らす・受け皿を複数用意する再変奏レシピ。`hits: 1` 出所 rewriter-002, naturalness-002
- C-5 絵文字削除後の文末吸収ルール / D 系結びは最小着地文を残す / 機能が必要な接続詞は変奏 / 原文が元から推量の D 系は推量保持（前回分・据置）。

### naturalness 判定の精緻化
- **クラスタ崩壊時の severity 降格ルール** `status: ready→実装` `hits: 2runs`。反復・密度で発火する S2 はクラスタ崩壊時に残 1〜2 を降格。001 で E-2(S2→S3)・C-1 消失・F-4 閾値未達(S2→S3)を実装。SSOT へ明文化候補。出所 naturalness-A(前回), naturalness-001
- **反復回数→深刻度の閾値を SSOT に数値化**（新・強い）: 「同一文末型 N 回以上で S2」等。002 の ください×8 を S2 認定した根拠が手動推論だった。IMP-010 の段階化と統合。`hits: 1`（naturalness-001,002,detector-002）
- 過推敲シグナルの定量化（敬体/常体の二値カウント・縮小率）／絶対残存数ガードを grade 表に組込み（前回分・据置、今回両 run で運用）。

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 2runs`
- ルーティン・モチベーション・データドリブン・メリット 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。001 で「メリット」を維持（finding 非該当）。出所 naturalness-B(前回), rewriter-001

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert）→ 001/002 とも自己検証を実施し不一致 0 で運用済み。仕様として明文化候補。
- 絵文字正規表現レンジ明示（前回分・据置）。
