# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-07-17（run 001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done` `hits: 2run` `applied: 2026-07-17-001,002`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。06-12 Sample B 54.6%、07-17 run001 31.4%・run002 37.2% がいずれも削除主導（挿入率 6〜9%）で hold 誤発火寸前。
- 出所: 06-12 rewriter-A/B, naturalness-B ／ 07-17 rewriter-A, rewriter-B, naturalness-A, naturalness-B（2 run で再現）
- **適用（v1.1）**: `insertion_rate` と `deletion_rate` を分離計上。中断判定を挿入率基準に置換 — 挿入率 ≤15% かつ fidelity=pass なら change_rate 30〜50% でも override accept（削除主導＝健全な圧縮）、挿入率 >25% または意味改変 edit で hold。旧 30/50% 一律閾値は廃止。
- 編集: `rewriting-playbook.md §変更率の数え方`, `SKILL.md §総合判定`。
- 残: rewriter/diff スキーマに insertion_rate/deletion_rate を正式フィールド化（次回）。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2run` `applied: 2026-07-17`
- 症状: 正規化式が SSOT に無く、07-17 では detector-A が `min(100,raw)`、detector-B が飽和型と別式を採用 → run 間・検出器間で数値が比較不能。
- 出所: 06-12 detector-A/B ／ 07-17 detector-A, detector-B, naturalness-B（2 run で再現）
- **適用（v1.1）**: `raw = 5|S1|+2|S2|+0.5|S3|`、`severity_weighted_score = round(100*(1-exp(-raw/30)),1)`（K=30 固定）を唯一の正典として明記。score_before/after 同式統一。ai_tell_density は分母=改行除く実文字数・分子=被覆 span の和集合（重複排除）と明文化。
- 編集: `ai-tell-taxonomy.md §検出出力スキーマ`（v1.1）, `ai-tell-detector.md §スコア算出`。

### IMP-003 score_before のフィールド契約が曖昧 `status: ready` `hits: 1run+`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。
- 部分解消（v1.1）: 「score_before/after は共に severity_weighted_score 式で算出」を SSOT 明記。残: 「score_before = 02_detection.json の meta.severity_weighted_score を参照」という参照元の明文化を naturalness-reviewer.md に。
- 出所: 06-12 naturalness-A ／ 07-17 naturalness-B

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: done` `hits: 2run` `applied: 2026-07-17`
- 症状: E-1 文長均一・E-2 文末単調・絵文字分散は単一 start/end で表せず、代表 span への無理アンカーで density 過大＆ start/end 自己検証と衝突。
- 出所: 06-12 detector-A/B ／ 07-17 detector-A, detector-B, rewriter-A, rewriter-B, fidelity-B（2 run で再現）
- **適用（v1.1）**: finding に `scope: contiguous|scattered|document`（既定 contiguous）。document は start/end/text_span を null 許容で `evidence`（文長 stdev・文末反復率等）を持つ。scattered は `occurrences:[[s,e],...]`。start/end 自己検証は contiguous/scattered のみ必須。density は document を分子除外。
- 編集: `ai-tell-taxonomy.md §スキーマ`（v1.1）, `ai-tell-detector.md`（手順6 scope 付与）。

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run` **← 次回適用候補**
- 症状: 1 span が複数カテゴリに該当（A-6＋A-8＋I-3 の三重、I-4＋B-2＋I-1 等）。edits/findings 1:1 前提で category_summary が過小評価、ロールバック時に連動 edit の before/after が破綻。
- 出所: 06-12 detector-A, rewriter-A/B, naturalness-A, fidelity-A ／ 07-17 detector-B, rewriter-A, rewriter-B, fidelity-A, fidelity-B（2 run で再現・最多）
- 提案: (a) 「1 span = 主分類 1 finding」＋ `merged_findings:[...]` 許容。(b) diff の edit に複数 finding_id を持てる `co_resolved:[...]` または `edit_group` キー。(c) rollback は「連動 edit グループ」単位。category_summary は「findings の category 先頭文字を集計」と注記。
- 影響: 全 .md のスキーマ節。

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: done(実践検証)` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは手動照合 → 推定値。
- 出所: 06-12 naturalness-A ／ 07-17 naturalness-A（run001 で ai-tell-detector サブエージェントを実呼び出しし score_after=2.0 を実測。経路が機能することを実証）
- 残: `naturalness-reviewer.md §処理` に「ai-tell-detector をサブエージェント再呼び出し必須（手動照合禁止）」を明文化（次回・小改修）。

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査 — v1.1 で拡張候補欄に登録済、本採用は異 run 再現待ち）
- **K. 過剰敬語・冗長敬語（★日本語固有）** `hits: 1run` 出所 07-17 detector-B, naturalness-B。K-1 二重敬語「していただく必要がございます」/ K-2 定型結語過反復「お願い申し上げます」×3+/ K-3「〜いただきますよう」連発。設計思想が柱に挙げる「過剰な丁寧体・敬語」の受け皿が A〜J に無い穴。実例 run002。※密度・二重敬語に条件を絞る設計が必要（人間も使うため）。
- **A-8 拡張: 行為者を伏せた受動（agentless passive）** `hits: 1run` 出所 07-17 detector-B。現行「〜によって」限定を拡張。実例 run002「実施されることとなりました/予定されております」（によって不使用で受動7回）。
- **A-14「〜されることで」受動経由の節接続 [S2]** `hits: 1run` 出所 07-17 detector-A。実例 run001「プロンプトにインジェクションされることで」。
- **B-2 サブ「英日同義反復（言い換え自己重複）」** `hits: 1run` 出所 07-17 detector-A。実例 run001「リトリーブ→取得」「セマンティック→意味的」同一概念の英日ダブり。
- **C 系: redundant restatement**（叙述と箇条書きの二重記載）`hits: 1` 出所 06-12 detector-A。
- **D-7 ブログ結び呼びかけ公式** `hits: 1` 出所 06-12 detector-B。
- **C-9 導入誘導定型**（さっそく見ていきましょう式）`hits: 1` 出所 06-12 detector-B。

