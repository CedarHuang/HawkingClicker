from tkinter import ttk

import config
import edit_page

tree = None

def init(master):
    global tree
    tree = ttk.Treeview(master, columns=('Range', 'Position', 'Type', 'Button', 'Hotkey', 'Interval', 'Clicks', 'Status'), show='headings')
    tree.pack(side='left')

    tree.heading('Range', text='范围')
    tree.heading('Position', text='位置')
    tree.heading('Type', text='类型')
    tree.heading('Button', text='按键')
    tree.heading('Hotkey', text='热键')
    tree.heading('Interval', text='频率')
    tree.heading('Clicks', text='次数')
    tree.heading('Status', text='状态')

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
    for item in config.items:
        tree.insert('', 'end', values=item.to_tuple())

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
        config.swap(selected_index, selected_index - 1)
        refresh()
        select_row_by_index(selected_index - 1)

def on_down_click():
    selected_item = tree.selection()
    if selected_item == ():
        return
    selected_index = tree.index(selected_item)
    if selected_index < len(config.items) - 1:
        config.swap(selected_index, selected_index + 1)
        refresh()
        select_row_by_index(selected_index + 1)

def on_double_click(event):
    selected_item = event.widget.identify_row(event.y)
    if not selected_item:
        return
    selected_index = tree.index(selected_item)
    edit_page.EditPage(tree.master, selected_index).show(refresh)