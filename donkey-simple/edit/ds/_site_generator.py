import os
import markdown2
import pprint
from _common import *
import json
import _template_renderer as tr
    
class Page(object):
    def __init__(self, name, template):
        self._page = {'name': name, 'template': template}
    
    def clean_page(self):
        r = tr.RenderTemplate(self._page['template'])
        self._page['context'] = r.get_empty_context()
        self._write()
        
    def _write(self):
        fn = '%s/%s.json' % (PAGE_DIR, self._page['name'])
        with open(fn, 'w') as outfile:
            json.dump(self._page, outfile, sort_keys=True, indent=4, separators=(',', ': '))
        
def get_all_templates():
    return [f for f in os.listdir(TEMPLATES_DIR) if f.startswith('t_')]

class SiteGenerator(object):
    def __init__(self):
        self._base_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))

    def generate_entire_site(self):
        self._delete_existing_files()
        for p in self.get_pages():
            self.generate_page(p)
            
    def get_pages(self):
        return [f for f in os.listdir(PAGE_DIR) if f.endswith('.json')]
    
    def generate_page(self, page_name):
        path = '%s/%s' % (PAGE_DIR, page_name)
        with open(path, 'r') as infile:
            page = json.load(infile)
        context = {}
        for var, item in page['context'].items():
            context[var] = item['value']
            if item['type'] == 'md':
                context[var] = markdown2.markdown(item['value'])
        r = tr.RenderTemplate(page['template'])
        content = r.render(context)
        fn = '%s/%s.html' % (self._base_dir, page['name'])
        open(fn, 'w').write(content)
        
    def _delete_existing_files(self):
        files = [os.path.join(self._base_dir, f) for f in os.listdir('../') if f.endswith('.html')]
        [os.remove(f) for f in files]
        return files
    
if __name__ == '__main__':
#     page = Page('index', 't_simple_site.html')
#     page.clean_page()
    site_gen = SiteGenerator()
    site_gen.generate_entire_site()




