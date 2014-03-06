from _common import *
import os, shutil, json
import HTMLParser
import _template_renderer as tr
import re, base64, hashlib

def get_all_repos():
    for repo in os.listdir(REPOS_DIR):
        repo_path = os.path.join(REPOS_DIR, repo)
        if os.path.isdir(repo_path):
            yield repo, repo_path
            
class _File(object):
    def __init__(self, repo, file_type, filename):
        self.repo = repo
        self.file_type = file_type
        self.filename = filename
        self.path = os.path.join(REPOS_DIR, repo, file_type, filename)
        self.sort_on = (repo, file_type, filename)
        self.id = base64.urlsafe_b64encode(hashlib.md5(self.path).digest()[:10]).strip('=')
        
    @property
    def display(self):
        return '%s:%s' % (self.repo, self.filename)
    
    def is_match(self, repo, name, ext=''):
        if (repo is None or self.repo == repo):
            if name == self.filename:
                return True
            filename = name+ext
            if filename == self.filename:
                return True
        return False

class _File_Controller(object):
    DIR = ''
    EXTENSION = ''
    perm_files = ['.gitignore', 'readme.txt']
    
    def __init__(self):
        self.cfiles = {} #sorted(list(self._get_all_files()), key= lambda f: f.sort_on)
        for cf in self._get_all_files():
            self.cfiles[cf.id] = cf
    
    def _file_test(self, fn):
        return True
    
    def _get_all_files(self):
        for repo, repo_path in get_all_repos():
            directory = os.path.join(repo_path, self.DIR)
            for fn in os.listdir(directory):
                if self._file_test(fn) and fn not in self.perm_files:
                    yield _File(repo, self.DIR, fn)
    
    def get_file_content(self, fid = None, name=None, repo=None):
        cfile = self.get_cfile(fid, name, repo)
        with open(cfile.path, 'r') as handle:
            content = handle.read()
        return cfile.filename, cfile.repo, content
    
#     def copy_file(self, src, dst):
#         dst_path = self._get_path_extension(dst)
#         _, src_path = self.get_cfile(src)
#         shutil.copy(src_path, dst_path)
#         self.set_mod(dst_path)
#         return dst_path
    
    def write_file(self, content, repo, name):
        path = self._get_path_extension(repo, name)
        try:
            self.delete_file(path=path)
        except: pass
        with open(path, 'w') as handle:
            handle.write(content)
        self.set_mod(path)
        return path
    
    def set_mod(self, path):
        os.chmod(path, 0666)
    
    def delete_file(self, path = None, repo = None, filename = None):
        if path is None:
            cfile = self.get_cfile(filename = filename, repo=repo)
        os.remove(cfile.path)
        return cfile
    
#     def new_file_path(self, name):
#         name = name.strip('.')
#         name = re.sub(r'[\\/]', '', name)
#         return self.get_path(self._new_name(name))
    
    def _new_name(self, name, repo, num=1):
        def not_existing(name):
            if self.get_cfile(name=name, repo=repo) is None:
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
        
    def get_cfile(self, fid = None, filename=None, repo=None):
        if fid is not None:
            return self.cfiles[fid]
        for cf in self.cfiles.values():
            if cf.is_match(repo, filename, self.EXTENSION):
                return cf
        raise Exception('File %s : %s does not exist' % (repo, filename))
    
    def get_path(self, repo, name):
        return os.path.join(REPOS_DIR, repo, self.DIR, name)
    
    def _get_path_extension(self, repo, name):
        return self.get_path(repo, '%s%s' % (name, self.EXTENSION))
    
class Pages(_File_Controller):
    DIR = PAGE_DIR
    EXTENSION = '.json'
    _page = {}
    type_sets = [['string'], ['list'], ['html', 'markdown']]
    
    def __init__(self, *args, **kw):
        super(Pages, self).__init__(*args, **kw)
        self.pages = self._get_pages()
    
    def set_name(self, name, template, repo):
        self._repo = repo
        self._page.update({'name': name, 'template': template})
    
    def get_empty_context(self):
        repo_path = os.path.join(REPOS_DIR, self._repo)
        r = tr.RenderTemplate(self._page['template'], repo_path)
        return r.get_empty_context()
    
    def load_file(self, cfile):
        _, _, text = self.get_file_content(name=cfile.filename, repo=cfile.repo)
        return json.loads(text)
    
    def get_pages(self):
        return [(page, item.display) for page, item in self.pages]
    
    def _get_pages(self):
        return [(self.load_file(cfile), cfile) for cfile in self.cfiles.values()]
    
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
        if pid is not None:
            self._page, self._repo = next(((page, cfile.repo) for page, cfile in self.pages if page['id'] == pid))
        else:
            self._page, self._repo = next(((page, cfile.repo) for page, cfile in self.pages if page['name'] == name))
        return self._page, self._repo
    
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
        self._page['id'] = max([p['id'] for p, cf in self.pages]) + 1
        content = json.dumps(self._page, sort_keys=True, indent=4, separators=(',', ': '))
        return self.write_file(content, self._repo, self._page['name'])

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
    