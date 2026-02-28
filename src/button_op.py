import keyboard
import pyautogui

MOUSE_BUTTON = ('Left', 'Right')

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
    if button in MOUSE_BUTTON:
        x, y = position(x, y)
        pyautogui.mouseDown(x, y, button=button)
        pyautogui.mouseUp(x, y, button=button)
    else:
        keyboard.press_and_release(button)

def down(button, x=-1, y=-1):
    if button in MOUSE_BUTTON:
        x, y = position(x, y)
        pyautogui.mouseDown(x, y, button=button)
    else:
        keyboard.press(button)

def up(button, x=-1, y=-1):
    if button in MOUSE_BUTTON:
        x, y = position(x, y)
        pyautogui.mouseUp(x, y, button=button)
    else:
        keyboard.release(button)