### B-2 維持/開語リスト（技術語ホワイト・ブラックリスト）`status: ready` `hits: 1run(3agent)` **← 有望**
- 症状: 「業界標準語は維持」の境界が判定者依存で B-2 件数がぶれ score 不安定。
- 提案: taxonomy/playbook に実語リスト。維持=ベクトル/プロンプト/トークン/エンベディング/チャンク/RAG/API/SDK/GPU、開語=アウトプット→出力/ナレッジ→知識/レスポンス→応答/メリット→利点/リトリーブ→取得/インジェクション→差し込み/キャッチアップ→追随/ソリューション→解決策。境界（コンテキスト/クエリ/インデックス/パフォーマンス/ソース）はジャンル別可否テーブルで。
- 出所: 07-17 detector-A, rewriter-A, fidelity-A（同 run 3 agent。異 run 再現で ready 確定）。

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** `status: ready` `hits: 1` 出所 06-12 fidelity-A（f019 型）。
- **削除専用サブチェック（deletion-recall test）** `status: ready` `hits: 1` 出所 06-12 fidelity-B。
- **手順・指示連鎖の順序保存チェック** `hits: 1run` 出所 07-17 fidelity-B（f017 濁り→通水→透明確認→使用の順序反転は欠落とは別種の毀損）＋ fidelity-A（列挙整合）。公的文書・マニュアル系で第14項候補。
- **borderline / pass_with_note verdict 層** `hits: 1run(2agent)` 出所 07-17 fidelity-A, fidelity-B。pass/fail 二値では「pass だが要観察」（modality 微減・手段↔条件変換）を落とせず独自フィールド化を強いられた。
- **modality 弱化除去の一次責任** `hits: 1run` 出所 07-17 fidelity-A。「でしょう」除去等は fidelity=pass だが過推敲軸と重なる。受け渡しルール明文化。
- 「情報を含む削除 vs ボイラープレート削除」二分判定 / #5論理関係 と #11情報追加 の責任境界一意化 / modality 強度の順序尺度化。出所 06-12 fidelity-A/B。

### playbook レシピ追補
- **複合クセの圧縮優先順位**（A-6 状態叙述→A-5 可能→I 形式名詞 の順に解体）`hits: 1run` 出所 07-17 rewriter-A（「返すことが可能となるのです」三重複合）。
- **近接する未検出 span との衝突回避ルール**（suggested_fix が隣接原文と重複する時の分散）`hits: 1run` 出所 07-17 rewriter-A。
- **ジャンル別 敬度フロア（レジスター下限）** `hits: 1run(3agent)` 出所 07-17 rewriter-B, naturalness-B, fidelity-B。公的文書は「してください」が上限で「しろ」不可。コラム/レポート/公的文書で敬度下限を明記。
- **体言止めの投入上限**（1段落あたり回数・文中位置の目安）`hits: 1run` 出所 07-17 rewriter-A, naturalness-A。
- C-5 絵文字削除後の文末吸収 / D 系結びの最小着地文 / 機能が必要な接続詞は変奏 / 元から推量の D 系は推量保持。出所 06-12 rewriter-A/B。

### naturalness 判定の精緻化
- **residual に origin フラグ（detection_miss vs rewrite_残存）** `hits: 1run` 出所 07-17 naturalness-B。今回 run002 の残存 S1 は detector 検出漏れ由来 → round2 は「reviewer 検出を根拠に紐づける」ことを発動条件に固定（span-grounded 原則保護）。
- **単発 S1 の等級インパクト救済** `hits: 1run` 出所 07-17 naturalness-B。severity ラベル（固定）と密度処方（「2回以下許容」）の矛盾で、処方閾値内に剪定した優秀な推敲が残り1件の S1 で C に落ちる。残存が密度処方内なら救済する分岐を検討。
- **公的文書の「格ダウン過推敲」シグナル**（敬語簿記語を削りすぎて事務連絡調に落ちる）`hits: 1run` 出所 07-17 naturalness-B。
- 過推敲シグナルの定量化 / クラスタ系 finding の降格ルール / E-2 到達ラインの緩和 / 絶対残存数ガードを grade 表に組込み。出所 06-12 naturalness-A/B。

### detector 実装
- start/end 自己検証（Python 実測で二段照合、不一致なら JSON 出さない）出所 06-12/07-17 detector-A。
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 06-12 detector-B。
