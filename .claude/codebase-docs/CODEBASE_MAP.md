# Slideon Codebase Documentation System

> 基于 codebase-memory-mcp 知识图谱自动生成 | 779 节点 · 767 边 · 79 Python · 19 Vue
> 生成日期: 2026-07-04

---

## 1. 系统分层架构 (Layered Architecture)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER                               │
│         slideon-frontend/  — Vue 3 + Vite + Pinia + Vue Router      │
│         10 Views · 6 Components · 3 Stores · 48 SVG Icons           │
├─────────────────────────────────────────────────────────────────────┤
│                          API LAYER                                   │
│              ppt_backend/api/  — FastAPI routes + auth               │
│          routes.py (27 endpoints) · auth_routes.py (8 endpoints)     │
├─────────────────────────────────────────────────────────────────────┤
│                      BUSINESS LOGIC                                  │
│              ppt_backend/services/  — 6 service modules              │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────────────┐  │
│  │   AI     │   RAG    │Rendering │Evaluation│ presentation_svc │  │
│  │ Pipeline │ Retrieval│ Compiler │ Evaluator│   auth_service   │  │
│  │ (3-stage)│ (hybrid) │(15 comp) │ (3-mode) │                  │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│                        DOMAIN MODELS                                 │
│   ppt_backend/domain/  — Pydantic models (6 files, 40+ types)       │
│   dsl.py: 15 slide DSL types  ·  render_tree.py: component tree     │
│   presentation.py: bundles  ·  theme.py: 4 themes + design tokens   │
├─────────────────────────────────────────────────────────────────────┤
│                     INFRASTRUCTURE                                   │
│   SQLAlchemy ORM (4 models) · Alembic (5 migrations) · PostgreSQL   │
│   Milvus 3.0 (vector DB) · File-based repo · Dependency Injection   │
├─────────────────────────────────────────────────────────────────────┤
│                        EXPORT                                        │
│   ppt_backend/exporters/  — RenderTree → .pptx                      │
│   pptx_exporter.py · pptx_components.py (16 renderers)              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. 模块依赖关系图 (Module Dependency Map)

### 2.1 后端包结构 — 知识图谱完整节点

#### 📁 `ppt_backend/api/` — API 层 (5 files)
| 文件 | 关键符号 | 职责 |
|------|----------|------|
| `main.py` | `create_app()` | FastAPI 应用工厂 (CORS, 限流, 挂载路由) |
| `routes.py` | `router` (APIRouter), 27 endpoint funcs | 核心业务 API (DSL→渲染→导出→RAG→评估→大纲) |
| `auth_routes.py` | `router` (APIRouter), 8 endpoint funcs | 认证 API (注册/登录/刷新/profile/LLM配置) |
| `deps.py` | `get_db()`, `get_current_user()`, `get_optional_current_user()` | 依赖注入 (DB session, JWT 用户解码) |

#### 📁 `ppt_backend/domain/` — 领域模型 (6 files)
| 文件 | 关键符号 | 职责 |
|------|----------|------|
| `dsl.py` | `BaseSlideDSL`, 15 slide DSL types, `PresentationDSL` | **15 种幻灯片语义 DSL 定义** (Pydantic BaseModel) |
| `render_tree.py` | `RenderTree`, `ComponentSpec`, `StyleSpec`, `RenderSlide`, `ComponentPatch` | 渲染中间表示 |
| `presentation.py` | `PresentationBundle`, `PresentationMeta` | 完整的 Presentation 聚合根 |
| `theme.py` | `ThemeTokens`, `ThemeColors`, `ThemeTypography`, `ThemeSpacing`, `get_theme_tokens()` | 4 套主题设计 Token 系统 |
| `ids.py` | `new_id()` | 统一 ID 生成器 |

#### 📁 `ppt_backend/services/ai/` — AI 生成流水线 (5 files)
| 文件 | 关键符号 | 职责 |
|------|----------|------|
| `pipeline.py` | `AiPipeline` | **3 阶段生成流水线** + 600 行容错修复代码 |
| `client.py` | `invoke_llm_text()`, `parse_model()`, `make_llm()`, `_strip_markdown_fences()`, `_extract_json_substring()` | LLM 调用 + JSON 解析/修复 |
| `prompts.py` | `intent_analysis_prompt()`, `presentation_plan_prompt()`, `dsl_generation_prompt()` | LangChain Prompt Templates |
| `schemas.py` | `IntentAnalysis`, `PresentationPlan`, `SlideSkeleton` | 流水线中间数据模型 |
| `model_config.py` | `UserLLMConfig`, `LLMProviderSpec`, `list_public_providers()`, `make_chat_llm()` | 多提供商 LLM 配置 |

