import imp
TEMPLATES_DIR = 'templates'
STATIC_DIR = 'static'
PAGE_DIR = 'pages'
SETTINGS_FILE = 'settings.py'
USERS_FILE = 'users.json'
# import os
# print os.path.dirname(os.path.realpath(__file__))
try:
    SETTINGS = imp.load_source('SETTINGS', SETTINGS_FILE)
except Exception, e:
    raise Exception('Error importing %s: %r' % (SETTINGS_FILE, e))

from SETTINGS import *

SETTINGS_DICT = {}
for attr in dir(SETTINGS):
    SETTINGS_DICT[attr] = getattr(SETTINGS, attr)

if 'SITE_URL' in globals():
    SITE_EDIT_URL = SITE_URL + 'edit/'