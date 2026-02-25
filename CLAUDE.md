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

## 🎨 Fluent Design 规范

本项目遵循 Microsoft Fluent Design System。所有 UI 设计必须符合以下原则：

### 五大核心原则

| 原则 | 说明 | 实现方式 |
|------|------|----------|
| **Light (光)** | 光影效果引导视觉焦点 | 使用 Mica 材质、阴影效果 |
| **Depth (深度)** | 层次感创造空间关系 | z-index 层级、模糊背景、提升效果 |
| **Motion (动效)** | 流畅自然的过渡 | qfluentwidgets 内置动画 |
| **Material (材质)** | 真实质感 | Mica/Acrylic 背景材质 |
| **Scale (缩放)** | 适应不同设备 | 响应式布局、自适应控件 |

### 颜色系统

#### 主题感知 (Theme-Aware)
- **必须**支持 Light 和 Dark 两种主题
- 使用 `isDarkTheme()` 检测当前主题
- 使用 `setTheme(Theme.AUTO)` 自动跟随系统
- **禁止**硬编码颜色值（如 `color: #000000`）

#### 层次与提升 (Layering & Elevation)
- 深色 = 较不重要的背景表面
- 浅色/亮色 = 重要的前景元素
- 背景色层级：`背景 < Layer 1 < Layer 2 < ...`

#### 强调色 (Accent Color)
- 品牌蓝: `#0078d4` (通过 `setThemeColor("#0078d4")` 设置)
- 用于：主要按钮、选中状态、链接、进度条
- 使用要克制，仅强调重要元素

### 主题适配规范

#### ✅ 正确做法

```python
from qfluentwidgets import (
    BodyLabel, StrongBodyLabel, isDarkTheme, setTheme, Theme
)
from PySide6.QtGui import QFont, QColor

# 1. 使用主题感知的标签组件
title = StrongBodyLabel("标题")  # 自动适配文字颜色

# 2. 在 paintEvent 中动态选择颜色
def paintEvent(self, event):
    painter = QPainter(self)
    if isDarkTheme():
        color = QColor("#1a1a2e")  # 暗色模式背景
    else:
        color = QColor("#0078d4")  # 亮色模式品牌色
    painter.fillRect(self.rect(), color)

# 3. 使用 QFont 设置字体大小，而非样式表
label = BodyLabel("文字")
font = label.font()
font.setPointSize(14)
font.setWeight(QFont.DemiBold)
label.setFont(font)
```

#### ❌ 错误做法

```python
# 硬编码颜色 - 暗色模式下看不清！
label.setStyleSheet("color: black;")  # ❌
label.setStyleSheet("font-size: 14px; color: #333;")  # ❌

# 使用 Qt 原生控件
from PySide6.QtWidgets import QLabel  # ❌
label = QLabel("文字")  # ❌
```

### 布局规范

#### 间距 (Spacing)
| 场景 | 推荐间距 |
|------|----------|
| 表单项之间 | 16-24px |
| 相关元素组 | 8-12px |
| 页面边距 | 32-48px |
| 按钮高度 | 36-40px |
| 输入框高度 | 36-40px |

#### 字体大小 (Typography)
| 组件 | 字号 | 字重 |
|------|------|------|
| 页面大标题 | 28pt | DemiBold |
| 区块标题 | 18-20pt | DemiBold |
| 表单标签 | 默认 | Regular |
| 正文内容 | 默认 | Regular |
| 说明文字 | 11-12pt | Regular |

### 登录界面设计规范

参考 `login_dialog.py` 的实现：

1. **左右分栏布局**
   - 左侧：品牌面板（渐变背景 + Logo + 产品名）
   - 右侧：登录表单（清晰的输入层次）

2. **主题适配**
   - 左侧面板在 `paintEvent` 中根据 `isDarkTheme()` 动态绘制渐变
   - 所有文字使用 `StrongBodyLabel` / `BodyLabel` 自动适配颜色

3. **视觉层次**
   - 欢迎标题 > 提示文字 > 表单标签 > 输入框
   - 使用 `StrongBodyLabel` 强调重要文字

4. **材质效果**
   - 启用 `micaEnabled = True` 使用 Windows 11 Mica 效果

---

## 相关资源

- [PySide6 文档](https://doc.qt.io/qtforpython/)
- [PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