#### 📁 `ppt_backend/services/rag/` — RAG 系统 (11 files)
| 文件 | 关键符号 | 职责 |
|------|----------|------|
| `rag_service.py` | `RagService` | RAG 门面 (统一接口) |
| `retrieval.py` | `HybridRetriever` | **混合检索核心**: Milvus ANN + 关键词 + Web Search → RRF 融合 |
| `milvus_client.py` | `MilvusStore` | Milvus 向量数据库客户端 |
| `embedding.py` | `EmbeddingService` | BGE-small-zh-v1.5 嵌入 (512-dim) |
| `knowledge_base.py` | — | 文档摄入 + 分块 + 去重 |
| `web_search.py` | — | DuckDuckGo / 百度搜索 |
| `content_fetcher.py` | `ContentFetcher` | 网页全文提取 (trafilatura) |
| `rag_graph.py` | — | **LangGraph 状态图** — 并行多源检索编排 |
| `document_parser.py` | `parse_document()`, `compact_document_text()`, `DocumentParseError` | PDF/DOCX/PPTX/TXT/MD 解析 |
| `seed_knowledge.py` | — | 63 个种子主题 × 12 类别 Bootstrap |
| `task_queue.py` | `get_import_queue()` | 异步文档导入队列 |

#### 📁 `ppt_backend/services/rendering/` — 渲染引擎 (6 files)
| 文件 | 关键符号 | 职责 |
|------|----------|------|
| `compiler.py` | `RenderCompiler` | **DSL → RenderTree 编译器** |
| `planning.py` | `SlideComposer` (Protocol), 15 Composers | 15 种幻灯片 Composer (语义→组件蓝图) |
| `layout.py` | `LayoutTemplate` (Protocol), 9 Layouts, `Rect`, `_place_by_slot()` | 9 种布局算法 (绝对定位) |
| `theme_engine.py` | — | 主题 Token → 组件样式映射 |
| `registry.py` | `build_slide_composer_registry()`, `build_layout_registry()` | Composer + Layout 注册工厂 |
| `layout_selector.py` | `select_layout()` | 自动布局选择器 |

#### 📁 `ppt_backend/services/evaluation/` — 质量评估 (5 files)
| 文件 | 关键符号 | 职责 |
|------|----------|------|
| `evaluator.py` | `Evaluator` | 评估编排器 |
| `metrics.py` | `compute_bleu()`, `compute_rouge_l()`, `compute_structure_completeness()`, `compute_information_density()`, `compute_content_diversity()`, `compute_rule_metrics()` | 规则基础指标 (BLEU, ROUGE-L, 结构完整度, 信息密度, 内容多样性) |
| `llm_judge.py` | `LLMJudge`, `LLMJudgeScoresWithSuggestions` | LLM-as-Judge 语义评分 |
| `rag_eval.py` | `log_retrieval()`, `compute_rag_recall()`, `compute_rag_precision()` | RAG 检索评估 |
| `schemas.py` | `EvalResult`, `EvalReport`, `RuleMetrics`, `BatchEvalConfig` | 评估数据模型 |

#### 📁 顶层服务 (2 files)
| 文件 | 关键符号 | 职责 |
|------|----------|------|
| `presentation_service.py` | `PresentationService` | **核心业务编排** — 生成、渲染、导出、RAG 全流程 |
| `auth_service.py` | `AuthService`, `hash_password()`, `create_access_token()`, `create_refresh_token()` | JWT 认证 + 用户管理 |

#### 📁 `ppt_backend/exporters/` — PPTX 导出 (2 files)
| 文件 | 关键符号 | 职责 |
|------|----------|------|
| `pptx_exporter.py` | `PptxExporter` | RenderTree → PPTX 编排器 |
| `pptx_components.py` | 16 个 Renderer | 16 种 PPTX 组件渲染器 (Title, Subtitle, Text, BulletList, Divider, Quote, KpiCards, Timeline, ComparisonTable, Swot, Roadmap, ProcessFlow, Chart, MultiColumn, TeamCards, ArchitectureDiagram) |

