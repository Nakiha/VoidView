"""瀑布流布局"""

from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtWidgets import QLayout, QSizePolicy, QWidgetItem


class WaterfallLayout(QLayout):
    """瀑布流布局

    将子组件按瀑布流方式排列，每列高度自动平衡。
    """

    def __init__(self, parent=None, columns: int = 3, spacing: int = 16):
        super().__init__(parent)
        self._columns = columns
        self._spacing = spacing
        self._items = []
        self._column_heights = [0] * columns

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Horizontal

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._doLayout(QRect(0, 0, width, 0), False)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._doLayout(rect, True)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        if not self._items:
            return QSize(0, 0)
        # 返回最小尺寸
        min_width = 200 * self._columns + self._spacing * (self._columns - 1)
        return QSize(min_width, 200)

    def setColumns(self, columns: int):
        """设置列数"""
        self._columns = max(1, columns)
        self._column_heights = [0] * self._columns
        self.invalidate()
        self.update()

    def setSpacing(self, spacing: int):
        """设置间距"""
        self._spacing = spacing
        self.invalidate()
        self.update()

    def clear(self):
        """清除所有项目"""
        while self._items:
            item = self._items.pop()
            if item.widget():
                item.widget().deleteLater()
        self._column_heights = [0] * self._columns
        self.invalidate()

    def _doLayout(self, rect, apply_geometry):
        """执行布局"""
        if not self._items:
            return 0

        x = rect.x()
        y = rect.y()
        width = rect.width()

        if width <= 0:
            return 0

        # 计算每列宽度
        total_spacing = self._spacing * (self._columns - 1)
        column_width = max(150, (width - total_spacing) // self._columns)

        # 重置列高度
        self._column_heights = [0] * self._columns

        for item in self._items:
            # 找到最短的列
            min_height = min(self._column_heights)
            min_column = self._column_heights.index(min_height)

            # 计算位置
            item_x = x + min_column * (column_width + self._spacing)
            item_y = y + self._column_heights[min_column]

            # 获取项目尺寸
            item_size = item.sizeHint()
            item_height = item_size.height()

            # 确保最小高度
            if item_height <= 0:
                item_height = 100

            if apply_geometry:
                item.setGeometry(QRect(item_x, item_y, column_width, item_height))

            # 更新列高度
            self._column_heights[min_column] += item_height + self._spacing

        return max(self._column_heights) if self._column_heights else 0
