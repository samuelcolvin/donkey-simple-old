donkey-simple
=============

Super simple site manager that provides a front end to generate static websites

To do:

* allow change of template for pages - DONE
* check correct mode is used by ace for markdown and html - DONE
* fix markdown/html rendering based on dropdown - DONE
* add static files - upload, move into place - DONE
* allow editing of static files- DONE
* get pull and push to git working - DONE
* Sitemap, add sitemap ranking to pages, and extension field to pages - DONE
* "clear and download libraries" button so generate only downloads new libs, .gitignore file for repos - DONE
* fix ace find & replace box problems from bootstrap - DONE
* global variables eg author, title, checkbox for override on pages - DONE
* get "override global" working for ace editors - DONE
* global vars to include static-dir, list of pages etc. - DONE
* global vars to allow lists for menus (or pages to include tags: http://aehlke.github.io/tag-it/ ?)
* link generation (link to a specific page), static-dir tag - DONE
* static file compression and organising
* JSON editor in pages for lists etc.
* JSON editor mode
* allow pages to use template from different repo (save repo in page) - DONE
* library static files should be downloaded (implement zip bit) - DONE
* static library file webinterface - DONE
* add fields to page if template has changed - DONE
* python sessions, user management and site settings - DONE
* download zip of site - DONE
* download zip of repos - DONE
* build script - DONE
* check install_requires in setup.py - DONE
* think about multiple repos for templates directory - DONE
* catch ctrl+s and save - DONE
* list global variables on templates page - DONE
* save and keep editting, undo - DONE
* generate on save - DONE

* ignore dict and list variables in pages - DONE
* add "donkysimple not installed message on ImportError: No module named DonkeySimple.WebInterface" - DONE
* this_page variable on page - DONE
* site index variable - DONE
* page not found page pointed to by htaccess: "ErrorDocument 404 /notfound.html" - DONE
* deal with "TemplateNotFound" error after deleting template - DONE
* deal with "UnicodeDecodeError: 'ascii' codec can't decode byte 0xe2 in position 56: ordinal not in range(128) - DONE?
* make errors visible on save & generate (eg. template errors) - DONE
* set owner permissions for all for .git folder - DONE
* solve display of static png or ttf files - DONE
* get global variable "index" from settings if not directly available (eg. in command line)

* add docs - DONE
* generate docs.txt from README.md - DONE
* change donkeysimple utility to point out you need to be inside the site to run edituser - DONE
* make sure index.cgi has execute permissions - DONE