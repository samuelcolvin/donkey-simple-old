import shutil, os, subprocess
import _controllers as con
from _site_generator import SiteGenerator
from random_string import get_random_string

from _common import KnownError, shell_path

def create_ds(path):
    if os.path.exists(path):
        if len(os.listdir(path)) != 0:
            raise KnownError('Path "%s" already exists and is not empty, please specify a new or empty path' % path)
        else:
            os.rmdir(path)
    this_dir = os.path.dirname(os.path.realpath(__file__))
    ds_root = os.path.realpath(os.path.join(this_dir, '..'))
    site_template = os.path.join(ds_root, 'site-template')
    shutil.copytree(site_template, path)
    print '\n\nSite template copied'
    old_edit_path = os.path.join('path', 'edit')
    if os.path.exists(old_edit_path):
        print 'found old edit folder in new site, this is left over from previous DS install, deleting it...'
        shutil.rmtree(old_edit_path)
    print 'Generating short random variable for cookies...'
    settings_file = os.path.join(path, 'settings.py')
    text = open(settings_file, 'r').read()
    random_text = get_random_string(20)
    text = text.replace('random_var_created_on_build', random_text)
    open(settings_file, 'w').write(text)
    print 'Changing files to replicate owner permissions for all...'
    con.repeat_owners_permission(path)
    cgi_path = os.path.join(path, 'index.cgi')
    con.chmod_own(cgi_path, 0777)
    true_static_path = os.path.join(ds_root, 'WebInterface', 'static')
    static_link = os.path.join(path, 'static')
    print 'Creating static file link...'
    command = 'ln -s %s %s' % (shell_path(true_static_path), shell_path(static_link))
    subprocess.check_call(command, shell=True)
#     print 'Generating default site...'
#     os.chdir(path)
#     sg = SiteGenerator()
#     sg.generate_entire_site()
    print 'default username: donkey, password: simple **You Should Change These**'
    print '========================='
    print 'SITE CREATED SUCCESSFULLY @ "./%s"' % path
    print '========================='