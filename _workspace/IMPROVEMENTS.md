# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-09-11（run 2026-09-11-001, -002）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 3run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で機械的に膨張。2026-06-12 Sample B は 54.6% で `hold_and_report` 誤発火（実際は fidelity=pass / 自然度 A）。
- 再現: 2026-09-11-001 rewriter（構造改変なしの純語句手術は 0.237、構造ありの前 run 0.476 と同一指標でも意味が別）・2026-09-11-002 rewriter（削除優位 削除112/挿入26 で change_rate が「健全な減量」を過大計上）。
- 提案: (a) 「語句改変率」と「構造/削除率」を分離計上。(b) 装飾・常套句の純削除分を控除。(c) 挿入率を単独併記し del≫ins は中断対象外。(d) 構造編集フラグの有無で閾値を切替（構造ありは 45%/60%）。(e) 50% 中断は「意味改変 edit 比率」基準へ。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`

### IMP-002 severity_weighted_score の正規化が未定義で run 間非互換 `status: done(2026-09-11)` `hits: 3run`
- 症状: 正規化式が SSOT に無く、検出器ごとに別式を発明。2026-09-11-001 は raw をそのまま（min-cap）score=61、2026-09-11-002 は指数飽和 100·(1−e^(−raw/41))=69.7。前 run は raw106→92.5。**同一 raw が run 間で別値**になり improvement_rate の横断比較が無意味化。
- 再現: detector-001, detector-002, naturalness-001, naturalness-002（2 run×計4 agent）。
- **適用（2026-09-11）**: 実測 4 点（92.5 / ~71.5 / 69.7）に整合する指数飽和式 `severity_weighted_score = round(100·(1−exp(−raw/41)), 1)`（`raw = 5·S1 + 2·S2 + 0.5·S3`）を SSOT に確定。before/after は同一 run 内で同一関数を必須化。taxonomy v1.1・`ai-tell-detector.md §スコア算出` に明記。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出`

### IMP-003 score_before のフィールド契約が曖昧 `status: done(2026-09-11)` `hits: 2run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定（スキーマ例 71.5 vs 実 severity_weighted_score）。
- 再現: naturalness-A(06-12), naturalness-002(09-11 で「score_before=69.7 は正規化値・score_after=0.5 は素和で単位不一致」と再指摘)。
- **適用（2026-09-11）**: 「score_before = 02_detection.json の meta.severity_weighted_score」「score_after も同一正規化関数（IMP-002）を通す」を `naturalness-reviewer.md` に明文化。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: ready` `hits: 2run`
- 症状: 絵文字分散・文末単調・まず…最後に は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
- 再現: detector-B(06-12), detector-001(09-11 で E-2・C 系・密度型は文書全体指摘で単一 start/end を持てず代表 span を無理に当てたと再指摘)。
- 提案: `span_type: "contiguous"|"scattered"|"document"` と scattered 用 `occurrences: [[s,e],...]`。`scope:"span"|"document"` 欄と文書型 `metrics`（文長 SD・文末反復率）。density は重複・locator を除いた実 AI クセ文字数ベース。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1／A-5＋A-6 可能となる 等）に該当。edits/findings が 1:1 前提で category_summary が実態を過小評価。ai_tell_density が重複文字を二重計上。
- 再現: detector-A ほか5 agent(06-12), detector-001・detector-002・fidelity-002(09-11)。
- 提案: 「1 span = 主分類 1 finding」を基本とし `secondary_categories: [...]` を許容。密度計算は非重複併合。入れ子構文は主カテゴリ1件＋従を reason 併記。
- 影響: 全 .md のスキーマ節

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: done(2026-09-11)` `hits: 3run`
- 症状: 仕様は「検出器を同基準で再走査」だが、**本 SDK 実行環境には検出器を spawn する Agent/Task ツールが存在せず**（naturalness サブエージェントからは呼べない）、レビュアーが手動再走査するほかない。
- 再現: naturalness-A(06-12 推定値と自認), naturalness-001・naturalness-002(09-11 で「Agent/Task 系ツール不在で実走査不能」と 2 run 連続で明示)。
- **適用（2026-09-11）**: `naturalness-reviewer.md §処理` に「Agent ツールで検出器を再走査。**呼べない実行環境では同一 SSOT・同一正規化での手動再走査で確定し、その旨を notes に必ず明記**」というフォールバックを正式化。恒久解として「検出器の決定論スクリプト化（Bash から呼べる経路）」を別途 P1 に起票（IMP-013）。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

