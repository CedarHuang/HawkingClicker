import os
import tkinter as tk
from tkinter import ttk

import common
import config
import edit_page
import list_view
import menu
import tray
from __version__ import __version__

root = None

def init():
    global root
    root = tk.Tk()
    root.title(f'HawkingClicker v{__version__}')
    root.iconbitmap(common.assets_path('icon.ico'))

    menu.init(root)

    button_frame = ttk.Frame(root)
    button_frame.pack(side='top', fill='x')
    config_dir = ttk.Button(button_frame, text='⚙', command=on_config_dir_click)
    config_dir.pack(side='left')
    create = ttk.Button(button_frame, text='+', command=on_create_click)
    create.pack(side='left', fill='x', expand=True)
    delete = ttk.Button(button_frame, text='-', command=on_delete_click)
    delete.pack(side='left', fill='x', expand=True)

    tree_frame = ttk.Frame(root)
    tree_frame.pack(side='top')
    list_view.init(tree_frame)

    root.protocol('WM_DELETE_WINDOW', on_close)

def on_config_dir_click():
    os.startfile(common.config_path())

def on_create_click():
    edit_page.EditPage(root, -1).show(list_view.refresh)

def on_delete_click():
    selected_item = list_view.tree.selection()
    selected_index = list_view.tree.index(selected_item)
    if selected_index >= len(config.events):
        return
    config.events.pop(selected_index)
    list_view.refresh()

def on_close():
    if tray.icon.visible:
        root.withdraw()
    else:
        tray.stop()
        root.destroy()