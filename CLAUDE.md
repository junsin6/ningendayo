# 人間だよ (Ningen da yo) — AI 日本語クセ除去ハーネス

## プロジェクト概要

AI（ChatGPT・Claude・Gemini など）が書いた日本語テキストを「人間が書いた文章のように」推敲する 5 人パイプラインハーネス。翻訳調・カタカナ語過多・機械的並列・AI 常套句・過剰なヘッジング・接続詞の多用・です/ます単調・絵文字/箇条書き濫用など 10 大カテゴリ 40+ の AI クセを検出・分類し、**内容は一字も変えずに**文体・リズム・表現だけ再作成する。

検出（detector）・推敲（rewriter）・内容監査（fidelity auditor）・自然度検証（naturalness reviewer）を分離したエージェントで実行し、A〜J の 10 分類・S1〜S3 の深刻度・span 単位の出力スキーマで一貫管理する。

## 鉄則

1. **意味不変 (Fidelity First)** — 事実・主張・数値・固有名詞・引用は 100% 原文保存。
2. **根拠ベース (Span-Grounded)** — すべての変更は検出 finding に紐づく。検出のない区間は触らない。
3. **文体維持 (Tone Match)** — 敬体／常体を変えない。コラムを文学に、レポートをエッセイに移さない。
4. **過推敲禁止 (No Over-Polish)** — 変更率 30% 超で警告、50% 超で強制中断。

## ディレクトリ構造

```
ningendayo/
├── CLAUDE.md                      # 本ファイル — プロジェクトガイド
├── README.md
├── .claude/
│   ├── agents/                    # 6 人エージェント定義
│   │   ├── japanese-ai-tell-taxonomist.md
│   │   ├── ai-tell-detector.md
│   │   ├── japanese-style-rewriter.md
│   │   ├── content-fidelity-auditor.md
│   │   ├── naturalness-reviewer.md
│   │   └── humanize-web-architect.md
│   └── skills/humanize-japanese/
│       ├── SKILL.md               # オーケストレーター
│       └── references/
│           ├── ai-tell-taxonomy.md     # SSOT — 10 大分類 × 40+ パターン
│           ├── rewriting-playbook.md   # カテゴリ別置換レシピ
│           └── web-service-spec.md     # Phase 5 Web 拡張用
├── scripts/
│   └── new_run.py                 # run_id 付き _workspace ディレクトリ生成
└── _workspace/                    # ランタイム成果物（run_id 別）
    └── {YYYY-MM-DD-NNN}/
        ├── 01_input.txt
        ├── 02_detection.json
        ├── 03_rewrite.md
        ├── 03_rewrite_diff.json
        ├── 04_fidelity_audit.json
        ├── 05_naturalness_review.json
        ├── final.md
        └── summary.md
```

## パイプライン

```
入力テキスト
    ↓
[ai-tell-detector] — 検出 (span・category・severity・suggested_fix)
    ↓
[japanese-style-rewriter] — 推敲 (finding ベースの手術的修正)
    ↓
[並列チーム]
    ├─ [content-fidelity-auditor] — 意味等価性監査（14 項）
    └─ [naturalness-reviewer]     — 残存 + 過推敲の判定
    ↓
[オーケストレーター総合判定]
    ├─ accept → final.md + summary.md
    ├─ rewrite_round_2 → 推敲役を再呼び出し（最大 3 回）
    ├─ rollback_and_rewrite → 問題 edit をロールバック
    └─ hold_and_report → 人間レビューを推奨
```

## 5 人コアチーム（+ Web アーキテクト拡張）

1. **japanese-ai-tell-taxonomist** — 分類体系 SSOT 管理。実戦で見つかった未分類パターンを審査し v1→v1.1 へ昇格。
2. **ai-tell-detector** — 検出器。span 単位 JSON レポート生成。文書レベルパターン（リズム・構造）も含む。
3. **japanese-style-rewriter** — 推敲役。finding ベースの手術的再作成。変更率を監視。
4. **content-fidelity-auditor** — 内容監査官。14 項チェックリストで意味毀損を検出 → ロールバック指示。
5. **naturalness-reviewer** — 自然度レビュアー。検出器を再実行し残存・過推敲を計測。品質等級判定。
6. **humanize-web-architect**（拡張用）— Web サービス要求時に Next.js 15 + Vercel アーキテクチャを設計。

## 深刻度の基準

* **S1 決定的**: 一度出ただけで AI と確信させるパターン。無条件除去。
* **S2 強い**: 1〜2 回許容、3 回+ 反復で除去。
* **S3 弱い**: 他パターンと重なるときのみ問題。

## 品質等級

* **A**: S1 0 件, S2 2 件以下, score 改善 70%+
* **B**: S1 0 件, S2 4 件以下, score 改善 50%+
* **C**: S1 1〜2 件 or 過推敲シグナル 2 個 — 2 次推敲
* **D**: S1 3 件以上 or 深刻な過推敲 — 人間レビュー

## 使い方

1. このフォルダ内で Claude Code を起動。
2. オーケストレータースキルをトリガー:
   ```
   この AI 文を自然に推敲して：
   （テキストを貼り付け）
   ```
3. オーケストレーターが run_id を生成し 5 段パイプラインを実行。
4. 結果 `final.md` + `summary.md` を返す。

## 主要な禁忌

* 数値・単位・日付の変更禁止。
* 固有名詞・製品名・モデル名の変更禁止。
* 鉤括弧「」内の引用文の変更禁止。
* 法令条文・学術概念語の任意置換禁止。
* 文体（敬体／常体）の変更禁止。
* 新しい主張・事実・例の追加禁止。
* 原文にあった情報の欠落禁止。

## 日本語版で特に注意する固有パターン

日本語ならではの強い AI クセ:

* **A-6** 「〜となっている」状態叙述の濫用
* **B-2** カタカナ語の濫用（レバレッジ・シームレス 等）
* **E-2** です・ます／だ・である体の単調反復
* **I-4** 「〜が求められる」行為者を曖昧にした要請
* **J-3** ダッシュ（—）の濫用
* **D-1** ブログ AI 特有の「いかがでしたでしょうか」

## 拡張ポイント

* **Web サービス化**: `humanize-web-architect` 呼び出し → `_workspace/web/` 成果物。
* **多言語拡張**: 中国語などへ拡張時は言語別 taxonomy 分離ファイルを追加。
* **ジャンル拡張**: 現在 4 ジャンル（コラム・レポート・ブログ・公的文書）。学術論文・法律文書・製品コピー追加可能。

## 参考

* 分類体系: `.claude/skills/humanize-japanese/references/ai-tell-taxonomy.md`
* 推敲処方: `.claude/skills/humanize-japanese/references/rewriting-playbook.md`
* Web 仕様: `.claude/skills/humanize-japanese/references/web-service-spec.md`
