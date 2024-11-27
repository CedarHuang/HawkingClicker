from tkinter import ttk

import config
import edit_page
import i18n

tree = None

def init(master):
    global tree
    columns = ('Range', 'Position', 'Type', 'Button', 'Hotkey', 'Interval', 'Clicks', 'Status')
    tree = ttk.Treeview(master, columns=columns, show='headings')
    tree.pack(side='left')

    for col in columns:
        tree.heading(col, text=i18n.t(col))

    tree.configure(selectmode='browse')

    tree.bind('<Double-1>', on_double_click)

    refresh()

    up = ttk.Button(master, text='↑', width=5, command=on_up_click)
    up.pack(side='top', fill='y', expand=True)
    down = ttk.Button(master, text='↓', width=5, command=on_down_click)
    down.pack(side='top', fill='y', expand=True)

def refresh():
    for item in tree.get_children():
        tree.delete(item)
    for event in config.events:
        tree.insert('', 'end', values=event.to_tuple())

def select_row_by_index(index):
    row_ids = tree.get_children()
    if index >= 0 and index < len(row_ids):
        tree.selection_set(row_ids[index])

def on_up_click():
    selected_item = tree.selection()
    if selected_item == ():
        return
    selected_index = tree.index(selected_item)
    if selected_index > 0:
        config.events.swap(selected_index, selected_index - 1)
        refresh()
        select_row_by_index(selected_index - 1)

def on_down_click():
    selected_item = tree.selection()
    if selected_item == ():
        return
    selected_index = tree.index(selected_item)
    if selected_index < len(config.events) - 1:
        config.events.swap(selected_index, selected_index + 1)
        refresh()
        select_row_by_index(selected_index + 1)

def on_double_click(event):
    selected_item = event.widget.identify_row(event.y)
    if not selected_item:
        return
    selected_index = tree.index(selected_item)
    edit_page.EditPage(tree.master, selected_index).show(refresh)