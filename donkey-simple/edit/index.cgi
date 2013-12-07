#!/usr/bin/python
    
class Debug:
    _text = ''
    def __init__(self, active):
        self._active = active
    
    def write_line(self, *args):
        self._write(' ', *args)
        self._text += '\n'

    def write_lines(self, *args):
        self._write('\n', *args)
        
    def _write(self, split, *args):
        for arg in args:
            self._text += '%s%s' % (str(arg), split)
        
    @property
    def html(self):
        if self._text.strip('\r\t\n ') == '' or not self._active:
            return ''
        try:
            import cgi
            self._text = cgi.escape(self._text)
        except:
            pass
        return '<div class="container"><h4>Debug Output:</h4>\n<pre><code>\n%s\n</code></pre></div>' % self._text
    
    @property
    def text(self):
        if not self._active:
            return ''
        return 'DEBUG:\n%s' % self._text

response = 'content-type: text/html\n\n'

try:
    import traceback, sys
    import ds
    debugger = Debug(ds.DEBUG)
    wi = ds.WebInterface(debugger)
    response += wi.page
     
except Exception, e:
    print 'content-type: text/plain\n\n'
    print 'EXCEPTION OCCURRED:'
    print e
    try:
        traceback.print_exc(file=sys.stdout)
    except:
        pass
    
    print 'RESPONSE:\n', response
    try: print debugger.text
    except: pass
    
else:
    print response
    print debugger.html


