# Slideon UI 设计规范 - Figma 原型设计文档

## 📐 Figma 项目结构

```
Slideon-UI-Design (Figma File)
│
├── 📁 01-Design-System (设计系统)
│   ├── 🎨 Color Palette (色彩)
│   ├── 🔤 Typography (字体)
│   ├── 🧩 Components (组件库)
│   │   ├── Buttons
│   │   ├── Inputs
│   │   ├── Cards
│   │   ├── Icons
│   │   └── Navigation
│   └── 📏 Spacing & Grid (间距与网格)
│
├── 📁 02-Home-Page (首页)
│   ├── Hero Section
│   ├── Features Section
│   ├── Recent Projects
│   └── Templates Gallery
│
├── 📁 03-Dashboard (仪表盘)
│   ├── My PPTs List
│   ├── Create New Modal
│   └── Project Cards
│
├── 📁 04-Editor (编辑器)
│   ├── Main Editor Layout
│   ├── Sidebar Variants
│   ├── AI Assistant Panel
│   └── Toolbar States
│
├── 📁 05-AI-Flows (AI流程)
│   ├── Outline Generation
│   ├── Content Generation
│   ├── Style Transfer
│   └── Chat Interface
│
├── 📁 06-Export-Share (导出分享)
│   ├── Export Options
│   ├── Share Modal
│   └── Preview Modes
│
└── 📁 07-Auth-Settings (认证设置)
    ├── Login/Register
    ├── User Profile
    └── Settings Pages
```

---

## 🎨 设计系统 (Design System)

### 色彩系统

#### 主色调 (Primary)
| 名称 | 色值 | 用途 |
|------|------|------|
| Primary-50 | `#EEF2FF` | 最浅背景 |
| Primary-100 | `#E0E7FF` | 浅色背景 |
| Primary-200 | `#C7D2FE` | 边框高亮 |
| Primary-300 | `#A5B4FC` | 禁用状态 |
| Primary-400 | `#818CF8` | 悬停状态 |
| **Primary-500** | **`#6366F1`** | **主品牌色** |
| Primary-600 | `#4F46E5` | 按钮按下 |
| Primary-700 | `#4338CA` | 文字链接 |
| Primary-800 | `#3730A3` | 深色文字 |
| Primary-900 | `#312E81` | 最深色 |

#### 中性色 (Neutral)
| 名称 | 色值 | 用途 |
|------|------|------|
| Gray-50 | `#F9FAFB` | 页面背景 |
| Gray-100 | `#F3F4F6` | 卡片背景 |
| Gray-200 | `#E5E7EB` | 分割线 |
| Gray-300 | `#D1D5DB` | 边框 |
| Gray-400 | `#9CA3AF` | 占位符 |
| Gray-500 | `#6B7280` | 次要文字 |
| Gray-600 | `#4B5563` | 正文文字 |
| **Gray-700** | **`#374151`** | **主要文字** |
| Gray-800 | `#1F2937` | 标题文字 |
| Gray-900 | `#111827` | 最深文字 |

#### 功能色 (Semantic)
| 类型 | 浅色 | 主色 | 深色 |
|------|------|------|------|
| Success | `#D1FAE5` | `#10B981` | `#047857` |
| Warning | `#FEF3C7` | `#F59E0B` | `#B45309` |
| Error | `#FEE2E2` | `#EF4444` | `#B91C1C` |
| Info | `#DBEAFE` | `#3B82F6` | `#1D4ED8` |

### 字体系统

#### 字体家族
```
中文: "PingFang SC", "Microsoft YaHei", sans-serif
英文: "Inter", "SF Pro Display", -apple-system, sans-serif
代码: "JetBrains Mono", "Fira Code", monospace
```

#### 字号规范
| 样式 | 大小 | 字重 | 行高 | 用途 |
|------|------|------|------|------|
| Display | 48px | 700 | 1.2 | Hero大标题 |
| H1 | 32px | 600 | 1.3 | 页面标题 |
| H2 | 24px | 600 | 1.4 | 区块标题 |
| H3 | 20px | 600 | 1.4 | 卡片标题 |
| H4 | 18px | 600 | 1.5 | 小标题 |
| Body Large | 16px | 400 | 1.6 | 重要正文 |
| **Body** | **14px** | **400** | **1.6** | **默认正文** |
| Body Small | 13px | 400 | 1.5 | 辅助文字 |
| Caption | 12px | 400 | 1.5 | 说明文字 |
| Overline | 11px | 500 | 1.4 | 标签文字 |

### 间距系统 (8px Grid)

| Token | 值 | 用途 |
|-------|-----|------|
| space-1 | 4px | 图标间距 |
| space-2 | 8px | 紧凑间距 |
| space-3 | 12px | 小组件内边距 |
| space-4 | 16px | 默认间距 |
| space-5 | 20px | 中等间距 |
| space-6 | 24px | 卡片内边距 |
| space-8 | 32px | 大间距 |
| space-10 | 40px | 区块间距 |
| space-12 | 48px | 大区块 |
| space-16 | 64px | 页面间距 |

