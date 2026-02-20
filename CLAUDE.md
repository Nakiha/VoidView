# VoidView - 视频主观质量评测系统

## 项目概述

VoidView 是一个基于 PySide6 和 Windows 11 Fluent UI 风格的桌面应用，用于视频转码团队的主观质量评测、评审、数据收集和趋势统计。

## 业务流程

```
创建实验 → 客观评测(VMAF/PSNR/比特率) → 主观评测(静帧/盲测) → 结果评审 → 上线回填
```

## 核心概念

| 概念 | 说明 |
|------|------|
| User | 用户，分为 root(管理员) 和 tester(测试人员) |
| Customer | 客户，提出转码需求的业务方 |
| App | 应用，客户下的具体业务 |
| Template | 模板，转码模板名称如 hd5、uhd |
| Experiment | 实验，一次完整的转码参数调优任务 |
| ExperimentGroup | 实验组，实验中的单个测试配置 |

## 技术栈

### 客户端
- **UI**: PySide6 + PyQt-Fluent-Widgets (Fluent Design)
- **HTTP**: httpx
- **本地存储**: SQLite (aiosqlite)
- **视频处理**: FFmpeg

### 服务端
- **Web**: FastAPI + Uvicorn
- **存储**: Excel (openpyxl) - 开发阶段
- **认证**: JWT + bcrypt
- **日志**: loguru

### 共享
- voidview-shared: 共享枚举、常量、日志配置

## 项目结构

```
VoidView/
├── client/                 # PySide6 桌面应用
│   ├── src/
│   │   ├── app/           # 应用核心 (application, config, app_state)
│   │   ├── ui/            # UI 层 (main_window, login_dialog, pages/)
│   │   ├── api/           # API 客户端 (client, auth, experiment)
│   │   ├── models/        # Pydantic 数据模型
│   │   └── utils/         # 工具函数
│   └── VoidView.spec      # PyInstaller 打包配置
│
├── server/                # FastAPI 后端
│   └── app/
│       ├── api/v1/        # API 路由 (auth, users, experiments)
│       ├── models/        # SQLAlchemy 模型
│       ├── schemas/       # Pydantic 请求/响应模型
│       ├── services/      # 业务逻辑
│       └── core/          # 安全、异常处理
│
├── shared/                # 客户端/服务端共享代码
│   └── src/voidview_shared/
│       ├── enums.py       # UserRole, ExperimentStatus 等
│       ├── constants.py   # API_VERSION
│       └── logging.py     # 统一日志配置
│
└── scripts/               # 工具脚本
    ├── install.py         # 安装依赖
    ├── build.py           # 打包客户端
    └── run.py             # 运行 client/server
```

## 数据模型关系

```
User ←─┬─→ Experiment (创建人)
       ├─→ SubjectiveResult (评测人)
       └─→ Review (评审人)

Customer 1:N App 1:N Template N:N Experiment
Experiment 1:N ExperimentGroup
ExperimentGroup 1:1 ObjectiveMetrics
ExperimentGroup 1:N SubjectiveResult 1:N Screenshot
ExperimentGroup 1:N Review
```

**注意**: Experiment 和 Template 是多对多关系（N:N），一个实验可以关联多个模板。

## 存储方式（开发阶段）

当前使用 Excel 文件存储数据，位于 `server/storage/excel_data/`：

| 文件 | Sheet | 说明 |
|------|-------|------|
| users.xlsx | users | 用户数据，默认 root/root123 |
| entities.xlsx | customers | 客户数据 |
| entities.xlsx | apps | 应用数据 |
| entities.xlsx | templates | 模板数据 |
| experiments.xlsx | experiments | 实验数据（含 color 字段） |
| experiments.xlsx | experiment_templates | 实验-模板关联表 |
| experiments.xlsx | experiment_groups | 实验组数据 |
| experiments.xlsx | objective_metrics | 客观指标数据 |

## API 接口规范

### 认证接口

```
POST /api/v1/auth/login
请求: { "username": string, "password": string }
响应: { "access_token": string, "refresh_token": string, "token_type": "bearer", "user": UserResponse }

POST /api/v1/auth/refresh
请求: refresh_token: string (query param)
响应: { "access_token": string, "refresh_token": string, "token_type": "bearer", "user": UserResponse }

GET /api/v1/auth/me
响应: UserResponse
```

### 用户接口（仅 root）

```
GET  /api/v1/users?page=1&page_size=20
POST /api/v1/users
请求: { "username": string, "password": string, "display_name": string, "role": "root"|"tester" }

GET  /api/v1/users/{user_id}
PUT  /api/v1/users/{user_id}
请求: { "display_name"?: string, "is_active"?: bool }

POST /api/v1/users/{user_id}/reset-password
POST /api/v1/users/{user_id}/toggle-active
```

### 客户/应用/模板接口

