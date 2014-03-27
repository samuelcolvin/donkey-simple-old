#!/usr/bin/python

from DonkeySimple.DS.download import download_libraries
import os, re

from setuptools import setup

with open('DonkeySimple/docs.txt') as file:
    long_description = file.read()

setup(name='DonkeySimple',
    version='0.20',
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
        'site-template/index.cgi',
        'site-template/users.json',
        'site-template/settings.py',
        'site-template/*.htaccess',
        'site-template/repos/default/*.*',
        'site-template/repos/default/pages/*.*',
        'site-template/repos/default/static/*.*',
        'site-template/repos/default/templates/*.*',
        'site-template/repos/builtin/*.*',
        'site-template/repos/builtin/pages/*.*',
        'site-template/repos/builtin/static/*.*',
        'site-template/repos/builtin/templates/*.*',
    ],
        'DonkeySimple.WebInterface':[
        'templates/*.*',
        'static/*.*',
        'static/libs/*.*',
        'static/libs/ace/*.*',
    ]},
    scripts=['DonkeySimple/bin/donkeysimple'],
    install_requires=[
        'Werkzeug>=0.9.4',
        'Jinja2>=2.7.2',
        'GitPython>=0.3.2.RC1',
        'markdown2>=2.1.0',
#         'FontTools>=2.4' (requires numpy so not required)
    ],
)