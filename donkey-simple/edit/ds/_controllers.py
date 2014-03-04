from _common import *
import os, shutil, json
import HTMLParser
import _template_renderer as tr
import re

class _File_Controller(object):
    DIR = ''
    EXTENSION = ''
    perm_files = ['.gitignore', 'readme.txt']
    
    def __init__(self):
        self.items = sorted(list(self._get_all_items()))
    
    def _file_test(self, fn):
        return True
    
    def _get_all_items(self):
        for repo in os.listdir(REPOS_DIR):
            if os.path.isdir(os.path.join(REPOS_DIR, repo)):
                directory = os.path.join(REPOS_DIR, repo, self.DIR)
                for fn in os.listdir(directory):
                    if self._file_test(fn) and fn not in self.perm_files:
                        path = os.path.join(directory, fn)
                        display_name = '%s:%s' % (repo, fn)
                        yield {'repo': repo, 'name': fn, 'path': path, 'display': display_name}
    
    def get_file_content(self, fid = None, name=None, repo=None):
        item = self._get_name(fid, name, repo)
        with open(item['path'], 'r') as handle:
            content = handle.read()
        return item['name'], content
    
#     def copy_file(self, src, dst):
#         dst_path = self._get_path_extension(dst)
#         _, src_path = self._get_name(src)
#         shutil.copy(src_path, dst_path)
#         self.set_mod(dst_path)
#         return dst_path
    
    def write_file(self, content, name):
        path = self._get_path_extension(name)
        try:
            self.delete_file(path=path)
        except: pass
        with open(path, 'w') as handle:
            handle.write(content)
        self.set_mod(path)
        return path
    
    def set_mod(self, path):
        os.chmod(path, 0666)
    
    def delete_file(self, name = None, path = None):
        if path is None:
            path = self._get_name(name)['path']
        os.remove(path)
        return path
    
#     def new_file_path(self, name):
#         name = name.strip('.')
#         name = re.sub(r'[\\/]', '', name)
#         return self.get_path(self._new_name(name))
    
    def _new_name(self, name, repo, num=1):
        def not_existing(name):
            if self._get_name(name=name, repo=repo) is None:
                return True
            return name not in self.perm_files
        if not_existing(name):
            return name
        num_str = ('', '_%d' % num)[num>1]
        if '.' in name:
            dot = name.index('.')
            new_name = name[:dot] + num_str + name[dot:]
        else:
            new_name = name + num_str
        if not_existing(new_name):
            return new_name
        return self._new_name(name, repo, num + 1)
        
    def _get_name(self, fid = None, name=None, repo=None):
        if fid is not None:
            return self.items[fid]
        for item in self.items:
            if repo is not None and item['repo'] != repo:
                continue
            if item['name'] == name:
                return item
    
    def get_path(self, repo, name):
        return os.path.join(REPOS_DIR, repo, self.DIR, name)
    
    def _get_path_extension(self, name):
        return self.get_path('%s%s' % (name, self.EXTENSION))
    
class Pages(_File_Controller):
    DIR = PAGE_DIR
    EXTENSION = '.json'
    _page = {}
    type_sets = [['string'], ['list'], ['html', 'markdown']]
    
    def set_name(self, name, template):
        self._page.update({'name': name, 'template': template})
    
    def get_empty_context(self):
        repo_path = os.path.join(REPOS_DIR, self._repo)
        r = tr.RenderTemplate(self._page['template'], repo_path)
        return r.get_empty_context()
    
    def load_file(self, item):
        _, text = self.get_file_content(name=item['name'], repo=item['repo'])
        return json.loads(text)
    
    def get_pages(self):
        return [(page, item['display']) for page, item in self._get_pages()]
    
    def _get_pages(self):
        return [(self.load_file(item), item) for item in self.items]
    
    def get_true_context(self):
        context = {}
        for name, item in self.get_empty_context().items():
            context[name] = item
            if name in self._page['context']:
                context[name]['value'] = self._page['context'][name]['value']
            if self._page['context'][name]['type'] != item['type']:
                for ts in self.type_sets:
                    if self._page['context'][name]['type'] in ts and item['type'] in ts:
                        context[name]['type'] = self._page['context'][name]['type']
                        break
        return context
    
    def get_page(self, pid=None, name=None):
        page_items = self._get_pages()
        if pid is not None:
            self._page, self._repo = next(((page, item['repo']) for page, item in page_items if page['id'] == pid))
        else:
            self._page, self._repo = next(((page, item['repo']) for page, item in page_items if page['name'] == name))
        return self._page
    
    def update_context(self, fields, f_types):
        context = {}
        for name, item in self.get_empty_context().items():
            context[name] = item
            if name in fields:
                text = fields[name]
                if item['type'] in ['html', 'markdown']:
                    text = HTMLParser.HTMLParser().unescape(text)
                context[name]['value'] = text
            if name in f_types:
                context[name]['type'] = f_types[name]
        self._page['context'] = context
        
    def _file_test(self, fn):
        return fn.endswith(self.EXTENSION)
        
    def generate_page(self):
        return self._write()
        
    def _write(self):
        self._page['id'] = len(self.items)
        content = json.dumps(self._page, sort_keys=True, indent=4, separators=(',', ': '))
        return self.write_file(content, self._page['name'])

class Templates(_File_Controller):
    DIR = TEMPLATES_DIR
    
    def _file_test(self, fn):
        return '.template.' in fn

class Statics(_File_Controller):
    DIR = STATIC_DIR
    extension_groups = (
        ('Text', ('.js', '.json', '.css', '.html', '.txt')),
        ('Image', ('.png', '.jpeg', '.jpg', '.gif', '.bmp')),
        ('Font', ('.ttf')),
    )
    
    def _file_test(self, fn):
        return True
        
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
    