#### 📁 Infrastructure & Storage (6 files)
| 文件 | 关键符号 | 职责 |
|------|----------|------|
| `database.py` | `Base`, `async_session_factory`, `get_db()` | SQLAlchemy async engine + session |
| `models/user.py` | `User` | 用户 ORM (id, email, password_hash, llm_provider, llm_api_key) |
| `models/refresh_token.py` | `RefreshToken` | 刷新 Token ORM (hashed, rotation tracking) |
| `models/presentation.py` | `Presentation` | 演示文稿 ORM |
| `models/outline.py` | `Outline` | 大纲 ORM |
| `repos/presentation_repo.py` | `PresentationRepository` (Protocol), `FilePresentationRepository` | **Repository Pattern** — 文件 JSON 存储 + 协议接口 |
| `settings.py` | `Settings` | 环境配置 (pydantic-settings) |
| `container.py` | `build_presentation_service()` | 依赖注入组装 |

---

### 2.2 前端结构 (Vue 3 SPA) — 30 源文件

```
slideon-frontend/src/
├── main.js                     # Vue app 入口
├── App.vue                     # 根组件
├── config/api.js               # API 端点配置
├── router/index.js             # Vue Router (10 routes)
├── services/
│   ├── api.js                  # Axios HTTP 客户端
│   └── auth.js                 # JWT 认证服务
├── stores/
│   ├── authStore.js            # 认证状态 (Pinia)
│   ├── kbTaskStore.js          # 知识库任务状态
│   └── outlineStore.js         # 大纲状态
├── composables/
│   └── useFloatingBall.js      # 浮动球 UI composable
├── views/                      # 10 页面组件
│   ├── HomeView.vue            # 首页 (Hero + CTA)
│   ├── EditorView.vue          # PPT 画布 (15+ 组件渲染)
│   ├── OutlineEditorView.vue   # DSL 大纲编辑器
│   ├── DashboardView.vue       # 大纲管理 Dashboard
│   ├── KnowledgeBaseView.vue   # 知识库文档管理
│   ├── BatchEvalView.vue       # 批量评估
│   ├── ProfileView.vue         # 用户资料 + LLM 配置
│   ├── LoginView.vue           # 登录
│   ├── RegisterView.vue        # 注册
│   └── TemplatesView.vue       # 模板浏览
├── components/
│   ├── common/                 # 6 个共享组件
│   │   ├── AppHeader.vue       # 导航栏
│   │   ├── OutlineModal.vue    # 生成模态框
│   │   ├── EvaluationPanel.vue # 质量评估面板
│   │   ├── KnowledgeBasePanel.vue # KB 管理面板
│   │   ├── RadarChart.vue      # SVG 雷达图
│   │   └── MetricCard.vue      # 评分卡片
│   └── icons/                  # 48 个自定义 SVG 图标
├── styles/                     # 4 个 CSS 文件 (variables, base, components, index)
└── utils/
    └── ids.js                  # 前端 ID 工具
```

---

## 3. 数据流与调用链 (Data Flow & Call Chains)

### 3.1 核心 PPT 生成流程

```
POST /presentations
    │
    ▼
[PresentationService.create_presentation()]
    │
    ├──▶ [RagService.enhance()]          ← 混合检索增强上下文
    │       ├── HybridRetriever.search()
    │       │   ├── MilvusStore.search()      (ANN 向量检索)
    │       │   ├── BM25 keyword search       (关键词搜索)
    │       │   └── WebSearch (DuckDuckGo/Baidu)
    │       └── RRF Fusion (倒数排序融合)
    │
    ├──▶ [AiPipeline.run()]              ← 3 阶段 AI 生成
    │       ├── Stage 1: IntentAnalysis   (意图分析)
    │       ├── Stage 2: PresentationPlan (结构规划, 15 intent types)
    │       └── Stage 3: PresentationDSL  (语义 DSL JSON)
    │            ↑
    │        3-layer fault tolerance:
    │        LLM retry → JSON repair (client.py 600+ lines) → default fallback
    │
    ├──▶ [RenderCompiler.compile()]      ← DSL → RenderTree
    │       ├── SlideComposer (15 types)  (planning.py)
    │       ├── LayoutTemplate (9 types)  (layout.py)
    │       └── theme_engine.apply()     (design token → styles)
    │
    ├──▶ [FilePresentationRepository.save()]  ← JSON bundle 持久化
    │
    └──▶ [PptxExporter.export()]         ← 按需导出
            └── ComponentRenderer (16 types)  (pptx_components.py)
```

