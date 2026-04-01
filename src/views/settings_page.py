"""
设置页
======
管理应用全局设置（主题、系统托盘、开机自启、管理员启动），
提供快捷操作按钮和关于信息展示。
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal

from ui.generated.ui_settings_page import Ui_SettingsPage


class SettingsPage(QWidget):
    """设置页面"""

    # 信号定义
    themeChanged = Signal(str)            # 主题切换（配置值: system/light/dark）
    trayToggled = Signal(bool)            # 系统托盘开关切换
    startupToggled = Signal(bool)         # 开机自启开关切换
    adminToggled = Signal(bool)           # 管理员启动开关切换
    openConfigDirRequested = Signal()     # 请求打开配置目录
    openScriptsDirRequested = Signal()    # 请求打开脚本目录

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.ui = Ui_SettingsPage()
        self.ui.setupUi(self)

        # 是否以管理员身份运行（UI 演示默认为 False）
        self._isAdmin = False

        # ---- 初始化主题下拉框 ----
        self.ui.themeCombo.addItem(self.tr("Follow system"), "system")
        self.ui.themeCombo.addItem(self.tr("Light"), "light")
        self.ui.themeCombo.addItem(self.tr("Dark"), "dark")

        # ---- 连接信号 ----
        self.ui.themeCombo.currentIndexChanged.connect(self._onThemeChanged)
        self.ui.chkEnableTray.toggled.connect(self._onTrayToggled)
        self.ui.chkStartup.toggled.connect(self._onStartupToggled)
        self.ui.chkStartupAsAdmin.toggled.connect(self._onAdminToggled)
        self.ui.btnOpenConfigDir.clicked.connect(self.openConfigDirRequested.emit)
        self.ui.btnOpenScriptsDir.clicked.connect(self.openScriptsDirRequested.emit)

        # ---- 初始化联动状态 ----
        self._applyAdminState()
        self._updateStartupUI(self.ui.chkStartup.isChecked())

    # ---- 公共方法 ----

    def setAdminMode(self, isAdmin: bool):
        """设置当前是否以管理员身份运行

        Args:
            isAdmin: True=管理员, False=普通用户
        """
        self._isAdmin = isAdmin
        self._applyAdminState()
        self._updateStartupUI(self.ui.chkStartup.isChecked())

    def setVersionText(self, version: str):
        """设置关于区域的版本号显示

        Args:
            version: 版本号文本 (如 "v0.7.2")
        """
        self.ui.aboutAppName.setText(f"HawkingHand  {version}")

    def setSettings(self, tray: bool, startup: bool, admin: bool, theme: str = "system"):
        """批量设置开关状态（阻断信号避免触发回调）

        Args:
            tray: 系统托盘开关
            startup: 开机自启开关
            admin: 管理员启动开关
            theme: 主题设置 (system/light/dark)
        """
        self.ui.themeCombo.blockSignals(True)
        self.ui.chkEnableTray.blockSignals(True)
        self.ui.chkStartup.blockSignals(True)
        self.ui.chkStartupAsAdmin.blockSignals(True)

        # 设置主题下拉框
        themeIndex = self.ui.themeCombo.findData(theme)
        if themeIndex >= 0:
            self.ui.themeCombo.setCurrentIndex(themeIndex)

        self.ui.chkEnableTray.setChecked(tray)
        self.ui.chkStartup.setChecked(startup)
        self.ui.chkStartupAsAdmin.setChecked(admin)

        self.ui.themeCombo.blockSignals(False)
        self.ui.chkEnableTray.blockSignals(False)
        self.ui.chkStartup.blockSignals(False)
        self.ui.chkStartupAsAdmin.blockSignals(False)

        # 更新联动状态
        self._updateStartupUI(startup)

    # ---- 内部方法 ----

    def _onThemeChanged(self, index: int):
        """主题下拉框切换"""
        value = self.ui.themeCombo.itemData(index)
        if value:
            self.themeChanged.emit(value)

    def _onTrayToggled(self, checked: bool):
        """系统托盘开关切换"""
        self.trayToggled.emit(checked)

    def _updateStartupUI(self, checked: bool):
        """根据开机自启状态更新管理员启动开关的联动 UI"""
        if self.ui.chkStartupAsAdmin:
            # 开机自启未启用时，管理员启动置灰禁用
            self.ui.chkStartupAsAdmin.setEnabled(checked and self._isAdmin)
            if not checked:
                self.ui.chkStartupAsAdmin.blockSignals(True)
                self.ui.chkStartupAsAdmin.setChecked(False)
                self.ui.chkStartupAsAdmin.blockSignals(False)

    def _onStartupToggled(self, checked: bool):
        """开机自启切换时，联动管理员启动开关并发射信号"""
        self._updateStartupUI(checked)
        self.startupToggled.emit(checked)

    def _onAdminToggled(self, checked: bool):
        """管理员启动开关切换"""
        self.adminToggled.emit(checked)

    def _applyAdminState(self):
        """根据是否以管理员身份运行，设置管理员开关状态"""
        # 锁定图标：非管理员时显示
        if self.ui.adminLockIcon:
            self.ui.adminLockIcon.setVisible(not self._isAdmin)

        # 管理员开关：非管理员时禁用
        if self.ui.chkStartupAsAdmin:
            self.ui.chkStartupAsAdmin.setEnabled(self._isAdmin)
            if not self._isAdmin:
                self.ui.chkStartupAsAdmin.setToolTip(self.tr("Requires running as administrator"))
            else:
                self.ui.chkStartupAsAdmin.setToolTip("")
