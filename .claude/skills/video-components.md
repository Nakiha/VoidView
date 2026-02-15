# 视频组件开发指南

此 SKILL 用于指导 VoidView 项目中视频播放器、视频对比组件的开发。

## 架构概述

```
┌───────────────────────────────────────────────────────────────┐
│                      视频组件架构                              │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                    VideoCompareWidget                    │ │
│  │  ┌─────────────────┐  ┌─────────────────┐              │ │
│  │  │  VideoPlayer A  │  │  VideoPlayer B  │              │ │
│  │  │  (原始/参考)    │  │  (转码后/实验)   │              │ │
│  │  └─────────────────┘  └─────────────────┘              │ │
│  │                                                         │ │
│  │  SyncController: 同步播放控制                           │ │
│  │  DisplayMode: side_by_side | split_screen | overlay     │ │
│  └─────────────────────────────────────────────────────────┘ │
│                            │                                  │
│                            ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                    ScreenshotTool                        │ │
│  │  - 区域截图                                              │ │
│  │  - 全屏截图                                              │ │
│  │  - 标注工具 (矩形框、箭头、文字)                         │ │
│  └─────────────────────────────────────────────────────────┘ │
│                            │                                  │
│                            ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                    VideoDecoder                          │ │
│  │  - FFmpeg 解码 (通用格式)                                │ │
│  │  - 自定义解码器 (特殊格式)                               │ │
│  │  - 硬件加速 (NVIDIA/Intel)                               │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. VideoPlayer 组件

```python
# src/ui/widgets/video_player.py
from PySide6.QtCore import Qt, Signal, QUrl, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSlider
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QVideoSink
from PySide6.QtMultimediaWidgets import QVideoWidget
from qfluentwidgets import PushButton, ToolButton, FluentIcon, Slider


class VideoPlayer(QWidget):
    """视频播放器组件"""

    # 信号定义
    positionChanged = Signal(float)  # 播放位置变化 (秒)
    durationChanged = Signal(float)  # 视频时长变化
    frameChanged = Signal(object)    # 当前帧变化 (QVideoFrame)
    playbackStateChanged = Signal(bool)  # 播放状态变化

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUI()
        self.setupPlayer()
        self._is_playing = False

    def setupUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # 视频显示区域
        self.videoWidget = QVideoWidget()
        self.videoWidget.setMinimumSize(320, 180)
        layout.addWidget(self.videoWidget, 1)

        # 控制栏
        controlLayout = QHBoxLayout()
        controlLayout.setSpacing(8)

        self.playBtn = ToolButton(FluentIcon.PLAY, self)
        self.playBtn.setFixedSize(32, 32)
        self.playBtn.clicked.connect(self.togglePlay)

        self.positionSlider = Slider(Qt.Horizontal, self)
        self.positionSlider.setRange(0, 1000)
        self.positionSlider.sliderMoved.connect(self.onSliderMoved)

        self.timeLabel = QLabel("00:00 / 00:00", self)

        controlLayout.addWidget(self.playBtn)
        controlLayout.addWidget(self.positionSlider, 1)
        controlLayout.addWidget(self.timeLabel)

        layout.addLayout(controlLayout)

    def setupPlayer(self):
        self.player = QMediaPlayer()
        self.audioOutput = QAudioOutput()
        self.videoSink = QVideoSink()

        self.player.setAudioOutput(self.audioOutput)
        self.player.setVideoOutput(self.videoSink)

        # 信号连接
        self.player.positionChanged.connect(self.onPositionChanged)
        self.player.durationChanged.connect(self.onDurationChanged)

        # 将帧渲染到 VideoWidget
        self.videoSink.videoFrameChanged.connect(
            self.videoWidget.videoSink().setVideoFrame
        )

    def loadVideo(self, url: str):
        """加载视频"""
        self.player.setSource(QUrl(url))
        self.player.pause()

    def togglePlay(self):
        """切换播放/暂停"""
        if self._is_playing:
            self.player.pause()
            self.playBtn.setIcon(FluentIcon.PLAY)
        else:
            self.player.play()
            self.playBtn.setIcon(FluentIcon.PAUSE)
        self._is_playing = not self._is_playing
        self.playbackStateChanged.emit(self._is_playing)

    def seek(self, position: float):
        """跳转到指定位置 (秒)"""
        self.player.setPosition(int(position * 1000))

    def setPosition(self, position: float):
        """设置播放位置 (用于同步)"""
        self.player.setPosition(int(position * 1000))

    def getPosition(self) -> float:
        """获取当前播放位置 (秒)"""
        return self.player.position() / 1000.0

    def getDuration(self) -> float:
        """获取视频时长 (秒)"""
        return self.player.duration() / 1000.0

    def setPlaybackRate(self, rate: float):
        """设置播放速度"""
        self.player.setPlaybackRate(rate)

    def grabCurrentFrame(self) -> QImage:
        """截取当前帧"""
        frame = self.videoSink.videoFrame()
        return frame.toImage()
