#!/usr/bin/python
"""
This is the recieving script for all page requests to the donkeys simple edit site.

You Shouldn't have to change anything in here unless there is a bug, for settings look in settings.py
"""
import sys, traceback, StringIO

class Debug:
    _text = ''
    _finished = False
    def __init__(self):
        self.active = True
        self._stdout_original = sys.stdout
        sys.stdout = StringIO.StringIO()
    
    def finish_debugging(self):
        if not self._finished:
            self._text = sys.stdout.getvalue()
            sys.stdout.close()
            sys.stdout = self._stdout_original
            self._finished = True
        
    @property
    def html(self):
        if self._text.strip('\r\t\n ') == '' or not self.active:
            return ''
        try:
            import cgi
            self._text = cgi.escape(self._text)
        except:
            pass
        return '<div class="container"><h4>Debug Output:</h4>\n<pre><code>%s\n</code></pre></div>' % self._text.strip('\r\t\n ')
    
    @property
    def text(self):
        if not self.active:
            return ''
        return 'DEBUG OUTPUT:\n%s' % self._text.strip('\r\t\n ')

debug = Debug()
response = ''
try:
    from DonkeySimple.WebInterface import View 
    import DonkeySimple.DS as ds
    import settings
    debug.active = settings.DEBUG
    wi = View()
    response = wi.response_code
    response += wi.location
    response += wi.content_type
    response += wi.cookie
    response += '\n\n'
    response += wi.page
    show_debug = 'html' in wi.content_type
except Exception, e:
    debug.finish_debugging()
    print 'Status: 500 Internal Server Error\n'
    print 'EXCEPTION OCCURRED:'
    print e
    try:
        traceback.print_exc(file=sys.stdout)
    except:
        pass
    try: print debug.text
    except Exception,e: print 'DEBUG ERROR:', e
    print 'RESPONSE:\n', response
else:
    debug.finish_debugging()
    print response
    if show_debug:
        print debug.html


