# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。
`hits` = これまでに指摘した **run 数**（同一 run 内の複数エージェント指摘は 1 run 扱い）。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。

最終更新: 2026-07-24（run 001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除・体言止め化・文接合で機械的に膨張。2026-06-12 B は 54.6%、2026-07-24-001 は 37.9%（del 27.5%≫ins 10.4%）で警告閾値超過だが fidelity=pass・自然度 A。いずれも override accept で処理。
- 出所: rewriter-A/B, naturalness-A/B（day0）＋ rewriter-A, naturalness-A（day1・2026-07-24-001）
- 提案: (a)「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を控除。(c) 挿入率を単独併記し del≫ins の削除主導ケースを中断対象から除外。(d) 50% 中断は「意味改変 edit 比率」基準に置換。(e) 分母を「本文のみ／改行含む」で確定。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`
- 備考: 2 run で再現し ready 継続。次回以降の最優先適用候補（層別 change_rate 指標の実装）。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done (2026-07-24 v1.1)` `hits: 2run`
- 症状: 正規化式が SSOT に無く、検出器ごとに式が割れる。2026-07-24 は detector-A が `100×raw/(raw+50)`=69.7、detector-B が raw クリップ=56.0 と**同日別 run で不整合が再現**。
- 出所: detector-A, detector-B（day0・day1 両方）
- 適用: taxonomy v1.1 で `severity_weighted_score = round(100×raw/(raw+50), 1)`（raw=S1×5+S2×2+S3×0.5, k=50）＋ density=union に確定。detector.md のスコア算出節も同期。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出`

### IMP-003 score_before のフィールド契約が曖昧 `status: done (2026-07-24)` `hits: 2run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。day0 でスキーマ例 71.5 と実値 92.5 がぶれた。
- 出所: naturalness-A（day0）＋ naturalness-A/B（day1 は両者とも meta.severity_weighted_score を採用し慣行が固まった）
- 適用: `naturalness-reviewer.md` に「score_before = 02_detection.json の meta.severity_weighted_score をそのまま採用。score_after は同一正規化式で再走査」を明記。
- 影響: `naturalness-reviewer.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: done (2026-07-24 v1.1)` `hits: 2run`
- 症状: 絵文字散在・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にせざるを得ず ai_tell_density が過大化。day1 でも E-2・C 構造で両検出器が再指摘。
- 出所: detector-A/B（day0・day1 両方）
- 適用: taxonomy v1.1 で `span_type: "contiguous"|"scattered"|"document"` ＋ scattered 用 `occurrences: [[s,e],...]` を追加。density は union で定義（IMP-002 と整合）。detector.md schema 例も同期。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリに該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。day1 は rewriter-A が入れ子 finding（f002⊃f003⊃f004 等）の diff 二重計上を再指摘。
- 出所: detector-A, rewriter-A/B, naturalness-A, fidelity-A（day0）＋ rewriter-A（day1）
- 提案: 「1 span = 主分類 1 finding」を基本とし `merged_findings: [...]` を許容。diff スキーマに `primary/subsumed` フラグを持たせ一次責任を追跡。category_summary は findings の category 先頭文字を集計と注記。
- 影響: 全 .md のスキーマ節, `03_rewrite_diff.json` スキーマ

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だが実際は手動照合 → 数値が推定。day1 も naturalness-A が detector サブエージェントを再起動せず人力再走査した（S2/S3 境界で評価者揺らぎ）。
- 出所: naturalness-A（day0・day1）
- 提案: `ai-tell-detector` をサブエージェントとして機械再実行し差分 finding を数える経路を必須化（手動照合禁止）。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

