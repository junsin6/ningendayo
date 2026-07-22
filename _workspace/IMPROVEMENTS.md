# 人間だよ — 改善バックログ（実戦由来）

実 run のエージェント報告から抽出した改善点を、優先度・再現回数つきで蓄積する。
**昇格規則**: 異なる run で 2 回以上再現したら `status: ready`（適用候補）へ。適用したら `status: done` と適用 run を記録。

凡例: P0 構造的欠陥 / P1 仕様の穴 / P2 個別レシピ・分類。`hits` = これまでに指摘した run 数。

最終更新: 2026-07-22（run 001 ベクトルDB技術解説, 002 自治体お知らせ）

---

## P0 — 構造的欠陥（最優先）

### IMP-001 変更率指標が「正当な削除」と「過推敲」を区別できない `status: done` `hits: 2run` `applied: 2026-07-22-002`
- 症状: difflib 文字単位 change_rate が C-1/C-2 構造編集・冗長要請/受動/状態叙述の純削除で機械的に膨張。
  - run 001(0612): Sample B 54.6% で hold_and_report 誤発火。
  - **run 002(0722): 公的文書で 0.38（挿入48字/削除181字の削除主導）。「〜していただく必要がございます」「〜によって〜される」「〜となっております」の官僚パディング圧縮で、fidelity=pass・情報欠落ゼロ・grade A なのに 30% 警告が機械発火。override accept で通した。**
- 出所: rewriter-A(0612), naturalness-B(0612), rewriter-002, naturalness-002, fidelity-002
- 適用(2026-07-22): `rewriting-playbook.md §変更率の数え方` を改訂し **`insert_rate`（挿入のみ／原文長）を過推敲の主指標**に格上げ。change_rate は参考値に降格。削除主導（del≫ins）かつ fidelity=pass のケースは中断対象から除外する規約を明記。`SKILL.md §総合判定` に override accept 条件を追記。分母は `meta.input_length` に一本化。
- 残: 「意味改変 edit 比率」ベースの中断基準（50%）はさらなる run で検証後に精緻化。

### IMP-002 severity_weighted_score の正規化が未定義で saturate `status: done` `hits: 2run` `applied: 2026-07-22-001`
- 症状: 正規化式が SSOT に無く、高密度短文で raw が即 100 付近に張り付き深刻度の解像度が消える。
  - run 001(0722): 828字・S1×12 で raw 加重和がちょうど 100 に到達し天井に張り付いた。2倍ひどい文も同じ 100 になり識別不能。
  - run 002(0722): 642字 density36% でも 74 で頭打ち感。`min(100, raw)` は「短文の高密度を過小評価しつつ長文を飽和させる二重欠陥」。
- 出所: detector-A(0612), detector-B(0612), detector-001, detector-002
- 適用(2026-07-22): `ai-tell-taxonomy.md §検出出力スキーマ` に **長さ正規化式 `score = 100 × (1 − exp(−raw / (0.06 × max(input_length,200))))`**（1000字あたり raw≈16.7 で ~63、飽和が緩やか）を明記。`ai-tell-detector.md §スコア算出` に算出手順を追記。raw（生加重和）も `meta.raw_weighted_sum` として併記し可逆性を確保。

### IMP-007【新規】cluster-anchor 問題 — 反復/列挙パターンを単一 anchor でしか検出できない `status: done` `hits: 2run` `applied: 2026-07-22-001`
- 症状: C-1（まず・次に・最後に）・F-4（〜的反復）・E-2（文末単調）・H-1（接続詞反復）のような**クラスタ型パターン**を、検出器が reason に複数座標を挙げながら `text_span`/`start`/`end` は先頭1点のみに anchor する。span 厳守の推敲役は先頭語しか触れず、第一項を叙述へ溶かした瞬間に残りが宙吊りになる。
  - **run 001(0722): C-1 が「まず」1点のみ anchor → 推敲役が「次に」「最後に」を触れず、naturalness が S1 残存で grade C → rewrite_round_2 に落ちた（1パスでは原理的に完治不能）。F-4 も「意味的」のみ anchor で密度3→2 半減止まり。**
  - **run 002(0722): detector-002 が「同一サブパターンの反復を occurrence リスト付き 1 finding に畳む」表現をスキーマに要望（同根の問題）。**
