# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-08-31（run 2026-08-31-001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。2026-06-12-002 は 54.6% で誤発火、001 も 47.6%。2026-08-31-001 でも箇条書き散文化(f024+f025)が difflib 削除量を押し上げ 0.337→（round2）0.375 と高止まり（語句改変は中程度・情報欠落ゼロ）。
- 出所: rewriter-A/B（001で「既知問題の再確認」明記）, naturalness-A/B（両 run）
- 提案: (a)「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を控除。(c) 挿入率を単独併記し del≫ins は中断対象外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。(e) 共通接頭辞/接尾辞をトリムした編集距離ベースを規約化（rewriter-B 2026-08-31: 「必要となります→必要です」をトリム有無で率が倍変わる）。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`

### IMP-002 severity_weighted_score の正規化が未定義で run 間非再現 `status: done(2026-08-31-001/002 で適用)` `hits: 2run`
- 症状: 正規化式が SSOT に無く、**同一サイクルで検出器2体が別式を採用**（2026-08-31: detector-001 は raw=95 をそのまま、detector-002 は raw/input_length×1000=43.9）。改善率が比較不能になる致命傷。naturalness も毎回リバースエンジニアリング。
- 出所: detector-A/B（両 run・式が食い違う実害を実証）, naturalness-A/B
- **適用(2026-08-31, v1.1)**: taxonomy §検出出力スキーマに正規化式を SSOT 固定 — `raw=S1×5+S2×2+S3×0.5` → `per1k=raw÷input_length×1000` → `severity_weighted_score=round(100×(1−exp(−per1k÷50)),1)`（飽和定数 **K=50 固定**、0〜100・100超えなし）。meta に `scoring_formula` フィールド追加。改善率の分母は推敲前 input_length に固定。detector.md §スコア算出も同式に統一（整合確認済み）。回帰検算: run001 raw95/len812→per1k117→90.4、run002 raw30/len684→per1k43.9→58.4（重い文書ほど高く、100超えなし・(raw,len)のみで一意再現）。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出`

