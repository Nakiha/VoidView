# 后端 API 设计

此 SKILL 用于指导 VoidView 服务端 API 的设计和实现。

## API 设计原则

1. **RESTful 风格**: 资源导向的 URL 设计
2. **版本控制**: URL 中包含版本号 `/api/v1/`
3. **分页**: 列表接口支持分页
4. **过滤和排序**: 支持多条件过滤和排序
5. **错误处理**: 统一的错误响应格式

## API 端点设计

### 认证相关

```
POST   /api/v1/auth/login              # 登录
POST   /api/v1/auth/logout             # 登出
POST   /api/v1/auth/refresh            # 刷新 Token
POST   /api/v1/auth/change-password    # 修改密码
GET    /api/v1/auth/me                 # 获取当前用户信息
```

### 用户管理 (root 专用)

```
GET    /api/v1/users                   # 获取用户列表
POST   /api/v1/users                   # 创建用户
GET    /api/v1/users/{id}              # 获取用户详情
PUT    /api/v1/users/{id}              # 更新用户
DELETE /api/v1/users/{id}              # 删除用户
PUT    /api/v1/users/{id}/reset-password  # 重置密码
PUT    /api/v1/users/{id}/toggle-active  # 启用/禁用
```

### 客户管理

```
GET    /api/v1/customers               # 获取客户列表
POST   /api/v1/customers               # 创建客户
GET    /api/v1/customers/{id}          # 获取客户详情
PUT    /api/v1/customers/{id}          # 更新客户
DELETE /api/v1/customers/{id}          # 删除客户

GET    /api/v1/customers/{id}/apps     # 获取客户下的应用列表
```

### 应用管理

```
GET    /api/v1/apps                    # 获取应用列表
POST   /api/v1/apps                    # 创建应用
GET    /api/v1/apps/{id}               # 获取应用详情
PUT    /api/v1/apps/{id}               # 更新应用

GET    /api/v1/apps/{id}/templates     # 获取应用下的模板列表
```

### 模板管理

```
GET    /api/v1/templates               # 获取模板列表
POST   /api/v1/templates               # 创建模板
GET    /api/v1/templates/{id}          # 获取模板详情
PUT    /api/v1/templates/{id}          # 更新模板

GET    /api/v1/templates/{id}/experiments  # 获取模板下的实验列表
```

### 实验管理

```
GET    /api/v1/experiments             # 获取实验列表 (支持筛选)
POST   /api/v1/experiments             # 创建实验
GET    /api/v1/experiments/{id}        # 获取实验详情 (含实验组)
PUT    /api/v1/experiments/{id}        # 更新实验
PUT    /api/v1/experiments/{id}/status # 更新实验状态
DELETE /api/v1/experiments/{id}        # 删除实验

# 实验组
GET    /api/v1/experiments/{id}/groups # 获取实验组列表
POST   /api/v1/experiments/{id}/groups # 添加实验组
GET    /api/v1/groups/{id}             # 获取实验组详情
PUT    /api/v1/groups/{id}             # 更新实验组
DELETE /api/v1/groups/{id}             # 删除实验组

# 批量操作
POST   /api/v1/experiments/{id}/groups/batch  # 批量添加实验组
```

### 评测相关

```
# 客观指标
POST   /api/v1/groups/{id}/objective-metrics      # 录入客观指标
GET    /api/v1/groups/{id}/objective-metrics      # 获取客观指标
PUT    /api/v1/groups/{id}/objective-metrics      # 更新客观指标

# 主观评测
GET    /api/v1/groups/{id}/subjective-results     # 获取主观评测结果列表
POST   /api/v1/groups/{id}/subjective-results     # 提交主观评测结果
GET    /api/v1/subjective-results/{id}            # 获取单条主观评测
PUT    /api/v1/subjective-results/{id}            # 更新主观评测

# 截图
POST   /api/v1/subjective-results/{id}/screenshots  # 上传截图
GET    /api/v1/subjective-results/{id}/screenshots  # 获取截图列表
DELETE /api/v1/screenshots/{id}                     # 删除截图

# 盲测
POST   /api/v1/blind-tests                        # 创建盲测任务
GET    /api/v1/blind-tests/{id}                   # 获取盲测详情
POST   /api/v1/blind-tests/{id}/submit            # 提交盲测结果
GET    /api/v1/blind-tests/{id}/summary           # 获取盲测汇总结果
```

