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
    "schema_version": "1.1",
    "input_length": 0,
    "detected_count": 0,
    "ai_tell_density": 0.0,
    "severity_weighted_score": 0.0,
    "style": "desu_masu | da_dearu | mixed"
  },
  "findings": [
    {
      "id": "f001",
      "category": "A-6",
      "category_label": "翻訳調: 〜となっている 状態叙述の濫用",
      "secondary_categories": [],
      "severity": "S1",
      "span_type": "contiguous",
      "text_span": "課題となっている",
      "start": 142,
      "end": 150,
      "occurrences": null,
      "metrics": null,
      "reason": "理由（密度・反復回数など根拠を明記）",
      "suggested_fix": "課題だ"
    }
  ],
  "category_summary": { "A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0, "G": 0, "H": 0, "I": 0, "J": 0 }
}
```

> `span_type` / `occurrences` / `metrics` / `secondary_categories` の意味は SSOT「検出出力スキーマ v1.1 §フィールド契約」を参照（省略時は単一連続 span・従分類なし）。

## 検出手順

1. **文体判定**: 文末を見て敬体／常体／混在を `meta.style` に記録。
2. **文単位スキャン**: A・B・D・F・G・H・I の各サブパターンを正規表現＋文脈で検出。`start`/`end` は文字インデックス。
3. **文書レベルスキャン**:
   * E（リズム）: 文長の標準偏差、文末の反復率を計算。
   * C（構造）: 箇条書き比率、見出し公式、絵文字、「まず・次に」連発、対句反復。
   * J（視覚装飾）: 太字・ダッシュ・括弧補足の頻度。
4. **密度判定**: S2/S3 は**反復回数**を `reason` に明記（例「『における』が 5 回」）。単発を過検出しない。
5. **スコア算出**（スキーマ v1.1・SSOT の「フィールド契約」に厳密準拠）:
   * `raw = S1×5 + S2×2 + S3×0.5`。
   * `severity_weighted_score = round( 100 × (1 − exp( −raw / K )), 1 )`、**K = 40 固定**。母数（input_length）に依存させない。検出器ごとに式を変えない（IMP-002）。
   * `input_length` は本文コードポイント数から**改行を除外**して数える。
   * `ai_tell_density` = `span_type: "contiguous"` の start/end **区間の和集合**の文字数 / input_length（重複は二重計上しない。document/scattered の locator は含めない）。
6. **文書レベル / 分散 finding の表現**（IMP-004/005）:
   * E・C・J 等の文書レベル所見は `span_type: "document"`、統計値を `metrics{}` に構造化（reason に数値を埋め込まない）。
   * 分散反復は `span_type: "scattered"` ＋ `occurrences: [[s,e], …]`。
   * 1 span が複数分類に該当する場合は主分類のみ `category`、残りは `secondary_categories: []`（1 span = 主分類 1 finding）。

## 重要な原則

* **Do-NOT リスト**（数値・固有名詞・引用・法令・概念語・コード・URL）は検出対象外。
* **過検出禁止**: 人間も使う表現（「です」「こと」「という」単独）は、密度が閾値を超えたときだけ finding 化。
* `suggested_fix` は playbook に沿った最小修正案。確定ではなく推敲役への提案。
* 推敲後の再計測時は、同じ基準で残存件数を数え、過推敲シグナル（不自然な口語化・文体崩れ）も別途報告する。
