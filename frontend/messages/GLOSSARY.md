# EKP en / zh 術語表(GLOSSARY)+ 字典維護規則

> **地位**:`en.json` / `zh.json` 嘅術語權威(W103 F5.2,2026-07-21 用戶拍板定案)。
> 加新 key、改譯文、校對(F5.3)都以此表為準;同此表衝突 = 要改字典,唔係改表(改表要用戶 approve)。
> 維護規則見 §F(W103 F8.2,類比 DESIGN_SYSTEM.md §7 sync 紀律)。

---

## A. 統一保留英文(zh 唔譯)

| 類別 | 例 | 理由 |
|---|---|---|
| Vendor / 產品名 | Azure AI Search · Cohere · Docling · python-pptx · Entra ID · MSAL · Langfuse · RAGAs · Postgres · SharePoint · GPT-5.5 · Blob | 專有名詞(CLAUDE.md §11 六類保留) |
| Metric 名 | Recall@5 · Faithfulness · Ans Relevancy · Ctx Precision · R@5 · P95 | RAGAs / eval 對照術語 |
| Status badge(大寫) | READY · ARCHIVED · EMPTY · ACTIVE · INVITED · SUSPENDED · HEALTHY · DEGRADED · OK · CRAG | 視覺 badge 慣例(mockup spec) |
| Role 專名 | Workspace Admin · Knowledge Editor · End User · Power User;segment 短標 Admin / Editor / User | ADR-0024 預定義角色名 |
| Schema / 參數(mono) | chunk_id · top_k · rerank_k · embedded_image_positions · allowed_principals · section_path · doc_order | 對應 backend field,唔可譯 |
| Tier / ADR / spec 編號 | Tier 1 / Tier 2 · T2 · ADR-0056 · architecture.md §3.5 · W72 | 治理引用 |
| Corpus 域 | AR / AP / FA / CB / GL / BM · D365 F&O ERP | 業務域縮寫 |
| 檔案格式 | .docx / .pdf / .pptx · Word / PDF / PowerPoint | 格式名 |
| **RAG 核心術語(2026-07-21 拍板)** | **chunk**(+ Chunks 表頭 / Chunk 策略 / chunker)· **preset** · **rerank / reranker** · **pipeline** · **overlap** · **embedding**(向量域)· **deployment** · **provider** · **ingest / ingestion** | 同 schema / 調校旋鈕 / backend 概念緊密對應,保留一致性最高 |
| Azure Portal 對照欄位 | Tenant ID · Client secret · Authority URL · 應用程式 (client) ID · Redirect URI | 管理員對照 Azure Portal 填寫,保留免歧義 |
| Pipeline stage 短標籤 | Parse · Extract · Chunk · Embed · Index · Document extraction | stepper / stage 卡單詞標籤,視覺緊湊 + 對應 backend stage 名 |
| 技術狀態句(mono 區塊) | auth-modes · MSAL footer · ACS footer · `<not provisioned>` sentinel | dashed technical block 慣例 |

## B. 統一中文定譯

| en | zh | 備註 |
|---|---|---|
| knowledge base | 知識庫 | 縮寫 KB 保留(「此 KB」) |
| index / indexing / re-index | 索引 / 索引中 / 重建索引 | |
| retrieval / retrieval testing | 檢索 / 檢索測試 | |
| search | 搜尋 | |
| workspace | 工作區 | Workspace Admin 角色名除外(A 類) |
| role / permission | 角色 / 權限 | EKP 角色 · Entra 群組(表頭都譯) |
| group | 群組 | Group ID → 群組 ID |
| audit log | 稽核日誌 | |
| secret(操作語境) | 密鑰 | `Client secret` 欄位名除外(A 類 Azure 對照) |
| connection(名詞) | 連線 | 動詞 connect 容許「連接」(「連接網站」) |
| deployment 表格外語境 | 部署(動詞)| 名詞欄位 / 配額語境保留 Deployment(A 類) |
| upload | 上傳 | |
| document | 文件 | |
| screenshot | 截圖 | |
| image | 圖片 | embedded images → 內嵌圖片(embed 向量域先保留) |
| extract(圖片/截圖) | **擷取** | 2026-07-21 統一(淘汰「抽取」) |
| parse(句子語境) | 解析 | stage 短標籤 Parse 除外(A 類) |
| anchor / anchoring | 錨定 / 錨點 | |
| marker(句子語境) | 標記 | `inline marker` 表頭短標可保留 |
| citation(用戶面) | 引用 | Chat 面向 end-user;**調校面 bare「citation」保留**(同 max_aux_per_citation 對應)|
| trace | 追蹤 | |
| eval | 評估 | |
| dashboard | 儀表板 | |
| settings | 設定 | |
| identity(EKP 語境) | 身分 | Identity & Auth → 身分與驗證;KB identity → KB 識別(唔同概念) |
| profile(用戶域) | 個人檔案 | user profile |
| **profile(文件域)** | **畫像** | 2026-07-21 統一(淘汰 bare「profile」/「設定檔」);profiler 組件名保留 |
| member | 成員 | |
| invite | 邀請 | |
| session | 工作階段 | |
| storage(一般) | 儲存 | Blob storage 保留(A 類 Azure) |
| synthesis(句子語境) | 合成 | 「GPT-5.5 合成」 |

## C. 分域 / 例外規則

