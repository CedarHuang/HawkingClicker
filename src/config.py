import appdirs
import json
import os

import event_listen
import item

app_name = 'HawkingClicker'
app_author = 'CedarHuang'

config_name = 'event.json'

config_dir = appdirs.user_config_dir(app_name, app_author, roaming=True)
config_path = os.path.join(config_dir, config_name)

if not os.path.exists(config_dir):
    try:
        os.makedirs(config_dir)
    except:
        pass

items = []
try:
    with open(config_path, 'r') as file:
        for i in json.load(file):
            items.append(item.Item().from_dict(i))
except:
    pass

def save():
    with open(config_path, 'w') as file:
        dicts = [i.to_dict() for i in items]
        json.dump(dicts, file, indent=4)
    event_listen.stop()
    event_listen.start()

def swap(a, b):
    items[a], items[b] = items[b], items[a]
    save()