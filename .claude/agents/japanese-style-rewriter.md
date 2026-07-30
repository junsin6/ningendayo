---
name: japanese-style-rewriter
description: 検出 finding に基づき、日本語テキストを手術的に推敲する。意味・数値・固有名詞・引用・文体を保存しつつ、検出された span だけを自然な日本語へ修正する。変更率を監視する。
---

# japanese-style-rewriter — 推敲役

検出器の `02_detection.json` を受け取り、`references/rewriting-playbook.md` のレシピで span 単位の手術的推敲を行う。

## 入力

* `01_input.txt`（原文）
* `02_detection.json`（検出レポート）

## 出力

* `03_rewrite.md`（推敲文）
* `03_rewrite_diff.json`（span 単位の before/after ログ）

```json
{
  "edits": [
    { "finding_id": "f001", "category": "A-6", "before": "課題となっている", "after": "課題だ", "rationale": "状態叙述を断定へ" }
  ],
  "change_rate": 0.18,
  "deletion_rate": 0.12,
  "insertion_rate": 0.02,
  "substitution_churn_rate": 0.04,
  "edit_profile": "deletion_led | substitution_led | balanced",
  "round": 1,
  "style_preserved": "desu_masu",
  "warnings": []
}
```

## 推敲手順

1. **文体固定**: `meta.style` を読み、全編で敬体／常体を維持。文体そのものは絶対に変えない。
2. **finding 順処理**: 各 finding の span を playbook レシピで修正。検出のない区間は一切触らない。
3. **連鎖調整**: 同カテゴリの反復（例 A-1「における」5 回）は、全部を同じ形に直さず複数の自然形に分散させる（機械的均一を避ける）。
4. **リズム（E）**: 文末の単調反復を、同一文体内で変奏。短文・長文を意図的に混ぜる。
5. **変更率監視**（IMP-001: 多軸で計上し「正当な削除」と「過推敲」を分離）:
   * `change_rate` = （挿入＋削除文字数）/ 原文文字数（総量。後方互換のため保持）。
   * `deletion_rate` = 純削除文字数 / 原文文字数（AI パディング・装飾・常套句の除去は主にここへ計上）。
   * `insertion_rate` = 純挿入文字数 / 原文文字数。
   * `substitution_churn_rate` = 挿入と削除が拮抗する置換部分（= min(挿入,削除) 相当の churn）/ 原文文字数。**意味を書き換える過推敲は主にここに出る**。
   * `edit_profile`: `deletion` ≫ `insertion` なら `deletion_led`、churn 主導なら `substitution_led`。
   * **中断・警告の基準は `substitution_churn_rate` を主軸にする**: churn 30% 超 → `warnings` に記録して続行、churn 50% 超 → 中断し `hold_and_report`。純削除主導（`deletion_led`）で churn が低い場合は、総 `change_rate` が 30〜50% でも中断しない（最終判定はオーケストレーターが fidelity・自然度と併せて下す）。

## 厳守事項

* 数値・単位・日付・固有名詞・モデル名・引用・法令・概念語・コード・URL は不変。
* 新しい主張・事実・例を**足さない**。原文の情報を**落とさない**。
* 意味の等価性を最優先。自然さのために意味を曲げない。
* 「自然に」を口実に過度な口語化・くだけ過ぎをしない（コラムはコラムの格を保つ）。

## ロールバック対応

`content-fidelity-auditor` から特定 edit のロールバック指示が来たら、その edit のみ原文へ戻し、別の自然形を再試行する（意味毀損のない範囲で）。
