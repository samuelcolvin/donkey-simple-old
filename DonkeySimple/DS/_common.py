TEMPLATES_DIR = 'templates'
STATIC_DIR = 'static'
PAGE_DIR = 'pages'
REPOS_DIR = 'repos'
SETTINGS_FILE = 'settings.py'
USERS_FILE = 'users.json'
MIN_PASSWORD_LENGTH = 6

def get_settings():
    import imp
    try:
        settings = imp.load_source('settings', SETTINGS_FILE)
    except Exception, e:
        raise Exception('Error importing %s: %r' % (SETTINGS_FILE, e))
    import settings
    return settings