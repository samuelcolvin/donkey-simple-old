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
        self._output('Generating page: %s...' % cfile.info['name'])
        context = {'this_page': cfile.info['name']}
        for var, item in cfile.info['context'].items():
            context[var] = item['value']
            if item['type'] == 'markdown':
                context[var] = markdown2.markdown(item['value'])
        r = tr.RenderTemplate(cfile.info['template'], cfile.info['template_repo'], env = self._env)
        content = r.render(context)
        ext = '.html'
        if 'extension' in cfile.info:
            ext = '.%s' % cfile.info['extension']
            if cfile.info['extension'].lower() == 'none':
                ext = ''
        name = cfile.info['name']
        if name.startswith('dot.'):
            name = name[3:]
        fn = os.path.join(self._base_dir, '%s%s' % (name, ext))
        open(fn, 'w').write(content)
        os.chmod(fn, 0666)
        fn2 = fn
        if len(fn2) > 40:
            fn2 = '...%s' % fn2[-37:]
        self._output('File generated "%s" using template: %s' % (fn2, cfile.info['template']))
        
    def global_context(self):
        self._page_con = con.Pages()
        context = {'static': 'static/', 
                   'libs': 'static/libs/', 
                   'todays_date': dtdt.now().strftime('%Y-%m-%d'),
                   'this_page': '[set during page generation]'}
        index = self._get_site_uri()
        index_slash = index
        if not index_slash.endswith('/'):
            index_slash += '/'
        if index:
            context['index'] = index
        context['pages'] = []
        context['sitemap_pages'] = []
        for cf in self._page_con.cfiles.values():
            url = cf.info['name']
            if url == 'index':
                url = index
            else:
                url = index_slash + url
            context['pages'].append(url)
            if 'sitemap' in cf.info:
                priority = 0.1
                try:
                    priority = '%0.1f' % float(cf.info['sitemap'])
                except:
                    self._output('Failed to convert sitemap priority to float: %s' % cf.info['sitemap'])
                context['sitemap_pages'].append({'url': url, 'priority': priority})
        context['sitemap_pages'].sort(key=lambda u: -float(u['priority']))
        extra_context = con.GlobConFiles().get_entire_context()
        context.update(extra_context)
        return context
    
    def _get_site_uri(self):
        index = None
        try:
            import settings
        except:
            self._output('Problem inporting settings, not setting index URI')
        else:
            if hasattr(settings, 'SITE_URI'):
                index = settings.SITE_URI
            if 'REQUEST_URI' in os.environ:
                auto_uri = os.environ['REQUEST_URI']
                auto_uri = auto_uri[:auto_uri.index('/edit/')]
                if index and auto_uri != index:
                    self._output('Auto detected URI (%s) does not match settings.SITE_URI (%s)' % (auto_uri, index))
                if not index:
                    index = auto_uri
        return index
        
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
        if not os.path.exists(dst):
            os.mkdir(dst)
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
        special_files = ['sitemap.xml', '.htaccess']
        files = [os.path.join(self._base_dir, f) for f in os.listdir(self._base_dir) if f.endswith('.html') or f in special_files]
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
    
def site_zip(zip_path):
    def path_check(path):
        if path.startswith('./%s/' % STATIC_DIR):
            return True
        path = path.lstrip('.' + os.path.sep)
        if os.path.sep in path:
            return False
        return True
    con.zip_dir('..', zip_path, 'site', path_check)


