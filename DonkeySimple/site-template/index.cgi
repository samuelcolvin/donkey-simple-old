#!/usr/bin/python
"""
CGI file, only for serving Donkey Simple as a cgi application.
For a simple server, run "donkeysimple runserver".
You Shouldn't have to change anything, for settings look in settings.py
"""

import DonkeySimple.WebInterface
DonkeySimple.WebInterface.run_cgi_server()