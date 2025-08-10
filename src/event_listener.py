import fnmatch
import keyboard
import pyautogui
import sys
import threading

import config
import foreground_listener
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

special_range = ['CHECK_WINDOW']

def callback_factory(event):
    parse_range(event)
    match event.type:
        case 'Click':
            return click_factory(event)
        case 'Press':
            return press_factory(event)
        case 'Multi':
            return multi_factory(event)
        case 'CHECK_WINDOW':
            return check_window(event)
        case _:
            return lambda: None

def click_factory(event):
    def callback():
        if not check_range(event):
            return
        button_click(event)

    return callback

def press_factory(event):
    already_down = False
    def callback():
        if not check_range(event):
            return
        nonlocal already_down
        if not already_down:
            button_down(event)
            already_down = True
        else:
            button_up(event)
            already_down = False

    return callback

def multi_factory(event):
    ing = False
    stop = threading.Event()
    def callback_impl():
        nonlocal ing, stop
        ing = True
        interval = event.interval / 1000
        clicks = event.clicks if event.clicks >= 0 else sys.maxsize
        count = 0
        while not stop.is_set():
            button_click(event)
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

def check_window(event):
    def callback():
        with foreground_listener.active_window_info_lock:
            process_name = foreground_listener.current_process_name
            window_title = foreground_listener.current_window_title
            event.position = (process_name, window_title)
        list_view.refresh()

    return callback

def parse_range(event):
    if event.range in special_range:
        event.type = event.range
    _range = []
    for i in event.range.split(':', 1):
        i = i.strip()
        if i == '':
            i = '*'
        _range.append(i)
    _range.extend(['*'] * (2 - len(_range)))
    event._range = _range
    event._version = 0
    event._passed = False

def check_range(event):
    with foreground_listener.active_window_info_lock:
        data_version = foreground_listener.current_data_version
        if event._version == data_version:
            return event._passed
        event._version = data_version

        process_name = foreground_listener.current_process_name
        window_title = foreground_listener.current_window_title

    e_p_name, e_w_title = event._range
    process_name_passed = fnmatch.fnmatchcase(process_name, e_p_name)
    window_title_passed = fnmatch.fnmatchcase(window_title, e_w_title)
    passed = process_name_passed and window_title_passed

    event._passed = passed
    return passed

def get_mouse_position(event):
    x, y = event.position
    if x >= 0 and y >= 0:
        return x, y
    nx, ny = pyautogui.position()
    if x < 0:
        x = nx
    if y < 0:
        y = ny
    return x, y

MOUSE_BUTTON = ('Left', 'Right')

def button_click(event):
    if event.button in MOUSE_BUTTON:
        x, y = get_mouse_position(event)
        pyautogui.mouseDown(x, y, button=event.button)
        pyautogui.mouseUp(x, y, button=event.button)
    else:
        keyboard.press_and_release(event.button)

def button_down(event):
    if event.button in MOUSE_BUTTON:
        pyautogui.mouseDown(button=event.button)
    else:
        keyboard.press(event.button)

def button_up(event):
    if event.button in MOUSE_BUTTON:
        pyautogui.mouseUp(button=event.button)
    else:
        keyboard.release(event.button)
