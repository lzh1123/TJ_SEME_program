# Slideon - PPT Outline Intelligent Generation and Content Completion System
# 项目设计文档

## 一、项目工作内容总结

### 1. Project Planning - 项目规划与启动
| 阶段 | 工作内容 | 交付物 |
|------|----------|--------|
| 项目启动 | 确定项目目标、范围、里程碑 | 项目章程 |
| 团队分工 | 定义角色职责、技术栈选型 | 团队组织架构图 |
| 需求收集 | 用户需求调研、竞品分析 | 需求规格说明书 |
| 需求分析 | 用户流程、用例设计 | 用例图、流程图 |

### 2. System Design - 系统设计
| 设计领域 | 核心内容 | 交付物 |
|----------|----------|--------|
| 架构设计 | 系统整体架构、技术选型 | 架构图、技术栈文档 |
| 数据库设计 | 数据模型、表结构设计 | ERD图、Schema定义 |
| UI设计 | 界面原型、交互设计 | 原型图、设计规范 |
| AI设计 | Prompt工程、模型选择 | Prompt模板、模型配置 |
| RAG设计 | 检索策略、知识库构建 | RAG流程图、向量库设计 |

---

## 二、架构设计 (Architecture Design)

### 2.1 系统整体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              前端层 (Frontend)                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Web App    │  │   Editor     │  │   Preview    │  │   Dashboard  │    │
│  │  (React/Vue) │  │  (Canvas)    │  │   (Slide)    │  │   (Admin)    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API网关层 (Gateway)                             │
│                    ┌─────────────────────────────────┐                      │
│                    │      Nginx / Kong Gateway       │                      │
│                    │  - 负载均衡  - 限流  - 认证      │                      │
│                    └─────────────────────────────────┘                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             服务层 (Backend Services)                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   User Service  │  │  PPT Service    │  │  AI Service     │             │
│  │  - 用户管理      │  │  - 大纲生成      │  │  - 内容生成      │             │
│  │  - 认证授权      │  │  - 内容填充      │  │  - 智能建议      │             │
│  │  - 权限控制      │  │  - 模板管理      │  │  - 风格迁移      │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │ Template Service│  │ Export Service  │  │ RAG Service     │             │
│  │  - 模板库        │  │  - PPT导出       │  │  - 知识检索      │             │
│  │  - 样式管理      │  │  - PDF导出       │  │  - 向量搜索      │             │
│  │  - 主题配置      │  │  - 图片导出      │  │  - 上下文增强    │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AI引擎层 (AI Engine)                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   LLM Engine    │  │  Embedding      │  │  RAG Pipeline   │             │
│  │  - GPT-4/Claude │  │  - text-embedding│  │  - 检索器        │             │
│  │  - 本地模型      │  │  - 向量编码      │  │  - 重排序        │             │
│  │  - 多模型路由    │  │  - 语义理解      │  │  - 生成器        │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              数据层 (Data Layer)                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   PostgreSQL    │  │   Redis         │  │  Vector DB      │             │
│  │  - 用户数据      │  │  - 缓存         │  │  - 知识向量      │             │
│  │  - PPT元数据     │  │  - 会话         │  │  - 模板向量      │             │
│  │  - 模板数据      │  │  - 限流         │  │  - 语义索引      │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│  ┌─────────────────┐  ┌─────────────────┐                                   │
│  │   MinIO/S3      │  │   Elasticsearch │                                   │
│  │  - 文件存储      │  │  - 全文检索      │                                   │
│  │  - 图片资源      │  │  - 日志分析      │                                   │
│  └─────────────────┘  └─────────────────┘                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈选型

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| **前端** | React 18 + TypeScript + Ant Design | 现代化UI框架，类型安全 |
| **前端编辑** | Fabric.js / PptxGenJS | PPT编辑与生成 |
| **后端** | Python 3.10+ / FastAPI | 高性能异步框架 |
| **AI/ML** | LangChain + OpenAI API / 本地模型 | AI编排与模型调用 |
| **向量数据库** | ChromaDB / Milvus / Pinecone | 语义检索存储 |
| **数据库** | PostgreSQL 15 | 关系型数据存储 |
| **缓存** | Redis 7 | 高性能缓存与会话 |
| **消息队列** | Celery + RabbitMQ/Redis | 异步任务处理 |
| **文件存储** | MinIO / AWS S3 | 对象存储 |
| **部署** | Docker + Kubernetes | 容器化与编排 |
| **监控** | Prometheus + Grafana | 监控与告警 |

