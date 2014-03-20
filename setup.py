#!/usr/bin/python

from DonkeySimple.DS.download import download_libraries
import os, re

lib_static_dir = os.path.join('DonkeySimple', 'WebInterface', 'static', 'libs')
libs_json_path = 'static_libraries.json'
try:
    download_libraries(libs_json_path, lib_static_dir)
except Exception, e:
    print 'ERROR: %s' % str(e)
    print 'Problem downloading libraries, you may have problems with internet connection.\n\n'
    
print 'generating long_descriptions docs for PyPi...'
import pandoc
pandoc.core.PANDOC_PATH = '/usr/bin/pandoc'
doc = pandoc.Document()
readme_file = 'README.md'
doc.markdown = open(readme_file, 'r').read()
docs_file = 'DonkeySimple/docs.txt'
open(docs_file,'w').write(doc.rst)
print '%s converted to rst and written to %s' % (readme_file, docs_file)
print 'changing version number'
setup_text = open('setup.py','r').read()
s=re.search("version='(.+?)'", setup_text)
v = s.groups()[0]
print 'setting version to: %s' % v
init_file = 'DonkeySimple/__init__.py'
init_text = "__version__ = 'v%s'\n" % v
open(init_file,'w').write(init_text)

from setuptools import setup


with open('DonkeySimple/docs.txt') as file:
    long_description = file.read()

setup(name='DonkeySimple',
    version='0.17',
    description='Super Simple python system for building and deploying static websites',
    long_description=long_description,
    author='Samuel Colvin',
    license='MIT',
    author_email='S@muelColvin.com',
    url='https://github.com/samuelcolvin/donkey-simple',
    packages=['DonkeySimple', 'DonkeySimple.DS', 'DonkeySimple.WebInterface', 'DonkeySimple.CmdInterface'],
    zip_safe=False,
    platforms='any',
    package_data={'DonkeySimple': [
        'docs.txt',
        'site-template/edit/index.cgi',
        'site-template/edit/users.json',
        'site-template/edit/settings.py',
        'site-template/edit/.htaccess',
        'site-template/edit/repos/default/*.*',
        'site-template/edit/repos/default/pages/*.*',
        'site-template/edit/repos/default/static/*.*',
        'site-template/edit/repos/default/templates/*.*',
    ],
        'DonkeySimple.WebInterface':[
        'templates/*.*',
        'static/*.*',
        'static/libs/*.*',
        'static/libs/ace/*.*',
    ]},
    scripts=['DonkeySimple/bin/donkeysimple'],
    install_requires=[
        'Jinja2>=2.7.2',
        'GitPython>=0.3.2.RC1',
        'markdown2>=2.1.0'
    ],
)