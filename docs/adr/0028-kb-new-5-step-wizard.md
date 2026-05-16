# ADR-0028: /kb/new 5-step wizard + Multimodal Tier 1/2 split + /kb-upload re-ingestion coexistence

**Date**: 2026-05-16
**Status**: **Accepted**(W19 F6 Chris approval 2026-05-16 — consensus decision)
**Approver**: Chris(Tech Lead + stakeholder)

## Context

`architecture.md v6 §5.5.3` 原 spec — Pipeline Wizard = **3-step** INSIDE KB Detail Pipeline tab:DATA SOURCE → DOCUMENT PROCESSING → EXECUTE。

`references/design-mockups/ekp-page-kb-new.jsx PageKbNew`(per W19 F1 audit) implements:

1. **Standalone `/kb/new` 5-step wizard** for new KB creation:Identity → Format & chunking → **Multimodal** → Retrieval defaults → Review
2. **`/kb-upload/[id]` 3-step wizard** for re-ingestion into existing KB(`ekp-page-misc.jsx PageUploadWizard`):Data source → Document processing → Execute

**Two distinct flows**:
- `/kb/new` = **new KB provisioning**(creates Azure AI Search index `ekp-kb-{kb_id}-v1` + Blob container per ADR-0018;captures identity + locked config + multimodal preferences + retrieval defaults + review)
- `/kb-upload/[id]` = **re-ingestion into existing KB**(adds documents to existing index;reuses KB-locked chunker + embedder)— spec §5.5.3 Pipeline Wizard equivalent

The Multimodal Step(`StepMultimodal` lines 103-312)mixes **Tier 1 active** options + **Tier 2 disabled affordances**:

**Tier 1 active**:
- `extract_embedded_images` — Docling extracts inline PNG/JPG from .docx + .pdf;python-pptx pulls picture shapes from .pptx
- `dedup_strategy: sha256` — cross-document SHA256 dedup per `ingestion/screenshots/extractor.py`
- `return_images_in_chat` — UI behavior toggle(backend `/query` always returns `embedded_images`,this controls chat-UI rendering preference)
- `slide_screenshots` — labeled `tier2` in prototype OptionRow,but considering active per ADR-0028(see Decision below)

**Tier 2 disabled affordance**:
- `captioning_model: gpt-5.5-vision | azure-doc-intel | off` — vision captioning to auto-fill empty alt_text(off = source alt_text only is Beta default);**Tier 2** per §11
- `render_pdf_pages` — page-as-screenshot for layout-critical PDFs;**Tier 2**(triples ingestion time + Blob storage)
- `low_value_threshold` — image-level vision classifier(distinct from chunk-level low_value_flag already present);**Tier 2**(needs vision classifier)
- `dedup_strategy: perceptual` — perceptual hash fuzzy match;**Tier 2**

**Prototype inconsistency**:comment says "4-step" but `steps[]` array has **5 entries**(prototype line 38-44);Step 1 footer reads "Step 1 of 4" inconsistent。Audit per W19 F1 §2.1 D4 flagged for ADR-0028 to clarify final step count + footer text。

Per CLAUDE.md §5.1 H1 — `architecture.md v6 §5.5.3` route topology + step composition change = architectural → requires ADR。

## Decision

Adopt the **5-step `/kb/new` wizard + 3-step `/kb-upload/[id]` re-ingestion** dual-flow per prototype。Amend `architecture.md v6 §5.5.3` Pipeline Wizard:

1. **Distinguish two flows**:
   - **§5.5.3a New KB wizard**(`/kb/new` 5-step):Identity → Format & chunking → Multimodal → Retrieval defaults → Review。**Locked-after-creation** fields:kb_id / embedding_model / embedding_dimension / chunk_strategy / multimodal extraction config(changing requires new KB / re-index)。**Editable** fields:name / description / default_top_k / default_rerank_k / return_images_in_chat。
   - **§5.5.3b Re-ingestion wizard**(`/kb-upload/[id]` 3-step):Data source → Document processing → Execute。Reuses KB-locked chunker + embedder。Document processing step exposes per-batch override(chunk_strategy + chunk_size + chunk_overlap)but KB-default reflected。

