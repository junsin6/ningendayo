# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数（別 run での再現のみカウント）。

最終更新: 2026-07-28（run 001 サーバーレス技術解説, 002 断水お知らせ）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: ready` `hits: 2run`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・絵文字/結びの純削除で膨張。加えて **LCS 法だと語順入替・文分割（意味等価な再配置）が削除+挿入として二重計上**され、良質な構造改修ほど過推敲警告に近づく逆インセンティブが働く。
- 出所: rewriter-A, rewriter-B, naturalness-B（run 2026-06-12）; **rewriter-001（LCS で文分割 f021/f022 が 27.3% までインフレ）, rewriter-002（run 2026-07-28）で再現**
- 進展: 両 run の推敲役が自発的に **substitution_rate / insertion_rate / deletion_rate を分離計上**して緩和（001: 置換0.19/挿入0.08、002: 語句改変0.18/削除0.013）。実運用では機能しているが SSOT 未記載。
- 提案: (a) 「語句改変率」「挿入率」「削除率」を分離計上を **playbook §変更率の数え方に正式化**。(b) 「意味等価な再配置（文分割・語順入替）」を割引く指標を併記。(c) 50% 中断は「意味改変 edit 比率」基準に置換。(d) fidelity=pass かつ自然度 A/B なら change_rate 超過でも override accept（DAILY 既定）を SKILL.md に明文化。
- 影響ファイル: `rewriting-playbook.md §変更率の数え方`, `japanese-style-rewriter.md`, `SKILL.md §総合判定`

### IMP-002 severity_weighted_score の正規化が未定義で detector 間で不整合 `status: done`（適用 2026-07-28-001/002, v1.1）
- 症状: 正規化式が SSOT に無く、detector ごとに解釈が割れた。**run 2026-07-28 では detector-001 が `min(100,raw)` キャップ法（→92.0）、detector-002 が `raw/length*1000` 線形法（→67.2）と別式を採用**し、横比較不能を実証。高密度短文で raw が即 100 付近に飽和し深刻度の解像度が消える問題も継続。
- 出所: detector-A, detector-B（run 2026-06-12）; **detector-001, detector-002（run 2026-07-28）で別式採用を実証**
- 適用内容: taxonomy §検出出力スキーマに **長さ正規化＋非飽和式**を明記 → `raw=Σweight(S1=5,S2=2,S3=0.5)`, `density_weighted=raw/input_length*1000`, `severity_weighted_score=round(100*(1-exp(-density_weighted/40)),1)`。K=40 はスキーマ例（length1820→71.5）に整合。次 run から有効（今日の run 成果物は本欠陥の証拠であり ad-hoc 式のまま）。
- 影響: `ai-tell-taxonomy.md §検出出力スキーマ`, `ai-tell-detector.md §スコア算出`

### IMP-003 score_before のフィールド契約が曖昧 `status: ready` `hits: 1run`
- 症状: naturalness-reviewer がどの値を score_before にするか未固定。
- 進展: run 2026-07-28 はオーケストレーターが「score_before = 02_detection.json の meta.severity_weighted_score」を明示指定して回避。**運用慣行としては機能したが .md 未記載**。
- 提案: 「score_before = 02_detection.json の meta.severity_weighted_score」を明文化。IMP-002 適用で数値が安定するため併せて記載推奨。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

### IMP-007 多出現パターンの単一アンカー finding 化バグ（round2 往復の直接原因）`status: ready` `hits: 1run(4agent)`
- 症状: 検出器が同一パターンの複数出現を **1 finding にまとめアンカー span 以外に独立 finding を張らない**ため、推敲役がアンカーだけ直し非アンカー出現が未修正で残る。**run 001 が grade C→round2 を要した根本原因**。実例: (a) A-2「について」が見出し(f001)＋本文「この点については」の 2 回だが finding は見出しのみ → 本文残存 r002。(b) A-5「することができ」を 5 箇所直しながら同一文の別出現「集中することができ」を取りこぼし → r001。
- 出所: naturalness-001（round1 で発見）, naturalness-001（round2 再確認）, fidelity-001（round2）, rewriter-001（round2）
- 提案: 検出器は反復パターンを **occurrence 単位で個別 finding 化**、または finding に `occurrences: [[s,e],...]` を必須化。推敲役・レビュアーは「reason に第2出現が書かれているのに finding が1つ」の不整合を検知したら全出現をカバー対象へ昇格。**→ IMP-004 の `occurrences[]` 追加で構造的に緩和済み（2026-07-28）**。別 run で再現したら本項単独で done 化。
- 影響: `ai-tell-detector.md`, `japanese-style-rewriter.md`, `ai-tell-taxonomy.md §スキーマ`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: done`（適用 2026-07-28, v1.1）
- 症状: E-1 文長分散・E-2 文末単調・C 群構造は「点」でなく文書全域の測定なのに、スキーマが `text_span/start/end` を必須にするため代表位置へ無理にアンカーし、実際の tell でない位置が ai_tell_density にノイズを混ぜる。絵文字散在・文末単調も同型。
- 出所: detector-B, detector-A（run 2026-06-12）; **detector-001, detector-002, naturalness-001, naturalness-002（run 2026-07-28）で再現**
- 適用内容: スキーマに `scope: "span"|"scattered"|"document"` を追加。`document`/`scattered` は start/end を任意化し、`scattered` は `occurrences: [[s,e],...]` を持つ。`ai_tell_density` は **document スコープを除外し、span/scattered の実 AI クセ文字数の union** で算出と定義。`occurrences[]` は IMP-007 の多出現取りこぼしも構造的に防ぐ。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `ai-tell-detector.md`

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: done`（適用 2026-07-28, v1.1）
- 症状: 1 span が複数カテゴリ（I-4＋B-2＋I-1、A-10＋A-6、B-2＋A-5 等）に該当し、edits/findings 1:1 前提で category_summary が実態を過小評価。density も単純加算で被覆率を超えうる。文再構成型 edit（抽象主語→実主語の文分割）は 1:1 部分文字列置換に落ちない。
- 出所: detector-A, rewriter-A, rewriter-B, naturalness-A, fidelity-A（run 2026-06-12）; **rewriter-001（cluster edit / covers_findings）, fidelity-001（複数カテゴリ重畳・も助詞スコープ）, detector-001（density 二重計上）（run 2026-07-28）で再現**
- 適用内容: 「1 span = 主分類 1 finding」を基本とし `merged_categories: [...]` 配列を許容。category_summary は「findings の主 category 先頭文字を集計」と注記。diff 側は `covers_findings: [...]`（1 edit が複数 finding を被覆する cluster edit）を正式サポート。density は文字集合の union で定義。
- 影響: `ai-tell-taxonomy.md §スキーマ`, `japanese-style-rewriter.md`, 各 .md のスキーマ節

### IMP-006 naturalness-reviewer への入力供給ギャップ `status: ready` `hits: 2run`
- 症状: (1) 仕様は「検出器を同基準で再走査」だがレビュアーが手動照合しがち。(2) **run 2026-07-28 では `01_input.txt` と `03_rewrite_diff.json` がレビュアーに未供給で change_rate が測れず**、鉄則「30%/50% 過推敲」を機械判定できなかった（両 naturalness が指摘）。
- 出所: naturalness-A（run 2026-06-12）; **naturalness-001, naturalness-002（run 2026-07-28）で diff 未供給を再現**
- 提案: (a) `ai-tell-detector` を再走査経路として必須化（手動照合禁止）。(b) **naturalness-reviewer に `03_rewrite_diff.json`（change_rate）と `01_input.txt` を必ず渡す入力契約**を SKILL.md / naturalness-reviewer.md に明記。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`

