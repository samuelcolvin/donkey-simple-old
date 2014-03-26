import _views as views
from _auth import UserAuth
from werkzeug.serving import run_simple
import os

def run_dev_server():
    views.SERVER_MODE = views.SERVER_MODES.DEBUG
    from werkzeug.wsgi import SharedDataMiddleware
    run_simple('localhost', views.DEBUG_PORT, views.get_siteserve_application(), use_reloader = True, use_debugger = True)