# Slideon 系统架构文档

> 版本：0.2.0 | 日期：2026-06-07 | 分支：feature/rag

---

## 1. 系统概览

### 1.1 项目简介

Slideon 是一个基于大语言模型（LLM）和检索增强生成（RAG）的智能 PPT 生成系统。用户只需输入一个主题或上传文档，系统即可自动完成意图分析、大纲规划、内容生成、排版渲染，并导出为标准的 `.pptx` 文件。

**核心设计理念**：**"AI 负责语义，Renderer 负责视觉"**。LLM 只输出结构化的语义 DSL（Domain Specific Language），不涉及任何布局细节（禁止输出 x/y/w/h/fontSize/templateId 等坐标/尺寸字段）；渲染引擎将 DSL 编译为 RenderTree，负责布局、样式和组件组合。这种解耦确保了生成内容的质量可控与视觉呈现的专业一致。

### 1.2 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **后端框架** | FastAPI (Python 3.12) | 异步 HTTP 服务，自动 OpenAPI 文档 |
| **AI 编排** | LangChain + LangGraph | Prompt 编排与状态图引擎 |
| **LLM** | DeepSeek / OpenAI 兼容 API | 通过 langchain-openai 适配，支持多模型切换 |
| **向量数据库** | Milvus 3.0-beta | 混合检索：ANN 向量检索 + 中文关键词检索 |
| **向量化模型** | BAAI/bge-small-zh-v1.5 | 512 维中英双语向量，轻量高效 |
| **网络搜索** | DuckDuckGo API + trafilatura | 搜索 + 全文抓取（Deep Fetch） |
| **文档解析** | pymupdf (PDF) + python-docx (Word) | 长文档文本提取 |
| **PPTX 导出** | python-pptx | 标准 PowerPoint 格式 |
| **前端** | Vue 3 (Composition API) + Vite | 轻量、零框架依赖的 SPA |
| **数据存储** | 文件系统 (JSON) | 轻量级本地存储，presentation 序列化为 JSON |

### 1.3 系统架构图

```
┌──────────────────────────────────────────────────────────────────┐
│                    前端 (slideon-frontend)                         │
│         Vue 3 + Vite: 首页 · Dashboard · 大纲编辑器 · 评估页面      │
│  ┌──────────────┐  ┌─────────────────┐  ┌────────────────────┐   │
│  │ OutlineModal  │  │ KnowledgeBase   │  │ Evaluation         │   │
│  │ (主题输入 +   │  │ Panel           │  │ Panel              │   │
│  │  文档上传)    │  │ (批量导入+进度)  │  │ (雷达图+指标卡片)   │   │
│  └──────────────┘  └─────────────────┘  └────────────────────┘   │
└──────────────────────────┬───────────────────────────────────────┘
                           │ HTTP REST API
┌──────────────────────────┴───────────────────────────────────────┐
│                    后端 (FastAPI)                                  │
│                                                                  │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────────────┐ │
│  │ AI Pipeline   │  │ Render Engine   │  │ RAG Service          │ │
│  │              │  │                │  │                      │ │
│  │ 1.意图分析   │  │ Component      │  │ HybridRetriever      │ │
│  │ 2.结构规划   │  │ Planner        │  │ ├─ Dense (Milvus ANN) │ │
│  │ 3.DSL 生成   │  │                │  │ ├─ Sparse (Keyword)  │ │
│  │              │  │ Layout Engine  │  │ ├─ Web (DuckDuckGo)  │ │
│  │ 15种语义类型 │  │ (绝对坐标布局)  │  │ └─ RRF Fusion        │ │
│  │              │  │                │  │                      │ │
│  │ Fallback +   │  │ Theme Engine   │  │ LangGraph 编排        │ │
│  │ Repair 策略  │  │ (Token→样式)    │  │ (并行检索+融合)       │ │
│  └──────────────┘  └────────────────┘  └──────────────────────┘ │
│                                                                  │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────────────┐ │
│  │ Evaluation    │  │ Export (PPTX)   │  │ Task Queue            │ │
│  │ System        │  │                │  │ (Async KB Import)     │ │
│  │              │  │ python-pptx    │  │                      │ │
│  │ Rule Metrics │  │ 组件→Shape     │  │ asyncio.Queue        │ │
│  │ + LLM Judge  │  │                │  │ + 后台 Worker         │ │
│  └──────────────┘  └────────────────┘  └──────────────────────┘ │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────┴───────────────────────────────────────┐
│                        数据层                                      │
│  ┌──────────────┐  ┌──────────────────┐  ┌────────────────────┐ │
│  │ File Repo    │  │ Milvus Vector DB │  │ Web Search          │ │
│  │ (JSON 文件)   │  │ (BGE Embedding)  │  │ (DuckDuckGo)        │ │
│  └──────────────┘  └──────────────────┘  └────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### 1.4 端到端数据流

```
用户输入（主题文本 或 上传文档）
    │
    ▼
