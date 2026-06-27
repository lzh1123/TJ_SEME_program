# Slideon 远程测试指南

> 服务器地址：`http://119.3.125.141`（未配置 HTTPS，暂用 HTTP）

---

## 一、认证系统测试

### 1. 健康检查

```bash
curl -s http://119.3.125.141/health
```

预期响应：
```json
{"ok":true}
```

---

### 2. 注册账号

```bash
curl -s -X POST http://119.3.125.141/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"用户名","email":"邮箱","password":"密码"}'
```

参数说明：
| 字段 | 必填 | 说明 |
|---|---|---|
| `username` | 是 | 3~50 位，字母/数字/下划线 |
| `email` | 是 | 合法邮箱格式 |
| `password` | 是 | 至少 6 位 |
| `display_name` | 否 | 显示名称，默认使用用户名 |

预期响应（201 Created）：
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "用户名",
  "email": "邮箱",
  "displayName": "用户名"
}
```

重复注册会返回 409：
```json
{"detail": "Username or email already exists"}
```

---

### 3. 登录

```bash
curl -s -X POST http://119.3.125.141/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"用户名或邮箱","password":"密码"}'
```

> 支持用 **用户名** 或 **邮箱** 登录。

预期响应（200 OK）：
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-...",
    "username": "用户名",
    "email": "邮箱",
    "displayName": "显示名称"
  }
}
```

---

### 4. 获取用户信息

```bash
curl -s http://119.3.125.141/auth/me \
  -H "Authorization: Bearer <access_token>"
```

---

### 5. 刷新 Token

```bash
curl -s -X POST http://119.3.125.141/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refreshToken": "<refresh_token>"}'
```

> refresh token 使用一次即失效（轮转机制），每次刷新会返回新的 token 对。

---

### 6. 登出

```bash
curl -s -X POST http://119.3.125.141/auth/logout \
  -H "Authorization: Bearer <access_token>"
```

> 撤销当前用户的所有 refresh token，access token 将在 30 分钟后过期。

---

### 7. 错误密码测试

```bash
curl -s -X POST http://119.3.125.141/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"存在的用户名","password":"错误密码"}'
```

预期响应（401）：
```json
{"detail": "Invalid username/email or password"}
```

---

## 二、演示文稿功能测试

### 8. 获取主题列表

```bash
curl -s http://119.3.125.141/themes
```

返回 4 套主题：`modern_blue`, `paper_light`, `academic_gray`, `minimal_black`

---

### 9. 创建演示文稿（需登录）

```bash
curl -s -X POST http://119.3.125.141/presentations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"topic":"人工智能发展简史","use_rag":false}'
```

参数说明：
| 字段 | 必填 | 说明 |
|---|---|---|
| `topic` | 是 | PPT 主题 |
| `theme` | 否 | 主题样式，不传则 AI 推荐 |
| `use_rag` | 否 | 是否启用 RAG 增强，默认 true |

---

### 10. 列出我的演示文稿（需登录）

```bash
curl -s http://119.3.125.141/presentations \
  -H "Authorization: Bearer <access_token>"
```

---

### 11. 获取演示文稿详情

```bash
curl -s http://119.3.125.141/presentations/<presentation_id>
```

---

### 12. 导出 PPTX

```bash
curl -s -o output.pptx http://119.3.125.141/presentations/<presentation_id>/export/pptx
```

---

## 三、完整测试脚本

```bash
#!/bin/bash
# 一键测试脚本

BASE="http://119.3.125.141"
echo "=== 1. Health ==="
curl -s $BASE/health

echo -e "\n\n=== 2. Register ==="
curl -s -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test_$(date +%s)","email":"test_$(date +%s)@test.com","password":"test123"}'

echo -e "\n\n=== 3. Login ==="
LOGIN=$(curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testapi","password":"test123"}')
TOKEN=$(echo $LOGIN | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
echo "Login success, token: ${TOKEN:0:20}..."

echo -e "\n=== 4. Get Me ==="
curl -s $BASE/auth/me -H "Authorization: Bearer $TOKEN"

echo -e "\n\n=== 5. Create Presentation ==="
PRES=$(curl -s -X POST $BASE/presentations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"topic":"测试演示文稿","use_rag":false}')
PRES_ID=$(echo $PRES | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
echo "Created: $PRES_ID"

echo -e "\n=== 6. Export PPTX ==="
curl -s -o /tmp/test_export.pptx "$BASE/presentations/$PRES_ID/export/pptx"
ls -la /tmp/test_export.pptx

echo -e "\n✅ Done!"
```

---

## 四、注意事项

| 项目 | 说明 |
|---|---|
| **认证方式** | Bearer Token（JWT），在 Header 中传入 `Authorization: Bearer <token>` |
| **Token 有效期** | access_token: **30 分钟**，refresh_token: **7 天** |
| **API 风格** | 请求使用 snake_case，响应部分字段使用 camelCase（如 `displayName`） |
| **鉴权要求** | 注册/登录/健康检查不需要登录；创建/查看演示文稿建议登录 |
| **RAG 注意事项** | `use_rag: true` 会调用 Milvus 知识库 + 网络搜索，响应较慢；首次使用需初始化知识库 |