```
GET    /api/v1/experiments/customers
POST   /api/v1/experiments/customers
GET    /api/v1/experiments/customers/{id}
PUT    /api/v1/experiments/customers/{id}
DELETE /api/v1/experiments/customers/{id}

GET    /api/v1/experiments/apps?customer_id={id}
POST   /api/v1/experiments/apps
GET    /api/v1/experiments/apps/{id}
PUT    /api/v1/experiments/apps/{id}
DELETE /api/v1/experiments/apps/{id}

GET    /api/v1/experiments/templates?app_id={id}
POST   /api/v1/experiments/templates
GET    /api/v1/experiments/templates/{id}
PUT    /api/v1/experiments/templates/{id}
DELETE /api/v1/experiments/templates/{id}
```

### 实验接口

```
GET  /api/v1/experiments?page=1&page_size=20&template_id={id}&status={status}
POST /api/v1/experiments
请求: { "template_ids": int[], "name": string, "reference_type": "new"|"supplier"|"self" }
响应: ExperimentResponse（含 id, name, status, color, created_at, ...）

GET    /api/v1/experiments/{id}
PUT    /api/v1/experiments/{id}
DELETE /api/v1/experiments/{id}

# 模板关联
POST   /api/v1/experiments/{id}/templates
请求: { "template_ids": int[] }
DELETE /api/v1/experiments/{id}/templates/{template_id}

# 矩阵数据
GET /api/v1/experiments/matrix
响应: { "rows": MatrixRow[], "experiments": ExperimentBrief[] }
```

### 响应模型

```typescript
// ExperimentResponse
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

// MatrixRow
{
  customer_id: number
  customer_name: string
  app_id: number
  app_name: string
  template_id: number
  template_name: string
  experiments: { [experiment_id: number]: ExperimentBrief }
}

// ExperimentBrief
{
  id: number
  name: string
  status: string
  color: string
}
```

## 主要数据字段

- **User**: username, password_hash, display_name, role(root/tester), is_active
- **Customer**: name, contact, description
- **App**: customer_id, name, description
- **Template**: app_id, name, description
- **Experiment**: name, status(draft/running/completed/archived), reference_type, color
- **ExperimentGroup**: experiment_id, name, transcode_params, input_url, output_url, status
- **ObjectiveMetrics**: group_id, bitrate, vmaf, psnr, ssim, cpu_usage, gpu_usage
- **SubjectiveResult**: group_id, evaluator, evaluation_type, has_artifacts, blur_score
- **Review**: group_id, reviewer, review_type, result(pass/reject)

## 快速开始

```bash
# 安装依赖
python scripts/install.py

# 运行服务端
python scripts/run.py server

# 运行客户端
python scripts/run.py client

# 打包客户端
python scripts/build.py
```

## 开发规范

- 代码: ruff (linting) + mypy (类型检查) + PEP 8
- Git: 分支命名 `feature/xxx`, `fix/xxx`；Commit 格式 `type(scope): description`
- UI: Windows 11 Fluent Design, PyQt-Fluent-Widgets

### UI 控件使用规范

**优先使用 PyQt-Fluent-Widgets (qfluentwidgets) 控件，避免使用 Qt 原生控件：**

| 场景 | 使用 | 避免使用 |
|------|------|----------|
| 主窗口(有导航) | FluentWindow | QMainWindow, QWidget |
| 对话框(无导航) | FluentWidget | QDialog, QWidget, FluentWindow |
| 简单弹窗 | MessageBoxBase | QDialog |
| 按钮 | PrimaryPushButton, PushButton, ToolButton | QPushButton, QToolButton |
| 输入框 | LineEdit, TextEdit, ComboBox | QLineEdit, QTextEdit, QComboBox |
| 标签 | SubtitleLabel, BodyLabel, CaptionLabel | QLabel |
| 布局容器 | CardWidget, ExpandLayout, FlowLayout | QWidget (作为容器时需设置透明背景) |

**Mica 效果 (Windows 11 亚克力材质):**
```python
class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.micaEnabled = True  # 启用 Mica 效果
```

**注意事项:**
- 使用 FluentWindow 时，不要设置自定义背景色样式表，否则会覆盖 Mica 效果
- 所有窗口都应继承 FluentWindow 以保持一致的视觉风格
- 使用 `isDarkTheme()` 判断当前主题，动态调整颜色

## 功能模块

1. **实验管理**: 创建/编辑实验、管理实验组
2. **客观评测**: 录入和展示 VMAF/PSNR 等指标
3. **主观评测**: 静帧评测(视频对比+截图标注)、盲测
4. **评审流程**: 审核评测结果、决策通过/驳回
5. **统计报表**: 仪表盘、趋势图表、Excel/Word 导出

## 相关资源

- [PySide6 文档](https://doc.qt.io/qtforpython/)
- [PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
