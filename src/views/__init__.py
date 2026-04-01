from PySide6.QtCore import QObject, QEvent, Qt
from PySide6.QtWidgets import QWidget, QSpinBox, QComboBox


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
            # 忽略滚轮，让父级 QScrollArea 处理
            event.ignore()
            return True
        return False


class _PopupShadowFilter(QObject):
    """弹出容器阴影移除过滤器。

    Qt 在每次 showPopup() 时都会为 QComboBox 的弹出容器重新添加
    QGraphicsDropShadowEffect（偏移 (3,3)、颜色接近黑色）。当
    QAbstractItemView 设置了 border-radius 后，右下角圆角处会露出该阴影。
    此过滤器监听容器的 Show 事件，在每次弹出时自动移除阴影效果。
    """

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Show and obj.graphicsEffect():
            obj.setGraphicsEffect(None)
        return False


# 模块级单例，避免重复创建
_noScrollFilter = _NoScrollFilter()
_popupShadowFilter = _PopupShadowFilter()


def polishInputWidgets(parent: QWidget):
    """统一修饰 parent 下的输入控件（QSpinBox / QComboBox）

    1. 安装滚轮过滤器：控件未聚焦时忽略滚轮，避免意外修改数值。
    2. 修复 ComboBox 弹出列表右下角圆角问题：Qt 每次 showPopup() 都会
       为弹出容器添加 QGraphicsDropShadowEffect（偏移右下 (3,3)、颜色接近
       黑色），导致 border-radius 右下角露出阴影。通过事件过滤器在每次弹出
       时自动移除该阴影效果。
    """

    for child in parent.findChildren(QSpinBox) + parent.findChildren(QComboBox):
        child.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        child.installEventFilter(_noScrollFilter)

    for combo in parent.findChildren(QComboBox):
        container = combo.view().parent()
        if container:
            container.installEventFilter(_popupShadowFilter)
