import tkinter as tk
import webbrowser

import i18n
import settings_page
import utils

menu = None

def init(master):
    global menu

    menu = tk.Menu(master)
    master.config(menu=menu)

    tools_menu = tk.Menu(menu, tearoff=0)
    menu.add_cascade(label=i18n.t('Tools'), menu=tools_menu)
    tools_menu.add_command(label=i18n.t('Settings'), command=on_settings_click)

    help_menu = tk.Menu(menu, tearoff=0)
    menu.add_cascade(label=i18n.t('Help'), menu=help_menu)
    help_menu.add_command(label=i18n.t('About'), command=on_about_click)

def on_settings_click():
    settings_page.SettingsPage(menu.master).show()

def on_about_click():
    about_window = tk.Toplevel(menu.master)
    about_window.title(i18n.t('About'))
    about_window.iconbitmap(utils.assets_path('icon.ico'))

    label = tk.Label(about_window, text='GitHub: ')
    label.pack(side='left')

    link_label = tk.Label(about_window, text='https://github.com/CedarHuang/HawkingClicker', fg='blue', cursor='hand2')
    link_label.pack(side='left')

    link_label.bind('<Button-1>', lambda _: webbrowser.open('https://github.com/CedarHuang/HawkingClicker'))