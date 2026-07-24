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
    "severity_weighted_score": 0.0,
    "style": "desu_masu | da_dearu | mixed"
  },
  "findings": [
    {
      "id": "f001",
      "category": "A-6",
      "category_label": "翻訳調: 〜となっている 状態叙述の濫用",
      "severity": "S1",
      "text_span": "課題となっている",
      "start": 142,
      "end": 150,
      "span_type": "scattered",
      "occurrences": [[142, 150], [389, 397], [612, 620]],
      "reason": "理由（密度・反復回数など根拠を明記）",
      "suggested_fix": "課題だ"
    }
  ],
  "category_summary": { "A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0, "G": 0, "H": 0, "I": 0, "J": 0 }
}
```

`span_type` は任意（既定 `"contiguous"`）。詳細は taxonomy「検出出力スキーマ」の finding 任意フィールドを参照:

* `"contiguous"`: 単一連続区間。`start`/`end` が該当範囲。フィールド省略時の既定。
* `"scattered"`: 分散反復。`occurrences` に `[[start,end], ...]` で全出現を列挙し、`start`/`end` は先頭出現を指す。
* `"document"`: 文書全体が根拠（E リズム・C 構造）。`start`/`end` に代表アンカー位置を置き、`reason` に文書レベル根拠（文末反復率・文長分布等）を記す。

## 検出手順

1. **文体判定**: 文末を見て敬体／常体／混在を `meta.style` に記録。
2. **文単位スキャン**: A・B・D・F・G・H・I の各サブパターンを正規表現＋文脈で検出。`start`/`end` は文字インデックス。
3. **文書レベルスキャン**:
   * E（リズム）: 文長の標準偏差、文末の反復率を計算。
   * C（構造）: 箇条書き比率、見出し公式、絵文字、「まず・次に」連発、対句反復。
   * J（視覚装飾）: 太字・ダッシュ・括弧補足の頻度。
   * 文書レベル finding は `span_type="document"` で表現し、`start`/`end` に代表アンカーを置く（単一 start/end で全域を覆わない → density 過大化を回避）。
4. **span_type の割り当て**: 単一連続区間は `"contiguous"`（省略可）、同一パターンが複数箇所に分散反復するなら `"scattered"` として `occurrences` に全出現を列挙、文書全体が根拠なら `"document"`。
5. **密度判定**: S2/S3 は**反復回数**を `reason` に明記（例「『における』が 5 回」）。単発を過検出しない。
6. **スコア算出**:
   * `raw = S1×5 + S2×2 + S3×0.5`
   * `severity_weighted_score = round(100 × raw / (raw + 50), 1)`（k=50 固定の有界飽和関数。0〜100 未満に収まる）。例: `raw=115→69.7` / `raw=56→52.8` / `raw=37.5→42.9`。
   * `ai_tell_density` = 検出 span が被覆する文字の**和集合（union）**の文字数 / 全体文字数。重複・入れ子・`scattered` の `occurrences` は二重計上せず union で数える（上限 1.0）。

## 重要な原則

* **Do-NOT リスト**（数値・固有名詞・引用・法令・概念語・コード・URL）は検出対象外。
* **過検出禁止**: 人間も使う表現（「です」「こと」「という」単独）は、密度が閾値を超えたときだけ finding 化。
* `suggested_fix` は playbook に沿った最小修正案。確定ではなく推敲役への提案。
* 推敲後の再計測時は、同じ基準で残存件数を数え、過推敲シグナル（不自然な口語化・文体崩れ）も別途報告する。
