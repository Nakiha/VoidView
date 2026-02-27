# UI/UX 设计指南 - Fluent Design 到 qfluentwidgets 映射

> ⚠️ 遇到 UI/UX 相关任务时，必须先阅读此文档！

## 设计原则

Fluent Design 五大原则 → qfluentwidgets 实现：

| 原则 | 含义 | 实现方式 |
|------|------|----------|
| Light | 光影引导焦点 | `StrongBodyLabel` 强调重要文字 |
| Depth | 层次感 | 卡片阴影、背景层级 |
| Motion | 流畅动效 | qfluentwidgets 内置动画，无需手动实现 |
| Material | 材质感 | `micaEnabled = True` 启用 Mica 效果 |
| Scale | 适配缩放 | 响应式布局、`FlowLayout`/`WaterfallLayout` |

---

## 控件映射速查表

### 窗口与容器

| 场景 | 使用 | 禁止 |
|------|------|------|
| 主窗口(带导航) | `FluentWindow` | `QMainWindow` |
| 简单对话框 | `MessageBoxBase` | `QDialog` |
| 卡片容器 | `CardWidget` | `QFrame` + 样式表 |
| 滚动区域 | `SmoothScrollArea` | `QScrollArea` |

### 输入控件

| 场景 | 使用 | 特点 |
|------|------|------|
| 文本输入 | `LineEdit` | 带清除按钮 |
| 多行文本 | `TextEdit` | Fluent 风格 |
| 下拉选择 | `ComboBox` | 圆角、主题适配 |
| 搜索框 | `SearchLineEdit` | 带搜索图标 |
| 复选框 | `CheckBox` | Fluent 动画 |

### 按钮控件

| 场景 | 使用 | 说明 |
|------|------|------|
| 主要操作 | `PrimaryPushButton` | 蓝色填充背景 |
| 次要操作 | `PushButton` | 灰色边框 |
| 工具按钮 | `TransparentToolButton` | 透明背景，hover 显示 |
| 图标按钮 | `ToolButton` | 带图标 |
| 图标 + 按钮组合 | `PushIconButton` | 图标在左，文字在右 |

### 文字控件

| 场景 | 使用 | 字号/字重 |
|------|------|-----------|
| 页面大标题 | `StrongBodyLabel` | 手动设置 20-28pt DemiBold |
| 区块标题 | `SubtitleLabel` | ~16pt |
| 正文内容 | `BodyLabel` | 默认 |
| 强调文字 | `StrongBodyLabel` | 默认加粗 |
| 说明/辅助 | `CaptionLabel` | ~11pt 浅色 |

### 布局管理

| 场景 | 使用 |
|------|------|
| 自适应换行 | `FlowLayout` |
| 瀑布流 | `WaterfallLayout` (项目自定义) |
| 可展开列表 | `ExpandLayout` |
| 普通垂直 | `QVBoxLayout` |
| 普通水平 | `QHBoxLayout` |

---

## 标准布局模板

### 1. 页面基础结构

```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import SubtitleLabel, TransparentToolButton, FluentIcon

class MyPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        # 主布局：垂直，边距 20px
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 标题栏：水平布局
        header = QHBoxLayout()
        title = SubtitleLabel("页面标题", self)
        header.addWidget(title)
        header.addStretch()  # 弹性空间，把按钮推到右边
        
        # 工具按钮
        refresh_btn = TransparentToolButton(FluentIcon.SYNC, self)
        header.addWidget(refresh_btn)
        
        layout.addLayout(header)
        
        # 内容区域（如果是可滚动的）
        # scroll = SmoothScrollArea(self)
        # layout.addWidget(scroll)
```

### 2. 卡片组件

```python
from qfluentwidgets import CardWidget
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout

class MyCard(CardWidget):
    """自定义卡片 - CardWidget 已有内置 clicked 信号"""
    
    # ⚠️ 不要定义 clicked 信号，会与父类冲突！
    cardClicked = Signal(int)  # 用其他名称
    
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self._data = data
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 16)  # 左16 上12 右16 下16
        layout.setSpacing(8)
        
        # 卡片内容...
```

### 3. 表单布局

```python
from qfluentwidgets import BodyLabel, LineEdit, ComboBox, PrimaryPushButton
from PySide6.QtWidgets import QGridLayout

def create_form(self):
    layout = QGridLayout()
    layout.setSpacing(12)  # 表单项间距
    layout.setColumnStretch(1, 1)  # 输入框列拉伸
    
    # 标签 + 输入框
    layout.addWidget(BodyLabel("用户名:", self), 0, 0)
    layout.addWidget(LineEdit(self), 0, 1)
    
    layout.addWidget(BodyLabel("角色:", self), 1, 0)
    layout.addWidget(ComboBox(self), 1, 1)
    
    # 提交按钮
    submit_btn = PrimaryPushButton("提交", self)
    layout.addWidget(submit_btn, 2, 0, 1, 2, Qt.AlignRight)
```

### 4. 对话框

> 📦 **对话框详细指南请参阅 `.claude/skills/dialog.md`**

基础结构：

```python
from qfluentwidgets import MessageBoxBase, SubtitleLabel, LineEdit

class MyDialog(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setClosableOnMaskClicked(True)  # 必须设置！

        self.titleLabel = SubtitleLabel("标题", self)
        self.viewLayout.addWidget(self.titleLabel)

        # 内容控件...

        self.yesButton.setText("确定")  # 必须中文！
        self.cancelButton.setText("取消")
        self.widget.setMinimumWidth(400)
```

