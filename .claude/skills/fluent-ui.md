# Fluent UI 组件开发指南

此 SKILL 用于指导 VoidView 项目中使用 PyQt-Fluent-Widgets 构建 Windows 11 Fluent UI 风格的界面。

## 核心依赖

```toml
PySide6 = "^6.6"
PyQt-Fluent-Widgets = "^1.4"  # 支持 PySide6 的 Fluent UI 组件库
```

## 基础用法

### 1. 导入库

```python
# 使用 PySide6 后端
from qfluentwidgets import (
    FluentWindow,          # 主窗口
    NavigationItemPosition,# 导航项位置
    SubtitleLabel,         # 副标题标签
    CardWidget,            # 卡片组件
    PrimaryPushButton,     # 主要按钮
    PushButton,            # 普通按钮
    ComboBox,              # 下拉框
    LineEdit,              # 输入框
    TableWidget,           # 表格
    MessageBox,            # 消息框
    InfoBar,               # 信息条
    FluentIcon,            # 图标
)
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout
```

### 2. 主窗口结构

```python
class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VoidView - 视频质量评测系统")
        self.resize(1200, 800)

        # 创建子页面
        self.experimentPage = ExperimentPage(self)
        self.evaluationPage = EvaluationPage(self)
        self.reviewPage = ReviewPage(self)
        self.statisticsPage = StatisticsPage(self)

        # 添加导航项
        self.navigationInterface.addItems([
            {
                'routeKey': 'experiment',
                'label': '实验管理',
                'icon': FluentIcon.DOCUMENT,
                'onClick': lambda: self.switchTo(self.experimentPage)
            },
            {
                'routeKey': 'evaluation',
                'label': '评测',
                'icon': FluentIcon.VIDEO,
                'onClick': lambda: self.switchTo(self.evaluationPage)
            },
            {
                'routeKey': 'review',
                'label': '评审',
                'icon': FluentIcon.CHECKBOX,
                'onClick': lambda: self.switchTo(self.reviewPage)
            },
            {
                'routeKey': 'statistics',
                'label': '统计',
                'icon': FluentIcon.CHART,
                'onClick': lambda: self.switchTo(self.statisticsPage)
            },
        ])
```

### 3. 卡片布局

```python
class ExperimentCard(CardWidget):
    """实验卡片组件"""

    def __init__(self, experiment, parent=None):
        super().__init__(parent)
        self.experiment = experiment
        self.setupUI()

    def setupUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = SubtitleLabel(self.experiment.name, self)
        layout.addWidget(title)

        # 信息行
        infoLayout = QHBoxLayout()
        statusLabel = BodyLabel(f"状态: {self.experiment.status}", self)
        dateLabel = BodyLabel(f"创建: {self.experiment.created_at}", self)
        infoLayout.addWidget(statusLabel)
        infoLayout.addWidget(dateLabel)
        infoLayout.addStretch()

        # 操作按钮
        detailBtn = PushButton("查看详情", self)
        detailBtn.clicked.connect(self.onDetailClick)
        infoLayout.addWidget(detailBtn)

        layout.addLayout(infoLayout)
```

### 4. 表格使用

```python
class ExperimentTable(TableWidget):
    """实验表格"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels([
            '实验组名', '镜像版本', '比特率', 'VMAF', '状态', '操作'
        ])
        self.verticalHeader().hide()
        self.setBorderVisible(True)
        self.setBorderRadius(8)

    def loadData(self, groups: list[ExperimentGroup]):
        self.setRowCount(len(groups))
        for row, group in enumerate(groups):
            self.setItem(row, 0, QTableWidgetItem(group.name))
            self.setItem(row, 1, QTableWidgetItem(group.encoder_version))
            self.setItem(row, 2, QTableWidgetItem(f"{group.bitrate:.1f}"))
            self.setItem(row, 3, QTableWidgetItem(f"{group.vmaf:.2f}"))

            # 状态使用徽章
            statusItem = QTableWidgetItem(group.status)
            self.setItem(row, 4, statusItem)

            # 操作按钮
            btnWidget = QWidget()
            btnLayout = QHBoxLayout(btnWidget)
            btnLayout.setContentsMargins(4, 4, 4, 4)
            evalBtn = PushButton("评测", btnWidget)
            btnLayout.addWidget(evalBtn)
            self.setCellWidget(row, 5, btnWidget)
```

### 5. 对话框

```python
class CreateExperimentDialog(MessageBoxBase):
    """创建实验对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel("创建新实验", self)

        # 表单控件
        self.nameEdit = LineEdit(self)
        self.nameEdit.setPlaceholderText("实验名称")

        self.customerCombo = ComboBox(self)
        self.customerCombo.addItems(["客户A", "客户B"])

        self.templateCombo = ComboBox(self)
        self.templateCombo.addItems(["hd5", "uhd", "ld5"])

        # 添加到布局
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.nameEdit)
        self.viewLayout.addWidget(self.customerCombo)
        self.viewLayout.addWidget(self.templateCombo)

        # 设置按钮文字
        self.yesButton.setText("创建")
        self.cancelButton.setText("取消")

    def validate(self) -> bool:
        if not self.nameEdit.text().strip():
            InfoBar.error("错误", "请输入实验名称", self)
            return False
        return True

    def getData(self) -> dict:
        return {
            'name': self.nameEdit.text(),
            'customer': self.customerCombo.currentText(),
            'template': self.templateCombo.currentText(),
        }
```

## 常用组件速查

| 组件 | 用途 | 示例 |
|------|------|------|
| `FluentWindow` | 主窗口 | 带侧边导航的主窗口 |
| `CardWidget` | 卡片容器 | 信息展示卡片 |
| `ExpandLayout` | 可展开布局 | 折叠面板 |
| `FlowLayout` | 流式布局 | 标签云 |
| `TableWidget` | 表格 | 数据列表 |
| `TreeWidget` | 树形列表 | 文件树 |
| `ComboBox` | 下拉选择 | 选择器 |
| `LineEdit` | 单行输入 | 文本输入 |
| `TextEdit` | 多行输入 | 备注 |
| `SpinBox` | 数字输入 | 评分 |
| `Slider` | 滑块 | 进度/音量 |
| `ProgressBar` | 进度条 | 加载状态 |
| `DatePicker` | 日期选择 | 日期筛选 |
| `MessageBox` | 消息框 | 确认弹窗 |
| `InfoBar` | 信息条 | 提示信息 |
| `StateToolTip` | 状态提示 | 操作结果 |
| `PushButton` | 按钮 | 普通按钮 |
| `PrimaryPushButton` | 主要按钮 | 提交/确认 |
| `ToolButton` | 工具按钮 | 图标按钮 |
| `ToggleButton` | 切换按钮 | 开关 |

## 主题设置

```python
from qfluentwidgets import setTheme, Theme

# 设置为暗色主题
setTheme(Theme.DARK)

# 设置为亮色主题
setTheme(Theme.LIGHT)
```

## 注意事项

1. 所有自定义组件应继承自 `CardWidget` 或 `QWidget`
2. 使用 `VBoxLayout`/`HBoxLayout` 进行布局
3. 图标使用 `FluentIcon` 枚举
4. 信号连接使用 PySide6 的信号槽机制
5. 保持组件的可复用性
