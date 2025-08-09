import tkinter as tk
from tkinter import ttk

import config
import utils
from i18n import i18n

CEHCK_SELECTED = ['!alternate', 'selected']
CEHCK_UNSELECTED = ['!alternate', '!selected']

class SettingsPage:
    def __init__(self, master):
        self.master = master

    def show(self):
        root = tk.Toplevel(self.master)
        self.root = root

        root.title(i18n('Settings'))
        root.iconbitmap(utils.assets_path('icon.ico'))

        # Tray
        tray_check = ttk.Checkbutton(root, text=i18n('EnableTray'))
        tray_check.pack(side='top', fill='x', expand=True)
        self.tray_check = tray_check

        # Startup
        startup_frame = ttk.Frame(root)
        startup_frame.pack(side='top', fill='x')

        startup_check = ttk.Checkbutton(startup_frame, text=i18n('Startup'), command=self.update_startup_state)
        startup_check.pack(side='left', fill='x', expand=True)
        self.startup_check = startup_check

        # StartupAsAdmin
        startup_as_admin_check = ttk.Checkbutton(startup_frame, text=i18n('StartupAsAdmin'), command=self.update_startup_as_admin_state)
        startup_as_admin_check.pack(side='left', fill='x', expand=True)
        self.startup_as_admin_check = startup_as_admin_check

        # Save
        save = ttk.Button(root, text=i18n('Save'), command=self.on_save_click)
        save.pack(side='top', fill='x', expand=True)
        save_check_label = ttk.Label(root, text='')
        self.save_check_label = save_check_label

        root.protocol('WM_DELETE_WINDOW', self.hide)

        self.fill_data()

    def fill_data(self):
        self.tray_check.state(CEHCK_SELECTED if config.settings.enable_tray else CEHCK_UNSELECTED)
        self.startup_check.state(CEHCK_SELECTED if config.settings.startup else CEHCK_UNSELECTED)
        self.startup_as_admin_check.state(CEHCK_SELECTED if config.settings.startup_as_admin else CEHCK_UNSELECTED)

    def hide(self):
        self.root.destroy()

    def update_startup_state(self):
        if self.startup_check.instate(CEHCK_UNSELECTED):
            self.startup_as_admin_check.state(CEHCK_UNSELECTED)

    def update_startup_as_admin_state(self):
        if self.startup_as_admin_check.instate(CEHCK_SELECTED):
            self.startup_check.state(CEHCK_SELECTED)

    def on_save_click(self):
        def value_check():
            temp = config.Settings()

            temp.enable_tray = self.tray_check.instate(CEHCK_SELECTED)
            temp.startup  = self.startup_check.instate(CEHCK_SELECTED)
            temp.startup_as_admin = self.startup_as_admin_check.instate(CEHCK_SELECTED)

            if not utils.is_running_as_admin():
                if config.settings.startup_as_admin == True or temp.startup_as_admin == True:
                    raise Exception(f'{i18n('RunningAsAdminIsRequiredToSet')} "{i18n('StartupAsAdmin')}"')

            return temp

        try:
            temp = value_check()
        except Exception as e:
            self.save_check_label.config(text=f'{e}')
            self.save_check_label.pack()
            return

        config.settings.update(temp)
        self.hide()