import keyboard
import pyautogui

MOUSE_LEFT = 'mouse_left'
MOUSE_RIGHT = 'mouse_right'

MOUSE_BUTTON = {
    MOUSE_LEFT: 'left',
    MOUSE_RIGHT: 'right',
}

_CONST_DOCS = {
    'MOUSE_LEFT': '鼠标左键的内部标准值。\n\n用于 click()、down()、up() 等函数的 button 参数，表示鼠标左键。',
    'MOUSE_RIGHT': '鼠标右键的内部标准值。\n\n用于 click()、down()、up() 等函数的 button 参数，表示鼠标右键。',
    'MOUSE_BUTTON': '鼠标按键映射字典。\n\n将内部标准值映射到底层库使用的按键名称。\n键为 MOUSE_LEFT / MOUSE_RIGHT，值为对应的底层按键名。',
}

def _resolve_button(button):
    button = button.lower()
    if button in MOUSE_BUTTON:
        return True, MOUSE_BUTTON[button]
    return False, button

def position(x=-1, y=-1):
    if x >= 0 and y >= 0:
        return x, y
    nx, ny = pyautogui.position()
    if x < 0:
        x = nx
    if y < 0:
        y = ny
    return x, y

def click(button, x=-1, y=-1):
    is_mouse, actual = _resolve_button(button)
    if is_mouse:
        x, y = position(x, y)
        pyautogui.mouseDown(x, y, button=actual, _pause=False)
        pyautogui.mouseUp(x, y, button=actual, _pause=False)
    else:
        keyboard.press_and_release(actual)

def down(button, x=-1, y=-1):
    is_mouse, actual = _resolve_button(button)
    if is_mouse:
        x, y = position(x, y)
        pyautogui.mouseDown(x, y, button=actual, _pause=False)
    else:
        keyboard.press(actual)

def up(button, x=-1, y=-1):
    is_mouse, actual = _resolve_button(button)
    if is_mouse:
        x, y = position(x, y)
        pyautogui.mouseUp(x, y, button=actual, _pause=False)
    else:
        keyboard.release(actual)