### IMP-007 fidelity-mandated retention が grade を不当に押し下げる `status: candidate` `hits: 1run`
- 症状: B-1 初出併記（RAG/LLM）・保存必須モデル名など fidelity が正当化する残存が residual S2 にカウントされ grade を下げる。2026-07-24-001 は raw S2=3（機械適用なら B）だが effective S2=1（A 相当）と乖離。
- 出所: naturalness-A（day1）
- 提案: grade 式を `not_applied`／fidelity-mandated retention と突き合わせ、控除後の **effective severity** で判定。絶対残存の下限ゲート（effective S1=0 かつ effective S2≤2 を必須）も明示化。
- 影響: `naturalness-reviewer.md §品質等級`, `SKILL.md §品質等級`

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち・v1.1 拡張候補欄に登録済み）
- **過剰敬語・冗長定型 ★日本語固有**（公的文書）: 「賜りますようお願い申し上げます」の反復・二重敬語・させていただく連鎖。taxonomy 設計思想は「過剰敬語」を4大重心の一つと明言するのに A〜J に対応分類が無い。実例 2026-07-24-002。 `hits: 1` 出所 detector-B, fidelity-B, naturalness-B → **要 2run 再現で新カテゴリ K もしくは A-14 として本採用審査**
- **A-8 行為者不在受動サブパターン**: 「業務が停止されます」等 by 行為者なしの受動過多（密度 S2）。現 A-8 は「〜によって」限定で取りこぼす。実例 2026-07-24-002。 `hits: 1` 出所 detector-B, naturalness-B
- **enable 直訳「〜を可能にする/実現する」**: 抽象主語＋enable 直訳。A-5 と A-10 の中間。実例 2026-07-24-001「取得することを可能にします」。 `hits: 1` 出所 detector-A, rewriter-A
- **誇張タイトル語「徹底解説/完全ガイド/〜のすべて」**: 解説/SEO 記事タイトルのハイプ。D-4 追記候補。実例 2026-07-24-001。 `hits: 1` 出所 detector-A
- **C-9 導入自己言及ナビ**「本記事では〜わかりやすく解説していきます」「さっそく見ていきましょう」式。 `hits: 2`（day0 detector-B「さっそく見ていきましょう」＋ day1 detector-A「本記事では〜解説していきます」で異 run 再現） 出所 detector-B（day0）, detector-A（day1） → **昇格条件充足。次回 taxonomy 本採用候補**
- **D-7 ブログ結び呼びかけ公式**「今回は〜ご紹介しました」「〜してみてはいかがでしょうか」。 `hits: 1` 出所 detector-B（day0）

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** `status: ready` `hits: 2run`。day1 で f026「ており→ため」の「潜在因果の顕在化 vs 新規付与」の判定境界が未定義と再指摘。二分基準（元節が連用中止/並列で因果に読めるか）を #14 本文へ明記すべき。出所 fidelity-A（day0・day1）
- **削除専用サブチェック（deletion-recall test）** `status: ready` `hits: 2run`。day1 は fidelity-A/B とも 30/104 字削除の高速確定に寄与し有効性を実証。出所 fidelity-A/B（day0・day1）
- **modality 強度を順序尺度化（要請/推奨/義務/必須）** `status: ready` `hits: 2run`。day1 で fidelity-A（f024/f028/f036）・fidelity-B（f011）が「等価とみなす段差の閾値」不在を再指摘。±1 段は pass・逆転や 2 段以上は fail を fidelity 仕様へ確定すべき。出所 fidelity-A（day0）, fidelity-A/B（day1）
- **公的文書の三つ組（受益者×期限×行為）を1単位とする突合サブチェック** `status: candidate` `hits: 1`。条件の部分欠落（期限だけ残り対象資料が抜ける）を機械検知。出所 fidelity-B（day1）
- **受動→能動が禁忌となるケース（受益者主語構文）の明文化** `status: candidate` `hits: 1`。f006「延長されます」の受動保持を評価する項が #9 内に埋没。出所 fidelity-B（day1）
- 「情報を含む削除 vs ボイラープレート削除」二分判定（day0）／ #5論理関係 と #11情報追加 の責任境界一意化（day0）。

### playbook レシピ追補
- **A-10 に enable/achieve 直訳の変換行を追加**（「抽象主語＋可能にする/実現する → 行為者へ、または可能動詞へ」）。現 playbook の A-10 例は「示している」型のみ。 `hits: 1` 出所 rewriter-A（day1）
- **B-2 技術ドメイン別の許容カタカナ語ホワイトリスト**（レイテンシ・インデックス・アルゴリズム・データソース等は開けない標準語、スケーラビリティ→拡張性・ソリューション→製品 は開ける）。「一語で定訳が確立し情報損失なく開けるか」を境界基準に明文化。 `status: ready` `hits: 2run` 出所 naturalness-B, fidelity-A, naturalness-A（day0）＋ detector-A, rewriter-A（day1）
- **公用文の敬語簡素化ルール**「同一定型が3回以上反復した場合のみ簡素化、末尾一箇所は最上位敬語を保持」。過削り防止。 `hits: 1` 出所 rewriter-B, naturalness-B（day1）
- **suggested_fix は文体非依存の骨子**であり推敲役が meta.style に合わせて敬体/常体を適合させる、と処方に明記（検出器の常体 fix と敬体維持鉄則の衝突回避）。 `hits: 1` 出所 rewriter-A（day1）
- C-5 絵文字削除後の文末吸収ルール／D 系結びは最小着地文を残す／機能が必要な接続詞は変奏／原文が元から推量の D 系は推量保持（day0・いずれも継続）。

### naturalness 判定の精緻化
- 過推敲シグナルの定量化（敬体/常体比・体言止め率 vs 閾値20%・平均文長変化率）。day1 で naturalness-A/B とも定性2値では borderline の再現性が出ないと再指摘。 `status: ready` `hits: 2run` 出所 naturalness-A（day0）, naturalness-A/B（day1）
- 公的文書ジャンルの過推敲閾値（敬語定型の保持下限・断定文末〜します の近接連続上限）。 `hits: 1` 出所 naturalness-B（day1）
- 絶対残存数ガードを grade 表に組込み（改善率が高くても effective S1 が1件でも C 以下）。day0・day1 継続。 `status: ready`
- クラスタ系 finding のクラスタ崩壊時 severity 降格／E-2 到達ライン緩和（体言止め1箇所以上で合格）。（day0）

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 2run`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。day1 の技術標準語免責（レイテンシ等）と統合し「許容カタカナ語ホワイトリスト」として playbook 追補へ合流。出所 naturalness-B/fidelity-A/naturalness-A（day0）＋ detector-A/rewriter-A（day1）

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert）。day0・day1 とも全検出で mismatch 0 を達成（有効・継続運用）。
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。（day0）
- **category_label 生成テンプレートの正規化**（プレフィックス・記号の統一）。検出器間で表記揺れ。 `hits: 1` 出所 detector-A（day1）
- **A-2 敬体変種（につきまして/つきましても）と A-5 複合形（〜が可能となる）のシグネチャ追記**。正規表現ベースの取りこぼし防止。 `hits: 1` 出所 detector-B（day1）
