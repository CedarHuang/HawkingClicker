import os
import sys

def base_path():
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def assets_path(asset_file_name):
    return os.path.join(base_path(), 'assets', asset_file_name)
