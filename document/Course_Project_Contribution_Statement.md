# SlideOn 课程项目贡献声明

生成日期：2026-07-02  
统计范围：仅统计 `main` 与 `user-service` 两个分支可达提交的并集。  
分配原则：四位核心成员课程项目贡献均等，各占 25%。

## 1. 成员贡献概述

本贡献声明由小组成员结合课程项目全过程分工、阶段汇报材料和 Git 历史记录共同确认。项目工作覆盖管理、需求分析、系统设计、文档编写、前后端开发、AI/RAG 模块、认证服务、测试与部署等内容。四位核心成员承担的任务类型不同，但均对最终交付形成了实质贡献。

| 成员 | GitHub 用户名 / 提交作者 | 项目角色 | 主要贡献依据 |
|---|---|---|---|
| 李子恒 | `lzh1123` | Team Leader / Architecture | 负责项目启动与分工、需求收集与分析、架构设计协同、QA 框架、集成测试计划、用户/维护文档和最终汇报组织，并参与 Prompt、大纲生成、渲染与导出等模块的方案协调。 |
| 孙钰淼 | `steve26456d` | AI/RAG Engineer | 负责数据与 Prompt 工程、大纲生成、内容生成、RAG 实现与 Prompt 优化，完成 Prompt 库、语义扩展、混合检索、LangGraph 工作流和实验验证等相关工作。 |
| 李昊 | `KebRainy` | Backend Developer | 负责后端 API、认证子系统、渲染与导出、最终汇报协作等工作，包括 RESTful 接口、JWT/Redis 认证服务、PPTX 导出稳定性和多类型幻灯片支持。其 `user-service` 分支代码被团队参考并手动合并到主线功能中。 |
| 丁桢垚 | `dingzhenyao` | Infrastructure / Frontend Developer | 负责开发环境搭建、前端实现、系统与性能测试、部署上线和里程碑汇报演示，交付 Docker Compose 多服务部署、核心页面、大纲编辑器、组件库和部署配置等内容。 |

## 2. GitHub 提交快照与有效代码行

### 2.1 统计口径

- 分支范围：`main` 与 `user-service`。
- 提交去重：使用两个分支可达提交并集，避免同一提交重复计算。
- 作者别名合并：`steve` 与 `steve26456d` 同邮箱合并为 `steve26456d`；`dingzhenyao` 两个邮箱合并为 `dingzhenyao`。
- 有效代码行：统计源代码、配置、测试脚本等可维护文本文件；排除 `node_modules`、`build`、`egg-info`、`docs`、`document`、`res`、`test/results`、`experiment/Report Assets`、`data`、`package-lock.json`、PDF/PPTX/图片/SVG 等生成物或二进制资产。

### 2.2 原始提交快照

命令：

```bash
git shortlog -sne main user-service
```

输出快照：

```text
43  steve26456d <stevehhhh2023@163.com>
13  dingzhenyao <dingzhenyao@users.noreply.github.com>
11  steve <stevehhhh2023@163.com>
10  dingzhenyao <2363441530@qq.com>
 1  KebRainy <kebrainy@qq.com>
 1  lzh1123 <3277002900@qq.com>
```

`user-service` 分支差异快照：

```bash
git log --left-right --cherry-pick --oneline main...user-service
```

关键输出：

```text
> f1c5540 user service complete
```

该提交作者为 `KebRainy <kebrainy@qq.com>`，内容包括 `backend/user_service/app/api/routes/auth.py`、`backend/user_service/app/services/auth_service.py`、`backend/user_service/tests/test_auth_api.py` 等认证服务文件，因此计入李昊的代码贡献。

### 2.3 合并别名后的 Git 统计

| 成员 | GitHub 用户名 | 提交数 | 有效新增行 | 有效删除行 | 有效变更行 | 有效净增行 | 主要目录/说明 |
|---|---:|---:|---:|---:|---:|---:|---|
| 孙钰淼 | `steve26456d` | 54 | 20,085 | 5,207 | 25,292 | 14,878 | 主要涉及 `backend`、`slideon-frontend`、`test`、`experiment` 等；对应 AI/RAG、Prompt、实验与测试支持 |
| 丁桢垚 | `dingzhenyao` | 23 | 25,114 | 9,035 | 34,149 | 16,079 | 主要涉及 `slideon-frontend`、`backend` 与远程测试说明；对应前端、基础设施、部署与联调 |
| 李昊 | `KebRainy` | 1 | 2,964 | 0 | 2,964 | 2,964 | `user-service` 分支认证服务；主分支中对应功能由参考/手动合并方式吸收 |
| 李子恒 | `lzh1123` | 1 | 2 | 0 | 2 | 2 | 仓库所有者/初始提交；主要贡献体现在管理、需求、架构、文档、测试计划与最终汇报组织 |

说明：提交量和代码行能反映部分实现贡献，但不能完整衡量项目管理、需求分析、架构设计、文档编写、测试计划和汇报组织。因此，Git 快照用于说明代码提交情况，最终贡献比例由小组结合整体分工共同确认。

## 3. 贡献百分比分配

| 成员 | 贡献比例 | 分配理由 |
|---|---:|---|
| 李子恒 | 25% | 承担项目管理、需求分析、架构协同、QA 框架、集成测试计划、文档与最终汇报组织。虽然 Git 代码行较少，但管理和文档工作是课程项目评价的重要组成部分。 |
| 孙钰淼 | 25% | 承担 AI/RAG、Prompt、大纲生成、内容生成与实验验证相关工作，Git 代码与实验文档均有支撑。 |
| 李昊 | 25% | 承担后端 API、认证子系统、渲染与导出相关工作；其 `user-service` 分支代码虽未直接以同等形式出现在主分支作者统计中，但已被团队参考并手动合并到主线功能。 |
| 丁桢垚 | 25% | 承担基础设施、前端实现、部署、性能测试和里程碑汇报演示，Git 代码、前端页面与部署工作均有支撑。 |

均等分配理由：四位成员在不同维度承担了互补职责，管理/分析/设计/文档/代码共同构成课程项目交付。尽管 Git 提交数和有效代码行不完全相同，但差异主要来自任务性质、分支合并方式、管理与文档工作不可完全由代码行体现；经团队确认，最终贡献比例均为 25%。

## 4. 成员签名确认

本人确认上述贡献描述、Git 证据统计口径与 25% 均等贡献分配。

| 成员 | 贡献比例 | 签名 |
|---|---:|---|
| 李子恒 | 25% | ![李子恒签名](../res/signature/Liziheng.png) |
| 孙钰淼 | 25% | ![孙钰淼签名](../res/signature/Sunyumiao.png) |
| 李昊 | 25% | ![李昊签名](../res/signature/Lihao.png) |
| 丁桢垚 | 25% | ![丁桢垚签名](../res/signature/Dingzhenyao.png) |