### 3.2 认证调用链

```
POST /auth/login
    │
    ├──▶ AuthService.authenticate()
    │       ├── verify_password()        (bcrypt)
    │       ├── create_access_token()    (JWT HS256, 30min)
    │       └── create_refresh_token()   (JWT + DB rotation)
    │
POST /auth/refresh
    │
    ├──▶ decode_token()
    ├──▶ DB lookup RefreshToken (hashed)
    ├──▶ Token rotation: delete old → create new pair
    └──▶ Return new access_token + refresh_token
```

### 3.3 知识库文档导入流程

```
POST /rag/documents/batch
    │
    ├──▶ get_import_queue().enqueue()
    │       └── Async background task
    │            ├── parse_document()          (PDF/DOCX/PPTX/TXT/MD)
    │            ├── chunk document            (语义分块)
    │            ├── EmbeddingService.embed()  (BGE-small-zh-v1.5)
    │            └── MilvusStore.insert()      (向量存储 + 元数据)
    │
GET /rag/documents
    │
    └──▶ MilvusStore.list_sources()    → 元数据列表
```

### 3.4 评估调用链

```
POST /eval/single/{id}
    │
    ├──▶ Evaluator.evaluate()
    │       ├── compute_rule_metrics()         (BLEU, ROUGE-L, 结构完整度, 信息密度, 内容多样性)
    │       ├── LLMJudge.score()               (语义评分: 结构合理性, 事实准确, 逻辑连贯, 内容深度)
    │       └── compute_rag_recall/precision() (RAG 检索评估)
    │
    └──▶ EvalReport                         → 综合评估报告
```

---

## 4. 领域模型 (Domain Model Catalog)

### 4.1 DSL 类型层级 (15 types)
```
BaseSlideDSL (抽象基类)
├── CoverSlideDSL          — 封面
├── AgendaSlideDSL         — 目录
├── TextSlideDSL           — 文本
├── TimelineSlideDSL       — 时间线 (TimelineEvent[])
├── KpiSlideDSL            — KPI 指标 (KPIItem[])
├── ComparisonSlideDSL     — 对比 (ComparisonSide[])
├── SwotSlideDSL           — SWOT 分析 (SwotBlock)
├── RoadmapSlideDSL        — 路线图 (RoadmapPhase[])
├── ProcessFlowSlideDSL    — 流程图 (ProcessStep[])
├── ChartSlideDSL          — 图表 (ChartSeries[], ChartSemantic)
├── MultiColumnSlideDSL    — 多栏 (ColumnBlock[])
├── ArchitectureSlideDSL   — 架构图 (ArchitectureLayer[])
├── QuoteSlideDSL          — 引用
├── DividerSlideDSL        — 分隔页
└── TeamSlideDSL           — 团队 (TeamMember[])

PresentationDSL            — 聚合根: slides[], title, meta
```

### 4.2 RenderTree 模型
```
RenderTree
├── slides: RenderSlide[]
│   └── components: ComponentSpec[]
│       ├── id, type, slot (position key)
│       ├── content: dict (semantic data)
│       └── style: StyleSpec (theme-applied)
└── theme: str

ComponentPatch            — 用户编辑用增量 patch
```

### 4.3 Theme 模型
```
ThemeTokens
├── colors: ThemeColors      (12 color tokens)
├── typography: ThemeTypography  (6 font tokens)
├── spacing: ThemeSpacing    (6 spacing tokens)
├── radii: dict             (corner radius tokens)
└── shadows: dict           (shadow tokens)

Built-in themes:
1. modern_blue    — 科技/蓝色系
2. paper_light    — 教育/浅色系
3. academic_gray  — 报告/灰度系
4. minimal_black  — 创意/深色系
```

