#!/usr/bin/python

response = 'content-type: text/html\n\n'

try:
    import ds, traceback
    wi = ds.WebInterface()
    response += wi.base_page()
     
except Exception, e:
    print 'content-type: text/plain\n\n'
    print 'EXCEPTION OCCURRED:'
    print e
    try:
        traceback.print_exc()
    except:
        pass
    
    print 'RESPONSE:\n', response
    
else:
    print response


