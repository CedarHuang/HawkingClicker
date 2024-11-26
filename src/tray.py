import pystray
import threading
from PIL import Image

import i18n
import main_page
import utils
from __version__ import __version__

icon = None

def start():
    global icon

    image = Image.open(utils.assets_path('icon.ico'))
    menu = (
        pystray.MenuItem(i18n.t('Open'), on_open_click, default=True),
        pystray.MenuItem(i18n.t('Exit'), on_exit_click)
    )
    icon = pystray.Icon('HawkingClicker', image, f'HawkingClicker v{__version__}', menu)

    threading.Thread(target=icon.run, daemon=True).start()

def stop():
    icon.visible = False
    icon.stop()

def on_open_click(icon, item):
    main_page.root.deiconify()

def on_exit_click(icon, item):
    stop()
    main_page.root.destroy()