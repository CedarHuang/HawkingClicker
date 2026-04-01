"""
事件编辑页
==========
提供事件配置的创建/编辑表单，包含类型分段切换联动、
热键录入、字段动态显示/隐藏、表单验证等 UI 交互。
"""

import os

from PySide6.QtCore import Signal, Qt, QEvent, QObject, QCoreApplication
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QWidget, QButtonGroup, QMessageBox,
)

from core import common
from core.input_backend import MOUSE_LEFT, MOUSE_RIGHT
from ui.generated.ui_event_edit_page import Ui_EventEditPage
from views import _polishWidget


class HotkeyRecorder(QObject):
    """热键录入辅助类，捕获组合键并显示文本"""

    # 修饰键映射
    _MODIFIER_MAP = {
        Qt.Key_Control: "Ctrl",
        Qt.Key_Shift: "Shift",
        Qt.Key_Alt: "Alt",
        Qt.Key_Meta: "Win",
    }

    def __init__(self, lineEdit):
        super().__init__(lineEdit)
        self._lineEdit = lineEdit
        self._recording = False
        self._modifiers = []
        self._key = None

        # 安装事件过滤器
        lineEdit.installEventFilter(self)

    def eventFilter(self, obj, event):
        """拦截热键输入框的键盘事件"""
        if obj is not self._lineEdit:
            return False

        if event.type() == QEvent.Type.FocusIn:
            self._startRecording()
            return False

        if event.type() == QEvent.Type.FocusOut:
            self._stopRecording()
            return False

        if event.type() == QEvent.Type.KeyPress and self._recording:
            self._handleKeyPress(event)
            return True

        if event.type() == QEvent.Type.KeyRelease and self._recording:
            return True

        return False

    def _startRecording(self):
        """开始录入状态"""
        self._recording = True
        self._lineEdit.setPlaceholderText(QCoreApplication.translate("EventEditPage", "Press a key combination..."))
        self._lineEdit.setProperty("recording", True)
        _polishWidget(self._lineEdit)

    def _stopRecording(self):
        """停止录入状态"""
        self._recording = False
        self._lineEdit.setPlaceholderText(QCoreApplication.translate("EventEditPage", "Click here, then press a key combination..."))
        self._lineEdit.setProperty("recording", False)
        _polishWidget(self._lineEdit)

    def _handleKeyPress(self, event: QKeyEvent):
        """处理按键事件，组合修饰键+普通键"""
        key = event.key()

        # 如果是修饰键，暂不处理
        if key in self._MODIFIER_MAP:
            return

        # Escape 取消录入
        if key == Qt.Key_Escape:
            self._lineEdit.clearFocus()
            return

        # 构建组合键文本
        parts = []
        modifiers = event.modifiers()
        if modifiers & Qt.ControlModifier:
            parts.append("Ctrl")
        if modifiers & Qt.ShiftModifier:
            parts.append("Shift")
        if modifiers & Qt.AltModifier:
            parts.append("Alt")

        # 获取按键名称
        keyText = QKeyEvent.keyValueToText(key) if hasattr(QKeyEvent, 'keyValueToText') else ""
        if not keyText:
            from PySide6.QtCore import QKeyCombination
            seq = QKeyCombination(Qt.KeyboardModifier(0), Qt.Key(key))
            keyText = seq.toCombined().name if hasattr(seq, 'name') else str(key)

        # 使用 Qt 内置的键名映射
        keyName = _keyToString(key)
        if keyName:
            parts.append(keyName)

        if parts:
            self._lineEdit.setText("+".join(parts))

        self._lineEdit.clearFocus()


