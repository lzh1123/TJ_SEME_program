# Auth Backend

Python 后端认证与授权服务。

## 功能

- 注册、登录、退出、刷新
- 邮箱验证码发送与校验
- 找回密码与重置密码
- JWT + Redis Session 双模式
- `me`、`introspect`、`authorize`、`permissions`、`roles`

## 启动

> 每次使用都需要启动

```bash
uvicorn app.main:app --reload
```

## HTTPS 强化

项目已支持最小 HTTPS 强化开关，默认对本地开发关闭。

- `FORCE_HTTPS=true`
  - 强制把 HTTP 请求重定向到 HTTPS
- `TRUST_PROXY_HEADERS=true`
  - 当服务部署在 Nginx / Caddy / Traefik / LB 后面时，信任 `X-Forwarded-Proto`
- `HSTS_ENABLED=true`
  - 为 HTTPS 响应附加 `Strict-Transport-Security`
- `ALLOWED_HOSTS=example.com,api.example.com`
  - 限制允许访问的 Host

如果你通过反向代理终止 TLS，建议至少启用：

```env
FORCE_HTTPS=true
TRUST_PROXY_HEADERS=true
HSTS_ENABLED=true
ALLOWED_HOSTS=your-domain.com
```

## 初始化

> 只有第一次使用需要初始化，启动后才能初始化

```bash
alembic upgrade head
python -m app.cli seed --service-name gateway --service-token your-secret
```

或者直接

```bash
alembic upgrade head
python -m app.cli seed
```

如果 PostgreSQL 数据库还不存在，先创建 `POSTGRES_DATABASE` 对应的库，再执行迁移和 seed。

## 使用示例

见 `docs/user-flow-guide.md`。

## 迁移与测试

```bash
alembic upgrade head
pytest -q
```

## 依赖

- Python 3.10+
- PostgreSQL
- Redis

## 环境变量

优先读取 `.env`，可参考 `.env-template`。
