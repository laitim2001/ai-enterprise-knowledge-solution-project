# ADR-0043: Original-File Blob Storage + Real KB-Level Reindex

**Date**: 2026-06-04
**Status**: Accepted(W46-ingestion-config-and-reindex kickoff — Chris AskUserQuestion 揀「原始檔儲存 + UI 一次過(大 W46)」批准 H1 方向 2026-06-04;H7 frontend mockup design 為獨立 sub-gate,frontend code 前另需確認)
**Approver**: Chris(技術 Lead)

## Context

W45 / ADR-0042 令 `chunker_max_images_per_chunk` per-KB 可調;W43 / ADR-0040 令 retrieval 旋鈕 per-KB 可調。但 **ingestion 旋鈕**(`chunk_strategy` / 圖數 cap)改咗之後**要 re-index 先生效**(per ADR-0041/0042 — cap 喺切 chunk 時消耗)。而家:

- **UI 觸發嘅 reindex 做唔到**:`POST /kb/{kb_id}/reindex`(`kb.py:252-280`)係**純 stub**(假 task_id + note「pending Track A」)。
- **真 reindex 需要 re-parse 原始檔**:改 `chunk_strategy` / 圖數 cap = **重切** → 一定要由原始 `.docx/.pdf/.pptx` 重新 parse(stored chunks 係切完嘅 output,逆唔返)。
- **但系統唔存原始檔**(R6 grep 2026-06-04 核實):ingest 時 stream 落 tempfile、`finally` 即刪;Azure 只有 **一個** blob container = screenshots(`ekp-kb-{kb_id}-screenshots`),冇 source-document container。
- doc-level reindex(`documents.py` `reindex_document`)靠**用戶 re-upload** 原檔繞過;W43/W44/W45 KB 重建靠 **local populate script**(檔喺開發機 disk)。兩者都唔係 UI 自助。

∴ **原始檔儲存係成個自助 ingestion-config loop 嘅 enabler** —— 冇佢,per-KB chunk config(W42/W45 已開)永遠 apply 唔到 existing KB。

## Decision

加 **source-document blob 儲存** + 把 KB-level reindex 由 stub 串成真:

1. **NEW source-document blob container** —— ingest 時把原始上傳檔多存一份,keyed by (kb_id, doc_id)。Container 命名沿用 `kb_naming.py` convention:`ekp-kb-{kb_id}-sources`(平行於 `-screenshots`);blob name = `{doc_id}{ext}`。NEW `storage/kb_naming.py` helper `kb_id_to_source_container(kb_id)`。
2. **Ingest 持久化原始檔** —— `_run_ingest_pipeline` 成功 ingest 後把原檔 upload 落 source container(**best-effort + warning**,對齊 screenshot uploader pattern:source-upload 失敗唔 fail 個 ingest,只 log warning;該 doc 之後 KB-reindex 會 report「需 re-upload」)。
3. **真 KB-level reindex** —— `POST /kb/{kb_id}/reindex` 由 stub 改為:iterate `RetrievalEngine.list_documents(kb_id)` → 每個 doc_id 由 source container 攞返原檔 → 跑 ingest pipeline(delete 舊 chunks + re-ingest 同 doc_id)。**同步**(Tier 1 無 task queue;取代假 task_id 為真 summary `{reindexed:[...], skipped_no_source:[...], failed:[...], chunks_total}`)。冇 stored original 嘅 pre-W46 doc → **skip + report**(需 re-upload)。
4. **`_run_ingest_pipeline` refactor** —— 抽 core ingest(parse→chunk→embed→push)接受 **file path / bytes**,令 UploadFile 路徑(upload / doc-reindex)同 stored-blob 路徑(KB-reindex)共用,唔複製 pipeline 邏輯。
5. **Production-preserve** —— pre-W46 KB(冇 stored originals)行 KB-reindex 時 skip + 清楚 report「no stored source — re-upload required」;之後新 ingest 會存 original。零 breaking change(現有 upload / doc-reindex 路徑行為不變,只多一個 best-effort source-upload step)。

