# ADR-0053: Synthesizer request timeout 由 30s 上調至 120s(mega-section synth timeout / DD-7)

**Date**: 2026-06-11
**Status**: Accepted
**Approver**: 用戶(laitim)

## Context

W59 image-recall baseline(2026-06-10)量度 AR 收款手冊圖密 query 時,Q001/Q036(預期 65 圖,含
S04 mega-section 44 圖)喺 production default `synthesizer_request_timeout_s=30.0`(`settings.py:140`)
下穩定觸發 `APITimeoutError`,streaming path 表現為 chat「Thinking…」hang。量度時用
`.env SYNTHESIZER_REQUEST_TIMEOUT_S=180` 繞過先取得數,但 production 30s 路徑風險未解 → 登記為
**DD-7**(`DEFERRED_REGISTER.md`)。

DD-7 close 條件係「評估 production timeout 上調 vs mega-section context 縮減」。2026-06-11 用 code
驗證根因,**否決 context 縮減方向**:

- **image bytes 從不進 synth prompt** — `prompt_builder.build_prompt`(`prompt_builder.py:151`)只組
  text(`chunk_text` / `expanded_text` / `parent_section_text`),`synthesizer.synthesize_stream`
  傳俾 `chat.completions.create` 嘅 `messages` 純文字。圖片只活喺 retrieval / citation 層。→ 縮 image
  對 synth 負擔零幫助。
- **真因 = output-bound generation 時間** — 圖密 mega section 對應多步 procedure,detailed answer 要逐步
  列舉 → output token 多 + GPT-5.5 reasoning → ~90-98s(settings.py 既有註解 + W59 實測一致)。圖片數
  只係 proxy(圖密 section = 步驟多 = 答案長)。
- **縮 text context 會 reverse DD-4** — 降 `citation_expansion_max_aux` / 關 `enable_parent_doc_retrieval`
  會犧牲 DD-4(ADR-0052)剛換來嘅 recall(W59 顯示 returned cap 本身已係 recall 天花板),且縮 input
  唔保證縮 output(query 仍要求列舉多步)。

**DD-4 疊加**:ADR-0052 flip(parent_doc ON + max_aux 2→10 + prefix_depth 0→1)令 text context 更重
→ 30s 風險面只會擴大。W59 baseline 喺 **pre-DD-4 舊 default** 下 Q001/Q036 已 timeout;flip 後更易觸發。

## Decision

`backend/storage/settings.py` `synthesizer_request_timeout_s` 由 `30.0` 上調至 `120.0`;同步
`backend/generation/synthesizer.py` constructor `timeout_s` default `30.0 → 120.0`(維持兩處 mirror
invariant,production path 用 settings 值,constructor default 係 bare fallback)。同步更新 settings 註解
記錄根因 + safety-net 性質 + 指向本 ADR。

**選 120s 理由**:安全覆蓋 W59 實測 mega query ~90-98s(留 ~20-30% margin),180s 屬 over-provision。
streaming path `text-delta` 逐 chunk yield(`synthesizer.py:288`),用戶逐步見字,故此值係 **stream 完成
嘅 safety-net 上限,非正常 query 嘅感知延遲** —— 正常 query 遠在此值下完成,上調無感。

**不改 retrieval / context 旋鈕**:DD-4 default 不動,per-KB / per-doc / per-query override 機制不變。

## Alternatives Considered

1. **mega-section context 縮減** — reject:經 code 確認方向錯(image 不進 prompt、reverse DD-4、縮 input
   不保證縮 output-bound 根因)。
2. **維持 30s 只 document** — reject:`.env` override 已存在但 production 圖密 query 仍 timeout,把責任丟
   俾每個部署手動設 `.env`,易漏 = 治標。
3. **timeout 納入 per-KB / per-query config** — defer(非 reject):最符合 per-KB 可調 product vision
   (memory `project_per_kb_tunable_config_vision`),圖密 KB 單獨調高、一般 KB 維持較低;但工程量需開新
   phase(R1),非本輪 surgical scope。登記為 DD-7 long-term 跟進。
4. **上調至 180s** — reject:over-provision;180s 係 W59 量度時嘅粗略 buffer,非實測需求;safety net 過大
   令真 hang 情境 fail 更慢。

## Consequences

- **Positive**:production 圖密 mega query(含 DD-4 flip 後加重嘅 context)唔再被 30s 攔腰斬;與
  DD-4 / W59「放寬 cap 提 recall」同向(唔犧牲 completeness);surgical(2 處 default + 註解)。
- **Negative**:真 hang(stuck 非進度)情境 fail 較慢(120s 才報錯)。緩解:streaming path partial output
  已逐步 deliver,用戶見到答案停滯可自行中止;synthesize()(非 stream)仍有 tenacity 3-retry,單次上限
  120s。
- **Neutral**:正常 query 感知延遲零變化(遠在 120s 下完成);`.env SYNTHESIZER_REQUEST_TIMEOUT_S`
  override 機制不變(dev/demo 仍可再調);per-KB timeout(Alternative 3)留 DD-7 future。

## References

- ADR-0052(DD-4 chat RAG 質素旋鈕 production flip — 加重 synth context、擴大本 timeout 風險面)
- ADR-0037(parent-doc retrieval — DD-4 flip 對象)
- `docs/01-planning/DEFERRED_REGISTER.md` DD-7(本 ADR close 佢)
- `docs/01-planning/CONFIG_PLATFORM_W43-W58_ROLLUP.md` §3.2(DD-7 登記)
- `docs/01-planning/W59-image-recall-metric/progress.md`(F4 baseline — Q001/Q036 30s timeout 實測)
- memory `project_per_kb_tunable_config_vision`(Alternative 3 long-term 方向)
- `backend/storage/settings.py:140` / `backend/generation/synthesizer.py:79`(改動點)
