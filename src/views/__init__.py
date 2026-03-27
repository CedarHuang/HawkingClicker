from PySide6.QtWidgets import QWidget


def _polishWidget(widget: QWidget):
    """刷新控件样式，使 setProperty 设置的动态属性在 QSS 中生效"""
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()
