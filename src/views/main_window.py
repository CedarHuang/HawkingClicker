"""
主窗口
======
应用主窗口框架，包含无边框窗口、标题栏拖拽、
左侧可折叠导航栏、右侧内容区页面切换等 UI 交互。
"""

import copy
import glob
import os

from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QPoint,
    QObject, QEvent, QCoreApplication, Signal,
)
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QButtonGroup, QApplication,
    QSystemTrayIcon, QMenu,
)


from core import common
from core.callbacks import callbacks, CallbackEvent
from core.config import (
    events as configEvents,
    settings as configSettings,
    Event,
)
from core.utils import is_running_as_admin
from ui.generated.ui_main_window import Ui_MainWindow
from views.event_list_page import EventListPage
from views.event_edit_page import EventEditPage
from views.settings_page import SettingsPage


# 路径常量
_SRC_DIR = os.path.dirname(os.path.abspath(__file__)) + os.sep + ".."
_UI_DIR = os.path.join(_SRC_DIR, "ui")
_STYLES_DIR = os.path.join(_UI_DIR, "styles")
_ASSETS_DIR = os.path.normpath(os.path.join(_SRC_DIR, "..", "assets"))

# 导航栏尺寸常量
_NAV_COLLAPSED_WIDTH = 48
_NAV_EXPANDED_WIDTH = 160


# ============================================================
# 样式加载工具
# ============================================================

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


# ============================================================
# 标题栏拖拽支持
# ============================================================

class _TitleBarDragHelper(QObject):
    """为无边框窗口的标题栏提供拖拽移动支持"""

    def __init__(self, titleBar: QWidget, window: QWidget):
        super().__init__(titleBar)
        self._titleBar = titleBar
        self._window = window
        self._dragging = False
        self._dragStartPos = QPoint()
        titleBar.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj is not self._titleBar:
            return False

        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                self._dragging = True
                self._dragStartPos = (
                    event.globalPosition().toPoint()
                    - self._window.frameGeometry().topLeft()
                )
                return True

        elif event.type() == QEvent.Type.MouseMove:
            if self._dragging and event.buttons() & Qt.LeftButton:
                self._window.move(
                    event.globalPosition().toPoint() - self._dragStartPos
                )
                return True

        elif event.type() == QEvent.Type.MouseButtonRelease:
            self._dragging = False
            return True

        return False


# ============================================================
# 双击事件过滤器
# ============================================================

class _DoubleClickFilter(QObject):
    """通用双击事件过滤器"""

    def __init__(self, target: QWidget, callback):
        super().__init__(target)
        self._target = target
        self._callback = callback
        target.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj is self._target and event.type() == QEvent.Type.MouseButtonDblClick:
            self._callback()
            return True
        return False


# ============================================================
# 导航栏折叠/展开控制器
# ============================================================

