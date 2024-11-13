import event_listen
import main_page

if __name__ == '__main__':

    event_listen.start()

    main_page.init()

    main_page.root.mainloop()