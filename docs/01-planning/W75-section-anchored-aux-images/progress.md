# W75 progress — section-anchored aux images(方案 A)

## Day 1 — 2026-06-14(kickoff)

**Context**:用戶開段②d「方案 A section 級錨定」。先 push-back「實測末尾堆殘餘量」(ADR-0056
roadmap conditional gate)→ 三輪 gate 全 PASS:
1. 末尾堆殘餘量(replay /query drive-images-1):單一文件 22-38% / 跨模組 55%(target 明顯存在)。
2. 章節級可錨率(`source_section[:1]` match 答案 anchored marker)= **100%**(全部 un-anchored 圖搵到同章節錨點)。
3. leaf section 可錨率 2-82%(query-dependent,靠 frontend `doc_order` sort 緩解)。
→ 用戶拍板「開 W75 phase build 章節級錨定」。

**R6 grounding(plan kickoff)**:
- un-anchored 來源確認 = `attach_neighbour_images`(`citation_image_neighbors.py`)post-synthesis 撈,
  synthesizer prompt 見唔到 → 永遠冇 marker → frontend `planAnchoredImages` 落 `trailing`。
- **H7 關鍵方向判斷**:採方向 1(backend marker 注入 post-attach)→ frontend `planAnchoredImages` /
  `parseInlineImageMarkers` 照常 parse,un-anchored 圖自動變 inline → **frontend 零改動 → H7 唔 trigger**。
  方向 2(frontend 改 render)= H7 trigger 要 mockup,不採。
- config knob 四層 mirror `enable_inline_image_markers`(settings:160 / effective_config:54+99+292 /
  kb:115 / doc_config:60)確認。
- profile gate via W73 PROFILE_PRESETS P1_sop_imgdense(條件式,P2/prose 繼承 global False 避反噬)。

**ADR**:ADR-0056 段②d render-side cover 方案 A(line 117 / 252-253 net-new);新 config knob =
ADR-0040 四層擴展,非 new ADR。

**Plan 落地**:W75 folder + plan.md(active)+ checklist.md(F1-F4)+ progress.md。

**Decisions**:
- 方向 1(backend marker 注入,frontend 零改動)— H7 唔 trigger。
- gate via config knob `enable_section_anchored_aux_images`(ADR-0040 四層,global default False)。
- 章節級(prefix-1,可錨率 100%)先做;leaf 級(2-82%)留後續。

**Next**:F1 config knob 四層 → F2 inject function + wire → F3 test → F4 preset + 實測 + 收爐。

**Commits**:(待 F1)