---

## 间距规范

### 基础单位：8px 网格

| 名称 | 值 | 用途 |
|------|-----|------|
| XS | 4px | 紧密元素间距 |
| SM | 8px | 相关元素间距 |
| MD | 12px | 表单项间距 |
| LG | 16px | 卡片内间距 |
| XL | 20px | 页面边距 |
| XXL | 32-48px | 大区块间距 |

### 常用边距

```python
# 页面边距
layout.setContentsMargins(20, 20, 20, 20)

# 卡片内边距
layout.setContentsMargins(16, 12, 16, 16)

# 对话框内边距
layout.setContentsMargins(24, 20, 24, 24)
```

---

## 主题适配

### ✅ 正确做法

```python
from qfluentwidgets import isDarkTheme, StrongBodyLabel
from PySide6.QtGui import QColor, QFont

# 1. 使用主题感知的标签（文字颜色自动适配）
title = StrongBodyLabel("标题")

# 2. 在 paintEvent 中动态选择颜色
def paintEvent(self, event):
    painter = QPainter(self)
    if isDarkTheme():
        bg_color = QColor("#1a1a2e")
        text_color = QColor("#ffffff")
    else:
        bg_color = QColor("#f5f5f5")
        text_color = QColor("#1a1a1a")

# 3. 字体设置用 QFont
label = BodyLabel("文字")
font = label.font()
font.setPointSize(14)
font.setWeight(QFont.DemiBold)
label.setFont(font)
```

### ❌ 错误做法

```python
# 硬编码颜色 - 暗色模式看不清！
label.setStyleSheet("color: black;")  # ❌
label.setStyleSheet("background: white;")  # ❌

# 样式表设置字体
label.setStyleSheet("font-size: 14px;")  # ❌

# 使用 Qt 原生控件
from PySide6.QtWidgets import QLabel  # ❌
```

---

## 图标使用

```python
from qfluentwidgets import FluentIcon, IconWidget

# 可用图标（常用）
FluentIcon.ADD           # 添加
FluentIcon.EDIT          # 编辑
FluentIcon.DELETE        # 删除
FluentIcon.CLOSE         # 关闭
FluentIcon.SEARCH        # 搜索
FluentIcon.SETTING       # 设置
FluentIcon.SYNC          # 刷新/同步
FluentIcon.CHECKBOX      # 复选框
FluentIcon.VIDEO         # 视频
FluentIcon.PEOPLE        # 用户
FluentIcon.FOLDER        # 文件夹
FluentIcon.DOCUMENT      # 文档
FluentIcon.INFO          # 信息
FluentIcon.CANCEL        # 取消

# 按钮带图标
btn = PrimaryPushButton()
btn.setIcon(FluentIcon.ADD)
btn.setText("添加")

# 纯图标按钮
btn = TransparentToolButton(FluentIcon.EDIT)
```

---

## 信息提示

```python
from qfluentwidgets import InfoBar, InfoBarPosition

# 成功提示
InfoBar.success(
    title="操作成功",
    content="数据已保存",
    orient=Qt.Horizontal,
    isClosable=True,
    position=InfoBarPosition.TOP,
    duration=2000,  # 2秒后自动关闭
    parent=self
)

# 错误提示
InfoBar.error(
    title="操作失败",
    content="网络连接失败",
    ...
)

# 警告提示
InfoBar.warning(...)

# 信息提示
InfoBar.info(...)
```

---

## 常见问题

### Q: CardWidget 的 clicked 信号冲突？

```python
# ❌ 错误 - 与父类 clicked 信号冲突
class MyCard(CardWidget):
    clicked = Signal(int)  # 冲突！

# ✅ 正确 - 使用其他名称
class MyCard(CardWidget):
    cardClicked = Signal(int)  # OK
```

### Q: 如何设置选中状态高亮？

```python
# ✅ 使用 property + polish，不用样式表
self.setProperty("selected", True)
self.style().polish(self)
```

### Q: 如何启用 Mica 效果？

```python
# 在 FluentWindow 中
class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.micaEnabled = True  # Windows 11 Mica 效果
```

### Q: 如何创建带装饰色的元素？

```python
from PySide6.QtWidgets import QFrame

# 装饰色方块
color_dot = QFrame(self)
color_dot.setFixedSize(12, 12)
color_dot.setStyleSheet(f"""
    background-color: {color};
    border-radius: 4px;
""")

# 装饰色竖条
color_bar = QFrame(self)
color_bar.setFixedWidth(4)
color_bar.setStyleSheet(f"background-color: {color};")
```

---

## 检查清单

创建 UI 组件时，确保：

- [ ] 所有控件来自 `qfluentwidgets`，没有 `QLabel`/`QPushButton` 等
- [ ] 主窗口使用 `FluentWindow`
- [ ] 对话框继承 `MessageBoxBase`
- [ ] 文字颜色使用 `BodyLabel`/`StrongBodyLabel` 自动适配主题
- [ ] 字体使用 `QFont` 设置，不用样式表
- [ ] 没有硬编码 `color: black` 或 `background: white`
- [ ] 间距使用 4/8/12/16/20 的标准值
- [ ] CardWidget 的自定义信号不叫 `clicked`
