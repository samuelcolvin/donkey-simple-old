import jinja2, os, cgi, re, httplib, traceback
import Cookie
import DonkeySimple.DS as ds
from _forms import ProcessForm, AnonFormProcessor
from _auth import Auth

sg = ds.SiteGenerator

THIS_PATH = os.path.dirname(os.path.realpath(__file__))
EDITOR_TEMPLATE_DIR = os.path.join(THIS_PATH, 'templates') 

urls = (
    ('logout$', 'logout'),
    ('add-page$', 'edit_page'),
    ('edit-page-last$', 'edit_last_page'),
    ('edit-page-(.+)$', 'edit_page'),
    ('add-template$', 'edit_template'),
    ('edit-template-(.+)$', 'edit_template'),
    ('add-static$', 'edit_static'),
    ('edit-static-(.+)$', 'edit_static'),
    ('add-user$', 'edit_user'),
    ('user$', 'edit_this_user'),
    ('edit-user-last$', 'edit_last_user'),
    ('edit-user-(.+)$', 'edit_user'),
    ('set-password-(.+)$', 'set_user_password'),
)

class View(object):
    user = None
    all_users = None
    cookie = ''
    content_type = 'content-type: text/html\n'
    location = ''
    response_code = ''
    page = ''
    
    def __init__(self,):
        self._msgs = {}
        self._env = jinja2.Environment(loader=jinja2.FileSystemLoader(EDITOR_TEMPLATE_DIR))
        uri = os.environ['REQUEST_URI']
        self._site_uri = uri[:uri.index('/edit/')]
        e_index = uri.index('/edit/') + 5
        self._site_edit_uri = uri[:e_index] + '/'
        self._edit_static_uri = join_uri(self._site_edit_uri, 'static/')
        fields = cgi.FieldStorage()
        valid_user = self._auth(fields)
        if valid_user:
            proc_form = ProcessForm(self._add_msg, fields, self.isadmin, self.username)
            if proc_form.regen_users:
                valid_user = self._auth(fields)
            self.created_item = proc_form.created_item
        else:
            AnonFormProcessor(self._add_msg, fields)
        self._generate_page(uri, loggedin = valid_user)
        
    def _generate_page(self, uri, loggedin = False):
        self.context = {'title': '%s Editor' % ds.SITE_NAME, 'static_uri': self._edit_static_uri, 
                   'edit_uri': self._site_edit_uri, 'site_uri': self._site_uri}
        if loggedin:
            self.context.update({'username': self.username, 'admin': self.user['admin']})
        self.context.update(ds.SETTINGS_DICT)
        self.context['repos'] = [r for r, _ in ds.con.get_all_repos()]
        print 'uri: %r' % uri
        if not loggedin:
            if 'reset-password' in uri:
                self.reset_password()
            else:
                self.login()
        else:
            found = False
            for reg, func in urls:
                m = re.search(reg, uri)
                if m:
                    found = True
                    fid = None
                    if len(m.regs) > 1:
                        fid = m.group(1)
                    getattr(self, func)(fid)
                    break
            if not found:
                if uri != self._site_edit_uri:
                    self._add_msg('%s not found' % uri, 'errors')
                self.index()
        self.context.update(self._msgs)
        if hasattr(self, '_template'):
            self.page = self._template.render(**self.context)
        
    def _auth(self, fields):
#         for name in fields:
#             print '%s:' % name, fields[name].value
        auth = Auth()
        if 'username' in fields and 'password' in fields:
            username = fields['username'].value
            password = fields['password'].value
            valid = auth.login(username, password)
        else:
            cookies = ''
            valid = False
            if 'HTTP_COOKIE' in os.environ:
                try: cookies = Cookie.SimpleCookie(os.environ["HTTP_COOKIE"])
                except: auth.msg = 'Error processing cookies'
            valid = auth.check_cookie(cookies)
        if not valid:
            if auth.msg not in ['', None]:
                self._add_msg(auth.msg, 'errors')
            return False
        C = Cookie.SimpleCookie()
        C[auth.cookie['name']] = auth.cookie['value']
        for name, value in auth.cookie['extra_values'].items():
            C[auth.cookie['name']][name] = value
        self.cookie = C.output()
        self.user = auth.user
        self.username = auth.username
        self.isadmin = self.user['admin']
        self.all_users = auth.users
