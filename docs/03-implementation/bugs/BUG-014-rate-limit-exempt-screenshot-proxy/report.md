---
bug_id: BUG-014
title: "Rate limiter applies to /kb/{kb_id}/screenshots/{sha}.{ext} → parallel <img> GETs hit 429 on the last requests when page renders multiple thumbnails"
severity: Sev3
status: done
reported: 2026-05-24
reporter: "Chris(chat 2026-05-24 — post-BUG-013 hard refresh:6/8 images rendered + 2/8 GETs returned 429 Too Many Requests)"
affects_components: [C08]    # API Gateway — rate limit middleware
spec_refs:
  - architecture.md §4.6     # screenshot blob serving
  - architecture.md §7       # rate limiting + abuse protection
related: [BUG-010, BUG-011, BUG-012, BUG-013]
---

# BUG-014 — Rate limiter throttles benign screenshot subresource GETs

> **Report version**:1.0(initial)
> **Triage approver**:AI self-triaged Sev3;Chris chat-acknowledged via 6/8 + 2× 429 paste 2026-05-24。

## 1. Symptom

User hard-refresh `/kb/sample-document-with-image-1?tab=images` after BUG-012 + BUG-013 fix。**6/8 image thumbnails render correctly**(BUG-012/013 chain validated working);**remaining 2/8 GETs fail with HTTP 429 Too Many Requests**(DevTools Console paste 2026-05-24)。

## 2. Reproduction Steps

1. Re-ingest a KB with ≥ 8 embedded images per doc(typical corporate docx with figures)
2. Visit `/kb/<kb_id>?tab=images` → `<ImagesTab>` renders an 8-cell grid + each cell mounts a `<ImageCard>` with `<img src=/api/backend/.../screenshots/<sha>.png>`(BUG-011 render + BUG-012 same-origin URL)
3. Browser fires 8 GETs concurrently(typical 6-parallel + 2-queued under HTTP/1.1 per-origin connection limit;or all-parallel under HTTP/2 multiplexing)
4. Backend `/kb` prefix is in `_PROTECTED_PREFIXES`(`server.py:223`)→ rate limiter `acquire/release` per request
5. The `rate_limit_concurrent` semaphore reaches its cap when 6-8 requests in-flight → next requests get 429

**Reproduction reliability**:Always — once a KB has > N images where N = `rate_limit_concurrent`(or ≤ N + browser HTTP/2 multiplexing rapid burst)。

## 3. Expected vs Actual

| 範疇 | Expected | Actual |
|---|---|---|
| Image subresource GETs | Pass through unmetered(benign,no LLM / no Azure search / no embedding cost)| Metered against the same bucket as `/query` + `/kb` POST mutations |
| User-visible result on 8-image page | 8/8 thumbnails render | 6/8 render + 2/8 placeholder fallback(BUG-011 onError → gradient)|

## 4. Impact

**Production-relevant** — not dev-only:
- Citation viewer(chat `<ImageGallery>`)future-typically render 5-10 citation images per chat turn
- KB Detail Images tab renders all images of a KB(can be 20-100+ for real corpus)
- Any page with parallel image subresources hits the same wall

**Symptoms scale with image count** — small KBs(<6 imgs)never trigger;medium KBs (~8 imgs)show partial drop;large KBs(20+ imgs)show majority drop。

