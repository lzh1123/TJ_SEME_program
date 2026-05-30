# RAG (Retrieval-Augmented Generation) 模块

## 架构概览

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          RAG 混合检索系统                                  │
│                                                                          │
│  ┌──────────────┐   ┌──────────────────┐   ┌────────────────────┐       │
│  │  Web Search   │   │  Local Knowledge  │   │  Image Search      │       │
│  │  (DuckDuckGo) │   │  (Milvus 向量库)  │   │  (DuckDuckGo)      │       │
│  └──────┬───────┘   └────────┬─────────┘   └─────────┬──────────┘       │
│         │                    │                       │                   │
│         ▼                    │                       │                   │
│  ┌──────────────┐            │                       │                   │
│  │ Deep Fetch    │            │                       │                   │
│  │ (抓取网页全文)│            │                       │                   │
│  │ trafilatura  │            │                       │                   │
│  └──────┬───────┘            │                       │                   │
│         │                    │                       │                   │
│         └────────────────────┼───────────────────────┘                   │
│                              ▼                                           │
│                    ┌──────────────────┐                                  │
│                    │   RRF Fusion     │                                  │
│                    │ (Reciprocal Rank │                                  │
│                    │  Fusion, k=60)   │                                  │
│                    └────────┬─────────┘                                  │
│                             ▼                                            │
│                    ┌──────────────────┐                                  │
│                    │  LangGraph 编排   │                                  │
│                    │  (状态图引擎)     │                                  │
│                    └────────┬─────────┘                                  │
│                             ▼                                            │
│                    ┌──────────────────┐                                  │
│                    │  PPT DSL 生成    │                                  │
│                    │  (RAG增强Prompt) │                                  │
│                    └──────────────────┘                                  │
└──────────────────────────────────────────────────────────────────────────┘
```

## 模块结构

```
services/rag/
├── __init__.py           # 模块导出
├── embedding.py          # 向量化服务 (BGE-small-zh-v1.5, 512维)
├── milvus_client.py      # Milvus 客户端 (向量检索 + 关键词检索, RRF融合)
├── web_search.py         # 网络搜索服务 (DuckDuckGo, 支持降级到 ddgs)
├── content_fetcher.py    # 网页内容抓取器 (trafilatura → BS4 → 正则 三级降级)
├── knowledge_base.py     # 知识库管理 (文档分块 → 向量化 → 写入Milvus)
├── retrieval.py          # 混合检索器 (网络 + 本地 + Deep Fetch + RRF融合)
├── rag_graph.py          # LangGraph 状态图 (查询分析 → 并行搜索 → 融合 → 构建上下文)
├── rag_service.py        # RAG 高层服务 (对接 PPT 生成管线)
├── seed_knowledge.py     # 种子知识引导器 (72个主题 14个类别, 一键初始化)
└── README.md             # 本文件
```

## 核心设计

### Deep Fetch — 关键设计

**LLM 不会自己访问 URL。** DuckDuckGo 返回的 snippet 只有约 100 字，URL 对 LLM 来说只是一段无效字符串。因此系统在检索链路中自动执行 Deep Fetch：

```
DuckDuckGo Search("SWOT分析框架")
  → 返回 [{title, url, snippet: "SWOT分析是通过对企业..."}]   ← 100字

  ↓ deep_fetch=True (默认)

ContentFetcher.fetch(url)
  → requests.get(url) → HTML
  → trafilatura.extract() → 纯文本正文
  → 返回 6000+ 字完整文章

  ↓

RRF Fusion → 传给 LLM 的 context
  "[来源1 - 知乎] SWOT分析的核心思想是通过对企业的优势、劣势...
   内部因素包括... 分析步骤第一步... 企业案例: 某公司在..."
```

### 混合检索策略

| 检索通路 | 技术 | 数据形态 | 说明 |
|----------|------|----------|------|
| **网络搜索** | DuckDuckGo API + ContentFetcher | URL → 搜索 → 抓取全文 | 实时公开信息, deep_fetch 默认开启 |
| **向量检索** | Milvus ANN (IP度量) | 512维 BGE 向量 | 语义相似性匹配, 捕捉同义表达 |
| **关键词检索** | Milvus 中文分词 + LIKE | 倒排索引文本匹配 | 精确术语匹配, 弥补向量检索不足 |
| **融合排序** | RRF (k=60) | 分数融合去重 | 多路结果取 Top-K |

### LangGraph 工作流

```
analyze_query ──┬── web_search ──────┐ (含 Deep Fetch)
                ├── local_search ────┤
                └── enrich_images ───┘
                                      │
                                      ▼
                                    fuse ──► build_context ──► END
