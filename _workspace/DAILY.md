# 日次ハーネス運用プロトコル

毎日 2 サンプルを生成 → 5 段パイプラインを完走 → 改善点を `IMPROVEMENTS.md` に蓄積 → 昇格した改善を適用する。
この文書だけで自律実行できるように手順を固定する。

## 1 日の手順

### Step 0 — 採番
- `python3 scripts/new_run.py` を 2 回（サンプル生成後に input を渡す）。run_id は `YYYY-MM-DD-NNN` 連番。

### Step 1 — サンプル 2 本を生成
- 下の**ジャンル・ローテーション**から、その日の 2 ジャンルを選ぶ（cycle_day = 通算実行日 mod 5、各日 2 枠）。
- 各サンプルは「いかにも AI（ChatGPT/Claude/Gemini）が書いた」**新規・典型的な日本語**（600〜1000字）。題材は毎回変える（前回と重複させない）。
- そのジャンルが狙う AI クセ（下表の「狙うクセ」）を意図的に濃く盛り込む。文体は敬体/常体どちらでも可（ジャンルに合わせる）。
- `_workspace/samples/{run_id}.txt` に保存し、`new_run.py` で `01_input.txt` 化。

### Step 2 — パイプライン完走（実サブエージェント）
1. `ai-tell-detector` ×2（並列）→ `02_detection.json`
2. `japanese-style-rewriter` ×2（並列）→ `03_rewrite.md` + `03_rewrite_diff.json`
3. `content-fidelity-auditor` ×2 ＋ `naturalness-reviewer` ×2（4 並列）→ `04_*` + `05_*`
4. オーケストレーター総合判定（SKILL.md §総合判定）:
   - fidelity 毀損 → 該当 edit のみロールバック再推敲（最大3回）
   - 変更率超過だけで fidelity=pass かつ自然度 A/B なら **override accept**（IMP-001 の既知欠陥のため）
   - `final.md` + `summary.md` 出力
- **各サブエージェントに「改善点も報告せよ」を必ず付ける**（これが改善発見の燃料）。

### Step 3 — 改善点を蓄積
- 6 エージェントの改善報告を `IMPROVEMENTS.md` に反映:
  - 既出項目は `hits` を +1（**別 run での再現**のみカウント）。
  - 新規は P0/P1/P2 で起票。
- 新パターン候補（taxonomy 未収載）は「新パターン候補」節に実例つきで追記。

### Step 4 — 昇格した改善を適用（重要 — これが「継続作業」の本体）
- `hits ≥ 2`（異なる run で再現）かつ `status: ready` の項目を **その日のうちに 1〜3 件適用**:
  - taxonomy / playbook / agent .md / スキーマを実際に編集。
  - 適用後は `status: done` ＋ 適用 run_id を記録。
  - taxonomy 改訂時は `japanese-ai-tell-taxonomist` に審査させ v1.x へ。
- 適用は小さく・1 コミット 1 改善。回帰を避けるため過去 run で軽く再検証。

### Step 5 — 日次ログ
- `_workspace/LOG.md` に 1 行追記: `YYYY-MM-DD | runs NNN,NNN | grades X,Y | new IMP n | applied IMP-xxx`。

## ジャンル・ローテーション（cycle_day = 通算日 mod 5）

| day | 枠1 ジャンル / 狙うクセ | 枠2 ジャンル / 狙うクセ |
|---|---|---|
| 0 | ビジネス/DX レポート（A翻訳調・I-4求められる・C-1段組） | SEO ライフスタイルブログ（C-5絵文字・D-1結び・C-2箇条書き） |
| 1 | 技術解説記事（B-2カタカナ・A-10抽象主語・A-5できる） | 公的文書/お知らせ（A-8受動・I-3必要がある・硬い敬語） |
| 2 | ニュース論説コラム（D-5擬人化・C-8対句・E文長均一） | EC 商品コピー（F修飾過多・D-4ハイプ・J-1太字） |
| 3 | 学術風要約（A-11名詞羅列・F-4〜的/F-5〜性・G婉曲） | メルマガ挨拶文（H接続詞多用・G-1ヘッジ・D-2誇張） |
| 4 | FAQ/ヘルプ（A-5できる・C-2箇条書き・I-1こと） | 自己啓発コーチング（D-4ハイプ・G婉曲・F-1程度副詞） |

> day 0 は 2026-06-12 に実施済み（run 001 ビジネス, 002 SEO ブログ）。次回は day 1 から。
> 5 日で taxonomy の全カテゴリを一巡。題材は毎回変えて同じ文を作らない。

## 不変条件（毎日チェック）
- 7 ファイル（01〜05 + final + summary）が両 run に揃っているか。
- fidelity 毀損を見逃していないか（A の f019 型: 接続語置換での序列混入）。
- change_rate 超過の override は summary に理由明記。
- 適用済み IMP が回帰していないか（直近 run で残存していないか）。