### 2.3 核心服务接口设计

```python
# 主要API端点设计

# 用户服务
POST   /api/v1/auth/register          # 用户注册
POST   /api/v1/auth/login             # 用户登录
POST   /api/v1/auth/refresh           # Token刷新
GET    /api/v1/users/me               # 获取当前用户
PUT    /api/v1/users/me               # 更新用户信息

# PPT服务
POST   /api/v1/ppts                   # 创建PPT
GET    /api/v1/ppts                   # 获取PPT列表
GET    /api/v1/ppts/{id}              # 获取PPT详情
PUT    /api/v1/ppts/{id}              # 更新PPT
DELETE /api/v1/ppts/{id}              # 删除PPT
POST   /api/v1/ppts/{id}/outline      # 生成大纲
POST   /api/v1/ppts/{id}/content      # 填充内容
POST   /api/v1/ppts/{id}/export       # 导出PPT

# AI服务
POST   /api/v1/ai/outline/generate    # 智能生成大纲
POST   /api/v1/ai/content/generate    # 智能生成内容
POST   /api/v1/ai/suggest             # 智能建议
POST   /api/v1/ai/style/transfer      # 风格迁移
POST   /api/v1/ai/chat                # AI对话助手

# 模板服务
GET    /api/v1/templates              # 获取模板列表
GET    /api/v1/templates/{id}         # 获取模板详情
POST   /api/v1/templates/{id}/apply   # 应用模板

# RAG服务
POST   /api/v1/rag/search             # 知识检索
POST   /api/v1/rag/upload             # 上传知识文档
```

---

## 三、数据库设计 (Database Design)

### 3.1 ERD 实体关系图

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│     users       │       │     ppts        │       │   templates     │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)         │──┐    │ id (PK)         │    ┌──│ id (PK)         │
│ email           │  │    │ user_id (FK)    │────┘  │ name            │
│ username        │  │    │ template_id(FK) │───────│ description     │
│ password_hash   │  │    │ title           │       │ category        │
│ avatar_url      │  │    │ description     │       │ thumbnail_url   │
│ created_at      │  │    │ status          │       │ config_json     │
│ updated_at      │  │    │ outline_json    │       │ is_public       │
└─────────────────┘  │    │ content_json    │       │ created_by      │
                     │    │ settings_json   │       │ created_at      │
                     │    │ created_at      │       └─────────────────┘
                     │    │ updated_at      │
                     │    └─────────────────┘
                     │              │
                     │              │
                     │    ┌─────────────────┐
                     │    │  ppt_slides     │
                     │    ├─────────────────┤
                     │    │ id (PK)         │
                     │    │ ppt_id (FK)     │
                     └───>│ created_by (FK) │
                          │ slide_index     │
                          │ layout_type     │
                          │ title           │
                          │ content_json    │
                          │ notes           │
                          │ created_at      │
                          └─────────────────┘

┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  knowledge_docs │       │  vector_store   │       │   ai_sessions   │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)         │       │ id (PK)         │       │ id (PK)         │
│ user_id (FK)    │───────│ doc_id (FK)     │       │ user_id (FK)    │
│ filename        │       │ embedding       │       │ ppt_id (FK)     │
│ file_path       │       │ metadata        │       │ session_type    │
│ file_type       │       │ chunk_text      │       │ messages_json   │
│ file_size       │       │ created_at      │       │ context_json    │
│ processed       │       └─────────────────┘       │ created_at      │
│ created_at      │                                 │ updated_at      │
└─────────────────┘                                 └─────────────────┘
```

### 3.2 数据库表结构

```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_premium BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PPT项目表
CREATE TABLE ppts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    template_id UUID REFERENCES templates(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'draft', -- draft, generating, completed, archived
    outline_json JSONB, -- 大纲结构
    content_json JSONB, -- 完整内容
    settings_json JSONB DEFAULT '{}', -- 页面设置、主题等
    ai_metadata JSONB, -- AI生成元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PPT幻灯片表
CREATE TABLE ppt_slides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ppt_id UUID NOT NULL REFERENCES ppts(id) ON DELETE CASCADE,
    slide_index INTEGER NOT NULL,
    layout_type VARCHAR(50) NOT NULL, -- title, content, two-column, etc.
    title VARCHAR(255),
    subtitle VARCHAR(255),
    content_json JSONB NOT NULL, -- 幻灯片内容结构
    speaker_notes TEXT, -- 演讲者备注
    ai_suggestions JSONB, -- AI建议
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ppt_id, slide_index)
);

