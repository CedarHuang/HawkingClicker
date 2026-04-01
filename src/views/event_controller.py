"""
事件业务控制器
=============
管理事件的增删改查、数据转换、脚本扫描等业务逻辑。
将 UI 层的信号与 core 层的数据操作解耦。
"""

import copy
import glob
import os

from PySide6.QtWidgets import QStackedWidget, QPushButton

from core import common
from core.input_backend import MOUSE_LEFT, MOUSE_RIGHT
from core.config import events as configEvents
from core.models import Event
from views.event_edit_page import EventEditPage
from views.event_list_page import EventListPage

# 鼠标按钮内部值 → 显示名称映射
_MOUSE_BUTTON_DISPLAY = {
    MOUSE_LEFT: 'Left',
    MOUSE_RIGHT: 'Right',
}

def _displayButton(button: str) -> str:
    """将内部按钮值转换为用户友好的显示名称"""
    return _MOUSE_BUTTON_DISPLAY.get(button, button)


class EventController:
    """事件业务控制器

    Args:
        eventListPage: 事件列表页实例
        eventEditPage: 事件编辑页实例
        contentStack: 内容区 QStackedWidget
        navBtnEvents: 事件列表导航按钮
    """

    def __init__(self, eventListPage: EventListPage, eventEditPage: EventEditPage,
                 contentStack: QStackedWidget, navBtnEvents: QPushButton):
        self._eventListPage = eventListPage
        self._eventEditPage = eventEditPage
        self._contentStack = contentStack
        self._navBtnEvents = navBtnEvents
        self._editingIndex = -1  # 当前正在编辑的事件索引（-1 表示新建）

        # 连接信号
        self._eventListPage.addEventRequested.connect(self.goToNewEvent)
        self._eventListPage.editEventRequested.connect(self.goToEditEvent)
        self._eventListPage.deleteEventRequested.connect(self.onDeleteEvent)
        self._eventListPage.copyEventRequested.connect(self.onCopyEvent)
        self._eventListPage.moveEventRequested.connect(self.onMoveEvent)
        self._eventListPage.statusToggled.connect(self.onStatusToggled)
        self._eventEditPage.backRequested.connect(self.goToEventList)
        self._eventEditPage.saveRequested.connect(self.onEventSaved)

    # ---- 事件数据加载与刷新 ----

    def refreshEventList(self):
        """从 config.events 加载真实数据并刷新事件列表卡片"""
        self._eventListPage.clearCards()
        for event in configEvents:
            eventType, hotkey, button, scope, extra, enabled = self._eventToCardData(event)
            self._eventListPage.addCard(eventType, hotkey, button, scope, extra, enabled)

    @staticmethod
    def _eventToCardData(event: Event) -> tuple:
        """将 Event 对象转换为卡片显示所需的参数元组

        Returns:
            (eventType, hotkey, button, scope, extra, enabled)
        """
        eventType = event.type or "Click"
        hotkey = event.hotkey or ""
        button = _displayButton(event.button or "")
        scope = event.range or "*"
        enabled = event.isEnabled

        # 构建额外信息文本
        extraParts = []

        # 位置信息
        if event.posX != -1 or event.posY != -1:
            extraParts.append(f"位置: ({event.posX}, {event.posY})")

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

    def goToEventList(self):
        """切换到事件列表页"""
        self._contentStack.setCurrentIndex(0)
        self._navBtnEvents.setChecked(True)

    def goToNewEvent(self):
        """切换到新建事件编辑页"""
        self._editingIndex = -1
        self._eventEditPage.resetForm(isEditing=False)
        self._eventEditPage.setScriptList(self._scanScripts())
        self._contentStack.setCurrentIndex(1)

    def goToEditEvent(self, index: int):
        """切换到编辑事件页，加载真实事件数据"""
        if index < 0 or index >= len(configEvents):
            return
        self._editingIndex = index
        event = configEvents[index]

        self._eventEditPage.resetForm(isEditing=True)
        self._eventEditPage.setScriptList(self._scanScripts())

        # 将 Event 对象转换为表单数据字典
        formData = {
            "type": event.type or "Click",
            "hotkey": event.hotkey or "",
            "button": event.button or MOUSE_LEFT,
            "range": event.range or "*",
            "posX": event.posX,
            "posY": event.posY,
            "interval": event.interval if event.interval is not None else 100,
            "clicks": event.clicks if event.clicks is not None else -1,
        }

        if event.type == "Script":
            formData["script"] = event.button or ""

        self._eventEditPage.setFormData(formData)
        self._contentStack.setCurrentIndex(1)

    # ---- 事件保存 ----

    def onEventSaved(self, data: dict):
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
            event.button = data.get("button", MOUSE_LEFT)
            event.interval = data.get("interval", 100)
            event.clicks = data.get("clicks", -1)
        else:
            event.button = data.get("button", MOUSE_LEFT)
            event.interval = None
            event.clicks = None

        # 保存到配置
        configEvents.update(self._editingIndex, event)

        # 刷新列表并返回
        self.refreshEventList()
        self.goToEventList()

    # ---- 事件列表操作 ----

    def onDeleteEvent(self, index: int):
        """删除事件"""
        if 0 <= index < len(configEvents):
            configEvents.pop(index)
            self.refreshEventList()

    def onCopyEvent(self, index: int):
        """复制事件（深拷贝并追加到列表末尾）"""
        if 0 <= index < len(configEvents):
            newEvent = Event.from_dict(copy.deepcopy(configEvents[index].to_dict()))
            configEvents.append(newEvent)
            self.refreshEventList()

    def onMoveEvent(self, fromIndex: int, toIndex: int):
        """移动事件到目标位置"""
        if (0 <= fromIndex < len(configEvents) and
                0 <= toIndex < len(configEvents) and
                fromIndex != toIndex):
            configEvents.move(fromIndex, toIndex)
            self.refreshEventList()

    @staticmethod
    def onStatusToggled(index: int, enabled: bool):
        """切换事件启用/禁用状态"""
        if 0 <= index < len(configEvents):
            configEvents[index].status = 1 if enabled else 0
            configEvents.save()
