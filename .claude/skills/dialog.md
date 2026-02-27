# 对话框开发指南

> ⚠️ **创建对话框时，必须遵循此指南！**

## 基础模板

```python
from qfluentwidgets import MessageBoxBase, SubtitleLabel, LineEdit, TextEdit

class MyDialog(MessageBoxBase):
    """自定义对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # 1. 允许点击遮罩关闭
        self.setClosableOnMaskClicked(True)

        # 2. 标题
        self.titleLabel = SubtitleLabel("对话框标题", self)
        self.viewLayout.addWidget(self.titleLabel)

        # 3. 内容区域
        self.inputField = LineEdit(self)
        self.inputField.setPlaceholderText("请输入...")
        self.viewLayout.addWidget(self.inputField)

        # 4. 设置中文按钮文字（必须！）
        self.yesButton.setText("确定")
        self.cancelButton.setText("取消")

        # 5. 设置最小宽度
        self.widget.setMinimumWidth(400)

    def get_value(self) -> str:
        """获取输入值"""
        return self.inputField.text().strip()

    def validate(self) -> bool:
        """验证输入 - 返回 False 阻止关闭"""
        value = self.get_value()
        if not value:
            InfoBar.warning(title="提示", content="请输入内容", parent=self, duration=5000)
            return False
        return True
```

---

## 必须遵循的规则

### 1. 中文按钮文字

```python
# ✅ 正确
self.yesButton.setText("确定")
self.cancelButton.setText("取消")

# ❌ 错误 - 默认是英文 OK/Cancel
# 不设置按钮文字
```

### 2. 允许点击遮罩关闭

```python
# ✅ 正确 - 用户体验更好
self.setClosableOnMaskClicked(True)

# ❌ 错误 - 必须点按钮才能关闭
# 不设置这个属性
```

### 3. 使用 `viewLayout` 添加内容

```python
# ✅ 正确 - 使用 MessageBoxBase 提供的布局
self.viewLayout.addWidget(self.titleLabel)
self.viewLayout.addWidget(self.inputField)

# ❌ 错误 - 自己创建布局
layout = QVBoxLayout(self)  # 会破坏对话框结构
```

### 4. 验证使用 `validate()` 方法

```python
# ✅ 正确 - 重写 validate 方法
def validate(self) -> bool:
    if not self.inputField.text().strip():
        InfoBar.warning(title="提示", content="不能为空", parent=self, duration=5000)
        return False
    return True

# ❌ 错误 - 在按钮点击中验证
self.yesButton.clicked.connect(self._validate)  # 不会阻止对话框关闭
```

---

## 常见对话框类型

### 输入对话框

```python
class InputDialog(MessageBoxBase):
    """单行输入对话框"""

    def __init__(self, title: str, placeholder: str = "", default: str = "", parent=None):
        super().__init__(parent)
        self.setClosableOnMaskClicked(True)

        self.titleLabel = SubtitleLabel(title, self)
        self.viewLayout.addWidget(self.titleLabel)

        self.inputField = LineEdit(self)
        self.inputField.setPlaceholderText(placeholder)
        self.inputField.setText(default)
        self.inputField.selectAll()
        self.viewLayout.addWidget(self.inputField)

        self.yesButton.setText("确定")
        self.cancelButton.setText("取消")

        self.inputField.setFocus()
        self.widget.setMinimumWidth(350)

    def get_value(self) -> str:
        return self.inputField.text().strip()
```

### 多行文本对话框

```python
class TextDialog(MessageBoxBase):
    """多行文本编辑对话框"""

    def __init__(self, title: str, content: str = "", parent=None):
        super().__init__(parent)
        self.setClosableOnMaskClicked(True)

        self.titleLabel = SubtitleLabel(title, self)
        self.viewLayout.addWidget(self.titleLabel)

        self.textEdit = TextEdit(self)
        self.textEdit.setPlainText(content)
        self.textEdit.setPlaceholderText("请输入内容...")
        self.textEdit.setFixedHeight(200)
        self.viewLayout.addWidget(self.textEdit)

        self.yesButton.setText("保存")
        self.cancelButton.setText("取消")

        self.widget.setMinimumWidth(450)

    def get_content(self) -> str:
        return self.textEdit.toPlainText()
```

### 确认对话框

```python
class ConfirmDialog(MessageBoxBase):
    """确认对话框"""

    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setClosableOnMaskClicked(True)

        self.titleLabel = SubtitleLabel(title, self)
        self.viewLayout.addWidget(self.titleLabel)

        self.messageLabel = BodyLabel(message, self)
        self.messageLabel.setWordWrap(True)
        self.viewLayout.addWidget(self.messageLabel)

        self.yesButton.setText("确定")
        self.cancelButton.setText("取消")

        self.widget.setMinimumWidth(350)
```

---

## ⚠️ 已知问题：遮罩闪烁

### 问题描述

`MessageBoxBase` 的遮罩层 (`windowMask`) 使用 `QPropertyAnimation` 做淡入淡出动画。当对话框下方的控件使用半透明背景 (`rgba(...)`) 时，动画会导致明显的闪烁。

### 解决方案

**使用不透明颜色替代半透明颜色**

## 调用对话框

```python
# 标准调用方式
dialog = MyDialog(self.window())
if dialog.exec():
    # 用户点击确定
    value = dialog.get_value()
    # 处理数据...
```

---

## 检查清单

创建对话框时，确保：

- [ ] 继承 `MessageBoxBase`
- [ ] 调用 `self.setClosableOnMaskClicked(True)`
- [ ] 设置中文按钮文字 (`"确定"`/`"取消"`)
- [ ] 使用 `self.viewLayout` 添加控件
- [ ] 验证逻辑放在 `validate()` 方法中
- [ ] 设置合适的 `widget.setMinimumWidth()`
- [ ] 调用时使用 `self.window()` 作为 parent
- [ ] 对话框下方控件使用不透明背景色
