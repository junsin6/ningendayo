---
name: ai-tell-detector
description: 日本語テキストを走査し、AI クセを span 単位の JSON レポートとして出力する検出器。文単位パターンと文書レベルパターン（リズム・構造）の両方を検出する。推敲前と推敲後（自然度再計測）の両方で使う。
---

# ai-tell-detector — 検出器

入力日本語テキストを `references/ai-tell-taxonomy.md` に照らして走査し、AI クセを span 単位で検出する。

## 入力

* `01_input.txt`（推敲前）または `03_rewrite.md`（推敲後の再計測）

## 出力

`02_detection.json`（または `05_*` 用の再計測 JSON）。スキーマは taxonomy の「検出出力スキーマ」に厳密準拠。

```json
{
  "meta": {
    "input_length": 0,
    "detected_count": 0,
    "ai_tell_density": 0.0,
    "severity_weighted_raw": 0.0,
    "severity_weighted_score": 0.0,
    "score_formula": "v1.1: 100*(1-exp(-(raw/input_length*100)/8))",
    "style": "desu_masu | da_dearu | mixed"
  },
  "findings": [
    {
      "id": "f001",
      "category": "A-6",
      "category_label": "翻訳調: 〜となっている 状態叙述の濫用",
      "severity": "S1",
      "scope": "contiguous | scattered | document",
      "text_span": "課題となっている",
      "start": 142,
      "end": 150,
      "occurrences": [[142, 150]],
      "reason": "理由（密度・反復回数など根拠を明記）",
      "suggested_fix": "課題だ"
    }
  ],
  "category_summary": { "A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0, "G": 0, "H": 0, "I": 0, "J": 0 }
}
```

## 検出手順

1. **文体判定**: 文末を見て敬体／常体／混在を `meta.style` に記録。
2. **文単位スキャン**: A・B・D・F・G・H・I の各サブパターンを正規表現＋文脈で検出。`start`/`end` は文字インデックス。
3. **文書レベルスキャン**:
   * E（リズム）: 文長の標準偏差、文末の反復率を計算。
   * C（構造）: 箇条書き比率、見出し公式、絵文字、「まず・次に」連発、対句反復。
   * J（視覚装飾）: 太字・ダッシュ・括弧補足の頻度。
4. **密度判定**: S2/S3 は**反復回数**を `reason` に明記（例「『における』が 5 回」）。単発を過検出しない。
5. **スコア算出**（v1.1 で式を確定・IMP-002。検出器ごとに式を発明しないこと）:
   * `severity_weighted_raw` = S1×5 + S2×2 + S3×0.5（生加重和）を `meta` に必ず併記。
   * `raw_per_100` = `severity_weighted_raw / input_length * 100`（100 字あたり密度）。
   * `severity_weighted_score` = `round(100 * (1 - exp(-raw_per_100 / 8)), 1)`（定数 K=8、文書長非依存・飽和しにくい）。
   * `meta.score_formula` に採用式を明記する（run 間・推敲前後のスコア比較を保証するため）。
   * `ai_tell_density` = 実 AI クセ文字数 / 全体文字数。重複と広域 locator を除いた実カバー文字集合で算出し、`scope:"document"` の代表 span は算入しない。
6. **scope 付与**（IMP-004）: 単一連続 span は `contiguous`。同一パターンが複数箇所に分散する場合は `scattered` とし `occurrences` に全 `[start,end]` を列挙（3 回以上の反復は 1 finding に潰さない）。文長均一・文末単調など文書全体の性質は `document`（`occurrences` に根拠 span 群、density には算入しない）。

## 重要な原則

* **Do-NOT リスト**（数値・固有名詞・引用・法令・概念語・コード・URL）は検出対象外。
* **過検出禁止**: 人間も使う表現（「です」「こと」「という」単独）は、密度が閾値を超えたときだけ finding 化。
* `suggested_fix` は playbook に沿った最小修正案。確定ではなく推敲役への提案。
* 推敲後の再計測時は、同じ基準で残存件数を数え、過推敲シグナル（不自然な口語化・文体崩れ）も別途報告する。
