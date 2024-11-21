import locale

from . import en
from . import zh_CN

language, _ = locale.getdefaultlocale()

i18n = None
try:
    i18n = eval(f'{language}.{language}')
except:
    i18n = en.en

def t(key):
    if key in i18n:
        return i18n[key]
    if key in en.en:
        return en.en[key]
    return key