┌──────────────┐
│ 文档解析      │ ← PDF/Word → 纯文本 (pymupdf / python-docx)
│ (如果是文件)  │     自动入库 Milvus（fire-and-forget）
└──────┬───────┘
       │
       ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ RAG 检索      │ →  │ AI Pipeline   │ →  │ Render Engine │
│ (Milvus+Web)  │    │ 意图→规划→DSL  │    │ DSL→RenderTree│
│ 混合检索+RRF  │    │ 15种语义类型   │    │ 组件+布局+主题 │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                               │
                    ┌──────────────────────────┘
                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ 前端编辑      │ ←  │ RenderTree   │ →  │ PPTX 导出     │
│ (Outline     │    │ (JSON)       │    │ (python-pptx) │
│  Editor)     │    │ 可编辑组件树   │    │ 标准 .pptx    │
└──────────────┘    └──────────────┘    └──────────────┘
       │
       ▼
┌──────────────┐
│ 质量评估      │
│ Rule Metrics │
│ + LLM Judge  │
└──────────────┘
```

---

## 2. AI Pipeline 核心模块详解

### 2.1 概述

AI Pipeline (`services/ai/pipeline.py`) 是整个系统的核心生成引擎，采用 **三阶段流水线架构**。每个阶段调用一次 LLM，上一阶段的输出作为下一阶段的输入。Pipeline 还内置了多层容错机制和 DSL 修复策略。

### 2.2 阶段 1：意图分析 (`analyze_intent`)

**职责**：理解用户意图，推断演示文稿的元信息。

**输入**：用户主题（字符串），例如 `"新能源汽车行业分析"`

**输出**：`IntentAnalysis` Pydantic 模型，包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| `audience` | str | 目标受众，如"企业中高层管理者" |
| `goal` | str | 演示目标，如"说服投资" |
| `tone` | str | 风格基调，如"专业、数据驱动" |
| `slideCount` | int | 建议页数（≥10，丰富主题可到 15-20） |
| `preferredTheme` | str\|null | 推荐主题：modern_blue / paper_light / academic_gray / minimal_black |

**Prompt 设计要点**：
- 系统角色：「资深 PPT 规划助手」
- 严格输出约束：只输出 JSON，不输出解释文字
- 页数下限：至少 10 页，内容丰富的主题可到 15-20 页

**容错**：初始化 LLM 失败或调用超时时，跳过分析阶段直接使用 fallback DSL。

### 2.3 阶段 2：结构规划 (`plan_presentation`)

**职责**：将意图分析结果转化为具体的页面结构规划。

**输入**：`IntentAnalysis` 对象（JSON 序列化后传入 prompt）

**输出**：`PresentationPlan` Pydantic 模型，包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | str | PPT 最终标题 |
| `theme` | str | 推荐主题 |
| `slides` | list | 页面规划列表，每个元素含 `id` / `intent` / `section` / `title` / `purpose` |

**15 种 intent 类型**：

| Intent | 说明 | 典型场景 |
|--------|------|---------|
| `cover` | 封面 | 标题、副标题、亮点 |
| `agenda` | 目录 | 内容导航列表 |
| `text` | 文本页 | 要点列表 + 段落 |
| `timeline` | 时间线 | 里程碑事件 |
| `kpi` | 关键指标 | 数值 + 单位 + 变化 |
| `comparison` | 对比 | 左右两栏对比 |
| `swot` | SWOT 分析 | 优势/劣势/机会/威胁 |
| `roadmap` | 路线图 | 阶段 + 交付物 |
| `process_flow` | 流程图 | 步骤序列 |
| `chart` | 图表 | 柱状图/折线图/饼图 |
| `multi_column` | 多列 | 并列要点 |
| `architecture` | 架构图 | 分层结构 |
| `quote` | 引用 | 名言/金句 |
| `divider` | 分隔页 | 章节过渡 |
| `team` | 团队 | 成员介绍 |

**Prompt 设计要点**：
- intent 必须从上述 15 种集合中选择
- 确保规划 ≥10 页，覆盖封面、目录、多个内容页、数据页、总结页
- 每个 section 可包含多页以充分展开

### 2.4 阶段 3：DSL 生成 (`generate_dsl`)

**职责**：基于规划结果生成完整的语义化 Presentation DSL，这是最核心的生成步骤。

**输入**：
- `topic`：主题
- `theme`：主题名称
- `rag_context`：RAG 检索到的参考资料（可选）

**输出**：`PresentationDSL` Pydantic 模型，包含完整的语义化页面描述。

**Prompt 设计要点**：

1. **严格的字段约束**：为每种 intent 类型明确定义必需字段
   - `cover`：subtitle / tagline / highlights (list[str])
   - `agenda`：items (list[str])
   - `text`：paragraphs / bullets (list[str])
   - `chart`：chartType (bar/line/pie) / labels / series
   - ...

2. **布局分离原则**（核心设计决策）：
   ```
   严格禁止输出任何布局字段：x/y/w/h/fontSize/templateId/坐标/尺寸。
   只输出结构化语义数据。
   ```

3. **RAG 自适应内容密度**：
   - **有参考资料时**：每页 4-6 bullets，完整句子，包含具体数据/案例/趋势
   - **无参考资料时**：每页 2-3 bullets，简洁精炼，避免冗长

4. **通用规则**：避免低信息量空洞内容（如单独的"概述"、"简介"）

### 2.5 容错与修复策略

Pipeline 内置 **多层容错机制**，确保在任何环节失败时都能返回可用结果：

```
LLM 初始化失败 ──→ _fallback() 生成默认 14 页 DSL