-- 模板表
CREATE TABLE templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL, -- business, education, creative, etc.
    thumbnail_url TEXT,
    preview_images TEXT[],
    config_json JSONB NOT NULL, -- 模板配置：颜色、字体、布局等
    slide_layouts JSONB, -- 幻灯片布局定义
    is_public BOOLEAN DEFAULT FALSE,
    is_premium BOOLEAN DEFAULT FALSE,
    usage_count INTEGER DEFAULT 0,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 知识文档表
CREATE TABLE knowledge_docs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_type VARCHAR(50) NOT NULL, -- pdf, docx, txt, md
    file_size BIGINT,
    content_text TEXT, -- 提取的文本内容
    processed BOOLEAN DEFAULT FALSE,
    chunk_count INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI会话表
CREATE TABLE ai_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ppt_id UUID REFERENCES ppts(id) ON DELETE CASCADE,
    session_type VARCHAR(50) NOT NULL, -- outline, content, chat
    title VARCHAR(255),
    messages_json JSONB NOT NULL DEFAULT '[]', -- 对话历史
    context_json JSONB, -- 上下文信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 生成任务表
CREATE TABLE generation_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ppt_id UUID REFERENCES ppts(id) ON DELETE CASCADE,
    task_type VARCHAR(50) NOT NULL, -- outline, content, style_transfer
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    input_params JSONB,
    output_result JSONB,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_ppts_user_id ON ppts(user_id);
CREATE INDEX idx_ppts_status ON ppts(status);
CREATE INDEX idx_ppt_slides_ppt_id ON ppt_slides(ppt_id);
CREATE INDEX idx_templates_category ON templates(category);
CREATE INDEX idx_knowledge_docs_user_id ON knowledge_docs(user_id);
CREATE INDEX idx_ai_sessions_user_id ON ai_sessions(user_id);
CREATE INDEX idx_generation_tasks_status ON generation_tasks(status);
```

---

## 四、UI/UX 设计 (UI Design)

### 4.1 页面结构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Logo    Home    Templates    My PPTs    [Search...]    [User] [Settings]   │  ← Header
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │                    主工作区 (Main Workspace)                         │   │
│  │                                                                     │   │
│  │  ┌─────────────┐  ┌─────────────────────────────────────────────┐  │   │
│  │  │             │  │                                             │  │   │
│  │  │   侧边栏     │  │                                             │  │   │
│  │  │  Sidebar    │  │           编辑画布 Editor Canvas             │  │   │
│  │  │             │  │                                             │  │   │
│  │  │ - 大纲视图   │  │         ┌─────────────────────────┐         │  │   │
│  │  │ - 页面缩略图 │  │         │                         │         │  │   │
│  │  │ - 模板选择   │  │         │      幻灯片编辑区域      │         │  │   │
│  │  │ - AI助手    │  │         │                         │         │  │   │
│  │  │             │  │         │   [标题]                  │         │  │   │
│  │  │             │  │         │                         │         │  │   │
│  │  │             │  │         │   [内容区域]              │         │  │   │
│  │  │             │  │         │                         │         │  │   │
│  │  │             │  │         └─────────────────────────┘         │  │   │
│  │  │             │  │                                             │  │   │
│  │  └─────────────┘  └─────────────────────────────────────────────┘  │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  [保存] [撤销] [重做] [预览] [导出]    缩放: 100%    页面: 3/10              │  ← Footer
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 核心页面设计

#### 4.2.1 首页 / 仪表盘
```
┌─────────────────────────────────────────────────────────────────┐
│  [Hero区域]                                                      │
│  "智能PPT生成，让创作更高效"                                      │
│  [输入框: 描述你的PPT主题...] [开始生成]                          │
├─────────────────────────────────────────────────────────────────┤
│  [功能特性]                                                      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐               │
│  │ AI大纲   │ │ 智能填充 │ │ 模板库   │ │ 知识增强 │               │
│  │ 生成    │ │ 内容    │ │         │ │ RAG     │               │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘               │
├─────────────────────────────────────────────────────────────────┤
│  [最近项目]                                    [查看全部 →]      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐               │
│  │ PPT 1   │ │ PPT 2   │ │ PPT 3   │ │ PPT 4   │               │
│  │ [缩略图] │ │ [缩略图] │ │ [缩略图] │ │ [缩略图] │               │
│  │ 标题    │ │ 标题    │ │ 标题    │ │ 标题    │               │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘               │
├─────────────────────────────────────────────────────────────────┤
│  [热门模板]                                    [浏览全部 →]      │
│  [模板卡片网格...]                                               │
└─────────────────────────────────────────────────────────────────┘
```

#### 4.2.2 编辑器页面
```
┌─────────────────────────────────────────────────────────────────┐
│  [返回] 项目名称 [保存] [分享] [导出▼]                           │
├──────────┬──────────────────────────────────────────┬───────────┤
│          │                                          │           │
│  大纲    │                                          │   AI助手   │
│  ─────   │                                          │   ─────   │
│  ▼ 封面  │                                          │  ┌─────┐  │
│  ▶ 目录  │          幻灯片编辑画布                   │  │ 🤖  │  │
│  ▶ 第1章 │                                          │  └──┬──┘  │
│  ▶ 第2章 │         ┌──────────────┐                 │     │     │
│  ▶ 第3章 │         │              │                 │  有什么可以 │
│          │         │   [幻灯片]    │                 │  帮您的吗？ │
│  + 添加  │         │              │                 │           │
│  页面    │         └──────────────┘                 │  [输入框] │
│          │                                          │           │
│          │                                          │  快捷操作:  │
│  模板    │                                          │  • 优化内容 │
│  ─────   │                                          │  • 生成图片 │
│ [模板1]  │                                          │  • 调整风格 │
│ [模板2]  │                                          │           │
│ [模板3]  │                                          │           │
│          │                                          │           │
├──────────┴──────────────────────────────────────────┴───────────┤
│  [撤销] [重做] | [插入▼] [布局▼] [主题▼] | 缩放 [100%] | 3/10     │
└─────────────────────────────────────────────────────────────────┘
```

#### 4.2.3 AI大纲生成对话框
```
┌─────────────────────────────────────────────────────────────┐
│  智能生成PPT大纲                                    [×]      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  步骤 1: 输入主题                                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 描述你的PPT主题、目标受众和主要内容...                │    │
│  │                                                      │    │
│  │ 例如: "为科技公司CEO准备的产品发布会PPT，            │    │
│  │      介绍新一代AI芯片的性能优势"                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  [可选] 上传参考文档  [拖拽或点击上传PDF/DOCX/TXT]            │
│                                                              │
│  步骤 2: 选择风格                                            │
│  ○ 商务正式  ○ 创意活泼  ○ 学术严谨  ○ 简约现代              │
│                                                              │
│  步骤 3: 设置页数                                            │
│  预计页数: [10] 页 (推荐 8-20 页)                            │
│                                                              │
│                    [取消]  [开始生成 →]                      │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 设计规范

