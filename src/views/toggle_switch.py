"""
ToggleSwitch 开关控件
====================
自绘 iOS/Material 风格的 Toggle Switch，支持平滑滑动动画和双主题适配。
继承 QAbstractButton，兼容 toggled 信号，可无缝替换 QPushButton/QCheckBox。
"""

from PySide6.QtCore import (
    Qt, QSize, QRectF, QPointF, Property, QPropertyAnimation, QEasingCurve,
)
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QAbstractButton, QWidget


class ToggleSwitch(QAbstractButton):
    """自绘 Toggle Switch 开关控件

    通过 QSS qproperty 设置颜色，例如：
        ToggleSwitch { qproperty-trackColorOff: #D0D1D4; }

    支持的颜色属性：
        - trackColorOff:      轨道关闭色
        - trackColorOn:       轨道开启色
        - thumbColor:         滑块颜色
        - trackColorOffHover: 轨道关闭悬停色
        - trackColorOnHover:  轨道开启悬停色
    """

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)

        # 滑块位置（0.0=左/关, 1.0=右/开），用于动画
        self._thumbPosition = 1.0 if self.isChecked() else 0.0

        # 悬停状态
        self._hovered = False

        # 颜色属性（默认值，可通过 QSS qproperty 覆盖）
        self._trackColorOff = QColor("#D0D1D4")
        self._trackColorOn = QColor("#4078F2")
        self._thumbColor = QColor("#FFFFFF")
        self._trackColorOffHover = QColor("#B8B9BC")
        self._trackColorOnHover = QColor("#5289F5")

        # 动画
        self._animation = QPropertyAnimation(self, b"thumbPosition", self)
        self._animation.setDuration(150)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        # 连接 toggled 信号驱动动画
        self.toggled.connect(self._onToggled)

    # ---- 尺寸 ----

    def sizeHint(self) -> QSize:
        return QSize(40, 22)

    def minimumSizeHint(self) -> QSize:
        return QSize(36, 20)

    # ---- Qt Property: 颜色（供 QSS qproperty- 使用） ----

    def _getTrackColorOff(self) -> QColor:
        return self._trackColorOff

    def _setTrackColorOff(self, color: QColor):
        self._trackColorOff = QColor(color)
        self.update()

    def _getTrackColorOn(self) -> QColor:
        return self._trackColorOn

    def _setTrackColorOn(self, color: QColor):
        self._trackColorOn = QColor(color)
        self.update()

    def _getThumbColor(self) -> QColor:
        return self._thumbColor

    def _setThumbColor(self, color: QColor):
        self._thumbColor = QColor(color)
        self.update()

    def _getTrackColorOffHover(self) -> QColor:
        return self._trackColorOffHover

    def _setTrackColorOffHover(self, color: QColor):
        self._trackColorOffHover = QColor(color)
        self.update()

    def _getTrackColorOnHover(self) -> QColor:
        return self._trackColorOnHover

    def _setTrackColorOnHover(self, color: QColor):
        self._trackColorOnHover = QColor(color)
        self.update()

    trackColorOff = Property(QColor, _getTrackColorOff, _setTrackColorOff)
    trackColorOn = Property(QColor, _getTrackColorOn, _setTrackColorOn)
    thumbColor = Property(QColor, _getThumbColor, _setThumbColor)
    trackColorOffHover = Property(QColor, _getTrackColorOffHover, _setTrackColorOffHover)
    trackColorOnHover = Property(QColor, _getTrackColorOnHover, _setTrackColorOnHover)

    # ---- Qt Property: 滑块动画位置 ----

    def _getThumbPosition(self) -> float:
        return self._thumbPosition

    def _setThumbPosition(self, pos: float):
        self._thumbPosition = pos
        self.update()

    thumbPosition = Property(float, _getThumbPosition, _setThumbPosition)

    # ---- 事件处理 ----

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def _onToggled(self, checked: bool):
        """checked 状态变化时启动滑块动画"""
        self._animation.stop()
        self._animation.setStartValue(self._thumbPosition)
        self._animation.setEndValue(1.0 if checked else 0.0)
        self._animation.start()

    def setChecked(self, checked: bool):
        """重写 setChecked，支持无动画的直接设置（如初始化时）"""
        # 如果信号被阻断，直接跳到目标位置（无动画）
        if self.signalsBlocked():
            self._thumbPosition = 1.0 if checked else 0.0
        super().setChecked(checked)

    # ---- 绘制 ----

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        trackRadius = h / 2.0

        # 轨道颜色：根据 thumbPosition 在 off/on 之间插值
        t = self._thumbPosition
        if self._hovered and self.isEnabled():
            baseOff = self._trackColorOffHover
            baseOn = self._trackColorOnHover
        else:
            baseOff = self._trackColorOff
            baseOn = self._trackColorOn

        # 禁用态降低饱和度
        if not self.isEnabled():
            baseOff = self._dimColor(baseOff)
            baseOn = self._dimColor(baseOn)

        trackColor = self._lerpColor(baseOff, baseOn, t)

        # 绘制轨道
        trackRect = QRectF(0, 0, w, h)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(trackColor)
        p.drawRoundedRect(trackRect, trackRadius, trackRadius)

        # 滑块参数
        margin = 2.0
        thumbDiameter = h - 2 * margin
        thumbRadius = thumbDiameter / 2.0

        # 滑块 X 位置：从左到右
        xLeft = margin
        xRight = w - margin - thumbDiameter
        thumbX = xLeft + (xRight - xLeft) * t
        thumbY = margin

        # 绘制滑块阴影
        if self.isEnabled():
            shadowColor = QColor(0, 0, 0, 25)
            p.setBrush(shadowColor)
            p.drawEllipse(QPointF(thumbX + thumbRadius, thumbY + thumbRadius + 1),
                          thumbRadius, thumbRadius)

        # 绘制滑块
        thumbC = self._thumbColor if self.isEnabled() else self._dimColor(self._thumbColor)
        p.setBrush(thumbC)
        p.drawEllipse(QPointF(thumbX + thumbRadius, thumbY + thumbRadius),
                      thumbRadius, thumbRadius)

        p.end()

    # ---- 辅助方法 ----

    @staticmethod
    def _lerpColor(c1: QColor, c2: QColor, t: float) -> QColor:
        """线性插值两个颜色"""
        r = c1.red() + (c2.red() - c1.red()) * t
        g = c1.green() + (c2.green() - c1.green()) * t
        b = c1.blue() + (c2.blue() - c1.blue()) * t
        a = c1.alpha() + (c2.alpha() - c1.alpha()) * t
        return QColor(int(r), int(g), int(b), int(a))

    @staticmethod
    def _dimColor(color: QColor) -> QColor:
        """降低颜色饱和度和透明度（禁用态）"""
        c = QColor(color)
        c.setAlpha(int(c.alpha() * 0.5))
        return c
