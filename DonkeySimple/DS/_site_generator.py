import os, shutil
import markdown2
from _common import *
import _template_renderer as tr
import _controllers as con
from datetime import datetime as dtdt

class SiteGenerator(object):
    def __init__(self, output = None):
        if output:
            self._output = output
        self._base_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))

    def generate_entire_site(self):
        self._delete_existing_files()
        self._env = tr.get_env(self.global_context())
        for cf in self._page_con.cfiles.values():
            self.generate_page(cf)
        self.generate_statics()
    
    def generate_page(self, cfile):
        context = {}
        for var, item in cfile.info['context'].items():
            context[var] = item['value']
            if item['type'] == 'markdown':
                context[var] = markdown2.markdown(item['value'])
        r = tr.RenderTemplate(cfile.info['template'], cfile.info['template_repo'], env = self._env)
        content = r.render(context)
        ext = 'html'
        if 'extension' in cfile.info:
            ext = cfile.info['extension']
        fn = os.path.join(self._base_dir, '%s.%s' % (cfile.info['name'], ext))
        open(fn, 'w').write(content)
        os.chmod(fn, 0666)
        fn2 = fn
        if len(fn2) > 40:
            fn2 = '...%s' % fn2[-37:]
        self._output('Generated html file "%s" from page: %s, using template: %s' % \
                     (fn2, cfile.info['name'], cfile.info['template']))
        
    def global_context(self):
        self._page_con = con.Pages()
        context = {'static': 'static/', 'libs': 'static/libs/', 'todays_date': dtdt.now().strftime('%Y-%m-%d')}
        context['pages'] = []
        context['sitemap_pages'] = []
        for cf in self._page_con.cfiles.values():
            context['pages'].append(cf.info['name'])
            if 'sitemap' in cf.info:
                context['sitemap_pages'].append({'url': cf.info['name'], 'priority': cf.info['sitemap']})
        extra_context = con.GlobConFiles().get_entire_context()
        context.update(extra_context)
        return context
        
    def generate_statics(self):
        static_dst = self._get_static_dir()
        os.mkdir(static_dst)
        s = con.Statics()
        for i, src_cfile in enumerate(s.cfiles.values()):
            dst = os.path.join(static_dst, src_cfile.name)
            shutil.copy(src_cfile.path, dst)
        self._output('copied %d static files from "%s" to "%s"' % (i + 1, STATIC_DIR, static_dst))
        download_lib_statics(self._output)
        libfiles = con.LibraryFiles()
        libs_dest = os.path.join(static_dst, 'libs')
        for cf in libfiles.cfiles.values():
            libs_path = libfiles.libs_dir(cf)
            if os.path.exists(libs_path):
                self._copytree(libs_path, libs_dest)
        self._output("copied libs to site static directory")
        con.repeat_owners_permission(static_dst)
        
    def _copytree(self, src, dst, symlinks=False, ignore=None):
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, symlinks, ignore)
            else:
                shutil.copy2(s, d)
        
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

def download_lib_statics(output=None, delete_first=False):
    libfiles = con.LibraryFiles()
    if delete_first:
        libfiles.delete_libs(output)
    libfiles.download(output)


