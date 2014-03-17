import jinja2, os, cgi, re, httplib, traceback
import Cookie
import DonkeySimple.DS as ds
from _forms import ProcessForm, AnonFormProcessor
from _auth import Auth
import settings

sg = ds.SiteGenerator

THIS_PATH = os.path.dirname(os.path.realpath(__file__))
EDITOR_TEMPLATE_DIR = os.path.join(THIS_PATH, 'templates') 

static_urls = ('static/(.+)$', 'static_file')
urls = (
    ('logout$', 'logout'),
    static_urls,
    ('add-repo', 'edit_repo'),
    ('view-repo-(.+)$', 'view_repo'),
    ('add-page$', 'edit_page'),
    ('edit-page-last$', 'edit_last_page'),
    ('edit-page-(.+)$', 'edit_page'),
    ('add-template$', 'edit_template'),
    ('edit-template-(.+)$', 'edit_template'),
    ('add-static$', 'edit_static'),
    ('edit-static-(.+)$', 'edit_static'),
    ('add-libfile', 'edit_libfile'),
    ('edit-libfile-(.+)$', 'edit_libfile'),
    ('add-globcon', 'edit_globcon'),
    ('edit-globcon-(.+)$', 'edit_globcon'),
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
        print 'site_uri:', self._site_uri
        e_index = uri.index('/edit/') + 5
        self._site_edit_uri = uri[:e_index] + '/'
        self._edit_static_uri = join_uri(self._site_edit_uri, 'static/')
        fields = cgi.FieldStorage()
        valid_user = self._auth(fields)
        processing_error = None
        try:
            if valid_user:
                proc_form = ProcessForm(self._add_msg, fields, self.isadmin, self.username)
                if proc_form.regen_users:
                    valid_user = self._auth(fields)
                self.created_item = proc_form.created_item
            else:
                AnonFormProcessor(self._add_msg, fields)
        except Exception, e:
            processing_error = e
        self._generate_page(uri, loggedin = valid_user, error = processing_error)
        
    def _generate_page(self, uri, loggedin = False, error = None):
        self.context = {'title': '%s Editor' % settings.SITE_NAME, 'site_name': settings.SITE_NAME, 'site_title': '%s Editor' % settings.SITE_NAME, 
                        'static_uri': self._edit_static_uri, 'edit_uri': self._site_edit_uri,
                        'site_uri': self._site_uri}
        if loggedin:
            self.context.update({'username': self.username, 'admin': self.user['admin']})
        self.repo_paths = list(ds.get_all_repos())
        self.context['repos'] = [r for r, _ in self.repo_paths]
        if len(self.context['repos']) == 0:
            self._add_msg('REPOS directory is empty: there are no repos, pages, templates or static files')
        print 'uri: %r' % uri
        if error:
            self._error_page(error, code = httplib.BAD_REQUEST)
        elif not loggedin:
            if 'reset-password' in uri:
                self.reset_password()
            else:
                # currently unused as static files are handled with a symlink:
#                 m = re.search(static_urls[0], uri)
#                 if m:
#                     self.static_file(m.group(1))
#                 else:
#                     self.login()
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
        if hasattr(self, '_static_file'):
            self.page = self._static_file
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
    
    def static_file(self, uri_path):
        """
        Render a static file from within the installed directory
        having made sure the path is inside static.
        
        Currently unused as static files are handled with a symlink
        for performance reasons (serving static files using cgi is a bit
        mad and predicably slow).
        """
        this_dir = os.path.dirname(os.path.realpath(__file__))
        uri_path = uri_path.strip(' ?')
        name = os.path.basename(uri_path)
        d = ''
        if os.path.dirname(uri_path).endswith('libs/ace'):
            d = 'libs/ace'
        elif os.path.dirname(uri_path).endswith('libs'):
            d = 'libs'
        path = os.path.join(this_dir, 'static', d, name)
#         print path
        if os.path.exists(path):
            if path.endswith('.css'):
                self.content_type = 'content-type: text/css\n'
            if path.endswith('.js'):
                self.content_type = 'content-type: text/javascript\n'
            self._static_file =open(path, 'r').read()
        else:
            self._page_not_found()
        
    def login(self):
        self._template = self._env.get_template('login.html')
        self.context['title'] =  settings.SITE_NAME + ' login'
        self.context['reset_password'] = 'reset-password'
        
    def reset_password(self):
        self._template = self._env.get_template('reset_password.html')
        
    def logout(self, fid):
        auth = Auth()
        auth.logout(self.username)
        self.location = 'Location: %s\n' % self._site_edit_uri
    
    def index(self):
        self._template = self._env.get_template('index.html')
        try:
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
            self.context['library_files'] = []
            s = ds.con.LibraryFiles()
            for cf in s.cfiles.values():
                self.context['library_files'].append({'link': 'edit-libfile-%s' % cf.id, 'name': cf.display})
            self.context['globcon_files'] = []
            gc = ds.con.GlobConFiles()
            for cf in gc.cfiles.values():
                self.context['globcon_files'].append({'link': 'edit-globcon-%s' % cf.id, 'name': cf.display})
            if self.isadmin:
                self.context['users'] = []
                for u in self.all_users:
                    self.context['users'].append({'link': 'edit-user-%s' % u, 'name': u})
        except Exception, e:
            return self._error_page(e)
        
    def view_repo(self, repo_name):
        self.context['repo_name'] = repo_name
        self.context['title'] = repo_name
        self.context['action_uri'] = self._site_edit_uri + 'view-repo-' + repo_name
        
        repo_path = (p for r, p in self.repo_paths if r == repo_name).next()
        git_repo = ds.Git(repo_path)
        if not git_repo.open_create():
            self._add_msg('Repo created from scratch')
        
        self.context['has_remotes'] = git_repo.has_remotes()
        if not self.context['has_remotes']:
            self._add_msg('Repo has no Remotes. To add one, run "git remote add origin &lt;giturl&gt;"')
        self.context['untracked_files'] = git_repo.untracked_files()
        self.context['modified_files'] = git_repo.modified_files()
        self.context['tracked_files'] = git_repo.tracked_files()
        self.context['status'] = git_repo.status()
        if git_repo.uptodate(self.context['status']):
            self._add_msg('Repo is up-to-date')
        else:
            self._add_msg('Repo not up-to-date', 'errors')
        self._template = self._env.get_template('repos.html')
    
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
            try:
                cfile = page_con.get_cfile_fid(pid)
            except:
                return self._error_page('Page not found', code=httplib.BAD_REQUEST)
            self.context['page_name'] = cfile.info['name']
            if 'sitemap' in cfile.info:
                self.context['sitemap'] = cfile.info['sitemap']
            if 'extension' in cfile.info:
                self.context['extension'] = cfile.info['extension']
            self.context['page_templates'] = t_con.cfiles.values()
            self.context['page_context_str'] = []
            self.context['page_context_other'] = []
            global_context = ds.SiteGenerator().global_context()
            for name, value in page_con.get_true_context().items():
                override = True
                global_var = name in global_context
                if value['value'] == None:
                    value['value'] = ''
                    if global_var:
                        override = False
                con_settings = {'name': name, 
                                'value': value['value'], 
                                'type': value['type'], 
                                'override': override,
                                'global_var': global_var}
                if value['type'] == 'string':
                    self.context['page_context_str'].append(con_settings)
                else:
                    con_settings['value'] = cgi.escape(value['value'])
                    self.context['page_context_other'].append(con_settings)
            self.context['active_page_template_id'] = t_con.get_cfile_name(name = cfile.info['template'], repo = cfile.info['template_repo']).id
            self.context['action_uri'] = self.context['edit_uri']
        self._template = self._env.get_template('edit_page.html')
    
    def edit_template(self, tid):
        self.context['help_statement'] = """
            <p>Template names should contain <span class="code">.template.</span> in their name, eg. <span class="code">my_template.template.html</span>.</p>
            <p>Templates are rendered using <a href="http://jinja.pocoo.org/docs/">Jinja2</a> which is a "Django like" template engine. See their site for Documentation.</p>
        """
        if tid is not None:
            t = ds.con.Templates()
            cfile, template_text = t.get_file_content(fid=tid)
            self.context['file_name'] = cfile.name
            self.context['active_repo'] = cfile.repo
            self.context['file_text'] = cgi.escape(template_text)
        else:
            self.context['new_file'] = True
        self.context['function'] = 'edit-template'
        self.context['delete_action'] = 'delete-template'
        self._template = self._env.get_template('edit_file.html')
    
    def edit_static(self, sid):
        self.context['file_type'] = 'Text'
        if sid is not None:
            static = ds.con.Statics()
            cfile, content = static.get_file_content(fid=sid)
            self.context['file_name'] = cfile.name
            self.context['file_id'] = cfile.id
            self.context['active_repo'] = cfile.repo
            self.context['file_type'] = static.get_file_type(self.context['file_name'])
            static_uri = join_uri(self._site_edit_uri, ds.REPOS_DIR, cfile.repo, static.DIR, cfile.name)
            if self.context['file_type'] == 'Text':
                self.context['file_text'] = cgi.escape(content)
            elif self.context['file_type'] == 'Image':
                self.context['file_image_path'] = static_uri
            elif self.context['file_type'] == 'Font':
                self.context['font_path'] = static_uri
                self.context['font_name'] = get_font_name(static.get_path(cfile.repo, cfile.name))
        else:
            self.context['new_file'] = True
        self.context['function'] = 'edit-static'
        self.context['delete_action'] = 'delete-static'
        self._template = self._env.get_template('edit_file.html')
        
    def edit_globcon(self, gcid):
        help_text = 'JSON file containing extra values for the global context used when rendering pages'
        linkname = 'globcon'
        con = ds.con.GlobConFiles()
        return self.edit_json(gcid, con, help_text, linkname, ds.GLOBCON_JSON_FILE)
        
    def edit_libfile(self, lid):
        help_text = """
            <p>JSON file containing list of external libraries (eg. css &amp; json) to download and include in static folder.</p>
            <p>See 
            <a href="https://github.com/samuelcolvin/donkey-simple/blob/master/DonkeySimple/static_libraries.json">github DonkeySimple/static_libraries.json</a>
            for an example.<p>
        """
        linkname = 'libfile'
        con = ds.con.LibraryFiles()
        return self.edit_json(lid, con, help_text, linkname, ds.LIBRARY_JSON_FILE)
        
    def edit_json(self, json_id, con, help_text, linkname, file_name):
        self.context['help_statement'] = help_text
        if json_id is not None:
            cfile, libfile_text = con.get_file_content(fid=json_id)
            self.context['active_repo'] = cfile.repo
            self.context['file_text'] = cgi.escape(libfile_text)
        else:
            self.context['new_file'] = True
        self.context['file_name'] = file_name
        self.context['fname_readonly'] = True
        self.context['function'] = 'edit-%s' % linkname
        self.context['delete_action'] = 'delete-%s' % linkname
        self._template = self._env.get_template('edit_file.html')
        
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
        edit_username = self.all_users[uid]
        if not self.isadmin and edit_username != self.username:
            return self._permission_denied()
        self.context['edit_username'] = uid
        self._template = self._env.get_template('set_password.html')
        
    def _permission_denied(self):
        self._bad('You do not have permission to view this page.', code=httplib.FORBIDDEN)
        
    def _page_not_found(self):
        self._bad('Page not Found', 'Page not Found: %s' % os.environ['REQUEST_URI'], code=httplib.NOT_FOUND)
        
    def _error_page(self, e, code = httplib.INTERNAL_SERVER_ERROR):
        error_details = None
        if settings.DEBUG:
            error_details = traceback.format_exc()
        self._bad(str(e),error_details=error_details, code=code)
        
    def _bad(self, error_name, error_details = None, code = httplib.BAD_REQUEST):
        self.context['error'] = '%d %s' % (code, httplib.responses[code])
        self.response_code = 'Status: %s\n' % self.context['error']
        self.context['error_name'] = error_name
        if error_details:
            self.context['error_details'] = str(error_details)
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
