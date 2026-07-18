# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数（別 run での再現のみ +1）。

最終更新: 2026-07-18（run 001 技術解説記事, 002 公的文書）

---

## ✅ 適用済み（DONE）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done` `hits: 2run` 適用: 2026-07-18-001/002
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・カタカナ短縮・純削除で機械的に膨張。2026-06-12 Sample B 54.6%・A 47.6%、**2026-07-18 run 001 は 30.5%（deleted 172 / inserted 41 の削除主導）で警告閾値超過も意味改変ゼロ**で再現。
- 出所: rewriter-A(06-12), rewriter-B(06-12), naturalness-B(06-12), rewriter-001(07-18), naturalness-001(07-18)
- **適用内容**: `rewriting-playbook.md §変更率の数え方` に `insertion_ratio = inserted/(inserted+deleted)` を導入。change_rate×insertion_ratio のマトリクスで中断可否を判定（削除主導 <0.35 は 30〜50% でも続行可、fidelity=pass で override accept）。`SKILL.md §総合判定` に override accept 行を追加。deleted/inserted の分離計上を diff.json meta に必須化。
- 影響ファイル: `rewriting-playbook.md`, `SKILL.md`
- 残課題: 「編集距離」でなく「意味単位（文節）改変率」への置換は将来課題。現状は insertion_ratio 併用で運用回避。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2run` 適用: 2026-07-18-001/002
- 症状: 正規化式が SSOT に無く `min(100, raw)` クランプ運用。高密度短文で raw が即 100 付近に張り付き解像度が消える。2026-07-18 は detector-001（raw=87）・detector-002（raw=34）の両者が「式が無く逆算・長さ非正規化」を再指摘。
- 出所: detector-A(06-12), detector-B(06-12), detector-001(07-18), detector-002(07-18)
- **適用内容**: taxonomy §スコア算出に `severity_weighted_score = round(100*(1-exp(-raw/K)),1)`, K=60 を確定。`raw_weighted_sum`・`scoring_weights` を meta 明示フィールド化。`ai-tell-detector.md §スコア算出` も追随。
- 影響: `ai-tell-taxonomy.md`, `ai-tell-detector.md`

### IMP-003 score_before のフィールド契約が曖昧 `status: done` `hits: 2run` 適用: 2026-07-18-001/002
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。2026-07-18 naturalness-001 が「scoring_weights が meta に無く findings 構成から逆算、reviewer 間でぶれる」と再指摘。
- 出所: naturalness-A(06-12), naturalness-001(07-18)
- **適用内容**: `naturalness-reviewer.md §処理` に「score_before = 02_detection.json の meta.severity_weighted_score、scoring_weights も同 meta を参照」を明文化。taxonomy にも `scoring_weights` フィールドを追加（IMP-002 と一体）。今回の 2 run は本ルールで運用済み。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: done` `hits: 2run` 適用: 2026-07-18-001/002
- 症状: E-2 文末単調・E-1 文長均一・H-1 接続詞は文書/分散パターン。単一 start/end では広域 locator になり density 過大。2026-07-18 は detector-001・detector-002・rewriter-001・naturalness-001 が横断的に「文書レベル finding の start/end 未規定」を再指摘。
- 出所: detector-B(06-12), detector-A(06-12), detector-001/002・rewriter-001・naturalness-001(07-18)
- **適用内容**: finding スキーマに `span_type`(contiguous/scattered/document) と `occurrences: [[s,e],…]` を追加。document/scattered は density 分子から除外。`ai-tell-detector.md` も追随。
- 影響: `ai-tell-taxonomy.md`, `ai-tell-detector.md`

---

## P1 — 仕様の穴（未適用）

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリに該当（I-4＋B-2＋I-1 / A-5＋A-10 / B-2＋F-5「リアルタイム性」等）。edits/findings が 1:1 前提で category_summary が実態を過小評価。2026-07-18 は detector-001（pt3）・detector-002（pt6）・fidelity-001（finding_id とパターン型のラベル混線）が再現。
- 出所: detector-A・rewriter-A・rewriter-B・naturalness-A・fidelity-A(06-12), detector-001・detector-002・fidelity-001(07-18)
- 提案: 「1 span = 主分類 1 finding、最深刻カテゴリ優先」を基本とし、`merged_categories: [...]` 配列を許容。`finding_id` と「パターン型（型ラベル）」を別フィールド管理（fidelity-001 提案）。category_summary は「findings の主 category を集計」と注記。
- 影響: 全 .md のスキーマ節。**次回適用候補（hits=2 到達）**。

