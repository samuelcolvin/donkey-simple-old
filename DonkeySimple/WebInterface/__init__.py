import _views as views
from _auth import UserAuth
from werkzeug.serving import run_simple
import os

def run_dev_server():
    static_files= {'/static': os.path.join(os.path.dirname(__file__), 'static')}
    views.SERVER_MODE = views.SERVER_MODES.DEBUG
    run_simple('localhost', views.DEBUG_PORT, views.application, use_reloader = True, use_debugger = True, static_files = static_files)