### 4.4 AI Pipeline 中间模型
```
IntentAnalysis
├── topic: str
├── domain: str
├── audience: str
├── depth: str (overview | detailed | comprehensive)
└── suggested_slide_types: list[str]

PresentationPlan
├── title: str
├── subtitle: str
└── slides: SlideSkeleton[]
    └── intent: str, title: str, description: str
```

---

## 5. API 端点完整清单 (35 端点)

### 5.1 核心业务 API (`routes.py`)

| # | Method | Path | Function | 功能 |
|---|--------|------|----------|------|
| 1 | GET | `/health` | `health()` | 健康检查 |
| 2 | GET | `/llm/providers` | `list_llm_providers()` | LLM 提供商列表 |
| 3 | GET | `/themes` | `list_themes()` | 主题列表 |
| 4 | POST | `/outline` | `generate_outline()` | 从文本生成 DSL 大纲 |
| 5 | POST | `/dsl/from-document` | `dsl_from_document()` | 从文档生成 DSL 大纲 |
| 6 | POST | `/compile` | `compile_outline()` | 编译大纲为 RenderTree |
| 7 | GET | `/presentations` | `list_presentations()` | 分页列出 Presentation |
| 8 | POST | `/presentations` | `create_presentation()` | 完整创建 (DSL+render+save) |
| 9 | GET | `/presentations/{id}` | `get_presentation()` | 获取完整 Bundle |
| 10 | GET | `/presentations/{id}/dsl` | `get_dsl()` | 获取 DSL |
| 11 | GET | `/presentations/{id}/render-tree` | `get_render_tree()` | 获取 RenderTree |
| 12 | PATCH | `/presentations/{id}/components/{cid}` | `patch_component()` | 编辑单个组件 |
| 13 | PUT | `/presentations/{id}/reorder` | `reorder_slides()` | 重排幻灯片 |
| 14 | PUT | `/presentations/{id}/theme` | `switch_theme()` | 切换主题 + 重渲染 |
| 15 | POST | `/presentations/{id}/regenerate` | `regenerate()` | 重新生成 |
| 16 | GET | `/presentations/{id}/export/pptx` | `export_pptx()` | 下载 .pptx |
| 17 | POST | `/rag/search` | `rag_search()` | RAG 混合搜索 |
| 18 | POST | `/rag/enhance` | `rag_enhance()` | RAG 增强上下文 |
| 19 | POST | `/rag/documents` | `rag_upload_document()` | 上传文档 |
| 20 | POST | `/rag/documents/batch` | `rag_upload_documents_batch()` | 批量异步上传 |
| 21 | GET | `/rag/documents` | `rag_list_documents()` | 列出文档 |
| 22 | GET | `/rag/sources` | `rag_list_sources()` | 列出来源 |
| 23 | DELETE | `/rag/sources/{source}` | `rag_remove_document()` | 删除文档 |
| 24 | GET | `/rag/preview/{source}` | `rag_preview_document()` | 预览文档内容 |
| 25 | GET | `/rag/stats` | `rag_stats()` | RAG 统计 |
| 26 | DELETE | `/rag/all` | `rag_clear_all()` | 清空全部文档 |
| 27 | POST | `/rag/init` | `rag_init_collection()` | 初始化 Milvus collection |
| 28 | POST | `/rag/reset` | `rag_reset_collection()` | 重置 collection |
| 29 | POST | `/rag/bootstrap` | `rag_bootstrap()` | 导入 63 个种子主题 |
| 30 | POST | `/eval/single/{id}` | `eval_single()` | 单次评估 |
| 31 | POST | `/eval/batch` | `eval_batch()` | 批量多配置评估 |
| — | GET | `/tasks/{task_id}` | `get_task_status()` | 异步任务状态 |
| — | CRUD | `/outlines` | 5 endpoints | 用户大纲 CRUD |

### 5.2 认证 API (`auth_routes.py` — 8 endpoints)

