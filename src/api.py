import keyboard
import pyautogui

import foreground_listener

# MOUSE_BUTTON: 定义了有效的鼠标按键名称。
# 类型: tuple
MOUSE_BUTTON = ('Left', 'Right')

# create_init()
# 无需关注，为程序内部自动调用。
# 而 Script 脚本环境中会自动生成一个 'init' 函数。
#
# init()
# 这个函数设计为只在首次调用时返回 True，之后的所有调用都返回 False。
# 适用于需要确保某个操作只执行一次的场景。
#
# 参数: 无
# 返回: bool - 首次调用返回 True，后续调用返回 False。
def create_init():
    flag = False
    def init():
        nonlocal flag
        if not flag:
            flag = True
            return True
        return False

    return init

# foreground()
# 获取当前处于前台（活动）窗口的进程名称和窗口标题。
#
# 参数: 无
# 返回: tuple - 包含两个字符串的元组 (process_name, window_title)。
#               process_name (str): 当前前台应用程序的进程名称。
#               window_title (str): 当前前台窗口的标题。
def foreground():
    with foreground_listener.active_window_info_lock:
        process_name = foreground_listener.current_process_name
        window_title = foreground_listener.current_window_title
        return process_name, window_title

# position(x=-1, y=-1)
# 获取鼠标的当前位置。
# 如果提供了有效的 x 和 y 坐标（大于等于 0），则直接返回这些坐标。
# 如果 x 与 y 为 -1，则获取当前鼠标位置的对应坐标。
#
# 参数:
#   x (int, optional): X坐标。如果为 -1，则使用当前鼠标的X坐标。默认为 -1。
#   y (int, optional): Y坐标。如果为 -1，则使用当前鼠标的Y坐标。默认为 -1。
# 返回: tuple - (x: int, y: int) 鼠标的坐标。
def position(x=-1, y=-1):
    if x >= 0 and y >= 0:
        return x, y
    nx, ny = pyautogui.position()
    if x < 0:
        x = nx
    if y < 0:
        y = ny
    return x, y

# click(button, x=-1, y=-1)
# 模拟鼠标或键盘按键的点击操作。
#
# 参数:
#   button (str): 要点击的按钮或按键的名称。
#                 如果 'button' 在 MOUSE_BUTTON 中，则执行鼠标点击。
#                 否则，视为键盘按键。
#   x (int, optional): 鼠标点击的X坐标。仅当 'button' 为鼠标按钮时有效。默认为 -1 (表示当前鼠标X坐标)。
#   y (int, optional): 鼠标点击的Y坐标。仅当 'button' 为鼠标按钮时有效。默认为 -1 (表示当前鼠标Y坐标)。
# 返回: 无
def click(button, x=-1, y=-1):
    if button in MOUSE_BUTTON:
        x, y = position(x, y)
        pyautogui.mouseDown(x, y, button=button)
        pyautogui.mouseUp(x, y, button=button)
    else:
        keyboard.press_and_release(button)

# down(button, x=-1, y=-1)
# 模拟鼠标或键盘按键的按下操作（不释放）。
#
# 参数:
#   button (str): 要按下的按钮或按键的名称。
#                 如果 'button' 在 MOUSE_BUTTON 中，则执行鼠标按下。
#                 否则，视为键盘按键。
#   x (int, optional): 鼠标按下的X坐标。仅当 'button' 为鼠标按钮时有效。默认为 -1 (表示当前鼠标X坐标)。
#   y (int, optional): 鼠标按下的Y坐标。仅当 'button' 为鼠标按钮时有效。默认为 -1 (表示当前鼠标Y坐标)。
# 返回: 无
def down(button, x=-1, y=-1):
    if button in MOUSE_BUTTON:
        x, y = position(x, y)
        pyautogui.mouseDown(x, y, button=button)
    else:
        keyboard.press(button)

# up(button, x=-1, y=-1)
# 模拟鼠标或键盘按键的释放操作。
#
# 参数:
#   button (str): 要释放的按钮或按键的名称。
#                 如果 'button' 在 MOUSE_BUTTON 中，则执行鼠标释放。
#                 否则，视为键盘按键。
#   x (int, optional): 鼠标释放的X坐标。仅当 'button' 为鼠标按钮时有效。默认为 -1 (表示当前鼠标X坐标)。
#   y (int, optional): 鼠标释放的Y坐标。仅当 'button' 为鼠标按钮时有效。默认为 -1 (表示当前鼠标Y坐标)。
# 返回: 无
def up(button, x=-1, y=-1):
    if button in MOUSE_BUTTON:
        x, y = position(x, y)
        pyautogui.mouseUp(x, y, button=button)
    else:
        keyboard.release(button)
