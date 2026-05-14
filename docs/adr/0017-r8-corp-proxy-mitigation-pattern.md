# ADR-0017: R8 — Ricoh corp-proxy mitigation pattern (dependency-add discipline)

**Date**: 2026-05-10
**Status**: Accepted
**Approver**: Chris (Tech Lead — W17 F1 decision, AskUserQuestion 2026-05-10: keep psycopg + defer local verification + formalize ADR-0017)

## Context

Risk **R8** (Ricoh corp proxy — `RISK_REGISTER`) has now bitten **6 times** across the Tier 1 build (one of which overlaps with R9 — MCR DNS intercept on Docker image pull), each in the same shape: the corp proxy SSL-inspects outbound HTTPS and **intermittently truncates / resets large downloads** from PyPI, vendor CDNs, and `mcr.microsoft.com` Docker layer blobs, so `pip install <package-with-binary-wheel>` / `docker pull mcr.microsoft.com/...` / `npx playwright install` and similar fetches fail with `IncompleteRead` / `ECONNRESET` / `503 Service Unavailable` mid-stream, often not reliably resumable.

Cumulative occurrences:

| # | When | What blocked | How it was handled |
|---|---|---|---|
| 1 | W3 | Cohere — direct-API / Cohere-SDK path complications under the proxy | Path A Azure Marketplace + an `httpx` REST client (`retrieval/reranker/cohere.py`) — no `cohere` SDK dependency at all (Q5 Resolved / ADR-0012) |
| 2 | W13 | `pip install argon2-cffi` (C-extension wheel) | Switched to `hashlib.scrypt` (Python stdlib) — **ADR-0016** |
| 3 | W13 | `pip install azure-communication-email` (ACS SDK) | Lazy import inside `email_provider.py`; `feature_email_mock=true` / empty `acs_connection_string` → `ConsoleEmailProvider` stub; real ACS path raises a clear `EmailSendError` when the dep is missing (C13 / ADR-0014) |
| 4 | W15 D5 | `npx playwright install chromium` (~180 MB browser binary CDN `cdn.playwright.dev`) | `ECONNRESET` at 0%; deferred to user smoke / personal Azure dev tier (CO17); `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1` + system-Chrome `channel:'chrome'` workaround documented; `@playwright/test` itself (npm) installed fine — only the browser binary CDN is blocked. **Resolved 2026-05-13 via Plan B** — see "Plan B realised" below: the E2E suite runs green (15/15) against the system-installed Chrome, the 4 pixel-diff baselines are captured |
| 5 | W17 F1 | `pip install psycopg[binary]>=3.2` (3.6 MB binary wheel — ADR-0023 Postgres driver) | `IncompleteRead` then "Connection timed out" on retry; **this ADR's trigger**. Code shipped anyway (dep declared in `pyproject.toml`, lazily imported via `kb_management/factory.py` so an unset `DATABASE_URL` never touches it, in-memory path unaffected); local Postgres-path verification (CRUD tests + `mypy postgres_backend.py` + manual smoke) deferred to W18+ / a personal Azure dev tier per CO17. **Re-attempted 2026-05-13 — still blocked** (PyPI wheel download timed out, 5 retries; F1.5b stays deferred) |
| 6 | 2026-05-14 (post-W18) | `docker pull mcr.microsoft.com/azure-storage/azurite:latest` — Azurite Blob emulator image. Container layer blob `1a142d512ad8` from `southeastasia.data.mcr.microsoft.com` returned **`503 Service Unavailable` mid-stream on two consecutive attempts** with the same SAS URL (SAS expiry was in the future, so not a token-expiry issue). **Recurrence of R9** (MCR DNS intercept first observed W1 D1 — `RISK_REGISTER` R9) | **Plan B realised same session via Decision-rule #5 augmentation — native package-manager global install**: a previously `npm install -g`'d `azurite.cmd` was already present at `C:\Users\CLai03\AppData\Roaming\npm\azurite.cmd`; started directly via `azurite --location infrastructure/azurite-data --blobHost 0.0.0.0 --queueHost 0.0.0.0 --tableHost 0.0.0.0`. The native CLI uses the same `infrastructure/azurite-data/` location that the docker-compose service mounts as a named volume, so the two delivery paths are **data-interchangeable**. See "Plan B realised — Azurite via native npm" below |

