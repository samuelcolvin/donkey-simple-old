#!/usr/bin/python

from distutils.core import setup

setup(name='DonkeySimple',
    version='0.1',
    description='Super Simple python system for building and deploying static websites',
    author='Samuel Colvin',
    author_email='S@muelColvin.com',
    url='http://www.scolvin.com',
    packages=['DonkeySimple', 'DonkeySimple.DS', 'DonkeySimple.WebInterface', 'DonkeySimple.CmdInterface'],
    package_data={'DonkeySimple': [
        'site-template/*.*',
        'site-template/static/*.*',
        'site-template/edit/*.*',
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
        'Jinja2 >= 2.7.2',
        'GitPython >= 0.3.2.RC1',
        'markdown2 >= 2.1.0'
    ],
)