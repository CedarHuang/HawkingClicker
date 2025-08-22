import appdirs
import os
import sys

app_name = 'HawkingClicker'
app_author = 'CedarHuang'

scripts_name = 'scripts'
event_config_name = 'event.json'
settings_config_name = 'settings.json'

def mkdir_if_not_exists(path):
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except:
            pass

def base_path():
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def assets_path(asset_file_name):
    return os.path.join(base_path(), 'assets', asset_file_name)

def exe_path():
    return os.path.abspath(sys.argv[0])

def root_path():
    if hasattr(sys, '_MEIPASS'):
        return os.path.abspath(os.path.join(sys._MEIPASS, '..'))
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def config_path():
    return appdirs.user_config_dir(app_name, app_author, roaming=True)

def scripts_path():
    return os.path.join(config_path(), scripts_name)

def event_config_path():
    return os.path.join(config_path(), event_config_name)

def settings_config_path():
    return os.path.join(config_path(), settings_config_name)
