---
phase: W42-hybrid-semantic-ranker-toggle
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active
last_updated: 2026-05-29
---

# W42 — Progress

> Daily progress journal。每日 append 一個 Day-N entry,closeout 時 retro 7 段。

## Day 0 — 2026-05-29(kickoff)

### Trigger

W41 closed 2026-05-28 + smoke test session 揭露 chat UI hybrid mode 撞 Azure Free tier 402。User 問「是否有其他更平嘅 vector DB 選擇能支援 chat UI full pipeline」→ 三方深入 trade-off 分析(Option ① drop semantic ranker / ② pgvector swap / ④ Basic $75)→ Chris AskUserQuestion 揀「起 W42 plan 做 Option ①」。

### 關鍵分析發現(driving Option ①)

1. **402 root cause = semantic ranker,NOT vector DB** — `hybrid.py:371` `queryType="semantic"` 係 Azure billable semantic ranker;vector / fulltext mode 唔用 → Free tier work
2. **換 vector DB 解錯問題** — pgvector / Qdrant 都冇 Azure semantic ranker,照樣要重寫 hybrid,仲觸發 H2 vendor swap
3. **semantic ranker 喺 EKP 大致 redundant** — Q21 已證佢比 Cohere WORSE;EKP search 之後行 Cohere 做主 reranker(同一 50 候選集)→ semantic ranker 只係被 override 嘅次等中間層
4. **成本落差 flag** — spec budget ~$75 以今日定價只買到 Basic,S1(spec lock)實際 $249.98

### Plan rationale

- **Option ① = cheapest path to stated goal**:$0(留 Free tier)/ ~1-2h / 完全可逆 / 唔換 vendor / 質素 risk 近乎零
- **對齊 W37-W41 knob pattern**:加 flag、default preserve production、`.env` override 做測試
- **但 H1-adjacent**(比 post-rerank knobs 更 core)→ 需 ADR-0039 + Gate 1 re-verify + F1 GATE STOP+ask

### R6 Day 0 7 catches surfaced(per CLAUDE.md §10 R6)

| # | Catch | Mitigation |
|---|---|---|
| 1 | `queryType=semantic` 只喺 `hybrid.py:371`;`reranker/azure_semantic.py` 係另一回事(unused standalone reranker)| F1 只 toggle hybrid.py,唔郁 reranker |
| 2 | chat UI 固定 hybrid(useChat SSE 唔 expose mode)→ flag main beneficiary | F3 chat UI test |
| 3 | flag 同 mode param 正交 — flag 控制 hybrid 用唔用 semantic,mode 控制 hybrid/vector/fulltext | F1 設計獨立 |
| 4 | `azure_semantic_config_name` settings 存在但 hybrid.py:372 hard-code literal | F1 順手 parametrize |
| 5 | Gate 1 0.9722 measured WITH semantic → flag OFF 必須 re-verify | F2 H1 safety gate |
| 6 | `test_hybrid_search_payload_shape_matches_spec` assert semantic | F1 保留 + 加 flag-False test |
| 7 | flag OFF hybrid = BM25+vector+RRF Azure 自動 fusion 仍 work | F1 design confirm |

### H1 boundary 評估(per plan §5)

W42 改 §3.1 retrieval search behavior(semantic ranker on/off)= **H1-adjacent**。雖然 default-preserve flag 令 production 行為不變,但觸及 Gate 1 + Q21 decision predicate → **需 ADR-0039 + Gate 1 re-verify**。

**F1 retrieval code 之前必須 STOP+ask 等 user confirm H1 boundary + ADR-0039 Accept**(per CLAUDE.md §5.1 H1 Required behavior)。

### Real-calendar projection

F0 ~30min + (等 H1 confirm)+ F1 ~45min + F2 eval ~30-45min + F3 LIVE chat UI ~30min + F4 ~20min = **~2.5-3h total**。

### Next

F0.7 commit + F0.8 session-start sync → **F0.9 STOP+ask H1 boundary + ADR-0039 Accept**(F1 GATE)。

---

## Retro(在 F4 closeout 時填)

### 1. 整體結果
_[F4 closeout 時填]_

### 2. 5 axes lessons learned
_[F4 closeout 時填]_

### 3. CLAUDE.md / PROCESS.md / session-start.md 同步
_[F4 closeout 時填]_

### 4. Memory updates
_[F4 closeout 時填]_

### 5. 後續(W43+ candidates)
_[F4 closeout 時填]_

### 6. Real-calendar collapse
_[F4 closeout 時填]_

### 7. PR readiness
_[F4 closeout 時填]_
