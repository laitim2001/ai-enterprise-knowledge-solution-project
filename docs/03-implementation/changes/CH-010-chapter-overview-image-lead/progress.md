---
change_id: CH-010
spec_ref: ./spec.md
checklist_ref: ./checklist.md
status: in-progress     # in-progress | closed
---

# CH-010 — Progress

> Day-N entries + closeout。每 commit 對應 Day-N mention(R2)。

---

## Day 1 — 2026-06-08

### Context
接 CH-009 衍生。CH-009 OD-4 修咗裝飾燈泡(live verified `3c709d2`),但用戶 live 仍見「順序唔對 + 步驟圖唔齊」。診斷確認兩個並存問題:① 章節 §3.1.1 概覽/流程圖未 attach → 無 lead;② 同章節其他 §3.1.x 步驟圖缺失。用戶要求「做到足」一齊解。

### Done(scope + 決策)
- **根因 grounding**(live 實測):drive-images-1 per-KB 完整性 knobs **全部 `null`(關)** + `default_rerank_k=5` + `max_images_per_answer=20`。只 5 個 chunk 入 citation + neighbour-attach depth=0/max_aux=2 → 帶唔到遠離嘅概覽 + 其他步驟圖。圖**存在於 index**,只係冇入候選池。
- **Key insight**:section-aware 同章節 attach 補齊步驟圖之餘,**順帶**令概覽圖入池 → 前端 document-order 自動 lead → 一套機制解兩 goal。
- **CH-010 spec**:scope 由「概覽 lead」擴大到「概覽 lead + 步驟圖完整性」;Approach 1(per-KB 完整性 config)vs Approach 2(+明確 pin)。
- **Approach 1 鎖定**(Chris AskUserQuestion 2026-06-08):per-KB 完整性 config,reuse memory 已 eval 驗證組合,minimal/no code,runtime config 零 re-index,per-KB 隔離可逆。
- **ADR-0047 Proposed** 寫 + README index;spec status draft → approved。

### Decision(Chris 2026-06-08)
- **Approach 1**:drive-images-1 per-KB 開 `enable_citation_neighbour_images=true` + `citation_neighbour_section_path_prefix_depth=1` + `citation_neighbour_max_aux_images=12`(起點,verify 校);可選 complementary parent_doc + expansion 組合(verify 時決定)。
- **不**做:Approach 2 明確 pin(留日後 cap 收窄 robustness)/ 全域 default flip / 改 rerank_k。
- **H4**:只用 section/文字信號,無 image embedding/multimodal。

### Blockers / Carry-over
- 🚧 **P1 ADR-0047 Proposed → Accepted(用戶)** ← config/eval GATE。**未落任何 config / 未跑 eval**,等 Chris Accept。
- 🚧 V3 跨文件 30-query eval(必須,防 regression)— Accept 後做。

### Effort
- Planned ~0.5-1 day(Approach 1 config + verify + eval);Actual:_(填)_

### Commits
| Hash | Subject |
|---|---|
| `f2e44fd` | docs(change): CH-010 spec — chapter-overview image lead (decision pending) |
| `71dd768` | docs(change): CH-010 spec — expand scope to step-image completeness |
| _(本次)_ | docs(adr+change): ADR-0047 Proposed + CH-010 Approach 1 locked |

---

## Day 1 cont — 2026-06-08(Accept → 實作)

### ADR-0047 Accepted(Chris)→ 執行 Approach 1 config

- live A/B(drive-images-1「confirm voucher」)逐步試 per-KB config(neighbour depth=1 max_aux 12→20 + parent_doc + expansion)。

### 關鍵發現:Approach 1 config-only 解唔到概覽 lead(兩個 code 層根因)

1. **neighbour-attach pile-on-lead + nearest-first**:所有 neighbour 圖 pile 落 top citation(CIT 1 idx 27),nearest-first 切,§3.1.3 就近大量圖(idx 25/26/28 共 ~25 張)食晒 max_aux → reach 唔到 idx-24 §3.1.1 概覽(距離 3)。
2. **`cap_images_per_answer` citation-order 餓死概覽**:expansion materialize §3.1.1 做 citation(CIT 5/13,連 2 張概覽圖),但 backend cap(citation/relevance order)喺前端 document-order 之前 pre-trim,top citation 食晒 `max_images_per_answer=20` budget → 概覽 citation 圖 trim 到 0。
- **驗證根因**:set `max_images_per_answer=null` → §3.1.1 citation 即 keep 返 2 張概覽圖(`60a8a6e9` + `cfe10a8d`)→ 證實 cap 餓死。

### 決策 + 落實(promote Approach 2 pin;config 全 revert baseline)

- Approach 1 config **全 revert 返 baseline**(6 個完整性 knobs → null;`max_images_per_answer=20` 保留)。
- 用戶「兩者都做(查 Y + 加 X)」→ Y(cap 餓死)= 診斷,X(pin-before-cap)= 修法,收斂成一個 cap-aware pin。
- 實作 `pin_chapter_overview_images`(NEW,`citation_image_neighbors.py`):偵測主導章節 → fetch §X.1 "Overview" chunk 圖 → prepend 到 lead citation 最前、排喺 cap 之前 → survive cap + document-order lead。per-KB flag `enable_chapter_overview_pin`(default OFF,production-preserve)。
- ADR-0047 加 implementation amendment。

### Code 變更(6 files + tests)

- `storage/settings.py`(C05):`enable_chapter_overview_pin: bool = False` 全域 default。
- `api/schemas/kb.py`(C03):`KbConfig.enable_chapter_overview_pin: bool | None`。
- `generation/effective_config.py`(C05):PerQueryOverrides + EffectiveConfig + resolve。
- `api/schemas/config_test.py`(C05):DraftRetrievalConfig 加 field(harness 可試)。
- `generation/citation_image_neighbors.py`(C05):`pin_chapter_overview_images`(pure aside fetch;graceful)。
- `api/routes/query.py`(C05):wire 兩條 path(attach 後、cap **前**)。
- `tests/test_ch010_chapter_overview_pin.py`:7 tests。

### Verify(單元)

- **V-unit PASS**:pytest 47(7 新 pin + 40 既有 neighbour/effective_config)+ ruff 我 code 乾淨(唯一 B905 = pre-existing,非我 code,surgical 不修)+ ruff format 全過 + mypy --strict 改動檔 0 新 error(64 pre-existing baseline)。

### Blockers / Carry-over

- 🚧 **重啟 backend 載新 code**(無 --reload;dual-process;startup 慢,輪詢 /health)。
- 🚧 **V1/V2 live**:enable drive-images-1 `enable_chapter_overview_pin=true`(+ neighbour depth=1 完整性)→ /query/stream 確認概覽 lead + 步驟補齊。
- 🚧 **V3 跨文件 30-query eval**(必須,防 regression)。
- 🚧 V5 用戶 chat live。

### Commits（本 cont）
| Hash | Subject |
|---|---|
| _(本次)_ | feat(chat): CH-010 chapter-overview image pin (ADR-0047) |

---

**End of CH-010 progress (Day 1 cont — pin implemented + unit-verified;backend restart + live/eval GATED)**
