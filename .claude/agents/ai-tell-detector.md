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
    "score_raw": 0.0,
    "severity_weighted_score": 0.0,
    "score_formula": "100*raw/(raw+30)",
    "style": "desu_masu | da_dearu | mixed"
  },
  "findings": [
    {
      "id": "f001",
      "category": "A-6",
      "category_label": "翻訳調: 〜となっている 状態叙述の濫用",
      "severity": "S1",
      "scope": "span",
      "text_span": "課題となっている",
      "start": 142,
      "end": 150,
      "occurrences": null,
      "reason": "理由（密度・反復回数など根拠を明記）",
      "suggested_fix": "課題だ"
    }
  ],
  "category_summary": { "A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0, "G": 0, "H": 0, "I": 0, "J": 0 }
}
```

`scope` は taxonomy §span 表現 に従う: `span`（連続区間・start/end 必須）/ `scattered`（分散・`occurrences:[[s,e],...]`、start/end/text_span は null）/ `document`（文書全体・start/end/text_span は null、reason 冒頭に `【文書レベル】`）。文書レベルパターン（E リズム・文末単調 等）を代表位置に無理アンカーしない。

## 検出手順

1. **文体判定**: 文末を見て敬体／常体／混在を `meta.style` に記録。
2. **文単位スキャン**: A・B・D・F・G・H・I の各サブパターンを正規表現＋文脈で検出。`scope:"span"`、`start`/`end` は文字インデックス、`text_span` は当該区間の実文字列と一致することを自己検証（不一致なら JSON を出さない）。
3. **文書レベルスキャン**（`scope:"document"` または `"scattered"` で表現。代表位置への無理アンカー禁止）:
   * E（リズム）: 文長の標準偏差、文末の反復率を計算 → `scope:"document"`。
   * C（構造）: 箇条書き比率、見出し公式、絵文字、「まず・次に」連発、対句反復。絵文字・文頭接続詞の分散は `scope:"scattered"` ＋ `occurrences`。
   * J（視覚装飾）: 太字・ダッシュ・括弧補足の頻度。
4. **密度判定**: S2/S3 は**反復回数**を `reason` に明記（例「『における』が 5 回」）。単発を過検出しない。
5. **スコア算出（taxonomy §スコア正規化 SSOT に厳密準拠。独自式禁止）**:
   * `score_raw` = S1×5 + S2×2 + S3×0.5（加重和・上限なし）。
   * `severity_weighted_score` = `100 × score_raw / (score_raw + 30)`（飽和なし。`min(100,raw)` 等の切詰は不可）。`meta.score_raw` を必ず併記。
   * `ai_tell_density` = 検出 span の**和集合(union)面積** / 全体文字数（内包・重複は二重計上しない。document/scattered scope は分子に含めない）。

## 重要な原則

* **Do-NOT リスト**（数値・固有名詞・引用・法令・概念語・コード・URL）は検出対象外。
* **過検出禁止**: 人間も使う表現（「です」「こと」「という」単独）は、密度が閾値を超えたときだけ finding 化。
* `suggested_fix` は playbook に沿った最小修正案。確定ではなく推敲役への提案。
* 推敲後の再計測時は、同じ基準で残存件数を数え、過推敲シグナル（不自然な口語化・文体崩れ）も別途報告する。
