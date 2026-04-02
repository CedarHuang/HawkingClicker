# nuitka-project: --product-name=HawkingHand
# nuitka-project: --file-description=HawkingHand
# nuitka-project: --company-name=CedarHuang
# nuitka-project: --copyright=Copyright (C) 2026 CedarHuang. Licensed under the Apache License 2.0.

# nuitka-project: --enable-plugin=pyside6
# nuitka-project: --output-dir=dist
# nuitka-project: --output-filename=HawkingHand
# nuitka-project: --standalone
# nuitka-project: --windows-console-mode=disable
# nuitka-project: --windows-icon-from-ico=src/resources/icons/icon.ico

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from __version__ import __version__
from core import event_listener
from core import foreground_listener
from core import single_instance
from core.config import settings as configSettings
from resources import resources_rc  # noqa: F401  注册 Qt 资源
from views.appearance import applyTheme, resolveTheme, installTranslator
from views.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setEffectEnabled(Qt.UIEffect.UI_AnimateCombo, False)

    # 单实例检查：若已有实例运行则唤醒并退出
    if not single_instance.check():
        sys.exit(0)

    # 加载翻译
    _translator = installTranslator(app, configSettings.language)

    # 根据配置应用主题
    applyTheme(app, resolveTheme(configSettings.theme))

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
