from _common import *
import os, shutil
import HTMLParser
import _template_renderer as tr

class _File_Controller(object):
    DIR = ''
    EXTENSION = ''
    
    def _file_test(self, fn):
        return True
    
    def get_all_filenames(self):
        return [f for f in os.listdir(self.DIR) if self._file_test(f)]
    
    def get_file_content(self, name = None, fid = None):
        name, path = self._get_name(name, fid)
        with open(path, 'r') as handle:
            content = handle.read()
        return name, content
    
    def copy_file(self,src, dst):
        dst_path = self._get_path_extension(dst)
        _, src_path = self._get_name(src)
        shutil.copy(src_path, dst_path)
        os.chmod(dst_path, 0666)
        return dst_path
    
    def write_file(self, content, name):
        path = self._get_path_extension(name)
        try:
            self.delete_file(name)
        except: pass
        with open(path, 'w') as handle:
            handle.write(content)
        os.chmod(path, 0666)
        return path
    
    def delete_file(self, name):
        _, path = self._get_name(name)
        os.remove(path)
        return path
        
    def _get_name(self, name, fid = -1):
        files = self.get_all_filenames()
        if name is None:
            if fid is None or fid < 0:
                raise Exception('No valid file id provided')
            if fid >= len(files):
                raise Exception('File id %d is greater than number of files(%d)' %(fid, len(files)))
            name = files[fid]
        elif name not in files:
            name_ext = '%s%s'  % (name, self.EXTENSION)
            if name_ext in files:
                name = name_ext
            else:
                raise Exception('File "%s" does not exist: %r' % (name, files))
        return name, self.get_path(name)
    
    def get_path(self, name):
        return '%s/%s' % (self.DIR, name)
    
    def _get_path_extension(self, name):
        return '%s/%s%s' % (self.DIR, name, self.EXTENSION)
    
class Pages(_File_Controller):
    DIR = PAGE_DIR
    EXTENSION = '.json'
    _page = {}
    
    def set_name(self, name, template):
        self._page.update({'name': name, 'template': template})
    
    def get_empty_context(self):
        r = tr.RenderTemplate(self._page['template'])
        return r.get_empty_context()
    
    def load_file(self, page_file_name):
        _, text = self.get_file_content(name = page_file_name)
        return json.loads(text)
    
    def get_pages(self):
        return [self.load_file(fn) for fn in self.get_all_filenames()]
    
    def get_page(self, pid=None, name=None):
        pages = self.get_pages()
        if pid is not None:
            return next((page for page in pages if page['id'] == pid))
        else:
            return next((page for page in pages if page['name'] == name))
    
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
        
    def _file_test(self, fn):
        return fn.endswith(self.EXTENSION)
        
    def generate_page(self):
        return self._write()
        
    def _write(self):
        self._page['id'] = len(self.get_all_filenames())
        content = json.dumps(self._page, sort_keys=True, indent=4, separators=(',', ': '))
        return self.write_file(content, self._page['name'])

class Templates(_File_Controller):
    DIR = TEMPLATES_DIR
    
    def _file_test(self, fn):
        return '.template.' in fn

class Statics(_File_Controller):
    DIR = STATIC_DIR
    ignore_files = ['.gitignore', 'readme.txt']
    extension_groups = (
        ('Text', ('.js', '.json', '.css', '.html', '.txt')),
        ('Image', ('.png', '.jpeg', '.jpg', '.gif', '.bmp')),
        ('Font', ('.ttf')),
    )
    
    def _file_test(self, fn):
        return fn not in self.ignore_files
        
    def get_file_type(self, file_name):
        for name, extensions in self.extension_groups:
            if self._is_file_type(file_name, extensions):
                return name
        return 'Unknown Binary File'
    
    def _is_file_type(self, file_name, extensions):
        for ext in extensions:
            if file_name.endswith(ext):
                return True
        return False
    