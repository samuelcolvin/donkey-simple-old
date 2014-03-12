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
        for cf in page_controller.cfiles.values():
            self.generate_page(cf)
        self.generate_statics()
    
    def generate_page(self, cfile):
        context = {}
        for var, item in cfile.info['context'].items():
            context[var] = item['value']
            if item['type'] == 'markdown':
                context[var] = markdown2.markdown(item['value'])
        r = tr.RenderTemplate(cfile.info['template'], cfile.repo_path)
        content = r.render(context)
        fn = os.path.join(self._base_dir, '%s.html' % cfile.info['name'])
        open(fn, 'w').write(content)
        os.chmod(fn, 0666)
        fn2 = fn
        if len(fn2) > 40:
            fn2 = '...%s' % fn2[-37:]
        self._output('Generated html file "%s" from page: %s, using template: %s' % \
                     (fn2, cfile.info['name'], cfile.info['template']))
        
    def generate_statics(self):
        static_dst = self._get_static_dir()
        os.mkdir(static_dst)
        s = con.Statics()
        for i, src_cfile in enumerate(s.cfiles.values()):
            dst = os.path.join(static_dst, src_cfile.filename)
            shutil.copy(src_cfile.path, dst)
        self._output('copied %d static files from "%s" to "%s"' % (i + 1, STATIC_DIR, static_dst))
        external_statics = os.path.join(static_dst, 'libs')
        libfiles = con.LibraryFiles()
        libfiles.download(external_statics, self._output)
        con.repeat_owners_permission(static_dst)
        
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
