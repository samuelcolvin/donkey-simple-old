#!/usr/bin/python
    
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

response = 'content-type: text/html\n\n'

import traceback, sys, StringIO
debug = Debug()
try:
    from web_interface import WebInterface 
    import ds
    debug.active = ds.DEBUG
    wi = WebInterface()
    response += wi.page
     
except Exception, e:
    debug.finish_debugging()
    print 'content-type: text/plain\n\n'
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
    print debug.html


