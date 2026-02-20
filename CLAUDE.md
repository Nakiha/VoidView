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
- **ORM**: SQLAlchemy 2.0 (async)
- **数据库**: SQLite (开发) / PostgreSQL (生产)
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

Customer 1:N App 1:N Template 1:N Experiment
Experiment 1:N ExperimentGroup
ExperimentGroup 1:1 ObjectiveMetrics
ExperimentGroup 1:N SubjectiveResult 1:N Screenshot
ExperimentGroup 1:N Review
```

## 主要数据表

- **User**: username, password_hash, display_name, role(root/tester), is_active
- **Experiment**: template_id, name, status(draft/running/completed), reference_type
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