- 出所: rewriter-001, fidelity-001, naturalness-001, rewriter-001-r2, fidelity-001-r2, naturalness-001-r2, detector-002（1 run で6エージェント＋別 run で1）
- 適用(2026-07-22): `ai-tell-taxonomy.md §検出出力スキーマ` に finding の **`scope: "span"|"cluster"|"document"`** と、cluster/document 用の **`occurrences: [[s,e],...]`**（反復メンバー全数の座標配列）を追加。`ai-tell-detector.md` に「反復/列挙パターン（C-1/C-2/C-7/C-8/E-1/E-2/F-4/F-5/H-1/H-2/I-5）は代表 anchor に加えて occurrences に全メンバー座標を張る」規則を明記。推敲役は occurrences 全域を span-grounded 領域として扱える → round2 往復を構造的に削減。IMP-004（下記）を包含。

### IMP-003 score_before のフィールド契約が曖昧 `status: ready` `hits: 2run`
- 症状: naturalness-reviewer がどの値を score_before にするか。run 0722 では両レビュアーとも `meta.severity_weighted_score` を正しく採用したが、SSOT に明文がないため運用依存のまま。
- 出所: naturalness-A(0612), naturalness-001, naturalness-002
- 提案: 「score_before = 02_detection.json の meta.severity_weighted_score」を SSOT 明記。IMP-002 の正規化明文化で score の一貫性は改善済み。次回この一文を naturalness-reviewer.md へ追記予定。
- 影響: `naturalness-reviewer.md`, `ai-tell-taxonomy.md`

---

## P1 — 仕様の穴

### IMP-004 scattered/document レベル span をスキーマが表現できない `status: done` `hits: 2run` `applied: 2026-07-22-001`（IMP-007 に統合）
- 症状: 絵文字分散・文末単調・E-1文長均一・F-4/H-1 反復は分散パターン。単一 start/end では広域 locator にするしかなく ai_tell_density が過大化。
  - run 001/002(0722): E-1/E-2/F-4/H-1 を「代表 anchor + reason 全体注記」で表現し密度から手動除外。恣意的。
- 出所: detector-B(0612), detector-A(0612), detector-001, detector-002
- 適用(2026-07-22): IMP-007 の `scope`+`occurrences` 追加で解決。加えて `ai_tell_density` を **occurrences 座標レンジの和集合（重複除去）/ 全文字数** と定義し直し（run 002 detector が既に手動採用）、document スコープ finding は density 非算入と明記。

### IMP-005 span 重複時の finding/edit カウント規約が無い `status: ready` `hits: 2run`
- 症状: 1 span が複数カテゴリに該当。
  - run 001(0722): カタカナ複合語（ファクター/メリット/ナレッジマネジメント）が A-6/A-10/B-2 と物理的に重なり、手動で anchor をずらし回避。
  - run 002(0722): A-8「利用者ご自身によって」と I-4「再入力が…必要」が隣接、A-8 span を切り詰め density を和集合算出で回避。
- 出所: detector-A/rewriter-A/rewriter-B/naturalness-A/fidelity-A(0612), detector-001, detector-002
- 提案: 「1 span = 主分類 1 finding」を基本とし、`merged_findings:[...]` または `overlapping_categories:[...]` を許容。category_summary は主分類先頭文字を集計と注記。density は和集合ベース（IMP-004 で対応済み）。
- 影響: 全 .md のスキーマ節。**次回適用候補（hits 到達済み）。**

### IMP-006 naturalness-reviewer が検出器を実行できず score_after が推定 `status: ready` `hits: 2run`
- 症状: 仕様は「検出器を同基準で再走査」だが、run 0722 では両レビュアーとも「detector をサブエージェント起動する手段が無い」と報告し taxonomy 基準の手動再走査で代替。score_after が人手依存で再現性リスク。
- 出所: naturalness-A(0612), naturalness-001, naturalness-002
- 提案: naturalness-reviewer が `ai-tell-detector` を必ず再呼び出しする経路を必須化（手動照合禁止）。オーケストレーター側で推敲後テキストへ detector を実走査し score_after を機械確定。
- 影響: `naturalness-reviewer.md §処理`, `SKILL.md`。**次回適用候補（hits 到達済み）。**

