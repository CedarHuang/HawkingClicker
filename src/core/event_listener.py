import fnmatch
import keyboard
import sys
import threading

from core import input_backend
from core import config
from core import foreground_listener
from core.callbacks import callbacks, CallbackEvent
from core.scripts import scripts

def start():
    for event in config.events:
        if not event.enabled:
            continue
        if event.hotkey == None or event.hotkey == '':
            continue
        keyboard.add_hotkey(event.hotkey, callback_factory(event))

def stop():
    keyboard.unhook_all()
    foreground_listener.clear_event_callback_list()

special_scope = ['CHECK_WINDOW']

def callback_factory(event):
    parse_scope(event)
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
        if not check_scope(event):
            return
        input_backend.click(event.target, *event.position)

    return callback

def press_factory(event):
    already_down = False
    def callback():
        if not check_scope(event):
            return
        nonlocal already_down
        if not already_down:
            input_backend.down(event.target, *event.position)
            already_down = True
        else:
            input_backend.up(event.target, *event.position)
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
            input_backend.click(event.target, *event.position)
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
        if not check_scope(event):
            return
        if if_ing_then_stop():
            return
        threading.Thread(target=callback_impl).start()

    foreground_listener.add_event_callback_list(if_ing_then_stop)

    return callback

def script_factory(event):
    script, context = scripts.load_as_function(event)
    thread = None

    def if_ing_then_stop():
        if thread and thread.is_alive():
            context.set_stop()
            return True
        return False

    def callback():
        nonlocal thread
        if not check_scope(event):
            return
        if if_ing_then_stop():
            return
        thread = threading.Thread(target=script)
        thread.start()

    foreground_listener.add_event_callback_list(if_ing_then_stop)

    return callback

def check_window(event):
    def callback():
        event.params.position = list(foreground_listener.active_window_info()[:2])
        callbacks.trigger(CallbackEvent.LIST_REFRESH)

    return callback

def parse_scope(event):
    if event.scope in special_scope:
        event.type = event.scope
    _scope = []
    for i in event.scope.split(':', 1):
        i = i.strip()
        if i == '':
            i = '*'
        _scope.append(i)
    _scope.extend(['*'] * (2 - len(_scope)))
    event._scope = _scope
    event._version = 0
    event._passed = False

def check_scope(event):
    process_name, window_title, data_version = foreground_listener.active_window_info()
    if event._version == data_version:
        return event._passed

    e_p_name, e_w_title = event._scope
    process_name_passed = fnmatch.fnmatchcase(process_name, e_p_name)
    window_title_passed = fnmatch.fnmatchcase(window_title, e_w_title)
    passed = process_name_passed and window_title_passed

    event._version = data_version
    event._passed = passed

    return passed

