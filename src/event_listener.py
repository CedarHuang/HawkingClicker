import fnmatch
import keyboard
import sys
import threading

import api
import config
import foreground_listener
import list_view
from scripts import scripts

def start():
    for event in config.events:
        if event.status != 'Enable':
            continue
        if event.hotkey == None or event.hotkey == '':
            continue
        keyboard.add_hotkey(event.hotkey, callback_factory(event))

def stop():
    keyboard.unhook_all()
    foreground_listener.clear_event_callback_list()

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
        case 'Script':
            return script_factory(event)
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

    def if_ing_then_stop():
        nonlocal ing, stop
        if ing:
            stop.set()
        return ing

    def callback():
        if not check_range(event):
            return
        if if_ing_then_stop():
            return
        threading.Thread(target=callback_impl).start()

    foreground_listener.add_event_callback_list(if_ing_then_stop)

    return callback

def script_factory(event):
    script, context = scripts.load_as_function(event.button)
    thread = None

    def if_ing_then_stop():
        if thread and thread.is_alive():
            context.set_stop()
            return True
        return False

    def callback():
        nonlocal thread
        if not check_range(event):
            return
        if if_ing_then_stop():
            return
        thread = threading.Thread(target=script)
        thread.start()

    foreground_listener.add_event_callback_list(if_ing_then_stop)

    return callback

def check_window(event):
    def callback():
        event.position = api.foreground()
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
    process_name, window_title, data_version = foreground_listener.active_window_info()
    if event._version == data_version:
        return event._passed

    e_p_name, e_w_title = event._range
    process_name_passed = fnmatch.fnmatchcase(process_name, e_p_name)
    window_title_passed = fnmatch.fnmatchcase(window_title, e_w_title)
    passed = process_name_passed and window_title_passed

    event._version = data_version
    event._passed = passed

    return passed

def get_mouse_position(event):
    return api.position(*event.position)

def button_click(event):
    return api.click(event.button, *event.position)

def button_down(event):
    return api.down(event.button, *event.position)

def button_up(event):
    return api.up(event.button, *event.position)