### IMP-008【新規】modality 強度の順序尺度化 `status: ready` `hits: 2run`
- 症状: 日本語の指示強度に順序尺度がなく、義務→依頼の軟化/強化が定性判断。
  - run 002(0722): 「必要がございます」→「ください」の義務→依頼 一段軟化を複数検出、また「予定となっております」→「公表いたします」の 予定→断定 firming（可謬性の欠落）も。fidelity は pass だが定量管理不能。
- 出所: fidelity-A(0612), fidelity-002
- 提案(fidelity-002 IMP-014/015): **順序尺度 `必須 ＞ しなければならない/必要がある ＞ ていただく必要がございます ＞ お願いいたします/ください ＞ ご検討ください`** を導入。ルール: 推敲は尺度を最大1段のみ下降可、かつ範囲・行為者・行為マーカー（すべて/一部/場合/手順）が明示保存されている場合に限る。「予定」等の可謬性を消す上方 firming も双方向で監視。
- 影響: `rewriting-playbook.md §I`, `content-fidelity-auditor.md §チェックリスト`。

### IMP-009【新規】公的文書ジャンルの過推敲定義（ジャンル別許容変奏テーブル） `status: ready` `hits: 1run(2agent)`
- 症状: 公的文書では E-2 処方「体言止めを混ぜる」を適用するとトーン逸脱になる。run 002 の推敲役は正しく回避したが playbook 暗黙依存。
- 出所: rewriter-002, naturalness-002
- 提案: `rewriting-playbook.md` に **ジャンル別許容変奏テーブル**（公的文書＝体言止め禁止・依頼形変奏のみ／コラム・技術解説＝体言止め可 等）を追加。naturalness の過推敲判定基準も同期。

---

## P2 — 分類・レシピ・チェックリスト

### 新パターン候補（taxonomist 審査待ち）
- **I-6 丁重要請複合「〜していただく必要がございます」** [S1相当]: ていただく（依頼敬語）＋必要（need to 直訳）＋ございます（丁重）の三重複合。**公的文書 AI の決定的シグネチャ**。実例(run 002)×4: ご了承いただく必要がございます／実施していただく必要があります／行っていただく必要がございます/があります。出所 detector-002, rewriter-002。`hits: 1run(2agent)`
- **B-4 カタカナ複合語の連鎖** [S2]: 単語単位 B-2 で捉えきれない カタカナ+カタカナ/英字 の複合名詞。実例(run 001): ナレッジマネジメント・カスタマーサポート・AIアプリケーション。出所 detector-001。`hits:1`
- **擬古コピュラ「〜であります」**: 「です/である」で足りる箇所の気取り。実例(run 002)「移行するものであります」。A/F 系に新設要検討。出所 detector-002。`hits:1`
- **C 系 redundant restatement**（0612 継続）叙述と箇条書きの二重記載。実例 001(0612)。`hits:1`
- **D-7 ブログ結び呼びかけ公式** / **C-9 導入誘導定型**（0612 継続）。`hits:1`

### taxonomy シグネチャ追補（低リスク・次回適用候補）
- **A-2 敬体変種**: 現行例は「について/に関して/に対して」だが公的文書主形は「につきまして(は)」。シグネチャ例に敬体変種を追記。出所 detector-002, naturalness-002。`hits:1run(2agent)`
- **A-6 敬体変種**: 「〜運びとなりました／こととなります／予定となっております」をサブ例に追記。出所 detector-002。
- **A-4 姉妹形「〜をベースに」**: based on の口語+B-2複合直訳。実例「履歴をベースに」。A-4 シグネチャに追記。出所 detector-001。
- **A-1「において」感度**: 要請述語と噛み合わない「利用者において」型の locative が検出漏れ。実例(run 002)「すべての利用者において」（残存 S2 の原因）。出所 rewriter-002, naturalness-002。`hits:1run(2agent)`

