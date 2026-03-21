import logging
import os
import sys

import common

# 应用日志文件路径
app_log_file_path = os.path.join(common.root_path(), 'app.log')
# 脚本日志文件路径
script_log_file_path = os.path.join(common.config_path(), 'scripts.log')

def log_level():
    if hasattr(sys, '_MEIPASS'):
        return logging.INFO
    return logging.DEBUG

def create_logger(name, path):
    level = log_level()

    logger = logging.getLogger(name)
    logger.setLevel(level)

    file_handler = logging.FileHandler(path, encoding='utf-8')
    file_handler.setLevel(level)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

app = create_logger('app', app_log_file_path)
script = create_logger('script', script_log_file_path)
