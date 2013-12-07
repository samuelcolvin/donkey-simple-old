import os
import markdown2
import pprint
from _common import *
import json
import _template_renderer as tr
import HTMLParser
    
class Page(object):
    def __init__(self, name, template=None):
        self._page = {'name': name, 'template': template}
        self._sg = SiteGenerator(None)
    
    def generate_empty_page(self):
        self._page['context'] = self.get_empty_context()
        return self._write()
    
    def get_empty_context(self):
        r = tr.RenderTemplate(self._page['template'])
        return r.get_empty_context()
    
    def update_context(self, fields):
        context = {}
        for name, item in self.get_empty_context().items():
            context[name] = item
            if name in fields:
                text = fields[name]
                if item['type'] in ['html', 'md']:
                    text = HTMLParser.HTMLParser().unescape(text)
                context[name]['value'] = text
        self._page['context'] = context
        
    def generate_page(self):
        return self._write()
    
    def delete_existing(self, quiet=False):
        file_name, path = self._get_path()
        if file_name not in self._sg.get_page_files():
            if quiet:
                return path
            raise Exception('"%s" not in pages directory' % file_name)
        os.remove(path)
        return path
        
    def _write(self):
        self._page['id'] = len(self._sg.get_page_files())
        path = self.delete_existing(quiet=True)
        with open(path, 'w') as outfile:
            json.dump(self._page, outfile, sort_keys=True, indent=4, separators=(',', ': '))
        os.chmod(path, 0666)
        return path
    
    def _get_path(self):
        filename = '%s.json' % self._page['name']
        return filename, '%s/%s' % (PAGE_DIR, filename)

class Templates(object):    
    def get_all_templates(self):
        return [f for f in os.listdir(TEMPLATES_DIR) if '.template.' in f]
    
    def get_template_text(self, name = None, tid = None):
        name, path = self._get_name(name, tid)
        return name, open(path, 'r').read()
    
    def write_template(self, text, name):
        path = self._get_path(name)
        try:
            self.delete_template(name)
        except: pass
        with open(path, 'w') as handle:
            handle.write(text)
        os.chmod(path, 0666)
        return path
    
    def delete_template(self, name):
        _, path = self._get_name(name)
        os.remove(path)
        return path
        
    def _get_name(self, name, tid = -1):
        templates = self.get_all_templates()
        if name is None:
            if tid >= len(templates):
                raise Exception('Template id %d is greater than number of templates(%d)' %(tid, len(templates)))
            if tid < 0:
                raise Exception('No valid template id provided')
            name = templates[tid]
        elif name not in templates:
            raise Exception('Template "%s" does not exist: %r' % (name, templates))
        path = self._get_path(name)
        return name, path
    
    def _get_path(self, name):
        return '%s/%s' % (TEMPLATES_DIR, name)

class SiteGenerator(object):
    def __init__(self, debug):
        self._debug = debug
        self._base_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))

    def generate_entire_site(self):
        self._delete_existing_files()
        for p in self.get_page_files():
            self.generate_page(p)
            
    def get_page_files(self):
        return [f for f in os.listdir(PAGE_DIR) if f.endswith('.json')]
    
    def get_pages(self):
        return [self._load_page_file(fn) for fn in self.get_page_files()]
    
    def get_page(self, pid=None, name=None):
        pages = self.get_pages()
        if pid is not None:
            return next((page for page in pages if page['id'] == pid))
        else:
            return next((page for page in pages if page['name'] == name))
            
    def _load_page_file(self, page_file_name):
        path = '%s/%s' % (PAGE_DIR, page_file_name)
        with open(path, 'r') as infile:
            return json.load(infile)
        return None
    
    def generate_page(self, page_file_name):
        path = '%s/%s' % (PAGE_DIR, page_file_name)
        self._debug.write_line(path)
        with open(path, 'r') as infile:
            page = json.load(infile)
        context = {}
        for var, item in page['context'].items():
            context[var] = item['value']
            self._debug.write_line(item)
            if item['type'] == 'md':
                context[var] = markdown2.markdown(item['value'])
        r = tr.RenderTemplate(page['template'])
        content = r.render(context)
        fn = '%s/%s.html' % (self._base_dir, page['name'])
        open(fn, 'w').write(content)
        os.chmod(fn, 0666)
        
    def _delete_existing_files(self):
        files = [os.path.join(self._base_dir, f) for f in os.listdir(self._base_dir) if f.endswith('.html')]
        [os.remove(f) for f in files]
        return files




