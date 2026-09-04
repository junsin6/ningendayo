# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数（別 run での再現のみ +1）。

最終更新: 2026-09-04（run 001 技術解説, 002 公的文書）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。001(0.336)・002(0.316) とも 30% 超だが fidelity=pass・自然度 A/B で override accept。高 AI クセ密度の定型文では意味不変でも churn が構造的に 30% 超。
- 出所: rewriter-A, rewriter-B, naturalness-A, naturalness-B（2 run 再現）
- **適用（2026-09-04-001/002）**: `rewriting-playbook.md §変更率の数え方` を v2 化 — `change_rate`（総）／`語句改変率`（意味担う置換・過推敲主指標）／`構造削除率`（ボイラープレート純削除）／`挿入率` を分離計上（`meta.change_rate_breakdown` 必須）。判定は総変更率でなく**語句改変率**（15% 超で警告・30% 超で中断）。`SKILL.md §3推敲` と `§総合判定` に **override accept** 行を追加（総変更率 30% 超でも fidelity=pass かつ A/B なら accept・summary に理由明記）。過推敲シグナルを「真性 vs 警告性(change_rate)」に二層化し等級 C 発火は真性のみで数える旨も明記。
- 残タスク: 推敲役 .md 側の breakdown 算出手順の明文化（現状は各 rewriter が meta に自主記録）。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2run`
- 症状: 正規化式が SSOT に無く、検出器ごとに式を自作 → run 間・推敲前後でスコア比較が破綻。本日は detector-A が 69.4（式 `min(100,raw/len*500)`）、detector-B が 60.4（式 `min(100,raw/len*1000)`）と**同じハーネスで別式**を採用し不整合が実証された。
- 出所: detector-A, detector-B, naturalness-A, naturalness-B（2 run 再現）
- **適用（2026-09-04-001/002）**: `ai-tell-taxonomy.md §検出出力スキーマ` を v1.1 化 — `severity_weighted_score = round(100*(1-exp(-(raw/input_length*100)/8)),1)`（K=8・文書長非依存・飽和しにくい）を確定。`severity_weighted_raw` 併記と `meta.score_formula` 記録を必須化。`ai-tell-detector.md §スコア算出` も同式に更新。
- 検証: 001 raw126/len908→82.4、002 raw41.5/len687→53.0（妥当なレンジ・比較可能）。

### IMP-003 score_before のフィールド契約が曖昧 `status: ready` `hits: 1run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。
- 出所: naturalness-A（2026-06-12）
- 経過: 2026-09-04 は両レビュアーとも `score_before = 02_detection.json meta.severity_weighted_score` を使用（001=69.4, 002=60.4）。運用では固定できているが SSOT 明文化は未実施。
- 提案: `naturalness-reviewer.md` に「score_before = 02_detection.json の meta.severity_weighted_score」を明記。IMP-002 適用で分母固定も解決済み。

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: done` `hits: 2run`
- 症状: 絵文字分散・文末単調・I-3/A-2 反復は分散パターン。単一 start/end では広域 locator にせざるを得ず density 過大化、反復の全 span を推敲役が取りこぼす。
- 出所: detector-A, detector-B, rewriter-B(A-2 反復), naturalness-B（2 run 再現）
- **適用（2026-09-04-001/002）**: `ai-tell-taxonomy.md` v1.1 で finding に `scope`(contiguous/scattered/document) と `occurrences: [[s,e],…]` を追加。反復（3 回以上）は 1 finding に潰さず全 occurrence 列挙。`ai_tell_density` を「重複・広域 locator 除外の実カバー文字集合」に再定義。`ai-tell-detector.md` に scope 付与手順を追加。

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリ該当（I-4＋B-2＋I-1／A-5＋A-10／D-4＋G-1＋A-8）。edits/findings が 1:1 前提で category_summary が過小評価。fidelity 側でも複合クセの「濃さ」が可視化されない。rewriter は入れ子 finding を 1 edit で解決せざるを得ず finding_id 対応が崩れる。
- 出所: detector-A/B, rewriter-A, fidelity-A/B, naturalness（2 run 再現・横断的に最多）
- 提案: `1 span = 主分類 1 finding` を基本に `secondary_categories: []`（複合タグ）と rewrite 側 `covers: [finding_ids]` を正式採用。category_summary は主分類先頭文字で集計と注記。IMP-004 の scope 追加で一部緩和したが「多重カテゴリ」は未対応。**次回適用候補（P0/P1 の適用一巡後）**。

### IMP-006 naturalness-reviewer が検出器を実呼び出しできず score_after が擬似再走査 `status: ready` `hits: 2run`
- 症状: 仕様は「検出器をサブエージェントとして再実行」だが、サブエージェントからサブエージェントを spawn する経路が無く、レビュアーが taxonomy 式を自分で再適用する形（before への手動照合ではないが厳密な別エージェント spawn でもない）。2026-09-04 の両レビュアーが構造的に同じ制約に到達。
- 出所: naturalness-A, naturalness-B（2 run 再現）
- 提案: **オーケストレーターが naturalness-reviewer の前段で `ai-tell-detector` を再走査ステップとして回し、`05_detection_after.json` を生成して渡す**設計に変更（IMP-006 を構造的に保証）。`SKILL.md §4並列検証` と `naturalness-reviewer.md §処理` を改訂。**次回適用候補**。

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち／2026-09-04 審査反映）
- **新カテゴリ K「過剰・古語的敬語」**（★日本語固有・公的文書特有）。実例: 「ご賢察のうえ」「賜り」×2・「御礼申し上げます」・「申し上げます」×3・「ございます」×6（run 002）。慣用敬語（残す: 御礼申し上げます）と過剰敬語（削る: ご賢察のうえ）の線引き表＋「反復・密度が閾値超のときのみ finding 化」の但し書きが必須。`hits: 1` 出所 detector-B, rewriter-B。→ taxonomist 審査。
- **A-6b「〜ようになる／できるようになる」到達点化**。実例:「集中することができるようになります」「対応していくことができるようになります」（run 001）。英語 come to be able to の直訳。A-6 サブ昇格候補。`hits: 1` 出所 detector-A。
- **「〜していく／ていく」進行アスペクトの濫用**。実例:「解説していきます」「推進していく」「対応していく」「活用していく」（run 001, 4回）。E/F 系サブ候補。`hits: 1` 出所 detector-A。
- **A-8 拡張: 行為者秘匿の無標受動**（実施される・図られ・なされ・変更される）。`hits: 1` 出所 detector-B → **taxonomist が A-8 に補足追記（適用済み 2026-09-04）**。
- **A-6 シグネチャに「こととなる／こととなっております」系を追記**（run 002・S1 相当・3回反復）。`hits: 1` 出所 detector-B → **taxonomist が A-6 に追記（適用済み 2026-09-04）**。
- **C 系 redundant restatement**（叙述と箇条書きの二重記載）実例 001(6/12)。`hits: 1` 出所 detector-A。
- **D-7 ブログ結び呼びかけ公式**（今回は〜ご紹介しました 等）。`hits: 1` 出所 detector-B。
- **C-9 導入誘導定型**（さっそく見ていきましょう）。`hits: 1` 出所 detector-B。

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値・論理型が新規付与されていないか** `status: ready` `hits: 2run`。f019（並列→基盤の序列混入・6/12）に続き f021「これにより→この方式なら」（帰結連結→条件連結の型変換・9/4）で再現。→ 独立項「連結表現の論理型（因果/条件/手段/逆接/並列）保存」として昇格し implicature 混入を専用チェック。**次回適用候補**。出所 fidelity-A×2run。
- **削除専用サブチェック（deletion-recall test）** `status: ready` `hits: 2run`。削除 span ごとに「読者が知り得なくなる事実」を逐一問う。9/4 fidelity-B が「移動による残存」（ご理解の移動）追跡の必要性を追加報告。→ 削除 span 内の固有名詞/数値/条件語を正規表現抽出し推敲文（移動先含む）に残存するか機械照合。出所 fidelity-B×2run。
- **modality 強度を順序尺度化** `status: ready` `hits: 2run`。義務系〔義務>要請>依頼>推奨〕・確信系〔断定>蓋然>推量>可能〕を順序尺度で定義し edit ごとに段階移動を記録、文書全体の義務/確信トーンの系統的変質を合算監視。9/4 f013(推量→断定+1)・f009-012(要請→依頼-1) で再現。出所 fidelity-A(6/12), fidelity-B(9/4)。
- **行為主体付与チェック（受動→能動）** `hits: 1`。(a)付与主体が文書名義から一意確定するか (b)原文が主体秘匿を意図した外交的表現でないか の 2 段判定を項 9 サブ基準に。出所 fidelity-B。
- **統治チェック（項0）: 全 edit の finding_id が 02_detection.json に実在するか** `hits: 1`。非 span-grounded 編集（f007b 橋渡し）を fidelity が検出できない盲点。出所 fidelity-A。
- **binary verdict に第三状態 pass_with_watch** `hits: 1`。境界事例（f021）を「全ロールバック or 無言 pass」の二択に追い込まない。出所 fidelity-A。
- 「情報を含む削除 vs ボイラープレート削除」二分判定・#5論理関係/#11情報追加の責任境界一意化。出所 fidelity-A/B。

### playbook レシピ追補
- **playbook↔taxonomy 矛盾: F-1 指定 fix「欠かせない」が D-4 ハイプ語リストに載る** `status: ready` `hits: 1`（矛盾自体は即修正可能）。両文書で扱いを統一。出所 naturalness-A。
- **A-5/A-6 一括修正後は E-2 を必ず再チェック** `hits: 1`。001 で A-5「することができる」5例を一律「できます」化し「集中できます/最適化できます/…」と 6 文中 5 文連続＝E-2 を新規発生（S2 残存）。カテゴリ一律置換が別クセを生む連鎖を playbook が警告すべき。出所 naturalness-A。
- **I-3 反復解消の依頼形バリエーション表** `hits: 1`。playbook I-3 は「→すべきだ」一択で 4 連発時の分散指針が無く、suggested_fix も全部「ください」系で「ください」4 連発の新単調を生む。依頼形表（ください・お願いします・願います・くださいますよう）を追加。出所 rewriter-B。
- **公的文書ジャンルの Do/Don't** `hits: 1`。能動化・断定化しても敬体の格を落とさない下限ライン（「配慮しています」可・「配慮してるよ」不可）、依頼・お詫び・挨拶の慣用敬語は温存。出所 rewriter-B。
- **suggested_fix は語形方向のみ示し、敬体/常体は rewriter が meta.style に強制整合** `hits: 1`。f003/f010/f033 の suggested が常体で文体維持と衝突。出所 rewriter-A。
- **表題文脈では体言止め可**（「最適化について→最適化」）、**C-6 はメタ定型のみ除去し範囲情報は保持**、**近接 span で同一訳語を避ける分散指示**（俊敏性/スピーディー→すばやく 2連回避）。出所 rewriter-A。
- **C-5 絵文字削除後の文末/区切り吸収ルール**・**D 系結びは最小着地文を残す**・**機能する接続詞（しかしながら）は削除でなく変奏**・**原文が元から推量の D 系は推量を保持**。出所 rewriter-A/B, naturalness-B（6/12）。

### naturalness 判定の精緻化
- **過推敲シグナルの定量化** `status: ready` `hits: 1run(2agent)`。「同一文末語が 3 連続、または同一文末型が全文末の 40% 超 → E-2 過推敲フラグ」等の決定的しきい値。真性シグナル（意味希薄化・ぶつ切り・文体崩れ・敬語不足・E-2 再単調）と警告性シグナル（change_rate 30-50%）の二層化。→ **二層化は SKILL に一部反映済み（IMP-001 適用）**、E-2 しきい値の数値化は未。出所 naturalness-A, naturalness-B。
- **公的文書ジャンル別 grade 基準** `hits: 1`。敬語レジスター保持スコア（下限）を A/B 必須条件に追加し、`honorific_deficiency` 検出時は改善率に関わらず最大 B 止まり。検出指標: 文末敬体率／冒頭末尾の慣用敬語存置本数／能動化 edit で丁寧補助が欠落した件数。出所 naturalness-B。
- クラスタ系 finding のクラスタ崩壊時 severity 降格・E-2 到達可能ライン緩和（体言止め1箇所で合格）・絶対残存数ガード（S1 が1件でも C 以下）。出所 naturalness-A/B（6/12）。

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 1run(3agent)`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B, fidelity-A, naturalness-A（6/12）。

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert）。9/4 detector-B が実施し全 span 一致を確認。出所 detector-A/B。
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B。
