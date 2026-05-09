# Slideon UI 原型 - Figma 快速启动指南

## 🚀 30分钟创建第一个页面

### 第一步: 创建 Figma 文件 (5分钟)

1. 打开 [Figma](https://www.figma.com) 并登录
2. 点击左侧边栏的 **New File**
3. 重命名为: `Slideon-UI-Design`

---

### 第二步: 设置设计系统 (10分钟)

#### 2.1 创建颜色样式

点击右侧 **Fill** → 选择颜色 → 点击 **Styles** (+ 图标) → 创建以下颜色:

| 样式名称 | 颜色值 | 快捷键 |
|---------|--------|--------|
| Primary/500 | `#6366F1` | - |
| Primary/600 | `#4F46E5` | - |
| Gray/50 | `#F9FAFB` | - |
| Gray/100 | `#F3F4F6` | - |
| Gray/200 | `#E5E7EB` | - |
| Gray/400 | `#9CA3AF` | - |
| Gray/600 | `#4B5563` | - |
| Gray/700 | `#374151` | - |
| Gray/800 | `#1F2937` | - |
| Gray/900 | `#111827` | - |
| White | `#FFFFFF` | - |

**操作路径**: Fill → 颜色选择器 → Styles → + → 命名 → Create Style

#### 2.2 创建文字样式

选择文字工具 → 设置字体 → 点击 **Text** → **Styles** → 创建:

| 样式名称 | 字体 | 大小 | 字重 | 行高 |
|---------|------|------|------|------|
| Display | PingFang SC | 48px | Bold | 120% |
| H1 | PingFang SC | 32px | SemiBold | 130% |
| H2 | PingFang SC | 24px | SemiBold | 140% |
| H3 | PingFang SC | 20px | SemiBold | 140% |
| Body | PingFang SC | 14px | Regular | 160% |
| Body Large | PingFang SC | 16px | Regular | 160% |
| Caption | PingFang SC | 12px | Regular | 150% |

#### 2.3 设置网格

按 `Shift + G` 或点击 **View** → **Layout Grid**:

```
Grid 1: 8px Grid (用于对齐)
- Type: Grid
- Size: 8px
- Color: #E5E7EB, 10% opacity

Grid 2: 12-Column Layout (用于布局)
- Type: Columns  
- Count: 12
- Width: 72px
- Gutter: 24px
- Margin: 64px
```

---

### 第三步: 创建组件库 (10分钟)

#### 3.1 主按钮组件

1. 按 `R` 创建矩形: **120 x 40px**
2. 设置:
   - Fill: Primary/500
   - Corner radius: 6px
   - Text: "按钮文字", White, 14px, Medium
3. 选中矩形和文字 → `Ctrl + Alt + K` 创建组件
4. 命名: `Button/Primary/Default`

**创建变体 (Variants):**
- 复制组件 → 修改状态 → 添加变体
- Hover: Fill 改为 Primary/600
- Disabled: Fill 改为 Gray-300, 文字 Gray-400
- Large: 高度改为 48px
- Small: 高度改为 32px

#### 3.2 输入框组件

1. 按 `R` 创建矩形: **280 x 40px**
2. 设置:
   - Fill: White
   - Stroke: 1px, Gray-300
   - Corner radius: 6px
3. 添加文字占位符: "请输入...", Gray-400
4. 创建组件: `Input/Default`

**变体:**
- Focus: Stroke 改为 Primary-500, 添加 Shadow (0 0 0 3px #E0E7FF)
- Error: Stroke 改为 Error-500, 添加错误图标
- Filled: 文字改为 Gray-700

#### 3.3 卡片组件

1. 按 `R` 创建矩形: **240 x 180px**
2. 设置:
   - Fill: White
   - Corner radius: 8px
   - Effect: Drop shadow (0 4px 6px rgba(0,0,0,0.1))
3. 添加内部结构:
   - 顶部图片区: 240 x 135px, Gray-200
   - 标题: 14px, Gray-800, 距左 16px, 距下 12px
   - 时间: 12px, Gray-500
4. 创建组件: `Card/PPT-Project`

---

### 第四步: 设计首页 (5分钟)

#### 4.1 创建页面 Frame

1. 按 `F` → 选择 **Desktop** (1440x1024)
2. 重命名为: `01-Home-Page`
3. 设置 Fill: Gray-50

#### 4.2 添加 Header

1. 按 `R` 创建: **1440 x 64px**, Fill: White
2. 添加底部边框: 1px, Gray-200
3. 添加内容:
   - Logo: 左侧 64px, 文字 "Slideon", 20px, Bold, Primary-600
   - 导航: 首页、模板、我的PPT (14px, Gray-600, gap 32px)
   - 搜索框: 280 x 36px, 右侧 200px
   - 用户头像: 36 x 36px, 圆形, 右侧 64px

#### 4.3 添加 Hero 区域

1. 按 `R` 创建: **1440 x 500px**, Fill: White
2. 添加内容 (居中对齐):
   - 标题: "智能PPT生成，让创作更高效", Display样式
   - 副标题: "输入主题，AI自动生成专业大纲和内容", 16px, Gray-600
   - 输入框: 520 x 56px, 圆角 28px (胶囊形)
   - 按钮: "开始生成", 120 x 48px, Primary

#### 4.4 添加 Features 区域

1. 创建 4 个卡片，每个 **240 x 160px**
2. 横向排列，gap 24px，居中对齐
3. 每个卡片包含:
   - 图标: 48 x 48px, Primary-100背景, Primary-600图标
   - 标题: 18px, SemiBold
   - 描述: 14px, Gray-600

---

## 📐 常用快捷键

| 操作 | Windows | Mac |
|------|---------|-----|
| 选择工具 | `V` | `V` |
| 矩形工具 | `R` | `R` |
| 文字工具 | `T` | `T` |
| 画框工具 | `F` | `F` |
| 创建组件 | `Ctrl + Alt + K` | `Cmd + Option + K` |
| 创建变体 | 右侧面板 Variants | - |
| 复制 | `Ctrl + D` | `Cmd + D` |
| 编组 | `Ctrl + G` | `Cmd + G` |
| 取消编组 | `Ctrl + Shift + G` | `Cmd + Shift + G` |
| 显示网格 | `Shift + G` | `Shift + G` |
| 标尺 | `Shift + R` | `Shift + R` |
| 放大/缩小 | `Ctrl + +/-` | `Cmd + +/-` |
| 适应屏幕 | `Shift + 1` | `Shift + 1` |
| 实际大小 | `Shift + 0` | `Shift + 0` |

---

## 🎯 设计检查清单

### 颜色使用
- [ ] 主按钮使用 Primary-500
- [ ] 文字使用 Gray-700 (正文) / Gray-900 (标题)
- [ ] 禁用状态使用 Gray-300
- [ ] 背景使用 Gray-50 或 White
- [ ] 边框使用 Gray-200

### 间距使用
- [ ] 组件内部 padding: 16px
- [ ] 卡片 gap: 24px
- [ ] 区块间距: 64px 或 80px
- [ ] 页面边距: 64px

### 文字规范
- [ ] 标题: SemiBold (600)
- [ ] 正文: Regular (400)
- [ ] 按钮: Medium (500)
- [ ] 行高: 1.5-1.6

### 圆角使用
- [ ] 按钮: 6px
- [ ] 输入框: 6px
- [ ] 卡片: 8px
- [ ] 模态框: 16px
- [ ] 圆形按钮: 9999px

---

## 📱 响应式设计

### 创建响应式变体

1. 选中 Desktop Frame
2. 按 `Ctrl + Alt + K` 创建组件
3. 点击右侧 **Variants** → **Add Variant**
4. 创建 Tablet (768px) 和 Mobile (375px) 版本

### 断点规范

| 设备 | 宽度 | 关键调整 |
|------|------|----------|
| Desktop | 1440px | 完整布局 |
| Laptop | 1024px | 侧边栏可折叠 |
| Tablet | 768px | 双列变单列 |
| Mobile | 375px | 隐藏侧边栏，底部导航 |

---

## 🎨 导出资源

### 导出图标

1. 选中图标组件
2. 右下角点击 **Export**
3. 设置: SVG 格式, 1x
4. 点击 Export

### 导出切图

1. 选中需要切图的元素
2. 点击 **Export** → **+**
3. 设置: PNG, 2x (用于视网膜屏)
4. 添加后缀: `@2x`

### 导出标注

1. 切换到 **Dev Mode** (右上角切换)
2. 选中元素查看 CSS 代码
3. 复制需要的样式代码

---

## 🔗 原型交互

### 添加页面跳转

1. 切换到 **Prototype** 模式 (顶部)
2. 选中可点击元素
3. 拖拽蓝色手柄到目标页面
4. 设置交互:
   - Trigger: On Click
   - Action: Navigate To
   - Animation: Smart Animate (Ease Out, 300ms)

### 常用交互动画

| 效果 | 设置 |
|------|------|
| 页面切换 | Smart Animate, 300ms, Ease Out |
| 模态框弹出 | Open Overlay, 200ms, Ease Out |
| 侧边栏滑入 | Slide In, 250ms, Ease In Out |
| 按钮悬停 | While Hover, 150ms |

---

## 📚 推荐资源

### Figma 插件
- **Unsplash**: 快速插入图片
- **Iconify**: 10万+ 图标
- **Content Reel**: 假数据填充
- **Autoflow**: 画流程图
- **Lorem ipsum**: 占位文字

### 图标库
- [Heroicons](https://heroicons.com/) - 免费 SVG 图标
- [Lucide](https://lucide.dev/) - 现代图标集
- [Phosphor Icons](https://phosphoricons.com/) - 多种风格

### 图片资源
- [Unsplash](https://unsplash.com) - 免费高清图片
- [Pexels](https://pexels.com) - 免费视频和图片

---

## ✅ 完成检查

当你完成首页设计后，检查以下事项:

- [ ] 所有文字使用 Text Styles
- [ ] 所有颜色使用 Color Styles
- [ ] 组件已创建 Variants
- [ ] 间距遵循 8px Grid
- [ ] 添加了原型交互
- [ ] 导出了需要的资源

---

**下一步**: 继续设计编辑器页面和 AI 对话框!

遇到问题? 参考完整设计规范文档: `Slideon-UI-Design-Figma.md`
