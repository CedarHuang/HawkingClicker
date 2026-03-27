"""
HawkingClicker — 主入口
========================
启动应用主窗口，加载主题样式，填充示例数据用于 UI 展示。

运行方式:
    cd src
    python main.py
"""

import sys

from PySide6.QtWidgets import QApplication

from __version__ import __version__
from views.main_window import MainWindow, applyTheme


def _populateSampleEvents(window: MainWindow):
    """向事件列表中填充示例卡片数据，用于 UI 效果展示"""
    sampleEvents = [
        ("Click",  "Ctrl+F1",   "Left",          "*",               "位置: 当前"),
        ("Press",  "Ctrl+F2",   "Right",         "chrome.exe:*",    "位置: (100, 200)"),
        ("Multi",  "Ctrl+F3",   "Left",          "notepad.exe:*",   "频率: 50ms · 次数: 100"),
        ("Script", "Ctrl+F4",   "auto_farm.py",  "*",               ""),
        ("Click",  "Alt+1",     "Middle",        "game.exe:*",      "位置: (500, 300)"),
        ("Multi",  "Shift+F5",  "Right",         "*",               "频率: 200ms · 次数: ∞"),
    ]

    for eventType, hotkey, button, scope, extra in sampleEvents:
        window.eventListPage.addCard(eventType, hotkey, button, scope, extra)


def main():
    app = QApplication(sys.argv)

    # 应用深色主题
    applyTheme(app, "dark")

    # 创建主窗口
    window = MainWindow()
    window.setVersion(f"v{__version__}")

    # 设置页：勾选系统托盘以便预览
    window.settingsPage.setSettings(tray=True, startup=False, admin=False)

    # 填充示例事件数据
    _populateSampleEvents(window)

    # 显示窗口
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