### IMP-007 A-8 受動の定義が by-passive に限定され「行為者を欠く受身の連鎖」を取りこぼす `status: ready` `hits: 1run(3agent)`
- 症状: SSOT の A-8 は「〜によって」型のみ定義・例示。公用文 AI の本体である行為者なし受身（設置されている／開始される／停止される／徴収される）が定義外。2026-09-11-002 で 4 連鎖出現、detector が f007 reason で「分類の穴」と自認して暫定計上。
- 再現: detector-002, rewriter-002, naturalness-002（同一 run 3 agent。別 run 再現待ちで昇格保留 → 拡張候補欄に A-8b として登録済み）。
- 提案: A-8 を「受動態の濫用（by-passive ＋ 行為者を欠く受身の 3 回以上連鎖）」へ拡張、または A-8b を新設。playbook に「行為者を出せない公用文脈での格を保った自動詞化（停止される→停止する／始まる）」レシピを追加。
- 影響: `ai-tell-taxonomy.md A-8`, `rewriting-playbook.md B/A-8`

### IMP-008 公用文ジャンルの「許容定型」allow-list が無い `status: ready` `hits: 1run(2agent)`
- 症状: 公用文には A/E/I パターンに形態一致するが正統で除去禁止の定型が密集（運びとなりました／賜り／御礼申し上げます／お願い申し上げます（結語1回）／につきましては／場合がございます／ご了承ください）。現状は detector が reason に都度手書き免責で属人的・非再現。
- 再現: detector-002, naturalness-002（同一 run 2 agent。公用文 run で必ず再発の見込み）。
- 提案: `references/` にジャンル別 allow-list（公用文）を新設。①単発は許容 ②同一依頼定型が N 回（例3回）反復で初めて finding、の反復閾値ルールを明文化（P2「定着カタカナ語免責」の公用文版）。
- 影響: 新規 `references/genre-allowlist.md`, `ai-tell-detector.md`

---

## P2 — 分類・レシピ・チェックリスト

### IMP-009 軽動詞「行う／実施する」による水増しの独立カテゴリが無い `status: candidate` `hits: 1run(2agent)`
- 症状: 「操作を行う→操作する」「交付申請を行う→申請する」「手続きを行う→手続きする」の名詞化＋水増しが公用文 AI で頻出だが A〜J に該当なし。finding に紐づかず「根拠ベース」原則に抵触したまま推敲する矛盾。
- 再現: detector-002, rewriter-002（2026-09-11-002）。
- 提案: F 群または I 群に「軽動詞水増し [S2]」を新設（F-6 or I-6）。検出・レシピ・スキーマに載せる。

### IMP-010 同一トークンの部分置換の取り残し（表記ゆれ）を拾う経路が無い `status: ready` `hits: 1run(2agent)`
- 症状: 「検出のない区間は触らない」を厳守すると、finding のある語（テクノロジー→技術）を開いた結果、別位置の同一語（未 finding）が残り表記ゆれが発生。2026-09-11-001 で line3 技術／line11 テクノロジーの混在が残存 S2 に。
- 再現: rewriter-001（grey-zone と自認）, naturalness-001（残存 S2 として検出、要 final 前補完）。
- 提案: (a) detector が同一トークン全出現を `occurrences[]` で 1 finding に束ねる、または (b) rewriter に「finding 語と字面同一の未検出出現は一貫適用してよい」surgical 例外を明記。(c) naturalness-reviewer 処理に「表記ゆれ検査」を追加し rollback ではなく「取り残し補完」を促す。
- 影響: `ai-tell-detector.md`, `rewriting-playbook.md`, `naturalness-reviewer.md`
- 注: 本 run では orchestrator が round-2 で line11 を補完済み（暫定対処）。