| # | Method | Path | Function | 功能 |
|---|--------|------|----------|------|
| 1 | POST | `/auth/register` | `register()` | 注册 |
| 2 | POST | `/auth/login` | `login()` | 登录 (返回 token pair) |
| 3 | POST | `/auth/refresh` | `refresh()` | Token 轮换刷新 |
| 4 | GET | `/auth/me` | `get_me()` | 获取当前用户 |
| 5 | PUT | `/auth/me` | `update_me()` | 更新当前用户 |
| 6 | GET | `/auth/llm-config` | `get_llm_config()` | 获取 LLM 配置 |
| 7 | PUT | `/auth/llm-config` | `update_llm_config()` | 更新 LLM 配置 |
| 8 | POST | `/auth/logout` | `logout()` | 登出 |

---

## 6. PPTX 组件渲染器与布局系统

### 6.1 16 种组件渲染器
| Renderer | 对应 Slide DSL | 产出的 PPTX 元素 |
|----------|---------------|-------------------|
| `TitleRenderer` | CoverSlideDSL | 标题文本框 + 副标题 |
| `SubtitleRenderer` | CoverSlideDSL | 副标题文本框 |
| `TextRenderer` | TextSlideDSL | 正文文本框 |
| `BulletListRenderer` | AgendaSlideDSL | 项目符号列表 |
| `DividerRenderer` | DividerSlideDSL | 分隔线/过渡页 |
| `QuoteRenderer` | QuoteSlideDSL | 引用文本框 |
| `KpiCardsRenderer` | KpiSlideDSL | KPI 卡片 (4 个矩形 + 值 + 标签) |
| `TimelineRenderer` | TimelineSlideDSL | 时间线 (轴线 + 节点 + 文本) |
| `ComparisonTableRenderer` | ComparisonSlideDSL | 对比表格 (2 列 × N 行) |
| `SwotRenderer` | SwotSlideDSL | SWOT 四象限网格 |
| `RoadmapRenderer` | RoadmapSlideDSL | 路线图 (阶段条 + 交付物) |
| `ProcessFlowRenderer` | ProcessFlowSlideDSL | 流程图 (步骤 + 箭头) |
| `ChartRenderer` | ChartSlideDSL | 原生 PowerPoint 图表 (bar/pie/line) |
| `MultiColumnRenderer` | MultiColumnSlideDSL | 多栏文本 (2-4 列) |
| `TeamCardsRenderer` | TeamSlideDSL | 团队成员卡片 |
| `ArchitectureDiagramRenderer` | ArchitectureSlideDSL | 分层架构图 |

### 6.2 9 种布局模板
| Layout | 适用 Slide 类型 | 定位策略 |
|--------|----------------|----------|
| `CoverLayout` | Cover | Title 居中 + Subtitle 下方 |
| `TitleBodyLayout` | Text, Agenda, Quote | Title 顶部 + Body 填充剩余空间 |
| `TwoColumnLayout` | Comparison, MultiColumn(2) | 左右对半分割 |
| `Grid2x2Layout` | SWOT, KPI | 4 象限网格 |
| `TimelineLayout` | Timeline | 水平时间线 + 节点散点 |
| `ProcessFlowLayout` | ProcessFlow | 水平步骤条 |
| `ChartLayout` | Chart | Title 顶部 + Chart 主体 |
| `RoadmapLayout` | Roadmap | 垂直 Phase 堆叠 |
| `ArchitectureLayout` | Architecture | 垂直 Layer 堆叠 + 箭头 |

---

## 7. 测试体系

| 测试类型 | 文件 | 覆盖范围 |
|----------|------|----------|
| Unit | `test/unit/test_auth_and_config.py` | 认证 + 用户 LLM 配置 |
| Unit | `test/unit/test_auth_routes.py` | 认证 API 路由 |
| Unit | `test/unit/test_dsl_repair.py` | DSL JSON 修复逻辑 |
| Unit | `test/unit/test_document_processing.py` | 文档解析 + 分块 |
| Unit | `test/unit/test_evaluation_metrics.py` | BLEU/ROUGE-L/结构完整度 |
| Unit | `test/unit/test_persistence_contracts.py` | Repository 契约 |
| Unit | `test/unit/test_rag_retrieval.py` | RAG 检索 |
| Unit | `test/unit/test_traceability_mapping.py` | 需求追溯 |
| Fixtures | `test/sample_deck_fixtures.py` | 测试数据 (已知好的 RenderTree/DSL) |
| Integration | `test/integration/` | API 冒烟 + 渲染往返 + 服务生命周期 |
| Contract | `test/scripts/run_api_contract_tests.py` | API 契约验证 |
| E2E | `test/scripts/run_frontend_e2e_tests.py` | 前端端到端流程 |
| Static | `test/scripts/run_frontend_static_tests.py` | 前端代码静态分析 |