```

- **analyze_query**: 从用户主题提取 3-5 个不同角度的搜索查询
- **web_search / local_search / enrich_images**: 三路并行执行
- **fuse**: RRF 融合去重排序
- **build_context**: 拼接参考文献块 + 图片URL

### PPT 生成增强

在 DSL 生成阶段, 将检索到的上下文注入 LLM Prompt：

```
## 用户主题
{用户的topic}

## RAG 增强上下文（来自知识库和网络搜索）
以下是与主题相关的最新信息和专业知识，请在生成 PPT 内容时充分利用：

[来源 1 - web:zhihu.com]
SWOT分析是通过对企业内部优势(Strengths)、劣势(Weaknesses)
和外部机会(Opportunities)、威胁(Threats)进行全面评估...

[来源 2 - seed:分析框架]
波特五力模型由Michael Porter于1979年提出, 用于分析行业竞争结构...

## 原始提示
{原有的system prompt}
```

LLM 在生成幻灯片内容时可**直接引用参考资料中的专业术语、数据、案例**。

## 技术选型

| 组件 | 选型 | 原因 |
|------|------|------|
| 向量数据库 | Milvus 3.0-beta | 混合检索、中文分词、AUTOINDEX 自动索引 |
| Embedding | BAAI/bge-small-zh-v1.5 | 中英双语优化、轻量(512维)、本地部署无需 API |
| 网络搜索 | DuckDuckGo (via ddgs) | 免费、无需 API Key、支持中英文区域 |
| 内容抓取 | trafilatura → BS4 → 正则 | 三级降级策略，最大化网页正文提取成功率 |
| 编排引擎 | LangGraph | 状态图原生支持条件路由和并行执行 |
| LLM 调用 | langchain-openai | 兼容 DeepSeek / OpenAI 等 API |

---

## Milvus 存储架构

Milvus 是**向量计算引擎**，负责索引构建、向量检索和相似度计算。它本身不直接管理磁盘存储，而是依赖多层底层存储机制。

### 部署配置

```bash
# standalone.bat 中的关键参数
-e ETCD_USE_EMBED=true                   # 嵌入式 etcd
-e ETCD_DATA_DIR=/var/lib/milvus/etcd    # etcd 数据目录
-e COMMON_STORAGETYPE=local              # 存储类型: 本地文件系统
-v ./volumes/milvus:/var/lib/milvus      # 宿主机挂载
```

### 三层存储

```
┌─────────────────────────────────────────────────────────────┐
│                      Milvus 进程                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                 向量计算引擎                          │    │
│  │   - 索引构建 (AUTOINDEX)                             │    │
│  │   - ANN 搜索 (IP/COSINE/L2)                         │    │
│  │   - 标量过滤 (LIKE/RANGE/BOOL)                      │    │
│  │   - RRF 融合排序                                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│          ┌────────────────┼────────────────┐                 │
│          ▼                ▼                ▼                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │    etcd      │ │  RocksDB     │ │  RocksDB     │        │
│  │  (元数据存储) │ │ (向量+标量)  │ │ (元数据KV)   │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
              ./volumes/milvus/  (宿主机目录)
```

| 存储层 | 底层引擎 | 容器内路径 | 宿主机路径 | 存储内容 |
|--------|---------|-----------|-----------|----------|
| **元数据** | etcd (内嵌) | `/var/lib/milvus/etcd/` | `volumes/milvus/etcd/` | Collection schema、索引配置、分区信息、节点状态 |
| **向量数据** | RocksDB | `/var/lib/milvus/rdb_data/` | `volumes/milvus/rdb_data/` | 浮点向量数组(.sst)、段元数据、WAL 日志 |
| **元数据KV** | RocksDB | `/var/lib/milvus/rdb_data_meta_kv/` | `volumes/milvus/rdb_data_meta_kv/` | 位图索引、Bloom Filter |

### 实际文件结构

```
volumes/milvus/
├── etcd/member/
│   ├── snap/db              # etcd 快照 (BoltDB)
│   └── wal/0000....wal      # Write-Ahead Log
├── rdb_data/                # 向量 + 标量数据
│   ├── IDENTITY             # RocksDB 标识
│   ├── CURRENT              # MANIFEST 指针
│   ├── MANIFEST-000012      # 版本元数据
│   ├── 000011.sst           # SSTable (有序键值对)
│   ├── 000013.log           # WAL 日志
│   └── LOG                  # RocksDB 运行日志
└── rdb_data_meta_kv/        # 同上结构
```

### 数据写入流程

```
Python: kb.ingest_text("金字塔原理是...", source="mckinsey.pdf")
  │
  ▼