```

### 2. VideoCompareWidget 组件

```python
# src/ui/widgets/video_compare.py
from enum import Enum
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget
from qfluentwidgets import ComboBox, PushButton, FluentIcon, SpinBox


class DisplayMode(Enum):
    SIDE_BY_SIDE = "side_by_side"  # 并排
    SPLIT_SCREEN = "split_screen"  # 分屏
    OVERLAY = "overlay"            # 叠加 (可切换)


class VideoCompareWidget(QWidget):
    """视频对比组件 - 支持并排、分屏、叠加模式"""

    syncEnabledChanged = Signal(bool)
    timeOffsetChanged = Signal(float)  # 时间偏移 (秒)
    displayModeChanged = Signal(DisplayMode)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.displayMode = DisplayMode.SIDE_BY_SIDE
        self.timeOffset = 0.0  # 时间偏移，用于同步不同FPS的视频
        self.syncEnabled = True
        self.setupUI()
        self.setupSync()

    def setupUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 视频容器 (使用 StackedWidget 切换不同显示模式)
        self.videoStack = QStackedWidget()

        # 并排模式
        self.sideBySideWidget = QWidget()
        sideLayout = QHBoxLayout(self.sideBySideWidget)
        sideLayout.setSpacing(4)
        self.playerA = VideoPlayer()
        self.playerB = VideoPlayer()
        sideLayout.addWidget(self.playerA, 1)
        sideLayout.addWidget(self.playerB, 1)

        # 分屏模式
        self.splitScreenWidget = SplitScreenWidget()

        # 叠加模式
        self.overlayWidget = OverlayVideoWidget()

        self.videoStack.addWidget(self.sideBySideWidget)
        self.videoStack.addWidget(self.splitScreenWidget)
        self.videoStack.addWidget(self.overlayWidget)

        layout.addWidget(self.videoStack, 1)

        # 控制面板
        controlPanel = self.createControlPanel()
        layout.addWidget(controlPanel)

    def createControlPanel(self) -> QWidget:
        panel = QWidget()
        layout = QHBoxLayout(panel)

        # 显示模式选择
        layout.addWidget(QLabel("显示模式:"))
        self.modeCombo = ComboBox()
        self.modeCombo.addItems(["并排", "分屏", "叠加"])
        self.modeCombo.currentIndexChanged.connect(self.onModeChanged)
        layout.addWidget(self.modeCombo)

        # 同步控制
        self.syncBtn = PushButton("同步: 开启", self)
        self.syncBtn.setCheckable(True)
        self.syncBtn.setChecked(True)
        self.syncBtn.clicked.connect(self.toggleSync)
        layout.addWidget(self.syncBtn)

        # 时间偏移
        layout.addWidget(QLabel("时间偏移:"))
        self.offsetSpinBox = SpinBox()
        self.offsetSpinBox.setRange(-10, 10)
        self.offsetSpinBox.setSingleStep(0.1)
        self.offsetSpinBox.setSuffix(" 秒")
        self.offsetSpinBox.valueChanged.connect(self.onOffsetChanged)
        layout.addWidget(self.offsetSpinBox)

        # 同步播放控制
        self.syncPlayBtn = PushButton(FluentIcon.PLAY, "同步播放", self)
        self.syncPlayBtn.clicked.connect(self.toggleSyncPlay)
        layout.addWidget(self.syncPlayBtn)

        layout.addStretch()
        return panel

    def setupSync(self):
        """设置同步播放逻辑"""
        # 当任一播放器位置变化时，同步另一个
        self.playerA.positionChanged.connect(
            lambda pos: self.syncPosition(self.playerA, self.playerB, pos)
        )
        self.playerB.positionChanged.connect(
            lambda pos: self.syncPosition(self.playerB, self.playerA, pos)
        )

    def syncPosition(self, source: VideoPlayer, target: VideoPlayer, pos: float):
        """同步播放位置"""
        if not self.syncEnabled:
            return

        # 应用时间偏移
        adjustedPos = pos + self.timeOffset
        targetPos = target.getPosition()

        # 只有差异超过阈值才同步，避免循环
        if abs(adjustedPos - targetPos) > 0.05:  # 50ms 容差
            target.setPosition(adjustedPos)

    def loadVideos(self, urlA: str, urlB: str, labelA: str = "原始", labelB: str = "转码"):
        """加载两个视频"""
        self.playerA.loadVideo(urlA)
        self.playerB.loadVideo(urlB)
        # 设置标签...

    def toggleSync(self):
        self.syncEnabled = not self.syncEnabled
        self.syncBtn.setText(f"同步: {'开启' if self.syncEnabled else '关闭'}")
        self.syncEnabledChanged.emit(self.syncEnabled)

    def toggleSyncPlay(self):
        """同步切换播放/暂停"""
        self.playerA.togglePlay()
        # playerB 会通过同步机制跟随

    def onModeChanged(self, index: int):
        modes = [DisplayMode.SIDE_BY_SIDE, DisplayMode.SPLIT_SCREEN, DisplayMode.OVERLAY]
        self.displayMode = modes[index]
        self.videoStack.setCurrentIndex(index)
        self.displayModeChanged.emit(self.displayMode)

    def onOffsetChanged(self, value: float):
        self.timeOffset = value
        self.timeOffsetChanged.emit(value)
