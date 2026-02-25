# 视频组件 (规划中)

> ⚠️ 此文档描述的是规划中的功能，尚未实现。仅作参考。

## 核心组件

### VideoPlayer
- 基于 QMediaPlayer + FFmpeg
- 支持播放、暂停、进度控制

### VideoCompareWidget
- 双视频对比 (原始 vs 转码后)
- 同步播放控制
- 显示模式: side_by_side | split_screen | overlay

### ScreenshotTool
- 区域截图
- 标注工具 (矩形框、箭头、文字)

## 依赖

- PySide6.QtMultimedia
- FFmpeg (硬件加速可选)
