# VoidView API 接口规范

> 本文档定义了 VoidView 服务端的所有 API 接口规范。
> 修改服务端 API 时必须确保与客户端的约定一致。

## 基础信息

- **Base URL**: `/api/v1`
- **认证方式**: Bearer Token (JWT)
- **Content-Type**: `application/json`

## 认证接口

### POST /auth/login
用户登录

**请求**
```json
{
  "username": "root",
  "password": "root123"
}
```

**响应**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "root",
    "display_name": "管理员",
    "role": "root",
    "is_active": true,
    "must_change_password": true,
    "created_at": "2024-01-01T00:00:00"
  }
}
```

### POST /auth/refresh
刷新令牌

**请求参数**: `refresh_token` (query string)

**响应**: 同 login

### GET /auth/me
获取当前用户信息

**响应**: UserResponse

### POST /auth/change-password
修改密码

**请求**
```json
{
  "old_password": "string",
  "new_password": "string"
}
```

---

## 用户管理接口（仅 root）

### GET /users
获取用户列表

**查询参数**
- `page`: int (default: 1)
- `page_size`: int (default: 20, max: 100)

**响应**
```json
{
  "items": [UserResponse],
  "total": 10,
  "page": 1,
  "page_size": 20
}
```

### POST /users
创建用户

**请求**
```json
{
  "username": "string",
  "password": "string",
  "display_name": "string",
  "role": "root" | "tester"
}
```

### GET /users/{user_id}
获取用户详情

### PUT /users/{user_id}
更新用户

**请求**
```json
{
  "display_name": "string",
  "is_active": true
}
```

### POST /users/{user_id}/reset-password
重置密码

**请求**
```json
{
  "new_password": "string"
}
```

### POST /users/{user_id}/toggle-active
切换用户启用状态

---

## 客户接口

### GET /experiments/customers
获取客户列表

**响应**: `[CustomerResponse]`

### POST /experiments/customers
创建客户

**请求**
```json
{
  "name": "string",
  "contact": "string?",
  "description": "string?"
}
```

### GET /experiments/customers/{id}
### PUT /experiments/customers/{id}
### DELETE /experiments/customers/{id}

---

## 应用接口

### GET /experiments/apps
获取应用列表

**查询参数**
- `customer_id`: int (可选，筛选指定客户的应用)

**响应**: `[AppResponse]`

### POST /experiments/apps
创建应用

**请求**
```json
{
  "customer_id": 1,
  "name": "string",
  "description": "string?"
}
```

### GET /experiments/apps/{id}
### PUT /experiments/apps/{id}
### DELETE /experiments/apps/{id}

---

## 模板接口

### GET /experiments/templates
获取模板列表

**查询参数**
- `app_id`: int (可选，筛选指定应用的模板)

**响应**: `[TemplateResponse]`

### POST /experiments/templates
创建模板

**请求**
```json
{
  "app_id": 1,
  "name": "string",
  "description": "string?"
}
```

### GET /experiments/templates/{id}
### PUT /experiments/templates/{id}
### DELETE /experiments/templates/{id}

---

## 实验接口

### GET /experiments
获取实验列表

**查询参数**
- `page`: int (default: 1)
- `page_size`: int (default: 20, max: 100)
- `template_id`: int (可选)
- `status`: string (可选: draft, running, completed, archived)

**响应**
```json
{
  "items": [ExperimentResponse],
  "total": 10,
  "page": 1,
  "page_size": 20
}
```

### GET /experiments/matrix
获取客户矩阵数据

**响应**
```json
{
  "rows": [
    {
      "customer_id": 1,
      "customer_name": "客户A",
      "app_id": 1,
      "app_name": "应用1",
      "template_id": 1,
      "template_name": "hd5",
      "experiments": {
        "1": {
          "id": 1,
          "name": "实验1",
          "status": "draft",
          "color": "#FF6B6B"
        }
      }
    }
  ],
  "experiments": [
    {
      "id": 1,
      "name": "实验1",
      "status": "draft",
      "color": "#FF6B6B"
    }
  ]
}
```

### POST /experiments
创建实验

**请求**
```json
{
  "template_ids": [1, 2, 3],
  "name": "实验名称",
  "reference_type": "new" | "supplier" | "self"
}
```

**响应**: ExperimentResponse

### GET /experiments/{id}
### PUT /experiments/{id}
### DELETE /experiments/{id}

### POST /experiments/{id}/templates
关联模板到实验

**请求**
```json
{
  "template_ids": [1, 2]
}
```

### DELETE /experiments/{id}/templates/{template_id}
解除实验与模板的关联

---

## 响应模型

### UserResponse
```typescript
{
  id: number
  username: string
  display_name: string
  role: "root" | "tester"
  is_active: boolean
  must_change_password: boolean
  created_at: datetime
  last_login_at: datetime?
}
```

### CustomerResponse
```typescript
{
  id: number
  name: string
  contact: string?
  description: string?
  created_at: datetime
}
```

### AppResponse
```typescript
{
  id: number
  customer_id: number
  name: string
  description: string?
  created_at: datetime
}
```

### TemplateResponse
```typescript
{
  id: number
  app_id: number
  name: string
  description: string?
  created_at: datetime
}
```

### ExperimentResponse
```typescript
{
  id: number
  name: string
  status: "draft" | "running" | "completed" | "archived"
  reference_type: "new" | "supplier" | "self"
  color: string  // 点缀色，如 "#FF6B6B"
  created_at: datetime
  created_by: number
  updated_at: datetime?
}
```

### ExperimentBrief
```typescript
{
  id: number
  name: string
  status: string
  color: string
}
```

---

## 错误响应

所有错误响应格式：
```json
{
  "detail": "错误信息"
}
```

HTTP 状态码：
- 400: 请求参数错误
- 401: 未认证
- 403: 权限不足
- 404: 资源不存在
- 500: 服务器内部错误
