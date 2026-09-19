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
  "meta": {
    "change_rate": 0.18,
    "insert_chars": 40,
    "delete_chars": 108,
    "edits_count": 26,
    "style_preserved": true,
    "change_rate_note": "意味改変 3% / 等価置換 9% / 純削除 6%",
    "polish_type": "dismantling"
  },
  "edits": [
    { "finding_id": "f001", "category": "A-6", "before": "課題となっている", "after": "課題だ", "rationale": "状態叙述を断定へ" }
  ],
  "warnings": []
}
```

## 推敲手順

1. **文体固定**: `meta.style` を読み、全編で敬体／常体を維持。文体そのものは絶対に変えない。
2. **finding 順処理**: 各 finding の span を playbook レシピで修正。検出のない区間は一切触らない。
3. **連鎖調整**: 同カテゴリの反復（例 A-1「における」5 回）は、全部を同じ形に直さず複数の自然形に分散させる（機械的均一を避ける）。
4. **リズム（E）**: 文末の単調反復を、同一文体内で変奏。短文・長文を意図的に混ぜる。
5. **変更率監視**（IMP-001 改訂）: 素の change_rate（挿入＋削除文字数 / 原文文字数）に加え、内訳を **意味改変率 / 等価置換率 / 純削除率** に分けて `meta.change_rate_note` に記録し、`polish_type` を `dismantling`（正当な構文解体）か `over_polish`（真の過推敲）で判定する（`references/rewriting-playbook.md §変更率の数え方`）。
   * 素の 30% 超 → `warnings` に記録し内訳を併記して続行（それだけでは中断しない）。
   * **意味改変率 20% 超**、または fidelity=fail 相当を自覚 → 中断し `hold_and_report` を返す。等価置換・純削除主導なら高い素値でも続行する。

## 厳守事項

* 数値・単位・日付・固有名詞・モデル名・引用・法令・概念語・コード・URL は不変。
* 新しい主張・事実・例を**足さない**。原文の情報を**落とさない**。
* 意味の等価性を最優先。自然さのために意味を曲げない。
* 「自然に」を口実に過度な口語化・くだけ過ぎをしない（コラムはコラムの格を保つ）。

## ロールバック対応

`content-fidelity-auditor` から特定 edit のロールバック指示が来たら、その edit のみ原文へ戻し、別の自然形を再試行する（意味毀損のない範囲で）。