#### 色彩系统
```css
/* 主色调 */
--primary-500: #6366F1;      /* 靛蓝 - 主品牌色 */
--primary-600: #4F46E5;      /* 深靛蓝 - 悬停 */
--primary-100: #E0E7FF;      /* 浅靛蓝 - 背景 */

/* 功能色 */
--success-500: #10B981;      /* 绿色 - 成功 */
--warning-500: #F59E0B;      /* 橙色 - 警告 */
--error-500: #EF4444;        /* 红色 - 错误 */
--info-500: #3B82F6;         /* 蓝色 - 信息 */

/* 中性色 */
--gray-900: #111827;         /* 标题文字 */
--gray-700: #374151;         /* 正文文字 */
--gray-500: #6B7280;         /* 次要文字 */
--gray-200: #E5E7EB;         /* 边框 */
--gray-100: #F3F4F6;         /* 背景 */
--white: #FFFFFF;            /* 纯白背景 */
```

#### 字体规范
```css
/* 中文字体 */
font-family: "PingFang SC", "Microsoft YaHei", "Helvetica Neue", sans-serif;

/* 标题 */
--font-h1: 600 32px/1.25 var(--font-family);    /* 页面大标题 */
--font-h2: 600 24px/1.3 var(--font-family);     /* 区块标题 */
--font-h3: 600 18px/1.4 var(--font-family);     /* 卡片标题 */

/* 正文 */
--font-body: 400 14px/1.6 var(--font-family);   /* 正文内容 */
--font-small: 400 12px/1.5 var(--font-family);  /* 辅助文字 */
```

---

## 五、AI设计 (AI Design)

