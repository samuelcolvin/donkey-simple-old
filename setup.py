#!/usr/bin/python

from setuptools import setup


with open('DonkeySimple/docs.txt') as file:
    long_description = file.read()

setup(name='DonkeySimple',
    version='0.15',
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
        'site-template/*.*',
        'site-template/.htaccess',
        'site-template/static/*.*',
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