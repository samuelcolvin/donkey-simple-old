import os, shutil
import markdown2
from _common import *
import _template_renderer as tr
import _controllers as con

class SiteGenerator(object):
    def __init__(self, output = None):
        if output:
            self._output = output
        self._base_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))

    def generate_entire_site(self):
        self._delete_existing_files()
        page_controller = con.Pages()
        for p in page_controller.get_pages():
            self.generate_page(p)
        self.generate_statics()
    
    def generate_page(self, page):
        context = {}
        for var, item in page['context'].items():
            context[var] = item['value']
            if item['type'] == 'md':
                context[var] = markdown2.markdown(item['value'])
        r = tr.RenderTemplate(page['template'])
        content = r.render(context)
        fn = os.path.join(self._base_dir, '%s.html' % page['name'])
        open(fn, 'w').write(content)
        os.chmod(fn, 0666)
        fn2 = fn
        if len(fn2) > 40:
            fn2 = '...%s' % fn2[-37:]
        self._output('Generated html file "%s" from page: %s, using template: %s' % (fn2, page['name'], page['template']))
        
    def generate_statics(self):
        static_dst = self._get_static_dir()
        os.mkdir(static_dst)
        os.chmod(static_dst, 0777)
        s = con.Statics()
        for i, src_name in enumerate(s.get_all_filenames()):
            src = s.get_path(src_name)
            dst = os.path.join(static_dst, src_name)
            shutil.copy(src, dst)
            os.chmod(dst, 0666)
        self._output('copied %d static files from "%s" to "%s"' % (i + 1, STATIC_DIR, static_dst))
        
    def _get_static_dir(self):
        return os.path.join(self._base_dir, STATIC_DIR)
        
    def _delete_existing_files(self):
        files = [os.path.join(self._base_dir, f) for f in os.listdir(self._base_dir) if f.endswith('.html')]
        [os.remove(f) for f in files]
        self._output('deleted %d html files' % len(files))
        static_path = self._get_static_dir()
        if os.path.exists(static_path):
            shutil.rmtree(static_path)
            self._output('deleted static dir: %s' % static_path)
        return files

    def _output(self, msg):
        print msg
