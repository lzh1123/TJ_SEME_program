# 用户流程使用指南

本文按正常用户的完整使用过程说明本项目的 RESTful 调用方式，覆盖：

- 注册
- 登录
- 携带 token 访问受保护接口
- 登出
- 忘记密码
- 重置密码

默认约定：

- 服务地址：`http://localhost:8000`
- 认证方式：JWT 或 `JWT + Session`
- 请求体格式：`application/json`
- access token 通过 `Authorization: Bearer <token>` 传递

关于密码传输，本项目现在有两组接口：

- 原始接口：`/auth/register`、`/auth/login`、`/auth/reset-password`
  - 这些接口接收的密码字段应当已经是“客户端先做过一次传输哈希后的结果”
- 兼容接口：`/auth/client-register`、`/auth/client-login`、`/auth/client-reset-password`
  - 这些接口接收明文密码
  - 服务端会模拟前端先做一次传输哈希，再把结果转发给原始接口

如果你的前端还没有实现客户端侧哈希，优先调用 `client-*` 接口。

即使使用了 `client-*` 兼容接口，也仍然建议生产环境启用 HTTPS。客户端传输哈希不能替代 TLS，它只能减少明文密码直接出现在请求体中的情况，不能防止重放和链路窃听。

## 1. 注册前发送验证码

注册前，前端先调用验证码发送接口，把邮箱验证码发到用户邮箱。

### 请求

```http
POST /auth/verify-code/send HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "email": "user@example.com",
  "purpose": "register"
}
```

### curl

```bash
curl -X POST "http://localhost:8000/auth/verify-code/send" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "purpose": "register"
  }'
```

### 预期响应

```json
{
  "message": "verification code sent"
}
```

## 2. 注册

用户拿到邮箱验证码后，再调用注册接口。

### 方式 A：推荐，调用兼容接口

前端直接传明文密码给 `client-*` 接口，由兼容层模拟客户端哈希。

```http
POST /auth/client-register HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "user1",
  "password": "password123",
  "verification_code": "123456"
}
```

```bash
curl -X POST "http://localhost:8000/auth/client-register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "user1",
    "password": "password123",
    "verification_code": "123456"
  }'
```

### 方式 B：原始接口

如果前端已经先对密码做过一次传输哈希，则调用原始接口。

### 请求

```http
POST /auth/register HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "user1",
  "password": "client-side-hash-output",
  "verification_code": "123456"
}
```

### curl

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "user1",
    "password": "client-side-hash-output",
    "verification_code": "123456"
  }'
```

### 预期响应

注册成功后，系统会直接返回用户主体信息，以及认证信息。

```json
{
  "user": {
    "id": 1,
    "username": "user1",
    "email": "user@example.com",
    "status": "active",
    "roles": [],
    "permissions": []
  },
  "auth": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 900,
    "session_id": "optional-session-id"
  }
}
```

## 3. 登录

本项目当前支持用用户名或邮箱作为 `account` 登录。

### 方式 A：推荐，调用兼容接口

```http
POST /auth/client-login HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "account": "user1",
  "password": "password123"
}
```

```bash
curl -X POST "http://localhost:8000/auth/client-login" \
  -H "Content-Type: application/json" \
  -d '{
    "account": "user1",
    "password": "password123"
  }'
```

### 方式 B：原始接口

原始接口的 `password` 字段应当已经是客户端传输哈希结果。

### 请求

```http
POST /auth/login HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "account": "user1",
  "password": "client-side-hash-output"
}
```

### curl

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "account": "user1",
    "password": "client-side-hash-output"
  }'
```

也可以用邮箱：

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "account": "user@example.com",
    "password": "client-side-hash-output"
  }'
```

### 预期响应

```json
{
  "user": {
    "id": 1,
    "username": "user1",
    "email": "user@example.com",
    "status": "active",
    "roles": [],
    "permissions": []
  },
  "auth": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 900,
    "session_id": "optional-session-id"
  }
}
```

## 4. 携带 token 访问受保护接口

登录成功后，前端通常要把 `access_token` 放进请求头：

```text
Authorization: Bearer <access_token>
```

这里用 `GET /auth/me` 作为示例。

### 请求

```http
GET /auth/me HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJ...
```

### curl

```bash
curl "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer eyJ..."
```

### 预期响应

```json
{
  "id": 1,
  "username": "user1",
  "email": "user@example.com",
  "status": "active",
  "roles": [],
  "permissions": []
}
```

## 5. 刷新 token

当 access token 过期时，前端可以使用 `refresh_token` 调用刷新接口。

### 请求

```http
POST /auth/refresh HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "refresh_token": "eyJ..."
}
```

### curl

```bash
curl -X POST "http://localhost:8000/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJ..."
  }'
