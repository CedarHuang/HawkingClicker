import keyboard
import psutil
import pyautogui
import sys
import threading
from win32 import win32gui, win32process

import config
import list_view

def start():
    for item in config.items:
        if item.status != 'Enable':
            continue
        if item.hotkey == None or item.hotkey == '':
            continue
        keyboard.add_hotkey(item.hotkey, callback_factory(item))

def stop():
    keyboard.unhook_all()

def callback_factory(item):
    match item.type:
        case 'Click':
            return click_factory(item)
        case 'Press':
            return press_factory(item)
        case 'Multi':
            return multi_factory(item)
        case _:
            return lambda: None

def click_factory(item):
    def callback():
        if not check_range(item):
            return
        x, y = get_position(item)
        pyautogui.click(x, y, button=item.button)

    return callback

def press_factory(item):
    mouse_down = False
    def callback():
        nonlocal mouse_down
        if not check_range(item):
            return
        if not mouse_down:
            pyautogui.mouseDown(button=item.button)
            mouse_down = True
        else:
            pyautogui.mouseUp(button=item.button)
            mouse_down = False

    return callback

def multi_factory(item):
    ing = False
    stop = threading.Event()
    def callback():
        nonlocal ing, stop
        if ing:
            stop.set()
            return

        ing = True
        if not check_range(item):
            return
        x, y = get_position(item)
        interval = item.interval / 1000
        clicks = item.clicks if item.clicks >= 0 else sys.maxsize
        count = 0
        while not stop.is_set():
            pyautogui.click(x, y, button=item.button)
            count += 1
            if count >= clicks:
                break
            stop.wait(interval)
        ing = False
        stop.clear()

    return lambda: threading.Thread(target=callback).start()

def check_range(item):
    if item.range == 'GLOBAL':
        return True

    hwnd = win32gui.GetForegroundWindow()
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    process = psutil.Process(pid)
    process_name = process.name()

    if item.range == 'CHECK_WINDOW':
        title = win32gui.GetWindowText(hwnd)
        item.position = (process_name, title)
        list_view.refresh()

    if process_name == item.range:
        return True

    return False

def get_position(item):
    x, y = item.position
    if x >= 0 and y >= 0:
        return x, y
    nx, ny = pyautogui.position()
    if x < 0:
        x = nx
    if y < 0:
        y = ny
    return x, y