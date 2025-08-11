import ctypes
import ctypes.wintypes
import psutil
import pythoncom
import threading
import time
import win32con
from win32 import win32api, win32gui, win32process

# --- 全局变量和锁，用于存储当前活跃窗口信息 ---
active_window_info_lock = threading.Lock()
current_active_hwnd = 0
current_process_name = ""
current_window_title = ""
current_data_version = 0
event_callback_list = []

# --- 事件钩子回调函数 ---
def callback_impl(hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
    if event != win32con.EVENT_SYSTEM_FOREGROUND:
        return

    # 重新获取当前活跃窗口的句柄，解决Alt+Tab切换窗口时，收到不在预期内的explorer.exe事件以致结果被干扰的问题
    hwnd = win32gui.GetForegroundWindow()

    with active_window_info_lock:
        global current_active_hwnd, current_process_name, current_window_title, current_data_version, event_callback_list
        try:
            if hwnd == current_active_hwnd:
                return

            window_title = win32gui.GetWindowText(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            process_name = process.name()

            current_active_hwnd = hwnd
            current_process_name = process_name
            current_window_title = window_title
            current_data_version += 1
        except:
            current_active_hwnd = 0
            current_process_name = ""
            current_window_title = ""
            current_data_version += 1
        finally:
            for event_callback in event_callback_list:
                event_callback()

# 定义回调函数的类型
WINEVENTPROC = ctypes.WINFUNCTYPE(
    None,                   # 返回值类型 (void)
    ctypes.wintypes.HANDLE, # hWinEventHook
    ctypes.wintypes.DWORD,  # event
    ctypes.wintypes.HWND,   # hwnd
    ctypes.wintypes.LONG,   # idObject
    ctypes.wintypes.LONG,   # idChild
    ctypes.wintypes.DWORD,  # dwEventThread
    ctypes.wintypes.DWORD   # dwmsEventTime
)

# 将 Python 回调函数转换为 ctypes 可用的函数指针
callback_ptr = WINEVENTPROC(callback_impl)

# --- 事件监听启动/停止函数 ---
def listener_thread_func():
    # 设置钩子，使用 ctypes 调用的 SetWinEventHook
    hook_handle = ctypes.windll.user32.SetWinEventHook(
        win32con.EVENT_SYSTEM_FOREGROUND,
        win32con.EVENT_SYSTEM_FOREGROUND,
        0,
        callback_ptr, # 传入 ctypes 包装后的回调函数指针
        0,
        0,
        win32con.WINEVENT_OUTOFCONTEXT
    )

    # 阻塞直到收到 WM_QUIT 消息
    pythoncom.PumpMessages()

    if hook_handle:
        ctypes.windll.user32.UnhookWinEvent(hook_handle)

listener_thread = None # 用于存储事件监听线程

def start():
    global listener_thread
    if listener_thread and listener_thread.is_alive():
        return

    listener_thread = threading.Thread(target=listener_thread_func, daemon=True)
    listener_thread.start()

    # 给予一点时间让钩子和线程初始化
    time.sleep(0.1)
    # 启动时，立即获取当前活跃窗口信息
    callback_impl(None, win32con.EVENT_SYSTEM_FOREGROUND, 0, 0, 0, 0, 0)

def stop():
    global listener_thread
    if listener_thread is None or not listener_thread.is_alive():
        return

    # 发送 WM_QUIT 消息给监听线程的消息队列，使其 PumpMessages 退出
    win32api.PostThreadMessage(listener_thread.ident, win32con.WM_QUIT, 0, 0)
    listener_thread.join(timeout=0.1)
    listener_thread = None
