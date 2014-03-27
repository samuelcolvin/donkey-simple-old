import jinja2, os, re, httplib, traceback, json, sys, StringIO
import DonkeySimple
import DonkeySimple.DS as ds
from DonkeySimple.DS import get_settings
sg = ds.SiteGenerator
settings = get_settings()
from _forms import ProcessForm, AnonFormProcessor
from _auth import UserAuth, SecureRequest

from werkzeug.utils import redirect
from werkzeug.wrappers import Response
from werkzeug.utils import escape
from werkzeug.wsgi import SharedDataMiddleware
# from werkzeug.exceptions import HTTPException, NotFound, BadRequest


DEBUG_PORT = 4000
class SERVER_MODES:
    UNKNOWN = 0
    DEBUG = 1
    CGI = 2
    WSGI = 3
SERVER_MODE = SERVER_MODES.UNKNOWN

THIS_PATH = os.path.dirname(os.path.realpath(__file__))
EDITOR_TEMPLATE_DIR = os.path.join(THIS_PATH, 'templates') 

def make_dev_app():
    """
    Generates the DEV server. Here werkzeug takes care of serving all the static
    files as well as the site itself.
    SiteServeMiddleware takes care of some server like file serving.
    """
    static_files= {'/favicon.ico': os.path.join('static', 'favicon.png'), 
                   '/static': 'static', 
                   '/repos': 'repos', 
                   settings.SITE_URL.rstrip('/'): settings.SITE_PATH}
    return SiteServeMiddleware(application, static_files, fallback_mimetype='text/html')

def make_cgi_app():
    """
    Generates the CGI application, with CGI we can't afford to serve static files with
    the application. That has to be done by the real server, eg. apache: see the .htaccess
    file in the site file (the one with settings.py).
    """
    return application

@SecureRequest.application
def application(request):
    request.check_for_login()
    view = View(request)
    response = view.response
    request.session.save_cookie(response)
    return response

urls = (
    ('logout$', 'logout'),
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
    ('submit.json', 'json_response'),
    ('add-user$', 'edit_user'),
    ('user$', 'edit_this_user'),
    ('edit-user-last$', 'edit_last_user'),
    ('edit-user-(.+)$', 'edit_user'),
    ('set-password-(.+)$', 'set_user_password'),
)