### 圆角系统

| Token | 值 | 用途 |
|-------|-----|------|
| radius-sm | 4px | 小标签、徽章 |
| radius-md | 6px | 按钮、输入框 |
| radius-lg | 8px | 卡片、弹窗 |
| radius-xl | 12px | 大卡片 |
| radius-2xl | 16px | 模态框 |
| radius-full | 9999px | 圆形按钮、头像 |

### 阴影系统

| 名称 | 值 | 用途 |
|------|-----|------|
| Shadow SM | `0 1px 2px rgba(0,0,0,0.05)` | 小元素 |
| Shadow MD | `0 4px 6px -1px rgba(0,0,0,0.1)` | 卡片 |
| Shadow LG | `0 10px 15px -3px rgba(0,0,0,0.1)` | 下拉菜单 |
| Shadow XL | `0 20px 25px -5px rgba(0,0,0,0.1)` | 模态框 |
| Shadow 2XL | `0 25px 50px -12px rgba(0,0,0,0.25)` | 对话框 |

---

## 🧩 组件库 (Components)

### 1. 按钮 (Buttons)

#### 主按钮 (Primary Button)
```
尺寸: height: 40px, padding: 0 20px
背景: Primary-500 (#6366F1)
文字: White, 14px, 500 weight
圆角: radius-md (6px)
悬停: Primary-600
按下: Primary-700
禁用: Gray-300
```

**变体:**
- Large: height 48px, padding 0 24px, font 16px
- Small: height 32px, padding 0 16px, font 13px
- With Icon: icon 16px, gap 8px

#### 次要按钮 (Secondary Button)
```
背景: White
边框: 1px solid Gray-300
文字: Gray-700
悬停: Gray-50
```

#### 文字按钮 (Text Button)
```
背景: Transparent
文字: Primary-600
悬停: Primary-50
```

#### 图标按钮 (Icon Button)
```
尺寸: 40x40px (默认), 32x32px (小), 48x48px (大)
背景: Transparent / Gray-100 (悬停)
图标: Gray-600 / Primary-600 (激活)
圆角: radius-md
```

### 2. 输入框 (Inputs)

#### 文本输入 (Text Input)
```
尺寸: height 40px, padding 0 14px
边框: 1px solid Gray-300
圆角: radius-md
字体: 14px, Gray-700
占位符: Gray-400

状态:
- 默认: border Gray-300
- 悬停: border Gray-400
- 聚焦: border Primary-500, shadow 0 0 0 3px Primary-100
- 错误: border Error-500, shadow 0 0 0 3px Error-100
- 禁用: bg Gray-100, text Gray-400
```

#### 文本域 (Textarea)
```
min-height: 100px
padding: 12px 14px
resize: vertical
```

#### 搜索框 (Search Input)
```
左侧图标: Search icon 16px, Gray-400
右侧: Clear button (有内容时显示)
圆角: radius-full (胶囊形)
```

### 3. 卡片 (Cards)

#### PPT项目卡片 (PPT Card)
```
宽度: 240px
背景: White
圆角: radius-lg
阴影: Shadow MD
悬停: Shadow LG, translateY(-2px)

结构:
┌─────────────────────┐
│  [缩略图 240x135]    │
├─────────────────────┤
│  标题               │
│  修改时间    [更多] │
└─────────────────────┘
```

#### 模板卡片 (Template Card)
```
宽度: 200px
圆角: radius-lg
悬停: 显示"使用模板"按钮覆盖层
```

### 4. 导航 (Navigation)

#### 顶部导航 (Header)
```
高度: 64px
背景: White
边框底部: 1px solid Gray-200
阴影: Shadow SM (滚动时)

结构:
[Logo 32px] [导航链接] [搜索框] [用户菜单]
```

#### 侧边栏 (Sidebar)
```
宽度: 280px (大纲模式) / 320px (AI助手模式)
背景: Gray-50
边框右侧: 1px solid Gray-200
```

#### 标签导航 (Tabs)
```
高度: 40px
激活: 底部 2px Primary-500 边框
文字: 14px, 激活时 Primary-600
```

### 5. 反馈组件 (Feedback)

####  toast 提示
```
位置: 右上角, 距边缘 24px
背景: Gray-800 (深色) / White (浅色)
圆角: radius-lg
阴影: Shadow LG
图标: 根据类型变化
```

#### 加载状态
```
Spinner: 20px, Primary-500, 1.5s 旋转动画
Skeleton: Gray-200, pulse 动画
Progress: height 4px, Primary-500
```

---

## 📱 页面设计详述

### 1. 首页 (Home Page)

