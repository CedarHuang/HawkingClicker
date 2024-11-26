import event_listen
import main_page
import tray

if __name__ == '__main__':

    event_listen.start()

    tray.start()

    main_page.init()

    main_page.root.mainloop()