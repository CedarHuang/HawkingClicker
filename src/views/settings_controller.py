"""
设置业务控制器
=============
管理设置页的业务逻辑：托盘开关、自启开关、管理员开关、打开目录等。
"""

import os

from core import common
from core.config import settings as configSettings
from core.utils import is_running_as_admin


class SettingsController:
    """设置业务控制器

    Args:
        settingsPage: 设置页实例
    """

    def __init__(self, settingsPage):
        self._settingsPage = settingsPage

        # 连接信号
        self._settingsPage.trayToggled.connect(self.onTrayToggled)
        self._settingsPage.startupToggled.connect(self.onStartupToggled)
        self._settingsPage.adminToggled.connect(self.onAdminToggled)
        self._settingsPage.openConfigDirRequested.connect(self.onOpenConfigDir)
        self._settingsPage.openScriptsDirRequested.connect(self.onOpenScriptsDir)

    def initSettings(self):
        """初始化设置页：检测管理员权限并从配置加载真实设置值"""
        self._settingsPage.setAdminMode(is_running_as_admin())
        self._settingsPage.setSettings(
            tray=configSettings.enable_tray,
            startup=configSettings.startup,
            admin=configSettings.startup_as_admin,
        )

    @staticmethod
    def onTrayToggled(checked: bool):
        """系统托盘开关切换 → 保存到配置"""
        configSettings.enable_tray = checked
        configSettings.save()

    @staticmethod
    def onStartupToggled(checked: bool):
        """开机自启开关切换 → 保存到配置并更新注册表/计划任务"""
        configSettings.startup = checked
        if not checked:
            configSettings.startup_as_admin = False
        configSettings.save(update_startup=True)

    @staticmethod
    def onAdminToggled(checked: bool):
        """管理员启动开关切换 → 保存到配置并更新计划任务"""
        configSettings.startup_as_admin = checked
        configSettings.save(update_startup=True)

    @staticmethod
    def onOpenConfigDir():
        """打开配置目录"""
        configDir = common.config_path()
        common.mkdir_if_not_exists(configDir)
        os.startfile(configDir)

    @staticmethod
    def onOpenScriptsDir():
        """打开脚本目录"""
        scriptsDir = common.scripts_path()
        common.mkdir_if_not_exists(scriptsDir)
        os.startfile(scriptsDir)
