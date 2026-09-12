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
5. **スコア算出**（taxonomy v1.2 SSOT 準拠）:
   * `raw` = S1×5 + S2×2 + S3×0.5。`meta.severity_weighted_raw` に併記してよい（検算用）。
   * `severity_weighted_score` = `min(100, round(raw / input_length * 500, 1))`。分母 `input_length` は改行込みの原文全文字数。必ずこの式を使い、`meta.score_formula` に式文字列を書く。
   * ⚠ 係数 500 は暫定（IMP-002b OPEN）。score の絶対値ではなく、同一係数内の相対比較（推敲前後の改善率）に用いる。
   * `ai_tell_density` = 検出 span 総文字数 / 全体文字数。**span は非重複**で数え、複合表現は分割して各カテゴリへ割り当てる。
6. **スキーマ規約**（v1.1）:
   * finding に `scope`（`"span"` 既定 / `"document"`）を付す。文書横断（E/C/リズム系）は `scope:"document"` とし、代表 `start/end` に加え `occurrences:[[s,e],...]` を列挙してよい。
   * 「1 span = 主分類 1 finding」。複数カテゴリ該当は従属分類を `merged_findings:[...]` へ。`category_summary` は主分類のみ集計。
   * `suggested_fix` は `meta.style`（敬体/常体）に合わせた文体で生成する（敬体入力に常体の fix を出さない）。
   * start/end 自己検証: regex マッチ位置と `text_span` が原文と一致することを assert し、不一致なら JSON を出さない。

## 重要な原則

* **Do-NOT リスト**（数値・固有名詞・引用・法令・概念語・コード・URL）は検出対象外。
* **過検出禁止**: 人間も使う表現（「です」「こと」「という」単独）は、密度が閾値を超えたときだけ finding 化。
* `suggested_fix` は playbook に沿った最小修正案。確定ではなく推敲役への提案。
* 推敲後の再計測時は、同じ基準で残存件数を数え、過推敲シグナル（不自然な口語化・文体崩れ）も別途報告する。
