"""
File controller class with inheritted classes for each type of file.
"""
from _common import *
import os, shutil, json
import HTMLParser
import _template_renderer as tr
import re, base64, hashlib, pwd, subprocess
from download import download_libraries

def get_all_repos():
    """
    Generator for all repos in the site.
    """
    for repo in os.listdir(REPOS_DIR):
        repo_path = os.path.join(REPOS_DIR, repo)
        if os.path.isdir(repo_path):
            yield repo, repo_path
            
def new_repo_path(repo):
    """
    Generate path for a new repo, throw error if it exists
    """
    repo = re.sub(r'[\\/]', '', repo)
    repo_path = os.path.join(REPOS_DIR, repo)
    if os.path.exists(repo_path):
        raise(Exception('path "%s" already exists, cannot create repo' % repo_path))
    return repo, repo_path

def repeat_owners_permission(path = REPOS_DIR):
    subprocess.call('chmod -R a+u %s' % path, shell=True)
    
def delete_tree(repo_path):
    shutil.rmtree(repo_path)
            
class _File(object):
    """
    Represents a single file, either page, template or static file.
    """
    info = None
    active_cfile = None
    def __init__(self, repo, file_type, filename, ext = ''):
        self.repo = repo
        self.file_type = file_type
        self.filename = filename
        self.ext = ext
        self.path = os.path.join(REPOS_DIR, repo, file_type, filename)
        self.sort_on = (repo, file_type, filename)
        self.id = base64.urlsafe_b64encode(hashlib.md5(self.path).digest()[:10]).strip('=')
        
    @property
    def display(self):
        """
        Display property for the file.
        """ 
        name = self.filename.replace(self.ext, '')
        return '%s :: %s' % (self.repo, name)
    
    @property
    def repo_path(self):
        return os.path.join(REPOS_DIR, self.repo)
    
    def is_match(self, repo, name, ext=''):
        """
        Identifies whether or not this file matches the details provided.
        """
        if (repo is None or self.repo == repo):
            if name == self.filename:
                return True
            filename = name+ext
            if filename == self.filename:
                return True
        return False
    
    def delete_file(self):
        os.remove(self.path)
    
    def write_file(self, content):
        try:
            self.delete_file()
        except: pass
        with open(self.path, 'w') as handle:
            handle.write(content)
        self.set_mod()
    
    def set_mod(self):
        chmod_own(self.path, 0666)

class _File_Controller(object):
    """
    Parent class for control of all files in a given directory: eg. pages, templates or static
    """
    DIR = ''
    EXTENSION = ''
    perm_files = ['.gitignore', 'readme.txt']
    
    def __init__(self):
        self.cfiles = {}
        for cf in self._get_all_files():
            self.cfiles[cf.id] = cf
    
    def _file_test(self, fn):
        """
        Tests whether a given file should be included in control.
        """
        return True
    
    def _get_all_files(self):
        """
        Generates list of _File objects of all files in self.DIR in each repo.
        """
        for repo, repo_path in get_all_repos():
            directory = os.path.join(repo_path, self.DIR)
            if not os.path.exists(directory):
                os.mkdir(directory)
                chmod_own(directory, 0777)
            for fn in os.listdir(directory):
                if self._file_test(fn) and fn not in self.perm_files:
                    yield _File(repo, self.DIR, fn, self.EXTENSION)
    
    def get_file_content(self, fid = None, name=None, repo=None):
        """
        Gets the content of a file either via file id or name and repo.
        """
        if fid is not None:
            cfile = self.cfiles[fid]
        else:
            cfile = self.get_cfile_name(name, repo)
        with open(cfile.path, 'r') as handle:
            content = handle.read()
        return cfile, content
    
    def copy_file(self, src_cfile, dst_cfile):
        shutil.copy(src_cfile.path, dst_cfile.path)
        dst_cfile.set_mod()
        self.cfiles.pop(src_cfile.id)
        return dst_cfile
    
    def write_file(self, content, repo, name):
        cfile = self.create_cfile(repo, name)
        cfile.write_file(content)
        return cfile
    
    def create_cfile(self, repo, name):
        self.active_cfile = _File(repo, self.DIR, self._valid_name(name))
        self.cfiles[self.active_cfile.id] = self.active_cfile
        return self.active_cfile
    
    def delete_file(self, path = None, repo = None, filename = None):
        if path is None:
            cfile = self.get_cfile_name(filename, repo)
        cfile.delete_file()
        return self.cfiles.pop(cfile.id)
    
    def new_file_path(self, repo, name):
        name = name.strip('.')
        name = re.sub(r'[\\/]', '', name)
        return self.get_path(self._new_name(repo, name))
    
    def _new_name(self, name, repo, num=1):
        def not_existing(name):
            if self.get_cfile_name(name, repo) is None:
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
    
    def get_cfile_fid(self, pid):
        self.active_cfile = self.cfiles[pid]
        return self.active_cfile 
    
    def get_cfile_name(self, filename, repo):
        """
        File a cfile based on name and repo.
        """
        for cf in self.cfiles.values():
            if cf.is_match(repo, filename, self.EXTENSION):
                return cf
        raise Exception('File %s : %s does not exist' % (repo, filename))
    
    def get_path(self, repo, name):
        return os.path.join(REPOS_DIR, repo, self.DIR, name)
    
    def _valid_name(self, name):
        """
        add the file extension if needed and make sure this is just a filename not a path.
        """
        name = os.path.basename(name)
        if name.endswith(self.EXTENSION):
            return name
        else:
            return '%s%s' % (name, self.EXTENSION)

