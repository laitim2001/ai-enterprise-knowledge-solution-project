# 01 — 平台導覽

> EKP(Enterprise Knowledge Platform)Tier 1:企業文件 RAG 知識平台。
> 上傳文件 → 自動切分 / 索引 → chat 問答(帶引用 + 截圖)→ 按 KB / 文件調配置 → 試跑驗證。

## 1. 頁面地圖(左側導覽)

| 頁面 | 路徑 | 做咩 |
|---|---|---|
| Dashboard | `/dashboard` | 總覽:KB 數 / 文件數 / 近期活動 |
| **Chat** | `/chat` | 問答主介面 — 揀 KB、串流答案、引用 pill、截圖 gallery、對話歷史 |
| **Knowledge** | `/kb` | KB 列表 → 入 KB 詳情(本手冊大部分操作喺呢度)|
| Eval | `/eval` | RAGAs 四指標評估 run 結果 |
| Traces | `/traces` | Langfuse 觀測(query 鏈路 / 成本)|
| Settings | `/settings` | 平台層設定 |
| Users & access | `/users` | 用戶 / 權限 |
| 全域搜尋 | `Ctrl/Cmd + K` | 跨 KB / traces / settings 快速跳轉 |

## 2. KB 詳情頁 8 個 tab(操作核心)

入一個 KB(`/kb/{kb_id}`)後:

| Tab | 用途 |
|---|---|
| Documents | 文件列表 → 撳入單份文件(per-doc 配置喺文件詳情入面)|
| Chunks | 睇切分結果(每個 chunk 嘅章節 / 內容 / 圖數)|
| Images | KB 全部已索引截圖 gallery(chat「View all in Image Library」嘅落點)|
| Chunking Lab | 切分策略預覽 / 對比 |
| Pipeline | ingest 管線狀態 |
| Retrieval Testing | **V4 檢索診斷**(retrieve-only,見 04 手冊)|
| **Settings** | **per-KB 配置中心**(General / Retrieval config / Advanced tuning / 試跑 / Re-index)|
| Access | KB 存取權限 |

## 3. 核心概念(4 個,明白咗成個平台就通)

### 3.1 四層配置解析鏈

```
per-query(試跑時臨時)>  per-doc(文件覆寫)>  per-KB(KB Settings)>  global(系統出廠值)
```

- 每個旋鈕喺 UI 留空 = 「繼承」上一層;填值 = 「已覆寫」(有 badge 標示 + 還原按鈕)。
- **per-doc 只覆蓋「答案生成 + 引用後處理 + 圖片」**;檢索層旋鈕(top_k / rerank_k /
  parent-doc)只去到 per-KB — 因為系統要檢索完先知答案主要引邊份文件。

### 3.2 Ingest-time vs Runtime 旋鈕

- **Ingest-time**(chunk strategy / 每 chunk 圖上限 / 抽唔抽嵌入圖):改完要 **Re-index** 先生效。
- **Runtime**(其餘全部):儲存即生效,下一條 query 就用新值。
- UI 有標示:「Runtime · no re-index」badge / 「需重新索引」提示。

### 3.3 試跑(config-test)

唔使儲存就可以攞草稿配置喺真 pipeline 上跑 N 次,同已存配置 A/B 對照,睇雙軸指標
(引用數 / 涵蓋章節數 / 圖片章節數 / 圖數 / 忠實度)。**先試跑、後儲存** 係平台嘅
標準工作流(詳見 04)。

### 3.4 文字完整性同圖片完整性係兩條獨立管線

文字靠 citation expansion + parent-doc retrieval;圖片靠 neighbour images 收割 + 圖片預算。
**調好文字唔等於圖片會齊**(反之亦然)— 兩邊有各自嘅旋鈕同指標(詳見 03 / 04)。

## 4. 一條 query 嘅生命周期(知道嘢喺邊層出錯)

```
query → (query expansion*) → hybrid 檢索(vector + BM25,top 50)→ Cohere rerank(top 5*)
      → parent-doc 聚合* → GPT-5.5 答案生成 → citation expansion*(補引用)
      → neighbour images 收割* + 圖片預算 cap* → 引用 + 圖回 UI
      → UI:裝飾圖過濾 + inline cap + gallery
```

`*` = 有旋鈕可調嘅層(03 手冊逐個講)。

## 5. 圖片顯示嘅三層數字(成日俾人撈亂,先講清)

同一條答案,「圖片有幾多張」有三個數,**唔相等係正常**:

1. **Backend 返回數**(引用攜帶嘅去重後圖)— eval 同試跑量嘅係呢個
2. **UI figure 數** = backend 數 − 裝飾性圖示(細過 64px 嘅 icon / 近正方形嘅 tip 圖案,顯示層自動過濾)
3. **Inline 卡數** = min(UI figure 數, 圖片上限)— 超出部分喺 gallery badge +「View all in Image Library」

例:backend 65 → UI 63 個 figure(過濾咗 1 個 Excel 附件 icon + 1 個燈泡 tip 圖案)→ 全部 inline(上限 80)。

## 6. 介面語言(en / 繁體中文,2026-07 W103 起)

介面文字支援 **English / 繁體中文** 切換(per ADR-0075;日文屬 Tier 2 未推出):

- **切換位置(兩個入口,同步生效)**:①頂欄地球儀圖示 → 揀語言(en / 繁體中文;ja 灰顯)②設定 → 外觀 → 語言下拉。揀完即時生效,記住一年(存 browser cookie,唔使登入)。
- **範圍 = 介面文字**(選單 / 按鈕 / 表頭 / 提示):**答案同文件內容維持原文檔語言,唔會翻譯** —— 呢個係刻意設計(RAG content 翻譯屬另一 Tier 2 項目)。
- **刻意保留英文嘅嘢**(唔係漏譯):技術術語(chunk / preset / rerank / pipeline)、vendor 名(Azure / Cohere)、指標名(Recall@5 / Faithfulness)、狀態 badge(READY / ARCHIVED)、角色名(Workspace Admin)。完整清單 + 點解:`frontend/messages/GLOSSARY.md`。
- **見到譯文有問題**:引述嗰句文字 + 邊一頁,交平台管理員(對照 GLOSSARY 修正)。