#### 布局结构
```
┌─────────────────────────────────────────────────────────────┐
│  Header (64px)                                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Hero Section (500px height)                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                                                       │  │
│  │   "智能PPT生成，让创作更高效"                          │  │
│  │   Display 48px, Gray-800, center                      │  │
│  │                                                       │  │
│  │   [输入框                                    ] [按钮]  │  │
│  │   width: 600px, center                                │  │
│  │                                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  Features Section (400px)                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │   🤖     │ │   ✨     │ │   📚     │ │   🎯     │       │
│  │ AI大纲   │ │ 智能填充 │ │ 模板库   │ │ 知识增强 │       │
│  │ 生成    │ │ 内容    │ │         │ │ RAG     │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
├─────────────────────────────────────────────────────────────┤
│  Recent Projects Section                                     │
│  [标题: 最近项目]                              [查看全部 →]   │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐               │
│  │ Card 1 │ │ Card 2 │ │ Card 3 │ │ Card 4 │               │
│  └────────┘ └────────┘ └────────┘ └────────┘               │
├─────────────────────────────────────────────────────────────┤
│  Templates Gallery                                           │
│  [分类标签: 全部 | 商务 | 教育 | 创意 | 科技]                │
│  [模板卡片网格]                                              │
├─────────────────────────────────────────────────────────────┤
│  Footer (200px)                                              │
│  [Logo] [链接组] [社交媒体] [版权信息]                       │
└─────────────────────────────────────────────────────────────┘
```

#### 关键尺寸
- 容器最大宽度: 1280px (居中)
- 水平内边距: 64px (桌面) / 24px (移动端)
- 区块间距: 80px

---

### 2. 编辑器页面 (Editor Page)

#### 整体布局
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Header (56px)                                                               │
│ [返回] [项目名称]                    [保存] [分享] [导出▼] [用户头像]        │
├──────────┬──────────────────────────────────────────────────┬───────────────┤
│          │                                                  │               │
│ Sidebar  │                                                  │  AI Panel    │
│ (280px)  │              Canvas Area                        │  (320px)     │
│          │              (自适应宽度)                        │              │
│ ─────────│                                                  │ ──────────── │
│ 大纲视图  │                                                  │              │
│          │         ┌───────────────────────────────┐       │  🤖 AI助手   │
│ ▼ 封面   │         │                               │       │              │
│ ▶ 目录   │         │     Slide Canvas              │       │  "有什么可以 │
│ ▶ 第1章  │         │     960 x 540px (16:9)        │       │   帮您的吗？"│
│ ▶ 第2章  │         │                               │       │              │
│          │         │   ┌───────────────────────┐   │       │  ┌─────────┐ │
│ ─────────│         │   │                       │   │       │  │ 输入框  │ │
│ 页面缩略 │         │   │     [幻灯片内容]       │   │       │  └─────────┘ │
│ [缩略图] │         │   │                       │   │       │              │
│ [缩略图] │         │   └───────────────────────┘   │       │  快捷操作:   │
│ [缩略图] │         │                               │       │  • 优化内容  │
│          │         └───────────────────────────────┘       │  • 生成图片  │
│ [+ 添加] │                                                  │  • 调整风格  │
│          │                                                  │              │
├──────────┴──────────────────────────────────────────────────┴───────────────┤
│ Toolbar (48px)                                                              │
│ [撤销] [重做] | [插入▼] [布局▼] [主题▼] | 缩放 [- 100% +] | 3/10 [▶]       │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 画布规格
- 幻灯片尺寸: 960 x 540px (16:9 比例)
- 背景: White / Gray-50 (网格线)
- 缩放范围: 50% - 200%
- 默认缩放: 自适应

#### 大纲树结构
```
┌─────────────────┐
│ 大纲            │
├─────────────────┤
│ ▼ 1. 封面       │ ← 当前页高亮
│   副标题文字     │
│                 │
│ ▶ 2. 目录       │
│                 │
│ ▶ 3. 第一章     │ ← 章节标题
│   □ 3.1 页面1   │ ← 子页面
│   □ 3.2 页面2   │
│                 │
│ ▶ 4. 第二章     │
│                 │
│ □ 5. 结束页     │
│                 │
│ ─────────────── │
│ [+ 添加页面]    │
└─────────────────┘
```

---

### 3. AI大纲生成对话框