---

## 8. 实验数据体系

```
experiment/
├── Experiment Design/
│   ├── experiment_protocol.md       # 实验协议 (4 阶段)
│   ├── prompt_strategies.json       # Prompt 策略定义
│   └── test_cases.json              # 测试用例矩阵
├── Alzheimer Disease/               # 领域 1: 医学
├── Football/                        # 领域 2: 体育
├── Software Engineering/            # 领域 3: 计算机科学
└── Report Assets/
    ├── raw_outputs/                 # 164 个 LLM JSON 输出
    ├── stage1_experiment_summary.md # 阶段 1: 模型可用性
    ├── stage2_experiment_summary.md # 阶段 2: 稳定性测试
    ├── stage3_manual_quality_summary.md # 阶段 3: 人工质量评估
    ├── stage4_prompt_schema_summary.md  # 阶段 4: Prompt 策略对比
    └── *.csv                        # 60+ CSV 汇总表
```

---

## 9. 知识图谱统计汇总

| 层级 | 文件数 | 关键符号数 |
|------|--------|-----------|
| API Layer | 5 | 35 endpoints, 20 Pydantic models |
| Domain Layer | 6 | 40+ Pydantic models |
| Services/AI | 5 | AiPipeline, 3 prompts, LLM client |
| Services/RAG | 11 | HybridRetriever, MilvusStore, LangGraph |
| Services/Rendering | 6 | 15 Composers, 9 Layouts, RenderCompiler |
| Services/Evaluation | 5 | Evaluator, LLMJudge, 10+ metric funcs |
| Services/Core | 2 | PresentationService, AuthService |
| Exporters | 2 | PptxExporter, 16 ComponentRenderers |
| Infrastructure | 6 | 4 ORM models, DB engine, repo |
| Config | 3 | Settings, container, bootstrap |
| Frontend | 30 | 10 views, 6 components, 3 stores |
| Tests | 10 | 8 unit + integration + fixtures |
| **总计** | **91** | **250+ classes & functions** |

---

## 10. 架构决策记录 (ADR Index)

已通过 `codebase-memory-mcp manage_adr` 工具持久化 7 条架构决策：

| ADR | 标题 | 核心决策 |
|-----|------|----------|
| ADR-001 | DSL-Driven Architecture | AI 只输出语义 DSL，渲染器处理视觉 |
| ADR-002 | 3-Stage AI Pipeline | 意图分析 → 结构规划 → DSL 生成 |
| ADR-003 | Hybrid RAG + LangGraph | Milvus + 关键词 + Web Search → RRF 融合 |
| ADR-004 | 15 Slide Intent Types | 标准化 15 种幻灯片类型，每种 4 层实现 |
| ADR-005 | File-Based JSON Storage | MVP 文件存储，Repository Pattern 可迁移 |
| ADR-006 | Per-User LLM Config | 用户自有 API Key，多提供商热切换 |
| ADR-007 | 3-Layer Fault Tolerance | LLM 重试 → JSON 修复 (600行) → 默认后备 |

---

## 11. 演进路线图

| 当前状态 | 推荐演进 | 优先级 |
|---------|---------|--------|
| 内存任务队列 | → Redis + Celery/RQ | HIGH |
| 文件 JSON 存储 | → S3/MinIO 对象存储 | MEDIUM |
| 本地 Milvus | → Milvus Cloud / Zilliz | MEDIUM |
| FastAPI 内置限流 | → API Gateway + 分布式限流 | LOW |
| logging 模块 | → OpenTelemetry + Sentry | LOW |
| 无缓存层 | → Redis 缓存热点 RAG 查询 | MEDIUM |

---

> 📖 **如何使用本文档系统**:
> - 新成员入职: 从 §1 架构图开始 → §2 模块职责 → §3 数据流
> - 开发新功能: 定位 §4 领域模型 → §5 API 端点 → 对应 §2 模块
> - 架构评审: 参考 §10 ADR 决策记录 → §11 演进路线图
> - 调试排查: §3 调用链追溯 → §6 组件映射表