class Pages(_File_Controller):
    DIR = PAGE_DIR
    EXTENSION = '.json'
    type_sets = [['string'], ['list'], ['html', 'markdown']]
    
    def __init__(self, *args, **kw):
        super(Pages, self).__init__(*args, **kw)
        self._generate_pages()
    
    def create_cfile(self, repo, name, template):
        super(Pages, self).create_cfile(repo, name)
        self.active_cfile.info = {'name': name, 'template': template}
    
    def get_empty_context(self):
        repo_path = os.path.join(REPOS_DIR, self.active_cfile.repo)
        r = tr.RenderTemplate(self.active_cfile.info['template'], self.active_cfile.repo_path)
        return r.get_empty_context()
    
    def load_file(self, cfile):
        _, text = self.get_file_content(cfile.id)
        return json.loads(text)
    
    def _generate_pages(self):
        """
        Add page info to cfile.info.
        """
        for key, cfile in self.cfiles.items():
            self.cfiles[key].info = self.load_file(cfile)
    
    def get_true_context(self):
        context = {}
        for name, item in self.get_empty_context().items():
            context[name] = item
            if name in self.active_cfile.info['context']:
                context[name]['value'] = self.active_cfile.info['context'][name]['value']
            if self.active_cfile.info['context'][name]['type'] != item['type']:
                for ts in self.type_sets:
                    if self.active_cfile.info['context'][name]['type'] in ts and item['type'] in ts:
                        context[name]['type'] = self.active_cfile.info['context'][name]['type']
                        break
        return context
    
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
        self.active_cfile.info['context'] = context
        
    def _file_test(self, fn):
        return fn.endswith(self.EXTENSION)
        
    def generate_page(self):
        return self._write()
        
    def _write(self):
        self.active_cfile.info['id'] = max([cf.info['id'] for cf in self.cfiles.values() if 'id' in cf.info]) + 1
        content = json.dumps(self.active_cfile.info, sort_keys=True, indent=4, separators=(',', ': '))
        self.active_cfile.write_file(content)
        return self.active_cfile

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

class LibraryFiles(_File_Controller):
    DIR = ''
    EXTENSION = '.json'
    
    def _get_all_files(self):
        """
        Generates list of _File objects of all lib json files.
        """
        for repo, repo_path in get_all_repos():
            lib_file_path = os.path.join(repo_path, LIBRARY_JSON_FILE)
            if os.path.exists(lib_file_path):
                yield _File(repo, self.DIR, LIBRARY_JSON_FILE, self.EXTENSION)

    def download(self, target, output):
        for cf in self.cfiles.values():
            download_libraries(cf.path, target, output = output)

def chmod_own(path, perms):
#     http_id = pwd.getpwnam(HTTP_USER).pw_uid
#     local_id = pwd.getpwnam(LOCAL_USER).pw_uid
    os.chmod(path, perms)
#     os.lchown(path, -1, local_id)
    