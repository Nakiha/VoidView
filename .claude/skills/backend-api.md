# 后端 API 规范

## 认证

```
POST /api/v1/auth/login          # 登录
POST /api/v1/auth/refresh        # 刷新 Token
GET  /api/v1/auth/me             # 当前用户信息
```

## 用户管理 (root)

```
GET/POST/PUT/DELETE /api/v1/users
PUT /api/v1/users/{id}/reset-password
PUT /api/v1/users/{id}/toggle-active
```

## 实体管理

```
GET/POST/PUT/DELETE /api/v1/experiments/customers
GET/POST/PUT/DELETE /api/v1/experiments/apps?customer_id={id}
GET/POST/PUT/DELETE /api/v1/experiments/templates?app_id={id}
```

## 实验管理

```
GET  /api/v1/experiments?page=1&page_size=20&status={status}
POST /api/v1/experiments
GET  /api/v1/experiments/matrix    # 矩阵数据
POST /api/v1/experiments/{id}/templates
```

详细 API 文档见 `server/API.md`
