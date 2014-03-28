import os
this_dir = os.path.dirname(__file__) #only used on this page

"""
Check and edit these settings:
==============================================
"""

# name of the site used in the web interface and available as a global variable during generate
SITE_NAME = 'Donkey Simple'

# whether or not to require authentication
# WARNING: if you are using this on a server this NEEDS to set to True and change the password
REQUIRE_AUTH = False

# details for commits to repos
GIT_EMAIL = 'donkey-simple@example.com'
GIT_NAME = 'DONKEY'

# domain of your site; prepended to SITE_URI to generate the sitemap
# should not end with /
SITE_DOMAIN = 'http://www.example.com'

# this is the base used for generating sitemap urls, 
# the homepage url and the 404 uri
# INTERLINK_URI is used for links between pages so the site works on the dev server
# should always start and end with /, eg '/' not '', '/site/' not 'site'
SITE_URI = '/site/'
# path site is generated at at
SITE_PATH = os.path.join(this_dir, 'site')

# delete SITE_PATH completely and start again
# or just delete *.html, sitemap.xml, .htaccess and static/ files
DELETE_ENTIRE_SITE_PATH = False

# email settings (a gmail/external server example is at the bottom of this file)
EMAIL_HOST = 'localhost'
EMAIL_FROM = 'admin@%s' % SITE_NAME

"""
==============================================
You can probably ignore settings from here on
"""

# whether to print details about the web interface as it's running
DEBUG = False

COOKIE_NAME = 'donksimpses'
SECRET_COOKIE_KEY = 'random_var_created_on_build'


# if debug is true, where to redirect print statements
# either 'PAGE' or 'STDOUT', might add STDERR in future
# (this can't be 'STDOUT' if you are using cgi)
PRINT_TO = 'PAGE'

# temporary path site is built at during generate
#  will always be deleted entirely on generate
SITE_PATH_TMP = os.path.join(this_dir, 'site_tmp')

# root used for links between pages, changing this may break the site when hosted
# by the dev server
INTERLINK_URI = ''

# this is the URL (or URI) the site will be displayed at when hosted by the dev server.
# (note, you probably don't need to change these two)
DEV_SITE_URL = '/site/'
# port the dev server runs on
DEV_PORT = 4000

# #example gmail settings
# EMAIL_USE_TLS = True
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_HOST_USER = 'username@gmail.com'
# EMAIL_HOST_PASSWORD = 'secret'
# EMAIL_FROM = EMAIL_HOST_USER