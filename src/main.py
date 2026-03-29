"""
HawkingClicker — 主入口
========================
启动应用主窗口。

运行方式:
    cd src
    python main.py
"""

import sys
from pathlib import Path

from PySide6.QtCore import QTranslator, QLocale
from PySide6.QtWidgets import QApplication

from __version__ import __version__
from core import event_listener
from core import foreground_listener
from core import single_instance
from views.main_window import MainWindow, applyTheme


def _installTranslator(app: QApplication):
    translator = QTranslator()
    trDir = str(Path(__file__).parent / "translations" / "generated")
    if translator.load(QLocale(), "hawkingclicker", "_", trDir, ".qm"):
        app.installTranslator(translator)
    return translator


def main():
    app = QApplication(sys.argv)

    # 单实例检查：若已有实例运行则唤醒并退出
    if not single_instance.check():
        sys.exit(0)

    # 加载翻译
    _translator = _installTranslator(app)

    # 应用深色主题
    applyTheme(app, "dark")

    # 创建主窗口
    window = MainWindow()
    window.setVersion(f"v{__version__}")

    # 注册 core 层回调
    window.registerCallbacks()

    # 加载数据到 UI
    window.refreshEventList()
    window.initSettings()

    # 初始化系统托盘
    window.initTray()

    # 启动后台监听
    foreground_listener.start()
    event_listener.start()

    # 显示窗口
    window.show()

    # 进入事件循环
    exitCode = app.exec()

    # 退出时清理
    event_listener.stop()
    foreground_listener.stop()
    window.cleanupTray()

    sys.exit(exitCode)


if __name__ == "__main__":
    main()
