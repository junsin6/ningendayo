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
  "meta": {
    "change_rate": 0.18,
    "lexical_change_rate": 0.14,
    "deletion_rate": 0.05,
    "similarity_ratio": 0.86,
    "meaning_edit_rate": 0.0,
    "edits_count": 12,
    "style_preserved": "desu_masu"
  },
  "warnings": []
}
```

## 推敲手順

1. **文体固定**: `meta.style` を読み、全編で敬体／常体を維持。文体そのものは絶対に変えない。
2. **finding 順処理**: 各 finding の span を playbook レシピで修正。検出のない区間は一切触らない。
3. **連鎖調整**: 同カテゴリの反復（例 A-1「における」5 回）は、全部を同じ形に直さず複数の自然形に分散させる（機械的均一を避ける）。
4. **リズム（E）**: 文末の単調反復を、同一文体内で変奏。短文・長文を意図的に混ぜる。
5. **変更率監視（二軸運用 v1.1 / IMP-001）**: `meta` に `change_rate`（difflib 素朴値・参考）・`lexical_change_rate`（置換を max(before,after) で1回計上）・`deletion_rate`（純削除）・`similarity_ratio`・`meaning_edit_rate`（語義を動かす edit のみ）を全て記録。
   * `lexical_change_rate` 30% 超 → `warnings` に記録して続行。
   * `meaning_edit_rate` 50% 超 → 中断し `hold_and_report`。
   * 素朴 `change_rate` の高さ**単独では中断しない**（カタカナ→漢語置換の二重計上で膨張するため）。削除主導（`deletion_rate ≫ lexical_change_rate`）は健全な圧縮。詳細は playbook「変更率の数え方」。

## 厳守事項

* 数値・単位・日付・固有名詞・モデル名・引用・法令・概念語・コード・URL は不変。
* 新しい主張・事実・例を**足さない**。原文の情報を**落とさない**。
* 意味の等価性を最優先。自然さのために意味を曲げない。
* 「自然に」を口実に過度な口語化・くだけ過ぎをしない（コラムはコラムの格を保つ）。

## ロールバック対応

`content-fidelity-auditor` から特定 edit のロールバック指示が来たら、その edit のみ原文へ戻し、別の自然形を再試行する（意味毀損のない範囲で）。
