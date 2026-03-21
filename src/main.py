import sys

import config
import event_listener
import foreground_listener
import logger
import main_page
import single_instance
import tray

def main():
    if not single_instance.check():
        sys.exit()

    foreground_listener.start()

    event_listener.start()

    tray.start()

    main_page.init()

    silent = False
    if len(sys.argv) > 1:
        silent = sys.argv[1] == 'silent'

    if silent and config.settings.enable_tray:
        main_page.root.withdraw()

    main_page.root.mainloop()

if __name__ == '__main__':
    try:
        main()
    except:
        logger.app.error(f'An error occurred while the program was running', exc_info=True)