EmbeddingService.embed(["金字塔原理是..."])
  → [0.00398, -0.02819, ...]  (512维float向量)
  │
  ▼
MilvusClient.insert([{text, embedding, source, ...}])
  │
  ├─► etcd:    schema 不变, 无需写入
  ├─► RocksDB(rdb_data):      向量 + 标量 → SSTable
  └─► RocksDB(rdb_data_meta_kv): 更新 Bloom Filter
```

### 数据检索流程

```
Python: store.hybrid_search(query_emb, "金字塔原理")
  │
  ├─► etcd:    查询 schema → AUTOINDEX, IP度量
  ├─► RocksDB(rdb_data_meta_kv): Bloom Filter 排除不相关段
  └─► RocksDB(rdb_data): ANN搜索 + LIKE标量过滤
       │
       ▼
    返回 Top-K + 距离分数
```

### 关键配置

| 参数 | 值 | 含义 |
|------|-----|------|
| `COMMON_STORAGETYPE` | `local` | 本地文件系统 (生产改为 `remote` + MinIO/S3) |
| `ETCD_USE_EMBED` | `true` | etcd 内嵌, 无需独立部署 |
| `DEPLOY_MODE` | `STANDALONE` | 单机模式 |
| 端口 19530 | gRPC | Milvus 数据操作 (Python SDK) |
| 端口 9091 | HTTP | 健康检查 / REST API |
| 端口 2379 | HTTP | etcd 客户端 |

### 注意事项

- **数据持久化**: Docker volume 挂载到 `volumes/milvus/`, 容器删除后数据保留
- **数据删除**: `standalone.bat delete` 删除容器 + `volumes/` 目录, **不可逆**
- **生产环境**: `COMMON_STORAGETYPE=remote`, MinIO/S3 对象存储, etcd 集群化
- **.gitignore**: `volumes/` 已排除, 不会提交到 Git

---

## API 端点

### 检索

| 端点 | 说明 |
|------|------|
| `POST /rag/search` | 混合检索, 参数: `query` / `top_k` / `enable_web` / `enable_local` / `deep_fetch` |
| `POST /rag/enhance` | 获取增强上下文 + 相关图片 (供 AI 生成使用) |
| `POST /rag/images/search` | 搜索图片资源, 参数: `query` / `max_results` |

### 知识库管理

| 端点 | 说明 |
|------|------|
| `POST /rag/documents` | 上传文档 (PDF/DOCX/TXT/MD) |
| `DELETE /rag/documents/{source}` | 按 source 删除知识库条目 |
| `GET /rag/stats` | 知识库统计 (Collection 是否存在 / 向量数) |

### 集合管理

| 端点 | 说明 |
|------|------|
| `POST /rag/collection/init` | 初始化 Milvus Collection |
| `POST /rag/collection/reset` | 清空并重建 Collection |

### 一键初始化

| 端点 | 说明 |
|------|------|
| `POST /rag/bootstrap` | 从网络自动抓取 72 个主题的专业知识, 参数: `max_articles_per_topic` / `max_topics` |

### PPT 生成增强

现有端点新增 `use_rag` 参数, 设为 `true` 即可开启 RAG 增强:

| 端点 | 新增参数 |
|------|----------|
| `POST /dsl` | `use_rag: bool` |
| `POST /presentations` | `use_rag: bool` |
| `POST /presentations/{id}/regenerate` | `use_rag: bool` |

---

## 使用指南

### 前提条件

```bash
# 1. 安装依赖
pip install pymilvus sentence-transformers duckduckgo_search langgraph trafilatura beautifulsoup4

# 2. 启动 Milvus (Docker)
cd backend/ppt_backend/milvus
./standalone.bat start
# 等待提示 "Start successfully"

# 3. 启动后端
cd backend
uvicorn ppt_backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 一键初始化知识库

```bash
# 快速测试 (5个主题)
cd backend
python -m ppt_backend.rag_bootstrap --max-topics 5

# 完整初始化 (72个主题, 约15分钟)
python -m ppt_backend.rag_bootstrap

# 清空后重新初始化
python -m ppt_backend.rag_bootstrap --reset
```

