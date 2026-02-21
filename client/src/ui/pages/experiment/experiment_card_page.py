"""实验卡片页面 - 瀑布流布局"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame
from qfluentwidgets import (
    SubtitleLabel, BodyLabel, CaptionLabel, CardWidget,
    PrimaryPushButton, PushButton, ComboBox, FluentIcon,
    InfoBar, InfoBarPosition, SmoothScrollArea, FlowLayout
)

from api import experiment_api, APIError
from models.experiment import ExperimentResponse
from voidview_shared import ExperimentStatus
from ..components.waterfall_layout import WaterfallLayout


class ExperimentCard(CardWidget):
    """实验卡片"""

    cardClicked = Signal(int)  # experiment_id

    def __init__(self, experiment: ExperimentResponse, parent=None):
        super().__init__(parent)
        self._experiment = experiment
        self.setupUI()

    def setupUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(4)

        # 第一行：装饰色方块 + 标题
        headerLayout = QHBoxLayout()
        headerLayout.setSpacing(8)

        # 装饰色圆角矩形
        color = self._experiment.color or "#0078D4"
        colorDot = QFrame(self)
        colorDot.setFixedSize(12, 12)
        colorDot.setStyleSheet(f"""
            background-color: {color};
            border-radius: 4px;
        """)
        headerLayout.addWidget(colorDot)

        # 标题
        nameLabel = SubtitleLabel(self)
        nameLabel.setText(self._experiment.name)
        nameLabel.setWordWrap(True)
        headerLayout.addWidget(nameLabel, 1)

        layout.addLayout(headerLayout)

        # 分隔线
        separator = QFrame(self)
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: rgba(255, 255, 255, 0.1);")
        layout.addWidget(separator)

        # 第二行：创建时间 + 状态
        metaLayout = QHBoxLayout()
        metaLayout.setSpacing(12)

        # 创建时间
        timeLabel = CaptionLabel(self)
        if self._experiment.created_at:
            timeLabel.setText(self._experiment.created_at.strftime("%Y-%m-%d %H:%M"))
        timeLabel.setStyleSheet("color: rgba(255, 255, 255, 0.5);")
        metaLayout.addWidget(timeLabel)

        # 状态标签
        statusText = self._getStatusText(self._experiment.status)
        statusColor = self._getStatusColor(self._experiment.status)
        statusLabel = CaptionLabel(self)
        statusLabel.setText(statusText)
        statusLabel.setStyleSheet(f"""
            color: {statusColor};
            font-weight: 500;
        """)
        metaLayout.addWidget(statusLabel)

        metaLayout.addStretch()
        layout.addLayout(metaLayout)

        # 模板列表（胶囊形状，高对比度）
        if self._experiment.template_names:
            templatesContainer = QWidget(self)
            templatesLayout = FlowLayout(templatesContainer, needAni=False)
            templatesLayout.setSpacing(6)
            templatesLayout.setContentsMargins(0, 0, 0, 0)

            for template_name in self._experiment.template_names:
                # 使用 CaptionLabel 配合样式表实现高对比度胶囊
                pill = CaptionLabel(templatesContainer)
                pill.setText(template_name)
                pill.setFixedHeight(24)
                pill.setStyleSheet("""
                    QLabel {
                        color: rgba(255, 255, 255, 0.95);
                        background-color: rgba(255, 255, 255, 0.15);
                        padding: 2px 10px;
                        border-radius: 12px;
                    }
                """)
                templatesLayout.addWidget(pill)

            layout.addWidget(templatesContainer)

        # 点击样式
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.cardClicked.emit(self._experiment.id)
        super().mousePressEvent(event)

    def _getStatusText(self, status) -> str:
        status_map = {
            ExperimentStatus.DRAFT: "草稿",
            ExperimentStatus.RUNNING: "进行中",
            ExperimentStatus.COMPLETED: "已完成",
            ExperimentStatus.ARCHIVED: "已归档",
        }
        return status_map.get(status, str(status))

    def _getStatusColor(self, status) -> str:
        color_map = {
            ExperimentStatus.DRAFT: "#888888",
            ExperimentStatus.RUNNING: "#0078D4",
            ExperimentStatus.COMPLETED: "#107C10",
            ExperimentStatus.ARCHIVED: "#A80000",
        }
        return color_map.get(status, "#888888")

    def _getStatusColor(self, status) -> str:
        color_map = {
            ExperimentStatus.DRAFT: "#888888",
            ExperimentStatus.RUNNING: "#0078D4",
            ExperimentStatus.COMPLETED: "#107C10",
            ExperimentStatus.ARCHIVED: "#A80000",
        }
        return color_map.get(status, "#888888")


class ExperimentCardPage(QWidget):
    """实验卡片页面 - 瀑布流布局"""

    experimentClicked = Signal(int)  # experiment_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._experiments = []
        self._page = 1
        self._pageSize = 50  # 卡片视图一次加载更多
        self._total = 0

        self.setupUI()
        self.loadExperiments()

    def setupUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 标题栏
        headerLayout = QHBoxLayout()
        title = SubtitleLabel(self)
        title.setText("实验概览")
        headerLayout.addWidget(title)
        headerLayout.addStretch()

        # 状态筛选
        self.statusCombo = ComboBox(self)
        self.statusCombo.addItems(["全部状态", "草稿", "进行中", "已完成", "已归档"])
        self.statusCombo.setCurrentIndex(0)
        self.statusCombo.setFixedWidth(120)
        self.statusCombo.currentIndexChanged.connect(self._onStatusChanged)
        headerLayout.addWidget(self.statusCombo)

        # 刷新按钮
        self.refreshBtn = PushButton(self)
        self.refreshBtn.setIcon(FluentIcon.SYNC)
        self.refreshBtn.setText("刷新")
        self.refreshBtn.clicked.connect(self.loadExperiments)
        headerLayout.addWidget(self.refreshBtn)

        layout.addLayout(headerLayout)

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
        self.cardContainer.setStyleSheet("background: transparent;")
        self.waterfallLayout = WaterfallLayout(self.cardContainer, columns=3, spacing=16)
        self.cardContainer.setLayout(self.waterfallLayout)

        self.scrollArea.setWidget(self.cardContainer)
        layout.addWidget(self.scrollArea)

    def loadExperiments(self):
        """加载实验列表"""
        try:
            status = self._getSelectedStatus()
            result = experiment_api.list(
                page=self._page,
                page_size=self._pageSize,
                status=status
            )

            self._experiments = result.items
            self._total = result.total

            self._renderCards()

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
        self.loadExperiments()

    def _getSelectedStatus(self) -> str:
        """获取选中状态"""
        idx = self.statusCombo.currentIndex()
        statuses = [None, "draft", "running", "completed", "archived"]
        if idx < len(statuses):
            return statuses[idx]
        return None

    def _onStatusChanged(self, index):
        """状态筛选变化"""
        self._page = 1
        self.loadExperiments()

    def _renderCards(self):
        """渲染卡片"""
        # 清除现有卡片
        self._clearCards()

        # 创建卡片
        for exp in self._experiments:
            card = ExperimentCard(exp, self)
            card.cardClicked.connect(lambda eid: self.experimentClicked.emit(eid))
            self.waterfallLayout.addWidget(card)

    def _clearCards(self):
        """清除所有卡片"""
        self.waterfallLayout.clear()

    def resizeEvent(self, event):
        """窗口大小变化时调整列数"""
        super().resizeEvent(event)
        if hasattr(self, 'waterfallLayout'):
            # 根据宽度调整列数
            width = self.width()
            if width < 600:
                self.waterfallLayout.setColumns(1)
            elif width < 900:
                self.waterfallLayout.setColumns(2)
            elif width < 1200:
                self.waterfallLayout.setColumns(3)
            else:
                self.waterfallLayout.setColumns(4)
