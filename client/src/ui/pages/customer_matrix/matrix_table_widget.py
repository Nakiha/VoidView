"""矩阵卡片组件 - Fluent Design 卡片式UI"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from qfluentwidgets import (
    BodyLabel, CaptionLabel, CardWidget, CheckBox, FlowLayout,
    SmoothScrollArea, StrongBodyLabel
)

from models.experiment import MatrixRow, ExperimentBrief


class ColorSquare(QLabel):
    """装饰色方块 - 同字号大小的圆角正方形"""

    def __init__(self, color: str, size: int = 14, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setStyleSheet(f"""
            background-color: {color};
            border-radius: 3px;
        """)


class ExperimentTag(QWidget):
    """实验标签 - 带装饰色方块"""

    clicked = Signal(int)  # experiment_id

    def __init__(self, experiment: ExperimentBrief, parent=None):
        super().__init__(parent)
        self._experiment = experiment
        self.setupUI()

    def setupUI(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        # 装饰色方块
        color = self._experiment.color or "#888888"
        self.colorSquare = ColorSquare(color, 14, self)
        layout.addWidget(self.colorSquare)

        # 实验名
        self.label = BodyLabel(self)
        self.label.setText(self._experiment.name)
        layout.addWidget(self.label)

        self.setFixedHeight(28)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            ExperimentTag {
                background-color: rgba(255, 255, 255, 0.06);
                border-radius: 6px;
            }
            ExperimentTag:hover {
                background-color: rgba(255, 255, 255, 0.12);
            }
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._experiment.id)
        super().mousePressEvent(event)


class ExperimentTagsRow(QWidget):
    """实验标签行 - 显示多个实验标签，过多时折叠"""

    experimentClicked = Signal(int)

    MAX_VISIBLE_TAGS = 3

    def __init__(self, experiments: list, parent=None):
        super().__init__(parent)
        self._experiments = experiments
        self._expanded = True  # 默认展开（不折叠）
        self._tags = []
        self._moreBtn = None
        self.setupUI()

    def setupUI(self):
        self._mainLayout = FlowLayout(self, needAni=False)
        self._mainLayout.setContentsMargins(0, 0, 0, 0)
        self._mainLayout.setHorizontalSpacing(8)
        self._mainLayout.setVerticalSpacing(4)
        self._renderTags()

    def setExpanded(self, expanded: bool):
        """设置展开状态"""
        if self._expanded != expanded:
            self._expanded = expanded
            self._renderTags()

    def _clearLayout(self):
        """安全清除布局中的所有 widgets"""
        # 先收集所有需要删除的 widgets
        widgets_to_delete = []
        for i in range(self._mainLayout.count()):
            item = self._mainLayout.itemAt(i)
            if item is not None:
                # FlowLayout 的 itemAt 可能返回 QWidget 或 QLayoutItem
                if isinstance(item, QWidget):
                    widgets_to_delete.append(item)
                elif hasattr(item, 'widget'):
                    w = item.widget()
                    if w:
                        widgets_to_delete.append(w)

        # 从布局中移除并删除
        for widget in widgets_to_delete:
            self._mainLayout.removeWidget(widget)
            widget.setParent(None)
            widget.deleteLater()

        self._tags.clear()
        self._moreBtn = None

    def _renderTags(self):
        # 清除现有内容
        self._clearLayout()

        if not self._experiments:
            # 无实验
            label = CaptionLabel(self)
            label.setText("-")
            label.setStyleSheet("color: rgba(255, 255, 255, 0.25);")
            self._mainLayout.addWidget(label)
            return

        # 显示标签
        visible_count = len(self._experiments) if self._expanded else min(self.MAX_VISIBLE_TAGS, len(self._experiments))

        for exp in self._experiments[:visible_count]:
            tag = ExperimentTag(exp, self)
            tag.clicked.connect(self.experimentClicked.emit)
            self._mainLayout.addWidget(tag)
            self._tags.append(tag)

        # 如果折叠状态且还有更多，显示展开按钮
        if not self._expanded and len(self._experiments) > self.MAX_VISIBLE_TAGS:
            self._moreBtn = BodyLabel(self)
            self._moreBtn.setText(f"+{len(self._experiments) - self.MAX_VISIBLE_TAGS}")
            self._moreBtn.setCursor(Qt.PointingHandCursor)
            self._moreBtn.setFixedHeight(28)
            self._moreBtn.setStyleSheet("""
                BodyLabel {
                    color: rgba(255, 255, 255, 0.7);
                    padding: 0 10px;
                    background-color: rgba(255, 255, 255, 0.06);
                    border: 1px rgba(255, 255, 255, 0.2);
                    border-radius: 6px;
                }
                BodyLabel:hover {
                    background-color: rgba(255, 255, 255, 0.12);
                    border-color: rgba(255, 255, 255, 0.3);
                    color: rgba(255, 255, 255, 0.9);
                }
            """)
            self._moreBtn.mousePressEvent = lambda _: self._toggleExpand()
            self._mainLayout.addWidget(self._moreBtn)

    def _toggleExpand(self):
        self._expanded = not self._expanded
        self._renderTags()


class GroupTitleCard(QWidget):
    """分组标题 - 显示 "客户名 APP" """

    def __init__(self, customer_name: str, app_name: str, parent=None):
        super().__init__(parent)
        self._customer_name = customer_name
        self._app_name = app_name
        self.setupUI()

    def setupUI(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(0)

        title = StrongBodyLabel(self)
        title.setText(f"{self._customer_name}  {self._app_name}")
        layout.addWidget(title)
        layout.addStretch()


class MatrixCard(CardWidget):
    """矩阵卡片 - 一行数据"""

    rowClicked = Signal(int)  # row_index (非多选模式下)
    selectionToggled = Signal(int)  # row_index (多选模式下)
    experimentClicked = Signal(int)  # experiment_id

    def __init__(self, row_index: int, row_data: MatrixRow, parent=None):
        super().__init__(parent)
        self._row_index = row_index
        self._row_data = row_data
        self._selected = False
        self._multi_select_mode = False
        self.setupUI()

    def setupUI(self):
        self.setBorderRadius(6)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # 多选框（默认隐藏）
        self.checkBox = CheckBox(self)
        self.checkBox.setFixedSize(20, 20)
        self.checkBox.stateChanged.connect(self._onCheckBoxChanged)
        self.checkBox.setVisible(False)
        layout.addWidget(self.checkBox)

        # 左侧：模板名（单行）
        leftLabel = BodyLabel(self)
        leftLabel.setText(self._row_data.template_name)
        layout.addWidget(leftLabel, 1)

        # 右侧：实验标签
        experiments = list(self._row_data.experiments.values())
        self._tagsRow = ExperimentTagsRow(experiments, self)
        self._tagsRow.experimentClicked.connect(self.experimentClicked.emit)
        layout.addWidget(self._tagsRow, 2)

        # 设置可点击
        self.setCursor(Qt.PointingHandCursor)

    def setMultiSelectMode(self, enabled: bool):
        """设置多选模式"""
        self._multi_select_mode = enabled
        self.checkBox.setVisible(enabled)
        if not enabled:
            self.checkBox.setChecked(False)
            self._selected = False
            self._updateStyle()

    def setCollapsed(self, collapsed: bool):
        """设置标签折叠状态"""
        self._tagsRow.setExpanded(not collapsed)

    def setSelected(self, selected: bool):
        """设置选中状态"""
        self._selected = selected
        self.checkBox.blockSignals(True)
        self.checkBox.setChecked(selected)
        self.checkBox.blockSignals(False)
        self._updateStyle()

    def isSelected(self) -> bool:
        return self._selected

    def _onCheckBoxChanged(self, state):
        """复选框状态变化"""
        self._selected = state == Qt.Checked
        self._updateStyle()
        self.selectionToggled.emit(self._row_index)

    def _updateStyle(self):
        """更新样式"""
        self.setProperty("selected", self._selected)
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._multi_select_mode:
                # 多选模式下切换选中状态
                self.checkBox.setChecked(not self.checkBox.isChecked())
            else:
                # 非多选模式下发出点击信号
                self.rowClicked.emit(self._row_index)
        super().mousePressEvent(event)


class MatrixTableWidget(QWidget):
    """卡片式矩阵表格"""

    rowSelectionChanged = Signal(set)  # 选中的行索引集合
    rowClicked = Signal(int)           # 点击行（非多选模式）
    experimentClicked = Signal(int)    # 点击实验

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows = []
        self._row_widgets = []
        self._group_titles = []  # 分组标题列表 [(widget, customer_name, app_name), ...]
        self._selected_rows = set()
        self._filter_text = ""
        self._multi_select_mode = False

        self.setupUI()

    def setupUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 滚动区域
        self.scrollArea = SmoothScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setStyleSheet("""
            SmoothScrollArea {
                border: none;
                background: transparent;
            }
        """)

        # 卡片容器
        self.cardContainer = QWidget()
        self.cardContainer.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)
        self.cardLayout = QVBoxLayout(self.cardContainer)
        # 右边距 20px 给滚动条预留空间
        self.cardLayout.setContentsMargins(0, 0, 20, 0)
        self.cardLayout.setSpacing(6)

        self.scrollArea.setWidget(self.cardContainer)
        layout.addWidget(self.scrollArea)

    def setData(self, rows: list, experiments: list = None):
        """设置数据"""
        self._rows = rows
        self._selected_rows.clear()
        self._renderCards()

    def getSelectedRows(self) -> set:
        """获取选中的行索引"""
        return self._selected_rows.copy()

    def getSelectedRowData(self) -> list:
        """获取选中行的数据"""
        return [self._rows[i] for i in self._selected_rows if i < len(self._rows)]

    def setMultiSelectMode(self, enabled: bool):
        """设置多选模式"""
        self._multi_select_mode = enabled
        if not enabled:
            self._selected_rows.clear()
        for card in self._row_widgets:
            card.setMultiSelectMode(enabled)
        self._updateSelectionHighlight()

    def clearSelection(self):
        """清空选择"""
        self._selected_rows.clear()
        self._updateSelectionHighlight()
        self.rowSelectionChanged.emit(set())

    def setCollapsed(self, collapsed: bool):
        """设置所有标签的折叠状态"""
        for card in self._row_widgets:
            card.setCollapsed(collapsed)

    def applyFilter(self, filter_text: str):
        """应用筛选（外部调用）"""
        self._filter_text = filter_text.lower()
        self._applyFilters()

    def _renderCards(self):
        """渲染卡片"""
        # 清除现有内容
        self._clearCards()

        # 按客户名+APP分组渲染
        current_group = None
        for row_idx, row_data in enumerate(self._rows):
            group_key = (row_data.customer_name, row_data.app_name)

            # 新分组时插入标题
            if group_key != current_group:
                current_group = group_key
                title = GroupTitleCard(row_data.customer_name, row_data.app_name, self)
                self.cardLayout.addWidget(title)
                self._group_titles.append((title, row_data.customer_name, row_data.app_name))

            # 渲染卡片
            card = MatrixCard(row_idx, row_data, self)
            card.setMultiSelectMode(self._multi_select_mode)
            card.rowClicked.connect(self.rowClicked.emit)
            card.selectionToggled.connect(self._onSelectionToggled)
            card.experimentClicked.connect(self.experimentClicked.emit)
            self.cardLayout.addWidget(card)
            self._row_widgets.append(card)

        self.cardLayout.addStretch()

    def _clearCards(self):
        """清除所有卡片和标题"""
        while self.cardLayout.count():
            item = self.cardLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._row_widgets.clear()
        self._group_titles.clear()

    def _onSelectionToggled(self, row_idx: int):
        """选择状态切换"""
        if row_idx in self._selected_rows:
            self._selected_rows.discard(row_idx)
        else:
            self._selected_rows.add(row_idx)
        self._updateSelectionHighlight()
        self.rowSelectionChanged.emit(self._selected_rows.copy())

    def _updateSelectionHighlight(self):
        """更新选中高亮"""
        for i, card in enumerate(self._row_widgets):
            card.setSelected(i in self._selected_rows)

    def _applyFilters(self):
        """应用筛选"""
        if not self._filter_text:
            # 显示所有卡片和标题
            for card in self._row_widgets:
                card.setVisible(True)
            for title, _, _ in self._group_titles:
                title.setVisible(True)
            return

        # 先隐藏所有分组标题
        for title, _, _ in self._group_titles:
            title.setVisible(False)

        # 过滤卡片，并记录哪些分组有可见卡片
        visible_groups = set()
        for i, card in enumerate(self._row_widgets):
            if i < len(self._rows):
                row_data = self._rows[i]
                # 搜索客户名、APP、模板
                search_text = f"{row_data.customer_name} {row_data.app_name} {row_data.template_name}".lower()
                visible = self._filter_text in search_text
                card.setVisible(visible)
                if visible:
                    visible_groups.add((row_data.customer_name, row_data.app_name))

        # 显示有可见卡片的分组标题
        for title, customer_name, app_name in self._group_titles:
            if (customer_name, app_name) in visible_groups:
                title.setVisible(True)
