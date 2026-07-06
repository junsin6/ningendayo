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
      "span_type": "contiguous",
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
5. **span_type の付与**（IMP-004, v1.1）:
   * `contiguous`（既定・省略可）: 連続した 1 区間。`start`/`end` が実文字列と一致すること（自己検証必須・不一致なら JSON を出さない）。
   * `scattered`: 同一クセが複数箇所に散在（絵文字・文末反復の個別出現など）。`occurrences: [[s,e],...]` に全出現を列挙し、`start`/`end` は先頭出現に置く。
   * `document`: 文書全体の統計量（E リズム・C 構造など）。代表 anchor に `start`/`end` を置き、`reason` に文書レベルの根拠を書く。**density 計算からは locator 相当分を除外**する。
6. **スコア算出**（IMP-002, v1.1 で確定）:
   * `W`（加重和）= S1×5 + S2×2 + S3×0.5。**span_type:"document" の locator は W に一度だけ計上**（反復回数で水増ししない）。
   * `severity_weighted_score = round(100 × (1 − exp(−W / K)), 1)`、**K = 40 固定**。飽和関数により高密度短文でも 100 に張り付かず解像度を保ち、文書長に依存しない。
   * `ai_tell_density` = 検出 span 総文字数（重複・document locator を除く実クセ文字数）/ input_length。
   * `input_length` の分母は「タイトルを含む本文・末尾改行除外」で統一。

## 重要な原則

* **Do-NOT リスト**（数値・固有名詞・引用・法令・概念語・コード・URL）は検出対象外。
* **過検出禁止**: 人間も使う表現（「です」「こと」「という」単独）は、密度が閾値を超えたときだけ finding 化。
* `suggested_fix` は playbook に沿った最小修正案。確定ではなく推敲役への提案。
* 推敲後の再計測時は、同じ基準で残存件数を数え、過推敲シグナル（不自然な口語化・文体崩れ）も別途報告する。