### 评审相关

```
GET    /api/v1/reviews                            # 获取评审列表 (待评审/已完成)
POST   /api/v1/groups/{id}/reviews                # 提交评审
GET    /api/v1/groups/{id}/reviews                # 获取实验组的评审记录
```

### 统计相关

```
GET    /api/v1/statistics/dashboard               # 仪表盘数据
GET    /api/v1/statistics/trends                  # 趋势数据
GET    /api/v1/statistics/experiments/{id}/metrics # 实验指标统计
```

### 文件上传

```
POST   /api/v1/files/upload                       # 通用文件上传
GET    /api/v1/files/{id}                         # 下载文件
DELETE /api/v1/files/{id}                         # 删除文件
```

## 请求/响应格式

### 统一响应格式

```python
# 成功响应
{
    "code": 0,
    "message": "success",
    "data": { ... }
}

# 列表响应 (带分页)
{
    "code": 0,
    "message": "success",
    "data": {
        "items": [...],
        "total": 100,
        "page": 1,
        "page_size": 20,
        "pages": 5
    }
}

# 错误响应
{
    "code": 40001,
    "message": "用户名已存在",
    "data": null
}
```

### 分页参数

```
GET /api/v1/experiments?page=1&page_size=20&status=running&sort=-created_at
```

## FastAPI 实现示例

### 应用入口

```python
# server/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1.router import api_router

app = FastAPI(
    title="VoidView API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
async def startup():
    # 初始化数据库连接池
    pass


@app.on_event("shutdown")
async def shutdown():
    # 关闭数据库连接池
    pass
```

### 认证依赖

```python
# server/app/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_token
from app.models.user import User, UserRole
from app.repositories.user_repo import UserRepository

security = HTTPBearer()


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证"
        )

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已禁用"
        )

    return user


def require_root(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_root():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user
```

### 认证接口

```python
# server/app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.schemas.user import UserLogin, UserResponse, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """用户登录"""
    auth_service = AuthService(db)
    user = await auth_service.authenticate(data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    tokens = auth_service.create_tokens(user)
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """修改密码"""
    auth_service = AuthService(db)
    await auth_service.change_password(current_user, old_password, new_password)
    return {"message": "密码修改成功"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user = Depends(get_current_user)):
    """获取当前用户信息"""
    return UserResponse.model_validate(current_user)
```

### 实验接口

```python
# server/app/api/v1/experiments.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.schemas.experiment import (
    ExperimentCreate, ExperimentUpdate, ExperimentResponse,
    ExperimentGroupCreate, ExperimentGroupResponse
)
from app.services.experiment_service import ExperimentService

router = APIRouter(prefix="/experiments", tags=["实验管理"])


@router.get("", response_model=PaginatedResponse[ExperimentResponse])
async def list_experiments(
    status: str | None = Query(None),
    customer_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取实验列表"""
    service = ExperimentService(db)
    result = await service.list_experiments(
        status=status,
        customer_id=customer_id,
        page=page,
        page_size=page_size
    )
    return result


@router.post("", response_model=ExperimentResponse)
async def create_experiment(
    data: ExperimentCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建实验"""
    service = ExperimentService(db)
    experiment = await service.create_experiment(data, current_user.id)
    return ExperimentResponse.model_validate(experiment)


@router.get("/{experiment_id}", response_model=ExperimentDetailResponse)
async def get_experiment(
    experiment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取实验详情"""
    service = ExperimentService(db)
    experiment = await service.get_experiment_with_groups(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")
    return ExperimentDetailResponse.model_validate(experiment)


@router.post("/{experiment_id}/groups", response_model=ExperimentGroupResponse)
async def add_group(
    experiment_id: int,
    data: ExperimentGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """添加实验组"""
    service = ExperimentService(db)
    group = await service.add_group(experiment_id, data)
    return ExperimentGroupResponse.model_validate(group)


@router.post("/{experiment_id}/groups/batch")
async def batch_add_groups(
    experiment_id: int,
    data: list[ExperimentGroupCreate],
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """批量添加实验组"""
    service = ExperimentService(db)
    groups = await service.batch_add_groups(experiment_id, data)
    return {"count": len(groups)}
```

