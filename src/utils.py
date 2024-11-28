import os
import sys
import winreg

def base_path():
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def assets_path(asset_file_name):
    return os.path.join(base_path(), 'assets', asset_file_name)

def exe_path():
    return os.path.abspath(sys.argv[0])

def add_to_startup():
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, 'HawkingClicker', 0, winreg.REG_SZ, f'{exe_path()} silent')
    winreg.CloseKey(key)

def remove_from_startup():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_WRITE)
        winreg.DeleteValue(key, 'HawkingClicker')
        winreg.CloseKey(key)
    except:
        pass

def update_startup(status):
    if status:
        add_to_startup()
    else:
        remove_from_startup()