### IMP-006 naturalness-reviewer が検出器を独立起動せず基準ドリフト `status: ready` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だがレビュアーは自前で再走査 → 走査主体が推敲前 detector と異なり微妙な基準ドリフト。2026-07-18 naturalness-001 が「別プロセスで detector を回す二重化」を再提案。
- 出所: naturalness-A(06-12), naturalness-001(07-18)
- 提案: naturalness-reviewer が `ai-tell-detector` をサブエージェントとして実起動し 05 に detector 出力 JSON を添付。手動再走査を補助線に留める。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`。**次回適用候補（hits=2 到達）**。IMP-003 の適用で score_before 契約は解決済みだが、再走査の主体二重化は未適用。

---

## P2 — 分類・レシピ・チェックリスト

### 新カテゴリ候補（taxonomist 審査中 — 2026-07-18 提出）
- **候補 K「メタ言及・進行実況」** `hits: 1`（run 001）: (a)読者ラベリング呼びかけ「初心者の方にもわかりやすく解説していきます」、(b)開始宣言形「〜していきます」。人間の書き手は自分で「わかりやすく」と宣言しない。C-6（見出し直後の案内文）・D-2（意義の誇張）・D-6（結び公式）の鏡像（冒頭版）との差分を要吟味。出所 detector-001。**追加実例待ち（再現2run で昇格）**。
- **候補 K「過剰・冗長敬語（★日本語固有）」** `hits: 1`（run 002）: 「賜りますよう」×2・「お願い申し上げます」×3・「させていただきます」×2・「におかれましては」×2 の密度・入れ子。設計思想の4本柱に「過剰な丁寧体・敬語」とあるのに本文で未形式化。判定基準案「同一依頼型3回以上反復 or 要請の入れ子3段以上。単発の正統敬語は AI クセでない」。出所 detector-002。naturalness-002 の逆方向シグナル（正統敬語削減による格崩れ）と対。**追加実例待ち**。

### taxonomy 拡張候補（v1.0→ 未昇格, 06-12 由来）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。`hits: 1` 出所 detector-A(06-12)。
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「〜してみてはいかがでしょうか」。`hits: 1` 出所 detector-B(06-12)。※ 07-18 run 001 でも「検討してみてはいかがでしょうか」出現（D-1 で処理済）だが結び公式としては別題材のため hits 据え置き。
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式。`hits: 1` 出所 detector-B(06-12)。

### 分類拡張候補（A-8 受動の定義拡張, 07-18）
- **A-8b 行為者省略受動（agentless passive）** `hits: 1`（run 002）: A-8 は「〜によって行為者後置」だが、公的文書 AI は「改善が図られる／拡充が実現される／見直される／移行される」と**行為者を完全に消した受動**を多用。by-phrase 無しで A-8 の狭い定義から漏れる。出所 detector-002。**追加実例待ち**。

### fidelity チェックリスト追補
- **#14 程度・強調表現の保存** 「非常に→（削除）」等の程度副詞削除が 13 項のどれにも正面から当たらない。`status: ready` `hits: 2run`（fidelity-A 06-12 の #14 接続語序列 と同じ「新規 #14 枠」要求、fidelity-001 07-18 が程度副詞で再要求）出所 fidelity-A・fidelity-001。※ 06-12 の「#14 接続語/順序語の置換で序列付与」と 07-18 の「#14 程度副詞」は別項目。番号衝突するため #14 序列・#16 程度副詞 と採番し直して次回適用予定。
- **#15 modality 方向性（強化/弱化）とジャンル整合** 可能表現→断定・ヘッジ→断定・義務→依頼の階段。公的文書で義務→依頼の弱化を可視化する軸が無い。`status: ready` `hits: 2run` 出所 fidelity-A(06-12 modality 順序尺度化), fidelity-001・fidelity-002(07-18)。**次回適用候補**。
- **#17 条件節・適用範囲・適用時点の保存（who/when/if）** 「一部の利用者」「〜の場合がございます」「移行完了後」の条件トリガ＋対象範囲。公的文書で最重要だが check6/check5 に分散。`status: ready` `hits: 1`（fidelity-002 07-18、新規）。
- **12b 専門語の抽象度変化** architecture→仕組み・real-time→即時性は別義でなく上位語化。0/1 でなく「別義/軽度一般化/等価」の3段階。`hits: 1` 出所 fidelity-001(07-18)。
- **削除専用サブチェック（deletion-recall test）** `hits: 1` 出所 fidelity-B(06-12)。
- 「情報を含む削除 vs ボイラープレート削除」二分判定。出所 fidelity-B(06-12)。
- #5論理関係 と #11情報追加 の責任境界を一意化。出所 fidelity-A(06-12)。責任境界（命題の真偽=fidelity / 強調度=naturalness）の明文化を fidelity-001(07-18) が補強。

### playbook レシピ追補
- **公的文書ジャンルでは体言止めを避け依頼形/条件形/能動短文で E-2 変奏** `status: ready` `hits: 1`（rewriter-002・naturalness-002 07-18、2agent 収束）。体言止めは公的通知の格を崩す。**次回適用候補（ジャンル分岐追記）**。
- **正統な非人称受動（移行される・設置されている）は温存、AI 冗長受動（図られる・実現される）のみ能動化** `hits: 1` 出所 rewriter-002(07-18)。A-8 処方にジャンル別線引きを追加。
- **公的文書の H-1 削除率を緩和**（また/なお がトピック転換標識のとき温存）。`hits: 1` 出所 rewriter-002・naturalness-002(07-18)。
- **ジャンル別 change_rate 期待レンジ**（公的文書 10〜25% 等）を summary 判定に持たせ過推敲/不足の誤判定を防ぐ。`hits: 1` 出所 rewriter-002(07-18)。
- **B-2 維持カタカナ・ホワイトリストの SSOT 化**（アプリケーション vs インフラストラクチャ の線引きが属人的）。`status: ready` `hits: 2run` 出所 naturalness-B(06-12 定着カタカナ半免責), detector-001・rewriter-001(07-18)。**次回適用候補**。
- **C-5 絵文字削除後の文末吸収ルール** 出所 rewriter-B(06-12)。
- **D 系結びは「最小着地文を残す」** 出所 rewriter-B・naturalness-B(06-12)。07-18 run 001「いかがでしょうか→検討してみてください」は着地文を残す好例。
- **機能が必要な接続詞は削除でなく変奏** 出所 rewriter-A(06-12)。
- **原文が元から推量の D 系は推量を保持** 出所 rewriter-A(06-12)。
- **E-1 は「既存文の分割による短文化のみ許可・新規命題挿入は禁止」と明文化**（内容追加禁止と衝突）。`hits: 1` 出所 rewriter-001(07-18)。
- **検出器 suggested_fix の格助詞整合**（f003「向上します」が他動詞構文と不整合）／推敲役に整合調整権限を明記。`hits: 1` 出所 rewriter-001(07-18)。

### naturalness 判定の精緻化
- **構造的残存（structural_residual）マーク** E-1/E-2 のように意味不変・文体維持の制約下で推敲単独では解消不能な finding を通常残存と区別。grade を不当に下げず 2次推敲の無駄打ちを防ぐ。`status: ready` `hits: 2run` 出所 naturalness-A/B(06-12 の E-2 到達可能ライン緩和 と同趣旨), naturalness-001(07-18)。**次回適用候補**。
- **改善率と絶対残存の二重ゲート化** 低ベース文書で改善率が伸びず A 落ち、高ベースで改善率水増しの両方向の穴。`status: ready` `hits: 2run` 出所 naturalness-A(06-12 絶対残存ガード), naturalness-002(07-18)。**次回適用候補**。
- **CJK-PUB-1 正統敬語削減による格崩れ（過推敲・逆方向シグナル）** `hits: 1` 出所 naturalness-002(07-18)。
- **CJK-PUB-2 ジャンル不適な文末変奏**（公的文書への体言止め・口語終止の混入を過推敲検出）`hits: 1` 出所 naturalness-002(07-18)。
- **E-2 の定型挨拶除外ルール**（冒頭/末尾の「お願い申し上げます」等を E-2 反復カウントから除外 or S2→S3 降格）。`hits: 1` 出所 naturalness-002(07-18)。
- **H-1 閾値のジャンル別化**（公的文書は また/なお 定型接続をホワイトリスト化）。`hits: 1` 出所 naturalness-002(07-18)。
- 過推敲シグナルの定量化（敬体/常体混入の二値カウント）。出所 naturalness-A(06-12)。
- クラスタ系 finding のクラスタ崩壊時 severity 降格。出所 naturalness-A(06-12)。
- **可能形「〜ようになります」系**（本 run 残存「検索できるようになります」）を A-5 派生として審査提案。`hits: 1` 出所 naturalness-001(07-18)。

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert）。出所 detector-A(06-12)。**07-18 は両 detector が自己検証を実施（部分定着）**。
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B(06-12)。
- **B-2 判定境界の付録リスト化（技術記事ジャンル別 維持/除去）** `hits: 1` 出所 detector-001(07-18)。playbook B-2 SSOT 化（上記）と統合予定。
- **E-1 判定の数値閾値**（pstdev<8 かつ 70% が 40〜60字 等）。`hits: 1` 出所 detector-002(07-18)。
