---
phase: W19-frontend-audit-and-adr-draft
deliverable: F4
plan_ref: ../plan.md
audit_refs:
  - ./W19-mockup-jsx-audit.md
  - ./W19-backend-gap-map.md
date: 2026-05-16
status: complete
---

# W19 F4 — Wave Breakdown(W20+ Phase Skeletons)

> Consume W19 F1 audit + F2 backend gap map + F3 ADR drafts → propose **4-Wave implementation roadmap** for design-mockups → real-`frontend/` work。Per CLAUDE.md §10 R1 rolling JIT,W20-W23 phase folders **NOT** pre-created;each Wave kickoff is its own session post-W19 F6 closure decision per ADR-0025 + scope authorization。
>
> **User decisions consumed**(per AskUserQuestion 2026-05-16):
> - 岔口 1 + 岔口 2 deferred to F6 Chris review — F4 documents both option set impacts
> - **Auth path** = Mock-auth default + W22 Wave C ships mock + real concurrent(per user 岔口 2)

---

## §1 Wave A — W20-frontend-wave-a(Dashboard + Chat + KB cluster)

### 1.1 Scope

Frontend(`frontend/`)implementation of:
- `/dashboard` — real overview(5 cards + 4-stat strip)per ADR-0030 polish bundle absorb
- `/chat` — advanced surfaces per **ADR-0031**(Conversation History localStorage Tier 1 + 3 citation placement modes + InlineImageCard + ImageGallery + CitationPill hover popover + FeedbackBar comment + CRAG strip indicator)
- `/kb` list + `/kb/new` 5-step wizard per **ADR-0028**(Multimodal Tier 1 active + Tier 2 disabled affordance)
- `/kb/[id]` **7-tab** Detail per **ADR-0025**(Documents + Chunks + **Images** + **Chunking Lab** + Pipeline + Retrieval Testing + Settings — **Access tab disabled affordance** "Tier 1.5 RBAC pending Wave C")
- `/kb-upload/[id]` 3-step re-ingestion wizard per ADR-0028 §5.5.3b
- `/login` + `/register` polish(Brand panel + Forgot password disabled per ADR-0014)
- Topbar polish per ADR-0032 absorbed:NotificationsMenu(mock or `/notifications` backend per W19 F2 item 21)+ Workspace switcher disabled affordance(per W19 F1 §2.3 Tier 2 leak fix)+ Sidebar Tools sub-section + Labs section recommend hidden(per F5.4 Option C)

### 1.2 Backend deps(per W19 F2 §3.1 + §3.2 — 8 items)

**Wave A blockers**(must land before W20 ship):
1. `GET /health` per-component connectivity payload(`/dashboard` System health card)— ~0.5-1d C07
2. `KbConfig` schema add multimodal ACTIVE fields(`extract_embedded_images` + `slide_screenshots` + `dedup_strategy: sha256` + `return_images_in_chat`)— ~0.5d C02 + C01
3. Q6 recent queries decision OR keep empty-state CTA per W18 F4 — decision item(if defer = CTA;if enable = `query_log` table + `POST /query` writes + `GET /queries/recent` endpoint ~2d)
4. Eval cached run decision OR keep empty-state CTA — decision item(if defer = CTA;if enable = `eval_run` cache + `GET /eval/runs/latest` endpoint ~1d)
5. `QueryResponse` schema verify includes `crag_triggered: bool` + `crag_iterations: int`(for Chat CRAG strip)— ~0.2d C05
6. `POST /kb/{kb_id}/archive` endpoint(KB Settings Danger zone)— ~0.3d C02
7. `GET /kb/{kb_id}/images` enriched(ADR-0025 Images tab)— ~1d C01 + C02 + C03
8. `POST /chunking-preview`(ADR-0025 Chunking Lab tab)— ~1.5d C01 + C03

**Wave A backend total**:~5-7 days depending on Q6/Eval-cache decisions(both default to empty-state CTA per W18 F4 acceptance,minimum scope = ~3-4 backend days)。

### 1.3 Frontend effort

Per W12-W18 real-calendar collapse pattern,plan-day budgets historically 3-4× larger than actual。Wave A is the largest by file count(8 routes touched):

