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
| Experiment | 实验，一次完整的转码参数调优任务，带装饰色(color)用于视觉区分 |
| ExperimentGroup | 实验组，实验中的单个测试配置 |

**关系**: Customer 1:N App 1:N Template N:N Experiment（实验和模板是多对多关系）

## 技术栈

### 客户端
- **UI**: PySide6 + PyQt-Fluent-Widgets (Fluent Design)
- **HTTP**: httpx
- **本地存储**: SQLite (aiosqlite)
- **视频处理**: FFmpeg

### 服务端
- **Web**: FastAPI + Uvicorn
- **存储**: Excel (openpyxl) - 便于开发调试
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
│   │   ├── ui/            # UI 层
│   │   │   ├── main_window.py
│   │   │   ├── login_dialog.py
│   │   │   └── pages/
│   │   │       ├── customer_matrix/   # 客户矩阵页面（卡片式）
│   │   │       ├── experiment/        # 实验卡片页面（瀑布流）
│   │   │       ├── user_management/   # 用户管理
│   │   │       └── components/        # 公共组件（ColorDot, WaterfallLayout）
│   │   ├── api/           # API 客户端
│   │   ├── models/        # Pydantic 数据模型
│   │   └── utils/         # 工具函数
│   └── VoidView.spec      # PyInstaller 打包配置
│
├── server/                # FastAPI 后端
│   └── app/
│       ├── api/v1/        # API 路由 (auth, users, experiments)
│       ├── schemas/       # Pydantic 请求/响应模型
│       ├── services/      # 业务逻辑
│       ├── storage/       # Excel 存储层 (excel_store.py)
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

## UI 页面

### 客户矩阵页面 (CustomerMatrixPage)
- 卡片式列表展示 Customer-App-Template-Experiment 关系
- 支持多选模式（左侧显示复选框）
- 实验标签显示装饰色方块，超过3个折叠显示
- 悬浮工具栏：添加客户/APP/模板、批量添加实验

### 实验卡片页面 (ExperimentCardPage)
- 瀑布流布局展示实验卡片
- 左侧装饰色条标识实验
- 按状态筛选

### 公共组件
- `ColorDot`: 装饰色圆点
- `ColorSquare`: 装饰色方块
- `ColorBar`: 装饰色竖条
- `WaterfallLayout`: 瀑布流布局

## 装饰色系统

实验自动分配装饰色，用于视觉区分：

```python
PRESET_COLORS = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
    "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9"
]

def get_color_for_experiment(experiment_id: int) -> str:
    return PRESET_COLORS[experiment_id % len(PRESET_COLORS)]
```

## API 接口规范

详细 API 文档见 [server/API.md](server/API.md)

### 主要接口

```
# 认证
POST /api/v1/auth/login
POST /api/v1/auth/refresh
GET  /api/v1/auth/me

# 用户管理（仅 root）
GET/POST/PUT/DELETE /api/v1/users

# 客户/应用/模板
GET/POST/PUT/DELETE /api/v1/experiments/customers
GET/POST/PUT/DELETE /api/v1/experiments/apps?customer_id={id}
GET/POST/PUT/DELETE /api/v1/experiments/templates?app_id={id}

# 实验
GET  /api/v1/experiments?page=1&page_size=20&status={status}
POST /api/v1/experiments  # 请求: { template_ids: int[], name, reference_type }
GET  /api/v1/experiments/matrix  # 获取矩阵数据
POST /api/v1/experiments/{id}/templates  # 关联模板
```

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

---

## ⚠️ CRITICAL: UI 控件使用规范

**本项目必须使用 PyQt-Fluent-Widgets (qfluentwidgets)，禁止使用 Qt 原生控件！**

这是强制要求，不要因为"更简单"或"更熟悉"而使用 Qt 原生控件。整个项目的 UI 风格依赖于 PyQt-Fluent-Widgets 的 Fluent Design 风格，混用 Qt 原生控件会破坏视觉一致性。

### ✅ 必须使用 (from qfluentwidgets)

| 场景 | 必须使用 |
|------|----------|
| 主窗口(有导航) | FluentWindow |
| 简单弹窗 | MessageBoxBase |
| 按钮 | PrimaryPushButton, PushButton, TransparentToolButton, ToolButton |
| 输入框 | LineEdit, TextEdit, ComboBox, SearchLineEdit |
| 标签 | SubtitleLabel, BodyLabel, CaptionLabel, StrongBodyLabel |
| 卡片 | CardWidget |
| 滚动 | SmoothScrollArea |
| 复选框 | CheckBox |
| 图标 | FluentIcon |
| 信息提示 | InfoBar, InfoBarPosition |
| 布局 | ExpandLayout, FlowLayout |

### ❌ 禁止使用 (from PySide6.QtWidgets)

| 禁止使用 | 替代方案 |
|----------|----------|
| QMainWindow | FluentWindow |
| QDialog | MessageBoxBase 或继承 FluentWidget |
| QPushButton | PushButton, PrimaryPushButton |
| QToolButton | ToolButton, TransparentToolButton |
| QLineEdit | LineEdit |
| QTextEdit | TextEdit |
| QComboBox | ComboBox |
| QLabel | BodyLabel, SubtitleLabel, CaptionLabel |
| QScrollArea | SmoothScrollArea |
| QCheckBox | CheckBox |

### 代码示例

```python
# ✅ 正确
from qfluentwidgets import (
    FluentWindow, CardWidget, PushButton, PrimaryPushButton,
    LineEdit, ComboBox, BodyLabel, SubtitleLabel, CheckBox,
    SmoothScrollArea, InfoBar, InfoBarPosition, FluentIcon,
    MessageBoxBase
)

# ❌ 错误 - 不要这样做！
from PySide6.QtWidgets import (
    QMainWindow, QDialog, QPushButton, QLineEdit,
    QLabel, QScrollArea  # 这些控件禁止使用
)
```

### 特殊注意事项

1. **CardWidget 信号冲突**: CardWidget 已有内置 `clicked` 信号，自定义点击信号时必须使用其他名称（如 `rowClicked`, `cardClicked`）

2. **FluentWindow 背景样式**: 使用 FluentWindow 时不要设置自定义背景色样式表，否则会破坏 Mica 效果

3. **选中状态高亮**: 使用 `setProperty("selected", True)` + `style().polish()` 而非样式表边框，避免布局抖动

4. **Mica 效果**: 在 FluentWindow 中设置 `self.micaEnabled = True` 启用 Windows 11 亚克力材质

---

## 相关资源

- [PySide6 文档](https://doc.qt.io/qtforpython/)
- [PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
