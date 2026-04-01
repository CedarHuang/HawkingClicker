"""
外观管理器
=========
管理应用的外观呈现，包括主题样式加载和国际化翻译安装。

所有资源通过 Qt Resource System（qrc）加载，
使用 :/ 前缀路径引用编译到 resources_rc.py 中的资源。
"""

import re
import sys
import winreg

from PySide6.QtCore import QFile, QIODevice, QTranslator, QLocale
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

# 用于从 QSS 中提取 QLabel#aboutGithub 的 color 值的正则
# 匹配形如 QLabel#aboutGithub { ... color: #RRGGBB; ... }
_RE_LINK_COLOR = re.compile(
    r"QLabel#aboutGithub\s*\{[^}]*?\bcolor\s*:\s*(#[0-9A-Fa-f]{6})", re.DOTALL
)


def _loadQss(name: str) -> str:
    """从 Qt 资源系统读取 .qss 文件内容"""
    f = QFile(f":/styles/{name}")
    if f.open(QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text):
        data = f.readAll().data().decode("utf-8")
        f.close()
        return data
    return ""


def detectSystemTheme() -> str:
    """检测 Windows 系统当前的颜色主题

    通过读取注册表 AppsUseLightTheme 键值判断系统是深色还是浅色模式。

    Returns:
        "dark" 或 "light"
    """
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return "light" if value else "dark"
    except Exception:
        return "dark"


def resolveTheme(theme: str) -> str:
    """将主题设置值解析为实际主题名称

    Args:
        theme: "system"、"dark" 或 "light"

    Returns:
        "dark" 或 "light"
    """
    if theme == "system":
        return detectSystemTheme()
    return theme if theme in ("dark", "light") else "dark"


def applyTheme(app: QApplication, theme: str):
    """合并 base.qss + 主题 qss 并应用到 QApplication

    链接颜色从 QSS 中 QLabel#aboutGithub 的 color 属性提取，
    通过 QPalette 设置，确保 QLabel 富文本 <a> 标签颜色正确显示。

    Args:
        app: QApplication 实例
        theme: 主题名称 ("dark" 或 "light")
    """
    base = _loadQss("base.qss")
    themeQss = _loadQss(f"{theme}.qss")
    combined = base + "\n\n" + themeQss
    app.setStyleSheet(combined)

    # 从 QSS 中提取链接颜色并设置到 QPalette（QSS 无法直接控制 <a> 标签颜色）
    palette = app.palette()
    match = _RE_LINK_COLOR.search(themeQss)
    if match:
        linkColor = QColor(match.group(1))
        palette.setColor(QPalette.ColorRole.Link, linkColor)
        palette.setColor(QPalette.ColorRole.LinkVisited, linkColor)
    app.setPalette(palette)


def installTranslator(app: QApplication):
    """从 Qt 资源系统加载并安装翻译文件

    Args:
        app: QApplication 实例

    Returns:
        QTranslator: 翻译器实例（需保持引用以防被回收）
    """
    translator = QTranslator()
    if translator.load(QLocale(), "hawkinghand", "_", ":/translations", ".qm"):
        app.installTranslator(translator)
    return translator