| Surface | Plan-day estimate | Per Karpathy §1.4 |
|---|---|---|
| `/dashboard` real cards + topbar polish | 1.5d | NEW page (W18 F4 placeholder → real cards) + NotificationsMenu + Workspace switcher disable |
| `/chat` advanced(ADR-0031) | 2-3d | Conversation History sidebar(localStorage)+ 3 citation modes + image cards + gallery + pill popover + FeedbackBar comment + CRAG strip |
| `/kb` list polish | 0.5d | Grid + Table view + filter bar |
| `/kb/new` 5-step wizard | 2d | NEW route + 5 step components + Multimodal Tier 1/2 affordance |
| `/kb/[id]` 7-tab Detail(`-Access`) | 3-4d | NEW Images tab + NEW Chunking Lab tab + existing 5 tabs polish |
| `/kb-upload/[id]` re-ingestion | 0.5d | existing 3-step skeleton polish |
| `/login` + `/register` polish | 0.5d | Brand panel + Forgot password disabled affordance |
| Cross-cutting(routing + tests + AppShell topbar/sidebar updates) | 1d | Notifications + Tools + Labs(F5.4 Option C — hidden) |

**Wave A frontend total**:~11-13 plan-days budget;actual ~3-5 days(per W12-W18 collapse pattern)。Window:**1.5-2 weeks**。

### 1.4 Acceptance criteria sketch

