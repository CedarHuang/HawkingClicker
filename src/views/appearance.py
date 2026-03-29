"""
外观管理器
=========
管理应用的外观呈现，包括主题样式加载和国际化翻译安装。
"""

import os
from pathlib import Path

from PySide6.QtCore import QTranslator, QLocale
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


def installTranslator(app: QApplication):
    """加载并安装 Qt 翻译文件

    Args:
        app: QApplication 实例

    Returns:
        QTranslator: 翻译器实例（需保持引用以防被回收）
    """
    translator = QTranslator()
    trDir = str(Path(__file__).parent.parent / "translations" / "generated")
    if translator.load(QLocale(), "hawkingclicker", "_", trDir, ".qm"):
        app.installTranslator(translator)
    return translator
