"""批量添加实验对话框"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from qfluentwidgets import (
    MessageBoxBase, SubtitleLabel, BodyLabel, CaptionLabel,
    LineEdit, ComboBox, CheckBox, InfoBar, InfoBarPosition
)

from api import experiment_api, APIError
from models.experiment import ExperimentCreateRequest, MatrixRow
from voidview_shared import ReferenceType
from ...components.color_badge import get_color_by_index


class AddExperimentDialog(MessageBoxBase):
    """批量添加实验对话框"""

    def __init__(self, selected_rows: list, matrix_rows: list, parent=None):
        super().__init__(parent)
        self._selected_rows = selected_rows  # 选中的行索引
        self._matrix_rows = matrix_rows      # 所有行数据
        self._created_experiment_id = None

        # 标题
        self.titleLabel = SubtitleLabel(self)
        self.titleLabel.setText("批量添加实验")
        self.viewLayout.addWidget(self.titleLabel)

        # 选中信息
        infoLabel = BodyLabel(self)
        infoLabel.setText(f"已选中 {len(selected_rows)} 行，将为这些模板创建实验")
        self.viewLayout.addWidget(infoLabel)

        # 实验名称输入
        self.nameLabel = BodyLabel(self)
        self.nameLabel.setText("实验名称")
        self.viewLayout.addWidget(self.nameLabel)

        self.nameEdit = LineEdit(self)
        self.nameEdit.setPlaceholderText("例如: xx客户_third_app实验")
        self.viewLayout.addWidget(self.nameEdit)

        # 参考类型
        self.refLabel = BodyLabel(self)
        self.refLabel.setText("参考类型")
        self.viewLayout.addWidget(self.refLabel)

        self.refCombo = ComboBox(self)
        self.refCombo.addItems(["全新模板", "供应商对齐", "自对齐"])
        self.refCombo.setCurrentIndex(0)
        self.viewLayout.addWidget(self.refCombo)

        # 模板预览
        self.previewLabel = BodyLabel(self)
        self.previewLabel.setText("选中的模板:")
        self.viewLayout.addWidget(self.previewLabel)

        # 模板列表
        previewWidget = QWidget(self)
        previewLayout = QVBoxLayout(previewWidget)
        previewLayout.setContentsMargins(8, 8, 8, 8)
        previewLayout.setSpacing(4)

        for row_idx in selected_rows:
            if row_idx < len(matrix_rows):
                row_data = matrix_rows[row_idx]
                template_info = f"{row_data.customer_name} / {row_data.app_name} / {row_data.template_name}"
                templateLabel = CaptionLabel(self)
                templateLabel.setText(f"  - {template_info}")
                previewLayout.addWidget(templateLabel)

        previewWidget.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 4px;
            }
        """)
        self.viewLayout.addWidget(previewWidget)

        # 颜色预览
        self.colorInfoLabel = CaptionLabel(self)
        self.colorInfoLabel.setText("点缀色将在创建后自动生成")
        self.colorInfoLabel.setStyleSheet("color: rgba(255, 255, 255, 0.6);")
        self.viewLayout.addWidget(self.colorInfoLabel)

        # 按钮
        self.yesButton.setText("创建")
        self.cancelButton.setText("取消")

        self.widget.setMinimumWidth(450)

    def validate(self) -> bool:
        """验证输入"""
        if not self.nameEdit.text().strip():
            InfoBar.warning(title="提示", content="请输入实验名称", parent=self)
            return False

        if not self._selected_rows:
            InfoBar.warning(title="提示", content="没有选中的行", parent=self)
            return False

        return True

    def getData(self) -> ExperimentCreateRequest:
        """获取表单数据"""
        refMap = {
            0: ReferenceType.NEW,
            1: ReferenceType.SUPPLIER,
            2: ReferenceType.SELF,
        }

        # 收集所有选中行的模板ID
        template_ids = []
        for row_idx in self._selected_rows:
            if row_idx < len(self._matrix_rows):
                template_ids.append(self._matrix_rows[row_idx].template_id)

        return ExperimentCreateRequest(
            template_ids=template_ids,
            name=self.nameEdit.text().strip(),
            reference_type=refMap[self.refCombo.currentIndex()]
        )

    def setCreatedExperimentId(self, experiment_id: int):
        """设置创建的实验ID"""
        self._created_experiment_id = experiment_id

    def getCreatedExperimentId(self) -> int:
        """获取创建的实验ID"""
        return self._created_experiment_id