1. **citation 分域**:Chat end-user 面 → 「引用」;KB / doc 調校面(旋鈕、hint)→ 保留「citation」(同 schema 參數並排時免中英割裂)。
2. **profile 分域**:用戶域「個人檔案」/ 文件域「畫像」—— 同字唔同概念,唔可互換。
3. **embedding vs embedded**:embedding(向量)保留英文;embedded images(內嵌圖片)譯中文 —— 唔同概念。
4. **品牌句例外**:行銷 / 空狀態一句式描述(AuthFrame subtitle、Chat empty、composer footer)入面「Cohere v4.0-pro **重排**」「CRAG **自我修正**」屬敘述文案,保持中文,唔受 A 類 rerank 保留約束。
5. **表頭一致**:同一概念喺唔同 view 嘅表頭要同譯(Users 同 SettingsIdentity 嘅「EKP 角色」「Entra 群組」)。

## D. 排版規則(2026-07-20 拍板)

- **全形標點**:中文緊鄰嘅逗號 / 冒號 / 分號 / 問號 / 驚嘆號 / 括號一律全形(`，：；？！（）`);省略號用「…」。
- **半形括號例外**:「中文標籤 + 空格 + 半形括號包純西文」保持半形 —— `應用程式 (client) ID` / `圖片密度 (img_density)`(通行中英混排慣例)。
- **ICU 保護**:`{placeholder}` / `<tag>` / URL 內部標點屬語法,唔受排版規則約束。
- **中英之間**:中文同英文 / 數字之間保留一個半形空格(現行慣例)。

## E. 拍板記錄

| 日期 | 決定 | 方式 |
|---|---|---|
| 2026-07-20 | 括號風格:純西文半形 + 空格保持 | AskUserQuestion |
| 2026-07-21 | chunk 系統一保留 chunk(含 Chunk 策略) | AskUserQuestion |
| 2026-07-21 | 文件 profile 域統一「畫像」 | AskUserQuestion |
| 2026-07-21 | preset 統一保留 | AskUserQuestion |
| 2026-07-21 | rerank / pipeline / overlap / deployment 保留英文;品牌句「重排」例外;Chat 面 citation 譯「引用」 | AskUserQuestion |

## F. 字典維護規則(W103 F8.2 — binding,類比 DESIGN_SYSTEM.md §7)

> **Why**:每次新 UI string 都要雙語同步,drift 風險同 design token 4-layer drift 同源(ADR-0075 §Consequences 預警)。呢度嘅 machine gate + 程序令 drift 喺 commit 前就紅燈,唔靠人肉記憶。

### F.1 加新 UI string(最常見)

1. **唔 hardcode 文案落 `.tsx`**(en / zh 都唔可以 — CH-023 教訓);一律 `useTranslations('<Namespace>')` + `t('key')`
2. **en.json + zh.json 同步加**(絕不只加一邊;namespace 對應組件,key 用 camelCase 語意名)
3. **術語過一次本表**:A 類保留英文 / B 類用定譯 / 唔確定 → 見 F.4
4. **排版過 D 類**:中文緊鄰標點全形;純西文括號半形;ICU `{param}` / `<tag>` 兩邊對稱
5. **跑 machine gate**:`npx vitest run tests/unit/i18n-dictionaries.test.ts` —— key parity / ICU 語法 / placeholder + rich tag 對稱 / 中文排版 / 保留清單抽樣,全部自動守(缺一邊 key 係 **runtime throw**,唔係靜靜 fallback)

### F.2 改既有譯文

- 只改 value 唔改 key;若涉術語譯法改變 → 先改本表(用戶 approve)再批次改字典(per-key 精準替換 + dry-run 審,見 `docs/01-planning/W103-i18n-en-zh/progress.md` Day 3 續方法)

### F.3 刪 key

- en / zh 同步刪 + **即刻 `JSON.parse` 驗**(懸掛逗號會壞檔 — W103 F6.2 踩過)+ grep 組件層無殘留 `t('該key')`

### F.4 新術語 / 譯法爭議

- 本表冇 cover 嘅新術語:傾向跟 A 類邏輯(schema / 調校 / vendor 域保留英文;end-user 敘述域譯中文);拿唔準 → 問用戶,拍板後補 E 類記錄 + 對應 A / B / C 類條目
- **唔可以**靜靜引入第三種譯法(profile 四譯 / pipeline 三譯就係咁積出嚟)

### F.5 Drift 偵測(季度 / phase closeout)

- 全量靜態掃描方法(1588 條逐條,browser 走查捉唔齊漏譯):見 `docs/01-planning/W103-i18n-en-zh/progress.md` Day 2 —— ①純英文 value 掃描(疑漏譯)②半形標點掃描 ③術語 pattern 掃描(B 類詞喺 zh 出現英文原詞 = 疑 drift)
- 測試層守門常駐 CI 前提 = B-27(frontend CI 加 vitest)落地;未落地前 phase closeout 手動跑一次 F.1 第 5 步

### F.6 組件 / 測試層慣例

- 新組件測試**唔使**包 `NextIntlClientProvider` —— `tests/unit/setup.ts` 已用官方 `createTranslator` 全域接管(en 預設;切換態用 `setTestLocale('zh')`,每 test 自動 reset)
- 語言 native name(English / 繁體中文 / 日本語)兩 locale 同值(慣例:語言名以其自身語言顯示)
