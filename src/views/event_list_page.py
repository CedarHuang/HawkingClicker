"""
事件列表页
==========
展示所有已配置的事件卡片列表，支持添加、空状态显示、
卡片启用/禁用切换、右键菜单操作、删除确认等 UI 交互。
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QSpacerItem, QSizePolicy, QMessageBox,
)
from PySide6.QtCore import Signal

from ui.generated.ui_event_list_page import Ui_EventListPage
from views.event_card import EventCard


class EventListPage(QWidget):
    """事件列表页面"""

    # 信号定义
    addEventRequested = Signal()          # 请求添加新事件
    editEventRequested = Signal(int)      # 请求编辑事件（传递索引）
    deleteEventRequested = Signal(int)    # 请求删除事件（传递索引）
    copyEventRequested = Signal(int)      # 请求复制事件（传递索引）
    moveEventRequested = Signal(int, int) # 请求移动事件（原索引, 目标索引）
    statusToggled = Signal(int, bool)     # 事件启用/禁用切换（索引, 状态）

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.ui = Ui_EventListPage()
        self.ui.setupUi(self)

        # 卡片列表引用
        self._cards: list[EventCard] = []
        # 底部弹性空间
        self._bottomSpacer: QSpacerItem | None = None

        # 连接按钮信号
        self.ui.btnAddEvent.clicked.connect(self.addEventRequested.emit)
        self.ui.btnAddFirstEvent.clicked.connect(self.addEventRequested.emit)

        # 初始化为空状态
        self._updateEmptyState()

    # ---- 公共方法 ----

    def clearCards(self):
        """清空所有事件卡片"""
        for card in self._cards:
            self.ui.eventListLayout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()

        # 移除底部弹性空间
        if self._bottomSpacer is not None:
            self.ui.eventListLayout.removeItem(self._bottomSpacer)
            self._bottomSpacer = None

        self._updateEmptyState()

    def addCard(self, eventType: str, hotkey: str, button: str,
                scope: str, extra: str = "", enabled: bool = True) -> EventCard:
        """添加一张事件卡片

        Returns:
            创建的 EventCard 实例
        """
        card = EventCard(self)
        card.setEventData(eventType, hotkey, button, scope, extra, enabled)

        index = len(self._cards)
        self._cards.append(card)

        # 移除底部弹性空间（稍后重新添加）
        if self._bottomSpacer is not None:
            self.ui.eventListLayout.removeItem(self._bottomSpacer)

        # 添加卡片到布局
        self.ui.eventListLayout.addWidget(card)

        # 重新添加底部弹性空间
        self._bottomSpacer = QSpacerItem(
            0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding
        )
        self.ui.eventListLayout.addItem(self._bottomSpacer)

        # 连接卡片信号
        card.clicked.connect(lambda idx=index: self.editEventRequested.emit(idx))
        card.editRequested.connect(lambda idx=index: self.editEventRequested.emit(idx))
        card.copyRequested.connect(lambda idx=index: self.copyEventRequested.emit(idx))
        card.deleteRequested.connect(lambda idx=index: self._confirmDelete(idx))
        card.moveUpRequested.connect(lambda idx=index: self._moveUp(idx))
        card.moveDownRequested.connect(lambda idx=index: self._moveDown(idx))
        card.statusToggled.connect(lambda checked, idx=index: self.statusToggled.emit(idx, checked))

        self._updateEmptyState()
        return card

    def cardCount(self) -> int:
        """返回当前卡片数量"""
        return len(self._cards)

    # ---- 内部方法 ----

    def _updateEmptyState(self):
        """根据卡片数量切换空状态/列表视图"""
        hasCards = len(self._cards) > 0
        self.ui.scrollArea.setVisible(hasCards)
        self.ui.emptyState.setVisible(not hasCards)

    def _confirmDelete(self, index: int):
        """弹出删除确认对话框"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除这个事件配置吗？\n此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.deleteEventRequested.emit(index)

    def _moveUp(self, index: int):
        """请求上移事件"""
        if index > 0:
            self.moveEventRequested.emit(index, index - 1)

    def _moveDown(self, index: int):
        """请求下移事件"""
        if index < len(self._cards) - 1:
            self.moveEventRequested.emit(index, index + 1)
