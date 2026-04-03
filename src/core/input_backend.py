import keyboard
import win32api
import win32con

MOUSE_LEFT = 'mouse_left'
MOUSE_RIGHT = 'mouse_right'

_MOUSE_FLAGS = {
    MOUSE_LEFT: (win32con.MOUSEEVENTF_LEFTDOWN, win32con.MOUSEEVENTF_LEFTUP),
    MOUSE_RIGHT: (win32con.MOUSEEVENTF_RIGHTDOWN, win32con.MOUSEEVENTF_RIGHTUP),
}
_DOWN, _UP = 0, 1

MOUSE_BUTTON = tuple(_MOUSE_FLAGS)

_CONST_DOCS = {
    'MOUSE_LEFT': '鼠标左键的标准值。\n\n用于 click()、down()、up() 等函数的 button 参数，表示鼠标左键。',
    'MOUSE_RIGHT': '鼠标右键的标准值。\n\n用于 click()、down()、up() 等函数的 button 参数，表示鼠标右键。',
    'MOUSE_BUTTON': '所有鼠标按键的集合。\n\n用于快速判断一个值是否为鼠标按键。',
}

def _resolve_button(button):
    button = button.lower()
    if button in _MOUSE_FLAGS:
        return True, button
    return False, button

def position(x=-1, y=-1):
    cx, cy = win32api.GetCursorPos()
    return (x if x >= 0 else cx, y if y >= 0 else cy)

def _mouse_event(button, action, x, y):
    if x >= 0 or y >= 0:
        win32api.SetCursorPos(position(x, y))
    win32api.mouse_event(_MOUSE_FLAGS[button][action], 0, 0, 0, 0)

def click(button, x=-1, y=-1):
    is_mouse, actual = _resolve_button(button)
    if is_mouse:
        _mouse_event(actual, _DOWN, x, y)
        _mouse_event(actual, _UP, x, y)
    else:
        keyboard.press_and_release(actual)

def down(button, x=-1, y=-1):
    is_mouse, actual = _resolve_button(button)
    if is_mouse:
        _mouse_event(actual, _DOWN, x, y)
    else:
        keyboard.press(actual)

def up(button, x=-1, y=-1):
    is_mouse, actual = _resolve_button(button)
    if is_mouse:
        _mouse_event(actual, _UP, x, y)
    else:
        keyboard.release(actual)

def move(x_offset, y_offset):
    cx, cy = win32api.GetCursorPos()
    win32api.SetCursorPos((cx + x_offset, cy + y_offset))

def move_to(x, y):
    win32api.SetCursorPos((x, y))
