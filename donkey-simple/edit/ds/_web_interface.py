import jinja2, os, cgi
import _site_generator
from _common import *
import HTMLParser

EDITOR_TEMPLATE_DIR = 'templates_editor'

class WebInterface(object):
    def __init__(self, debug):
        self._msgs = {}
        self._debug = debug
        self._env = jinja2.Environment(loader=jinja2.FileSystemLoader(EDITOR_TEMPLATE_DIR))
        uri = os.environ['REQUEST_URI']
        self._site_uri = uri[:uri.index('/edit/')]
        e_index = uri.index('/edit/') + 5
        self._site_edit_uri = uri[:e_index] + '/'
        self._static_uri = self._site_edit_uri + 'editor_static/'
        sub_page = uri[e_index:].replace('/','')
        self._process_form(sub_page)
        self._generate_page(sub_page)
        
    def _generate_page(self, sub_page):
        context = {'title': '%s Editor' % SITE_NAME, 'static_uri': self._static_uri, 
                   'edit_uri': self._site_edit_uri, 'site_uri': self._site_uri}
        context.update(CONFIG_SETTINGS)
#         self._debug.write_line('sub_page:', sub_page)
        if 'add-template' in sub_page:
            self._edit_template(context, -1)
        elif 'edit-template' in sub_page:
            tid = int(sub_page.replace('edit-template-', ''))
            self._edit_template(context, tid)
        elif 'add-page' in sub_page:
            self._edit_page(context, -1)
        elif 'edit-page' in sub_page:
            pid = int(sub_page.replace('edit-page-', ''))
            self._edit_page(context, pid)
        else:
            self._index(context)
        context.update(self._msgs)
        self.page = self._template.render(**context)
            
    def _process_form(self, sub_page):
        self._debug.write_line(sub_page)
        if sub_page == 'generate':
            sg = _site_generator.SiteGenerator(self._debug)
            sg.generate_entire_site()
            self._add_msg('Site generated successfully', 'success')
        fields = cgi.FieldStorage()
        if 'action' in fields:
            for name in fields:
                self._debug.write_line(name, fields[name].value)
            action = fields['action'].value
            if action == 'edit-template':
                t = _site_generator.Templates()
                text = HTMLParser.HTMLParser().unescape(fields['template-text'].value)
                fname = t.write_template(text, fields['template-name'].value)
                self._add_msg('"%s" successfully saved' % fname, 'success')
            elif action == 'delete-template':
                t = _site_generator.Templates()
                fname = t.delete_template(fields['template-name'].value)
                self._add_msg('"%s" successfully deleted' % fname, 'success')
            elif action == 'edit-page':
                page = _site_generator.Page(fields['page-name'].value, fields['page-template'].value)
                context = dict([(name, fields[name].value) for name in fields])
                page.update_context(context)
                fname = page.generate_page()
                self._add_msg('"%s" successfully saved' % fname, 'success')
            elif action == 'delete-page':
                page = _site_generator.Page(fields['page-name'].value)
                fname = page.delete_existing()
                self._add_msg('"%s" successfully deleted' % fname, 'success')
    
    def _index(self, context):
        self._template = self._env.get_template('edit_index.html')
        sg = _site_generator.SiteGenerator(self._debug)
        context['pages'] = []
        for page in sg.get_pages():
            context['pages'].append({'link': 'edit-page-%d' % page['id'], 'name': page['name']})
        context['templates'] = []
        t = _site_generator.Templates()
        for i, t in enumerate(t.get_all_templates()):
            context['templates'].append({'link': 'edit-template-%d' % i, 'name': t})
    
    def _edit_template(self, context, tid):
        if tid >= 0:
            t = _site_generator.Templates()
            context['template_name'], template_text = t.get_template_text(tid=tid)
            context['template'] = cgi.escape(template_text)
        self._template = self._env.get_template('edit_template.html')
    
    def _edit_page(self, context, pid):
        if pid >= 0:
            sg = _site_generator.SiteGenerator(self._debug)
            page = sg.get_page(pid=pid)
            context['page_name'] = page['name']
            context['page_context_str'] = []
            context['page_context_other'] = []
            for name, value in page['context'].items():
                if value['type'] == 'string':
                    context['page_context_str'].append({'name': name, 'value': value['value'], 'type': value['type']})
                else:
                    context['page_context_other'].append({'name': name, 'value': cgi.escape(value['value']), 'type': value['type']})
            context['page_template'] = page['template']
        self._template = self._env.get_template('edit_page.html')
    
    def _add_msg(self, msg, mtype='info'):
        if mtype not in self._msgs:
            self._msgs[mtype] = [msg]
        else:
            self._msgs[mtype].append(msg)