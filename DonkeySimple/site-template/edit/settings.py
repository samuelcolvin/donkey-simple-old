DEBUG = True
SITE_NAME = 'Site'
COOKIE_NAME = 'donksimpses'
SECRET_COOKIE_KEY = 'random_var_created_on_build'

# COOKIE_NAME = 'session'
# SECRET_COOKIE_KEY = '\xfa\xdd\xb8z\xae\xe0}4\x8b\xea'

GIT_EMAIL = 'donkey-simple@example.com'
GIT_NAME = 'DONKEY'

# URI used when generating the site
# comment out or remove to auto-detect the URI 
# (autodetect is only available in the web interface) 
SITE_URI = '/uri/of/site'

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