意图分析超时 ──→ 直接抛出 APITimeoutError (HTTP 504)
意图分析失败 ──→ _fallback()

结构规划失败 ──→ _fallback()

DSL 生成超时 ──→ 直接抛出 APITimeoutError (HTTP 504)
DSL 生成 JSON 解析失败 ──→ _repair_dsl_dict() 遍历修复
    │
    ├── 修复成功 → 返回修复后的 DSL
    └── 修复失败 → _fallback()

DSL slides 为空 ──→ _fallback()
```

**`_repair_dsl_dict()` 修复能力**（约 600 行防御性代码）：

| 问题类型 | 修复方式 |
|---------|---------|
| notes 为 string 而非 array | `"notes": "xxx"` → `"notes": ["xxx"]` |
| 字段缺失 | 从 topic / analysis 继承（title、audience、tone 等） |
| intent 无效 | 从对象结构推断正确的 intent |
| items 为 string 而非 object | 按"："分割为 label/value |
| 多字段合并 | 尝试从 content/text/items/bullets 等字段提取有效内容 |
| 类型错误 | 自动类型转换（str→list, dict→list 等） |

**`_fallback()` 方法**：生成一个完整的 14 页默认 PPT（涵盖所有 intent 类型的示例），确保系统在极限情况下始终有可用输出。

### 2.6 RAG 与 Pipeline 的集成

DSL 生成时通过 `rag_context` 参数注入 RAG 增强内容：

```python
# 在 PresentationService.create() 中
rag_context = rag_service.retrieve_context(topic, top_k=8)
dsl = ai_pipeline.generate_dsl(topic, theme, rag_context=rag_context)
```

Prompt 中 RAG 上下文格式：
```
## 参考资料（来自知识库和网络搜索，务必充分利用）
请大量引用以下资料中的具体数据、案例、趋势、事实来丰富 PPT 内容。
每页内容应从参考资料中提取相关信息，而非泛泛而谈。

