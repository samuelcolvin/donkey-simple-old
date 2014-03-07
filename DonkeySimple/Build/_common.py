import imp
TEMPLATES_DIR = 'templates'
STATIC_DIR = 'static'
PAGE_DIR = 'pages'
REPOS_DIR = 'repos'
SETTINGS_FILE = 'settings.py'
USERS_FILE = 'web_interface/users.json'
MIN_PASSWORD_LENGTH = 6

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