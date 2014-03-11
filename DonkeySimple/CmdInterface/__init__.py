import DonkeySimple.DS as ds
from DonkeySimple.WebInterface import Auth 

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
    print '  =============='
    print '      STATUS'
    print '  =============='
    repros = [r for r, _ in ds.con.get_all_repos()]
    print_list('Repos', repros)
    print_con('Pages', ds.con.Pages())
    print_con('Templates', ds.con.Templates())
    print_con('Static Files', ds.con.Statics())
    auth = Auth()
    print_list('Web Interface Users', auth.users)
    