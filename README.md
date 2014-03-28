Donkey Simple
=============

Copyright (C) 2013-2014 [Samuel Colvin](http://www.scolvin.com) <S@muelColvin.com>

License: The MIT License (MIT)

Donkey Simple is an extremely simple platform for building static websites either from a web interface or the command line.

It uses [Werkzeug](http://werkzeug.pocoo.org/), [Jinja2](http://jinja.pocoo.org/), [Ace Code Editor](http://ace.c9.io/) and [Markdown](http://daringfireball.net/projects/markdown/) to make writing the site as painless as possible. 

The pages, templates, static files and config files which make up the site are stored in a git repository so you can easily manage the version history of your site.

Once you've written your site, it is generated **ONCE** and then saved as static files, meaning the site is **FAST**, **REALLY FAST** in a way dynamic sites build from templates using lots of database calls and slow interpretted languages so rarely are.

DonkeySimple was built to work with Apache (it comes with .htaccess files) but it should be extremely simple to use it with other server. Similarly it has only been tested on Linux and Mac OS, however there's nothing fundamental to stop it running on windows.

View the code and download it at [github.com/samuelcolvin/donkey-simple](https://github.com/samuelcolvin/donkey-simple). Donkey Simple is available through PyPi [pypi.python.org/pypi/DonkeySimple](https://pypi.python.org/pypi/DonkeySimple/).

### Quick Start

    sudo pip install DonkeySimple
    donkeysimple create my_new_site
    cd ./my_new_site
    donkeysimple runserver
    # go to localhost:4000

Then edit `./my_new_site/settings.py`.

If you're running this on a server **set REQUIRE_AUTH = True** and **change your username/password** from the defaults: donkey/simple.

### Documentation

(These docs assume you're setting up Donkey Simple to work with Apache on Ubuntu, but they should give you the gist of the process on other linux variants and Mac OS, even Windows and other web servers (like nginx and lighttpd) shouldn't be that different. However you might have problems with windows paths.)

To Install run:

    [sudpo] pip install DonkeySimple
    
You should then be able to use the command line utility `donkeysimple`, to show options:

    donkeysimple --help

To build a new site run

    donkeysimple create my_new_site
    
which will create a new site template at `working/directory/my_new_site`. Eg. you might think of running this command from `/var/www/home/` to create `/var/www/my_new_site`.

(More details on what the donkeysimple utility can do can be found by running `donkeysimple --help`.)

You can then use the system on a dev server by running

    donkeysimple runserver

from within the new site directory.

You might also think about changing the password for the default user, you can do this by going into `my_new_site` and running.

    donkeysimple edituser
    
Once you've run "generate site" you can host the resulting site anywhere.

To host the donkey simple web interface is only a little more complicated, it's a standard Werkzeug application so it can run via cgi, wsgi or the dev server as above.

Example `.htaccess` are generated on `create` (see above).

### Building (You can probably ignore this)

If you download the source (eg. from github as opposed to installing with pip) you should run `python mini_build.py` prior to installing. All this does is download the static files for the web interface and generate the docs.txt file for PyPi's `long_description`, for this you will require pandoc and pyandoc.
