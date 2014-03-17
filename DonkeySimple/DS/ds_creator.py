import shutil, os, subprocess
import _controllers as con
from _site_generator import SiteGenerator
from random_string import get_random_string

def create_ds(path):
    if os.path.exists(path):
        if len(os.listdir(path)) != 0:
            raise Exception('Path "%s" already exists and is not empty, please specify a new or empty path' % path)
        else:
            os.rmdir(path)
    this_dir = os.path.dirname(os.path.realpath(__file__))
    ds_root = os.path.realpath(os.path.join(this_dir, '..'))
    site_template = os.path.join(ds_root, 'site-template')
    shutil.copytree(site_template, path)
    full_path = os.path.realpath(path)
    print 'Site template copied'
    print 'Generating short random variable for cookies...'
    settings_file = os.path.join(path, 'edit', 'settings.py')
    text = open(settings_file, 'r').read()
    random_text = get_random_string(8)
    text = text.replace('short_random_var', random_text)
    open(settings_file, 'w').write(text)
    print 'Changing files to replicate owner permissions for all...'
    con.repeat_owners_permission(path)
    edit_path = os.path.join(path, 'edit')
    cgi_path = os.path.join(edit_path, 'index.cgi')
    con.chmod_own(cgi_path, 0777)
    true_static_path = os.path.join(ds_root, 'WebInterface', 'static')
    static_link = os.path.join(path, 'edit', 'static')
    print 'Creating static file link...'
    subprocess.call('ln -s %s %s' % (true_static_path, static_link), shell=True)
    print 'Generating default site...'
    os.chdir(edit_path)
    print os.getcwd()
    sg = SiteGenerator()
    sg.generate_entire_site()
    print '==========================='
    print 'SITE GENERATED SUCCESSFULLY'
    print '==========================='
    print 'location: %s' % full_path
    print 'default username: donkey, password: simple'
    print 'run "donkeysimple edituser" from inside the site directory to change the password, or login and change.'