[来源 1 - web:article_title]
文章内容...

---
[来源 2 - knowledge_base]
知识库文本...

基于以上参考资料，确保生成的内容有深度、有数据支撑、有具体案例。
```

---

## 3. RAG 模块详解

### 3.1 架构总览

RAG 模块 (`services/rag/`) 实现了一个完整的检索增强生成系统，架构如下：

```
RagService (rag_service.py)              ← 高层服务接口
  │
  ├── HybridRetriever (retrieval.py)      ← 混合检索核心
  │     ├── MilvusStore: Dense 向量检索 (ANN) + Sparse 关键词检索
  │     ├── WebSearchService: DuckDuckGo 网络搜索
  │     ├── ContentFetcher: trafilatura 全文抓取（Deep Fetch）
  │     └── RRF Fusion: 倒数排列融合排序
  │
  ├── KnowledgeBase (knowledge_base.py)   ← 知识库管理
  │     ├── EmbeddingService: BGE-small-zh-v1.5 (512 维)
  │     ├── 文档解析: PDF (pymupdf) + DOCX (python-docx) + TXT + MD
  │     └── 文本分块: 500 chars + 80 chars overlap
  │
  └── RAG Graph (rag_graph.py)           ← LangGraph 状态图编排
        ├── analyze_query: 查询分析 → 多查询生成
        ├── web_search: 网络并行搜索
        ├── local_search: Milvus 本地搜索
        ├── enrich_images: 图片资源搜索
        ├── fuse: RRF 融合去重
        └── build_context: 构建最终增强上下文
```

### 3.2 混合检索策略（核心）

`HybridRetriever` 是 RAG 模块的核心，实现了 **四层检索融合**：

#### 第一层：Dense 向量检索（Milvus ANN）

- 使用 BGE-small-zh-v1.5 将查询文本编码为 512 维向量
- Milvus AUTOINDEX（自动选择最优 ANN 索引）进行近似最近邻搜索
- 相似度度量：Inner Product (IP)
- 支持 `source_filter` 按来源过滤
- 检索 `top_k * 2` 条结果供后续 RRF 融合

#### 第二层：Sparse 关键词检索（BM25-like）

- 利用 Milvus 的中文分词器和 VARCHAR 列的 LIKE 查询
- 实现类 BM25 的关键词匹配：`text like "%query%"`
- 对中文分词后的 token 进行匹配
- 不受向量空间语义漂移的影响，精确匹配关键词

#### 第三层：网络搜索

- 使用 DuckDuckGo 即时回答 API 进行网络搜索
- 结果包含 title、url、snippet
- 支持区域配置（默认 `wt-wt` 全球）

#### 第四层：Deep Fetch（全文抓取）

- 对前 3 条网络搜索结果调用 `ContentFetcher.fetch(url)` 抓取完整网页
- 使用 trafilatura 库提取正文内容（去除导航/广告/脚本）
- 300ms 请求间隔避免触发反爬
- 抓取失败则回退到 snippet

#### RRF 融合排序

所有检索结果通过 **Reciprocal Rank Fusion (RRF)** 统一排序：

```
RRF_score(d) = Σ 1 / (k + rank_i(d) + 1)

