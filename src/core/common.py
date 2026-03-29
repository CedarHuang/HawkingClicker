import appdirs
import os
import sys

app_name = 'HawkingClicker'
app_author = 'CedarHuang'

scripts_name = 'scripts'
builtins_name = '__builtins__.py'
event_config_name = 'event.json'
settings_config_name = 'settings.json'

def mkdir_if_not_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

def exe_path():
    return os.path.abspath(sys.argv[0])

def root_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def config_path():
    return appdirs.user_config_dir(app_name, app_author, roaming=True)

def scripts_path():
    return os.path.join(config_path(), scripts_name)

def builtins_path():
    return os.path.join(scripts_path(), builtins_name)

def event_config_path():
    return os.path.join(config_path(), event_config_name)

def settings_config_path():
    return os.path.join(config_path(), settings_config_name)
