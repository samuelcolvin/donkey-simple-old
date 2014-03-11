import DonkeySimple.DS as ds
import os, json, imp

def get_status():
    """
    Prints the current state of the site.
    """
    def print_list(title, values, indent = 2):
        print '%s%s:' % (' '*indent, title)
        new_indent = indent + 4
        for v in values:
            print ' '*new_indent, v
    def print_con(title, con, indent = 2):
        print_list(title, [cf.display for cf in con.cfiles.values()], indent)
    print os.getcwd()
    try:
        settings = imp.load_source('settings', ds.SETTINGS_FILE)
    except Exception, e:
        raise Exception('Error importing %s: %r' % (ds.SETTINGS_FILE, e))
    import settings
    
    print '  ================'
    print '  %s STATUS' % settings.SITE_NAME
    print '  ================'
    repros = [r for r, _ in ds.con.get_all_repos()]
    print_list('Repos', repros)
    print_con('Pages', ds.con.Pages())
    print_con('Templates', ds.con.Templates())
    print_con('Static Files', ds.con.Statics())
    
    if os.path.exists(ds.USERS_FILE):
        with open(ds.USERS_FILE, 'r') as handle:
            users = json.load(handle)
        print_list('Web Interface Users', users.keys())
    
def generate_site():
    print '  ================'
    print '  GENERATING SITE'
    print '  ================'
    sg = ds.SiteGenerator()
    sg.generate_entire_site()
    print ''
    print '  Site Generated Successfully'
    print '  ---------------------------'


        
def chdir(default_path, path):
    def find_path():
        look_for = ('index.cgi', 'settings.py')
        if path != default_path:
            if not all([os.path.exists(os.path.join(path,f)) for f in look_for]):
                raise Exception(
                'Path supplied "%s" does not appear to be the "edit" folder of a donkey simple site tree.'\
                % path)
            return path
        else:
            search_dirs = ('edit', '.', '..', '../..', '../../..')
            for d in search_dirs:
                if all([os.path.exists(os.path.join(d,f)) for f in look_for]):
                    return d
        raise Exception("No path supplied and you don't appear to be in a site tree now.")
    
    
    new_path = find_path()
    if new_path != '.':
        print 'changing working directory to "%s"' % new_path
        os.chdir(new_path)
    return new_path


