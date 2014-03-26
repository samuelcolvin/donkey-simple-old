import os
DEBUG = True
SITE_NAME = 'Site'
COOKIE_NAME = 'donksimpses'
SECRET_COOKIE_KEY = 'random_var_created_on_build'

# either 'PAGE' or 'STDOUT'
PRINT_TO = 'PAGE'

GIT_EMAIL = 'donkey-simple@example.com'
GIT_NAME = 'DONKEY'

# URL used when generating the site
SITE_URL = '/site/'
this_dir = os.path.dirname(__file__)
SITE_PATH = os.path.join(this_dir, 'site')
SITE_PATH_TMP = os.path.join(this_dir, 'site_tmp')

# email settings
EMAIL_HOST = 'localhost'
EMAIL_FROM = 'admin@%s' % SITE_NAME

# #example gmail settings
# EMAIL_USE_TLS = True
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_HOST_USER = 'username@gmail.com'
# EMAIL_HOST_PASSWORD = 'secret'
# EMAIL_FROM = EMAIL_HOST_USER