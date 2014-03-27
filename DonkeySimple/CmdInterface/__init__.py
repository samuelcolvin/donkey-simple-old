import DonkeySimple.DS as ds
import os, json, imp, getpass
from DonkeySimple.DS.ds_creator import create_ds
from DonkeySimple.DS import KnownError

def get_status(path):
    """
    Prints the current state of the site.
    """
    _chdir(path)
    def print_list(title, values, indent = 2):
        print '%s%s:' % (' '*indent, title)
        new_indent = indent + 4
        for v in values:
            print ' '*new_indent, v
    def print_con(title, con, indent = 2):
        print_list(title, [cf.display for cf in con.cfiles.values()], indent)
    import settings
    print '  ================'
    print '  %s Status' % settings.SITE_NAME
    print '  ================'
    repros = [r for r, _ in ds.get_all_repos()]
    print_list('Repos', repros)
    print_con('Pages', ds.con.Pages())
    print_con('Templates', ds.con.Templates())
    print_con('Static Files', ds.con.Statics())
    
    if os.path.exists(ds.USERS_FILE):
        users = _get_users()
        user_info = []
        for user, info in users.items():
            admin = ('', ' (admin)')[info['admin']]
            user_info.append('%s%s, last seen: %s' % (user, admin, info['last_seen']))
        print_list('Web Interface Users', user_info)
    
def generate_site(path):
    _chdir(path)
    print '  ==============='
    print '  GENERATING SITE'
    print '  ==============='
    sg = ds.SiteGenerator()
    sg.generate_entire_site()
    print ''
    print '  Site Generated Successfully'
    print '  ---------------------------'
    
def runserver(path):
    _chdir(path)
    import DonkeySimple.WebInterface as wi
    wi.run_dev_server()
    
def edituser(path):
    _chdir(path)
    import DonkeySimple.WebInterface as wi
    users = _get_users()
    user_names = users.keys()
    print 'Users:'
    for i, u in enumerate(user_names):
        print '  %d: %s' % (i, u)
    username = user_names[int(raw_input('Choose user id: '))]
    print 'User: %s' % username
    user = users[username]
    for k,v in user.items():
        print '  %s: %r' % (k, v)
    print 'Actions:'
    actions = ['enter new password', 
               'reset password and print', 
               'reset password and email', 
               'cancel']
    for i, a in enumerate(actions):
        print '  %d: %s' % (i, a)
    action = actions[int(raw_input('Choose Action: '))]
    print 'Action: %s' % action
    if action == 'enter new password':
        pw1 = getpass.getpass('Enter new password: ')
        pw2 = getpass.getpass('Repeat: ')
        if pw1 != pw2:
            raise KnownError('Passwords do not match')
        pw = pw1
        if len(pw) < ds.MIN_PASSWORD_LENGTH:
            raise KnownError('Password must be at least %d characters in length' % ds.MIN_PASSWORD_LENGTH)
        auth = wi.UserAuth()
        user = auth.pop_user(username)
        auth.add_user(username, user, pw)
        print 'Password Changed'
    elif action in ['reset password and print', 'reset password and email']:
        auth = wi.UserAuth()
        user = auth.pop_user(username)
        pw = auth.new_random_password()
        if action == 'reset password and print':
            print 'new password: %s' % pw
            auth.add_user(username, user, pw)
        else:
            email = user['email']
            if '@' in email:
                from DonkeySimple.DS.send_emails import password_email
                success, msg = password_email(email, 'the site', username, pw)
                if success:
                    auth.add_user(username, user, pw)
                    print 'Password email sent'
                else:
                    raise KnownError('Error sending email, not changing password')

def _get_users():
    with open(ds.USERS_FILE, 'r') as handle:
        users = json.load(handle)
    return users 

def _chdir(path):
    def find_path():
        look_for = ('index.cgi', 'settings.py')
        if path is None:
            search_dirs = ('edit', '.', '..', '../..', '../../..')
            for d in search_dirs:
                if all([os.path.exists(os.path.join(d,f)) for f in look_for]):
                    return d
        else:
            if not all([os.path.exists(os.path.join(path,f)) for f in look_for]):
                raise KnownError(
                'Path supplied "%s" does not appear to be the "edit" folder of a donkey simple site tree.'\
                % path)
            return path
        raise KnownError("No path supplied and you don't appear to be in a site tree now.")
    
    new_path = find_path()
    if new_path != '.':
        print 'changing working directory to "%s"' % new_path
        os.chdir(new_path)
    return new_path


