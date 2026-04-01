import keyboard
import pyautogui

# 鼠标按键内部标准值
MOUSE_LEFT = 'mouse_left'
MOUSE_RIGHT = 'mouse_right'

MOUSE_BUTTON = {
    MOUSE_LEFT: 'left',
    MOUSE_RIGHT: 'right',
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
