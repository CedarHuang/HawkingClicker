"""
设置业务控制器
=============
管理设置页的业务逻辑：主题切换、托盘开关、自启开关、管理员开关、打开目录等。
"""

import os

from PySide6.QtWidgets import QApplication

from core import common
from core.config import settings as configSettings
from views.appearance import applyTheme, resolveTheme
from views.settings_page import SettingsPage


# 需要重启才能生效的提示消息框
def _showRestartHint(parent):
    """显示需要重启的提示"""
    from PySide6.QtWidgets import QMessageBox
    QMessageBox.information(
        parent,
        QApplication.translate("SettingsController", "Restart required"),
        QApplication.translate("SettingsController",
                               "Language change will take effect after restart."),
    )


class SettingsController:
    """设置业务控制器

    Args:
        settingsPage: 设置页实例
    """

    def __init__(self, settingsPage: SettingsPage):
        self._settingsPage = settingsPage

        # 连接信号
        self._settingsPage.themeChanged.connect(self.onThemeChanged)
        self._settingsPage.languageChanged.connect(self._onLanguageChanged)
        self._settingsPage.trayToggled.connect(self.onTrayToggled)
        self._settingsPage.startupToggled.connect(self.onStartupToggled)
        self._settingsPage.adminToggled.connect(self.onAdminToggled)
        self._settingsPage.openConfigDirRequested.connect(self.onOpenConfigDir)
        self._settingsPage.openScriptsDirRequested.connect(self.onOpenScriptsDir)

    def initSettings(self):
        """初始化设置页：检测管理员权限并从配置加载真实设置值"""
        self._settingsPage.setAdminMode(common.is_running_as_admin())
        self._settingsPage.setSettings(
            tray=configSettings.enable_tray,
            startup=configSettings.startup,
            admin=configSettings.startup_as_admin,
            theme=configSettings.theme,
            language=configSettings.language,
        )

    @staticmethod
    def onThemeChanged(theme: str):
        """主题切换 → 保存到配置并立即应用"""
        configSettings.theme = theme
        configSettings.save()
        app = QApplication.instance()
        if app:
            applyTheme(app, resolveTheme(theme))

    def _onLanguageChanged(self, language: str):
        """语言切换 → 保存到配置并提示重启"""
        configSettings.language = language
        configSettings.save()
        _showRestartHint(self._settingsPage)

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
        os.startfile(common.config_path())

    @staticmethod
    def onOpenScriptsDir():
        """打开脚本目录"""
        os.startfile(common.scripts_path())