### IMP-008 公的文書での modality 型遷移（義務→依頼／推量→断定）が自動 pass されうる `status: candidate` `hits: 1run(2agent)`
- 症状: I-3「必要がございます」→「お願いいたします／ご持参ください」は necessity→request の deontic 軟化。run 002 では「求める行為・条件・タイミングが同一で読者を誤誘導しない」ため pass としたが、監査が rollback に最も近づいたグレーゾーン。公的文書では「必要」の客観的必要性フレーム（怠れば住民が困る）が依頼フレームで薄れうる。因果接続詞削除（e006「そのため」）の論理保存も「自明」判定に依存。
- 出所: fidelity-002, naturalness-002（run 2026-07-28, run 002）
- 提案: genre=`public_notice`/`legal` のとき diff に (a) modality 型遷移（義務↔依頼↔予定）を `modality_shift: true`、(b) 因果/条件/逆接接続詞の削除を `logic_bearing: true` で自動フラグし、auditor の強制レビュー項目に回す。コラム・ブログでは過剰なので genre 条件付き。
- 影響: `japanese-style-rewriter.md`（diff フラグ）, `content-fidelity-auditor.md`（強制チェック）, `rewriting-playbook.md`（ジャンル分岐）

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **C 系: redundant restatement** 叙述（まず・次に・最後に）と箇条書きが同内容を二重記載。実例: 001(2026-06-12)。 `hits: 1` 出所 detector-A
- **D-7 ブログ結び呼びかけ公式** 「今回は〜ご紹介しました」「〜してみてはいかがでしょうか」。 `hits: 1` 出所 detector-B(2026-06-12)
- **C-9 導入誘導定型** 「さっそく見ていきましょう」式。 `hits: 1` 出所 detector-B(2026-06-12)
- **A-14 無主体の受動連発**（〜される の非敬語的多用）: 行為者を持たない受動が一文書に多発し翻訳調を強める。実例(002, 2026-07-28): 「断水が行われることとなりました」「応急給水も実施される予定」「濁りが解消されます」「設置される予定」。A-8 は「によって」明示が要件、E は文末リズム主体で、無 agent 受動の連発を拾う枠が無い。 `hits: 1` 出所 detector-002
- **A-15 「〜することで〜できる」手段+冗長可能の複合**: 手段句「活用することで」＋冗長可能「削減することができます」の連結。A-3(を通じて)と A-5 の複合で単体分類に落ちない。実例(001, 2026-07-28): 「活用することで…削減することができます」「活用することで…和らげられます」。 `hits: 1` 出所 detector-001
- **公的文書の二重敬語スタック**「〜していただく必要がございます」（いただく＋必要＋ございます）: I-3・過剰敬語・翻訳調のどれにも掛かる三重スタック。独立サブ項目化の余地。 `hits: 1` 出所 detector-002

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019(2026-06-12) 由来。`status: ready` `hits: 1` 出所 fidelity-A
- **#15 述語の意味役割（誰が何を誰に）の保存** ← 万能動詞の相互置換（提供→採用／利用／実現）は A-6/A-10 除去時に多発。実例 e009(001)「実行モデルを提供しており→採用しています」。`status: ready` `hits: 1` 出所 fidelity-001
- **とりたて助詞（も・は・まで）のスコープ移動チェック** ← e018(001)「課題も存在→サーバーレスにも課題は」。含意（対比・限定・追加）を変えうる。`hits: 1` 出所 fidelity-001
- **削除専用サブチェック（deletion-recall test）** 削除 span ごとに「読者が知り得なくなる事実は何か」を逐一問う。`status: ready` `hits: 1` 出所 fidelity-B
- 「情報を含む削除 vs ボイラープレート削除」二分判定。出所 fidelity-B
- 未改変 span の原文完全一致を LCS で機械照合し部分改変見落としを防ぐ。`hits: 1` 出所 fidelity-001