### 评测接口

```python
# server/app/api/v1/evaluations.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.schemas.evaluation import (
    ObjectiveMetricsCreate, ObjectiveMetricsResponse,
    SubjectiveResultCreate, SubjectiveResultResponse
)
from app.services.evaluation_service import EvaluationService

router = APIRouter(tags=["评测管理"])


# 客观指标
@router.post("/groups/{group_id}/objective-metrics", response_model=ObjectiveMetricsResponse)
async def create_objective_metrics(
    group_id: int,
    data: ObjectiveMetricsCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """录入客观指标"""
    service = EvaluationService(db)
    metrics = await service.create_objective_metrics(group_id, data)
    return ObjectiveMetricsResponse.model_validate(metrics)


# 主观评测
@router.post("/groups/{group_id}/subjective-results", response_model=SubjectiveResultResponse)
async def submit_subjective_result(
    group_id: int,
    data: SubjectiveResultCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """提交主观评测结果"""
    service = EvaluationService(db)
    result = await service.submit_subjective_result(
        group_id=group_id,
        evaluator_id=current_user.id,
        data=data
    )
    return SubjectiveResultResponse.model_validate(result)


# 截图上传
@router.post("/subjective-results/{result_id}/screenshots")
async def upload_screenshot(
    result_id: int,
    file: UploadFile = File(...),
    annotation: str | None = None,
    issue_type: str | None = None,
    timestamp: float | None = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """上传评测截图"""
    service = EvaluationService(db)
    screenshot = await service.upload_screenshot(
        result_id=result_id,
        file=file,
        annotation=annotation,
        issue_type=issue_type,
        timestamp=timestamp
    )
    return {"id": screenshot.id, "url": screenshot.url}
```

## 客户端 API 调用

```python
# client/src/api/client.py
import httpx
from typing import TypeVar, Type
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=30.0)
        self._token: str | None = None

    def set_token(self, token: str):
        self._token = token
        self.client.headers["Authorization"] = f"Bearer {token}"

    def clear_token(self):
        self._token = None
        self.client.headers.pop("Authorization", None)

    async def get(self, path: str, model: Type[T] | None = None) -> T | dict:
        resp = await self.client.get(path)
        resp.raise_for_status()
        data = resp.json()
        if model and "data" in data:
            return model.model_validate(data["data"])
        return data

    async def post(self, path: str, body: BaseModel | None = None) -> dict:
        resp = await self.client.post(
            path,
            json=body.model_dump() if body else None
        )
        resp.raise_for_status()
        return resp.json()

    async def upload(self, path: str, file_path: str, extra_data: dict | None = None) -> dict:
        with open(file_path, "rb") as f:
            files = {"file": f}
            data = extra_data or {}
            resp = await self.client.post(path, files=files, data=data)
        resp.raise_for_status()
        return resp.json()


# 使用示例
api = APIClient("http://localhost:8000/api/v1")

# 登录
result = await api.post("/auth/login", UserLogin(username="root", password="root123"))
api.set_token(result["data"]["access_token"])

# 获取实验列表
experiments = await api.get("/experiments", ExperimentListResponse)

# 创建实验
new_exp = await api.post("/experiments", ExperimentCreate(name="测试实验", ...))
```

## 部署配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: voidview
      POSTGRES_PASSWORD: voidview123
      POSTGRES_DB: voidview
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  api:
    build: ./server
    environment:
      DATABASE_URL: postgresql+asyncpg://voidview:voidview123@db:5432/voidview
      JWT_SECRET: your-secret-key
      JWT_EXPIRE: 3600
    ports:
      - "8000:8000"
    depends_on:
      - db
    volumes:
      - ./server/storage:/app/storage

volumes:
  postgres_data:
```
