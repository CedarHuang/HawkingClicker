import functools
import inspect
import pyautogui
import threading
import win32api
import win32con

import button_op
import common
import foreground_listener
import logger

class ScriptExit(Exception):
    """自定义异常类，用于表示脚本的有意终止。

    当脚本通过 'exit()' 或 'quit()' 函数终止时，会抛出此异常。

    Attributes:
        message (str): 异常消息，默认为 "Script terminated."。
        code (int): 退出代码，默认为 0。
    """

    def __init__(self, message="Script terminated.", code=0):
        super().__init__(message)
        self.code = code

def _create_init(_=None):
    """为 Script 脚本环境生成init。

    :meta private: 内部使用。
    """
    init_flag = False

    def init():
        """检查是否为首次调用。

        这个函数设计为只在首次调用时返回 True，之后的所有调用都返回 False。
        适用于需要确保某个操作只执行一次的场景。

        Returns:
            bool: 首次调用返回 True，后续调用返回 False。
        """
        nonlocal init_flag
        if not init_flag:
            init_flag = True
            return True
        return False

    return init

_context_id_inc = 0
_global_cache = {}
_script_cache = {}
_global_cache_lock = threading.Lock()
_script_cache_lock = threading.Lock()

def _create_context(event):
    """为 Script 脚本环境生成API。

    :meta private: 内部使用。
    """

    ############################################################################
    functions = {}

    def register(name=None):
        """注册函数到上下文。

        :meta private: 内部使用。
        """
        def decorator(func):
            functions[name or func.__name__] = func
            return func
        return decorator

    ############################################################################
    global _context_id_inc
    _context_id_inc += 1
    _context_id = _context_id_inc

    @register()
    def context_id():
        """获取当前上下文的唯一标识符。

        Returns:
            int: 当前上下文的唯一标识符。
        """
        return _context_id

    ############################################################################
    stop_event = threading.Event()

    @register()
    def sleep(ms):
        """暂停脚本执行指定的毫秒数。

        Args:
            ms (float | int): 暂停的毫秒数。
        """
        stop_event.wait(ms / 1000)
        if stop_event.is_set():
            exit()

    @register()
    def set_stop():
        """设置停止事件标志。

        :meta private: 内部使用。
        """
        stop_event.set()

    @register()
    def clear_stop():
        """清除停止事件标志。

        :meta private: 内部使用。
        """
        stop_event.clear()

    ############################################################################
    delay_time = 100
    delay_flag = False

    def delay(func):
        """延迟装饰器，在函数调用后添加延迟。

        :meta private: 内部使用。
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal delay_flag
            if delay_flag:
                sleep(delay_time)
            delay_flag = True
            result = func(*args, **kwargs)
            sleep(delay_time)
            return result
        return wrapper

    @register()
    def clear_delay_flag():
        """清除延迟标记。

        :meta private: 内部使用。
        """
        nonlocal delay_flag
        delay_flag = False

    @register('get_pause')
    @register()
    def get_delay():
        """获取鼠标操作调用之后的延迟时间。

        Returns:
            float | int: 当前的延迟时间（毫秒）。
        """
        return delay_time

    @register('set_pause')
    @register()
    def set_delay(ms):
        """设置鼠标操作调用之后的延迟时间。

        Args:
            ms (float | int): 延迟的毫秒数。
        """
        nonlocal delay_time
        delay_time = ms

    ############################################################################

    @register()
    def get_global_cache(key, default=None):
        """获取全局缓存中的值。

        这个字典在所有脚本的不同上下文中共享，可以用于存储跨脚本的数据。

        Args:
            key: 要获取的值的键。
            default: 如果键不存在时返回的默认值。默认为 None。

        Returns:
            any: 全局缓存字典中的值，如果键不存在则返回默认值。
        """
        with _global_cache_lock:
            return _global_cache.get(key, default)

    @register()
    def set_global_cache(key, value):
        """设置全局缓存中的值。

        这个字典在所有脚本的不同上下文中共享，可以用于存储跨脚本的数据。

        Args:
            key: 要设置的值的键。
            value: 要设置的值。

        Returns:
            any: 设置的值。
        """
        with _global_cache_lock:
            _global_cache[key] = value
            return value

    def _cur_script_cache():
        """获取当前脚本的缓存字典。
        
        这个字典在同一脚本的不同上下文中共享，但在不同脚本之间不共享。
        可以用于存储同一脚本的不同运行实例之间的数据。
        
        :meta private: 内部使用。
        """
        script_name = event.button
        if script_name not in _script_cache:
            _script_cache[script_name] = {}
        return _script_cache[script_name]

    @register()
    def get_script_cache(key, default=None):
        """获取脚本缓存中的值。

        这个字典在同一脚本的不同上下文中共享，但在不同脚本之间不共享。
        可以用于存储同一脚本的不同运行实例之间的数据。

        Args:
            key: 要获取的值的键。
            default: 如果键不存在时返回的默认值。默认为 None。

        Returns:
            any: 脚本缓存字典中的值，如果键不存在则返回默认值。
        """
        with _script_cache_lock:
            return _cur_script_cache().get(key, default)

    @register()
    def set_script_cache(key, value):
        """设置脚本缓存中的值。

        这个字典在同一脚本的不同上下文中共享，但在不同脚本之间不共享。
        可以用于存储同一脚本的不同运行实例之间的数据。

        Args:
            key: 要设置的值的键。
            value: 要设置的值。

        Returns:
            any: 设置的值。
        """
        with _script_cache_lock:
            _cur_script_cache()[key] = value
            return value

    ############################################################################

    @register('init')
    @_create_init
    def _():
        ...

    @register('print')
    def _(*args, **kwargs):
        sep = kwargs.get('sep', ' ')
        end = kwargs.get('end', '\n')
        message = sep.join(map(str, args)) + end.rstrip('\n')
        logger.script.info(message)

    @register('quit')
    @register()
    def exit(code=0):
        """终止当前脚本的执行。

        此函数通过抛出 'ScriptExit' 异常来实现终止。

        Args:
            code (int, optional): 脚本的退出代码。默认为 0。

        Raises:
            ScriptExit: 始终抛出此异常以终止脚本。
        """
        raise ScriptExit(f"Script exited with code {code}", code)

    @register()
    def event_hotkey():
        """获取当前事件的热键。

        Returns:
            str: 当前事件的热键。
        """
        return event.hotkey

    @register()
    def foreground():
        """获取当前处于前台（活动）窗口的进程名称和窗口标题。

        Returns:
            tuple[str, str]: 包含两个字符串的元组。
                - process_name (str): 当前前台应用程序的进程名称。
                - window_title (str): 当前前台窗口的标题。
        """
        process_name, window_title, _ = foreground_listener.active_window_info()
        return process_name, window_title

    @register()
    def position(x=-1, y=-1):
        """获取鼠标的当前位置。

        如果提供了有效的 x 和 y 坐标（大于等于 0），则直接返回这些坐标。
        如果 x 与 y 为 -1，则获取当前鼠标位置的对应坐标。

        Args:
            x (int, optional): X坐标。如果为 -1，则使用当前鼠标的X坐标。默认为 -1。
            y (int, optional): Y坐标。如果为 -1，则使用当前鼠标的Y坐标。默认为 -1。

        Returns:
            tuple[int, int]: 鼠标的坐标 (x, y)。
        """
        return button_op.position(x, y)

    @register()
    @delay
    def click(button, x=-1, y=-1):
        """模拟鼠标或键盘按键的点击操作。

        Args:
            button (str): 要点击的按钮或按键的名称。
            x (int, optional): 鼠标点击的X坐标。仅当 'button' 为鼠标按钮时有效。
                默认为 -1（表示当前鼠标X坐标）。
            y (int, optional): 鼠标点击的Y坐标。仅当 'button' 为鼠标按钮时有效。
                默认为 -1（表示当前鼠标Y坐标）。
        """
        button_op.click(button, x, y)

    @register('press')
    @register()
    @delay
    def down(button, x=-1, y=-1):
        """模拟鼠标或键盘按键的按下操作（不释放）。

        Args:
            button (str): 要按下的按钮或按键的名称。
            x (int, optional): 鼠标按下的X坐标。仅当 'button' 为鼠标按钮时有效。
                默认为 -1（表示当前鼠标X坐标）。
            y (int, optional): 鼠标按下的Y坐标。仅当 'button' 为鼠标按钮时有效。
                默认为 -1（表示当前鼠标Y坐标）。
        """
        button_op.down(button, x, y)

    @register('release')
    @register()
    @delay
    def up(button, x=-1, y=-1):
        """模拟鼠标或键盘按键的释放操作。

        Args:
            button (str): 要释放的按钮或按键的名称。
                如果 'button' 在 MOUSE_BUTTON 中，则执行鼠标释放。
                否则，视为键盘按键。
            x (int, optional): 鼠标释放的X坐标。仅当 'button' 为鼠标按钮时有效。
                默认为 -1（表示当前鼠标X坐标）。
            y (int, optional): 鼠标释放的Y坐标。仅当 'button' 为鼠标按钮时有效。
                默认为 -1（表示当前鼠标Y坐标）。
        """
        button_op.up(button, x, y)

    @register()
    @delay
    def move(x_offset, y_offset):
        """相对当前鼠标位置移动鼠标。

        Args:
            x_offset (int): X轴方向的偏移量。正值向右，负值向左。
            y_offset (int): Y轴方向的偏移量。正值向下，负值向上。
        """
        pyautogui.move(x_offset, y_offset, _pause=False)

    @register()
    @delay
    def move_to(x, y):
        """将鼠标移动到屏幕上的指定绝对坐标。

        Args:
            x (int): 目标X坐标。
            y (int): 目标Y坐标。
        """
        pyautogui.moveTo(x, y, _pause=False)

    @register()
    def is_caps_lock_on():
        """检查 Caps Lock 是否开启。

        Returns:
            int: 如果 Caps Lock 开启则返回 1，否则返回 0。
        """
        return win32api.GetKeyState(win32con.VK_CAPITAL)

    ############################################################################
    return functions

def _generate_builtins():
    lines = [
    '"""',
    '自动生成的 __builtins__.py 文件',
    '为 IDE 提供代码补全和类型提示',
    '"""',
    '',
    'from builtins import *',
    '',
    ]

    context = _create_context(None)
    for name, func in context.items():
        if name.startswith('_'):
            continue

        sig = inspect.signature(func)
        doc = inspect.getdoc(func)

        lines.append(f'def {name}{sig}:')
        lines.append(f'    """{doc}\n"""'.replace('\n', '\n    '))
        lines.append('    ...\n')

    with open(common.builtins_path(), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

_generate_builtins()