#         self.o_usernames = auth.get_sorted_users()
        return True
        
    def login(self):
        self._template = self._env.get_template('login.html')
        self.context['title'] =  ds.SITE_NAME + ' login'
        self.context['reset_password'] = 'reset-password'
        
    def reset_password(self):
        self._template = self._env.get_template('reset_password.html')
        
    def logout(self, fid):
        auth = ds.Auth()
        auth.logout(self.username)
        self.location = 'Location: %s\n' % self._site_edit_uri
    
    def index(self):
        self._template = self._env.get_template('edit_index.html')
        page_con = ds.con.Pages()
        self.context['pages'] = []
        for cf in page_con.cfiles.values():
            self.context['pages'].append({'link': 'edit-page-%s' % cf.id, 'name': cf.display})
        self.context['templates'] = []
        t = ds.con.Templates()
        for cf in t.cfiles.values():
            self.context['templates'].append({'link': 'edit-template-%s' % cf.id, 'name': cf.display})
        self.context['static_files'] = []
        s = ds.con.Statics()
        for cf in s.cfiles.values():
            self.context['static_files'].append({'link': 'edit-static-%s' % cf.id, 'name': cf.display})
        if self.isadmin:
            self.context['users'] = []
            for u in self.all_users:
                self.context['users'].append({'link': 'edit-user-%s' % u, 'name': u})
    
    def edit_template(self, tid):
        self.context['help_statement'] = """
            <p>Template names should contain <span class="code">.template.</span> in their name, eg. <span class="code">my_template.template.html</span>.</p>
            <p>Templates are rendered using <a href="http://jinja.pocoo.org/docs/">Jinja2</a> which is a "Django like" template engine. See their site for Documentation.</p>
        """
        if tid is not None:
            t = ds.con.Templates()
            cfile, template_text = t.get_file_content(fid=tid)
            self.context['file_name'] = cfile.filename
            self.context['active_repo'] = cfile.repo
            self.context['file_text'] = cgi.escape(template_text)
        else:
            self.context['new_file'] = True
        self.context['action'] = 'edit-template'
        self.context['delete_action'] = 'delete-template'
        self._template = self._env.get_template('edit_file.html')
    
    def edit_static(self, sid):
        self.context['file_type'] = 'Text'
        if sid is not None:
            static = ds.con.Statics()
            cfile, content = static.get_file_content(fid=sid)
            self.context['file_name'] = cfile.filename
            self.context['file_id'] = cfile.id
            self.context['active_repo'] = cfile.repo
            self.context['file_type'] = static.get_file_type(self.context['file_name'])
            static_uri = join_uri(self._site_edit_uri, ds.REPOS_DIR, cfile.repo, static.DIR, cfile.filename)
            if self.context['file_type'] == 'Text':
                self.context['file_text'] = cgi.escape(content)
            elif self.context['file_type'] == 'Image':
                self.context['file_image_path'] = static_uri
            elif self.context['file_type'] == 'Font':
                self.context['font_path'] = static_uri
                self.context['font_name'] = get_font_name(static.get_path(cfile.repo, cfile.filename))
        else:
            self.context['new_file'] = True
        self.context['action'] = 'edit-static'
        self.context['delete_action'] = 'delete-static'
        self._template = self._env.get_template('edit_file.html')
    
    def edit_last_page(self, _):
        self.edit_page(self.created_item)
    
    def edit_page(self, pid):
        print 'pid:', pid
        t_con = ds.con.Templates()
        self.context['page_templates'] = t_con.cfiles.values()
        self.context['other_formats'] = ['markdown', 'html']
        self.context['action_uri'] = self._site_edit_uri + 'edit-page-last'
        if pid is not None:
            page_con = ds.con.Pages()
