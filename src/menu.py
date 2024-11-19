import tkinter as tk
import webbrowser

menu = None

def init(master):
    global menu

    menu = tk.Menu(master)
    master.config(menu=menu)

    help_menu = tk.Menu(menu, tearoff=0)
    menu.add_cascade(label="帮助", menu=help_menu)
    help_menu.add_command(label="关于", command=on_about_click)

def on_about_click():
    about_window = tk.Toplevel(menu.master)
    about_window.title("关于")

    label = tk.Label(about_window, text="GitHub: ")
    label.pack(side='left')

    link_label = tk.Label(about_window, text="https://github.com/CedarHuang/HawkingClicker", fg="blue", cursor="hand2")
    link_label.pack(side='left')

    link_label.bind("<Button-1>", lambda _: webbrowser.open("https://github.com/CedarHuang/HawkingClicker"))