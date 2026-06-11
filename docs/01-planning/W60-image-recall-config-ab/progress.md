# W60 Progress — 圖片召回 config A/B(DD-4 前後)

## Day 1(2026-06-11)— kickoff

### 緣起 + 用戶決策
- rollup §4.5 末「未盡部分」之一 = per-config A/B 對比(W59 只跑 single config baseline)。
- 用戶 AskUserQuestion(2026-06-11):① **先做 A/B**(prose 型第二份 GT 延後,硬依賴用戶提供文件 + 親自標注);
  ② A/B 軸 = **DD-4 前後**(W59 baseline 剛好 pre-DD-4 = 天然 A 臂)。

### 方法論核實(寫 plan 前 recon)
- `ConfigTestResult`(`/config-test`)response **只有圖數 counters**,**無圖片 checksum 集** →
  無法算 recall(需 set intersection)→ **方式 2(config-test override)否決**。
- `/query` response 有 `citations[].embedded_images[].checksum_sha256` → **唯一可算 recall 的 path**
  (W59 baseline 同 path,apples-to-apples)。
- DD-4 三旋鈕含 `enable_parent_doc_retrieval`(檢索入口),per ADR-0050 不在 per-doc/per-query
  override → 由 **global default** 控制 → **process 環境變數**(非 .env file,守 H5)toggle。
- → A/B = 兩次重啟 backend(同 path / KB / timeout,唯一變數 = DD-4 三旋鈕);driver **零 code 改動**。

### A/B 設計(controlled)
| 變數 | A 臂(pre-DD-4) | B 臂(post-DD-4 現 default) |
|---|---|---|
| `enable_parent_doc_retrieval` | False(env) | True(settings default) |
| `citation_expansion_max_aux` | 2(env) | 10(settings default) |
| `citation_expansion_section_path_prefix_depth` | 0(env) | 1(settings default) |
| path / KB / timeout / semantic | 同:`/query` / `drive-images-1` / 180s / `false` | 同 |

### plan kickoff(R1)
- `docs/01-planning/W60-image-recall-config-ab/` 建:plan.md / checklist.md / progress.md。
- 待 commit plan 後 implement(R1:無 plan 不 implement)。

### F1 — B 臂(post-DD-4 現 default)done
- backend 重啟(post-DD-4 settings default + `SYNTHESIZER_REQUEST_TIMEOUT_S=180`),ready ~120s,全 component ok。
- 跑 9/9 → `reports/image_recall_ar_postdd4.yaml`;**mean recall 0.609 / precision 0.977**。

### F2 — A 臂(pre-DD-4 controlled)done
- backend 重啟(process env override `ENABLE_PARENT_DOC_RETRIEVAL=false` + `CITATION_EXPANSION_MAX_AUX=2` +
  `CITATION_EXPANSION_SECTION_PATH_PREFIX_DEPTH=0` + 180s),ready ~132s。
- 跑 9/9 → `reports/image_recall_ar_predd4.yaml`;**mean recall 0.572 / precision 0.982**。
- **✅ sanity PASS(AC2)**:A 臂 0.572 ≈ W59 baseline 0.5715(precision 0.982 ≈ 0.9824)→ 幾乎完全重現
  → env toggle 生效 + KB 狀態不變 + **DD-4 是唯一變數**(非跨 session confounding)。

### F3 — controlled A/B 對比(同一 session,只變 DD-4 三旋鈕)

| Query | 分類(W59)| A 臂 pre-DD-4 | B 臂 post-DD-4 | Δ recall | returned |
|---|---|---|---|---|---|
| Q001 | A. cap 天花板 | 0.31 (20/65) | 0.31 (20/65) | 0 | 20→20 |
| Q036 | A. cap 天花板 | 0.31 (20/65) | 0.31 (20/65) | 0 | 20→20 |
| Q043 | A. cap 天花板 | 0.27 (20/73) | 0.27 (20/73) | 0 | 20→20 |
| Q003 | A. cap 天花板 | 0.46 (17/37) | 0.51 (19/37) | +0.05(弱)| 18→20 |
| Q038 | A. cap 天花板 | 0.51 (19/37) | 0.51 (19/37) | 0 | 20→20 |
| Q002 | B. ≤cap | 1.00 (18/18) | 1.00 (18/18) | 0 | 19→19 |
| Q004 | B. ≤cap | 1.00 (12/12) | 1.00 (12/12) | 0 | 12→12 |
| Q006 | B. ≤cap | 1.00 (8/8) | 1.00 (8/8) | 0 | 8→8 |
| **Q005** | **C. section miss** | **0.28 (9/32)** | **0.56 (18/32)** | **+0.28** | **9→19** |
| **mean** | | **0.572** | **0.609** | **+0.037** | |

