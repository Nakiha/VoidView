"""矩阵卡片组件 - Fluent Design 卡片式UI"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from qfluentwidgets import (
    BodyLabel, CaptionLabel, CardWidget, CheckBox, SmoothScrollArea
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
        self._expanded = False
        self._tags = []
        self._moreBtn = None
        self.setupUI()

    def setupUI(self):
        self._mainLayout = QHBoxLayout(self)
        self._mainLayout.setContentsMargins(0, 0, 0, 0)
        self._mainLayout.setSpacing(8)
        self._renderTags()

    def _renderTags(self):
        # 清除现有内容
        while self._mainLayout.count():
            item = self._mainLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._tags.clear()

        if not self._experiments:
            # 无实验
            label = CaptionLabel(self)
            label.setText("-")
            label.setStyleSheet("color: rgba(255, 255, 255, 0.25);")
            self._mainLayout.addWidget(label)
            self._mainLayout.addStretch()
            return

        # 显示标签
        visible_count = len(self._experiments) if self._expanded else min(self.MAX_VISIBLE_TAGS, len(self._experiments))

        for i, exp in enumerate(self._experiments[:visible_count]):
            tag = ExperimentTag(exp, self)
            tag.clicked.connect(self.experimentClicked.emit)
            self._mainLayout.addWidget(tag)
            self._tags.append(tag)

        # 如果还有更多，显示展开按钮
        if len(self._experiments) > self.MAX_VISIBLE_TAGS and not self._expanded:
            self._moreBtn = BodyLabel(self)
            self._moreBtn.setText(f"+{len(self._experiments) - self.MAX_VISIBLE_TAGS}")
            self._moreBtn.setCursor(Qt.PointingHandCursor)
            self._moreBtn.setFixedHeight(28)
            self._moreBtn.setStyleSheet("""
                BodyLabel {
                    color: #0078D4;
                    padding: 0 10px;
                    background-color: rgba(0, 120, 212, 0.12);
                    border-radius: 6px;
                }
                BodyLabel:hover {
                    background-color: rgba(0, 120, 212, 0.2);
                }
            """)
            self._moreBtn.mousePressEvent = lambda e: self._toggleExpand()
            self._mainLayout.addWidget(self._moreBtn)

        self._mainLayout.addStretch()

    def _toggleExpand(self):
        self._expanded = not self._expanded
        self._renderTags()


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
        self.checkBox.setFixedWidth(20)
        self.checkBox.stateChanged.connect(self._onCheckBoxChanged)
        self.checkBox.setVisible(False)
        layout.addWidget(self.checkBox)

        # 左侧：客户名、APP/模板
        leftWidget = QWidget(self)
        leftLayout = QVBoxLayout(leftWidget)
        leftLayout.setContentsMargins(0, 0, 0, 0)
        leftLayout.setSpacing(2)

        # 客户名
        customerLabel = BodyLabel(leftWidget)
        customerLabel.setText(self._row_data.customer_name)
        customerLabel.setStyleSheet("font-weight: 600;")
        leftLayout.addWidget(customerLabel)

        # APP / 模板
        pathLabel = CaptionLabel(leftWidget)
        pathLabel.setText(f"{self._row_data.app_name} / {self._row_data.template_name}")
        pathLabel.setStyleSheet("color: rgba(255, 255, 255, 0.5);")
        leftLayout.addWidget(pathLabel)

        layout.addWidget(leftWidget, 1)

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
            MatrixCard[selected="true"] {
                background-color: rgba(0, 120, 212, 0.15);
            }
        """)
        self.cardLayout = QVBoxLayout(self.cardContainer)
        self.cardLayout.setContentsMargins(0, 4, 0, 12)
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

    def applyFilter(self, filter_text: str):
        """应用筛选（外部调用）"""
        self._filter_text = filter_text.lower()
        self._applyFilters()

    def _renderCards(self):
        """渲染卡片"""
        # 清除现有内容
        self._clearCards()

        # 渲染卡片
        for row_idx, row_data in enumerate(self._rows):
            card = MatrixCard(row_idx, row_data, self)
            card.setMultiSelectMode(self._multi_select_mode)
            card.rowClicked.connect(self.rowClicked.emit)
            card.selectionToggled.connect(self._onSelectionToggled)
            card.experimentClicked.connect(self.experimentClicked.emit)
            self.cardLayout.addWidget(card)
            self._row_widgets.append(card)

        self.cardLayout.addStretch()

    def _clearCards(self):
        """清除所有卡片"""
        while self.cardLayout.count():
            item = self.cardLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._row_widgets.clear()

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
            for card in self._row_widgets:
                card.setVisible(True)
            return

        for i, card in enumerate(self._row_widgets):
            if i < len(self._rows):
                row_data = self._rows[i]
                # 搜索客户名、APP、模板
                search_text = f"{row_data.customer_name} {row_data.app_name} {row_data.template_name}".lower()
                card.setVisible(self._filter_text in search_text)
