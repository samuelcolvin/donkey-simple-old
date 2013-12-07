import os
import markdown2
from _common import *
import _template_renderer as tr
import _controllers as con

class SiteGenerator(object):
    def __init__(self):
        self._base_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))

    def generate_entire_site(self):
        self._delete_existing_files()
        page_controller = con.Pages()
        for p in page_controller.get_pages():
            self.generate_page(p)
    
    def generate_page(self, page):
        context = {}
        for var, item in page['context'].items():
            context[var] = item['value']
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