#### 關鍵發現
1. **DD-4 的圖片召回 robust 改善 = Q005**(W59 失敗分類 C「section miss」)。W59 progress 把 Q005 標為
   「非純 cap 問題,是檢索/cite 的 section 覆蓋缺口,**cap 放寬解不了**,需獨立調查」。**W60 A/B 實證:
   DD-4 的 `parent_doc` + `citation_expansion`(depth=1)正是解 Q005 section 覆蓋缺口的手段** —— returned
   9→19,recall 0.28→0.56。即 DD-4 文字完整性 fix(ADR-0052)同時 side-effect 改善了圖片召回的 section 覆蓋。
2. **cap 天花板(Q001/Q036/Q043)+ ≤cap 完美(Q002/Q004/Q006)對 DD-4 0 反應**。cap-bound query 卡 returned
   ~20,DD-4 提的是文字 cite,圖片返回受 image cap 限制,recall 不動 → cap 天花板需 **per-doc 放寬 cap**
   (另一軸,本輪 non-goal)。
3. **precision 幾乎不變**(0.982 → 0.977,仍高)→ DD-4 帶出的多 section 圖片質素未劣化(Q005 多返回的 9 張
   全命中:hit 9→18)。
4. **caveat(single-run variance)**:每臂只跑一次;W59 記 run-to-run figure swing ~20%。Q005 +0.28
   (returned 翻倍 9→19,+10 圖)**遠超** variance → robust 結論;Q003 +0.05(+2 圖)在 variance 範圍 → 弱信號,
   不單獨下結論。mean +0.037 主要由 Q005 driven。

### F3 結論(一句)
**DD-4 production flip(ADR-0052)對 AR 圖密手冊的圖片召回有淨正面 side-effect(mean +3.7pp),且精準地
解了 W59 唯一的 section-miss 異常(Q005);但對 cap-bound query 無能為力(那需 per-doc 放寬 cap)。**
圖片召回的下一個槓桿由實數確認 = **per-doc 放寬 returned cap**(對 cap 天花板 5 條中 3 條 returned 卡 20 的)。

### F4 — doc-sync done
- rollup §4.5 加「W60 A/B 落地」段(A 臂/B 臂/Q005 改善/cap 0 反應/caveat)+ §5 第 3 項更新 + 提議③ 標 done。
- DEFERRED_REGISTER **不改**:§4.5 未盡(prose)= phase-local 一次性 deferral,per 維護規則留 progress.md +
  rollup §4.5,不入 recurring-class 冊。

### 🚧 延後項(carry-over)
- **prose 型第二份 GT**(§4.5 未盡之二)— **硬依賴用戶**:① 提供一份 prose 型(散文/說明型)文件 doc_id;
  ② 親自標注「哪幾張圖相關」(領域判斷,AI 不能代)。close 條件 = 用戶備文件 + 完成標注 → 屆時重用 W59
  catalog dump + HTML 標注頁 tooling 建第二份 GT + 跑 baseline。**target**:用戶觸發(無排期)。
- **cap 放寬軸 A/B**(候選,非欠債)— 本輪用戶選 DD-4 軸;cap 軸驗證「per-doc 放寬 returned cap」對
  cap-bound 3 條(Q001/Q036/Q043 returned 卡 20)的 recall 提升。W60 已由實數確認此為下一槓桿,但跑與否
  待用戶決定。

### Retro
- **方法論勝負手**:寫 plan 前 recon 發現 `config-test` response 無 checksum → 否決 config-test path,
  改 `/query` + process env toggle。若沒先 recon 就掛 config-test,會量錯(數不到 checksum)。Karpathy
  §1.1 think-before-coding 的直接收益。
- **controlled A/B 的價值**:A 臂重現 W59 baseline(0.572 ≈ 0.5715)是關鍵 sanity —— 沒有它,B 臂 vs W59
  跨 session 對比會被質疑 confounding(KB re-index / variance)。controlled 同 session 只變一個旋鈕,delta 可信。
- **實證推翻一個 §4.4 斷言**:W59/§4.4 認為 C 類 section miss「語義層、配置解不了」。W60 證明 **section-覆蓋型**
  C 類(相關 section 存在但沒被 cite)DD-4 這個檢索層配置解到(Q005);真正解不了的是「圖片本身無語義信號」
  (§4.6 結構路線)。把「配置邊界」講得更精準。
- **零 code 改動達標**:全程重用 W59 harness(`run_image_recall.py` 零改),純 env + 跑數 + 分析 → 守 H1/H6。