class View(object):
    site_edit_url = '/'
    edit_static_url = 'static/'
    response_code = httplib.OK
    page = ''
    mimetype = 'text/html'
    
    def __init__(self, request):
        with CatchStdout(self.print_function):
            self._msgs = {}
            self._response = None
            if SERVER_MODE == SERVER_MODES.UNKNOWN:
                raise Exception('Mode UNKNOWN')
            self.request = request
            if self.request.login_message:
                self._add_msg(self.request.login_message, ('errors', 'success')[self.request.valid_user])
            self.isadmin = self.request.valid_user and self.request.user and self.request.user['admin']
            self._env = jinja2.Environment(loader=jinja2.FileSystemLoader(EDITOR_TEMPLATE_DIR))
            self.site_url = (settings.SITE_URL, '/')[settings.SITE_URL == '']
            if SERVER_MODE == SERVER_MODES.CGI:
                self._uri = request.environ['REQUEST_URI']
                sim = _string_similar_point(self._uri, request.environ['SCRIPT_NAME'])
                self.site_edit_url = self._uri[:sim]
            else:
                url = request.base_url.replace('http://', '')
                self._uri = str(url[url.index('/'):])
            self.edit_static_url = join_uri(self.site_edit_url, 'static/')
            self._process_forms()
            self._generate_page(self._uri, loggedin = request.valid_user, error = self.processing_error)
                  
    @property
    def print_function(self):
        if settings.PRINT_TO == 'PAGE':
            return self.add_to_page
        
    def add_to_page(self, content):
        if self.mimetype == 'text/html':
            self.page += content
    
    @property
    def response(self):
        if self._response is None:
            self._response = Response(self.page, mimetype = self.mimetype, status = self.response_code)
        return self._response
    
    def _process_forms(self):
        self.processing_error = None
        if self.request.method != 'POST':
            return
        self.processing_error = None
        try:
            if self.request.valid_user:
                proc_form = ProcessForm(self._add_msg, self.request, self.isadmin, self.request.username)
                if proc_form.regen_users:
                    self.logout(None)
                self.created_item = proc_form.created_item
            else:
                AnonFormProcessor(self._add_msg, self.request.form)
        except Exception, e:
            print 'processing _process_forms error:', e
            _, _, exc_traceback = sys.exc_info()
            self.processing_error = (e, exc_traceback)
        
    def _generate_page(self, uri, loggedin = False, error = None):
        self.context = {'title': '%s Editor' % settings.SITE_NAME, 
                        'site_name': settings.SITE_NAME, 
                        'site_title': '%s Editor' % settings.SITE_NAME, 
                        'static_url': self.edit_static_url, 
                        'edit_uri': self.site_edit_url,
                        'site_url': self.site_url, 
                        'json_submit_url': '%ssubmit.json' % self.site_edit_url, 
                        'version': DonkeySimple.__version__
                        }
        if loggedin:
            self.context.update({'username': self.request.username, 'admin': self.isadmin})
            self.context['anon'] = self.request.is_anon
        self.repo_paths = list(ds.get_all_repos())
        self.context['repos'] = [r for r, _ in self.repo_paths]
        if len(self.context['repos']) == 0:
            self._add_msg('REPOS directory is empty: there are no repos, pages, templates or static files')
        print 'uri: %r' % uri
        if error:
            e, tb = error
            self._error_page(e, code = httplib.BAD_REQUEST, tb=tb)
        elif not loggedin:
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
                if uri != self.site_edit_url:
                    self._add_msg('%s not found' % uri, 'errors')
                    self.response_code = httplib.NOT_FOUND
                self.index()
        self.context.update(self._msgs)
        if hasattr(self, '_template'):
            self.page = self._template.render(**self.context)
            
    def json_response(self, rid):
        self._json_response(self._msgs)
        
    def _json_response(self, data):
        self._template = self._env.get_template('json_response.json')
        self.mimetype = 'application/json'
        self.context['json_response'] = json.dumps(data, sort_keys=True, indent=2, separators=(',', ': '))
        
    def login(self):
        self._template = self._env.get_template('login.html')
        self.context['title'] =  settings.SITE_NAME + ' login'
        self.context['reset_password'] = 'reset-password'
        
    def reset_password(self):
        self._template = self._env.get_template('reset_password.html')
        
    def logout(self, fid):
        self.request.logout()
        self._response = redirect(self.site_edit_url)
    
    def index(self):
        self._template = self._env.get_template('index.html')
        try:
            page_con = ds.con.Pages()
            self.context['pages'] = []
            for _, cf in page_con.cfiles_ordered:
                self.context['pages'].append({'link': 'edit-page-%s' % cf.id, 'name': cf.display})
            self.context['templates'] = []
            t = ds.con.Templates()
            for _, cf in t.cfiles_ordered:
                self.context['templates'].append({'link': 'edit-template-%s' % cf.id, 'name': cf.display})
            self.context['static_files'] = []
            s = ds.con.Statics()
            for _, cf in s.cfiles_ordered:
                self.context['static_files'].append({'link': 'edit-static-%s' % cf.id, 'name': cf.display})
            self.context['library_files'] = []
            s = ds.con.LibraryFiles()
            for _, cf in s.cfiles_ordered:
                self.context['library_files'].append({'link': 'edit-libfile-%s' % cf.id, 'name': cf.display})
            self.context['globcon_files'] = []
            gc = ds.con.GlobConFiles()
            for _, cf in gc.cfiles_ordered:
                self.context['globcon_files'].append({'link': 'edit-globcon-%s' % cf.id, 'name': cf.display})
            if self.isadmin:
                self.context['users'] = []
                for u in self.request.users:
                    self.context['users'].append({'link': 'edit-user-%s' % u, 'name': u})
        except KeyError, e:
            return self._error_page(e)
        
    def view_repo(self, repo_name):
        self.context['repo_name'] = repo_name
        self.context['title'] = repo_name
        self.context['action_uri'] = self.site_edit_url + 'view-repo-' + repo_name
        
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
        t_con = ds.con.Templates()
        self.context['page_templates'] = [cf for _, cf in t_con.cfiles_ordered]
        self.context['other_formats'] = ['markdown', 'html']
        self.context['action_uri'] = self.site_edit_url + 'edit-page-last'
        if pid is not None:
            page_con = ds.con.Pages()
            try:
                cfile = page_con.get_cfile_fid(pid)
            except:
                return self._error_page('Page not found', code=httplib.BAD_REQUEST)
            self.context['page_name'] = cfile.info['name']
            self.context['active_repo'] = cfile.repo
            if 'sitemap' in cfile.info:
                self.context['sitemap'] = cfile.info['sitemap']
            if 'extension' in cfile.info:
                self.context['extension'] = cfile.info['extension']
            self.context['page_context_str'] = []
            self.context['page_context_other'] = []
            global_context = ds.SiteGenerator().global_context()
            true_context = page_con.get_true_context()
            if true_context is None:
                self._add_msg('Problem getting template context', 'errors')
            else:
                for name, value in true_context.items():
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
                        con_settings['value'] = escape(value['value'])
                        self.context['page_context_other'].append(con_settings)
            try:
                self.context['active_page_template_id'] = t_con.get_cfile_name(name = cfile.info['template'], repo = cfile.info['template_repo']).id
            except Exception, e:
                self._add_msg('Problem getting template id: %s' % str(e), 'errors')
            self.context['action_uri'] = self.context['edit_uri']
        self._template = self._env.get_template('edit_page.html')
    
    def edit_template(self, tid):
        def generate_global_vars(var_tree):
            for name, value in var_tree.items():
                if type(value) == dict:
                    for name2, value2 in value.items():
                        yield {'name': '%s.%s' % (name, name2), 'value': str(value2)}
                elif type(value) == list:
                    yield {'name': '{%% for item in %s %%}' % name}
                    for i, item in enumerate(value):
                        if type(item) == dict:
                            yield {'name': 'item %d' % i, 'indent': 20}
                            for k, v in item.items():
                                yield {'name': '{{ item.%s }}' % k, 'value': str(v), 'indent': 40}
                        else:
                            yield {'name': '{{ item }}', 'value': str(item), 'indent': 20}
                    yield {}
                else:
                    yield {'name': '{{ %s }}' % name, 'value': str(value)}
                
        self.context['help_statement'] = """
            <p>Template names should contain <span class="code">.template.</span> in their name, eg. <span class="code">my_template.template.html</span>.</p>
            <p>Templates are rendered using <a href="http://jinja.pocoo.org/docs/">Jinja2</a> which is a "Django like" template engine. See their site for Documentation.</p>
        """
        if tid is not None:
            t = ds.con.Templates()
            cfile, template_text = t.get_file_content(fid=tid)
            self.context['file_name'] = cfile.name
            self.context['active_repo'] = cfile.repo
            self.context['file_text'] = escape(template_text)
        self.context['global_variables'] = generate_global_vars(ds.SiteGenerator().global_context())
        self.context['show_file_text'] = True
        self.context['function'] = 'edit-template'
        self.context['save_gen_func'] = 'edit-template-gen'
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
            static_uri = join_uri(self.site_edit_url, ds.REPOS_DIR, cfile.repo, static.DIR, cfile.name)
            if self.context['file_type'] == 'Text':
                self.context['file_text'] = escape(content)
                self.context['show_file_text'] = True
            elif self.context['file_type'] == 'Image':
                self.context['file_image_path'] = static_uri
            elif self.context['file_type'] == 'Font':
                self.context['font_path'] = static_uri
                self.context['font_name'] = get_font_name(static.get_path(cfile.repo, cfile.name))
        else:
            self.context['show_file_text'] = True
        self.context['function'] = 'edit-static'
        self.context['save_gen_func'] = 'edit-static-gen'
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
            <a href="https://github.com/samuelcolvin/donkey-simple/blob/master/static_libraries.json">github static_libraries.json</a>
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
            self.context['file_text'] = escape(libfile_text)
        self.context['show_file_text'] = True
        self.context['file_name'] = file_name
        self.context['fname_readonly'] = True
        self.context['function'] = 'edit-%s' % linkname
        self.context['delete_action'] = 'delete-%s' % linkname
        self._template = self._env.get_template('edit_file.html')
        
    def edit_last_user(self, _):
        uid = self.created_item
        self.edit_user(uid)
    
    def edit_this_user(self, uid):
        self.edit_user(self.request.username)
    
    def edit_user(self, uid):
        self.context['page_tag'] = 'New User'
        if not self.isadmin:
            if uid is None or uid != self.request.username or self.request.is_anon:
                return self._permission_denied()
        self.context['action_uri'] = self.site_edit_url + 'edit-user-last'
        if uid is not None:
            self.context['existing_user'] = True
            self.context['password_uri'] = self.site_edit_url + 'set-password-%s' % uid
            edit_user = self.request.users[uid]
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
        edit_username = self.request.users[uid]
        if not self.isadmin and edit_username != self.request.username or self.request.is_anon:
            return self._permission_denied()
        self.context['edit_username'] = uid
        self._template = self._env.get_template('set_password.html')
        
    def _permission_denied(self):
        self._bad('You do not have permission to view this page.', code=httplib.FORBIDDEN)
        
    def _page_not_found(self):
        self._bad('Page not Found', 'Page not Found: %s' % os.environ['REQUEST_URI'], code=httplib.NOT_FOUND)
        
    def _error_page(self, e, code = httplib.INTERNAL_SERVER_ERROR, tb = None):
        error_details = None
        if settings.DEBUG:
            if tb:
                error_details = '\n'.join(traceback.format_tb(tb))
            else:
                error_details = traceback.format_exc()
        self._bad(str(e),error_details=error_details, code=code)
        
    def _bad(self, error_name, error_details = None, code = httplib.BAD_REQUEST):
        print error_details
        self.context['error'] = '%d %s' % (code, httplib.responses[code])
        self.response_code = code
        self.context['error_name'] = error_name
        if error_details:
