import importlib
import locale

from . import en

language, _ = locale.getdefaultlocale()

_i18n = None
try:
    language_module = importlib.import_module(f'.{language}', package=__package__)
    _i18n = language_module.i18n
except:
    _i18n = en.i18n

def i18n(key):
    if key in _i18n and _i18n[key] is not None:
        return _i18n[key]
    if key in en.i18n and en.i18n[key] is not None:
        return en.i18n[key]
    return key