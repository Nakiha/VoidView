# VoidView - 视频主观质量评测系统

## 项目概述

VoidView 是基于 PySide6 + PyQt-Fluent-Widgets 的桌面应用，用于视频转码团队的主观质量评测、评审和数据统计。

**业务流程**: 创建实验 → 客观评测 → 主观评测 → 结果评审 → 上线回填

## 核心概念

| 概念 | 说明 |
|------|------|
| User | 用户: root(管理员) / tester(测试人员) |
| Customer | 客户，提出转码需求的业务方 |
| App | 应用，客户下的具体业务 |
| Template | 模板，转码模板如 hd5、uhd |
| Experiment | 实验，一次完整的转码参数调优任务，带装饰色 |

## 技术栈

| 层级 | 技术 |
|------|------|
| 客户端 | PySide6 + PyQt-Fluent-Widgets |
| 服务端 | FastAPI + Uvicorn |
| 存储 | Excel (openpyxl) - 开发阶段 |
| 认证 | JWT + bcrypt |

## 项目结构

```
VoidView/
├── client/src/           # PySide6 桌面应用
│   ├── app/              # 应用核心 (application, config)
│   ├── ui/               # UI 层
│   │   ├── main_window.py
│   │   ├── login_dialog.py
│   │   └── pages/        # 各功能页面
│   ├── api/              # API 客户端
│   └── models/           # Pydantic 模型
│
├── server/app/           # FastAPI 后端
│   ├── api/v1/           # 路由
│   ├── services/         # 业务逻辑
│   └── storage/          # Excel 存储层
│
├── shared/               # 共享代码
│   └── voidview_shared/  # 枚举、常量、日志
│
└── scripts/              # 工具脚本
    ├── install.py        # 安装依赖
    ├── run.py            # 运行 client/server
    └── build.py          # 打包
```

## 快速开始

```bash
python scripts/install.py    # 安装依赖
python scripts/run.py server # 启动服务端
python scripts/run.py client # 启动客户端
```

默认账号: `root` / `root123`

---

## ⚠️ UI/UX 设计规范

> 🎨 **涉及 UI 设计时，必须先阅读 `.claude/skills/ui-design.md`！**
>
> 该文档包含：
> - Fluent Design → qfluentwidgets 控件映射表
> - 标准布局模板（页面/卡片/表单/对话框）
> - 间距规范（8px 网格系统）
> - 主题适配写法
> - 常见问题与检查清单

> 📦 **创建对话框时，必须先阅读 `.claude/skills/dialog.md`！**
>
> 该文档包含：
> - 对话框标准模板
> - 中文按钮、遮罩关闭等必须设置
> - 遮罩闪烁问题的解决方案
> - 常见对话框类型示例

**本项目必须使用 PyQt-Fluent-Widgets，禁止使用 Qt 原生控件！**

### ✅ 必须使用

```python
from qfluentwidgets import (
    FluentWindow, CardWidget, MessageBoxBase,
    PrimaryPushButton, PushButton, TransparentToolButton,
    LineEdit, TextEdit, ComboBox, SearchLineEdit,
    SubtitleLabel, BodyLabel, CaptionLabel, StrongBodyLabel,
    SmoothScrollArea, CheckBox, InfoBar, FluentIcon
)
```

### ❌ 禁止使用

| 禁止 | 替代 |
|------|------|
| QMainWindow, QDialog | FluentWindow, MessageBoxBase |
| QPushButton | PushButton, PrimaryPushButton |
| QLineEdit | LineEdit |
| QLabel | BodyLabel, SubtitleLabel |
| QScrollArea | SmoothScrollArea |

### 注意事项

1. **CardWidget 信号冲突**: 已有内置 `clicked` 信号，自定义信号用 `rowClicked` 等名称
2. **主题适配**: 使用 `isDarkTheme()` 检测主题，不要硬编码颜色
3. **字体设置**: 用 `QFont` 而非样式表

```python
# ✅ 正确
label = StrongBodyLabel("标题")  # 自动适配主题
font = label.font()
font.setPointSize(14)
label.setFont(font)

# ❌ 错误
label.setStyleSheet("color: black; font-size: 14px;")  # 暗色模式看不清
```

---

## 装饰色系统

实验自动分配装饰色用于视觉区分：

```python
PRESET_COLORS = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", ...]
color = PRESET_COLORS[experiment_id % len(PRESET_COLORS)]
```

## 开发规范

- **代码**: ruff + mypy + PEP 8
- **Git**: 分支 `feature/xxx`, `fix/xxx`；提交 `type(scope): description`
- **UI**: Windows 11 Fluent Design

## 相关资源

- [PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
