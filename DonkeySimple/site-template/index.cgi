#!/usr/bin/python
"""
CGI file, only for serving Donkey Simple as a cgi application.
For a simple server, run "donkeysimple runserver".
You Shouldn't have to change anything, for settings look in settings.py
"""
try:
    import DonkeySimple.WebInterface
except:
    print 'Status: 500 Internal Server Error\n\nERROR IMPORTING DonkeySimple.WebInterface'
    print 'check DonkeySimple is installed'
else:
    DonkeySimple.WebInterface.run_cgi_server()