class _NavBarController:
    """控制导航栏的折叠/展开动画和按钮文字切换"""

    # 导航项配置：(objectName, 图标, 展开文字翻译键)
    # NOTE: QCoreApplication.translate 调用让 lupdate 能正确提取翻译条目到 MainWindow 上下文
    # 模块加载时翻译器尚未安装，translate 返回原始英文字符串，作为翻译键使用
    NAV_ITEMS = {
        "navBtnEvents": ("📋", QCoreApplication.translate("MainWindow", "Events")),
        "navBtnSettings": ("⚙", QCoreApplication.translate("MainWindow", "Settings")),
        "navBtnToggle": ("☰", QCoreApplication.translate("MainWindow", "Collapse")),
    }

    def __init__(self, navBar: QWidget, mainWin: QWidget):
        self._navBar = navBar
        self._mainWin = mainWin
        self._expanded = False

        # 创建宽度动画（同时动画 min/max width）
        self._animMax = QPropertyAnimation(navBar, b"maximumWidth")
        self._animMax.setDuration(200)
        self._animMax.setEasingCurve(QEasingCurve.InOutCubic)

        self._animMin = QPropertyAnimation(navBar, b"minimumWidth")
        self._animMin.setDuration(200)
        self._animMin.setEasingCurve(QEasingCurve.InOutCubic)

        # 动画结束后更新按钮文字
        self._animMax.finished.connect(self._onAnimationFinished)

        # 缓存按钮引用
        self._buttons = {}
        for name in self.NAV_ITEMS:
            btn = mainWin.findChild(QWidget, name)
            if btn:
                self._buttons[name] = btn

        # 初始化为折叠态
        self._updateButtonTexts()

    @property
    def isExpanded(self) -> bool:
        return self._expanded

    def toggle(self):
        """切换折叠/展开状态"""
        if self._expanded:
            self._collapse()
        else:
            self._expand()

    def _expand(self):
        """展开导航栏"""
        self._animMax.stop()
        self._animMin.stop()

        currentWidth = self._navBar.width()
        self._animMax.setStartValue(currentWidth)
        self._animMax.setEndValue(_NAV_EXPANDED_WIDTH)
        self._animMin.setStartValue(currentWidth)
        self._animMin.setEndValue(_NAV_EXPANDED_WIDTH)

        # 展开前先更新文字
        self._expanded = True
        self._updateButtonTexts()

        self._animMax.start()
        self._animMin.start()

    def _collapse(self):
        """折叠导航栏"""
        self._animMax.stop()
        self._animMin.stop()

        currentWidth = self._navBar.width()
        self._animMax.setStartValue(currentWidth)
        self._animMax.setEndValue(_NAV_COLLAPSED_WIDTH)
        self._animMin.setStartValue(currentWidth)
        self._animMin.setEndValue(_NAV_COLLAPSED_WIDTH)

        self._expanded = False

        self._animMax.start()
        self._animMin.start()

    def _onAnimationFinished(self):
        """动画结束后更新按钮文字（折叠时在动画结束后切换为仅图标）"""
        if not self._expanded:
            self._updateButtonTexts()

    def _updateButtonTexts(self):
        """根据当前状态更新所有导航按钮的文字"""
        _tr = QCoreApplication.translate
        for name, (icon, textKey) in self.NAV_ITEMS.items():
            btn = self._buttons.get(name)
            if btn:
                translated = _tr("MainWindow", textKey)
                btn.setText(f"{icon} {translated}" if self._expanded else icon)


# ============================================================
# 主窗口
# ============================================================