#             self.context['error_details'] = str(error_details)
            traceback.print_exc()
        if 'submit.json' in self._uri:
            self._json_response(self.context)
        else:
            self._template = self._env.get_template('bad.html')
    
    def _add_msg(self, msg, mtype='info'):
        if mtype not in self._msgs:
            self._msgs[mtype] = [msg]
        else:
            self._msgs[mtype].append(msg)

class SiteServeMiddleware(SharedDataMiddleware):
    
    def get_directory_loader(self, directory):        
        def loader(path):
            """
            changed from original to serve index.html if the directory is requested
            and /*.html if if /* is requested.
            """ 
            path_orig = path
            if path is not None:
                path = os.path.join(directory, path)
            else:
                path = directory
            if os.path.isfile(path):
                return os.path.basename(path), self._opener(path)
            
            attempts = []
            if path_orig is None:
                attempts.append('index.html')
            else:
                attempts.append(path_orig + '.html')
            attempts.append('404.html')
            for attempt_fname in attempts:
                filepath = os.path.join(directory, attempt_fname)
                if os.path.isfile(filepath):
                    return attempt_fname, self._opener(filepath)
            return None, None
        return loader


class CatchStdout(object):
    """
    change working directory and always return
    """
    stdout_text = ''
    override = False
    
    def __init__(self, print_to = None):
        self.print_to = print_to
    
    def __enter__(self):
        if self.override:
            return
        sys.stdout.flush()
        self._stdout_orig = sys.stdout
        sys.stdout = StringIO.StringIO()
    
    def __exit__(self, e_type, e_value, e_tb):
        if self.override:
            return
        self._stdout_orig.flush()
        self.stdout_text = sys.stdout.getvalue()
        sys.stdout.close()
        sys.stdout = self._stdout_orig
        if settings.DEBUG:
            if self.print_to:
                if e_tb:
                    print self.text
                else:
                    self.print_to(self.html)
            else:
                print self.text
        
    @property
    def html(self):
        if self.stdout_text.strip('\r\t\n ') == '':
            return ''
        text = ''
        try:
            text = escape(self.stdout_text).strip('\r\t\n ')
        except:
            pass
        return '<div class="container"><h4>Debug Output:</h4>\n<pre><code>%s\n</code></pre></div>' % text
    
    @property
    def text(self):
        if self.stdout_text.strip('\r\t\n ') == '':
            return ''
        debug  = '==========DEBUG OUTPUT==========\n'
        debug += '%s\n' % self.stdout_text
        debug += '================================'
        return debug
 
def get_font_name(filename, add_msg):
    try:
        from fontTools import ttLib
        tt = ttLib.TTFont(filename)
        return tt['name'].names[1].string
    except Exception, e:
        e_str = 'Problem processing font: %s' % str(e)
        print e_str
        add_msg(e_str, 'errors')
        return 'unknown'

def join_uri(*args):
    uri = '/' + '/'.join(p.strip('/') for p in args)
    if args[-1].endswith('/'):
        uri += '/'
    uri = uri.replace('//', '/')
    return uri

    
def _string_similar_point(s1, s2):
    i = 0
    while True:
        if i == len(s1) or i == len(s2):
            return i
        if s1[i] != s2[i]:
            return i
        i += 1
    