The session-start.md §11 / W15 retro flagged ADR-0017 as **reserved**, with a formalization trigger of "5th cumulative occurrence OR vendor-decision pivot needed". The W17 F1 `psycopg` block is the 5th — and was also a vendor-decision pivot point (resolved 2026-05-10: keep `psycopg`, don't pivot to sqlite3). So both halves of the trigger are met. This ADR formalizes the pattern so future dependency additions don't re-discover it ad hoc.

(Note: `truststore.inject_into_ssl()` in `api/server.py` already addresses the *runtime* HTTPS leg — it makes `httpx`/`urllib3` honour the Windows cert store so the proxy's SSL inspection doesn't break live API calls. It does **not** help `pip` downloads, which is what R8 keeps blocking.)

## Decision

**Adopt the following dependency-add discipline. The plan author + implementer run it whenever a new third-party dependency is proposed; it is the standing R8 mitigation pattern.**

1. **Prefer stdlib over a dependency.** If a stdlib module covers the need acceptably (even less ergonomically), use it. Precedent: `argon2-cffi → hashlib.scrypt` (ADR-0016). This is the first thing to consider for any new dep.
2. **Prefer a managed-service REST path over a vendor SDK.** When integrating a cloud vendor, an `httpx` client against the documented REST endpoint avoids a heavy SDK dependency. Precedent: Cohere via Azure Marketplace REST, no `cohere` SDK.
3. **Make any unavoidable third-party dep optional + lazily imported.** If the dep is only needed when a feature/config is enabled, import it inside that branch (not at module load), and provide a graceful fallback (stub / clear error) when it's absent. Precedents: ACS SDK lazy import (`email_provider.py`); `psycopg` lazy import (`kb_management/factory.py` — unset `DATABASE_URL` never touches it; in-memory backend keeps working). This way an R8-blocked install doesn't break local dev / CI.
4. **Declare the dep in `pyproject.toml` / `package.json` even when it can't be installed under the proxy.** A real deploy environment (Azure pipeline, personal Azure dev tier per CO17, or after an IT-mirror is configured) will install it. Don't silently drop the dep — declare it, gate the code path, and document the local-install caveat in the plan/progress.
5. **For binary-heavy / CDN-fetched assets (browser binaries, large wheels, Docker image layers): try Plan B candidates in this order before deferring.** (a) **Existing system binary**: drive an already-installed system tool via vendor-supported channel selectors (Playwright `channel:'chrome'` against the corp-managed Chrome — see "Plan B realised — Playwright" below). (b) **Native package-manager global install** (`npm install -g`, `pip install --user`, `winget install`, `brew install`) — these flow through registry-metadata + smaller payloads that empirically pass the corp proxy when image-layer / large-wheel CDN downloads do not. Precedent: Azurite via `npm install -g azurite` sidesteps the blocked `mcr.microsoft.com` docker pull (occurrence #6 — see "Plan B realised — Azurite via native npm" below). (c) Only if (a) and (b) are not viable: **defer to a non-proxy environment** — document the skip-download env vars + personal Azure dev tier workaround and accept a PARTIAL-PASS for the proxy-bound verification (precedent: Playwright `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1` documented before Plan B (a) was realised; `pip install psycopg[binary]` still sits here — occurrence #5).
6. **Dev dependencies (test/lint/format/type tooling) are still exempt from the H2 ADR requirement** (per CLAUDE.md §5.2), but the same R8 caveats apply to *installing* them — note it if a dev-dep install is blocked.
7. **When a new dep is genuinely unavoidable, doesn't fit a stdlib/REST/lazy path, and its proxy-blocked install would block the work: STOP and ask** (per CLAUDE.md §5 / §13) — surface it as a vendor-decision pivot point.

This ADR does **not** supersede any vendor lock (§3.2 stack stays as-is) and does **not** require IT to change the proxy — it is a coding-discipline ADR. An IT-side fix (an internal PyPI/npm mirror that the proxy whitelists) would make most of this moot, and is tracked separately (out of scope here).

### Plan B realised — Playwright E2E via system Chrome (2026-05-13)

Decision-rule #5 ("defer binary-heavy / CDN-fetched assets to a non-proxy environment; document the system-binary-channel workaround; accept PARTIAL-PASS") has now been **executed** for the Playwright browser binary, on the corp dev box itself — no non-proxy environment needed, because the box already has a corp-managed **Google Chrome** installed:

- `frontend/playwright.config.ts` gained two opt-in env hooks: `PW_CHANNEL` (sets the chromium project's `channel`, e.g. `chrome`/`msedge`) and a derived `PW_VIDEO` (forced `'off'` when `PW_CHANNEL` is set, because `video:'retain-on-failure'` needs the **ffmpeg** binary which is in the same blocked `cdn.playwright.dev` bucket as the Chromium download). Both default to "unset" → bundled Chromium + video on, so **CI behaviour is unchanged**; this is purely a local escape hatch.
- `PW_CHANNEL=chrome pnpm test:e2e` → **15/15 green** (`app-shell-path.spec.ts` + `golden-path.spec.ts` + `visual-baseline.spec.ts`), including the new BUG-002 "no horizontal overflow at 375px" regression test. Two pre-existing stale test-selectors surfaced (they'd never run before — no browser) and were fixed: `getByLabel(/password/i)` → `getByLabel('Password',{exact:true})` (the register form has both Password + Confirm-password); `getByText(/cohere v4\.0-pro/i)` → `getByRole('cell',…)` (3 mentions on `/eval`); a brittle `[class*="step"]` stepper locator → `getByText(/step 1 of 3/i)`.
- `PW_CHANNEL=chrome pnpm test:e2e:update-snapshots` → the **4 pixel-diff baselines** committed under `frontend/tests/e2e/visual-baseline.spec.ts-snapshots/` (`v8-login` / `v9-register-step1` / `dashboard` / `v5-eval-console`, `*-chromium-win32.png`) — closes **CO_W15_F4_browser_binaries** + **CO_W15_F4_baseline_capture** (the W12-W18 "user pre-Beta browser smoke" backlog's automated portion).

What's **still** R8-blocked (no Plan B): `pip install psycopg[binary]` (PyPI wheel — re-attempted 2026-05-13, timed out) → **F1.5b** Postgres-path runtime smoke + `mypy postgres_*` stays deferred per CO17; `playwright install ffmpeg` (Plan-B runs just turn video off); `playwright install chromium` itself (the bundled binary — the system-Chrome channel sidesteps needing it).

### Plan B realised — Azurite via native npm (2026-05-14)

Decision-rule #5 (b) — "native package-manager global install" — has now been **executed** for the Azurite Blob emulator after the live `docker compose up -d azurite` blew up with `503 Service Unavailable` mid-stream on layer blob `1a142d512ad8` from `southeastasia.data.mcr.microsoft.com` (occurrence #6 above; same root cause as R9 MCR DNS intercept). Because `azurite` had previously been globally installed via `npm install -g azurite` (the CLI lives at `%APPDATA%\npm\azurite.cmd`), the docker pull was sidestepped entirely:

- `azurite --location infrastructure/azurite-data --blobHost 0.0.0.0 --queueHost 0.0.0.0 --tableHost 0.0.0.0 --silent` running as a host-side background process — `127.0.0.1:10000` returns `400` to an unsigned `GET /` (service alive, refusing the unauthenticated root request, exactly as a real Azurite container would).
- The data directory `infrastructure/azurite-data/` is the *same* path the docker-compose `azurite` service mounts as the `ekp-azurite-data` named volume, so blobs written by either delivery path are **interchangeable** — when the docker pull eventually goes through (IT mirror or a fresh `mcr.microsoft.com` CDN attempt), nothing in the data on disk needs to change. The path is already gitignored (`.gitignore` line under `# Local emulator data`).
- `AZURE_BLOB_CONNECTION_STRING` in `.env` is unchanged — the well-known `devstoreaccount1` account name + key + `127.0.0.1:10000` endpoint work for both the docker-served and native-CLI-served Azurite. Backend `backend/storage/blob.py` needs no code change.

`docker-compose.yml`'s Azurite service definition stays in the compose file (R9 may eventually decay when IT whitelists `mcr.microsoft.com`); a comment block above the service points readers to this Plan B, and `docs/setup.md §8.1` has a matching troubleshooting row. This entry closes the **R9 recurrence** observed 2026-05-14 — R9 itself stays open until IT whitelists MCR for CI / production-deploy pipelines (per `RISK_REGISTER` R9 "Decay date" = W7+ cloud deploy gate).

## Alternatives Considered

- **Don't formalize — keep handling R8 ad hoc each time** — rejected: 5 occurrences is enough signal that this recurs; an ad-hoc approach means each new dep re-discovers the same lessons (and risks someone adding a hard dep that breaks local dev / CI).
- **Wait for IT to provide an internal PyPI/npm mirror** — desirable but out of the team's control and not time-bound; this ADR doesn't block on it. If/when a mirror lands, this ADR can be amended/superseded.
- **Configure `pip` to use a corporate index now** — `pip config list` is empty (no mirror configured); setting one up is an IT task, not something the AI can do. Documented as the long-term fix.
- **Vendor everything (commit wheels into the repo)** — rejected: bloats the repo, license/security concerns, doesn't scale; the lazy-import + declare-anyway pattern (#3 + #4) achieves the goal without it.

## Consequences

- **Positive**: a written checklist the plan author / implementer runs for every new dep → fewer R8 surprises; the lazy-import + declare-anyway pattern keeps local dev / CI working even when an install is blocked; codifies the precedents (ADR-0016 stdlib, ACS lazy import, psycopg lazy import, Playwright deferral) so they're reused, not re-derived; clarifies that `truststore` covers runtime HTTPS but not `pip`.
- **Negative**: adds a step to the dependency-add flow; some deps that *would* be more ergonomic to add directly will instead get a stdlib/REST/lazy treatment (a small dev-ergonomics cost — the same trade ADR-0016 already accepted); the "declare-but-can't-install-locally" state means some verification (e.g. `mypy` on a module importing the blocked dep, integration tests needing it) is deferred to a non-proxy env — PARTIAL-PASS is the Tier 1 acceptance.
- **Neutral**: doesn't change the §3.2 vendor stack; doesn't require IT action; an IT-side mirror would supersede most of it later; the per-dep H2 ADR requirement (CLAUDE.md §5.2) is unchanged — this ADR is *additional* discipline, not a replacement for it.

## References

- `RISK_REGISTER` — risk R8 (Ricoh corp proxy)
- ADR-0016 — argon2-cffi → hashlib.scrypt (R8 occurrence #2, stdlib mitigation precedent)
- ADR-0014 — hybrid auth / C13 (ACS SDK lazy import — R8 occurrence #3)
- ADR-0012 — Cohere v4.0-pro (Azure Marketplace REST path — R8 occurrence #1)
- ADR-0023 — KB Manager persistent backing (psycopg — R8 occurrence #5, this ADR's trigger)
- session-start.md §11 — ADR-0017 reservation + 5th-occurrence trigger; CO17 (personal Azure dev tier pattern)
- `docs/01-planning/W15-polish-closeout/plan.md` §F4 risks (Playwright browser CDN — R8 occurrence #4)
- `docs/01-planning/W17-beta-hardening/progress.md` Day 2 (the psycopg block + this decision)
- `frontend/playwright.config.ts` — the `PW_CHANNEL` / `PW_VIDEO` Plan-B opt-ins (2026-05-13)
- `frontend/tests/e2e/visual-baseline.spec.ts-snapshots/` — the 4 captured pixel-diff baselines (CO_W15_F4_baseline_capture closed)
- CLAUDE.md §5.2 H2 (vendor / dependency constraint — dev-dep exception); §13 (when in doubt → ask)
- `backend/api/server.py` — `truststore.inject_into_ssl()` (runtime HTTPS cert-store leg)
- `RISK_REGISTER` R9 (MCR DNS intercept on Docker image pull — occurrence #6 is a R9 recurrence; R9's pre-existing mitigation "Azurite via npm distribution" is what this ADR's Decision-rule #5 (b) now codifies as the standing pattern)
- `infrastructure/docker-compose.yml` — Azurite service header comment points to Plan B (b)
- `docs/setup.md §8.1` — troubleshooting row for the blocked-`mcr.microsoft.com` case