### playbook レシピ追補
- **A・I 系も「反復時は複数の自然形へ分散（同一置換の禁止）」を明文化** ← 現状 playbook の分散指示は E 系リズムのみ。A-6 3連鎖・I-3 反復・A-5 5回の分散は処方外の裁量だった。特に I-3 依頼形は「お願いします/ください/お願いいたします」で敬度が異なり機械均一化で別の AI っぽさが出る。`status: ready` `hits: 2run` 出所 rewriter-001, rewriter-002
- **技術記事向けカタカナ変換表の追補**（アジリティ→俊敏さ/機動力、オペレーション→作業/運用、オーケストレーション、プロビジョニング等の非固有語）＋「保持すべき業界標準語」ホワイトリストとの明確な線引き。B-2 判定の操作的基準「和語・漢語で1〜2語に置換でき、かつ製品名/プロトコル名でない」。`status: ready` `hits: 2run` 出所 rewriter-001, naturalness-A
- **公的文書向け「冗長敬語→簡潔敬語」変換表**（ご使用いただくことができません→ご使用になれません、していただく必要がございます→お願いいたします/ご持参ください）。過推敲（口語化）と推敲不足（翻訳調残存）の両方を防ぐ。`hits: 1` 出所 rewriter-002
- **suggested_fix が span 外の未検出要素の改変を要求する場合は最小変更を優先**（例 f003 能動化「断水を実施します」は責任主体の含意を変えうるため「となりました→になりました」に留めた）。`hits: 1` 出所 rewriter-002
- **推敲後の「除去したクセを別のクセに再生産していないか」自己照合ステップ**（A-6→です化で「です/予定です」新クラスタ発生）。`status: ready` `hits: 2run` 出所 rewriter-002, naturalness-002
- **機能が必要な接続詞（しかしながら）は削除でなく変奏**／**原文が元から推量の D 系は推量を保持**（2026-06-12）。出所 rewriter-A