### IMP-003 score_before のフィールド契約が曖昧 `status: ready` `hits: 2run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。スキーマ例値(71.5)と実 meta 値の混同が常態化。
- 出所: naturalness-A（両 run で meta 値の自力再現チェックを実施）
- 提案: 「score_before = 02_detection.json の meta.severity_weighted_score」と明文化し、プロンプト手渡し値と meta 値の不一致時は notes 警告を必須化。改善率の分母は推敲前 input_length に固定。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`
- 注: IMP-002 適用で式が確定したため、次サイクルで naturalness-reviewer.md への1行契約追記として適用予定。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: done(2026-08-31 で適用)` `hits: 2run`
- 症状: 絵文字分散・文末単調・C-1三段公式・E-1文長均一は分散/文書レベル。単一 start/end では広域 locator になり ai_tell_density が過大化（2026-08-31-001 で E-1 の代表 span 長により density 0.488→0.416 に手補正した実例）。
- 出所: detector-A/B（両 run で `scope` フラグを独自導入して回避）
- **適用(2026-08-31)**: findings に `scope: "span"|"scattered"|"document"` を追加。`scattered` 用 `occurrences: [[s,e],...]`。density は document スコープを除外し、重複を除いた実 AI クセ文字数ベースと定義。→ v1.1。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複・複合カテゴリのカウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリに該当。2026-08-31 では「〜が可能となります」=A-5(可能)×A-6(状態叙述)、「〜いただく必要がございます」=I-3×敬語、が 1 finding=1 category に収まらず検出器ごとにブレる。
- 出所: detector-A/B（両 run）, rewriter, fidelity（横断的に最多）
- 提案: 「1 span = 主分類 1 finding」を基本とし `merged_findings:[...]`（primary/secondary category）を許容。複合定型は SSOT に主カテゴリ裁定ルール（例: 可能×状態叙述は A-6 を主）を明記。category_summary は findings の先頭文字集計と注記。
- 影響: 全 .md のスキーマ節, `ai-tell-taxonomy.md`

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だが、本環境に detector サブ呼び出し経路が無く**2サイクル連続で手走査推定**。C-1 を S1 とみるか降格するかで grade が C↔A を跨ぐ主観リスク。
- 出所: naturalness-A/B（両 run）
- 提案: (a) オーケストレーター(SKILL)が naturalness 呼び出し前に ai-tell-detector を 03_rewrite.md に機械実行し `05_redetection.json` を生成してレビュアーに渡す2段構成。または (b) scripts/ に再走査スクリプトを用意。レビュアー定義に「サブ呼び出し不能時は推定・notes 明記」を正式フォールバックとして明文化。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`, `scripts/`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち／昇格）
- **D-7 勧誘型ブログ結び「〜してみてはいかがでしょうか」** `status: done(2026-08-31 昇格)` `hits: 2` — 「行動促し型の締め」で D-1(過去形の締め「いかがでしたでしょうか」)とは別動作。実例: 2026-06-12-002「気軽に始めてみてください」系＋2026-08-31-001「自社のシステムに取り入れてみてはいかがでしょうか」。2 run 再現で v1.1 へ昇格。出所 detector-B, detector-A。
- **A-5 多層可能形「〜することができるようになります」** `hits: 1` — 「できる＋ようになる＋ます」三重。実例 2026-08-31-001「特定することができるようになります」。A-5 に最上位サブシグネチャ注記候補。出所 detector-A。
- **A-9b「〜することによって」手段節** `hits: 1` — A-3/A-9 の隙間。実例「活用することによって」「押さえていくことによって」。出所 detector-A。
- **I-3 敬体変種「〜いただく必要がございます」** `hits: 1` — 公的文書 AI 最頻出。実例3連 2026-08-31-002。I-3 シグネチャに敬体変種追記候補。出所 detector-B。
- **I-4「望まれます／望ましいと考えられます」** `hits: 1` — 行政文書の行為者曖昧要請。実例「申請されることが望まれます」。I-4 シグネチャ拡充候補。出所 detector-B。
- **A-8 丁寧受動「される＋ております」** `hits: 1` — 「によって」を伴わない裸の受動＋状態叙述。実例「交付の対象とされております」「設定されております」。A-8 に変種追加候補。出所 detector-B。
- **C 系 redundant restatement**（叙述と箇条書きの二重記載）`hits: 1` 実例 2026-06-12-001。
- **C-9 導入誘導定型「さっそく見ていきましょう」** `hits: 1` 出所 detector-B(day0)。

### ジャンル別 Do-KEEP リスト（過検出・過推敲の両防止）`status: ready` `hits: 2run`
- **公用文レジスタ許容リスト**: 御礼／お願い申し上げます／賜る／所存でございます／につきましては／設置されている（状態受動）等は公的文書の定型として残す（E-2・I-4・A-8 の検出/除去対象外）。出所 detector-B, rewriter-B, fidelity-B, naturalness-B（2026-08-31-002 で全員が独自に保護）。
- **IT 標準カタカナ whitelist**: API/SDK/CI/CD/コンテナ/オブザーバビリティ/デプロイメント/トレーシング/ロギング 等は B-2 除外。ボトルネック/デフォルト/スケジュール等の定着一般カタカナは S3 扱い（他クセと重なる時のみ変換）。出所 detector-A, rewriter-A。
- → taxonomy/playbook に「ジャンル別保護定型」節を新設予定（次サイクル適用候補、hits 十分）。

### fidelity チェックリスト追補
- **modality 強度の順序尺度化** `status: ready` `hits: 2run` — 2値「強まったか」では緩和(必要→依頼)と強化(推奨→依頼)を同方向に見てしまう。2026-08-31-002 で `modality_scale`(0断定〜5義務)を試験導入し f011=Δ+1(唯一の強化)と定量提示。閾値契約案: |Δ|≥2 or after_level≥4 は自動 rollback、+1段は warn(人間確認)。出所 fidelity-A/B, taxonomist(day0)。
- **status の三値化 pass/warn/fail** `hits: 1` — 境界事例(f011 +1段, f018 概念精度劣化)を pass に丸めず warn で下流へ。`pass_with_concern`/`defer_to_naturalness:[...]`/`watch_edits:[{finding_id,check_id,reason}]`。出所 fidelity-A/B。
- **係助詞（も/は/こそ/さえ）新規挿入の含意検査** `hits: 1` — 「も」新規挿入は添加前提が原文にあるか(#11)必須チェック。`presupposition_source` フィールド。前提項が原文に無い「も」は f019 型密輸入。出所 fidelity-A(2026-08-31-001)。
- **entailment（含意）判定の明文化** `hits: 1` — 列挙項目数の数え上げ(「四つ」)・既出事実の再叙述は「追加」に含めない但し書き。出所 fidelity-A。
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019 型。`status: ready` `hits: 1`（day0）。
- 削除専用サブチェック（deletion-recall test）・「情報を含む削除 vs ボイラープレート削除」二分判定。出所 fidelity-B(day0)。

### playbook レシピ追補
- **C-1 三段公式は複数項の一括処理を必須**（1項だけ直すと S1 再検出）`status: ready` `hits: 2run` — 2026-08-31-001 round1 が「まず」だけ直し「次に/さらに」放置→grade C。有効レシピ:「序列副詞を消し内容語(トピック名詞)を文頭へ、既存の添加助詞『も』に並列を担わせる」。出所 rewriter-A round2, naturalness-A。
- **過短縮による文末均一化の回避**（同一縮約レシピ反復時は着地文末を分散。同一文末2-gramが3連したら1つを別相へ）`status: ready` `hits: 1` — 「できます」4連。出所 rewriter round2, naturalness-A。
- **C-2 箇条書き散文化に「本文未出情報」分岐**（各項が本文重複か個別判定、独自情報を含む項は削除禁止・必ず散文へ吸収）`status: ready` `hits: 1` — 「段階的なマイグレーション戦略」。出所 rewriter-A。
- **E-1 は「挿入」でなく「既存文の分割・体言止め」で緩急**（新規文の創作は鉄則違反）`hits: 1`。出所 rewriter-A。
- **公的文書ジャンル処方**（受動・状態叙述・形式名詞を緩めつつ硬い格は残す。他他動詞受動→自動詞化で格助詞温存: 「開始される→始まる」）`status: ready` `hits: 1`。出所 rewriter-B。
- C-5 絵文字削除後の文末吸収／D 系結びは最小着地文を残す／機能が必要な接続詞は変奏／原文が元から推量の D 系は推量保持。出所 rewriter（day0）。

### naturalness 判定の精緻化
- **文末 n-gram 反復率の定量化** `status: ready` `hits: 2run` — 定性記述どまり。指標案: `文末最頻2-gram率 = 最頻文末2-gram数/総文末数`、0.25 超で E-2 の S3、0.33 超で S2。隣接反復(twin opener)と分布反復(4連)を別指標に分離。出所 naturalness-A（両 round）, naturalness-A(day0)。
- **delta_findings スキーマ**（2次推敲の `resolved:[...]`/`introduced:[...]` を対で記録）`hits: 1` — もぐら叩き型劣化(S1潰し→twin生成)の検知。出所 naturalness-A round2。
- **grade_history + grade_confidence**（各 round の blocking finding を明示、単一 S1 律速の脆さを confidence で割引）`hits: 1`。出所 naturalness-A round2。
- 過推敲シグナル2値カウント・クラスタ系降格・E-2 到達ライン緩和・絶対残存数ガード。出所 naturalness（day0）。

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 2run`
- ルーティン・モチベーション・データドリブン・ボトルネック・デフォルト等の定訳が冗長化する語は B-2 半免責で残差 S3 固定。出所 naturalness-B, fidelity-A, naturalness-A（day0）+ rewriter-A（2026-08-31）。

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert）。出所 detector-A（両サイクル実施）。
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B。
- `repetition_counts` マップを meta/category 単位に持たせ reason は参照のみ。出所 detector-A。
- category_label の正典対応表を SSOT に。出所 detector-A。
