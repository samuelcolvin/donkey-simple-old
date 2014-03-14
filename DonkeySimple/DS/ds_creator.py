import shutil, os
import _controllers as con
from random_string import get_random_string

def create_ds(path):
    if os.path.exists(path):
        if len(os.listdir(path)) != 0:
            raise Exception('Path "%s" already exists and is not empty, please specify a new or empty path' % path)
        else:
            os.rmdir(path)
    this_dir = os.path.dirname(os.path.realpath(__file__))
    site_template = os.path.realpath(os.path.join(this_dir, '../site-template'))
    shutil.copytree(site_template, path)
    full_path = os.path.realpath(path)
    print 'Site template copied'
    print 'Generating short random variable for cookies...'
    settings_file = os.path.join(path, 'edit', 'settings.py')
    text = open(settings_file, 'r').read()
    random_text = get_random_string(8)
    text = text.replace('short_random_var', random_text)
    open(settings_file, 'w').write(text)
    print 'Changing files to replicate owner permissions for all'
    con.repeat_owners_permission(path)
    print '==========================='
    print 'SITE GENERATED SUCCESSFULLY'
    print '==========================='
    print 'location: %s' % full_path
    print 'default username: donkey, password: simple'
    print 'run "donkeysimple edituser" to change the password, or login and change.'