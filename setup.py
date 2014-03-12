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
        'static_libraries.json',
        'site-template/*.*',
        'site-template/static/*.*',
        'site-template/edit/*.*',
        'site-template/edit/repos/default/pages/*.*',
        'site-template/edit/repos/default/static/*.*',
        'site-template/edit/repos/default/templates/*.*',
      ],
      'DonkeySimple.WebInterface':[
        'templates/*.*',
      ]},
      scripts=['DonkeySimple/bin/donkeysimple']
)