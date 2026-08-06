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
      "scope": "span",
      "start": 142,
      "end": 150,
      "occurrences": [[142, 150]],
      "co_located_with": [],
      "reason": "理由（密度・反復回数など根拠を明記）",
      "suggested_fix": "課題だ"
    }
  ],
  "category_summary": { "A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0, "G": 0, "H": 0, "I": 0, "J": 0, "K": 0 }
}
```

* `scope`: `"span"`（連続1区間）/ `"scattered"`（同一パターンが散在）/ `"document"`（文長均一・文末単調など連続 span を持たない文書レベル現象）。（IMP-004）
* `occurrences`: 同一 finding が支配する全出現の `[start,end]` 配列。scattered/document で必須、span でも冗長に併記可。推敲役はこの配列で全出現を機械的に手術する。（IMP-004）
* `co_located_with`: 同一の連続文字列に同居する別 finding の id 配列（例 A-8＋A-6 複合）。ロールバックは finding 単位でなく**セグメント（連続書き換え領域）単位**で行う。（IMP-005）
* **アンカー規約（IMP-007）**: `text_span` を唯一の正規アンカーとする。`start`/`end`/`occurrences` は補助情報。後段（推敲役・監査官）は offset ではなく text_span 文字列で照合すること。

## 検出手順

1. **文体判定**: 文末を見て敬体／常体／混在を `meta.style` に記録。
2. **文単位スキャン**: A・B・D・F・G・H・I の各サブパターンを正規表現＋文脈で検出。`start`/`end` は文字インデックス。
3. **文書レベルスキャン**:
   * E（リズム）: 文長の標準偏差、文末の反復率を計算。
   * C（構造）: 箇条書き比率、見出し公式、絵文字、「まず・次に」連発、対句反復。
   * J（視覚装飾）: 太字・ダッシュ・括弧補足の頻度。
4. **密度判定**: S2/S3 は**反復回数**を `reason` に明記（例「『における』が 5 回」）。単発を過検出しない。集約 vs 個別は「一意な span 文字列 = 主分類 1 finding、reason に回数」を原則とする（IMP-005）。
5. **スコア算出**（IMP-002 で正規化式を確定）:
   * `raw_weighted` = S1×5 + S2×2 + S3×0.5（finding 数ベース、集約 finding は 1 件で数える）。
   * `severity_weighted_score` = **`min(100, raw_weighted / input_length * 1000)`**（per-1000字加重、K=1000・上限100固定）。文長非依存の比較のため分母は必ず `input_length`。
   * `ai_tell_density` = 検出 span 実文字数 / 全体文字数。ただし `scope:"document"` の finding と重複領域は **de-dup**（二重計上しない）。（IMP-004）
6. **自己検証ゲート（必須・IMP-007）**: JSON を出す前に全 finding で以下を assert し、1 つでも失敗したら JSON を出さず修正する:
   * `source[start:end] == text_span`（全 span スライス突合）。
   * `len(body) == meta.input_length`（本文実長と一致。改行・タイトル行を数えるか統一）。
   * `category_summary` の各値 = findings の category 先頭文字の集計と一致。
   * span 同士の物理重複が無いか検査（重複は `co_located_with` で明示）。

## 重要な原則

* **Do-NOT リスト**（数値・固有名詞・引用・法令・概念語・コード・URL）は検出対象外。
* **過検出禁止**: 人間も使う表現（「です」「こと」「という」単独）は、密度が閾値を超えたときだけ finding 化。
* `suggested_fix` は playbook に沿った最小修正案。確定ではなく推敲役への提案。
* 推敲後の再計測時は、同じ基準で残存件数を数え、過推敲シグナル（不自然な口語化・文体崩れ）も別途報告する。
