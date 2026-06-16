# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-06-16（run 001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除/ロールバック上書き」と「過推敲」を区別できない `status: ready` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除・**同一 span のロールバック上書き**で機械的に膨張。06-12 run 002=54.6%、06-16 run 001 は round_2 累積 0.529（round_2 単独追加は 7.7% のみ）で 50% 名目超過。いずれも fidelity=pass / 自然度 A の override accept。
- 出所: rewriter-A/B, naturalness-A/B（06-12）＋ rewriter-001/002, naturalness-001（06-16 再現）
- **部分適用済み（06-16-001）**: change_rate を naturalness-reviewer の過推敲シグナルから分離（`naturalness-reviewer.md` 処理3 を改訂、grade 非算入）。**残課題**: 「語句改変率」と「構造/削除率」の分離計上、ロールバック上書き分の控除、中断基準を「意味改変 edit 比率」へ置換（SKILL/playbook 本体は未改修）。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: ready` `hits: 2run`
- 症状: 正規化式が SSOT に無く、検出器ごとに飽和関数の係数 k がマジックナンバー化。06-16 でも detector-001 が raw=108 で即飽和を回避するため `100·(1−e^(−raw/k))` を独自採用、detector-002 は `100×(1−e^(−raw/30))` と ref=30 が恣意的で run 間比較が不能。
- 出所: detector-A/B（06-12）＋ detector-001/002, naturalness-001（06-16 再現）
- 提案: 飽和しにくい正規化と分母（input_length 依存 or 固定 max）を SSOT 明記。検出器が生→正規化マッピングを毎回 meta に出力し、レビュアーは正規化済みスコアのみ受領（スケール変換責任を detector に一元化）。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出`