### fidelity チェックリスト追補
- **#14 接続語/順序語の置換で序列・因果・価値が新規付与されていないか** ← f019。`status: ready` `hits:1`（0612）
- **#15【新規】追加的並列マーカー（も/でも）の三分岐判定**: 順序語→追加係助詞の移し替え時、(a)中立 co-membership〈許容〉/(b)エスカレーション「さらに・その上」共起〈情報追加=毀損〉/(c)想定外性譲歩「意外にも・even」〈modality/極性混入=毀損〉を判別。観測点=NP接続か文頭独立か/scalar文脈の有無/程度強調語共起。出所 fidelity-001-r2。`hits:1`
- **連結型マイグレーション検査の独立化**: 表層連結型（序数/逆接/換言）ではなく underlying 論理関係の不変を別立て検証。出所 fidelity-001-r2, fidelity-A(0612)。
- **削除専用サブチェック（deletion-recall test）** ＋ **`preserved_info_items` マニフェスト**: 削除主導 run で推敲役 diff に「保存すべき情報項目チェックリスト」と各削除 span への「情報担持/パディング」フラグを付与し #10 照合を構造化。出所 fidelity-B(0612), fidelity-002 IMP-016。`hits:2run`
- 情報削除 vs ボイラープレート二分判定（数値/固有名詞/日付・条件/因果・固有例示=情報欠落／挨拶/CTA/装飾=パディング）。出所 fidelity-B(0612), fidelity-001。`hits:2run`

### playbook レシピ追補
- **I-3 敬体サブテーブル**: 「〜していただく必要がございます」の敬体分散カタログ（ください／お願いいたします／お手続きください／〜が必要です）。現行 After は常体前提で公的文書に非対応。出所 rewriter-002。
- **E-1 レシピの現実化**: 「10〜20字短文の**新設**」は原文に素材が無いと情報付加=fidelity 違反。「既存長文の**分割**による文長SD引き上げ」へ書き換え、達成不能時は残存を減点対象外に。出所 rewriter-001, naturalness-001。`hits:1run(2agent)`
- **H-1 機能別残置判定**: 削除率ではなく機能別（帰結/追加/補足/主題）で残置判定。つきましては/また 等の論理必須接続は保持。出所 rewriter-002, rewriter-A(0612)。
- **隣接未検出クセの座礁**: 検出 span の編集が隣接の未検出クセ（例 A-1「において」）を露出させるケースを明記し、検出器差し戻し or 最小隣接調整の例外規定。出所 rewriter-002。
- 定着カタカナ語 B-2 免責リスト（ルーティン・モチベーション・データドリブン）。出所 naturalness-B/fidelity-A/naturalness-A(0612)。`hits:1run(3agent)`

### naturalness 判定の精緻化
- 過推敲シグナルの定量化（敬体/常体混入は文末形態の二値カウント／`insert_rate` を diff から機械抽出）。出所 naturalness-A(0612), naturalness-002。
- クラスタ系 finding のクラスタ崩壊時 severity 降格ルール。出所 naturalness-A(0612)。
- 絶対残存数ガード（S1 が1件でも C 以下）。出所 naturalness-A/B(0612), naturalness-001（実際に grade C を出し機能した）。

### detector / schema 実装
- **`meta.severity_breakdown`（S1/S2/S3 内訳カウント）を追加**: 品質等級が S1/S2 件数依存なのに meta に無く下流が再計算。出所 detector-001。`hits:1`（低リスク・次回適用候補）
- **ジャンル別カタカナ許容ホワイトリスト**を references に明文化（技術記事: アーキテクチャ/インデックス/クエリ/ベクトル/パフォーマンス等を B-2 除外）。出所 detector-001。
- start/end 自己検証（regex 位置と text_span 一致を assert）。出所 detector-A(0612)。両 run とも "all spans match slice: True" を自主検証済み。
- 絵文字正規表現レンジ明示。出所 detector-B(0612)。