### 5.1 AI能力架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AI能力层 (AI Capabilities)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        LangChain 编排层                              │   │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │   │
│  │   │ Chains   │  │ Agents   │  │ Memory   │  │ Tools    │           │   │
│  │   └──────────┘  └──────────┘  └──────────┘  └──────────┘           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│         ┌──────────────────────────┼──────────────────────────┐             │
│         ▼                          ▼                          ▼             │
│  ┌──────────────┐          ┌──────────────┐          ┌──────────────┐      │
│  │   OpenAI     │          │    Claude    │          │   本地模型    │      │
│  │   GPT-4      │          │   Claude-3   │          │  ChatGLM3    │      │
│  │   GPT-3.5    │          │   Sonnet     │          │  Qwen2       │      │
│  └──────────────┘          └──────────────┘          └──────────────┘      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Prompt工程策略

#### 5.2.1 大纲生成 Prompt

```python
OUTLINE_GENERATION_PROMPT = """
你是一位专业的PPT设计专家。请根据用户输入的主题，生成一份结构清晰、逻辑严谨的PPT大纲。

## 用户输入
主题: {topic}
目标受众: {audience}
风格: {style}
预计页数: {page_count}
参考文档摘要: {context}

## 输出要求
1. 生成JSON格式的大纲，包含以下结构
2. 大纲层级：封面 → 目录 → 章节 → 内容页 → 结束页
3. 每页包含：标题、副标题、内容要点（3-5条）
4. 确保逻辑流畅，内容完整

## 输出格式
```json
{
  "title": "PPT标题",
  "slides": [
    {
      "type": "cover",
      "title": "封面标题",
      "subtitle": "副标题"
    },
    {
      "type": "table_of_contents",
      "title": "目录",
      "items": ["章节1", "章节2", "章节3"]
    },
    {
      "type": "chapter",
      "title": "第一章标题",
      "subtitle": "章节概述"
    },
    {
      "type": "content",
      "title": "页面标题",
      "layout": "title_content", 
      "bullet_points": ["要点1", "要点2", "要点3"]
    }
  ]
}
```

## 风格指南
- 商务正式: 专业术语，数据支撑，逻辑严密
- 创意活泼: 生动语言，案例丰富，互动性强
- 学术严谨: 理论深度，引用规范，论证充分
- 简约现代: 精炼表达，重点突出，视觉导向

请直接输出JSON，不要包含其他解释文字。
"""
```

#### 5.2.2 内容填充 Prompt

```python
CONTENT_GENERATION_PROMPT = """
你是一位专业的内容创作专家。请根据提供的大纲，为每一页PPT生成详细的内容。

## 输入信息
PPT主题: {ppt_title}
当前页面: 第{current_page}页 / 共{total_pages}页
页面类型: {slide_type}
页面标题: {slide_title}
内容要点: {bullet_points}
上下文: {context}
参考知识: {retrieved_knowledge}

## 输出要求
1. 为每个要点扩展成2-3句完整的说明文字
2. 内容要专业、准确、有深度
3. 适当使用数据、案例、引用增强说服力
4. 保持语言风格一致

## 输出格式
```json
{
  "title": "页面标题（可优化）",
  "subtitle": "副标题",
  "content": {
    "main_points": [
      {
        "heading": "要点1标题",
        "text": "详细说明文字..."
      },
      {
        "heading": "要点2标题", 
        "text": "详细说明文字..."
      }
    ],
    "supporting_data": [
      {
        "type": "statistic",
        "content": "数据或统计信息"
      }
    ],
    "suggested_visuals": [
      "建议的图表类型或图片概念"
    ]
  },
  "speaker_notes": "演讲者备注，包含关键提示和过渡语"
}
```

请直接输出JSON，确保内容高质量且适合PPT展示。
"""
```

#### 5.2.3 智能建议 Prompt

```python
SUGGESTION_PROMPT = """
你是一位PPT优化顾问。请分析当前PPT内容，提供改进建议。

## 当前PPT信息
标题: {ppt_title}
当前页面内容: {current_slide_content}
整体大纲: {outline}

## 分析维度
1. 内容完整性：是否覆盖了所有关键点
2. 逻辑连贯性：页面之间的过渡是否自然
3. 视觉建议：适合的图表、图片、布局
4. 表达优化：更精炼或更有力的表达方式
5. 数据支撑：可以补充的数据或案例

## 输出格式
```json
{
  "suggestions": [
    {
      "type": "content",
      "priority": "high",
      "issue": "发现的问题",
      "recommendation": "具体建议",
      "example": "改进示例"
    },
    {
      "type": "visual",
      "priority": "medium", 
      "recommendation": "建议使用柱状图展示数据对比",
      "reason": "数据对比更直观"
    }
  ],
  "quick_actions": [
    "优化标题",
    "添加数据",
    "调整布局",
    "生成图表"
  ]
}
```
"""
```

