import tkinter as tk
from tkinter import ttk
import keyboard

import config
import event_listen
import item

class EditPage:
    def __init__(self, master, index):
        self.master = master
        self.index = index
        self.record = False

        if index >= 0 and index < len(config.items):
            self.item = config.items[self.index]
        else:
            self.item = None

    def show(self, on_hide):
        self.on_hide = on_hide

        root = tk.Toplevel(self.master)
        self.root = root

        root.title('')
        root.grab_set()

        # Range
        range_frame = ttk.Frame(root)
        range_frame.pack(side='top', fill='x')
        range_label = ttk.Label(range_frame, text='范围: ')
        range_label.pack(side='left')
        range_entry = ttk.Entry(range_frame)
        range_entry.pack(side='left', fill='x', expand=True)
        self.range_entry = range_entry

        # Location
        location_frame = ttk.Frame(root)
        location_frame.pack(side='top', fill='x')
        location_label1 = ttk.Label(location_frame, text='位置: (')
        location_label1.pack(side='left')
        location_entry_x = ttk.Entry(location_frame)
        location_entry_x.pack(side='left', fill='x', expand=True)
        location_label2 = ttk.Label(location_frame, text=', ')
        location_label2.pack(side='left')
        location_entry_y = ttk.Entry(location_frame)
        location_entry_y.pack(side='left', fill='x', expand=True)
        location_label3 = ttk.Label(location_frame, text=')')
        location_label3.pack(side='left')
        self.location_entry_x = location_entry_x
        self.location_entry_y = location_entry_y

        # Type
        type_frame = ttk.Frame(root)
        type_frame.pack(side='top', fill='x')
        type_label = ttk.Label(type_frame, text='类型: ')
        type_label.pack(side='left')
        type_combobox = ttk.Combobox(type_frame, state='readonly')
        type_combobox['values'] = ('Click', 'Press', 'Multi')
        type_combobox.pack(side='left', fill='x', expand=True)
        type_combobox.bind('<<ComboboxSelected>>', self.on_type_combobox_select)
        self.type_combobox = type_combobox

        # Button
        button_frame = ttk.Frame(root)
        button_frame.pack(side='top', fill='x')
        button_label = ttk.Label(button_frame, text='按键: ')
        button_label.pack(side='left')
        button_combobox = ttk.Combobox(button_frame, state='readonly')
        button_combobox['values'] = ('Left', 'Right')
        button_combobox.pack(side='left', fill='x', expand=True)
        self.button_combobox = button_combobox

        # Hotkey
        hotkey_frame = ttk.Frame(root)
        hotkey_frame.pack(side='top', fill='x')
        hotkey_label = ttk.Label(hotkey_frame, text='热键: ')
        hotkey_label.pack(side='left')
        hotkey_button = ttk.Button(hotkey_frame, command=self.on_hotkey_click)
        hotkey_button.pack(side='left', fill='x', expand=True)
        self.hotkey_button = hotkey_button

        # Interval
        interval_pin = ttk.Frame(root)
        interval_pin.pack(side='top', fill='x')
        interval_frame = ttk.Frame(interval_pin)
        interval_label1 = ttk.Label(interval_frame, text='频率: ')
        interval_label1.pack(side='left')
        interval_entry = ttk.Entry(interval_frame)
        interval_entry.pack(side='left', fill='x', expand=True)
        interval_label2 = ttk.Label(interval_frame, text='ms')
        interval_label2.pack(side='left')
        self.interval_frame = interval_frame
        self.interval_entry = interval_entry

        # Clicks
        clicks_pin = ttk.Frame(root)
        clicks_pin.pack(side='top', fill='x')
        clicks_frame = ttk.Frame(clicks_pin)
        clicks_label = ttk.Label(clicks_frame, text='次数: ')
        clicks_label.pack(side='left')
        clicks_entry = ttk.Entry(clicks_frame)
        clicks_entry.pack(side='left', fill='x', expand=True)
        self.clicks_frame = clicks_frame
        self.clicks_entry = clicks_entry

        # Status
        status_frame = ttk.Frame(root)
        status_frame.pack(side='top', fill='x')
        status_label = ttk.Label(status_frame, text='状态: ')
        status_label.pack(side='left')
        status_combobox = ttk.Combobox(status_frame, state='readonly')
        status_combobox['values'] = ('Enable', 'Disable')
        status_combobox.pack(side='left', fill='x', expand=True)
        self.status_combobox = status_combobox

        # Save
        save = ttk.Button(root, text='保存', command=self.on_save_click)
        save.pack(fill='x', expand=True)
        save_check_label = ttk.Label(root, text='')
        self.save_check_label = save_check_label

        root.protocol('WM_DELETE_WINDOW', self.hide)

        self.fill_data()
        self.on_type_combobox_select(None)

    def fill_data(self):
        if self.item is None:
            self.item = item.Item()
            self.range_entry.insert(0, 'GLOBAL')
            self.location_entry_x.insert(0, -1)
            self.location_entry_y.insert(0, -1)
            self.type_combobox.current(0)
            self.button_combobox.current(0)
            self.hotkey_button.config(text='')
            self.interval_entry.insert(0, 200)
            self.clicks_entry.insert(0, -1)
            self.status_combobox.current(0)
        else:
            self.range_entry.insert(0, self.item.range)
            self.location_entry_x.insert(0, self.item.location[0])
            self.location_entry_y.insert(0, self.item.location[1])
            self.type_combobox.set(self.item.type)
            self.button_combobox.set(self.item.button)
            self.hotkey_button.config(text=self.item.hotkey)
            self.interval_entry.insert(0, self.item.interval if self.item.interval != -1 else 200)
            self.clicks_entry.insert(0, self.item.clicks)
            self.status_combobox.set(self.item.status)

    def hide(self):
        self.root.grab_release()
        self.root.destroy()
        self.on_hide()

    def on_type_combobox_select(self, event):
        selected = self.type_combobox.get()
        if selected == 'Multi':
            self.interval_frame.pack(side='left', fill='x', expand=True)
            self.clicks_frame.pack(side='left', fill='x', expand=True)
        else:
            self.interval_frame.pack_forget()
            self.clicks_frame.pack_forget()

    def on_hotkey_click(self):
        self.hotkey_button.config(text='...')
        self.record = True
        event_listen.stop()

        current_keys = set()

        def on_press(event):
            current_keys.add(event.name)
            self.hotkey_button.config(text='+'.join(current_keys))

        def on_release(event):
            if  event.name in current_keys:
                current_keys.remove(event.name)
            if len(current_keys) == 0:
                self.record = False
                keyboard.unhook_all()
                event_listen.start()

        def hook(event):
            match event.event_type:
                case keyboard.KEY_DOWN:
                    return on_press(event)
                case keyboard.KEY_UP:
                    return on_release(event)
                case _:
                    return
        
        keyboard.hook(hook)

    def on_save_click(self):
        def value_check():
            temp = item.Item()

            temp.range = self.range_entry.get()
            if temp.range == '':
                raise Exception('Range is empty')

            temp.location = (int(self.location_entry_x.get()), int(self.location_entry_y.get()))

            temp.type = self.type_combobox.get()

            temp.button = self.button_combobox.get()

            temp.hotkey = self.hotkey_button.cget('text')
            if temp.hotkey == '':
                raise Exception('Hotkey is empty')

            if temp.type == 'Multi':
                temp.interval = int(self.interval_entry.get())
                temp.clicks = int(self.clicks_entry.get())
            else:
                temp.interval = -1
                temp.clicks = -1

            temp.status = self.status_combobox.get()
            
            return temp

        try:
            temp = value_check()
            self.item.__dict__ = temp.__dict__
        except Exception as e:
            self.save_check_label.config(text=f'{e}')
            self.save_check_label.pack()
            return

        if self.index == -1:
            config.items.append(self.item)
        config.save()
        self.hide()
        pass