import jinja2, os, cgi, re, httplib, traceback
import ds
import HTMLParser
import Cookie

sg = ds.SiteGenerator


EDITOR_TEMPLATE_DIR = 'templates_editor'

urls = (
    ('logout$', 'logout'),
    ('add-page$', 'edit_page'),
    ('edit-page-(\d+)$', 'edit_page'),
    ('edit-page-last$', 'edit_last_page'),
    ('add-template$', 'edit_template'),
    ('edit-template-(\d+)$', 'edit_template'),
    ('add-static$', 'edit_static'),
    ('edit-static-(\d+)$', 'edit_static'),
    ('add-user$', 'edit_user'),
    ('user$', 'edit_this_user'),
    ('edit-user-(\d+)$', 'edit_user'),
    ('edit-user-last$', 'edit_last_user'),
    ('set-password-(\d+)$', 'set_user_password'),
)

class WebInterface(object):
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
        self._edit_static_uri = self._site_edit_uri + 'editor_static/'
        self._static_uri = self._site_edit_uri + 'static/'
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
                        fid = int(m.group(1))
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
        auth = ds.Auth()
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
        self.o_usernames = auth.get_sorted_users()
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
        for page in page_con.get_pages():
            self.context['pages'].append({'link': 'edit-page-%d' % page['id'], 'name': page['name']})
        self.context['templates'] = []
        t = ds.con.Templates()
        for i, t in enumerate(t.get_all_filenames()):
            self.context['templates'].append({'link': 'edit-template-%d' % i, 'name': t})
        self.context['static_files'] = []
        s = ds.con.Statics()
        for i, s in enumerate(s.get_all_filenames()):
            self.context['static_files'].append({'link': 'edit-static-%d' % i, 'name': s})
        if self.isadmin:
            self.context['users'] = []
            for i, u in enumerate(self.o_usernames):
                self.context['users'].append({'link': 'edit-user-%d' % i, 'name': u})
    
    def edit_template(self, tid):
        self.context['help_statement'] = """
            <p>Template names should contain <span class="code">.template.</span> in their name, eg. <span class="code">my_template.template.html</span>.</p>
            <p>Templates are rendered using <a href="http://jinja.pocoo.org/docs/">Jinja2</a> which is a "Django like" template engine. See their site for Documentation.</p>
        """
        if tid is not None:
            t = ds.con.Templates()
            self.context['file_name'], template_text = t.get_file_content(fid=tid)
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
            self.context['file_name'], content = static.get_file_content(fid=sid)
            self.context['file_type'] = static.get_file_type(self.context['file_name'])
            if self.context['file_type'] == 'Text':
                self.context['file_text'] = cgi.escape(content)
            elif self.context['file_type'] == 'Image':
                self.context['file_image_path'] = self._static_uri + self.context['file_name']
            elif self.context['file_type'] == 'Font':
                self.context['font_path'] = self._static_uri + self.context['file_name']
                self.context['font_name'] = get_font_name(static.get_path(self.context['file_name']))
        else:
            self.context['new_file'] = True
        self.context['action'] = 'edit-static'
        self.context['delete_action'] = 'delete-static'
        self._template = self._env.get_template('edit_file.html')
    
    def edit_last_page(self, _):
        page_con = ds.con.Pages()
        page = page_con.get_page(name = self.created_item)
        self.edit_page(page['id'])
    
    def edit_page(self, pid):
        t_con = ds.con.Templates()
        self.context['page_templates'] = t_con.get_all_filenames()
        self.context['other_formats'] = ['markdown', 'html']
        self.context['action_uri'] = self._site_edit_uri + 'edit-page-last'
        if pid is not None:
            page_con = ds.con.Pages()
            try:
                page = page_con.get_page(pid=pid)
            except:
                return self._error_occurred('Page not found', code=httplib.BAD_REQUEST)
            self.context['page_name'] = page['name']
            self.context['page_context_str'] = []
            self.context['page_context_other'] = []
            for name, value in page_con.get_true_context().items():
                print name, value
                if value['type'] == 'string':
                    self.context['page_context_str'].append({'name': name, 'value': value['value'], 'type': value['type']})
                else:
                    self.context['page_context_other'].append({'name': name, 'value': cgi.escape(value['value']), 'type': value['type']})
            self.context['active_page_template'] = page['template']
            self.context['action_uri'] = self.context['edit_uri']
        self._template = self._env.get_template('edit_page.html')
        
    def edit_last_user(self, _):
        uid = self.o_usernames.index(self.created_item)
        self.edit_user(uid)
    
    def edit_this_user(self, uid):
        uid = (uid for uid, un in enumerate(self.o_usernames) if un == self.username).next()
        self.edit_user(uid)
    
    def edit_user(self, uid):
        self.context['page_tag'] = 'New User'
        if not self.isadmin:
            if uid is None:
                return self._permission_denied()
            edit_username = self.o_usernames[uid]
            if edit_username != self.username:
                return self._permission_denied()
        self.context['action_uri'] = self._site_edit_uri + 'edit-user-last'
        if uid is not None:
            self.context['existing_user'] = True
            self.context['password_uri'] = self._site_edit_uri + 'set-password-%d' % uid
            edit_username = self.o_usernames[uid]
            edit_user = self.all_users[edit_username]
            self.context['page_tag'] = edit_username
            self.context['edit_email'] = edit_user['email']
            self.context['edit_username'] = edit_username
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