其中 k = 60（平滑参数）
本地结果权重 = 1.0
网络结果权重 = 0.4
```

RRF 的优点：无需训练、无需归一化分数、对不同来源的排序结果公平融合。

### 3.3 Milvus 向量数据库

**Collection**: `ppt_knowledge_base`

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INT64 (auto_id) | 主键，自动生成 |
| `text` | VARCHAR(65535) | 文本内容，启用中文分词器 |
| `embedding` | FLOAT_VECTOR(512) | BGE-small-zh-v1.5 生成的 512 维向量 |
| `source` | VARCHAR(512) | 来源标识（文件名/URL） |
| `chunk_index` | INT64 | 分块序号 |
| `metadata` | JSON | 额外元数据 |

**索引配置**：
- `embedding` 字段：AUTOINDEX + IP 度量（Milvus 自动选择最优索引类型）
- `id` 字段：STL_SORT（排序索引，加速过滤查询）

**混合搜索实现** (`milvus_client.py:112-121`)：
```python
def hybrid_search(self, query_embedding, query_text, top_k, source_filter=None):
    dense_hits = self._dense_search(query_embedding, top_k * 2, source_filter)
    sparse_hits = self._keyword_search(query_text, top_k * 2, source_filter)
    return self._rrf_fuse(dense_hits, sparse_hits, top_k)
```

### 3.4 知识库管理

`KnowledgeBase` 提供完整的文档生命周期管理：

**文档摄入** (`ingest_file` → `ingest_text`)：
1. 文件类型检测（按后缀）
2. 文档解析：
   - PDF：pymupdf (fitz) 逐页提取
   - DOCX：python-docx 逐段提取
   - TXT/MD：直接读取
3. 文本清洗：`re.sub(r"\s+", " ", text)`
4. 智能分块（见下文）
5. 批量向量化（batch_size=32）
6. 批量写入 Milvus

**分块策略**：
- `CHUNK_SIZE = 500` 字符
- `CHUNK_OVERLAP = 80` 字符
- 优先按段落边界分块（保持语义完整性）
- 超长段落按句号（"。"）寻找最佳切割点
- 如果找不到句号，回退到字符数强制截断

**管理操作**：
- `remove_source(source)`: 按来源标识删除所有相关 chunks
- `get_stats()`: 获取 collection 统计（存在性、实体数量）
- `ensure_collection(drop_if_exists)`: 创建或重置 collection

### 3.5 LangGraph 状态图编排

RAG Graph (`rag_graph.py`) 使用 LangGraph 的状态图引擎编排多步检索流程：

```
START
  │
  ▼
analyze_query (LLM 生成 3-5 个不同角度的搜索查询)
  │
  ├──────────────────┬──────────────────┐
  ▼                  ▼                  ▼
web_search        local_search      enrich_images
(DuckDuckGo)     (Milvus ANN)     (图片搜索)
  │                  │                  │
  └──────────────────┴──────────────────┘
                     │
                     ▼
                   fuse
              (RRF 融合去重)
                     │
                     ▼
              build_context
         (构建增强文本 + 图片URL)
                     │
                     ▼
                   END
```

**状态定义** (`RAGState` TypedDict)：
- `topic`: 用户主题
- `search_queries`: 生成的多个搜索查询
- `web_results` / `local_results` / `fused_results`: 各级检索结果
- `images`: 相关图片资源
- `enhanced_context`: 最终增强上下文

**并行执行**：web_search、local_search、enrich_images 三个节点没有依赖关系，LangGraph 自动并行执行。

### 3.6 网络搜索

`WebSearchService` 和 `ContentFetcher`：

- **搜索 API**：`duckduckgo_search` 库，支持区域配置
- **全文抓取**：trafilatura 提取网页正文
  - 自动去除导航栏、广告、侧边栏
  - 保留文章标题、段落、列表
  - 返回纯文本（而非 HTML）
- **容错**：fetch 失败时回退到 snippet（搜索结果摘要）
- **频率控制**：300ms 延迟避免请求过频

### 3.7 文档→大纲生成流程

新增的文档导入功能（`POST /dsl/from-document`）：

```
用户上传 PDF/Word
    │
    ▼
后端接收文件 → 保存临时文件
    │
    ▼
KnowledgeBase._read_file() 解析全文
    │
    ├── 长文档（>10k 字符）→ 智能截断（前 40% + 后 20% + 截断标记）
    │
    ▼
