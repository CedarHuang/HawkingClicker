import ctypes
import winreg
import win32com.client
import pywintypes

from core import common
from core import logger

def create_startup_to_winreg():
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, 'HawkingClicker', 0, winreg.REG_SZ, f'{common.exe_path()} silent')
    winreg.CloseKey(key)

def delete_startup_from_winreg():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_WRITE)
        winreg.DeleteValue(key, 'HawkingClicker')
        winreg.CloseKey(key)
    except FileNotFoundError:
        pass  # 注册表项不存在，无需处理
    except Exception:
        logger.app.error('Failed to delete startup from Windows Registry:', exc_info=True)

def create_startup_to_scheduled_task():
    scheduler = win32com.client.Dispatch('Schedule.Service')
    scheduler.Connect()
    root_folder = scheduler.GetFolder('\\')

    task = scheduler.NewTask(0)
    task.RegistrationInfo.Description = 'HawkingClicker Startup'

    TASK_RUNLEVEL_HIGHEST = 1
    task.Principal.RunLevel = TASK_RUNLEVEL_HIGHEST

    TASK_TRIGGER_LOGON = 9
    trigger = task.Triggers.Create(TASK_TRIGGER_LOGON)
    trigger.Enabled = True

    TASK_ACTION_EXEC = 0
    action = task.Actions.Create(TASK_ACTION_EXEC)
    action.Path = common.exe_path()
    action.Arguments = 'silent'

    TASK_CREATE_OR_UPDATE = 6
    TASK_LOGON_INTERACTIVE_TOKEN = 3
    root_folder.RegisterTaskDefinition(
        'HawkingClicker', task, TASK_CREATE_OR_UPDATE, None, None, TASK_LOGON_INTERACTIVE_TOKEN
    )

def delete_startup_from_scheduled_task():
    scheduler = win32com.client.Dispatch('Schedule.Service')
    scheduler.Connect()
    root_folder = scheduler.GetFolder('\\')
    try:
        root_folder.DeleteTask('HawkingClicker', 0)
    except pywintypes.com_error as e:
        # HRESULT 0x80070002 = ERROR_FILE_NOT_FOUND，计划任务不存在，无需处理
        if len(e.args) >= 4 and isinstance(e.args[2], tuple) and e.args[2][-1] == -2147024894:
            pass
        else:
            logger.app.error('Failed to delete startup from Scheduled Task:', exc_info=True)
    except Exception:
        logger.app.error('Failed to delete startup from Scheduled Task:', exc_info=True)

def is_running_as_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def update_startup(status, startup_as_admin):
    delete_startup_from_scheduled_task()
    delete_startup_from_winreg()
    if status:
        if is_running_as_admin() and startup_as_admin:
            create_startup_to_scheduled_task()
        else:
            create_startup_to_winreg()