#             cfile = page_con.get_cfile_fid(pid)
            try:
                cfile = page_con.get_cfile_fid(pid)
            except:
                return self._error_occurred('Page not found', code=httplib.BAD_REQUEST)
            self.context['page_name'] = cfile.info['name']
            self.context['page_templates'] = [fc for fc in t_con.cfiles.values() if fc.repo == cfile.repo]
            self.context['page_context_str'] = []
            self.context['page_context_other'] = []
            for name, value in page_con.get_true_context().items():
                print name, value
                if value['type'] == 'string':
                    self.context['page_context_str'].append({'name': name, 'value': value['value'], 'type': value['type']})
                else:
                    self.context['page_context_other'].append({'name': name, 'value': cgi.escape(value['value']), 'type': value['type']})
            self.context['active_page_template_id'] = t_con.get_cfile_name(filename = cfile.info['template'], repo = cfile.repo).id
            self.context['action_uri'] = self.context['edit_uri']
        self._template = self._env.get_template('edit_page.html')
        
    def edit_last_user(self, _):
        uid = self.created_item
        self.edit_user(uid)
    
    def edit_this_user(self, uid):
        self.edit_user(self.username)
    
    def edit_user(self, uid):
        self.context['page_tag'] = 'New User'
        if not self.isadmin:
            if uid is None:
                return self._permission_denied()
            if uid != self.username:
                return self._permission_denied()
        self.context['action_uri'] = self._site_edit_uri + 'edit-user-last'
        if uid is not None:
            self.context['existing_user'] = True
            self.context['password_uri'] = self._site_edit_uri + 'set-password-%s' % uid
            edit_user = self.all_users[uid]
            self.context['page_tag'] = uid
            self.context['edit_email'] = edit_user['email']
            self.context['edit_username'] = uid
            self.context['is_admin'] = edit_user['admin']
            self.context['user_details'] = []
            if 'last_seen' in edit_user:
                self.context['user_details'].append({'name': 'Last Seen', 'value': edit_user['last_seen']})
            if 'created' in edit_user:
                self.context['user_details'].append({'name': 'Created', 'value': edit_user['created']})
                #self.context['user_details'].append({'name': 'Session Expires', 'value': user['session_expires']})
            self.context['action_uri'] = self.context['edit_uri']
        self._template = self._env.get_template('edit_user.html')
        
    def set_user_password(self, uid):
        edit_username = self.o_usernames[uid]
        if not self.isadmin and edit_username != self.username:
            return self._permission_denied()
        self.context['edit_username'] = edit_username
        self._template = self._env.get_template('set_password.html')
        
    def _permission_denied(self):
        self._bad('You do not have permission to view this page.', code=httplib.FORBIDDEN)
        
    def _error_occurred(self, e, code = httplib.INTERNAL_SERVER_ERROR):
        self._bad(str(e),error=e, code=code)
        
    def _bad(self, error_description, error = None, code = httplib.BAD_REQUEST):
        self.context['error'] = '%d %s' % (code, httplib.responses[code])
        self.response_code = 'Status: %s\n' % self.context['error']
        self.context['description'] = error_description
        if error:
            self.context['error_details'] = str(error)
            traceback.print_exc()
        self._template = self._env.get_template('bad.html')
    
    def _add_msg(self, msg, mtype='info'):
        if mtype not in self._msgs:
            self._msgs[mtype] = [msg]
        else:
            self._msgs[mtype].append(msg)
 
def get_font_name(filename):
    try:
        from fontTools import ttLib
        tt = ttLib.TTFont(filename)
        return tt['name'].names[1].string
    except Exception, e:
        print 'Problem processing font:', e
        return 'unknown'

def join_uri(*args):
    uri = '/' + '/'.join(p.strip('/') for p in args)
    if args[-1].endswith('/'):
        uri += '/'
    return uri