- **Affected users / scenarios**:every user once the multi-image surface lands(W25 F5 D1 citation post-process + Wave B+ doc-detail viewer)
- **Workaround available?**:No(user can't influence rate limit)
- **Data loss / corruption?**:No
- **Security implication?**:No — exemption surface is GET-only,private blob(BUG-010 proxy preserves auth)
- **Cost implication?**:None — image bytes 喺 Azurite local OR Azure Blob production both have no LLM / no semantic-search cost

## 5. Severity Justification

**Sev3** per `PROCESS.md §4.5`:user-visible image-rendering regression but text retrieval / Gate 1 / chat 文字 unaffected。No data loss、no security regression(if anything exemption slightly tightens noise from rate-limiter for benign GETs)。Same tier as BUG-010/011/012/013。

## 6. Initial Diagnosis(root cause confirmed)

`backend/api/server.py:223`:
```python
_PROTECTED_PREFIXES = ("/query", "/kb", "/feedback", "/auth")
```

`/kb/{kb_id}/screenshots/{sha}.{ext}` matches `/kb` prefix wholesale。`backend/api/middleware/rate_limit.py:191-196` dispatch:

```python
path = request.url.path
if not any(path == p or path.startswith(f"{p}/") or path == p for p in self._prefixes):
    return await call_next(request)
# also match exact prefix without trailing slash (e.g. "/kb")
if not any(path.startswith(p) for p in self._prefixes):
    return await call_next(request)
```

Both conditions pass → semaphore acquire → on capacity exhaustion → 429。

`_RateLimiter` settings(`storage/settings.py`):`rate_limit_per_minute` + `rate_limit_concurrent` — the concurrent cap is what 8 parallel `<img>` GETs trip。

**Fix shape**:add **path-pattern exemption** for the screenshot proxy subpath。Cleanest implementation = additional pre-check in `RateLimitMiddleware.dispatch` before the prefix gate:

```python
_RATE_LIMIT_EXEMPT_RE = re.compile(r"^/kb/[^/]+/screenshots/[a-f0-9]{64}\.[a-z0-9]+$")

# In dispatch, before the protected_prefix check:
if _RATE_LIMIT_EXEMPT_RE.match(path):
    return await call_next(request)
```

Exemption surface narrow:
- `^/kb/`:KB-scoped
- `[^/]+`:single kb_id segment(not multi-segment)
- `/screenshots/`:literal subpath fixed by `documents.py:269` route
- `[a-f0-9]{64}\.[a-z0-9]+$`:SHA-256 lowercase hex + extension(matches the existing `_SCREENSHOT_BLOB_RE` validator in `documents.py`)

**No bypass for arbitrary `/kb/<id>/<anything>`** — only the precise screenshot blob shape exempt。Other `/kb` routes(POST /kb/{kb_id}/documents upload + DELETE + reindex + chunks + images metadata + …)仍 fully metered。

非架構 / vendor / storage-layout 改動(rate-limit policy carve-out)→ **唔觸發 H1 / H2,唔需 ADR**。

## 7. Acceptance for Fix(checklist preview)

- [ ] Root cause confirmed:`/kb/.../screenshots/<sha>.<ext>` matches `/kb` rate-limit prefix → 8 parallel `<img>` GETs exhaust `rate_limit_concurrent` semaphore → 429 on overflow
- [ ] **Fix** — `backend/api/middleware/rate_limit.py`:add module-level `_RATE_LIMIT_EXEMPT_RE` + early-return in `dispatch` before protected-prefix check
- [ ] Tests — `tests/api/test_rate_limit.py`(or middleware-level test) add:(a) `/kb/<id>/screenshots/<sha>.png` repeat 10x in burst returns 200 each(not 429)+ (b) regression: `/kb/<id>/documents` POST still metered as before
- [ ] Verify gates — `pytest tests/` 0 fail vs current baseline 939
- [ ] Runtime verify — user hard-refresh `/kb/<kb_id>?tab=images` → 8/8 thumbnails render + Network 8 × 200

## 8. Alternatives Considered

| # | Alternative | Pros | Cons | Verdict |
|---|---|---|---|---|
| 1 | Bump `rate_limit_concurrent` from default to higher value | One-line settings tweak | Doesn't scale to large image-rich pages;treats benign GET same as expensive query | Rejected — bandage |
| 2 | Add HTTP `Cache-Control: max-age=...` to screenshot Response | Browser de-duplicates repeat GETs across refresh | Same-page parallel GETs are concurrent(no benefit);cache poisoning risk if blob churns | Rejected — different problem |
| 3 | Frontend serial-stage `<img>` loads | Reduces parallelism | UX regression(staircase loading);per-component change everywhere | Rejected — defies browser native parallelism |
| 4 | **Pattern-exempt screenshot proxy at middleware level**(this report)| Production-correct;surgical;narrow regex;no settings dependency;handles all parallel rendering surfaces uniformly | Adds one pattern check on every request hot path(negligible — compiled regex)| **Selected** |
| 5 | Disable rate limiting in dev only via settings | Quick dev unblock | Doesn't solve production-time risk(citation viewer hits same wall in prod)| Rejected — production-symptom present |

## 9. Report Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-24 | Initial triage(Sev3)— post-BUG-013 user shows 6/8 + 2× 429;cascade closure 4-bug chain ends here | Image-pipeline closure final mile | Chris(chat-confirm 2026-05-24)|

---

**Lifecycle reminder**:Sev3 → `postmortem.md` 不需要(only Sev1/Sev2 mandatory per `PROCESS.md §4.5`)。