2. **Multimodal Step Tier 1/2 boundary explicit**:
   - **Tier 1 active**:`extract_embedded_images`(default `true`)+ `slide_screenshots`(default `true` for .pptx-heavy KBs — promote from prototype's "tier2" label to active since python-pptx slide extraction is C01 W2 implemented)+ `dedup_strategy: sha256`(only Tier 1 option)+ `return_images_in_chat`(UI behavior toggle)
   - **Tier 2 disabled affordance with coral "TIER 2" badge**:captioning_model options(GPT-5.5 Vision + Azure Doc Intelligence)/ `render_pdf_pages` / `low_value_threshold` / `dedup_strategy: perceptual`

3. **Fix prototype inconsistency**:5-step wizard,Step N footer reads "Step N of 5"(not "of 4")。Prototype `ekp-page-kb-new.jsx PageKbNew.steps[]` array(line 38-44)is correct;footer text in `StepIdentity` line 389 needs fix(prototype docs note as "comment says 4-step but actually 5 steps" per W19 F1 §2.1 D4 flag)。

4. **Backend additions**(per W19 F2 §3.1 item 2):
   - `KbConfig` schema(`backend/api/schemas/kb.py:9`)ADD multimodal Tier 1 fields:`extract_embedded_images: bool = True` + `slide_screenshots: bool = False` + `dedup_strategy: Literal["sha256"] = "sha256"` + `return_images_in_chat: bool = True`
   - Tier 2 multimodal fields **NOT added** to schema(disabled affordance frontend-only — backend doesn't accept them per H4 boundary policing)
   - `KbCreate` schema(`backend/api/schemas/kb.py:17`)— no change(already accepts `config: KbConfig`)
   - `POST /kb`(`backend/api/routes/kb.py:54`)— no change(already provisions index per body)

## Alternatives Considered

1. **Keep 3-step inside KB Detail Pipeline tab**(spec §5.5.3 original) — rejected。Creating a brand-new KB vs re-ingesting an existing KB are different flows with different user mental models(identity + locked config + multimodal preferences for new KB;just doc upload + chunker override for re-ingest)。Conflating them in one wizard makes the "identity + locked config" capture awkward for new KB + irrelevant for re-ingest。
2. **Drop Multimodal step entirely + put options in Settings**(separate concern) — rejected。Multimodal config decisions are inherently per-KB-creation(image extraction is part of the ingestion pipeline locked at KB provision time per ADR-0018 + W2 multi-format ingestion design)。Settings is for cross-KB or per-user concerns(theme + auth + providers per ADR-0026).
3. **Adopt 4-step wizard(drop Multimodal step,bake into Format & chunking step)** — considered。Reduces wizard length but loses the "image pipeline education" surface(prototype's Multimodal step has a 5-step pipeline hero explainer:Parse → Caption → Dedup → Bind to chunks → Index)which is high-value onboarding for operators new to multimodal RAG。Decision:keep 5-step,merge consideration deferred to post-Beta UX review。
4. **All Multimodal options Tier 1 active**(promote captioning + render PDF pages + low_value vision filter + perceptual dedup) — rejected per H4 boundary policing。Vision captioning model(GPT-5.5 Vision + Azure Doc Intelligence)is genuinely Tier 2 — needs new C? component or large C01 extension + cost-per-image impact(~$0.001-0.002/img × thousands of images per KB)。Defer per §11 Tier 2 trigger matrix。
5. **All Multimodal options Tier 2 disabled**(only extract_embedded_images + sha256 dedup active) — rejected。Slide screenshots for .pptx is implemented(python-pptx W2 + ADR-0003 multi-format ingestion);marking as Tier 2 disabled would be a regression from current capability。Promote `slide_screenshots` from prototype's "tier2" label to active per Decision §3。

## Consequences

**Positive**:
- Two-flow design preserves user mental models(new KB = identity + locked config commit;re-ingest = doc-only upload)
- 5-step wizard's Multimodal step is the operator's primary touchpoint for understanding the image-text retrieval pipeline(5-step hero explainer + per-option warn text + outcome preview)— high-value onboarding for non-multimodal-RAG-experienced operators
- Tier 1/2 boundary explicit:operators see what's coming(coral "TIER 2" badge + tooltip)without confusing it with current capability
- Backend changes minimal(`KbConfig` add 4 fields + Tier 2 fields stay frontend-disabled-affordance only)
- Both wizards consume existing endpoints(`POST /kb` for new + `POST /kb/{kb_id}/documents` for re-ingest per CH-001 closed 2026-05-12)— no new endpoint required for the wizards themselves

**Negative**:
- 5-step wizard may feel long for first-time KB creation;UX trade-off accepted per operator-onboarding value
- Slide screenshot promotion(prototype tier2 → Tier 1 active per Decision §3)is a small spec deviation from prototype labeling — surface in F4 Wave A documentation to confirm with stakeholder + adjust prototype OptionRow `tier2={false}` for slide_screenshots if desired
- `KbConfig` schema addition impacts existing KbCreate payloads — backward-compatible via Pydantic field defaults(existing prod data without multimodal fields gets defaults applied),no migration needed for in-memory mode;Postgres-backed mode(per ADR-0023)needs schema migration but additive

**Neutral**:
- `architecture.md v6 §5.5.3` 3-step → 5.5.3a 5-step new KB + 5.5.3b 3-step re-ingest amendment inline-tagged at W20-frontend-wave-a kickoff
- `COMPONENT_CATALOG.md` C09 KB cluster row(new KB wizard + re-ingest wizard)+ C01 Ingestion row(KbConfig multimodal fields)scope notes
- Prototype inconsistency fix(Step 1 of 4 → Step 1 of 5)is a small frontend mockup edit — not a real `frontend/` deliverable but worth documenting for Wave A implementer

## References

- `architecture.md v6 §5.5.3` Pipeline Wizard(3-step original spec)+ §3.3 Multi-format ingestion + §11 Tier 2 trigger matrix
- `references/design-mockups/ekp-page-kb-new.jsx`(`PageKbNew` lines 6-101;StepIdentity lines 350-396;StepConfig lines 398-491;StepMultimodal lines 103-312;StepDefaults lines 493-538;StepReview lines 540-583)
- `references/design-mockups/ekp-page-misc.jsx`(`PageUploadWizard` 3-step lines 4-67;StepDataSource lines 69-158;StepDocumentProcessing lines 160-235;StepExecute lines 237-305)
- W19 F1 audit §2.1 D4(5-step wizard + Multimodal Tier 1/2 mix + `/kb-upload/[id]` coexistence)
- W19 F2 backend gap map §3.1 item 2(KbConfig multimodal Tier 1 fields)+ §2.1 row 4 + row 7
- ADR-0018 Multi-KB kb_id propagation(per-KB index name `ekp-kb-{kb_id}-v1` provisioned at /kb POST)
- ADR-0003 Multi-format ingestion(Docling + python-pptx + slide_screenshots Tier 1 implementation basis)
- CH-001 per-doc upload/reindex/delete closed 2026-05-12(`/kb-upload/[id]` execute step backend)
- Q19 embedding_dimension 1024d MRL truncate baseline(W2 D3)
