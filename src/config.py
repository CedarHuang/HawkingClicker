import appdirs
import builtins
import importlib
import importlib.util
import inspect
import json
import os

import api
import event_listener
import tray
import utils
from logger import script_logger

app_name = 'HawkingClicker'
app_author = 'CedarHuang'

scripts_name = 'scripts'
event_config_name = 'event.json'
settings_config_name = 'settings.json'

config_dir = appdirs.user_config_dir(app_name, app_author, roaming=True)
scripts_path = os.path.join(config_dir, scripts_name)
event_config_path = os.path.join(config_dir, event_config_name)
settings_config_path = os.path.join(config_dir, settings_config_name)

def mkdir_if_not_exists(path):
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except:
            pass

mkdir_if_not_exists(config_dir)
mkdir_if_not_exists(scripts_path)

class Event:
    def __init__(self):
        self.range = None
        self.position = None
        self.type = None
        self.button = None
        self.hotkey = None
        self.interval = None
        self.clicks = None
        self.status = None

    def from_dict(self, dict):
        self.__dict__ = dict
        return self

    def to_dict(self):
        return self.__dict__

    def to_tuple(self):
        return tuple(value if value != -1 else '--' for value in self.__dict__.values())

class Events(list):
    def __init__(self):
        super().__init__()
        try:
            with open(event_config_path, 'r') as file:
                self.extend([Event().from_dict(i) for i in json.load(file)])
        except:
            pass

    def save(self):
        with open(event_config_path, 'w') as file:
            dicts = [
                {k: v for k, v in event.to_dict().items() if not k.startswith('_')}
                for event in self
            ]
            json.dump(dicts, file, indent=4)
        event_listener.stop()
        event_listener.start()

    def append(self, event):
        super().append(event)
        self.save()
    
    def pop(self, index):
        super().pop(index)
        self.save()

    def swap(self, a, b):
        self[a], self[b] = self[b], self[a]
        self.save()

    def update(self, index, event):
        if index < 0 or index >= len(self):
            return self.append(event)
        self[index] = event
        self.save()

events = Events()

class Settings:
    def __init__(self):
        self.enable_tray = False
        self.startup = False
        self.startup_as_admin = False
        try:
            with open(settings_config_path, 'r') as file:
                self.__dict__.update(json.load(file))
        except:
            pass

    def save(self, update_startup = False):
        with open(settings_config_path, 'w') as file:
            json.dump(self.__dict__, file, indent=4)
        tray.update_visible()
        if update_startup:
            utils.update_startup(self.startup, self.startup_as_admin)

    def update(self, settings):
        update_startup = self.startup != settings.startup or self.startup_as_admin != settings.startup_as_admin
        self.__dict__ = settings.__dict__
        self.save(update_startup)

settings = Settings()

class ScriptContext(dict):
    # 用户脚本中import的查找路径
    allowed_import_paths = [
        os.path.abspath(scripts_path),
    ]

    def __init__(self):
        super().__init__()

        self['__builtins__'] = self.create_restricted_builtins()

    def create_restricted_builtins(self):
        restricted_builtins = builtins.__dict__.copy()

        if 'open' in restricted_builtins:
            del restricted_builtins['open']
        if 'exit' in restricted_builtins:
            del restricted_builtins['exit']
        if 'quit' in restricted_builtins:
            del restricted_builtins['quit']

        restricted_builtins['__import__'] = self.custom_import
        restricted_builtins['print'] = self.custom_print
        restricted_builtins['init'] = api.create_init()
        restricted_builtins.update(api.create_sleep())

        self.import_module_to_target(restricted_builtins, 'api', import_root=False, import_all=True, exclude_module=True)

        return restricted_builtins

    def set_stop(self):
        self['__builtins__']['set_stop']()

    def clear_stop(self):
        self['__builtins__']['clear_stop']()

    def custom_import(self, name, globals=None, locals=None, fromlist=(), level=0):
        # 允许导入的内置模块
        if name in ['math', 'time']:
            return importlib.import_module(name)

        # 禁止相对导入
        if level != 0:
            raise ImportError(f"Relative imports are not allowed in sandboxed scripts: '{name}' (level={level})")

        # 尝试在允许的路径中查找模块
        for allowed_path_root in self.allowed_import_paths:
            # 构造可能的模块文件路径
            # 对于 'module' -> 'module.py'
            # 对于 'package.sub_module' -> 'package/__init__.py' then 'package/sub_module.py'
            module_path_parts = name.split('.')
            # 尝试作为文件导入 (e.g., module.py)
            potential_file_path = os.path.join(allowed_path_root, *module_path_parts) + '.py'
            # 尝试作为包导入 (e.g., package/__init__.py)
            potential_package_init_path = os.path.join(allowed_path_root, *module_path_parts, '__init__.py')

            found_path = None
            if os.path.exists(potential_file_path) and os.path.isfile(potential_file_path):
                found_path = potential_file_path
            elif os.path.exists(potential_package_init_path) and os.path.isfile(potential_package_init_path):
                found_path = potential_package_init_path
            if not found_path:
                continue

            # 确保找到的路径在搜索路径下
            resolved_found_path = os.path.realpath(found_path)
            resolved_allowed_path_root = os.path.realpath(allowed_path_root)
            if not resolved_found_path.startswith(resolved_allowed_path_root + os.sep) and resolved_found_path != resolved_allowed_path_root:
                continue

            # 加载模块
            spec = importlib.util.spec_from_file_location(name, resolved_found_path)
            if not spec:
                continue

            module = importlib.util.module_from_spec(spec)
            module.__builtins__ = self['__builtins__']
            module.__builtins__['init'] = api.create_init()
            spec.loader.exec_module(module)
            return module

        raise ImportError(f"Module '{name}' not found or not allowed to be imported from restricted paths.")

    def custom_print(self, *args, **kwargs):
        sep = kwargs.get('sep', ' ')
        end = kwargs.get('end', '\n')
        message = sep.join(map(str, args)) + end.rstrip('\n')
        script_logger.info(message)

    @staticmethod
    def import_module_to_target(target, module_name, import_root=True, import_all=False, exclude_module=False):
        module = importlib.import_module(module_name)

        if import_root:
            target[module_name] = module

        if not import_all:
            return

        for name in dir(module):
            if name.startswith('_'):
                continue

            member = getattr(module, name)
            if exclude_module and inspect.ismodule(member):
                continue

            target[name] = member

class Scripts:
    def __init__(self):
        pass

    def load_as_function(self, script_name):
        script_path = os.path.join(scripts_path, f'{script_name}.py')
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                script_code = f.read()
        except:
            return lambda: None

        compiled_code = None
        try:
            compiled_code = compile(script_code, f'<{script_name}>', 'exec')
        except SyntaxError as e:
            script_logger.error(f'Syntax error in script <{script_name}> at "{script_path}": {e}', exc_info=True)
            return lambda: None
        except Exception as e:
            script_logger.error(f'Unexpected error compiling script <{script_name}> at "{script_path}": {e}', exc_info=True)
            return lambda: None

        script_context = ScriptContext()

        def wrapped_function():
            try:
                exec(compiled_code, script_context)
            except api.ScriptExit as e:
                script_logger.info(f'Script <{script_name}> terminated: {e}')
            except Exception as e:
                script_logger.error(f'Runtime error in script <{script_name}>: {e}', exc_info=True)
            finally:
                script_context.clear_stop()

        return wrapped_function, script_context

scripts = Scripts()