### naturalness 判定の精緻化
- **絶対残存数ガードは正しく機能中（維持）** ← run 001 は改善84.8%でも S1×2 で grade C を正しく発火し round2 で A に到達。改善率単独でゲートしない現行 SKILL.md 基準は妥当と両レビュアーが確認。`status: validated` 出所 naturalness-001, naturalness-002
- **grade 条件に score_after 絶対上限を併記**（例 A は改善70%+ かつ score_after≤10）: 短文書は 1 finding 増減で改善率が大きく振れるため。`status: ready` `hits: 2run` 出所 naturalness-A/B(2026-06-12), naturalness-002
- **E-2 の客観閾値**: 「終止形の最頻値占有率>80% で S2」等の数値基準。体言止め1箇所以上で緩和。`status: ready` `hits: 2run` 出所 naturalness-B(2026-06-12), naturalness-001
- クラスタ系 finding のクラスタ崩壊時 severity 降格ルール。出所 naturalness-A(2026-06-12)

### 定着カタカナ語 B-2 免責リスト `status: ready` `hits: 1run(3agent)`
- ルーティン・モチベーション・データドリブン 等の定訳が冗長になる語は B-2 から半免責し残差 S3 固定。出所 naturalness-B, fidelity-A, naturalness-A(2026-06-12)

### ジャンル別「定型敬語免除」リストの明文化 `status: ready` `hits: 1run`
- 公的文書の御礼申し上げます/お願い申し上げます/賜り/ございます 等はジャンル必須。免除ルールが taxonomy/SKILL 未記載でレビュアー間の E-2 判定がぶれる温床。ジャンル別免除語リストを taxonomy に正式節として追加すべき。出所 naturalness-002, detector-002

### detector 実装
- start/end 自己検証（regex マッチ位置と text_span 一致を assert）。`hits: 1` 出所 detector-A(2026-06-12)
- 絵文字正規表現レンジ明示 `\U0001F300-\U0001FAFF` ＋ `☀-➿`。出所 detector-B(2026-06-12)
- A-8「による/によって」の除外則: 「によっては」（条件）・「N による N」（連体修飾の手段, 例「給水車による給水」）は非該当。公的文書で by-passive 過検出を防ぐ。`hits: 1` 出所 detector-002
