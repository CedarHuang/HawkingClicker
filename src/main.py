import sys

import config
import event_listen
import main_page
import tray

if __name__ == '__main__':

    event_listen.start()

    tray.start()

    main_page.init()

    silent = False
    if len(sys.argv) > 1:
        silent = sys.argv[1] == 'silent'

    if silent and config.settings.enable_tray:
        main_page.root.withdraw()

    main_page.root.mainloop()