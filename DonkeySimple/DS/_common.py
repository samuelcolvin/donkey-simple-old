TEMPLATES_DIR = 'templates'
STATIC_DIR = 'static'
PAGE_DIR = 'pages'
REPOS_DIR = 'repos'
SETTINGS_FILE = 'settings.py'
USERS_FILE = 'users.json'
LIBRARY_JSON_FILE = 'libraries.json'
GLOBCON_JSON_FILE = 'global_context.json'
MIN_PASSWORD_LENGTH = 6

def get_settings():
    import imp
    try:
        settings = imp.load_source('settings', SETTINGS_FILE)
    except Exception, e:
        raise Exception('Error importing %s: %r' % (SETTINGS_FILE, e))
    import settings
    return settings

import os
def get_all_repos():
    """
    Generator for all repos in the site.
    """
    for repo in os.listdir(REPOS_DIR):
        repo_path = os.path.join(REPOS_DIR, repo)
        if os.path.isdir(repo_path):
            yield repo, repo_path