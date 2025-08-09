import importlib
import locale

from . import en

language, _ = locale.getdefaultlocale()

i18n = None
try:
    language_module = importlib.import_module(f'.{language}', package=__package__)
    i18n = language_module.i18n
except:
    i18n = en.i18n

def t(key):
    if key in i18n:
        return i18n[key]
    if key in en.i18n:
        return en.i18n[key]
    return key