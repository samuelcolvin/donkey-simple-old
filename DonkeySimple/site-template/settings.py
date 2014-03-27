import os
DEBUG = False
SITE_NAME = 'Site'
COOKIE_NAME = 'donksimpses'
SECRET_COOKIE_KEY = 'random_var_created_on_build'

# if debug is true, where to redirect print statements
# either 'PAGE' or 'STDOUT', might add STDERR in future
# (this can't be 'STDOUT' if you are using cgi)
PRINT_TO = 'PAGE'

# whether or not to require authenication
# WARNING: if you are using this on a server this NEEDS  to set to True
REQUIRE_AUTH = False

GIT_EMAIL = 'donkey-simple@example.com'
GIT_NAME = 'DONKEY'

# URL used when generating the site
SITE_URL = '/site/'
this_dir = os.path.dirname(__file__)
SITE_PATH = os.path.join(this_dir, 'site')
SITE_PATH_TMP = os.path.join(this_dir, 'site_tmp')

# delete SITE_PATH completely and start again, or just delete *.html, sitemap.xml, .htaccess and static/ files
# note SITE_PATH_TMP will always be deleted entirely
DELETE_ENTIRE_SITE_PATH = False

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