#### 对话框布局
```
┌─────────────────────────────────────────────────────────────────┐
│  智能生成PPT大纲                                          [×]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Step 1: 输入主题                                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 描述你的PPT主题、目标受众和主要内容...                    │    │
│  │                                                          │    │
│  │ 例如: 为科技公司CEO准备的产品发布会PPT，介绍新一代AI芯片  │    │
│  │       的性能优势和市场前景                                │    │
│  │                                    0/500                 │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  [可选] 上传参考文档                                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  [📎] 拖拽文件到此处，或点击上传                          │    │
│  │   支持 PDF, DOCX, TXT, MD (最大 20MB)                     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  Step 2: 选择风格                                                │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│  │  💼        │ │  🎨        │ │  📖        │ │  ✨        │   │
│  │  商务正式   │ │  创意活泼   │ │  学术严谨   │ │  简约现代   │   │
│  │  ○         │ │  ○         │ │  ○         │ │  ●         │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘   │
│                                                                  │
│  Step 3: 设置页数                                                │
│  预计页数: [━━●━━━━] 12 页 (推荐 8-20 页)                        │
│                                                                  │
│  [高级选项 ▼]                                                    │
│                                                                  │
│                    [取消]        [开始生成 →]                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 对话框规格
- 宽度: 640px
- 最大高度: 80vh
- 圆角: radius-2xl (16px)
- 阴影: Shadow 2XL
- 遮罩: Black 50% opacity

---

### 4. 仪表盘 (Dashboard)

#### 项目列表视图
```
┌─────────────────────────────────────────────────────────────────┐
│ Header                                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  我的PPT                                          [+ 新建PPT]   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ [全部 ▼] [最近修改 ▼]        [🔍 搜索项目...] [视图切换] │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  Grid View:                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ [封面图]  │ │ [封面图]  │ │ [封面图]  │ │ [封面图]  │           │
│  │ 项目标题  │ │ 项目标题  │ │ 项目标题  │ │ 项目标题  │           │
│  │ 2天前    │ │ 1周前    │ │ 2周前    │ │ 1月前    │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │    +     │ │          │ │          │ │          │           │
│  │ 新建PPT  │ │          │ │          │ │          │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│                                                                  │
│  [← 1 2 3 ... 10 →]  共 96 个项目                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 交互状态设计

### 按钮状态
```
Default → Hover → Active → Loading → Disabled

Hover: brightness 1.1, translateY(-1px)
Active: brightness 0.95, translateY(0)
Loading: Spinner 替换文字, disabled 状态
Disabled: opacity 0.5, cursor not-allowed
```

### 卡片状态
```
Default → Hover → Selected

Hover: Shadow LG, translateY(-2px), 200ms ease-out
Selected: border 2px Primary-500, Shadow MD
```

### 输入框状态
```
Default → Hover → Focus → Filled → Error → Disabled

Focus: border Primary-500, ring 3px Primary-100
Error: border Error-500, ring 3px Error-100, Error icon + message
```

### 页面过渡
```
页面切换: fade + slide, 300ms ease-in-out
模态框: scale 0.95→1 + fade, 200ms ease-out
侧边栏: slide, 250ms ease-in-out
Toast: slide from right + fade, 300ms ease-out
```

---

## 📐 响应式断点

| 断点 | 宽度 | 布局调整 |
|------|------|----------|
| Mobile | < 640px | 单列，隐藏侧边栏，底部导航 |
| Tablet | 640-1024px | 双列，可折叠侧边栏 |
| Desktop | 1024-1440px | 完整三栏布局 |
| Large | > 1440px | 最大宽度1280px居中 |

---

## 🎨 Figma 设计文件创建指南

### 步骤1: 创建文件结构
1. 在 Figma 中创建新文件 "Slideon-UI-Design"
2. 按上述结构创建 Pages
3. 设置颜色样式 (Color Styles)
4. 设置文字样式 (Text Styles)
5. 设置效果样式 (Effect Styles)

### 步骤2: 创建组件库
1. 创建 Buttons 组件集 (Variants: Primary/Secondary/Text/Ghost × Small/Default/Large)
2. 创建 Input 组件集 (Variants: Default/Hover/Focus/Error/Disabled)
3. 创建 Card 组件
4. 创建 Icon 组件库

### 步骤3: 设计页面
1. 使用 Frame 工具创建页面容器 (1280px width)
2. 应用网格系统 (8px grid + 12-column layout)
3. 使用组件库搭建页面
4. 添加交互原型 (Prototype)

### 步骤4: 导出规范
1. 使用 Figma 的 Dev Mode 生成标注
2. 导出切图 (SVG for icons, 2x PNG for images)
3. 生成 CSS 变量代码

---

## 📦 资源清单

### 需要准备的资源
- [ ] Logo (SVG, 多种尺寸)
- [ ] 空状态插图 (Empty state illustrations)
- [ ] 功能图标集 (48个)
- [ ] 模板缩略图 (10+ 张)
- [ ] 示例头像图片

### 推荐插件
- **Unsplash**: 免费图片
- **Iconify**: 图标库
- **Content Reel**: 填充假数据
- **Autoflow**: 用户流程图
- **Stark**: 无障碍检查

---

*文档版本: v1.0*  
*Figma 版本要求: 最新版*  
*最后更新: 2026-04-19*