def _keyToString(key: int) -> str:
    """将 Qt Key 枚举转换为可读字符串"""
    # 常用功能键
    _KEY_NAMES = {
        Qt.Key_F1: "F1", Qt.Key_F2: "F2", Qt.Key_F3: "F3", Qt.Key_F4: "F4",
        Qt.Key_F5: "F5", Qt.Key_F6: "F6", Qt.Key_F7: "F7", Qt.Key_F8: "F8",
        Qt.Key_F9: "F9", Qt.Key_F10: "F10", Qt.Key_F11: "F11", Qt.Key_F12: "F12",
        Qt.Key_Space: "Space", Qt.Key_Return: "Enter", Qt.Key_Enter: "Enter",
        Qt.Key_Tab: "Tab", Qt.Key_Backspace: "Backspace", Qt.Key_Delete: "Delete",
        Qt.Key_Insert: "Insert", Qt.Key_Home: "Home", Qt.Key_End: "End",
        Qt.Key_PageUp: "PageUp", Qt.Key_PageDown: "PageDown",
        Qt.Key_Up: "Up", Qt.Key_Down: "Down", Qt.Key_Left: "Left", Qt.Key_Right: "Right",
        Qt.Key_CapsLock: "CapsLock", Qt.Key_NumLock: "NumLock",
        Qt.Key_ScrollLock: "ScrollLock", Qt.Key_Pause: "Pause",
        Qt.Key_Print: "PrintScreen",
    }

    if key in _KEY_NAMES:
        return _KEY_NAMES[key]

    # 字母键 A-Z
    if Qt.Key_A <= key <= Qt.Key_Z:
        return chr(key)

    # 数字键 0-9
    if Qt.Key_0 <= key <= Qt.Key_9:
        return chr(key)

    # 小键盘数字
    if Qt.Key_0 <= key - 0x01000000 + ord('0') <= Qt.Key_9:
        pass  # 不常用，跳过

    return ""


