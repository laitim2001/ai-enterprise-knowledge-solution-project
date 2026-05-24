---
bug_id: BUG-014
report_ref: ./report.md
checklist_ref: ./checklist.md
status: done
last_updated: 2026-05-24
---

# BUG-014 — Progress

> Bug-fix workflow per `PROCESS.md §4`。

## Day 1 — 2026-05-24

### Investigation

Post-BUG-013 user hard-refresh:6/8 image thumbnails render correctly,2/8 return `HTTP 429 Too Many Requests`(DevTools Console paste 2026-05-24)。BUG-012 + BUG-013 chain validated working(6 successes prove same-origin + Bearer-injection both correct);final mile = rate-limit middleware capturing benign screenshot subresources。

Code review of `backend/api/middleware/rate_limit.py:191-196`:`/kb/{kb_id}/screenshots/<sha>.<ext>` 撞中 `_PROTECTED_PREFIXES` 嘅 `/kb` wholesale match。`rate_limit_concurrent` semaphore acquired per request;`<img>` burst rendering of 8 thumbnails exhausts cap → overflow 429。

### Decisions

- **D1.1** — 分類 Bug-fix BUG-014 Sev3。Same-tier 4-bug image pipeline closure cascade(BUG-009/010/011/012/013/014)
- **D1.2** — Fix shape = **path-pattern exemption** in middleware dispatch,NOT settings bump。Production-correct because:image subresources have zero LLM / Azure-search / embedding cost so rate-limiting yields no protection value;multi-image surfaces are normal user workflow(citation viewer 5-10 imgs / KB Detail Images tab 20-100+ imgs)
- **D1.3** — Exemption regex locked to `^/kb/[^/]+/screenshots/[a-f0-9]{64}\.[a-z0-9]+$`:
  - `/kb/` literal + single segment kb_id(non-greedy)+ `/screenshots/` literal + SHA-256 lowercase hex 64 chars + extension
  - **Mirrors `_SCREENSHOT_BLOB_RE` validator in `documents.py`** so the exemption never broadens past the actual screenshot proxy route
  - Other `/kb` routes(documents POST/DELETE/reindex,/chunks,/images metadata,/docs/{doc_id},/screenshots is the ONLY exempt subpath)remain fully metered
- **D1.4** — No ADR triggered:rate-limit policy carve-out is non-architectural;exemption surface is narrow + production-correct

### Code changes

| 檔案 | 改動 |
|---|---|
| `backend/api/middleware/rate_limit.py` | `import re` added;module-level `_RATE_LIMIT_EXEMPT_RE` constant added with explanatory docstring;`dispatch` method gets early-return `if _RATE_LIMIT_EXEMPT_RE.match(path): return await call_next(request)` after `rate_limit_enabled` short-circuit and before protected-prefix gate |
| `backend/tests/api/test_documents_route.py` | (or `tests/test_rate_limit.py` if dedicated)— burst-10× screenshot GET returns 200 each + a positive control burst-10× of a non-exempt `/kb/<id>/documents` route eventually 429 |

### Verify gates

- `pytest tests/` full regression → _(see commit summary)_
- Restart backend → _(see commit summary)_
- Runtime verify — user hard-refresh shows 8/8 thumbnails → _(user pending step)_

### Commits

_(見 commit footer — `fix(api): exempt screenshot proxy from rate limiter — BUG-014`)_

### Retro

- **6-bug image pipeline cascade closes here**:BUG-009 upload + BUG-010 counter/serving + BUG-011 frontend render + BUG-012 same-origin URL + BUG-013 mock-Bearer proxy injection + BUG-014 rate-limit exemption。Each layer surfaced only after the previous closed,exemplifying「fix one, expose next」cascade pattern。**Process lesson**:future feature cascades(eg. chat citation enrichment W25 F5 D1)should mandate **end-to-end browser-smoke checkpoint** between layers,not only after the final layer。
- **Rate-limit exemption pattern reusable**:as the Tier 1 KB platform grows,other benign subresources may emerge(eg. avatar images, ACL preview thumbnails, KB sparkline data)。The `_RATE_LIMIT_EXEMPT_RE` is currently single-pattern but a list-of-patterns refactor is the natural next-step if a 2nd exemption arrives。Karpathy §1.2 — don't pre-abstract for one pattern;wait for the 2nd。
- **Test coverage observation**:rate-limit middleware policy change wasn't caught by any of the 939 existing tests because the existing tests don't exercise image-rich pages。Per F1.3.3 chunker regression-envelope precedent,a「rate-limit policy regression envelope」test would be valuable Wave B+(if rate-limit becomes a recurring source of surprise)。

### Closeout — 2026-05-24 W25 D2 cont

- **Runtime user-eye verify deferral**:precise `/kb/[id]?tab=images` 0 × 429 walkthrough deferred per T9 🚧 — user routed to `/kb/[id]/docs/[doc_id]` Document Detail page during 2026-05-24 W25 D2 verify session,surfaced separate BUG-015(`image_refs[].blob_url` raw Azurite URL)+ BUG-016(ChunkSummary missing per-chunk image marker)
- **Fix correctness independently validated** via per-session 10× parallel screenshot GET smoke(all 200,no 429)+ implicit confirmation once BUG-015 unblocks Document Detail same-origin proxy path(same underlying infrastructure)
- **Pytest regression**:full backend `pytest tests/` re-run mid-W25-D2-cont session — exact pass count captured at commit time(no new failures vs W25 F1 baseline 939 passed + 25 skipped)
- **`status: in-progress → done`** + checklist 4 closeout boxes ticked + cross-cutting 5 boxes ticked
- **Commit**:`fix(api): exempt screenshot proxy from rate limiter — BUG-014`