### IMP-011 detector の suggested_fix が span を超えて技術語破壊・情報改変しうる `status: ready` `hits: 1run(2agent)`
- 症状: f009 の fix「アーキテクチャ→構成」（技術語破壊＋直前文と重複）、f015 の narrowing 誘発「リソース→処理能力」。I-1/B-2 の最小手術が目的なのに fix が禁忌（技術用語不変）と衝突。
- 再現: rewriter-001（f009 の fix を退けた）, fidelity-001（f015 を #12 で rollback、f009 退けを適切と評価）。
- 提案: taxonomy/playbook に「suggested_fix は finding 種別の最小手術に限定、CLAUDE.md 禁忌と衝突する fix を出さない」規約。rewriter は fix を無批判採用しない前提を明記。

### IMP-012 residual_findings が件数のみでオーケストレーター/推敲役に残存 span が渡らない `status: ready` `hits: 2run`
- 症状: `naturalness-reviewer.md` の出力例は `{S1,S2,S3}` の数だけ。`rewrite_round_2` を指示してもどの span が残ったかが伝わらない。両 run でレビュアーが自主的に `residual_detail` 配列を付けており実質標準化済み。
- 再現: naturalness-001, naturalness-002（2 run 再現）。
- 提案: residual を `residual_detail: [{category, severity, text_span, note}]` として正式化（IMP-004 のレビュアー出力版）。
- 影響: `naturalness-reviewer.md §出力`

### IMP-013 検出器がサブエージェント前提のため本 SDK 環境で再走査不能（恒久解） `status: ready` `hits: 2run`
- 症状: IMP-006 の根治。naturalness から検出器を spawn できないため、決定論的な検出ロジックを Bash 実行可能なスクリプト（`scripts/detect.py` 等）として切り出す必要。
- 再現: naturalness-001, naturalness-002。
- 提案: 正規表現ベースのコア検出（A-1/A-5/A-6/D-1/I-3 等の決定的パターン）を `scripts/` にスクリプト化し、レビュアーは Bash で呼ぶ。文脈依存の密度判定はエージェント側で補正。

### fidelity チェックリスト追補 `status: ready`
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか**（f019 型・06-12 で起票）。`hits: 2run`（09-11 f015 も「スタイル系カテゴリ作業に寄生した毀損」で同型と fidelity-001 が指摘）。
- **#12 概念整合サブ手順**: カタカナ語→和語変換時、和語が原語より狭義・広義になっていないか外延を照合（f015 narrowing を「別義ではないが狭義」で取りこぼした）。出所 fidelity-001。`hits: 1run`
- **#10 情報欠落 と #12 概念改変 の帰属ルール**: 概念の広狭変化は #12 を主 fail とする、と注記。出所 fidelity-001。
- **#5 因果「ので／から」の句点分割の許容境界**: 残差の並置が原因の一意な復元を許すか検査、多義なら毀損。出所 fidelity-002。
- **#9 行為者含意の変化**: 受身→自動詞/能動で「原文が意図的にぼかした行為者を確定させていないか」（責任所在）。出所 fidelity-002。
- **modality 強度の順序尺度化**: 推量（かもしれない＜だろう/でしょう＜はずだ＜に違いない＜断定）を reference 化し「±1段まで許容」。出所 fidelity-001, fidelity-A。
- **削除専用サブチェック（deletion-recall）／情報 vs ボイラープレート二分判定**（06-12 起票・継続）。

### playbook レシピ追補 `status: ready`
- **I-3 の公用文分岐**: 敬体・依頼文脈では「ください」へ、真の必須要件は「必要があります」を残す（一律「すべきだ」は公用文の格を壊す）。出所 rewriter-002, fidelity-002。`hits: 1run`
- **E-2 結語ポジションの単発は保持可**、反復のみ除去（公用文の結語格式）。出所 rewriter-002, naturalness-002。
- **E-2 変奏の目標分布/閾値**（同一文末は連続2文まで／文書内3回まで 等）を明記し rewriter と reviewer が同一物差しに。出所 rewriter-001。
- **分散推敲（レシピ3）と surgical 原則の適用境界**を明文化（同一語反復では正面衝突。IMP-010 参照）。出所 rewriter-001。
- C-5 絵文字削除後の文末吸収／D 系「最小着地文を残す」／機能が必要な接続詞は変奏／原文が元推量の D 系は保持（06-12 起票・継続）。