AiPipeline.generate_dsl() 以文档文本为 rag_context 生成 DSL
    │
    ▼ (后台 fire-and-forget)
KnowledgeBase.ingest_text() → Milvus 入库
    │
    ▼
返回大纲 JSON → 前端跳转编辑器
```

---

## 4. Render Engine 简介

### 4.1 渲染流水线

```
DSL (15 种语义类型)
    │
    ▼
Component Planner (planning.py)
  └── 语义 intent → 组件类型映射
  └── cover → TitleBlock + SubtitleBlock
  └── chart → ChartComponent + TitleBlock
    │
    ▼
Layout Engine (layout.py + layout_selector.py)
  └── 绝对坐标布局 (x, y, w, h)
  └── 预定义布局模板（居中、左对齐、两栏等）
    │
    ▼
Theme Engine (theme_engine.py)
  └── ThemeToken → CSS-like 样式
  └── 应用到每个 Component 的 style 字段
    │
    ▼
RenderTree (JSON)
  └── 可编辑的组件树（前端按 Component 粒度 patch）
```

### 4.2 主题系统

四种内置主题，每种定义了一套 DesignToken（主色、辅色、背景色、字体、间距、圆角等）：

| 主题 | 主色调 | 风格 |
|------|--------|------|
| modern_blue | #3B82F6 | 现代科技蓝，适合企业/产品发布 |
| paper_light | #F5F5DC | 清新纸质感，适合教育/培训 |
| academic_gray | #6B7280 | 学术灰调，适合论文/报告 |
| minimal_black | #1F2937 | 极简黑色，适合设计/创意 |

### 4.3 RenderTree 编辑模型

前端通过 `PATCH /presentations/{id}/components/{cid}` 按组件粒度编辑：
- 位置调整（x, y, w, h）
- 样式修改（颜色、字体、大小）
- 内容更新（文案、数据）
- 组件级拖拽重排

### 4.4 PPTX 导出

```
RenderTree → PptxExporter → python-pptx Slide
  └── component_renderers: 每种组件类型对应一个 PPTX 渲染器
    ├── TextBox → 文本框 + 字体/颜色/对齐样式
    ├── Chart → python-pptx Chart 对象（原生图表）
    ├── Table → 表格 + 合并单元格
    ├── Shape → 形状（矩形、圆角、箭头等）
    └── Group → 组合元素
```

---

## 5. 评估体系

### 5.1 架构

```
services/evaluation/
├── schemas.py      # Pydantic 数据模型
├── metrics.py      # 规则指标（BLEU, ROUGE-L, 结构, 密度, 多样性）
├── rag_eval.py     # RAG 专项指标（召回率, 精确率）
├── llm_judge.py    # LLM-as-Judge 语义评分
└── evaluator.py    # 编排器（规则 + LLM 综合评分）
```

### 5.2 评估指标

#### 规则统计指标（确定性，免费）

| 指标 | 计算方式 | 范围 |
|------|---------|------|
| 结构完整性 | 是否有封面+目录+内容+总结；intent 类型覆盖度 | 0-1 |
| 信息密度 | 平均每页 bullets/words/paragraphs | 0-1 |
| 内容多样性 | Type-Token Ratio (TTR) | 0-1 |
| BLEU-1~4 | 字符级 n-gram 精度 + Brevity Penalty | 0-1 |
| ROUGE-L | 最长公共子序列 (LCS) 精度/召回/F1 | 0-1 |
| RAG 召回率 | 检索 chunks 中被实际使用的比例 | 0-1 |
| RAG 精确率 | 有命中 chunks 的检索轮次比例 | 0-1 |

#### LLM-as-Judge 指标（语义，1-10 分）

| 指标 | 评估维度 |
|------|---------|
| 结构合理性 | 章节划分逻辑、过渡自然度 |
| 事实准确率 | 与参考资料一致性、是否存在编造 |
| 逻辑连贯性 | 各 slide 之间叙事线索清晰度 |
| 内容深度 | 具体数据/案例/分析 vs 泛泛概述 |
| 综合质量 | 整体沟通工具质量 |

### 5.3 两种评估模式

**用户自评**：集成在 OutlineEditor 中，点击"评估"按钮实时评分 + 改进建议

**批量评估**：独立页面 `/eval`，支持多配置 × 多主题的交叉对比

---

## 6. API 参考

### 6.1 PPT 生成

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/dsl` | AI 生成大纲（文本主题） |
| `POST` | `/dsl/from-document` | 从文档生成大纲（PDF/Word） |
| `POST` | `/render-tree` | 编译大纲为 RenderTree |
| `POST` | `/presentations` | 一键创建完整 PPT |
| `GET` | `/presentations/{id}` | 获取 PPT Bundle |
| `PATCH` | `/presentations/{id}/components/{cid}` | 编辑组件 |
| `PUT` | `/presentations/{id}/theme` | 切换主题 |
| `POST` | `/presentations/{id}/regenerate` | 重新生成 |
| `POST` | `/presentations/{id}/export/pptx` | 导出 PPTX 文件 |

