import _views as views
from _auth import UserAuth
import sys, StringIO, traceback, re

def run_dev_server():
    from werkzeug.serving import run_simple
    views.SERVER_MODE = views.SERVER_MODES.DEBUG
    run_simple('localhost', views.DEBUG_PORT, views.make_dev_app(), use_reloader = True, use_debugger = True)
    
def run_cgi_server():
    from wsgiref.handlers import CGIHandler
    views.SERVER_MODE = views.SERVER_MODES.CGI
    with Debug():
        CGIHandler().run(views.make_cgi_app())
    
class Debug:
    def __init__(self):
        pass
        
    def __enter__(self):
        sys.stdout.flush(); sys.stderr.flush()
        self._stdout_orig = sys.stdout
        self._stderr_orig = sys.stderr
        sys.stdout = StringIO.StringIO()
        sys.stderr = StringIO.StringIO()
    
    def __exit__(self, e_type, e_value, e_tb):
        self._stdout_orig.flush(); self._stderr_orig.flush()
        stdout = sys.stdout.getvalue()
        stderr = sys.stderr.getvalue()
        sys.stdout.close(); sys.stderr.close()
        sys.stdout = self._stdout_orig
        sys.stderr = self._stderr_orig
        if e_type or stderr != '':
            stdout = re.sub('Content\-Length\:[ 0-9]*\r*\n', '', stdout)
            print stdout
#             print 'Status: 500 Internal Server Error\n'
            print 'CGI SERVER CAUGHT EXCEPTION:'
            if e_type:
                print '%s: %s' % (e_type.__name__, e_value)
                print 'TRACEBACK:'
                print '/n'.join(traceback.format_tb(e_tb)) 
            print '\n\n    STDERR:\n', stderr
        else:
            print stdout
            