### naturalness 判定の精緻化 `status: ready`
- **短文（<800字）は改善率要件を緩め、絶対残存（S1=0,S2≤N）主導で判定**（09-11-002 は 638字で 1 finding の増減が改善率を 0.964〜0.993 に振らす）。出所 naturalness-002。既存「絶対残存数ガード」の公用文短文版。
- **改善による S2→S3 降格ルール**を成文化（決定的シグネチャ除去＋密度閾値以下で降格可）。降格運用の有無で等級が B/A に変わる。出所 naturalness-001, naturalness-002。
- **公用文の格式保持チェック**（結語敬度・冒頭挨拶の有無・敬語定型の残存下限）を over_polish_signals に追加。依頼定型の消しすぎ＝格式喪失を検出。出所 naturalness-002。
- 過推敲シグナルの深刻度差（文体崩れ=重 vs 軽い口語化=軽）を区別。出所 naturalness-001。
- クラスタ系 finding のクラスタ崩壊時 severity 降格（06-12 起票・継続）。

### スキーマ実装追補 `status: ready`
- **diff の finding_id 重複**（E-2 等の分散適用で f014 が2エントリ）→ サブ id（f014a/f014b）または `spans[]`/`edit_group` を付与し rollback 一意特定を可能に。出所 rewriter-002, fidelity-002。`hits: 1run`
- **category_label の SSOT registry 化**（カテゴリコード→正準ラベル、手打ちドリフト防止）。出所 detector-001。
- **オフセット基準の固定**: 「0-based code-point index into `01_input.txt` as-is（改行含む）」と一句で明記。出所 detector-001。
- **検出器出口の整合性バリデータ**（sum(category_summary)==detected_count／text_span==input[start:end]／id 連番一意）。出所 detector-001。
- **B-2 維持/変換のカタカナ語彙リスト**を SSOT 付属で保守（アーキテクチャ/デバイス/クラウド/ハイブリッド の in/out がブレる）。出所 detector-001。

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 1run(3agent)`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B, fidelity-A, naturalness-A（06-12）。

---

## 新パターン候補（taxonomist 審査待ち）

- **A-8b 行為者を欠く受身の連鎖** [S2 候補] — 「設置されている／開始される／停止される／徴収される」等 by 句のない受身が 3 回以上連鎖。★公用文で最頻出。実例（2026-09-11-002）: 4 件。別 run 再現で A-8 サブへ昇格。出所 detector-002, rewriter-002, naturalness-002。
- **軽動詞「行う」水増し** [S2 候補] — 「操作を行う→操作する」。実例（002）: 操作を行う／交付申請を行う／手続きを行う。出所 detector-002, rewriter-002。
- **定義提示の定型「〜とは、〜のことです／のことを指します」** — AI 解説記事の冒頭定義に高頻度。実例（001）: 「…アーキテクチャのことを指します」。出所 detector-001。
- **SEO 見出し公式「〜とは？その仕組みと〜をわかりやすく解説」** — AI ブログ記事タイトルの決定的定型。実例（001）: タイトル行。C-3/見出し公式候補。出所 detector-001。
- **オープニング定型「近年、〜が（大きな）注目を集めています」** — D-4 ハイプ寄りの導入常套句。実例（001）: 「近年、IoT の普及にともない…大きな注目を集めています」。出所 detector-001。
- **C 系 redundant restatement** 叙述と箇条書きの二重記載。実例: 001(06-12)。出所 detector-A。
- **D-7 ブログ結び呼びかけ公式**「今回は〜ご紹介しました」等。実例2件で条件充足。出所 detector-B（06-12）。
- **C-9 導入誘導定型**「さっそく見ていきましょう」式。出所 detector-B（06-12）。
