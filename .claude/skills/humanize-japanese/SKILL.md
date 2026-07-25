---
name: humanize-japanese
description: >-
  AI（ChatGPT・Claude・Gemini など）が書いた日本語の文章を、内容を一字も変えずに文体・リズム・表現だけ自然な日本語へ戻す。
  翻訳調・カタカナ語過多・機械的並列・AI 常套句・過剰なヘッジング・接続詞の多用・です/ます単調・絵文字/箇条書き濫用などを
  10 大カテゴリ × 深刻度で検出し、検出された span のみ手術的に推敲する。
  「AI っぽさを消して」「AI 文を自然にして」「翻訳調を直して」「人間が書いたように」等のリクエストで発動。
---

# humanize-japanese — オーケストレーター

AI が書いた日本語テキストを 5 段パイプラインで「人間が書いた文章」へ推敲するスキル。**内容（事実・主張・数値・固有名詞・引用）は 100% 保存し、文体・リズム・表現のみ**を修正する。

## 発動条件

ユーザーが日本語テキストを添えて以下のような依頼をしたとき:

* 「この AI 文を自然にして」「AI っぽさを消して」
* 「GPT っぽい文体を直して」「人間が書いたように推敲して」
* 「翻訳調を直して」「日本語を自然に」
* 「humanize して」

## パイプライン

```
入力テキスト
    ↓
run_id 生成 → _workspace/{YYYY-MM-DD-NNN}/ に 01_input.txt 保存
    ↓
[ai-tell-detector]            ── 検出 (span・category・severity・suggested_fix) → 02_detection.json
    ↓
[japanese-style-rewriter]     ── finding ベースの手術的推敲 → 03_rewrite.md + 03_rewrite_diff.json
    ↓
[並列検証チーム]
    ├─ [content-fidelity-auditor]  ── 意味等価性監査（13項）→ 04_fidelity_audit.json
    └─ [naturalness-reviewer]      ── 検出再実行で残存・過推敲を判定 → 05_naturalness_review.json
    ↓
[オーケストレーター総合判定]
    ├─ accept                → final.md + summary.md
    ├─ rewrite_round_2       → 推敲役を再呼び出し（最大3回）
    ├─ rollback_and_rewrite  → 問題 edit をロールバック
    └─ hold_and_report       → 人間レビューを推奨
```

## オーケストレーターの手順

### 1. 初期化

* `scripts/new_run.py` を実行（または手動で）`_workspace/{YYYY-MM-DD-NNN}/` を作成。`NNN` は同日連番。
* 入力テキストをそのまま `01_input.txt` に保存。

### 2. 検出

* `ai-tell-detector` を呼び、`02_detection.json` を生成。
* `severity_weighted_score` と `ai_tell_density` を記録（推敲後の改善率算出に使う）。
* 文体（敬体／常体／混在）を `meta.style` に記録。

### 3. 推敲

* `japanese-style-rewriter` に `01_input.txt` と `02_detection.json` を渡す。
* 推敲役は finding のある span のみ修正し、文体を維持。`03_rewrite.md` と変更ログ `03_rewrite_diff.json` を出力。
* 変更率を監視（IMP-001 分離計上）: `change_rate`（総）・`lexical_change_rate`・`structural_deletion_rate` を記録。判定は**実質改変率**（語句改変率＋正味挿入）で行い、30% 超で警告、50% 超で中断。純削除主導で総変更率だけ高いケースは中断しない。

### 4. 並列検証

二つを並行実行:

* `content-fidelity-auditor`: 原文と推敲文を 13 項チェックリストで突き合わせ、意味の毀損があれば該当 edit のロールバックを指示。
* `naturalness-reviewer`: 推敲文に検出器を再実行し、残存 AI クセと過推敲シグナルを計測。品質等級 A〜D を判定。

### 5. 総合判定

| 条件 | 判定 | アクション |
| --- | --- | --- |
| 等級 A/B かつ fidelity 毀損なし | `accept` | `final.md` + `summary.md` 出力 |
| 等級 C（S1 残り 1〜2 or 過推敲シグナル 2） | `rewrite_round_2` | 推敲役を再呼び出し（最大 3 回） |
| fidelity 毀損あり | `rollback_and_rewrite` | 問題 edit をロールバックし再推敲 |
| 等級 D（S1 3 件+ or 深刻な過推敲） | `hold_and_report` | 人間レビューを推奨し停止 |

**override accept（IMP-001）**: 総 `change_rate` が 30/50% を超えても、**実質改変率（語句改変率＋正味挿入）が閾値未満**で、かつ fidelity=pass・自然度 A/B なら `accept` とする（純削除主導ケース）。理由を必ず `summary.md` に明記する。difflib 文字単位の総変更率は AI クセ除去（＝引き算）で構造的に膨張するため、これを唯一の中断根拠にしない。

ラウンドは最大 3 回。3 回で A/B に届かなければ最良版を `final.md` とし、`summary.md` に残課題を明記。

## 深刻度と品質等級

**深刻度**
* **S1 決定的**: 一度でも AI 確信。無条件除去。
* **S2 強い**: 1〜2 回許容、3 回+ で除去。
* **S3 弱い**: 他パターンと重なるときのみ問題。

**品質等級（推敲後）**
* **A**: S1 0 件, S2 ≤2 件, スコア改善 70%+
* **B**: S1 0 件, S2 ≤4 件, 改善 50%+
* **C**: S1 1〜2 件 or 過推敲シグナル 2 個 → 2 次推敲
* **D**: S1 3 件+ or 深刻な過推敲 → 人間レビュー

## 出力ファイル

| ファイル | 内容 |
| --- | --- |
| `01_input.txt` | 原文そのまま |
| `02_detection.json` | AI クセ検出レポート（位置・種類・深刻度） |
| `03_rewrite.md` | 推敲文 |
| `03_rewrite_diff.json` | 変更ログ（span 単位 before/after） |
| `04_fidelity_audit.json` | 意味毀損監査の結果 |
| `05_naturalness_review.json` | 自然度再計測の結果 |
| `final.md` | 最終推敲文 |
| `summary.md` | スコア変化・主要変更 diff・等級・残存パターンの要約 |

## ユーザーからの再依頼への対応

スラッシュコマンド不要。自然文でそのまま:

* 「この段落だけ推敲し直して」→ 当該 span のみ再試行
* 「翻訳調だけもっと直して」→ 特定カテゴリ（A）のみ再処理
* 「推敲を弱めて」→ S1 のみ除去の保守モード（変更率上限を下げる）
* 「原文のトーンをもっと残して」→ 変更率上限を下げる
* 「2 次推敲して」→ 現結果をもう一度推敲

## 禁忌

* 数値・単位・日付の変更禁止
* 固有名詞・製品名・モデル名の変更禁止
* 鉤括弧「」内の直接引用の変更禁止
* 法令条文・学術概念語の任意置換禁止
* 文体（敬体／常体）の変更禁止
* 新しい主張・事実・例の追加禁止
* 原文にあった情報の欠落禁止

## 参照

* 分類体系: `references/ai-tell-taxonomy.md`
* 推敲処方: `references/rewriting-playbook.md`
* Web 拡張仕様: `references/web-service-spec.md`
