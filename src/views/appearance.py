"""
外观管理器
=========
管理应用的外观呈现，包括主题样式加载和国际化翻译安装。

所有资源通过 Qt Resource System（qrc）加载，
使用 :/ 前缀路径引用编译到 resources_rc.py 中的资源。
"""

from PySide6.QtCore import QFile, QIODevice, QTranslator, QLocale
from PySide6.QtWidgets import QApplication


def _loadQss(name: str) -> str:
    """从 Qt 资源系统读取 .qss 文件内容"""
    f = QFile(f":/styles/{name}")
    if f.open(QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text):
        data = f.readAll().data().decode("utf-8")
        f.close()
        return data
    return ""


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
    """从 Qt 资源系统加载并安装翻译文件

    Args:
        app: QApplication 实例

    Returns:
        QTranslator: 翻译器实例（需保持引用以防被回收）
    """
    translator = QTranslator()
    if translator.load(QLocale(), "hawkingclicker", "_", ":/translations", ".qm"):
        app.installTranslator(translator)
    return translator
