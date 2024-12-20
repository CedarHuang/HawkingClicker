import fnmatch
import keyboard
import psutil
import pyautogui
import sys
import threading
from win32 import win32gui, win32process

import config
import list_view

def start():
    for event in config.events:
        if event.status != 'Enable':
            continue
        if event.hotkey == None or event.hotkey == '':
            continue
        keyboard.add_hotkey(event.hotkey, callback_factory(event))

def stop():
    keyboard.unhook_all()

def callback_factory(event):
    parse_range(event)
    match event.type:
        case 'Click':
            return click_factory(event)
        case 'Press':
            return press_factory(event)
        case 'Multi':
            return multi_factory(event)
        case _:
            return lambda: None

def click_factory(event):
    def callback():
        if not check_range(event):
            return
        x, y = get_position(event)
        pyautogui.click(x, y, button=event.button)

    return callback

def press_factory(event):
    mouse_down = False
    def callback():
        if not check_range(event):
            return
        nonlocal mouse_down
        if not mouse_down:
            pyautogui.mouseDown(button=event.button)
            mouse_down = True
        else:
            pyautogui.mouseUp(button=event.button)
            mouse_down = False

    return callback

def multi_factory(event):
    ing = False
    stop = threading.Event()
    def callback_impl():
        nonlocal ing, stop
        ing = True
        x, y = get_position(event)
        interval = event.interval / 1000
        clicks = event.clicks if event.clicks >= 0 else sys.maxsize
        count = 0
        while not stop.is_set():
            pyautogui.click(x, y, button=event.button)
            count += 1
            if count >= clicks:
                break
            stop.wait(interval)
        ing = False
        stop.clear()

    def callback():
        if not check_range(event):
            return
        nonlocal ing, stop
        if ing:
            stop.set()
            return
        threading.Thread(target=callback_impl).start()

    return callback

def parse_range(event):
    _range = []
    for i in event.range.split(':', 1):
        i = i.strip()
        if i == '':
            i = '*'
        _range.append(i)
    _range.extend(['*'] * (2 - len(_range)))
    event._range = _range

def check_range(event):
    e_p_name, e_w_title = event._range
    if e_p_name == '*' and e_w_title == '*':
        return True

    hwnd = win32gui.GetForegroundWindow()
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    process = psutil.Process(pid)
    process_name = process.name()
    title = win32gui.GetWindowText(hwnd)

    if e_p_name == 'CHECK_WINDOW':
        event.position = (process_name, title)
        list_view.refresh()
        return False

    if fnmatch.fnmatchcase(process_name, e_p_name) and fnmatch.fnmatchcase(title, e_w_title):
        return True

    return False

def get_position(event):
    x, y = event.position
    if x >= 0 and y >= 0:
        return x, y
    nx, ny = pyautogui.position()
    if x < 0:
        x = nx
    if y < 0:
        y = ny
    return x, y