class UniversalProcessor(object):
    def process(self, fields):
        if 'action' in fields:
            for name in fields:
                print '%s:' % name, 
                if hasattr(fields[name], 'value'):
                    if 'password' in name:
                        print '*'*len(fields[name].value)
                    else:
                        print fields[name].value
                else:
                    print fields[name]
            action_func = fields['action'].value.replace('-', '_')
            if hasattr(self, action_func):
                self.fields = fields
                getattr(self, action_func)()
            else:
                raise Exception('ProcessForm has no function called %s' % action_func)
            
    def _password_reset_email(self, username):
        auth = ds.Auth()
        if username not in auth.users:
            return False
        user = auth.pop_user(username)
        pw = auth.new_random_password()
        email = user['email']
        url = os.environ['HTTP_REFERER']
        e_index = url.index('/edit/') + 5
        url = url[:e_index] + '/'
        if '@' in email:
            success, msg = ds.password_email(user['email'], url, username, pw)
            if success:
                auth.add_user(username, user, pw)
                self._add_msg('Password email sent', 'success')
                return True
            else:
                self._add_msg('Error sending email, not changing password', 'errors')
                self._add_msg(msg, 'errors')
        return False

class ProcessForm(UniversalProcessor):
    created_item = None
    def __init__(self, add_msg, fields, isadmin, username):
        self._add_msg = add_msg
        self.isadmin = isadmin
        self.username = username
        self.regen_users = False
        self.process(fields)
    
    def generate_site(self):
        ds.SiteGenerator(self._add_msg).generate_entire_site()
        self._add_msg('Site generated successfully', 'success')
        
    def edit_page(self):
        page_con = ds.con.Pages()
        if 'page-name' not in self.fields:
            self._add_msg('page name may not be blank', 'errors')
            return
        page_name = self.fields['page-name'].value
        page_con.set_name(page_name, self.fields['page-template'].value)
        context = dict([(name, self.fields[name].value) for name in self.fields])
        ftypes = dict([(name.replace('contype-', ''), self.fields[name].value) for name in self.fields if name.startswith('contype-')])
        page_con.update_context(context, ftypes)
        fname = page_con.generate_page()
        self.created_item = page_name
        self._add_msg('"%s" successfully saved' % fname, 'success')
        
    def delete_page(self):
        page = ds.con.Pages()
        self._delete_file(page, 'page-name')
        
    def edit_template(self):
        t = ds.con.Templates()
        text = self._unescape_file_text()
        fname = t.write_file(text, self.fields['file-name'].value)
        self._add_msg('"%s" successfully saved' % fname, 'success')
        
    def delete_template(self):
        t = ds.con.Templates()
        self._delete_file(t, 'file-name')
        
    def upload_template(self):
        self._process_files('files', ds.con.Templates())
        
    def edit_static(self):
        static = ds.con.Statics()
        if self.fields['file-type'].value == 'Text':
            text = self._unescape_file_text()
            fname = static.write_file(text, self.fields['file-name'].value)
        else:
            src = self.fields['previous-file-name'].value
            dst = self.fields['file-name'].value
            if src == dst:
                return
            fname = static.copy_file(src, dst)
        self._add_msg('"%s" successfully saved' % fname, 'success')
            
    def delete_static(self):
        static = ds.con.Statics()
        self._delete_file(static, 'file-name')
        
    def edit_user(self):
        if 'previous-username' in self.fields:
            prev_username = self.fields['previous-username'].value
            if not self.isadmin and prev_username != self.username:
                return self._add_msg('Permission Denied', 'errors')
        elif not self.isadmin:
            return self._add_msg('Permission Denied', 'errors')
        username = self.fields['username'].value
        formuser = {'email': self.fields['email'].value}
        formuser['admin'] = self.isadmin and 'admin' in self.fields and self.fields['admin'].value == 'on'
        auth = ds.Auth()
        msg_type = 'success'
        if 'previous-username' not in self.fields:
            if username in auth.users:
                self._add_msg('user "%s" already exists, not creating user' % username, 'errors')
                return
            action_type = 'created'
            newuser = formuser
        else:
            olduser = auth.pop_user(prev_username)
            newuser = dict(olduser)
            newuser.update(formuser)
            if newuser == olduser and prev_username == username:
                action_type = 'not changed'
                msg_type = 'info'
            else:
                action_type = ''
                if newuser != olduser:
                    action_type = 'editted'
                if prev_username != username:
                    action_type += ' username changed'
        auth.add_user(username, newuser)
        self.created_item = username
        self.regen_users = True
        self._add_msg('"%s" %s' % (username, action_type), msg_type)
    
    def delete_user(self):
        if not self.isadmin:
            return self._add_msg('Permission Denied', 'errors')
        username = self.fields['previous-username'].value
        auth = ds.Auth()
        auth.pop_user(username, save=True)
        self.regen_users = True
        self._add_msg('deleted "%s"' % username, 'success')
    
    def email_pword_user(self):
        username = self.fields['previous-username'].value
        if not self.isadmin and username != self.username:
            return self._add_msg('Permission Denied', 'errors')
        else:
            self._password_reset_email(username)

    def change_user_password(self):
        username = self.fields['username'].value
        if not self.isadmin and username != self.username:
            return self._add_msg('Permission Denied', 'errors')
        pw1 = self.fields['password1'].value
        pw2 = self.fields['password2'].value
        if pw1 != pw2:
            self._add_msg('Passwords do not match', 'errors')
            return
        pw = pw1
        if len(pw) < ds.MIN_PASSWORD_LENGTH:
            self._add_msg('Password must be at least %d characters in length' % ds.MIN_PASSWORD_LENGTH, 'errors')
            return
        auth = ds.Auth()
        user = auth.pop_user(username)
        auth.add_user(username, user, pw)
        self._add_msg('"%s" password updated' % username, 'success')
        
    def upload_static(self):
        self._process_files('files', ds.con.Statics())
    
    def _process_files(self, field_name, controller):
        if isinstance(self.fields[field_name], list):
            for f in self.fields[field_name]:
                self._process_file(f, controller)
        else:
            self._process_file(self.fields[field_name], controller)
    
    def _process_file(self, file_field, controller):
        if file_field.file:
            name = file_field.filename
            path = controller.new_file_path(name)
            fout = file(path, 'wb')
            while 1:
                chunk = file_field.file.read(100000)
                if not chunk: break
                fout.write(chunk)
            fout.close()
            controller.set_mod(path)
            self._add_msg('File successfully uploaded to "%s"' % path, 'success')
        else:
            self._add_msg('Error getting file from upload', 'error')
        
    def _delete_file(self, controller, field_name):
        fname = controller.delete_file(self.fields[field_name].value)
        self._add_msg('"%s" successfully deleted' % fname, 'success')
    
    def _unescape_file_text(self):
        return HTMLParser.HTMLParser().unescape(self.fields['file-text'].value)
    
class AnonFormProcessor(UniversalProcessor):
    def __init__(self, add_msg, fields):
        self._add_msg = add_msg
        self.process(fields)
 
    def reset_password(self):
        username = self.fields['username'].value
        success = self._password_reset_email(username)
 
def get_font_name(filename):
    try:
        from fontTools import ttLib
        tt = ttLib.TTFont(filename)
        return tt['name'].names[1].string
    except Exception, e:
        print 'Problem processing font:', e
        return 'unknown'




