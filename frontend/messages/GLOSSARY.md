# EKP en / zh 術語表(GLOSSARY)

> **地位**:`en.json` / `zh.json` 嘅術語權威(W103 F5.2,2026-07-21 用戶拍板定案)。
> 加新 key、改譯文、校對(F5.3)都以此表為準;同此表衝突 = 要改字典,唔係改表(改表要用戶 approve)。
> 維護規則詳見 F8.2(W103 closeout 補);drift 檢查:`node scripts` 見 `docs/01-planning/W103-i18n-en-zh/progress.md` Day 2 靜態掃描方法。

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