### 5.3 模型配置策略

| 任务类型 | 推荐模型 | 温度 | 说明 |
|----------|----------|------|------|
| 大纲生成 | GPT-4 / Claude-3-Opus | 0.7 | 需要创意和结构化能力 |
| 内容填充 | GPT-4 / Claude-3-Sonnet | 0.5 | 平衡创意和准确性 |
| 文本优化 | GPT-3.5 / Claude-3-Haiku | 0.3 | 快速、确定性输出 |
| 智能建议 | GPT-4 / Claude-3-Sonnet | 0.6 | 需要分析能力 |
| 聊天对话 | GPT-3.5-Turbo | 0.8 | 自然对话体验 |

### 5.4 多模型路由策略

```python
class ModelRouter:
    """智能模型路由，根据任务类型和复杂度选择最优模型"""
    
    MODEL_CONFIGS = {
        "outline_generation": {
            "primary": "gpt-4",
            "fallback": "claude-3-opus",
            "temperature": 0.7,
            "max_tokens": 4000
        },
        "content_generation": {
            "primary": "gpt-4",
            "fallback": "claude-3-sonnet", 
            "temperature": 0.5,
            "max_tokens": 2000
        },
        "text_optimization": {
            "primary": "gpt-3.5-turbo",
            "temperature": 0.3,
            "max_tokens": 1000
        },
        "chat": {
            "primary": "gpt-3.5-turbo",
            "temperature": 0.8,
            "max_tokens": 1500
        }
    }
    
    async def route(self, task_type: str, complexity: str) -> ModelConfig:
        """根据任务选择模型配置"""
        config = self.MODEL_CONFIGS.get(task_type)
        
        # 高复杂度任务强制使用最强模型
        if complexity == "high":
            config["primary"] = "gpt-4"
        
        return config
```

---

## 六、RAG设计 (RAG Design)

### 6.1 RAG系统架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RAG系统架构 (Retrieval-Augmented Generation)         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        知识摄取层 (Ingestion)                        │   │
│  │                                                                     │   │
│  │   文档上传 → 格式解析 → 文本提取 → 分块处理 → 向量化 → 存储索引        │   │
│  │                                                                     │   │
│  │   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌────────┐│   │
│  │   │  PDF    │   │  DOCX   │   │   TXT   │   │   MD    │   │  Web   ││   │
│  │   │ Parser  │   │ Parser  │   │ Parser  │   │ Parser  │   │ Crawler││   │
│  │   └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘   └───┬────┘│   │
│  │        └─────────────┴─────────────┴─────────────┴────────────┘     │   │
│  │                              │                                      │   │
│  │                              ▼                                      │   │
│  │   ┌─────────────────────────────────────────────────────────────┐  │   │
│  │   │                    文档处理流水线                            │  │   │
│  │   │  1. 文本清洗 → 2. 语义分块 → 3. 元数据提取 → 4. 向量化编码    │  │   │
│  │   └─────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        向量存储层 (Vector Store)                     │   │
│  │                                                                     │   │
│  │   ┌─────────────────────────────────────────────────────────────┐  │   │
│  │   │  Collection: user_knowledge_{user_id}                        │  │   │
│  │   │  ├─ Vector: 1536-dim (text-embedding-3-large)               │  │   │
│  │   │  ├─ Metadata: {doc_id, chunk_id, page_num, section, ...}    │  │   │
│  │   │  └─ Text: Original chunk content                            │  │   │
│  │   └─────────────────────────────────────────────────────────────┘  │   │
│  │                                                                     │   │
│  │   ┌─────────────────────────────────────────────────────────────┐  │   │
│  │   │  Collection: template_knowledge                              │  │   │
│  │   │  ├─ 行业模板知识库                                          │  │   │
│  │   │  ├─ 最佳实践案例                                            │  │   │
│  │   │  └─ 常用内容素材                                            │  │   │
│  │   └─────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        检索生成层 (Retrieval & Generation)           │   │
│  │                                                                     │   │
│  │   用户查询 → 查询理解 → 混合检索 → 重排序 → 上下文组装 → LLM生成      │   │
│  │                                                                     │   │
│  │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │   │
│  │   │Query        │  │Hybrid       │  │Reranker     │  │Context    │ │   │
│  │   │Understanding│→ │Retrieval    │→ │(Cross-      │→ │Builder    │ │   │
│  │   │             │  │(Vector+BM25)│  │Encoder)     │  │           │ │   │
│  │   └─────────────┘  └─────────────┘  └─────────────┘  └─────┬─────┘ │   │
│  │                                                            │       │   │
│  │                                                            ▼       │   │
│  │   ┌─────────────────────────────────────────────────────────────┐  │   │
│  │   │  Enhanced Prompt = Original Query + Retrieved Context       │  │   │
│  │   │  → LLM → Generated Content                                  │  │   │
│  │   └─────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 文档处理流水线

