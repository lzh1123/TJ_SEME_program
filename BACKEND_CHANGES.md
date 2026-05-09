
# 后端改动说明

## 📅 日期
2026-05-09

## 🎯 问题概述
后端调用 DeepSeek API 生成内容时，返回的 JSON 解析失败，导致使用 Fallback 模拟数据。

## 🔍 问题原因
- DeepSeek API 有时会返回额外的解释文字或 Markdown 格式
- JSON 解析函数不够健壮，无法处理复杂的格式情况
- 提示词不够严格，没有充分强调只输出 JSON

## 🔧 改动内容

### 1. `ppt_backend/services/ai/client.py` - 增强 JSON 解析

#### 改动点：
- **`_strip_markdown_fences` 函数改进**：
  - 逐行解析文本，更好地识别代码块
  - 正确处理代码块的开始和结束标记
  - 移除可能的语言标识（如 `json`）

- **`_extract_json_substring` 函数改进**：
  - 使用括号平衡算法找到完整的 JSON 对象
  - 正确处理嵌套的 JSON 结构
  - 确保只提取有效的 JSON 部分

- **`parse_model` 函数增强**：
  - 多重尝试策略，提高成功率
  - 先尝试标准解析
  - 失败后尝试更激进的清理
  - 最后尝试从原始文本重新提取

- **`parse_json` 函数增强**：
  - 增加异常处理和重试逻辑

### 2. `ppt_backend/services/ai/pipeline.py` - 优化提示词

#### 改动点：
- **`analyze_intent` 方法**：
  - 增加更严格的要求：不要输出任何 Markdown、代码块标记
  - 强调"只输出 JSON 对象本身"

- **`plan_presentation` 方法**：
  - 同样增加严格的格式要求
  - 强调只输出 JSON

- **`generate_dsl_with_debug` 方法**：
  - 同样增强提示词的严格性

### 3. 前端改动（辅助）

#### `slideon-frontend/src/components/common/OutlineModal.vue`：
- 删除主题风格选择组件（暂时不支持）
- 添加详细的调试日志，显示 AI 生成状态
- 修复 API 调用，不再传递 theme 参数

#### `slideon-frontend/src/services/api.js`：
- 修复 `createPresentation` 函数，不再接受 theme 参数
- 保持向后兼容

#### `slideon-frontend/src/config/api.js`：
- 将超时时间从 60 秒增加到 180 秒

## ✅ 验证结果

### 测试命令：
```bash
cd backend
.\venv\Scripts\python.exe run_test.py
```

### 测试结果：
```
✅ 成功！使用了真实 API 生成内容！

📑 生成的演示文稿:
  标题: 人工智能在医疗领域的应用
  受众: general public or medical professionals
  语调: informative and professional
  主题: modern_blue
  幻灯片数量: 10

📄 幻灯片列表:
   1. [CoverSlideDSL       ] 人工智能在医疗领域的应用
   2. [AgendaSlideDSL      ] 演讲内容概览
   3. [TextSlideDSL        ] 为什么AI需要医疗？
   4. [KpiSlideDSL         ] AI医疗关键绩效指标
   ...
```

### Debug 信息：
```
llmConfigured: True
usedFallback:  False
stage:        ok
error:        None
```

## 📊 改动统计

| 文件 | 改动类型 | 改动内容 |
|------|---------|---------|
| `client.py` | 🔧 修复 | 增强 JSON 解析函数 |
| `pipeline.py` | ✨ 改进 | 优化提示词，更严格 |
| `OutlineModal.vue` | 🗑️ 删除 | 移除主题选择组件 |
| `api.js` | 🔧 修复 | 修复 API 调用 |
| `api.js` (config) | ⚙️ 配置 | 增加超时时间 |

## 🎯 效果

### 之前：
- API 调用成功，但 JSON 解析失败
- 使用 Fallback 模拟数据
- 用户收到的总是相同的演示文稿

### 现在：
- API 调用成功
- JSON 解析成功率大幅提升
- 使用真实的 AI 生成内容
- 每次生成的内容都是独特的

## 💡 注意事项

1. **超时时间**：前端和后端都设置为 180 秒，确保 API 有足够时间响应
2. **提示词优化**：虽然增强了解析，但提示词的严格性仍然很重要
3. **错误处理**：如果仍然失败，会回退到模拟数据，保证系统可用
4. **日志输出**：前端添加了详细日志，方便调试

## 🔮 后续建议

1. 考虑添加流式响应，提供更好的用户体验
2. 可以添加重试机制，提高成功率
3. 考虑添加更多的调试信息，方便问题定位
4. 可以考虑支持用户选择主题风格