### 6.2 RAG

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/rag/search` | 混合检索（Web + Local + Deep Fetch） |
| `POST` | `/rag/enhance` | 获取增强上下文文本 |
| `POST` | `/rag/documents` | 上传单个文档到 KB |
| `POST` | `/rag/documents/batch` | 批量上传文档（异步，返回 task_id） |
| `GET` | `/rag/tasks/{task_id}` | 查询导入进度 |
| `GET` | `/rag/documents` | 列出 KB 中的文档 |
| `DELETE` | `/rag/documents/{source}` | 删除 KB 条目 |
| `POST` | `/rag/bootstrap` | 初始化种子知识库 |

### 6.3 评估

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/eval/single/{presentation_id}` | 单次评估（规则 + LLM） |
| `POST` | `/eval/batch` | 批量评估（多配置 × 多主题） |

### 6.4 系统

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/health` | 健康检查 |
| `GET` | `/themes` | 列出可用主题 |

---

## 7. 关键设计决策

| 决策 | 理由 |
|------|------|
| **AI 只输出语义 DSL** | 解耦内容与布局；Renderer 保证视觉一致性；LLM 不需要理解坐标系统 |
| **15 种 intent 类型** | 覆盖常见 PPT 场景，可扩展；每种类型有专门的 Composer 和 Layout |
| **RAG 混合检索 + RRF 融合** | 向量语义匹配 + 关键词精确匹配 + 网络最新信息，多源互补 |
| **LangGraph 编排** | 多路并行检索 + 结构化状态管理；比硬编码 if/else 更灵活 |
| **三层容错（Fallback + Repair）** | 600 行修复代码 + 默认 14 页 PPT，确保任何情况下系统都有可用输出 |
| **内存任务队列** | MVP 阶段避免 Redis/Celery 复杂度；未来可无缝迁移 |
| **BGE-small-zh-v1.5** | 512 维中英双语，轻量高效；与 Milvus IP 度量匹配 |
| **文档自动入库** | 上传文档生成大纲时自动写入 KB，最大化知识复用 |
| **评估体系混合模式** | 规则指标免费确定；LLM Judge 提供语义洞察；用户可选择性开启 |
| **前端轻量** | Vanilla JS 理念（Vue 3 + Vite），构建产物 <200KB gzip |

---

## 8. 项目结构

```
TJ_SEME_program/
├── backend/
│   ├── ppt_backend/
│   │   ├── api/                          # FastAPI 主入口 + 路由
│   │   │   ├── main.py                   # 应用工厂 (CORS, 并发限制, Worker 启动)
│   │   │   └── routes.py                 # 全部 API 端点
│   │   ├── domain/                       # 领域模型 (Pydantic)
│   │   │   ├── dsl.py                    # 15 种语义化 Slides DSL
│   │   │   ├── render_tree.py            # RenderTree 模型
│   │   │   ├── presentation.py           # PresentationBundle 模型
│   │   │   ├── theme.py                  # ThemeToken 主题定义
│   │   │   └── ids.py                    # ID 生成器
│   │   ├── services/
│   │   │   ├── ai/                       # AI 生成管线
│   │   │   │   ├── pipeline.py           # 三阶段流水线 (意图→规划→DSL)
│   │   │   │   ├── client.py             # LLM 调用客户端
│   │   │   │   └── schemas.py            # IntentAnalysis / PresentationPlan
│   │   │   ├── rendering/                # 渲染引擎
│   │   │   │   ├── compiler.py           # DSL → RenderTree 编译器
│   │   │   │   ├── planning.py           # Component Planner
│   │   │   │   ├── layout.py             # 布局引擎
│   │   │   │   ├── layout_selector.py    # 布局模板选择
│   │   │   │   ├── theme_engine.py       # 主题引擎
│   │   │   │   └── registry.py           # 组件注册中心
│   │   │   ├── rag/                      # RAG 检索增强
│   │   │   │   ├── rag_service.py        # RAG 高层服务
│   │   │   │   ├── retrieval.py          # 混合检索器（核心）
│   │   │   │   ├── milvus_client.py      # Milvus 客户端
│   │   │   │   ├── embedding.py          # BGE 向量化服务
│   │   │   │   ├── web_search.py         # DuckDuckGo 网络搜索
│   │   │   │   ├── content_fetcher.py    # trafilatura 全文抓取
│   │   │   │   ├── knowledge_base.py     # 知识库管理
│   │   │   │   ├── rag_graph.py          # LangGraph 状态图
│   │   │   │   ├── seed_knowledge.py     # 种子知识引导
│   │   │   │   └── task_queue.py         # 异步导入任务队列
│   │   │   ├── evaluation/               # 评估体系
│   │   │   │   ├── schemas.py            # 评估数据模型
│   │   │   │   ├── metrics.py            # 规则指标 (BLEU, ROUGE-L, ...)
│   │   │   │   ├── rag_eval.py           # RAG 召回率/精确率
│   │   │   │   ├── llm_judge.py          # LLM-as-Judge 评分
│   │   │   │   └── evaluator.py          # 综合评估编排器
│   │   │   └── presentation_service.py   # 核心业务服务
│   │   ├── exporters/                    # 导出模块
│   │   │   ├── pptx_exporter.py          # PPTX 导出
│   │   │   └── pptx_components.py        # PPTX 组件渲染器
│   │   ├── repos/
│   │   │   └── presentation_repo.py      # 文件存储仓库
│   │   ├── container.py                  # 依赖注入容器
│   │   ├── settings.py                   # 配置管理 (dotenv)
│   │   └── rag_bootstrap.py              # 知识库初始化 CLI
│   └── requirements.txt
├── slideon-frontend/                     # 前端 (Vue 3 + Vite)
│   └── src/
│       ├── components/common/
│       │   ├── OutlineModal.vue          # 大纲创建（主题 + 文档上传）
│       │   ├── KnowledgeBasePanel.vue    # 知识库管理面板
│       │   ├── EvaluationPanel.vue       # 质量评估面板
│       │   ├── RadarChart.vue            # 雷达图 SVG 组件
│       │   └── MetricCard.vue            # 指标卡片组件
│       ├── views/
│       │   ├── DashboardView.vue         # 大纲管理 + KB 入口
│       │   ├── OutlineEditorView.vue     # 大纲编辑器 + 评估
│       │   └── BatchEvalView.vue         # 批量评估页面
│       ├── services/api.js               # API 服务层
│       ├── config/api.js                 # API 端点配置
│       └── router/index.js               # 前端路由
├── docs/
│   ├── superpowers/
│   │   ├── specs/                        # 设计规格文档
│   │   └── plans/                        # 实施计划文档
│   └── system-architecture.md            # 本文档
├── data/                                 # 运行时数据 (gitignored)
├── .env.example                          # 环境变量模板
└── README.md
```