**H7 sub-gate(frontend,獨立確認)**:Settings tab 解鎖 ingestion config(`chunk_strategy` + W45 per-KB 圖數 cap)+ 加「Reindex KB」trigger UX + warning modal —— mockup 而家係 **locked design**(`ekp-page-kb.jsx:744-815` disabled + hint),**改 mockup = H7 STOP+ask**,frontend code 前另需 design 確認(per §5.7 + W18/ADR-0024 design-first precedent)。本 ADR 只 lock **H1 backend** 部分;H7 mockup design 喺 W46 plan 嘅 design gate deliverable 處理。`embedding_model` **維持 locked**(re-embed 全 KB 較重 + 1024d MRL 維度影響,out-of-scope W46;另起)。

## Alternatives Considered

- **v1→v2 索引原子切換** — DEFERRED:production 零 downtime reindex(舊 index 服務 + 新 index build 完 alias 切)需 net-new infra(`kb_naming.py` 固定 `-v1` 無 alias)+ Track A(Standard S1 + IT cred)。W46 dev 層做 **in-place per-doc delete+reingest**,接受 roadmap [AUDIT-C] 講嘅短暫不一致窗口。
- **Re-chunk from stored chunks(唔存原檔)** — REJECTED:stored chunks 係切完 output,逆唔返原始 parse(段落/標題/圖 by doc_order),改 chunk_strategy 必須重 parse。
- **Bulk re-upload UX(唔加 storage)** — REJECTED(Chris 揀 Option 4 storage):用戶要 re-supply 全 KB 檔,UX 笨拙 + 唔解 existing KB。
- **Source-upload 設 fatal on failure** — REJECTED:會令 Azurite/R8 短暫故障時連 ingest 都 fail;best-effort + warning 較穩(對齊 screenshot pattern),失敗 doc 之後 reindex report 出嚟。
- **Async task queue for KB-reindex** — DEFERRED:Tier 1 無 scheduler(per ADR-0017 風格),同步 reindex + summary 夠用;大 KB 慢可後補 progress streaming。

## Consequences

- **Positive**:
  - unblock 成個自助 ingestion-config loop —— W43 retrieval + W45 chunk cap + chunk_strategy 終於可 apply 落 existing KB(UI 觸發,唔使 re-upload)
  - doc-level reindex 都受惠(將來可由 stored original reindex,唔一定要用戶 re-upload — 雖然 W46 doc-reindex 路徑暫不改)
  - reuse `list_documents` + refactored pipeline,KB-reindex wiring 缺口收窄
- **Negative**:
  - storage 成本升(多存原檔 —— 但 manuals 細;可後加 retention policy)
  - in-place per-doc reindex 有短暫不一致窗口(舊 chunk 刪、新 chunk 未上)—— v1→v2 原子切換留 Track A
  - pre-W46 ingested doc 要一次 re-upload 先有 stored original(reindex 會清楚 report)
  - 同步 KB-reindex 對大 KB 會慢(blocking request)—— Tier 1 接受,progress streaming 後補
- **Neutral**:
  - production 零 downtime reindex 仍 Track A(本 ADR 唔關閉)
  - `embedding_model` unlock 留另起 phase

## References

- ADR-0042(W45 per-KB ingest-time chunker image cap — 本 ADR unblock 佢 apply 落 existing KB)
- ADR-0041(W44 chunker image-density — reindex required 性質)
- ADR-0040(W43 per-KB config-scope — retrieval 半邊;本 ADR 補 ingestion 半邊嘅 apply 機制)
- ADR-0023(KB Manager Postgres backing — KB metadata 持久化先例)
- ADR-0024(W18 unified shell IA — design-first mockup amendment precedent,H7 sub-gate 沿用)
- roadmap `ROADMAP-per-kb-tunable-config.md` §3「後續候選」(原 W45 UI ingestion 配置 + 真 reindex)+ [AUDIT-C] 兩層(dev in-place / prod v1→v2 + Track A)
- R6 grep 驗證 2026-06-04(KB-reindex stub `kb.py:252-280` / 單一 screenshots container / Settings tab locked `ekp-page-kb.jsx:744-815`)
- CLAUDE.md §5.1 H1(storage layout 改動 → ADR)+ §5.7 H7(mockup design change — frontend sub-gate)
