"""
系统托盘管理
===========
管理系统托盘图标、右键菜单及托盘相关事件。
"""

import os

from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QWidget, QApplication, QSystemTrayIcon, QMenu

from core.config import settings as configSettings

# 路径常量
_ASSETS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets")
)


class TrayManager:
    """系统托盘管理器

    Args:
        window: 主窗口实例，用于显示/隐藏窗口和获取默认图标
        wakeupCallback: 唤醒窗口的回调函数
    """

    def __init__(self, window: QWidget, wakeupCallback):
        self._window = window
        self._wakeupCallback = wakeupCallback
        self._tray = self._createTrayIcon()

    def init(self):
        """根据配置初始化托盘显示状态"""
        if configSettings.enable_tray:
            self._tray.show()
        else:
            self._tray.hide()

    def cleanup(self):
        """退出时清理托盘图标"""
        self._tray.hide()

    def update(self):
        """根据配置更新托盘显示状态（TRAY_UPDATE 回调）"""
        if configSettings.enable_tray:
            self._tray.show()
        else:
            self._tray.hide()

    @property
    def isVisible(self) -> bool:
        """托盘图标是否可见"""
        return self._tray.isVisible()

    def shouldMinimizeToTray(self) -> bool:
        """判断关闭窗口时是否应最小化到托盘"""
        return configSettings.enable_tray and self._tray.isVisible()

    def _createTrayIcon(self) -> QSystemTrayIcon:
        """创建系统托盘图标及右键菜单"""
        tray = QSystemTrayIcon(self._window)

        # 设置图标
        iconPath = os.path.join(_ASSETS_DIR, "icon.png")
        if os.path.exists(iconPath):
            tray.setIcon(QIcon(iconPath))
        else:
            tray.setIcon(self._window.style().standardIcon(
                self._window.style().StandardPixmap.SP_ComputerIcon
            ))
        tray.setToolTip("HawkingClicker")

        # 右键菜单
        menu = QMenu()
        actShow = QAction(self._window.tr("Show"), menu)
        actShow.triggered.connect(self._wakeupCallback)
        menu.addAction(actShow)

        menu.addSeparator()

        actQuit = QAction(self._window.tr("Quit"), menu)
        actQuit.triggered.connect(self._onQuit)
        menu.addAction(actQuit)

        tray.setContextMenu(menu)

        # 双击托盘图标 → 显示主窗口
        tray.activated.connect(self._onActivated)

        return tray

    def _onActivated(self, reason):
        """托盘图标激活事件"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._wakeupCallback()

    @staticmethod
    def _onQuit():
        """托盘菜单 → 退出应用"""
        QApplication.quit()
