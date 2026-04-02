from PySide6.QtCore import QObject, QEvent, Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtWidgets import QWidget, QSpinBox, QComboBox, QGraphicsOpacityEffect


def _polishWidget(widget: QWidget):
    """刷新控件样式，使 setProperty 设置的动态属性在 QSS 中生效"""
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


class _NoScrollFilter(QObject):
    """滚轮事件过滤器：控件未聚焦时忽略滚轮，避免意外修改数值。

    安装后会将控件的 focusPolicy 设为 StrongFocus（仅点击/Tab 聚焦），
    未聚焦时滚轮事件被忽略并自动传递给父级滚动区域。
    """

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Wheel and not obj.hasFocus():
            event.ignore()
            return True
        return False


class _ComboPopupFadeFilter(QObject):
    """QComboBox 弹出容器事件过滤器：淡入淡出 + 阴影移除。

    安装在弹出容器（combo.view().window()）上，监听 Show/Hide 事件：
    - Show：移除 Qt 自动添加的阴影，启动淡入动画。
    - Hide：重置透明度状态，确保下次弹出正常。

    淡出由 combo.hidePopup 的猴子补丁驱动，在动画结束后才真正关闭弹层。
    """

    _DURATION = 120  # ms

    def installOn(self, combo: QComboBox):
        """为 combo 安装弹层淡入淡出。仅首次调用生效。"""
        if getattr(combo, "_fadeInstalled", False):
            return
        combo._fadeInstalled = True
        combo._fadeClosing = False
        combo._fadeAnim = None

        # 绑定容器
        container = combo.view().window()
        container._fadeCombo = combo
        container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        container.installEventFilter(self)

        # 保存原始方法
        origShow = combo.showPopup
        origHide = combo.hidePopup
        ctrl = self

        def _showPopup():
            ctrl._stopAnim(combo)
            combo._fadeClosing = False
            ctrl._opacityEffect(combo.view()).setOpacity(0.0)
            origShow()

        def _hidePopup():
            if combo._fadeClosing:
                return
            if not container.isVisible():
                ctrl._opacityEffect(combo.view()).setOpacity(1.0)
                origHide()
                return
            combo._fadeClosing = True
            ctrl._animate(combo, 0.0, QEasingCurve.Type.InCubic,
                          lambda: ctrl._finishHide(combo, origHide))

        combo.showPopup = _showPopup
        combo.hidePopup = _hidePopup

    # ---- 事件过滤 ----

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Show:
            # 移除 Qt 每次弹出时自动添加的 QGraphicsDropShadowEffect
            if obj.graphicsEffect():
                obj.setGraphicsEffect(None)
            # 延迟一帧启动淡入，确保弹层已完成布局
            QTimer.singleShot(0, lambda c=obj: self._fadeIn(c))
        elif event.type() == QEvent.Type.Hide:
            # 安全网：弹层被外部关闭时重置状态
            combo = getattr(obj, "_fadeCombo", None)
            if combo is not None:
                combo._fadeClosing = False
                self._stopAnim(combo)
                self._opacityEffect(combo.view()).setOpacity(1.0)
        return False

    # ---- 内部方法 ----

    def _opacityEffect(self, view) -> QGraphicsOpacityEffect:
        effect = view.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(view)
            effect.setOpacity(1.0)
            view.setGraphicsEffect(effect)
        return effect

    def _stopAnim(self, combo: QComboBox):
        anim = combo._fadeAnim
        if anim is not None:
            combo._fadeAnim = None
            anim.stop()

    def _animate(self, combo: QComboBox, endVal: float,
                 curve: QEasingCurve.Type, onDone=None):
        self._stopAnim(combo)
        effect = self._opacityEffect(combo.view())
        anim = QPropertyAnimation(effect, b"opacity", combo)
        anim.setDuration(self._DURATION)
        anim.setStartValue(effect.opacity())
        anim.setEndValue(endVal)
        anim.setEasingCurve(curve)
        combo._fadeAnim = anim

        def finished():
            if combo._fadeAnim is not anim:
                return
            combo._fadeAnim = None
            if onDone:
                onDone()

        anim.finished.connect(finished)
        anim.start()

    def _fadeIn(self, container):
        combo = getattr(container, "_fadeCombo", None)
        if combo is None or combo._fadeClosing or not container.isVisible():
            return
        # 移除容器自身的阴影（Qt 可能在 show 后再次添加）
        if container.graphicsEffect():
            container.setGraphicsEffect(None)
        self._animate(combo, 1.0, QEasingCurve.Type.OutCubic)

    def _finishHide(self, combo: QComboBox, origHide):
        combo._fadeClosing = False
        self._opacityEffect(combo.view()).setOpacity(1.0)
        origHide()


# 模块级单例
_noScrollFilter = _NoScrollFilter()
_comboFadeFilter = _ComboPopupFadeFilter()


def polishInputWidgets(parent: QWidget):
    """统一修饰 parent 下的输入控件（QSpinBox / QComboBox）

    1. 安装滚轮过滤器：控件未聚焦时忽略滚轮，避免意外修改数值。
    2. 为 ComboBox 弹层安装淡入淡出动画 + 阴影移除。
    """

    for child in parent.findChildren(QSpinBox) + parent.findChildren(QComboBox):
        child.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        child.installEventFilter(_noScrollFilter)

    for combo in parent.findChildren(QComboBox):
        _comboFadeFilter.installOn(combo)
