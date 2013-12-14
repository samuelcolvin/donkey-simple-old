import jinja2, os, cgi, re
import ds
import HTMLParser
import Cookie

sg = ds.SiteGenerator


EDITOR_TEMPLATE_DIR = 'templates_editor'

urls = (
    ('logout', 'logout'),
    ('add-page', 'edit_page'),
    ('edit-page-(\d+)', 'edit_page'),
    ('add-template', 'edit_template'),
    ('edit-template-(\d+)', 'edit_template'),
    ('add-static', 'edit_static'),
    ('edit-static-(\d+)', 'edit_static'),
)

class WebInterface(object):
    user = None
    all_users = None
    cookie = ''
    content_type = 'content-type: text/html\n'
    location = ''
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
        ProcessForm(self._add_msg, fields)
        self._generate_page(uri, loggedin = valid_user)
        
    def _generate_page(self, uri, loggedin = False):
        context = {'title': '%s Editor' % ds.SITE_NAME, 'static_uri': self._edit_static_uri, 
                   'edit_uri': self._site_edit_uri, 'site_uri': self._site_uri}
        if self.user:
            context.update({'username': self.user['username'], 'admin': self.user['admin']})
        context.update(ds.SETTINGS_DICT)
        print 'uri:', uri
        if not loggedin:
            self.login(context)
        else:
            found = False
            for reg, func in urls:
                m = re.search(reg, uri)
                if m:
                    found = True
                    fid = None
                    if len(m.regs) > 1:
                        fid = int(m.group(1))
                    getattr(self, func)(context, fid)
                    break
            if not found:
                self.index(context)
        context.update(self._msgs)
        if hasattr(self, '_template'):
            self.page = self._template.render(**context)
        
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
            try:cookies = Cookie.SimpleCookie(os.environ["HTTP_COOKIE"])
            except:
                valid = False
                auth.msg = 'Error processing cookies'
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
        self.all_users = auth.users
        return True
        
    def login(self, context):
        self._template = self._env.get_template('login.html')
        context['title'] =  ds.SITE_NAME + ' login'
        
    def logout(self, context, fid):
        auth = ds.Auth()
        auth.logout(self.user['username'])
        self.location = 'Location: %s\n' % self._site_edit_uri
    
    def index(self, context):
        self._template = self._env.get_template('edit_index.html')
        page_con = ds.con.Pages()
        context['pages'] = []
        for page in page_con.get_pages():
            context['pages'].append({'link': 'edit-page-%d' % page['id'], 'name': page['name']})
        context['templates'] = []
        t = ds.con.Templates()
        for i, t in enumerate(t.get_all_filenames()):
            context['templates'].append({'link': 'edit-template-%d' % i, 'name': t})
        context['static_files'] = []
        s = ds.con.Statics()
        for i, s in enumerate(s.get_all_filenames()):
            context['static_files'].append({'link': 'edit-static-%d' % i, 'name': s})
        context['users'] = []
        for i, u in enumerate(self.all_users.values()):
            context['users'].append({'link': 'edit-user-%d' % i, 'name': u['username']})
    
    def edit_template(self, context, tid):
        context['help_statement'] = """
            <p>Template names should contain <span class="code">.template.</span> in their name, eg. <span class="code">my_template.template.html</span>.</p>
            <p>Templates are rendered using <a href="http://jinja.pocoo.org/docs/">Jinja2</a> which is a "Django like" template engine. See their site for Documentation.</p>
        """
        if tid is not None:
            t = ds.con.Templates()
            context['file_name'], template_text = t.get_file_content(fid=tid)
            context['file_text'] = cgi.escape(template_text)
        else:
            context['new_file'] = True
        context['action'] = 'edit-template'
        context['delete_action'] = 'delete-template'
        self._template = self._env.get_template('edit_file.html')
    
    def edit_static(self, context, sid):
        context['file_type'] = 'Text'
        if sid is not None:
            static = ds.con.Statics()
            context['file_name'], content = static.get_file_content(fid=sid)
            context['file_type'] = static.get_file_type(context['file_name'])
            if context['file_type'] == 'Text':
                context['file_text'] = cgi.escape(content)
            elif context['file_type'] == 'Image':
                context['file_image_path'] = self._static_uri + context['file_name']
            elif context['file_type'] == 'Font':
                context['font_path'] = self._static_uri + context['file_name']
                context['font_name'] = get_font_name(static.get_path(context['file_name']))
        else:
            context['new_file'] = True
        context['action'] = 'edit-static'
        context['delete_action'] = 'delete-static'
        self._template = self._env.get_template('edit_file.html')
    
    def edit_page(self, context, pid):
        t_con = ds.con.Templates()
        context['page_templates'] = t_con.get_all_filenames()
        context['other_formats'] = ['markdown', 'html']
        if pid is not None:
            page_con = ds.con.Pages()
            page = page_con.get_page(pid=pid)
            context['page_name'] = page['name']
            context['page_context_str'] = []
            context['page_context_other'] = []
            for name, value in page_con.get_true_context().items():
                print name, value
                if value['type'] == 'string':
                    context['page_context_str'].append({'name': name, 'value': value['value'], 'type': value['type']})
                else:
                    context['page_context_other'].append({'name': name, 'value': cgi.escape(value['value']), 'type': value['type']})
            context['active_page_template'] = page['template']
        self._template = self._env.get_template('edit_page.html')
    
    def _add_msg(self, msg, mtype='info'):
        if mtype not in self._msgs:
            self._msgs[mtype] = [msg]
        else:
            self._msgs[mtype].append(msg)

class ProcessForm:
    def __init__(self, add_msg, fields):
        self._add_msg = add_msg
        if 'action' in fields:
            for name in fields:
                print '%s:' % name, 
                if hasattr(fields[name], 'value'):
                    print fields[name].value
                else:
                    print fields[name]
            action_func = fields['action'].value.replace('-', '_')
            if hasattr(self, action_func):
                self.fields = fields
                getattr(self, action_func)()
            else:
                raise Exception('ProcessForm has no function called %s' % action_func)
    
    def generate_site(self):
        ds.SiteGenerator(self._add_msg).generate_entire_site()
        self._add_msg('Site generated successfully', 'success')
        
    def edit_page(self):
        page_con = ds.con.Pages()
        page_con.set_name(self.fields['page-name'].value, self.fields['page-template'].value)
        context = dict([(name, self.fields[name].value) for name in self.fields])
        ftypes = dict([(name.replace('contype-', ''), self.fields[name].value) for name in self.fields if name.startswith('contype-')])
        page_con.update_context(context, ftypes)
        fname = page_con.generate_page()
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
 
def get_font_name(filename):
    try:
        from fontTools import ttLib
        tt = ttLib.TTFont(filename)
        return tt['name'].names[1].string
    except Exception, e:
        print 'Problem processing font:', e
        return 'unknown'