或通过 API:

```bash
curl -X POST http://localhost:8000/rag/bootstrap \
  -H "Content-Type: application/json" \
  -d '{"max_articles_per_topic": 3, "max_topics": 5}'
```

### 手动上传文档

```bash
curl -X POST http://localhost:8000/rag/documents \
  -F "file=@/path/to/industry_report.pdf"

curl http://localhost:8000/rag/stats
```

### RAG 检索

```bash
# 全功能检索 (网络 + 本地 + 全文抓取)
curl -X POST http://localhost:8000/rag/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SWOT分析框架 案例 方法",
    "top_k": 5,
    "enable_web": true,
    "enable_local": true,
    "deep_fetch": true
  }'

# 仅本地知识库
curl -X POST http://localhost:8000/rag/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "金字塔原理 演示结构",
    "top_k": 5,
    "enable_web": false,
    "enable_local": true
  }'

# 仅网络搜索 (快速模式, 不抓全文)
curl -X POST http://localhost:8000/rag/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "2025 AI presentation trends",
    "top_k": 5,
    "enable_web": true,
    "enable_local": false,
    "deep_fetch": false
  }'

# 增强上下文 + 图片 (供 AI 使用)
curl -X POST http://localhost:8000/rag/enhance \
  -H "Content-Type: application/json" \
  -d '{
    "query": "新能源汽车行业分析 市场规模",
    "top_k": 5,
    "deep_fetch": true
  }'

# 图片搜索
curl -X POST http://localhost:8000/rag/images/search \
  -H "Content-Type: application/json" \
  -d '{"query": "startup pitch deck design", "max_results": 5}'
```

### RAG 增强 PPT 生成 (对比实验)

```bash
# 对照组: 不启用 RAG
curl -X POST http://localhost:8000/presentations \
  -H "Content-Type: application/json" \
  -d '{"topic": "企业数字化转型战略", "theme": "modern_blue", "use_rag": false}'

# 实验组: 启用 RAG
curl -X POST http://localhost:8000/presentations \
  -H "Content-Type: application/json" \
  -d '{"topic": "企业数字化转型战略", "theme": "modern_blue", "use_rag": true}'
```

> 对比两组返回的 `dsl.slides` 中内容的专业度、术语准确性、案例丰富度。

---

## Postman 测试集

| # | 方法 | 端点 | 关键参数 |
|---|------|------|----------|
| 1 | GET | `{{base}}/health` | — |
| 2 | GET | `{{base}}/rag/stats` | — |
| 3 | POST | `{{base}}/rag/collection/init` | — |
| 4 | POST | `{{base}}/rag/bootstrap` | `{"max_articles_per_topic":2, "max_topics":5}` |
| 5 | POST | `{{base}}/rag/search` | `{"query":"SWOT分析框架","top_k":5,"enable_web":true,"enable_local":true,"deep_fetch":true}` |
| 6 | POST | `{{base}}/rag/search` | `{"query":"金字塔原理","top_k":5,"enable_web":false,"enable_local":true}` |
| 7 | POST | `{{base}}/rag/search` | `{"query":"波特五力模型","top_k":5,"enable_web":true,"enable_local":false,"deep_fetch":false}` |
| 8 | POST | `{{base}}/rag/enhance` | `{"query":"融资路演PPT","top_k":5,"deep_fetch":true}` |
| 9 | POST | `{{base}}/rag/images/search` | `{"query":"startup pitch deck","max_results":5}` |
| 10 | POST | `{{base}}/presentations` | `{"topic":"新能源汽车行业分析","use_rag":true}` |
| 11 | POST | `{{base}}/presentations` | `{"topic":"新能源汽车行业分析","use_rag":false}` |
| 12 | POST | `{{base}}/rag/documents` | multipart: `file=@doc.pdf` |
| 13 | DELETE | `{{base}}/rag/documents/{source}` | 从检索结果复制 source 值 |

**测试顺序**: 1 → 2 → 3 → 4 → 5/6/7 (对比三种检索模式) → 8 → 10/11 (对比 RAG 开关)

---

## 环境变量

在 `.env` 文件中覆盖:

```bash
# Milvus
MILVUS_URI=http://localhost:19530
MILVUS_DB=default

# Embedding
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5

# 网络搜索区域 (wt-wt=全球 / cn-zh=中国 / us-en=美国)
WEB_SEARCH_REGION=wt-wt

# RAG 全局开关
RAG_ENABLED=true
```
