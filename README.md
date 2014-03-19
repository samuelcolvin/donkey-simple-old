Donkey Simple
=============

Copyright (C) 2013-2014 [Samuel Colvin](http://www.scolvin.com) <S@muelColvin.com>

License: The MIT License (MIT)

Donkey Simple is an extremely simple CMS that allows you to build a static website either from a web interface or the command line.

It uses clever tools like [Ace Code Editor](http://ace.c9.io/), [Markdown](http://daringfireball.net/projects/markdown/) and [Jinja2](http://jinja.pocoo.org/) to make writing the site as painless as possible. 

The pages, templates, static files and config files which make up the site are stored in a git repository so you can easily manage the version history of your site.

Once you've written your site, it is generated **ONCE** and then saved as static files, meaning the site is **FAST**, **REALLY FAST** in a way dynamic sites build from templates using lots of database calls and slow interpretted languages so rarely are.

DonkeySimple was built to work with Apache (it comes with .htaccess files) but it should be extremely simple to use it with other server. Similarly it has only been tested on Linux and Mac OS, however there's nothing fundamental to stop it running on windows.

View the code and download it at [https://github.com/samuelcolvin/donkey-simple](https://github.com/samuelcolvin/donkey-simple). Donkey Simple is available through PyPi [here](https://pypi.python.org/pypi/DonkeySimple/).

### Documentation

(These docs assume you're setting up Donkey Simple to work with Apache on Ubuntu, but they should give you the gist of the process on other linux variants and Mac OS, even Windows and other web servers (like nginx and lighttpd) shouldn't be that different.)

To Install run:

    sudo pip install DonkeySimple
    
You should then be able to use the command line utility `donkeysimple`.

To build a new site run

    donkeysimple build my_new_site
    
which will create a new site template at `working/directory/my_new_site`. Eg. you might think of running this command from `/var/www/home/` to create `/var/www/my_new_site`.

(More details on what the donkeysimple utility can do can be found by running `donkeysimpl --help`.)

At this stage you might think about changing the password for the default user, you can do this by going into `my_new_site` and running.

    donkeysimple edituser

The only remaining step is to setup apache to work with this directory. I won't go into details of setting up an apache site, the only "special" thing you need to do is enable `.htaccess` files, there are details [here](https://help.ubuntu.com/community/EnablingUseOfApacheHtaccessFiles) but basically just need something like

    <Directory /var/www/home/my_new_site>
        AllowOverride All
    </Directory>

You should then be able to go to the site at http://ww.example.com/my_new_site to see the default site and http://ww.example.com/my_new_site/edit to login and start building your site.

### Building (You can Probably ignore this)

If you download the source (eg. from github as opposed to installing with pip) you should run `python mini_build.py` prior to installing. All this does is download the static files for the web interface and generate the docs.txt file for PyPi's `long_description`, for this you will require pandoc and pyandoc.