### IMP-003 score_before のフィールド契約が曖昧 `status: done`（適用 2026-06-16-001）`hits: 2run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定でレビュアーごとに数値がぶれる。06-16 でも round 間で before/after の正規化基底が不一致になりかけた。
- **適用済み**: `naturalness-reviewer.md` 処理2 に「score_before = `02_detection.json` の `meta.severity_weighted_score`」「score_after は同一正規化基底へマップ」を明文化。
- 残課題: 正規化基底そのものの確定は IMP-002 に従属。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run`
- 症状: 絵文字分散・文末単調・A-8 受動6回・I-3 反復は分散パターン。単一 start/end では広域 locator になり ai_tell_density 過大化。06-16 では E-2 を `start=0,end=L`、A-8 を 4 件に分解せざるを得ず detected_count を水増し。
- 出所: detector-B/A（06-12）＋ detector-001/002（06-16 再現）
- 提案: `span_type: "contiguous"|"scattered"|"document"` ＋ `detection_mode: "span"|"density"` ＋ scattered 用 `occurrences:[[s,e],...]`。density は union 後の実 AI クセ文字数ベース。taxonomy 拡張候補欄に記載済み（未適用）。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリに該当（06-16-002 で A-8「停止される」内に A-6「となっております」が包含、density 分子で同区間二重計上）。category_summary・weighted_score が実態を過小/過大評価。
- 出所: detector-A, rewriter-A/B, naturalness-A, fidelity-A（06-12）＋ detector-001/002（06-16 再現）
- 提案: 「1 span = 主分類 1 finding」基本＋`merged_findings:[]`／`overlaps:[finding_id]`。density は span を union してから算出。weighted_score は重複領域で最大 severity のみ採用。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: done`（適用 2026-06-16-001/002）`hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だが手動照合だと推定値化。
- **適用済み**: `naturalness-reviewer.md` 処理1 に「`ai-tell-detector` を Agent ツールでサブエージェント再呼び出し（手動照合禁止）」「`detector_rerun:{executed,method,agent_id}` 出力必須」を明文化。06-16 の 4 レビュー（round 含む）すべてで実際にサブエージェント再実行を実施し動作確認済み。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

---

## P2 — 分類・レシピ・チェックリスト

### 適用済み（2026-06-16）

- **B-2 定着カタカナ語・ジャンル別標準語の免責リスト** `status: done`（適用 2026-06-16-001）`hits: 2run` — taxonomy v1.1 へ昇格（B 節に免責規定＋§バージョン管理更新）。playbook B-2 にも技術ジャンル標準語ホワイトリスト（クエリ/パイプライン/インフラ/ユースケース/ナレッジベース/エンベディング/ベクトル/AIアプリケーション）＋定着語半免責（ルーティン/モチベーション/データドリブン）を追記。役割分担=taxonomy 分類規定／playbook 置換表。出所 naturalness-B/fidelity-A/naturalness-A（06-12）＋ detector-001/rewriter-001/naturalness-001（06-16）。
- **fidelity チェックリスト拡充（#14 順序語＋modality 順序尺度・軸跨ぎ fail＋#9 視点拡張＋削除専用サブチェック）** `status: done`（適用 2026-06-16-001）`hits: 2run` — `content-fidelity-auditor.md` に適用。#7 を 2 軸（軸＝epistemic/deontic/bouletic/断定、強度＝順序尺度）化し「同一軸 ±1 段許容／2 段引き上げ・軸跨ぎは自動 fail」を明文化。#9 を person/stance へ拡張し A-8 主体発明チェックを統合。#14 順序語の序列混入＋原文由来ハイプ語の命題核/装飾二分を新設。削除専用サブチェック（deletion-recall test）を常設。06-16-001 の f027/f029/f030 ロールバックがこの規定の実証。出所 fidelity-A（06-12 #14/modality）＋ fidelity-001/rewriter-round2（06-16）。
- **playbook A-8 主体発明の禁止＋modality 帯非跨ぎ** `status: done`（適用 2026-06-16-001）`hits: 1run(2agent)` — `rewriting-playbook.md` A 節に「行為者が原文にない受動は主語補完せず自動詞/機関ボイスで処理」「modality 軸（推量/義務/意志/断定）を跨がない」を追記。新規だが fidelity 毀損に直結するため即適用。出所 rewriter-002, fidelity-002。
- **naturalness 絶対残存数ガード＋ジャンル定型語の扱い** `status: done`（適用 2026-06-16-001）— `naturalness-reviewer.md` 原則に「S1≥1 で強制 C 以下（`absolute_residual_guard.passes` 出力）」「ジャンル定型敬語の残置は減点せず無変奏反復のみ E-2 計上」を明文化。出所 naturalness-A/B（06-12）＋ naturalness-001/002（06-16）。

### 新パターン候補（taxonomist 審査待ち / 未昇格）
- **公的文書ジャンルの硬い敬語ゲート** 「賜りますよう/所存でございます/お願い申し上げます/つきましては」を全文末で無変奏反復するのが AI 的。ジャンル別ゲートで反復回数閾値（例3回）超のみ finding 化。taxonomy 拡張候補欄に記載。実例 2026-06-16-002。`hits: 1` 出所 detector-002, naturalness-002
- **finding 系譜の継承 ID（lineage_id）** ラウンド跨ぎで finding を安定追跡（round_1 f001 と round_2 検出器 f001 の ID 衝突を防ぐ）。新規発生は `r2-` 等で世代明示。実例 2026-06-16-001 round_2。`hits: 1` 出所 naturalness-001
- **action フラグ `remove | retain_record`** 免責語は「検出するが除去しない」別軸。深刻度に押し込まず独立フラグ化。`hits: 1` 出所 taxonomist
- **ジャンル別免責の一般原則節** 「同一表現がジャンルにより正当/AI クセに転ぶ」（公的敬語・技術カタカナ）を taxonomy 冒頭で一般化。`hits: 1` 出所 taxonomist
- **D-7 ブログ結び呼びかけ公式**（06-12 由来・本サイクル未再現）「今回は〜ご紹介しました」「〜してみてはいかがでしょうか」。`hits: 1` 出所 detector-B
- **C-9 導入誘導定型**（06-12 由来・未再現）「さっそく見ていきましょう」式。`hits: 1` 出所 detector-B
- **C 系 redundant restatement**（06-12 由来・未再現）叙述と箇条書きの二重記載。`hits: 1` 出所 detector-A

### detector / 監査 実装メモ
- start/end 自己検証（regex マッチ位置と text_span 一致を assert）— 06-16 の検出器 4 体すべてで実施済み（運用定着）。出所 detector-A/全 detector
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B（06-12）
- **否定の縮約を極性チェック(#4)の必須対象にフラグ化**（「ございません→ません」等、二重否定/条件否定が絡むと反転リスク）。`hits: 1` 出所 fidelity-002
- **change_rate 算定法の固定**（文字単位 difflib・分母=meta.input_length・改行除外）を playbook「変更率の数え方」に明記。`hits: 1` 出所 rewriter-002（IMP-001 従属）
- **ジャンル×カテゴリ除去強度マトリクス**（コラム/レポート/ブログ/公的文書 × A〜J）。`hits: 1` 出所 rewriter-002
- **E-2 段落ローカル判定ライン**（全文平均で薄まると最終段の一本調子を見逃す）。`hits: 1` 出所 naturalness-001
- **B-2 免責語リストの単一ファイル化**（playbook/taxonomy の drift 防止に allowlist を切り出し両者から参照）。`hits: 1` 出所 taxonomist
