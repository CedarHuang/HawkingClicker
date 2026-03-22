import pystray
import threading
from PIL import Image

from core import common
from core import config
from core.callbacks import callbacks, CallbackEvent
from i18n import i18n
from views import main_page
from __version__ import __version__

icon = None

def start():
    global icon

    image = Image.open(common.assets_path('icon.ico'))
    menu = (
        pystray.MenuItem(i18n('Open'), on_open_click, default=True),
        pystray.MenuItem(i18n('Exit'), on_exit_click)
    )
    icon = pystray.Icon('HawkingClicker', image, f'HawkingClicker v{__version__}', menu)

    threading.Thread(target=icon.run, args=(update_visible,), daemon=True).start()

@callbacks.on(CallbackEvent.TRAY_UPDATE)
def update_visible(_ = None):
    icon.visible = config.settings.enable_tray

def stop():
    icon.visible = False
    icon.stop()

def on_open_click(icon, item):
    main_page.root.deiconify()

def on_exit_click(icon, item):
    stop()
    main_page.root.destroy()