```python
class DocumentProcessor:
    """文档处理流水线"""
    
    async def process_document(self, file_path: str, doc_type: str) -> List[DocumentChunk]:
        """处理文档并返回分块结果"""
        
        # 1. 文档解析
        raw_text = await self.parse_document(file_path, doc_type)
        
        # 2. 文本清洗
        cleaned_text = self.clean_text(raw_text)
        
        # 3. 语义分块
        chunks = self.semantic_chunking(cleaned_text)
        
        # 4. 元数据提取
        enriched_chunks = await self.extract_metadata(chunks)
        
        # 5. 向量化
        embedded_chunks = await self.embed_chunks(enriched_chunks)
        
        return embedded_chunks
    
    def semantic_chunking(self, text: str) -> List[str]:
        """语义感知的智能分块"""
        # 使用递归字符分割 + 语义边界检测
        separators = ["\n\n", "\n", "。", "；", " "]
        
        chunks = []
        current_chunk = ""
        
        for paragraph in text.split("\n\n"):
            # 如果段落太长，进一步分割
            if len(paragraph) > 1000:
                sentences = self.split_sentences(paragraph)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) < 800:
                        current_chunk += sentence
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = sentence
            else:
                if len(current_chunk) + len(paragraph) < 1000:
                    current_chunk += "\n\n" + paragraph if current_chunk else paragraph
                else:
                    chunks.append(current_chunk)
                    current_chunk = paragraph
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
```

### 6.3 混合检索策略

```python
class HybridRetriever:
    """混合检索器：结合向量检索和关键词检索"""
    
    def __init__(self, vector_store, keyword_index):
        self.vector_store = vector_store
        self.keyword_index = keyword_index
        self.embedding_model = OpenAIEmbeddings(model="text-embedding-3-large")
        self.reranker = CrossEncoderReranker()
    
    async def retrieve(
        self, 
        query: str, 
        filters: Dict = None,
        top_k: int = 10
    ) -> List[RetrievedDocument]:
        """执行混合检索"""
        
        # 1. 向量检索 (语义相似度)
        query_embedding = await self.embedding_model.aembed_query(query)
        vector_results = await self.vector_store.similarity_search(
            embedding=query_embedding,
            filter=filters,
            k=top_k * 2
        )
        
        # 2. 关键词检索 (BM25)
        keyword_results = self.keyword_index.search(
            query=query,
            filter=filters,
            k=top_k * 2
        )
        
        # 3. 结果融合 (RRF - Reciprocal Rank Fusion)
        fused_results = self.reciprocal_rank_fusion(
            vector_results, 
            keyword_results,
            k=60  # RRF参数
        )
        
        # 4. 重排序
        reranked_results = await self.reranker.rerank(
            query=query,
            documents=fused_results[:top_k * 2],
            top_k=top_k
        )
        
        return reranked_results
    
    def reciprocal_rank_fusion(self, vector_results, keyword_results, k=60):
        """RRF融合算法"""
        scores = {}
        
        # 向量检索得分
        for rank, doc in enumerate(vector_results):
            doc_id = doc.id
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
            scores[doc_id + "_doc"] = doc
        
        # 关键词检索得分
        for rank, doc in enumerate(keyword_results):
            doc_id = doc.id
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
            scores[doc_id + "_doc"] = doc
        
        # 排序并返回
        sorted_docs = sorted(
            [(doc_id, score) for doc_id, score in scores.items() if not doc_id.endswith("_doc")],
            key=lambda x: x[1],
            reverse=True
        )
        
        return [scores[doc_id + "_doc"] for doc_id, _ in sorted_docs]
```

### 6.4 RAG在PPT生成中的应用

