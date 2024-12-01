import appdirs
import json
import os

import event_listen
import tray
import utils

app_name = 'HawkingClicker'
app_author = 'CedarHuang'

event_config_name = 'event.json'
settings_config_name = 'settings.json'

config_dir = appdirs.user_config_dir(app_name, app_author, roaming=True)
event_config_path = os.path.join(config_dir, event_config_name)
settings_config_path = os.path.join(config_dir, settings_config_name)

if not os.path.exists(config_dir):
    try:
        os.makedirs(config_dir)
    except:
        pass

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
        event_listen.stop()
        event_listen.start()

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
        try:
            with open(settings_config_path, 'r') as file:
                self.__dict__.update(json.load(file))
        except:
            pass

    def save(self):
        with open(settings_config_path, 'w') as file:
            json.dump(self.__dict__, file, indent=4)
        tray.update_visible()
        utils.update_startup(self.startup)

    def update(self, settings):
        self.__dict__ = settings.__dict__
        self.save()

settings = Settings()