```

### 预期响应

```json
{
  "access_token": "eyJ...new",
  "refresh_token": "eyJ...new",
  "token_type": "bearer",
  "expires_in": 900,
  "session_id": "optional-session-id"
}
```

如果系统启用了 Session 模式，也可以用现有登录态做 session 刷新。

## 6. 登出

### 场景 A：JWT + Session 模式

如果服务启用了 Session，登出接口可用。

### 请求

```http
POST /auth/logout HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Authorization: Bearer eyJ...

{
  "refresh_token": "eyJ...",
  "all_sessions": false
}
```

### curl

```bash
curl -X POST "http://localhost:8000/auth/logout" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ..." \
  -d '{
    "refresh_token": "eyJ...",
    "all_sessions": false
  }'
```

### 预期响应

```json
{
  "message": "logged out"
}
```

### 场景 B：JWT-only 模式

如果系统只启用了 JWT 模式，没有启用 Session，则该接口不支持，通常会返回 `405`。

## 7. 忘记密码：先发送重置验证码

当用户忘记密码时，先调用：

### 请求

```http
POST /auth/forgot-password HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "email": "user@example.com"
}
```

### curl

```bash
curl -X POST "http://localhost:8000/auth/forgot-password" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'
```

### 预期响应

```json
{
  "message": "reset code sent"
}
```

系统会向该邮箱发送一枚用于重置密码的 OTP 验证码。

## 8. 重置密码

用户收到验证码后，用新密码调用重置接口。

### 方式 A：推荐，调用兼容接口

```http
POST /auth/client-reset-password HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "email": "user@example.com",
  "verification_code": "654321",
  "new_password": "new-password-123"
}
```

```bash
curl -X POST "http://localhost:8000/auth/client-reset-password" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "verification_code": "654321",
    "new_password": "new-password-123"
  }'
```

### 方式 B：原始接口

原始接口的 `new_password` 应当已经是客户端传输哈希结果。

### 请求

```http
POST /auth/reset-password HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "email": "user@example.com",
  "verification_code": "654321",
  "new_password": "client-side-hash-output"
}
```

### curl

```bash
curl -X POST "http://localhost:8000/auth/reset-password" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "verification_code": "654321",
    "new_password": "client-side-hash-output"
  }'
```

### 预期响应

```json
{
  "message": "password reset"
}
```

## 9. 修改密码说明

当前项目提供的是：

- `forgot-password`
- `reset-password`

也就是“通过邮箱验证码重置密码”的流程。

当前没有单独提供“用户已登录后输入旧密码，再修改新密码”的接口，例如：

- `POST /auth/change-password`

如果你希望支持“已登录改密”，建议后续新增专门接口，常见入参为：

```json
{
  "old_password": "old-password",
  "new_password": "new-password"
}
```

## 10. 完整串联示例

最常见的前端使用顺序如下：

1. `POST /auth/verify-code/send`
2. `POST /auth/client-register`
3. 保存 `access_token` 和 `refresh_token`
4. 用 `Authorization: Bearer <access_token>` 访问 `GET /auth/me`
5. access token 过期后调用 `POST /auth/refresh`
6. 用户退出时调用 `POST /auth/logout`
7. 用户忘记密码时调用 `POST /auth/forgot-password`
8. 收到验证码后调用 `POST /auth/client-reset-password`

## 11. 常见前端实现建议

- `access_token` 用于每次访问受保护接口。
- `refresh_token` 不应混用为业务访问 token。
- 如果启用了 Session，同步保存 `session_id`，便于 session 维度控制。
- 注册、重置密码、忘记密码，都依赖验证码目的值 `purpose` 的一致性。
- 邮件验证码发送接口有基础频控，短时间重复发送可能收到 `429`。
