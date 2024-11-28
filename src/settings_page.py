import tkinter as tk
from tkinter import ttk

import config
import i18n
import utils

CEHCK_SELECTED = ['!alternate', 'selected']
CEHCK_UNSELECTED = ['!alternate', '!selected']

class SettingsPage:
    def __init__(self, master):
        self.master = master

    def show(self):
        root = tk.Toplevel(self.master)
        self.root = root

        root.title(i18n.t('Settings'))
        root.iconbitmap(utils.assets_path('icon.ico'))

        # Tray
        tray_check = ttk.Checkbutton(root, text=i18n.t('EnableTray'))
        tray_check.pack(side='top', fill='x', expand=True)
        self.tray_check = tray_check

        # Save
        save = ttk.Button(root, text=i18n.t('Save'), command=self.on_save_click)
        save.pack(side='top', fill='x', expand=True)

        root.protocol('WM_DELETE_WINDOW', self.hide)

        self.fill_data()

    def fill_data(self):
        self.tray_check.state(CEHCK_SELECTED if config.settings.enable_tray else CEHCK_UNSELECTED)

    def hide(self):
        self.root.destroy()

    def on_save_click(self):
        temp = config.Settings()
        temp.enable_tray = self.tray_check.instate(CEHCK_SELECTED)
        config.settings.update(temp)
        self.hide()