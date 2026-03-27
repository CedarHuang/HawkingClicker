"""
主窗口
======
应用主窗口框架，包含无边框窗口、标题栏拖拽、
左侧可折叠导航栏、右侧内容区页面切换等 UI 交互。
"""

import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QButtonGroup, QApplication,
)
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QPoint,
    QObject, QEvent,
)

from ui.generated.ui_main_window import Ui_MainWindow
from views.event_list_page import EventListPage
from views.event_edit_page import EventEditPage
from views.settings_page import SettingsPage


# 路径常量
_UI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ui")
_STYLES_DIR = os.path.join(_UI_DIR, "styles")

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

    # 导航项配置：(objectName, 图标, 展开文字)
    NAV_ITEMS = {
        "navBtnEvents": ("📋", "📋 事件"),
        "navBtnSettings": ("⚙", "⚙ 设置"),
        "navBtnToggle": ("☰", "« 收起"),
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
        for name, (icon, expandedText) in self.NAV_ITEMS.items():
            btn = self._buttons.get(name)
            if btn:
                btn.setText(expandedText if self._expanded else icon)


# ============================================================
# 主窗口
# ============================================================

class MainWindow(QWidget):
    """应用主窗口"""

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
        self.ui.navBtnToggle.setToolTip("展开/折叠导航栏")

        # ---- 标题栏按钮 ----
        self.ui.btnMinimize.clicked.connect(self.showMinimized)
        self.ui.btnClose.clicked.connect(self.close)

        # ---- 子页面信号连接 ----
        # 事件列表页 → 添加按钮 → 跳转编辑页
        self.eventListPage.addEventRequested.connect(self._goToNewEvent)
        # 事件列表页 → 编辑事件 → 跳转编辑页
        self.eventListPage.editEventRequested.connect(self._goToEditEvent)
        # 事件编辑页 → 返回 → 回到列表页
        self.eventEditPage.backRequested.connect(self._goToEventList)
        # 事件编辑页 → 保存 → 回到列表页
        self.eventEditPage.saveRequested.connect(self._onEventSaved)

        # ---- 主题切换（隐藏功能：双击版本号） ----
        self._currentTheme = "dark"
        if self.ui.versionLabel:
            self.ui.versionLabel.setToolTip("双击切换主题")
            self._themeFilter = _DoubleClickFilter(
                self.ui.versionLabel, self._toggleTheme
            )

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
        self.eventEditPage.resetForm(isEditing=False)
        self.eventEditPage.setScriptList(["auto_farm", "auto_click", "my_script"])
        self.ui.contentStack.setCurrentIndex(1)

    def _goToEditEvent(self, index: int):
        """切换到编辑事件页（演示用，填充示例数据）"""
        self.eventEditPage.resetForm(isEditing=True)
        self.eventEditPage.setScriptList(["auto_farm", "auto_click", "my_script"])
        # 演示：填充一些示例数据
        self.eventEditPage.setFormData({
            "type": "Click",
            "hotkey": "Ctrl+F1",
            "button": "Left",
            "range": "*",
            "posX": -1,
            "posY": -1,
        })
        self.ui.contentStack.setCurrentIndex(1)

    def _onEventSaved(self, data: dict):
        """事件保存后回到列表页"""
        self._goToEventList()

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
