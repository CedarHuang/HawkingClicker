import tkinter as tk
from tkinter import ttk

import config
import edit_page
import list_view
from __version__ import __version__

root = None

def init():
    global root
    root = tk.Tk()
    root.title(f'HawkingClicker {__version__}')

    button_frame = ttk.Frame(root)
    button_frame.pack(side='top', fill='x')
    create = ttk.Button(button_frame, text='+', command=on_create_click)
    create.pack(side='left', fill='x', expand=True)
    delete = ttk.Button(button_frame, text='-', command=on_delete_click)
    delete.pack(side='left', fill='x', expand=True)

    tree_frame = ttk.Frame(root)
    tree_frame.pack(side='top')
    list_view.init(tree_frame)

def on_create_click():
    edit_page.EditPage(root, -1).show(list_view.refresh)

def on_delete_click():
    selected_item = list_view.tree.selection()
    selected_index = list_view.tree.index(selected_item)
    if selected_index >= len(config.items):
        return
    config.items.pop(selected_index)
    config.save()
    list_view.refresh()