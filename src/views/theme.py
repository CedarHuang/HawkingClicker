"""
主题与样式
=========
加载 QSS 样式文件并应用主题到 QApplication。
"""

import os

from PySide6.QtWidgets import QApplication

# 路径常量
_SRC_DIR = os.path.dirname(os.path.abspath(__file__)) + os.sep + ".."
_UI_DIR = os.path.join(_SRC_DIR, "ui")
_STYLES_DIR = os.path.join(_UI_DIR, "styles")


def _loadQss(filename: str) -> str:
    """读取 .qss 文件内容"""
    filepath = os.path.join(_STYLES_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def applyTheme(app: QApplication, theme: str):
    """合并 base.qss + 主题 qss 并应用到 QApplication

    Args:
        app: QApplication 实例
        theme: 主题名称 ("dark" 或 "light")
    """
    base = _loadQss("base.qss")
    themeQss = _loadQss(f"{theme}.qss")
    app.setStyleSheet(base + "\n\n" + themeQss)
