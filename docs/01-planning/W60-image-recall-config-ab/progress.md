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

<!-- 跑數結果待 append -->