class EventEditPage(QWidget):
    """事件编辑页面"""

    # 信号定义
    backRequested = Signal()              # 请求返回列表页
    saveRequested = Signal(dict)          # 请求保存（传递表单数据字典）

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.ui = Ui_EventEditPage()
        self.ui.setupUi(self)

        # 当前编辑模式：True=编辑已有事件, False=新建事件
        self._isEditing = False
        # 表单是否有修改
        self._isDirty = False

        # ---- 类型分段按钮互斥组 ----
        self._typeGroup = QButtonGroup(self)
        self._typeGroup.setExclusive(True)
        self._typeGroup.addButton(self.ui.typeBtnClick)
        self._typeGroup.addButton(self.ui.typeBtnPress)
        self._typeGroup.addButton(self.ui.typeBtnMulti)
        self._typeGroup.addButton(self.ui.typeBtnScript)
        self._typeGroup.buttonClicked.connect(self._onTypeChanged)

        # 按钮 → 类型名称映射
        self._btnTypeMap = {
            self.ui.typeBtnClick: "Click",
            self.ui.typeBtnPress: "Press",
            self.ui.typeBtnMulti: "Multi",
            self.ui.typeBtnScript: "Script",
        }

        # ---- 热键录入 ----
        self._hotkeyRecorder = HotkeyRecorder(self.ui.hotkeyInput)

        # ---- 按钮信号 ----
        self.ui.btnBack.clicked.connect(self._onBackClicked)
        self.ui.btnCancel.clicked.connect(self._onBackClicked)
        self.ui.btnSave.clicked.connect(self._onSaveClicked)
        self.ui.btnOpenScriptsDir.clicked.connect(self._onOpenScriptsDir)

        # ---- 表单变更追踪 ----
        self.ui.hotkeyInput.textChanged.connect(self._markDirty)
        self.ui.rangeInput.textChanged.connect(self._markDirty)
        self.ui.buttonCombo.currentTextChanged.connect(self._markDirty)
        self.ui.scriptCombo.currentTextChanged.connect(self._markDirty)
        self.ui.positionX.valueChanged.connect(self._markDirty)
        self.ui.positionY.valueChanged.connect(self._markDirty)
        self.ui.intervalInput.valueChanged.connect(self._markDirty)
        self.ui.clicksInput.valueChanged.connect(self._markDirty)

        # ---- 为预设鼠标按钮选项设置内部值（不受翻译影响） ----
        self._initButtonComboData()

        # ---- 初始状态：Click 类型 ----
        self._applyType("Click")

    # ---- 公共方法 ----

    def resetForm(self, isEditing: bool = False):
        """重置表单为初始状态

        Args:
            isEditing: True=编辑模式, False=新建模式
        """
        self._isEditing = isEditing
        self._isDirty = False

        # 更新标题
        self.ui.pageTitle.setText(
            self.tr("Edit Event") if isEditing else self.tr("New Event")
        )

        # 重置所有字段
        self.ui.typeBtnClick.setChecked(True)
        self.ui.hotkeyInput.clear()
        self.ui.buttonCombo.setCurrentIndex(0)
        self.ui.rangeInput.clear()
        self.ui.positionX.setValue(-1)
        self.ui.positionY.setValue(-1)
        self.ui.intervalInput.setValue(100)
        self.ui.clicksInput.setValue(-1)

        # 清除错误提示样式
        self._clearErrors()

        # 应用类型联动
        self._applyType("Click")

    def setFormData(self, data: dict):
        """用数据填充表单

        Args:
            data: 包含 type, hotkey, target, range, posX, posY, interval, clicks 的字典
        """
        self._isEditing = True
        self.ui.pageTitle.setText(self.tr("Edit Event"))

        eventType = data.get("type", "Click")

        # 选中对应的类型按钮
        typeButtons = {
            "Click": self.ui.typeBtnClick,
            "Press": self.ui.typeBtnPress,
            "Multi": self.ui.typeBtnMulti,
            "Script": self.ui.typeBtnScript,
        }
        btn = typeButtons.get(eventType)
        if btn:
            btn.setChecked(True)
        self._applyType(eventType)

        # 填充字段
        self.ui.hotkeyInput.setText(data.get("hotkey", ""))
        self._setButtonComboValue(data.get("target", MOUSE_LEFT))

        # range 为 "*" 或空时显示为空，让 placeholder 提示用户格式
        rangeVal = data.get("range", "")
        self.ui.rangeInput.setText("" if rangeVal in ("", "*") else rangeVal)

        self.ui.positionX.setValue(data.get("posX", -1))
        self.ui.positionY.setValue(data.get("posY", -1))
        self.ui.intervalInput.setValue(data.get("interval", 100))
        self.ui.clicksInput.setValue(data.get("clicks", -1))

        # 如果是脚本类型，设置脚本选择
        if eventType == "Script":
            scriptName = data.get("script", "")
            idx = self.ui.scriptCombo.findText(scriptName)
            if idx >= 0:
                self.ui.scriptCombo.setCurrentIndex(idx)

        self._isDirty = False

    def setScriptList(self, scripts: list[str]):
        """设置脚本下拉列表

        Args:
            scripts: 脚本名称列表（不含 .py 后缀）
        """
        self.ui.scriptCombo.clear()
        self.ui.scriptCombo.addItems(scripts)

    # ---- 内部方法 ----

    def _onTypeChanged(self, button):
        """类型分段按钮切换回调"""
        typeName = self._btnTypeMap.get(button, "Click")
        self._applyType(typeName)
        self._markDirty()

    def _applyType(self, typeName: str):
        """根据类型名称显示/隐藏对应字段"""
        # Multi 类型显示连点配置
        self.ui.multiGroup.setVisible(typeName == "Multi")

        # Script 类型显示脚本选择，隐藏按键选择
        self.ui.scriptRow.setVisible(typeName == "Script")
        self.ui.buttonFieldLabel.setVisible(typeName != "Script")
        self.ui.buttonCombo.setVisible(typeName != "Script")

    def _onBackClicked(self):
        """返回/取消按钮点击"""
        if self._isDirty:
            reply = QMessageBox.question(
                self,
                self.tr("Discard Changes"),
                self.tr("Discard unsaved changes?"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return
        self.backRequested.emit()

    def _onSaveClicked(self):
        """保存按钮点击"""
        # 验证必填字段
        if not self._validate():
            return

        # 收集表单数据
        checkedBtn = self._typeGroup.checkedButton()
        typeName = self._btnTypeMap.get(checkedBtn, "Click")

        data = {
            "type": typeName,
            "hotkey": self.ui.hotkeyInput.text().strip(),
            "target": self._getButtonComboValue(),
            "range": self.ui.rangeInput.text().strip(),
            "posX": self.ui.positionX.value(),
            "posY": self.ui.positionY.value(),
            "interval": self.ui.intervalInput.value(),
            "clicks": self.ui.clicksInput.value(),
        }

        if typeName == "Script":
            data["script"] = self.ui.scriptCombo.currentText()

        self._isDirty = False
        self.saveRequested.emit(data)

    def _validate(self) -> bool:
        """验证必填字段，返回是否通过"""
        valid = True
        self._clearErrors()

        # 热键不能为空
        if not self.ui.hotkeyInput.text().strip():
            self.ui.hotkeyInput.setProperty("hasError", True)
            _polishWidget(self.ui.hotkeyInput)
            self.ui.hotkeyInput.setPlaceholderText(self.tr("⚠ Hotkey is required"))
            valid = False

        # 按键/脚本不能为空
        checkedBtn = self._typeGroup.checkedButton()
        typeName = self._btnTypeMap.get(checkedBtn, "Click")

        if typeName == "Script":
            if not self.ui.scriptCombo.currentText().strip():
                valid = False
        else:
            if not self.ui.buttonCombo.currentText().strip():
                self.ui.buttonCombo.setProperty("hasError", True)
                _polishWidget(self.ui.buttonCombo)
                valid = False

        return valid

    def _clearErrors(self):
        """清除所有字段的错误提示样式"""
        self.ui.hotkeyInput.setProperty("hasError", False)
        _polishWidget(self.ui.hotkeyInput)
        self.ui.hotkeyInput.setPlaceholderText(self.tr("Click here, then press a key combination..."))

        self.ui.buttonCombo.setProperty("hasError", False)
        _polishWidget(self.ui.buttonCombo)

    def _markDirty(self, *_args):
        """标记表单已修改"""
        self._isDirty = True

    def _initButtonComboData(self):
        """为 buttonCombo 的预设选项设置 itemData（内部值），使其不受翻译影响

        .ui 文件中定义的顺序：index 0 = Left, index 1 = Right
        显示文本会被 Qt 翻译系统翻译（如 "左键"/"右键"），
        但 itemData 始终保持英文内部值，供数据层使用。
        """
        _BUTTON_DATA = [MOUSE_LEFT, MOUSE_RIGHT]
        for i, value in enumerate(_BUTTON_DATA):
            if i < self.ui.buttonCombo.count():
                self.ui.buttonCombo.setItemData(i, value)

    def _getButtonComboValue(self) -> str:
        """获取 buttonCombo 的内部值（优先取 itemData，回退到 currentText）

        对于预设的鼠标按钮选项，返回不受翻译影响的内部值（如 "mouse_left"）；
        对于用户手动输入的键盘按键名，返回输入的文本。
        """
        data = self.ui.buttonCombo.currentData()
        if data is not None:
            return str(data)
        # 用户手动输入的键盘按键，无 itemData，直接返回文本
        return self.ui.buttonCombo.currentText().strip()

    def _setButtonComboValue(self, value: str):
        """根据内部值设置 buttonCombo 的选中项

        优先通过 itemData 匹配预设选项；若未找到，则作为自定义文本设置。
        """
        idx = self.ui.buttonCombo.findData(value)
        if idx >= 0:
            self.ui.buttonCombo.setCurrentIndex(idx)
        else:
            # 自定义键盘按键名，直接设置文本
            self.ui.buttonCombo.setCurrentText(value)

    @staticmethod
    def _onOpenScriptsDir():
        """打开脚本目录"""
        os.startfile(common.scripts_path())