```

### 3. ScreenshotTool 组件

```python
# src/ui/widgets/screenshot_tool.py
from PySide6.QtCore import Qt, Signal, QRect, QPoint
from PySide6.QtGui import QImage, QPainter, QPen, QColor, QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import ToolButton, FluentIcon, ComboBox, PushButton


class AnnotationType(Enum):
    RECT_RED = "rect_red"      # 红框
    RECT_YELLOW = "rect_yellow" # 黄框
    ARROW = "arrow"            # 箭头
    TEXT = "text"              # 文字


class ScreenshotTool(QWidget):
    """截图标注工具"""

    screenshotTaken = Signal(QImage, list)  # 截图完成信号 (图像, 标注列表)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.currentAnnotation = AnnotationType.RECT_RED
        self.annotations = []  # 标注列表
        self.isDrawing = False
        self.startPoint = QPoint()
        self.currentRect = QRect()
        self.setupUI()

    def setupUI(self):
        layout = QVBoxLayout(self)

        # 工具栏
        toolbar = QHBoxLayout()

        self.rectBtn = ToolButton(FluentIcon.RECT, self)
        self.rectBtn.setCheckable(True)
        self.rectBtn.setChecked(True)
        self.rectBtn.setToolTip("矩形框")

        self.arrowBtn = ToolButton(FluentIcon.UP, self)
        self.arrowBtn.setCheckable(True)
        self.arrowBtn.setToolTip("箭头")

        self.textBtn = ToolButton(FluentIcon.EDIT, self)
        self.textBtn.setCheckable(True)
        self.textBtn.setToolTip("文字标注")

        self.colorCombo = ComboBox()
        self.colorCombo.addItems(["红色", "黄色", "绿色"])

        self.clearBtn = ToolButton(FluentIcon.DELETE, self)
        self.clearBtn.setToolTip("清除标注")

        toolbar.addWidget(self.rectBtn)
        toolbar.addWidget(self.arrowBtn)
        toolbar.addWidget(self.textBtn)
        toolbar.addWidget(self.colorCombo)
        toolbar.addWidget(self.clearBtn)
        toolbar.addStretch()

        layout.addLayout(toolbar)

        # 截图区域
        self.canvas = ScreenshotCanvas(self)
        layout.addWidget(self.canvas, 1)

        # 操作按钮
        btnLayout = QHBoxLayout()
        self.captureBtn = PushButton("截取当前帧", self)
        self.saveBtn = PushButton("保存截图", self)
        btnLayout.addStretch()
        btnLayout.addWidget(self.captureBtn)
        btnLayout.addWidget(self.saveBtn)
        layout.addLayout(btnLayout)

        # 信号连接
        self.captureBtn.clicked.connect(self.captureFrame)
        self.saveBtn.clicked.connect(self.saveScreenshot)
        self.clearBtn.clicked.connect(self.clearAnnotations)

    def captureFromPlayer(self, player: VideoPlayer):
        """从播放器捕获当前帧"""
        image = player.grabCurrentFrame()
        self.canvas.setImage(image)

    def captureFrame(self):
        """截取当前帧"""
        # 发送截图和标注
        image = self.canvas.getImage()
        self.screenshotTaken.emit(image, self.annotations.copy())

    def clearAnnotations(self):
        self.annotations.clear()
        self.canvas.update()


