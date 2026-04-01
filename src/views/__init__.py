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


# 模块级单例，避免重复创建
_noScrollFilter = _NoScrollFilter()


def installNoScrollFilter(parent: QWidget):
    """为 parent 下所有 QSpinBox 和 QComboBox 安装滚轮过滤器"""
    for child in parent.findChildren(QSpinBox) + parent.findChildren(QComboBox):
        child.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        child.installEventFilter(_noScrollFilter)
