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

**F1-F3 implement(Day 1)**:
- **F1 config knob 四層**:`enable_section_anchored_aux_images` 加 settings.py(global False)/ effective_config.py
  (QueryConfigOverlay + EffectiveConfig + _resolve 四層)/ kb.py / doc_config.py。mirror `enable_inline_image_markers`。
- **F2 inject function + wire**:新 module `generation/section_anchor_markers.py`
  `inject_section_anchored_markers(answer, citations, *, section_prefix_depth=1)` pure function(抽已有 anchored sha8
  → 同章節 match → back-to-front splice 插 marker,doc_order 排)。query.py 兩處 wire:**/query**(line 499 前 gate
  inject)+ **/query/stream**(`compose_query_stream` 新 `answer_post_process` callback,done event answer)。**關鍵**:
  frontend done.answer replace 機制(BUG-028 ②,`chat/page.tsx:449/452`)令注入 marker 自動 interleave → **frontend
  零改動 → H7 唔 trigger**。
- **F3 test**:`test_section_anchor_markers.py`(10 case:同章節錨定 / 無錨點留 trailing / doc_order / no-op /
  dedup / 多章節 / 最後錨點 / too-shallow skip)+ `test_effective_config.py` append 5 resolve case。
- **Gate**:mypy --strict 新 code 0(剩 6 pre-existing 我冇 touch,git diff 核實)+ ruff 0;pytest 51 passed
  (inject + resolve + stream_composer)+ query route 48 passed(wire 唔 break,gate OFF bit-identical)。

**F4 preset 接駁 + 實測 + 收爐(Day 1)**:
- **F4.1**:`profile_presets.py` P1_sop_imgdense preset 加 `enable_section_anchored_aux_images=True`(條件式
  只 P1 圖密 SOP,per ADR-0056 D7;P1_sop_text 低圖 aux 少收益細,守 simplicity)。test_profile_routing assert 加,7 passed。
- **F4.2 實測**(真實 drive-images-1,offline apply inject on 舊 code /query 答案,零 backend restart):末尾堆
  **28-85% → 0%**(depreciation 8→0 / create-master 41→0 / ap+gl 52→0),3 query 全錨,注入 8-52 圖/query。
  章節級可錨率 100% 兌現;跨模組 query(80 圖)都全錨(drive-images-1 全 P1 SOP,章節級錨點充足,比 ADR 保守預期更好)。

**Retro**:
- 方向 1(backend marker 注入)正路 — frontend done.answer replace 機制(BUG-028 ②,`chat/page.tsx:449/452`)令
  注入 marker 自動 interleave,**H7 零 trigger**,frontend 一行唔使改。R6 grounding 喺 plan kickoff 揭示呢條係本 phase 最大省力位。
- 實測用 **offline apply**(舊 code /query capture answer+citations + offline inject)取代 backend restart end-to-end:
  零 infra 風險(唔使殺 dual-process / 等慢 startup)+ 驗證真實數據縮小。inject 純函數設計(answer + citations → new answer)令呢個 offline 驗證可行。
- **R1 章節內 clump 風險真實存在**(create-master 7 anchored 收 41 un-anchored = 平均每錨點 clump ~6 圖),
  但「末尾堆 → 章節內 clump」係明顯改善;靠 frontend `doc_order` sort(CH-011)緩解,leaf 級精準錨留後續(query-dependent)。
- **DD-1 browser 肉眼(已做,2026-06-14,closed)**:重啟全部服務後 chat `/query/stream` live 驗證 — 45 圖全 inline
  交織入步驟 list、**末尾堆 0**、stream path 注入生效(done.answer)、**frontend 零改動兌現**(reuse W71 render)。
  **但揭示 clump 偏重**:每步驟圖卡分佈 **[39,1,1,1,1,1,1]**,`maxConsecutiveFigureRun=39`(一步驟「Click Close twice」
  後 39 張連續圖卡 ≈ 換位置嘅末尾堆)。根因:章節級(prefix-1)太粗 + image-recall 39 aux 圖 + synthesizer 少 cite
  (7 anchored)→ 39 張同章節圖全 clump 一個錨點。**方法論教訓:headless 量化(末尾堆 0)睇落完美,肉眼先見 clump
  重 —— DD-1 browser 肉眼嘅真實價值**。**用戶判決(2026-06-14):接受現狀(章節級,不優化 clump)**;clump 優化
  (每錨點 cap / leaf 級精準錨,leaf 可錨率 2-82% 有 tension)留將來 explicit trigger。
- **Runtime 註**:demo 用 backend env `ENABLE_SECTION_ANCHORED_AUX_IMAGES=true` 啟動令 drive-images-1 生效
  (per-KB config 無此新旋鈕 → inherit global env);**非 persistent**,下次 backend restart 回 default False。要
  drive-images-1 持續 ON 需 per-KB config 設旋鈕(或 W73 routing re-ingest)。

**Commits**:
- `23b3952` docs(planning): W75 kickoff
- `0b501bd` feat(generation): W75 F1-F3 section-anchored aux image injection
- `cfbad35` feat(generation): W75 F4 closeout — preset + 實測
- `6bd5c11` docs(planning): W75 DD-1 browser 肉眼 closed

---

## Day 2 — 2026-06-14(reopen F5 每錨點 cap)

**Context**:DD-1 揭示 clump 偏重(maxConsecutiveFigureRun=39)。用戶初選接受現狀,後 trigger
「每錨點 cap 試吓改善 clump」→ 重開 W75 加 F5。

**F5 設計(D5)**:新 knob `section_anchor_max_per_anchor`(ADR-0040 四層,global default 0 = 無 cap,保
F1-F4 bit-identical)+ inject `max_per_anchor` 參數(每章節注入 `doc_order` 前 N,超出不注入回 trailing)。
trade-off:clump 限 N vs 末尾堆部分回歸,實測 browser 定 N。placement 不變(仍插同章節最後一個 anchored marker 後)。

**Next**:F5.1-F5.7 implement → F5.8 實測 browser 不同 N → F5.9 closeout。

**Commits(Day 2)**:(待 F5)
