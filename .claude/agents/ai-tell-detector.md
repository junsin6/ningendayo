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
    "raw_weighted_sum": 0.0,
    "severity_weighted_score": 0.0,
    "severity_breakdown": { "S1": 0, "S2": 0, "S3": 0 },
    "ai_tell_density": 0.0,
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
      "reason": "理由（密度・反復回数など根拠を明記）",
      "suggested_fix": "課題だ"
    }
  ],
  "category_summary": { "A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0, "G": 0, "H": 0, "I": 0, "J": 0 }
}
```

反復・列挙パターン（cluster）は次のように全メンバー座標を張る:

```json
{ "id": "f018", "category": "C-1", "severity": "S1", "scope": "cluster",
  "text_span": "まず、", "start": 470, "end": 473,
  "occurrences": [[470, 473], [536, 539], [594, 598]],
  "reason": "「まず・次に・最後に」3段公式。列挙全メンバーを occurrences に張る", "suggested_fix": "順序語を全廃し対等な並列を保つ" }
```

## 検出手順

1. **文体判定**: 文末を見て敬体／常体／混在を `meta.style` に記録。
2. **文単位スキャン**: A・B・D・F・G・H・I の各サブパターンを正規表現＋文脈で検出。`start`/`end` は文字インデックス。
3. **文書レベルスキャン**:
   * E（リズム）: 文長の標準偏差、文末の反復率を計算。
   * C（構造）: 箇条書き比率、見出し公式、絵文字、「まず・次に」連発、対句反復。
   * J（視覚装飾）: 太字・ダッシュ・括弧補足の頻度。
4. **密度判定**: S2/S3 は**反復回数**を `reason` に明記（例「『における』が 5 回」）。単発を過検出しない。
5. **cluster/document 発行規則（IMP-007 — 必須）**: 反復・列挙パターン（C-1/C-2/C-7/C-8/E-1/E-2/F-4/F-5/H-1/H-2/I-5 等、reason が複数座標を根拠に挙げるもの）は、代表 anchor を1点に留めず `scope:"cluster"` とし **`occurrences` に全メンバーの座標を張る**。文書全体に散在するリズム/構造パターンは `scope:"document"`。これを怠ると span 厳守の推敲役が先頭要素しか処理できず、残りが宙吊りになり残存 S1 → 不要な 2 次推敲を生む。
6. **スコア算出**:
   * `raw_weighted_sum` = S1×5 + S2×2 + S3×0.5（生加重和）。
   * `severity_weighted_score` = `100 × (1 − exp(−raw_weighted_sum / (0.06 × max(input_length, 200))))`（長さ正規化。IMP-002。飽和しない）。
   * `severity_breakdown` = S1/S2/S3 の内訳件数。
   * `ai_tell_density` = 検出 span 座標レンジの**和集合（重複除去）**の総文字数 / 全体文字数。document スコープは非算入。
   * `start`/`end` は自己検証（`text[start:end] == text_span` を assert。不一致なら JSON を出さない）。

## 重要な原則

* **Do-NOT リスト**（数値・固有名詞・引用・法令・概念語・コード・URL）は検出対象外。
* **過検出禁止**: 人間も使う表現（「です」「こと」「という」単独）は、密度が閾値を超えたときだけ finding 化。
* `suggested_fix` は playbook に沿った最小修正案。確定ではなく推敲役への提案。
* 推敲後の再計測時は、同じ基準で残存件数を数え、過推敲シグナル（不自然な口語化・文体崩れ）も別途報告する。