class MainWindow(QWidget):
    """应用主窗口"""

    # 跨线程信号（子线程 emit → 主线程槽函数）
    _wakeupSignal = Signal()
    _trayUpdateSignal = Signal()

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        # ---- 设置 UI ----
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("HawkingClicker")

        # ---- 无边框窗口 ----
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        # ---- 标题栏拖拽 ----
        self._dragHelper = _TitleBarDragHelper(self.ui.titleBar, self)

        # ---- 创建子页面 ----
        self.eventListPage = EventListPage()
        self.eventEditPage = EventEditPage()
        self.settingsPage = SettingsPage()

        # ---- 将子页面嵌入 contentStack ----
        self._embedPage(0, self.eventListPage)
        self._embedPage(1, self.eventEditPage)
        self._embedPage(2, self.settingsPage)

        # ---- 导航栏控制 ----
        self._navController = _NavBarController(self.ui.navBar, self)

        # ---- 导航按钮互斥 + 页面切换 ----
        self._navGroup = QButtonGroup(self)
        self._navGroup.setExclusive(True)
        self._navGroup.addButton(self.ui.navBtnEvents, 0)
        self._navGroup.addButton(self.ui.navBtnSettings, 2)
        self._navGroup.idClicked.connect(self._onNavClicked)

        # ---- 导航栏展开/折叠按钮 ----
        self.ui.navBtnToggle.clicked.connect(self._navController.toggle)
        self.ui.navBtnToggle.setToolTip(self.tr("Toggle navigation bar"))

        # ---- 标题栏按钮 ----
        self.ui.btnMinimize.clicked.connect(self.showMinimized)
        self.ui.btnClose.clicked.connect(self.close)

        # ---- 子页面信号连接 ----
        # 事件列表页 → 添加按钮 → 跳转编辑页
        self.eventListPage.addEventRequested.connect(self._goToNewEvent)
        # 事件列表页 → 编辑事件 → 跳转编辑页
        self.eventListPage.editEventRequested.connect(self._goToEditEvent)
        # 事件列表页 → 删除事件
        self.eventListPage.deleteEventRequested.connect(self._onDeleteEvent)
        # 事件列表页 → 复制事件
        self.eventListPage.copyEventRequested.connect(self._onCopyEvent)
        # 事件列表页 → 移动事件
        self.eventListPage.moveEventRequested.connect(self._onMoveEvent)
        # 事件列表页 → 启用/禁用切换
        self.eventListPage.statusToggled.connect(self._onStatusToggled)
        # 事件编辑页 → 返回 → 回到列表页
        self.eventEditPage.backRequested.connect(self._goToEventList)
        # 事件编辑页 → 保存 → 回到列表页
        self.eventEditPage.saveRequested.connect(self._onEventSaved)

        # ---- 设置页信号连接 ----
        self.settingsPage.trayToggled.connect(self._onTrayToggled)
        self.settingsPage.startupToggled.connect(self._onStartupToggled)
        self.settingsPage.adminToggled.connect(self._onAdminToggled)
        self.settingsPage.openConfigDirRequested.connect(self._onOpenConfigDir)
        self.settingsPage.openScriptsDirRequested.connect(self._onOpenScriptsDir)

        # ---- 当前正在编辑的事件索引（-1 表示新建） ----
        self._editingIndex = -1

        # ---- 主题切换（隐藏功能：双击版本号） ----
        self._currentTheme = "dark"
        if self.ui.versionLabel:
            self.ui.versionLabel.setToolTip(self.tr("Double-click to switch theme"))
            self._themeFilter = _DoubleClickFilter(
                self.ui.versionLabel, self._toggleTheme
            )

        # ---- 跨线程信号 ----
        self._wakeupSignal.connect(self._onWakeup)
        self._trayUpdateSignal.connect(self._onTrayUpdate)

        # ---- 系统托盘 ----
        self._tray = self._createTrayIcon()

        # ---- 初始显示事件列表页 ----
        self.ui.contentStack.setCurrentIndex(0)

    # ---- 公共方法 ----

    def setVersion(self, version: str):
        """设置版本号显示

        Args:
            version: 版本号文本 (如 "v0.7.2")
        """
        self.ui.versionLabel.setText(version)
        self.settingsPage.setVersionText(version)

    def currentTheme(self) -> str:
        """返回当前主题名称"""
        return self._currentTheme

    def registerCallbacks(self):
        """注册 core 层回调"""
        callbacks.register(CallbackEvent.LIST_REFRESH, self.refreshEventList)
        callbacks.register(CallbackEvent.WAKEUP, self._wakeupSignal.emit)
        callbacks.register(CallbackEvent.TRAY_UPDATE, self._trayUpdateSignal.emit)

    def initSettings(self):
        """初始化设置页：检测管理员权限并从配置加载真实设置值"""
        self.settingsPage.setAdminMode(is_running_as_admin())
        self.settingsPage.setSettings(
            tray=configSettings.enable_tray,
            startup=configSettings.startup,
            admin=configSettings.startup_as_admin,
        )

    # ---- 事件数据加载与刷新 ----

    def refreshEventList(self):
        """从 config.events 加载真实数据并刷新事件列表卡片"""
        self.eventListPage.clearCards()
        for event in configEvents:
            eventType, hotkey, button, scope, extra, enabled = self._eventToCardData(event)
            self.eventListPage.addCard(eventType, hotkey, button, scope, extra, enabled)

    @staticmethod
    def _eventToCardData(event: Event) -> tuple:
        """将 Event 对象转换为卡片显示所需的参数元组

        Returns:
            (eventType, hotkey, button, scope, extra, enabled)
        """
        eventType = event.type or "Click"
        hotkey = event.hotkey or ""
        button = event.button or ""
        scope = event.range or "*"
        enabled = event.status == 1 if event.status is not None else True

        # 构建额外信息文本
        extraParts = []

        # 位置信息
        if event.position is not None and event.position != [-1, -1]:
            if isinstance(event.position, (list, tuple)) and len(event.position) == 2:
                x, y = event.position
                if x != -1 or y != -1:
                    extraParts.append(f"位置: ({x}, {y})")

        if not extraParts and eventType in ("Click", "Press"):
            extraParts.append("位置: 当前")

        # Multi 类型的频率和次数
        if eventType == "Multi":
            interval = event.interval if event.interval is not None else 100
            clicks = event.clicks if event.clicks is not None else -1
            extraParts.append(f"频率: {interval}ms")
            clicksText = "∞" if clicks == -1 else str(clicks)
            extraParts.append(f"次数: {clicksText}")

        extra = " · ".join(extraParts)
        return eventType, hotkey, button, scope, extra, enabled

    @staticmethod
    def _scanScripts() -> list[str]:
        """扫描 scripts 目录，返回脚本名称列表（不含 .py 后缀和 __builtins__）"""
        scriptsDir = common.scripts_path()
        if not os.path.isdir(scriptsDir):
            return []
        scripts = []
        for f in sorted(glob.glob(os.path.join(scriptsDir, "*.py"))):
            name = os.path.splitext(os.path.basename(f))[0]
            if name.startswith("__"):
                continue
            scripts.append(name)
        return scripts

    # ---- 页面导航 ----

    def _onNavClicked(self, btnId: int):
        """导航按钮点击，切换到对应页面"""
        self.ui.contentStack.setCurrentIndex(btnId)

    def _goToEventList(self):
        """切换到事件列表页"""
        self.ui.contentStack.setCurrentIndex(0)
        self.ui.navBtnEvents.setChecked(True)

    def _goToNewEvent(self):
        """切换到新建事件编辑页"""
        self._editingIndex = -1
        self.eventEditPage.resetForm(isEditing=False)
        self.eventEditPage.setScriptList(self._scanScripts())
        self.ui.contentStack.setCurrentIndex(1)

    def _goToEditEvent(self, index: int):
        """切换到编辑事件页，加载真实事件数据"""
        if index < 0 or index >= len(configEvents):
            return
        self._editingIndex = index
        event = configEvents[index]

        self.eventEditPage.resetForm(isEditing=True)
        self.eventEditPage.setScriptList(self._scanScripts())

        # 将 Event 对象转换为表单数据字典
        position = event.position if event.position else [-1, -1]
        posX = position[0] if isinstance(position, (list, tuple)) and len(position) >= 1 else -1
        posY = position[1] if isinstance(position, (list, tuple)) and len(position) >= 2 else -1

        formData = {
            "type": event.type or "Click",
            "hotkey": event.hotkey or "",
            "button": event.button or "Left",
            "range": event.range or "*",
            "posX": posX,
            "posY": posY,
            "interval": event.interval if event.interval is not None else 100,
            "clicks": event.clicks if event.clicks is not None else -1,
        }

        if event.type == "Script":
            formData["script"] = event.button or ""

        self.eventEditPage.setFormData(formData)
        self.ui.contentStack.setCurrentIndex(1)

    def _onEventSaved(self, data: dict):
        """事件保存：将表单数据写入 config.events 并刷新列表"""
        event = Event()
        event.type = data.get("type", "Click")
        event.hotkey = data.get("hotkey", "")

        # range 为空时默认为 "*"
        rangeVal = data.get("range", "").strip()
        event.range = rangeVal if rangeVal else "*"

        # 编辑已有事件时保留原有启用状态，新建事件默认启用
        if (0 <= self._editingIndex < len(configEvents)
                and configEvents[self._editingIndex].status is not None):
            event.status = configEvents[self._editingIndex].status
        else:
            event.status = 1

        posX = data.get("posX", -1)
        posY = data.get("posY", -1)
        event.position = [posX, posY]

        if event.type == "Script":
            event.button = data.get("script", "")
            event.interval = None
            event.clicks = None
        elif event.type == "Multi":
            event.button = data.get("button", "Left")
            event.interval = data.get("interval", 100)
            event.clicks = data.get("clicks", -1)
        else:
            event.button = data.get("button", "Left")
            event.interval = None
            event.clicks = None

        # 保存到配置
        configEvents.update(self._editingIndex, event)

        # 刷新列表并返回
        self.refreshEventList()
        self._goToEventList()

    # ---- 事件列表操作 ----

    def _onDeleteEvent(self, index: int):
        """删除事件"""
        if 0 <= index < len(configEvents):
            configEvents.pop(index)
            self.refreshEventList()

    def _onCopyEvent(self, index: int):
        """复制事件（深拷贝并追加到列表末尾）"""
        if 0 <= index < len(configEvents):
            newEvent = Event()
            newEvent.__dict__ = copy.deepcopy(configEvents[index].__dict__)
            configEvents.append(newEvent)
            self.refreshEventList()

    def _onMoveEvent(self, fromIndex: int, toIndex: int):
        """移动事件（交换位置）"""
        if (0 <= fromIndex < len(configEvents) and
                0 <= toIndex < len(configEvents)):
            configEvents.swap(fromIndex, toIndex)
            self.refreshEventList()

    def _onStatusToggled(self, index: int, enabled: bool):
        """切换事件启用/禁用状态"""
        if 0 <= index < len(configEvents):
            configEvents[index].status = 1 if enabled else 0
            configEvents.save()

    # ---- 设置操作 ----

    def _onTrayToggled(self, checked: bool):
        """系统托盘开关切换 → 保存到配置"""
        configSettings.enable_tray = checked
        configSettings.save()

    def _onStartupToggled(self, checked: bool):
        """开机自启开关切换 → 保存到配置并更新注册表/计划任务"""
        configSettings.startup = checked
        if not checked:
            configSettings.startup_as_admin = False
        configSettings.save(update_startup=True)

    def _onAdminToggled(self, checked: bool):
        """管理员启动开关切换 → 保存到配置并更新计划任务"""
        configSettings.startup_as_admin = checked
        configSettings.save(update_startup=True)

    @staticmethod
    def _onOpenConfigDir():
        """打开配置目录"""
        configDir = common.config_path()
        common.mkdir_if_not_exists(configDir)
        os.startfile(configDir)

    @staticmethod
    def _onOpenScriptsDir():
        """打开脚本目录"""
        scriptsDir = common.scripts_path()
        common.mkdir_if_not_exists(scriptsDir)
        os.startfile(scriptsDir)

    # ---- 窗口唤醒 ----

    def _onWakeup(self):
        """唤醒窗口：显示、置顶并激活（由跨线程信号触发，在主线程执行）"""
        self.showNormal()
        self.raise_()
        self.activateWindow()

    # ---- 系统托盘 ----

    def _createTrayIcon(self) -> QSystemTrayIcon:
        """创建系统托盘图标及右键菜单"""
        tray = QSystemTrayIcon(self)

        # 设置图标
        iconPath = os.path.join(_ASSETS_DIR, "icon.png")
        if os.path.exists(iconPath):
            tray.setIcon(QIcon(iconPath))
        else:
            tray.setIcon(self.style().standardIcon(
                self.style().StandardPixmap.SP_ComputerIcon
            ))
        tray.setToolTip("HawkingClicker")

        # 右键菜单
        menu = QMenu()
        actShow = QAction(self.tr("Show"), menu)
        actShow.triggered.connect(self._onWakeup)
        menu.addAction(actShow)

        menu.addSeparator()

        actQuit = QAction(self.tr("Quit"), menu)
        actQuit.triggered.connect(self._onTrayQuit)
        menu.addAction(actQuit)

        tray.setContextMenu(menu)

        # 双击托盘图标 → 显示主窗口
        tray.activated.connect(self._onTrayActivated)

        return tray

    def initTray(self):
        """根据配置初始化托盘显示状态"""
        if configSettings.enable_tray:
            self._tray.show()
        else:
            self._tray.hide()

    def cleanupTray(self):
        """退出时清理托盘图标"""
        self._tray.hide()

    def _onTrayUpdate(self):
        """TRAY_UPDATE 回调：根据配置更新托盘显示状态"""
        if configSettings.enable_tray:
            self._tray.show()
        else:
            self._tray.hide()

    def _onTrayActivated(self, reason):
        """托盘图标激活事件"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._onWakeup()

    def _onTrayQuit(self):
        """托盘菜单 → 退出应用"""
        self._tray.hide()
        QApplication.quit()

    def closeEvent(self, event):
        """重写关闭事件：托盘启用时最小化到托盘，否则正常关闭"""
        if configSettings.enable_tray and self._tray.isVisible():
            self.hide()
            event.ignore()
        else:
            event.accept()

    # ---- 主题切换 ----

    def _toggleTheme(self):
        """切换深色/浅色主题"""
        app = QApplication.instance()
        if app:
            self._currentTheme = "light" if self._currentTheme == "dark" else "dark"
            applyTheme(app, self._currentTheme)

    # ---- 内部方法 ----

    def _embedPage(self, index: int, page: QWidget):
        """将子页面嵌入 contentStack 的指定索引页"""
        container = self.ui.contentStack.widget(index)
        if container.layout() is None:
            container.setLayout(QVBoxLayout())
        container.layout().setContentsMargins(0, 0, 0, 0)
        container.layout().addWidget(page)
