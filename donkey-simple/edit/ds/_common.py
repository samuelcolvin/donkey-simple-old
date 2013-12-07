import json
TEMPLATES_DIR = 'templates'
PAGE_DIR = 'pages'
CONFIG_FILE = 'config.json'
CONFIG_SETTINGS = {}
with open(CONFIG_FILE, 'r') as infile:
    try:
        _config =  json.load(infile)
    except Exception, e:
        raise Exception('Error processing %s: %r' % (CONFIG_FILE, e))
    for name, val in _config.items():
        globals()[name] = val
        CONFIG_SETTINGS[name] = val
    if 'SITE_URL' in globals():
        SITE_EDIT_URL = SITE_URL + 'edit/'