- F1: `<AppShell>` topbar NotificationsMenu + Workspace switcher disabled affordance + Sidebar polish all per ADR-0032 absorbed scope
- F2-F8 per-route implementations(roughly matching prototype's component structure but using `frontend/components/ui/` shadcn primitives)
- F9: `architecture.md v6 §5` inline-tagged amendment per ADR-0025 + ADR-0028 + ADR-0031;ADR-0025/0028/0031 Status `Proposed` → `Accepted` after Chris confirms at Wave A kickoff
- F10: Wave A Gate PASS conditions:`tsc`+`lint` clean + `[oklch(`=0 + Vitest 13/13 baseline preserved(per W17 F6 + W18 F8.4)

### 1.5 ADR deps + option pick impact

- ADR-0025 KB Detail 8-tab → **Wave A scope ships 7-tab(-Access)** per consensus
- ADR-0028 /kb/new 5-step → **Wave A scope ships full 5-step** with Multimodal Tier 1/2 affordance
- ADR-0031 Chat advanced → **Wave A scope** depends on Conversation History option:
  - Option A(localStorage)= 0 backend days,full frontend scope
  - Option B(server-side)= 3 backend days deferred to Wave A backend list(item 21 promotion);frontend scope same
  - Option C(Tier 2 defer)= Wave A frontend simplifies(no history sidebar — just chat + citations + feedback)

---

## §2 Wave B — W21-frontend-wave-b(Doc Detail + Eval + Traces)

### 2.1 Scope

- `/doc-detail/[kbId]/[docId]` OR `/kb/[id]/docs/[docId]` per **ADR-0029**(route name pick at F6) — 3-pane layout(outline + chunks + inspector with embedding viz)
- `/eval` Eval Console — 4-metric stat + Reranker Shootout + Failed queries + Recommendation + Ops Metrics + CRAG Insights(consume W17 F3 RAGAs backend per ADR-0012)
- `/traces` index list view per ADR-0030 absorb(filter seg + date range + 9-col table)
- `/traces/[traceId]` 9-stage trace with **3 viz modes** per ADR-0030 absorb(vertical + waterfall + flame)+ Final response card

### 2.2 Backend deps(per W19 F2 §3.3 — 2 items)

**Wave B blockers**:
9. `GET /kb/{kb_id}/docs/{doc_id}` enriched(outline + parse/embed durations + image refs)per ADR-0029 — ~1d C01 + C03
10. `GET /traces?filter=...&since=...` list view — ~1d C07(query Langfuse Postgres + filter)

**Wave B backend total**:~2 days。

### 2.3 Frontend effort

| Surface | Plan-day estimate |
|---|---|
| `/doc-detail` 3-pane(outline + chunks + inspector + image strip) | 2-3d |
| `/eval` Eval Console(4-metric stat + Shootout + Failed queries + Recommendation + Ops + CRAG insights) | 2d |
| `/traces` list view | 0.5d |
| `/traces/[traceId]` 3 viz modes(vertical default + waterfall + flame) | 1.5d |
| Cross-cutting(routing + tests) | 0.5d |

**Wave B frontend total**:~6.5-7.5 plan-days budget;actual ~2-3 days per collapse pattern。Window:**~1 week**。

### 2.4 Acceptance criteria

- ADR-0029 Status `Proposed` → `Accepted` at Wave B kickoff with route name pick
- ADR-0030 absorb confirmed at Wave B kickoff(Trace 3 viz + /traces list both ship without separate ADR)
- 3 viz modes via `tweaks.traceViz`(carry-over of W18 design pattern)
- Embedding vector preview feasibility verified — if Azure Search exposes vectors,implement;if not,disabled affordance "Tier 2"

### 2.5 ADR deps

- ADR-0029 /doc-detail 3-pane → Wave B exclusive
- ADR-0030 absorbed bundle(Dashboard + Trace + /traces list)— Dashboard shipped Wave A,Trace + /traces ship Wave B

---

## §3 Wave C — W22-frontend-wave-c(Settings + /users + Auth polish + real-MSAL concurrent ship)

### 3.1 Scope

- `/settings` 6-tab hub per **ADR-0026**(Option C hybrid recommended) — Profile + Appearance + Account fully editable;Connections + Identity & Auth + API Keys read-only + Test connection
- `/users` 4-tab(Members + Roles + Groups + Audit log)per **ADR-0027**(Option B minimal 3-role recommended) — Members read-only listing + invite + suspend;Roles read-only matrix;Groups + Audit log disabled affordance Tier 2
- `/kb/[id]` Access tab(ADR-0025) — per-KB ACL using ADR-0027 RBAC infrastructure
- `/login` + `/register` real-MSAL path concurrent ship(per user 岔口 2 — mock-auth default Tier 1 preserves + real MSAL feature-flagged ready-to-flip when Track A IT cred lands)
- `<LoginGate>` `// TODO(W16)` tighten to `router.replace('/login')` per W18 F2.2 deferral(if Q11 Track A cred lands by W22)

### 3.2 Backend deps(per W19 F2 §3.4 — 10 items,option-set scoped)

**Per recommended Option C + Option B picks**:

| # | Item | Effort | Cn |
|---|---|---|---|
| 11a | `GET /admin/connections/list` → status overview | 0.5d | C12 |
| 11b | `POST /admin/connections/{id}/test` → test connection × 9 providers | 1.5d | C12 |
| 12 | `GET /admin/identity/{tenant|app|msal|roles|policy}` read-only | 1d | C11 + C12 |
| 13 | `GET /admin/api-keys` read-only + `GET /admin/usage-stats` | 0.5d | C08 |
| 14 | Postgres migration:add `users.role` column(default `'user'`)| 0.5d | new C16 or C11 |
| 15 | `GET /users` list + `PATCH /users/{id}` + `POST /users/invite` + `POST /users/{id}/suspend` | 1d | C11 |
| 16 | `GET /roles` + `GET /role-permissions-matrix`(read-only hard-coded matrix) | n/a(hard-coded in code) | n/a |
| 19 | ACL middleware checks `users.role` only against hard-coded PERMISSIONS_MATRIX + auth-time role claim | 0.5d | C11 |
| 6 | `/kb/{kb_id}/acl` minimal(GET only Tier 1) | n/a — deferred Tier 2 per ADR-0027 Option B(workspace role enforces) | — |
| 20 | `<LoginGate>` real-MSAL tighten — `router.replace('/login')` | 0.2d | C11 frontend |

**Wave C backend total per Option B+C**:**~5-6 days**(fits single Wave C phase per F2 §6)。

**Per Option A+B picks(NOT recommended)**:**~22 backend days** — must split Wave C into C1+C2 sub-phases per CLAUDE.md §10 rolling JIT。

### 3.3 Frontend effort

| Surface | Plan-day estimate |
|---|---|
| `/settings` 6-tab(Option C hybrid) | 3-4d |
| `/users` 4-tab(Option B minimal) | 2-3d |
| `/kb/[id]` Access tab activate(per-KB ACL UI consume RBAC) | 1d |
| `/login` + `/register` real-MSAL feature-flag wire | 1d |
| `<LoginGate>` tighten | 0.2d |
| Cross-cutting(routing + tests) | 0.5d |

**Wave C frontend total**:~8-10 plan-days budget per Option B+C;actual ~3-4 days per collapse pattern。Window:**~1.5-2 weeks**。

### 3.4 ADR deps

- ADR-0026 Status `Proposed (option set)` → `Accepted (Option C)` at Wave C kickoff
- ADR-0027 Status `Proposed (option set)` → `Accepted (Option B)` at Wave C kickoff
- ADR-0025 Access tab → Wave C activates(was disabled affordance Wave A)
- ADR-0014 hybrid auth + ADR-0022 transport hardening — Wave C real-MSAL feature-flagged ship per user 岔口 2

### 3.5 岔口 → Wave C impact diagram

**Option pick scenarios**(per user F6 pick):

```
        ADR-0026 Settings Connections                  ADR-0027 /users RBAC
        ┌─────────┬───────────┬─────────┐              ┌─────────┬───────────┬─────────┐
        │  A r/o  │  C hybrid │  B full │              │ B mini  │  C stage  │  A full │
        │  ~3 days│  ~5 days  │ ~22 days│              │ ~5 days │ ~5 days   │ ~20 days│
        └─────────┴───────────┴─────────┘              └─────────┴───────────┴─────────┘
                       ▼                                              ▼
                  Wave C scope per combination:
                  ┌─────────────────────────────────────────────────────────────────┐
                  │ B + C(recommended):    ~10 backend days,single Wave C phase    │
                  │ A + B(minimum):         ~8 backend days,single Wave C phase    │
                  │ C + C(both hybrid):     ~10 backend days,single Wave C phase    │
                  │ B + A(full RBAC):       ~25 backend days,must split C1 + C2    │
                  │ A + A(both full):       ~42 backend days,must split C1 + C2 + C3│
                  └─────────────────────────────────────────────────────────────────┘
```

**Recommendation**:**B (minimal RBAC) + C (hybrid Settings)** = balanced Tier 1 maturity at single-phase budget。Tier 2 promotion path for both options is clear and incremental。

### 3.6 Wave C2 trigger conditions(only if Option A picked for either ADR)

If Chris picks Option A for ADR-0026 OR ADR-0027(or both):**must split Wave C** into C1 + C2 sub-phases per CLAUDE.md §10 R1 rolling JIT。Trigger:Wave C plan-day budget > ~10 days = split。**Decision flag for F6**:if Option A pick,W22 phase folder is W22-frontend-wave-c1 not W22-frontend-wave-c;C2 phase kickoff post-C1 closeout decision per rolling JIT。

---

## §4 Wave D — Tier 2 hold(post-Beta launch governance Q12)

### 4.1 Scope

8 `/labs/*` pages per F1.3 Labs disposition:
- `/labs-graph-rag` — GraphRAG / Knowledge Graph retrieval
- `/labs-agents` — Multi-Agent orchestration L4+
- `/labs-languages` — JP/ZH multi-language
- `/labs-voice` — Voice I/O(Web Speech API + Azure CogServ Speech)
- `/labs-finetune` — Custom fine-tune training pipeline(NEW C14)
- `/labs-workflows` — Workflow builder canvas(NEW C15)
- `/labs-personalization` — Per-user retrieval ranking boost
- `/labs-tenancy` — Multi-tenancy

### 4.2 Wave D disposition

**Recommend Option C(per W19 F1.5 F5.4)— prototype-only,don't ship `frontend/`**。Tier 2 governance Q12 post-Beta launch triggers:
- Promote specific Lab(per stakeholder Q12 decision)to active feature → new Wave-equivalent phase
- Add new C14 / C15 / C16-onwards components per `COMPONENT_CATALOG.md` §6 Tier 2 Future Slots

### 4.3 Wave D **NOT pre-created**

Per CLAUDE.md §10 R1 rolling JIT — no W23+ phase folder created until governance Q12 trigger fires and specific Lab is promoted。

---

## §5 Dep ordering

```
┌─────────┐
│ Wave A  │ ─────── parallel ──────► ┌─────────┐
│  W20    │                          │ Wave B  │
│ 1.5-2w  │                          │  W21    │
└────┬────┘                          │  ~1w    │
     │                               └────┬────┘
     │                                    │
     ▼                                    ▼
  closes                              closes
     │                                    │
     └────────────► merge ◄───────────────┘
                      │
                      ▼
                ┌─────────┐
                │ Wave C  │ — requires Wave A close(Settings UserMenu nav from <AppShell> + Access tab activation needs ADR-0027 RBAC infrastructure)
                │  W22    │
                │ ~1.5-2w │
                └────┬────┘
                     │
                     ▼
                  closes
                     │
                     ▼
               ┌──────────┐
               │ Production │
               │  launch    │
               │ gate       │ — pending Track A IT cred populate event + R-B1 closure(W16 F1)— parallel track
               └──────────┘
                     │
                     ▼
                 Q12 trigger
                     │
                     ▼
              ┌─────────────┐
              │ Wave D       │
              │ NOT pre-created │
              │ per Lab promotion │
              └─────────────┘
```

**Key dep facts**:
- Wave A + Wave B **can run in parallel**(disjoint surfaces;both depend on W18 chrome + F3 ADRs only)
- Wave C **needs Wave A close**(Settings nav from `<AppShell>` `<UserMenu>` + Access tab activation depends on Wave C RBAC infrastructure)
- Wave D **requires Beta launch first**(Q12 governance trigger post-launch)

---

## §6 Per-Wave H4 boundary policing(consume F5 catalog)

See `audit/W19-tier2-disabled-affordance-catalog.md`(F5)for full per-affordance handling spec。Summary by Wave:

| Wave | Tier 2 disabled affordances in scope |
|---|---|
| Wave A | Topbar language toggle / Login Forgot password / Multimodal Vision captioning + Render PDF + low_value vision + Perceptual dedup / Quick Actions API access disabled / Topbar Workspace switcher disable / Sidebar Labs section recommend hidden |
| Wave B | Embedding vector preview(Tier 2 conditional)|
| Wave C | `/users` Power User role + Custom roles + Groups + Audit log / `/kb/[id]` Access Public visibility + Anonymous API key / `/settings` API Keys Incoming + Identity Power User mapping + Distributed token cache(Redis)+ Account Delete account + Sign-in policy MFA all roles |
| Wave D | All `/labs/*` 8 pages |

---

## §7 Final F4 recommendation

1. **Adopt 4-Wave structure**:W20-frontend-wave-a / W21-frontend-wave-b / W22-frontend-wave-c / Wave D Tier 2 hold(Q12 trigger)
2. **Wave A + B parallel**;Wave C sequential after A;Wave D Tier 2 reserved
3. **Per F2+F3 recommendation**:Chris picks Option C(ADR-0026)+ Option B(ADR-0027)+ Option A(ADR-0031)at F6 → Wave C fits single phase
4. **Wave C2 trigger** documented for option-A scenarios(if Chris picks differently — graceful split path)
5. **Wave A ships 7-tab KB Detail**(`-Access`,Access tab disabled affordance)— Access tab activates Wave C with RBAC infrastructure
6. **Wave A ships ADR-0030 + ADR-0032 absorbed**(Dashboard polish + Trace 3 viz + /traces list + Workspace switcher disable + Sidebar Labs hidden)without separate ADR
7. **Mock-auth default through Wave C**;real-MSAL feature-flagged ship Wave C concurrent per user 岔口 2
8. **Track A IT cred parallel track**(W16 F1)— independent of W20-W22;if cred lands by Wave C start = real-MSAL fully activates;if not = feature-flag stays off,mock-auth default continues post-Wave C until cred lands(per user 岔口 2 decision)

---

**Next deliverable**:F5 Tier 2 disabled-affordance catalog → `audit/W19-tier2-disabled-affordance-catalog.md`