```python
class PPTGenerationRAG:
    """PPT生成场景的RAG应用"""
    
    async def generate_outline_with_rag(self, topic: str, user_id: str) -> dict:
        """使用RAG增强的大纲生成"""
        
        # 1. 检索用户相关知识
        user_docs = await self.retriever.retrieve(
            query=topic,
            filters={"user_id": user_id, "doc_type": "reference"},
            top_k=5
        )
        
        # 2. 检索行业最佳实践
        best_practices = await self.retriever.retrieve(
            query=f"{topic} PPT structure best practice",
            filters={"collection": "template_knowledge"},
            top_k=3
        )
        
        # 3. 组装上下文
        context = self.build_context(user_docs, best_practices)
        
        # 4. 生成大纲
        outline = await self.llm.generate(
            prompt=OUTLINE_GENERATION_PROMPT,
            context=context,
            topic=topic
        )
        
        return outline
    
    async def generate_slide_content_with_rag(
        self, 
        slide_title: str,
        bullet_points: List[str],
        user_id: str
    ) -> dict:
        """使用RAG增强的幻灯片内容生成"""
        
        # 构建检索查询
        queries = [
            slide_title,
            " ".join(bullet_points),
            f"{slide_title} 案例 数据"
        ]
        
        # 多查询检索
        all_results = []
        for query in queries:
            results = await self.retriever.retrieve(
                query=query,
                filters={"user_id": user_id},
                top_k=3
            )
            all_results.extend(results)
        
        # 去重并排序
        unique_results = self.deduplicate_results(all_results)
        
        # 生成内容
        content = await self.llm.generate(
            prompt=CONTENT_GENERATION_PROMPT,
            retrieved_knowledge=unique_results,
            slide_title=slide_title,
            bullet_points=bullet_points
        )
        
        return content
```

### 6.5 向量数据库设计

```python
# ChromaDB Collection Schema
COLLECTION_SCHEMA = {
    "user_knowledge": {
        "description": "用户上传的知识文档向量库",
        "embedding_function": "text-embedding-3-large",
        "metadata_schema": {
            "doc_id": "string",           # 文档ID
            "user_id": "string",          # 用户ID
            "chunk_index": "integer",     # 分块索引
            "doc_type": "string",         # 文档类型: pdf, docx, txt
            "filename": "string",         # 原始文件名
            "page_num": "integer",        # 页码（PDF）
            "section": "string",          # 章节标题
            "uploaded_at": "timestamp",   # 上传时间
            "file_path": "string"         # 存储路径
        }
    },
    "template_knowledge": {
        "description": "模板和最佳实践知识库",
        "embedding_function": "text-embedding-3-large", 
        "metadata_schema": {
            "template_id": "string",      # 模板ID
            "category": "string",         # 分类: business, tech, education
            "content_type": "string",     # 类型: structure, example, tip
            "title": "string",            # 标题
            "tags": "list[string]"        # 标签
        }
    },
    "ppt_history": {
        "description": "用户PPT历史内容向量库",
        "embedding_function": "text-embedding-3-large",
        "metadata_schema": {
            "ppt_id": "string",           # PPT ID
            "user_id": "string",          # 用户ID
            "slide_index": "integer",     # 幻灯片索引
            "slide_type": "string",       # 类型: cover, content, chapter
            "created_at": "timestamp"     # 创建时间
        }
    }
}
```

---

## 七、项目里程碑与时间规划

| 阶段 | 任务 | 预计时间 | 关键交付物 |
|------|------|----------|------------|
| **Phase 1** | 基础架构搭建 | 2周 | 项目脚手架、CI/CD |
| **Phase 2** | 核心功能开发 | 4周 | 大纲生成、内容填充 |
| **Phase 3** | AI能力集成 | 3周 | RAG系统、多模型支持 |
| **Phase 4** | 编辑器开发 | 4周 | PPT编辑器、模板系统 |
| **Phase 5** | 优化与测试 | 2周 | 性能优化、用户测试 |
| **Phase 6** | 部署上线 | 1周 | 生产环境、监控告警 |

---

## 八、技术风险与应对策略

| 风险 | 影响 | 应对策略 |
|------|------|----------|
| AI生成质量不稳定 | 高 | 多模型备份、人工审核机制、A/B测试 |
| 大模型API成本 | 中 | 本地模型部署、智能缓存、使用量监控 |
| PPT渲染兼容性 | 中 | 多种导出格式、浏览器兼容性测试 |
| 向量检索性能 | 中 | 索引优化、分层检索、缓存策略 |
| 数据安全 | 高 | 数据加密、访问控制、审计日志 |

---

*文档版本: v1.0*  
*创建日期: 2026-04-19*  
*作者: Slideon Team*
