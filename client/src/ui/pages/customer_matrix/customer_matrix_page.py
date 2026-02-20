"""客户矩阵页面"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    SubtitleLabel, BodyLabel, TransparentToolButton, FluentIcon,
    LineEdit, InfoBar, InfoBarPosition
)

from api import experiment_api, APIError
from models.experiment import MatrixResponse
from .matrix_table_widget import MatrixTableWidget
from .floating_toolbar import FloatingToolbar
from .dialogs import AddEntityDialog, AddExperimentDialog


class CustomerMatrixPage(QWidget):
    """客户矩阵页面 - Excel 风格展示 Customer-App-Template-Experiment 关系"""

    # 信号: 请求跳转到实验详情
    experimentClicked = Signal(int)  # experiment_id
    rowClicked = Signal(int)  # 行点击（非多选模式下）

    def __init__(self, parent=None):
        super().__init__(parent)
        self._matrix_data = MatrixResponse(rows=[], experiments=[])
        self._selected_rows = set()
        self._multi_select_mode = False

        self.setupUI()
        self.loadData()

    def setupUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 标题栏
        headerLayout = QHBoxLayout()
        title = SubtitleLabel(self)
        title.setText("客户矩阵")
        headerLayout.addWidget(title)
        headerLayout.addStretch()

        # 多选按钮
        self.multiSelectBtn = TransparentToolButton(FluentIcon.CHECKBOX, self)
        self.multiSelectBtn.setCheckable(True)
        self.multiSelectBtn.clicked.connect(self._toggleMultiSelect)
        headerLayout.addWidget(self.multiSelectBtn)

        # 刷新按钮
        self.refreshBtn = TransparentToolButton(FluentIcon.SYNC, self)
        self.refreshBtn.clicked.connect(self.loadData)
        headerLayout.addWidget(self.refreshBtn)

        # 搜索框
        self.searchEdit = LineEdit(self)
        self.searchEdit.setPlaceholderText("搜索客户名、APP、模板...")
        self.searchEdit.setFixedWidth(280)
        self.searchEdit.setFixedHeight(32)
        self.searchEdit.textChanged.connect(self._onSearchChanged)
        headerLayout.addWidget(self.searchEdit)

        layout.addLayout(headerLayout)

        # 表格区域
        self.matrixTable = MatrixTableWidget(self)
        self.matrixTable.rowSelectionChanged.connect(self._onRowSelectionChanged)
        self.matrixTable.experimentClicked.connect(self._onExperimentClicked)
        self.matrixTable.rowClicked.connect(self._onRowClicked)
        layout.addWidget(self.matrixTable)

        # 悬浮工具栏
        self.floatingToolbar = FloatingToolbar(self)
        self.floatingToolbar.addEntityClicked.connect(self._showAddEntityDialog)
        self.floatingToolbar.addExperimentClicked.connect(self._showAddExperimentDialog)

    def _toggleMultiSelect(self):
        """切换多选模式"""
        self._multi_select_mode = self.multiSelectBtn.isChecked()

        # 更新按钮样式
        if self._multi_select_mode:
            self.multiSelectBtn.setStyleSheet("""
                TransparentToolButton {
                    background-color: rgba(255, 200, 0, 0.3);
                    border-radius: 4px;
                }
            """)
        else:
            self.multiSelectBtn.setStyleSheet("")
            # 退出多选模式时清空选择
            self.matrixTable.clearSelection()

        # 更新表格的多选模式
        self.matrixTable.setMultiSelectMode(self._multi_select_mode)

    def _onRowClicked(self, row_idx: int):
        """行点击（非多选模式下）"""
        # 预留给后续业务逻辑
        pass

    def _onSearchChanged(self, text: str):
        """搜索文本变化"""
        self.matrixTable.applyFilter(text)

    def loadData(self):
        """加载矩阵数据"""
        try:
            self._matrix_data = experiment_api.get_matrix()
            self.matrixTable.setData(self._matrix_data.rows, self._matrix_data.experiments)
            self._selected_rows.clear()
            self.floatingToolbar.setHasSelection(False)
        except APIError as e:
            InfoBar.error(
                title="加载失败",
                content=e.message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )

    def refresh(self):
        """刷新数据"""
        self.loadData()

    def _onRowSelectionChanged(self, selected_rows: set):
        """行选择变化"""
        self._selected_rows = selected_rows
        self.floatingToolbar.setHasSelection(len(selected_rows) > 0)

    def _onExperimentClicked(self, experiment_id: int):
        """点击实验"""
        self.experimentClicked.emit(experiment_id)

    def _showAddEntityDialog(self):
        """显示添加客户/APP/模板对话框"""
        dialog = AddEntityDialog(self)
        dialog.exec()
        # 刷新数据
        self.loadData()

    def _showAddExperimentDialog(self):
        """显示批量添加实验对话框"""
        if not self._selected_rows:
            InfoBar.warning(
                title="提示",
                content="请先选择要添加实验的行",
                parent=self
            )
            return

        dialog = AddExperimentDialog(
            list(self._selected_rows),
            self._matrix_data.rows,
            self
        )
        if dialog.exec():
            data = dialog.getData()
            try:
                experiment = experiment_api.create(data)
                InfoBar.success(
                    title="成功",
                    content=f"实验 '{data.name}' 创建成功",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                # 刷新数据
                self.loadData()
            except APIError as e:
                InfoBar.error(
                    title="创建失败",
                    content=e.message,
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )

    def resizeEvent(self, event):
        """窗口大小变化时调整工具栏位置"""
        super().resizeEvent(event)
        if hasattr(self, 'floatingToolbar'):
            self.floatingToolbar._adjustPosition()
