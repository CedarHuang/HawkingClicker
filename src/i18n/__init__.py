import importlib
import locale

from . import en
# 显式导入 诱使Pyinstaller正确打包
from . import zh_CN

language, _ = locale.getdefaultlocale()

_i18n = None
try:
    _i18n = globals()[language].i18n
except:
    _i18n = en.i18n

def i18n(key):
    if key in _i18n and _i18n[key] is not None:
        return _i18n[key]
    if key in en.i18n and en.i18n[key] is not None:
        return en.i18n[key]
    return key