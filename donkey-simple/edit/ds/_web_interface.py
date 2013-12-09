import jinja2, os, cgi, re
import _site_generator as sg
import _controllers as con
from _common import *
import HTMLParser

EDITOR_TEMPLATE_DIR = 'templates_editor'

urls = (
    ('add-page', 'edit_page'),
    ('edit-page-(\d+)', 'edit_page'),
    ('add-template', 'edit_template'),
    ('edit-template-(\d+)', 'edit_template'),
    ('add-static', 'edit_static'),
    ('edit-static-(\d+)', 'edit_static'),
)

class WebInterface(object):
    def __init__(self,):
        self._msgs = {}
        self._env = jinja2.Environment(loader=jinja2.FileSystemLoader(EDITOR_TEMPLATE_DIR))
        uri = os.environ['REQUEST_URI']
        self._site_uri = uri[:uri.index('/edit/')]
        e_index = uri.index('/edit/') + 5
        self._site_edit_uri = uri[:e_index] + '/'
        self._edit_static_uri = self._site_edit_uri + 'editor_static/'
        self._static_uri = self._site_edit_uri + 'static/'
        ProcessForm(self._add_msg)
        self._generate_page(uri)
        
    def _generate_page(self, uri):
        context = {'title': '%s Editor' % SITE_NAME, 'static_uri': self._edit_static_uri, 
                   'edit_uri': self._site_edit_uri, 'site_uri': self._site_uri}
        context.update(CONFIG_SETTINGS)
        print 'uri:', uri
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
        self.page = self._template.render(**context)
    
    def index(self, context):
        self._template = self._env.get_template('edit_index.html')
        page_con = con.Pages()
        context['pages'] = []
        for page in page_con.get_pages():
            context['pages'].append({'link': 'edit-page-%d' % page['id'], 'name': page['name']})
        context['templates'] = []
        t = con.Templates()
        for i, t in enumerate(t.get_all_filenames()):
            context['templates'].append({'link': 'edit-template-%d' % i, 'name': t})
        context['static_files'] = []
        s = con.Statics()
        for i, s in enumerate(s.get_all_filenames()):
            context['static_files'].append({'link': 'edit-static-%d' % i, 'name': s})
    
    def edit_template(self, context, tid):
        context['help_statement'] = """
            <p>Template names should contain <span class="code">.template.</span> in their name, eg. <span class="code">my_template.template.html</span>.</p>
            <p>Templates are rendered using <a href="http://jinja.pocoo.org/docs/">Jinja2</a> which is a "Django like" template engine. See their site for Documentation.</p>
        """
        if tid is not None:
            t = con.Templates()
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
            static = con.Statics()
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
        t_con = con.Templates()
        context['page_templates'] = t_con.get_all_filenames()
        if pid is not None:
            page_con = con.Pages()
            page = page_con.get_page(pid=pid)
            context['page_name'] = page['name']
            context['page_context_str'] = []
            context['page_context_other'] = []
            for name, value in page['context'].items():
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
    def __init__(self, add_msg):
        self._add_msg = add_msg
        fields = cgi.FieldStorage()
        if 'action' in fields:
            for name in fields:
                print name, 
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
        sg.SiteGenerator().generate_entire_site()
        self._add_msg('Site generated successfully', 'success')
        
    def edit_page(self):
        page_con = con.Pages()
        page_con.set_name(self.fields['page-name'].value, self.fields['page-template'].value)
        context = dict([(name, self.fields[name].value) for name in self.fields])
        page_con.update_context(context)
        fname = page_con.generate_page()
        self._add_msg('"%s" successfully saved' % fname, 'success')
        
    def delete_page(self):
        page = con.Pages()
        self._delete_file(page)
        
    def edit_template(self):
        t = con.Templates()
        text = self._unescape_file_text()
        fname = t.write_file(text, self.fields['file-name'].value)
        self._add_msg('"%s" successfully saved' % fname, 'success')
        
    def delete_template(self):
        t = con.Templates()
        self._delete_file(t)
        
    def upload_template(self):
        self._process_files('files', con.Templates())
        
    def edit_static(self):
        static = con.Statics()
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
        static = con.Statics()
        self._delete_file(static)
        
    def upload_static(self):
        self._process_files('files', con.Statics())
    
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
        
    def _delete_file(self, controller):
        fname = controller.delete_file(self.fields['file-name'].value)
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