class ScreenshotCanvas(QWidget):
    """截图画布 - 支持标注绘制"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = None
        self.annotations = []
        self.drawing = False
        self.startPos = QPoint()
        self.currentAnnotation = None
        self.setMouseTracking(True)

    def setImage(self, image: QImage):
        self.image = image
        self.update()

    def getImage(self) -> QImage:
        """获取带标注的图像"""
        if not self.image:
            return None

        result = self.image.copy()
        painter = QPainter(result)
        self.drawAnnotations(painter)
        painter.end()
        return result

    def paintEvent(self, event):
        painter = QPainter(self)

        # 绘制底图
        if self.image:
            scaled = self.image.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawImage(x, y, scaled)

        # 绘制标注
        self.drawAnnotations(painter)

    def drawAnnotations(self, painter: QPainter):
        for annotation in self.annotations:
            if annotation['type'] == 'rect':
                pen = QPen(QColor(annotation['color']), 2)
                painter.setPen(pen)
                painter.drawRect(annotation['rect'])
            elif annotation['type'] == 'arrow':
                # 绘制箭头
                pass
            elif annotation['type'] == 'text':
                painter.setPen(QPen(QColor(annotation['color'])))
                painter.setFont(QFont("Microsoft YaHei", 12))
                painter.drawText(annotation['pos'], annotation['text'])

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.startPos = event.pos()

    def mouseMoveEvent(self, event):
        if self.drawing:
            self.currentRect = QRect(self.startPos, event.pos()).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            # 保存标注
            self.annotations.append({
                'type': 'rect',
                'rect': self.currentRect,
                'color': '#FF0000'
            })
            self.update()
```

### 4. 使用示例

```python
# 在评测页面中使用
class SubjectiveEvaluationPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        # 视频对比组件
        self.videoCompare = VideoCompareWidget()
        layout.addWidget(self.videoCompare, 1)

        # 截图工具
        self.screenshotTool = ScreenshotTool()
        layout.addWidget(self.screenshotTool, 1)

        # 连接信号
        self.videoCompare.playerA.frameChanged.connect(self.onFrameChanged)

    def loadExperimentGroup(self, group: ExperimentGroup):
        """加载实验组视频"""
        self.videoCompare.loadVideos(
            urlA=group.input_url,  # 原始视频
            urlB=group.output_url,  # 转码后视频
            labelA="片源",
            labelB="转码后"
        )
```

## 特殊格式支持

对于需要自定义解码器的特殊格式:

```python
# src/utils/video_decoder.py
import ffmpeg
import numpy as np
from PySide6.QtGui import QImage


class CustomVideoDecoder:
    """自定义视频解码器 - 基于 FFmpeg"""

    def __init__(self):
        self.process = None

    def decode_frame(self, video_path: str, timestamp: float) -> QImage:
        """解码指定时间戳的帧"""
        # 使用 ffmpeg-python 调用 FFmpeg
        out, _ = (
            ffmpeg
            .input(video_path, ss=timestamp)
            .filter('scale', width=-1, height=720)
            .output('pipe:', vframes=1, format='image2', vcodec='png')
            .run(capture_stdout=True, quiet=True)
        )

        # 转换为 QImage
        image = QImage()
        image.loadFromData(out)
        return image

    def decode_custom_codec(self, video_path: str, codec_name: str):
        """使用自定义编解码器解码"""
        # 这里可以调用自定义的 C/C++ 解码器
        # 通过 ctypes 或 pybind11 调用
        pass
```

## 注意事项

1. 视频同步时注意避免信号循环
2. 大视频文件考虑预加载和缓存
3. 截图功能需要处理高 DPI 显示
4. 分屏模式需要自定义 Shader 实现
5. 硬件加速需要检测用户 GPU 支持
