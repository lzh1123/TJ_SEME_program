# Slideon User Manual RBS Traceability Matrix

本矩阵用于说明《Slideon 用户手册》如何覆盖 final RBS。当前手册定位为“面向普通网站用户的操作教程”，不再写成开发者部署手册；涉及开发环境、后端和 API 的 RBS 项，在手册中转化为用户可感知的登录、生成、保存、上传、编辑和导出流程。

| RBS | 最终需求 | 用户手册覆盖方式 | 主要依据 |
| --- | --- | --- | --- |
| 1.0 | Dev Environment Building | 第 2 章说明普通用户使用前准备：浏览器、网络、账号、主题和可选资料 | `HomeView.vue`、`AppHeader.vue`、手册截图 |
| 1.1 | Dependency Installation | 用户无需安装依赖；手册改为说明使用网站所需条件 | `README.md`、前端页面入口 |
| 1.2 | Version Control Setup | 用户无需配置版本控制；手册不展开开发者 Git 操作 | final RBS、用户手册定位 |
| 2.0 | Backend & API | 以用户功能呈现：注册、登录、保存大纲、生成 PPT、知识库上传 | `auth_routes.py`、`routes.py`、`api.js`、前端页面 |
| 2.1 | Backend Framework Setup | 用户无需启动后端；手册以“网站可访问后如何使用”为前提 | `main.py`、`HomeView.vue` |
| 2.2 | API Design | 用户不直接调用 API；手册按页面和按钮组织功能 | `api.js`、`AppHeader.vue` |
| 2.3 | API Implementation | 通过页面操作体现 API 能力：生成、保存、删除、预览、导出 | `routes.py`、`api.js` |
| 2.4 | Database Integration | 以用户可见的“账号、大纲、知识库资料可保存”体现 | `DashboardView.vue`、`KnowledgeBaseView.vue` |
| 2.5 | Authentication | 第 3 章：注册、登录、个人资料、退出登录 | `LoginView.vue`、`RegisterView.vue`、`ProfileView.vue`、相关截图 |
| 3.0 | Frontend | 第 2-9 章介绍首页、导航、我的大纲、大纲编辑器、PPT 编辑器、知识库 | `router/index.js`、`views/`、`components/common/` |
| 3.1 | Frontend Setup | 用户不需要安装前端；手册说明打开网站后的主要页面 | `HomeView.vue`、`AppHeader.vue` |
| 3.2 | UI Components Development | 通过按钮、输入框、上传区、列表、预览弹窗等操作说明体现 | `OutlineModal.vue`、`DashboardView.vue`、`KnowledgeBaseView.vue` |
| 3.3 | API Integration Frontend | 用户通过页面触发接口，手册不写接口细节 | `api.js`、`auth.js` |
| 3.4 | Responsive Design | 常见问题中提示复杂编辑建议使用电脑浏览器 | `OutlineEditorView.vue`、`KnowledgeBaseView.vue` |
| 4.0 | Data & Prompt Engineering | 第 4-5 章说明主题输入和文档输入；第 10 章说明 RAG 资料增强 | `OutlineModal.vue`、`prompts.py` |
| 4.1 | Prompt Template Design | 用户侧表现为“主题写清楚，生成更贴合需求” | `prompts.py`、第 13 章使用建议 |
| 4.2 | Input Preprocessing | 第 5 章说明上传文档生成大纲；第 9 章说明知识库资料上传 | `document_parser.py`、`OutlineModal.vue`、`KnowledgeBaseView.vue` |
| 4.3 | Output Postprocessing | 第 7 章说明检查、编辑、保存 AI 生成的大纲 | `pipeline.py`、`OutlineEditorView.vue` |
| 5.0 | Outline Generation | 第 4-7 章：从主题/文档生成大纲并编辑结构 | `OutlineModal.vue`、`OutlineEditorView.vue` |
| 5.1 | Topic Analysis | 第 4 章：输入主题、描述用途、受众和重点 | `OutlineModal.vue`、`prompts.py` |
| 5.2 | Outline Structuring | 第 7 章：添加页面、调整顺序、选择页面类型 | `OutlineEditorView.vue`、`dsl.py` |
| 5.3 | Section Allocation | 第 7 章：页面列表、章节名、页面类型和内容编辑 | `OutlineEditorView.vue` |
| 6.0 | Content Generation | 第 7.9 和第 8 章：从大纲生成 PPT 并查看结果 | `OutlineEditorView.vue`、`EditorView.vue` |
| 6.1 | Slide Content Generation | 第 7.5-7.6 说明 15 类页面类型和内容填写项 | `dsl.py`、`OutlineEditorView.vue` |
| 6.2 | Content Refinement | 第 7 章：编辑标题、段落、要点、图表、KPI、SWOT 等 | `OutlineEditorView.vue` |
| 6.3 | Multi-slide Consistency | 第 7 章通过统一大纲结构和页面类型编辑体现 | `theme.py`、`OutlineEditorView.vue` |
| 7.0 | RAG Implementation | 第 9-10 章：知识库和 RAG 增强生成 | `KnowledgeBaseView.vue`、`rag_service.py` |
| 7.1 | Document Indexing | 第 9.2：上传知识库资料并等待处理 | `KnowledgeBaseView.vue`、`document_parser.py` |
| 7.2 | Retrieval Mechanism | 第 10 章用普通用户语言解释 RAG 参考资料生成 | `retrieval.py`、`rag_service.py` |
| 7.3 | Context Injection | 第 10.2：在主题生成中开启“混合 RAG 增强” | `OutlineModal.vue`、`pipeline.py` |
| 8.0 | Rendering & Export | 第 7.9、第 8 章：生成 PPT、查看页面、导出 PPTX | `EditorView.vue`、`pptx_exporter.py` |
| 8.1 | Template Design | 第 7.1 提到主题样式作为用户可编辑基本信息 | `theme.py`、`OutlineEditorView.vue` |
| 8.2 | Slide Rendering | 第 8 章：PPT 编辑器查看生成后的页面 | `EditorView.vue`、`compiler.py` |
| 8.3 | File Export | 第 8.4：导出 PPTX 并用 PowerPoint 或 WPS 继续编辑 | `pptx_exporter.py`、`api.js` |

## 审核结论

- 手册已从开发者手册改为普通用户教程。
- 批量评估功能已从用户手册中删除，因为当前系统不提供该用户功能。
- 手册正文嵌入了 `res/picture` 中的 19 张前端使用截图，覆盖登录、生成、大纲管理、大纲编辑、知识库和 PPT 生成等主要用户路径。
- final RBS 中偏工程实现的项目，均以用户可见功能或使用前准备方式呈现，避免让普通用户阅读安装依赖、启动服务或 API 调用说明。
