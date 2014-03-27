import os, shutil
import markdown2
from _common import *
import _template_renderer as tr
import _controllers as con
from datetime import datetime as dtdt
settings = None

class SiteGenerator(object):
    def __init__(self, output = None):
        global settings
        settings = get_settings()
        if output:
            self._output = output
        self._base_dir = settings.SITE_PATH
        self._tmp_base_dir = settings.SITE_PATH_TMP

    def generate_entire_site(self):
        self._output('Generating site in temp: %s ...' % self._short_path(self._tmp_base_dir))
        if os.path.exists(self._tmp_base_dir):
            shutil.rmtree(self._tmp_base_dir)
        os.mkdir(self._tmp_base_dir)
        self._env = tr.get_env(self.global_context())
        for cf in self._page_con.cfiles.values():
            self.generate_page(cf)
        self.generate_statics()
        delete_type = ('partially', 'completely-')[settings.DELETE_ENTIRE_SITE_PATH]
        self._output('site succesfully generated, deleting live %s...' % delete_type)
        if settings.DELETE_ENTIRE_SITE_PATH:
            if os.path.exists(self._base_dir):
                shutil.rmtree(self._base_dir)
            self._output('moving temp to live in bulk...')
            shutil.move(self._tmp_base_dir, self._base_dir)
        else:
            if os.path.exists(self._base_dir):
                self._delete_relevent()
            else:
                os.mkdir(self._base_dir)
                os.chmod(self._base_dir, 0777)
            self._output('moving temp to live one by one...')
            for f in os.listdir(self._tmp_base_dir):
                path = os.path.join(self._tmp_base_dir, f)
                shutil.move(path, self._base_dir)
            shutil.rmtree(self._tmp_base_dir)
        self._output('site copied to live, temp deleted: %s' % self._base_dir)
    
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
        if 'extension' in cfile.info and cfile.info['extension'] != "":
            ext = '.%s' % cfile.info['extension']
            if cfile.info['extension'].lower() == 'none':
                ext = ''
        name = cfile.info['name']
        if name.startswith('dot.'):
            name = name[3:]
        fn = os.path.join(self._tmp_base_dir, '%s%s' % (name, ext))
        open(fn, 'w').write(content)
        os.chmod(fn, 0666)
        self._output('File generated "%s" using template: %s' % (self._short_path(fn), cfile.info['template']))
        
    def _short_path(self, path):
        path2 = path
        max_length = 50
        if len(path2) > max_length:
            path2 = '...%s' % path2[-(max_length-3):]
        return path2
        
    def global_context(self):
        self._page_con = con.Pages()
        context = {'static': 'static/', 
                   'libs': 'static/libs/', 
                   'todays_date': dtdt.now().strftime('%Y-%m-%d'),
                   'this_page': '[set during page generation]'}
        if not hasattr(settings, 'SITE_URL'):
            raise Exception('settings.SITE_URL is not set')
        index = settings.SITE_URL
        self._output('Site URL: ' + index)
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
        
    def generate_statics(self):
        static_dst = self._get_static_dir(self._tmp_base_dir)
        os.mkdir(static_dst)
        os.chmod(static_dst, 0777)
        s = con.Statics()
        for i, src_cfile in enumerate(s.cfiles.values()):
            dst = os.path.join(static_dst, src_cfile.name)
            shutil.copy(src_cfile.path, dst)
        self._output('copied %d static files from "%s" to "%s"' % (i + 1, STATIC_DIR, self._short_path(static_dst)))
        download_lib_statics(self._output)
        libfiles = con.LibraryFiles()
        libs_dest = os.path.join(static_dst, 'libs')
        copied_libs = False
        for cf in libfiles.cfiles.values():
            libs_path = libfiles.libs_dir(cf)
            if os.path.exists(libs_path):
                self._copytree(libs_path, libs_dest)
                copied_libs = True
        if copied_libs:
            self._output("copied libs to site static directory")
        con.repeat_owners_permission(static_dst)
        
    def _copytree(self, src, dst, symlinks=False, ignore=None):
        if not os.path.exists(dst):
            os.mkdir(dst)
            os.chmod(dst, 0777)
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, symlinks, ignore)
            else:
                shutil.copy2(s, d)
                
    def _delete_relevent(self):
        special_files = ['sitemap.xml', '.htaccess']
        files = [os.path.join(self._base_dir, f) for f in os.listdir(self._base_dir) if f.endswith('.html') or f in special_files]
        [os.remove(f) for f in files]
        self._output('deleted %d relevent files: %s' % (len(files), ', '.join(files)))
        static_path = self._get_static_dir(self._base_dir)
        if os.path.exists(static_path):
            shutil.rmtree(static_path)
            self._output('deleted static dir: %s' % static_path)
        return files
        
    def _get_static_dir(self, base):
        return os.path.join(base, STATIC_DIR)

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


