"""
File controller class with inheritted classes for each type of file.
"""
from _common import *
import os, shutil, json, zipfile
import HTMLParser
import _template_renderer as tr
import re, base64, hashlib, pwd, subprocess
from download import download_libraries
from _git import Change2Directory
            
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
    
def zip_dir(path2zip, zip_file_path, arcfolder, path_check = None):
    zipf = zipfile.ZipFile(zip_file_path, 'w')
    with Change2Directory(path2zip):
        for root, _, files in os.walk('.'):
            for f in files:
                file_path = os.path.join(root, f)
                if path_check:
                    if not path_check(file_path):
                        continue
                arc_name = os.path.join(arcfolder, file_path)
                zipf.write(file_path, arc_name)
    zipf.close()
    repeat_owners_permission(zip_file_path)
    
def zip_repos(zip_file_path):
    return zip_dir(REPOS_DIR, zip_file_path, REPOS_DIR)
    
def delete_tree(repo_path):
    shutil.rmtree(repo_path)
            
class _File(object):
    """
    Represents a single file, either page, template or static file.
    """
    info = None
    active_cfile = None
    def __init__(self, repo, file_type, name, ext = ''):
        self.repo = repo
        self.file_type = file_type
        self.name = name
        self.ext = ext
        self.path = os.path.join(REPOS_DIR, repo, file_type, name)
        self.sort_on = (repo, file_type, name)
        self.id = base64.urlsafe_b64encode(hashlib.md5(self.path).digest()[:10]).strip('=')
        
    @property
    def display(self):
        """
        Display property for the file.
        """ 
        name = self.name.replace(self.ext, '')
        return '%s :: %s' % (self.repo, name)
    
    @property
    def repo_path(self):
        return os.path.join(REPOS_DIR, self.repo)
    
    def is_match(self, repo, name, ext=''):
        """
        Identifies whether or not this file matches the details provided.
        """
        if (repo is None or self.repo == repo):
            if name == self.name:
                return True
            name = name+ext
            if name == self.name:
                return True
        return False
    
    def delete_file(self):
        os.remove(self.path)
    
    def write_file(self, content):
        chunking = hasattr(content, 'next')
        write_setting = ('w', 'wb')[chunking]
        try:
            self.delete_file()
        except: pass
        with open(self.path, write_setting) as handle:
            if chunking:
                for chunk in content:
                    handle.write(chunk)
            else:
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
                file_path = os.path.join(directory, fn)
                if os.path.isfile(file_path) and self._file_test(fn) and fn not in self.perm_files:
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
    
    def delete_file(self, path = None, repo = None, name = None):
        if path is None:
            cfile = self.get_cfile_name(name, repo)
        cfile.delete_file()
        return self.cfiles.pop(cfile.id)
    
    def new_file_path(self, repo, name):
        name = name.strip('.')
        name = re.sub(r'[\\/]', '', name)
        return self.get_path(repo, self._new_name(repo, name))
    
    def _new_name(self, name, repo, num=1):
        def not_existing(name):
            if self.get_cfile_name(name, repo, no_exist_error = False) is None:
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
    
    def get_cfile_name(self, name, repo, no_exist_error = True):
        """
        File a cfile based on name and repo.
        """
        for cf in self.cfiles.values():
            if cf.is_match(repo, name, self.EXTENSION):
                return cf
        if no_exist_error:
            raise Exception('File %s : %s does not exist' % (repo, name))
    
    def get_path(self, repo, name):
        return os.path.join(REPOS_DIR, repo, self.DIR, name)
    
    def _valid_name(self, name):
        """
        add the file extension if needed and make sure this is just a file name not a path.
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
    
    def create_cfile(self, repo, name, template, template_repo):
        super(Pages, self).create_cfile(repo, name)
        self.active_cfile.info = {'name': name, 'template': template, 'template_repo': template_repo}
    
    def get_empty_context(self):
        r = tr.RenderTemplate(self.active_cfile.info['template'], self.active_cfile.info['template_repo'])
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
            else:
                context[name]['value'] = None
        return context
    
    def update_context(self, fields, f_types):
        print fields
        context = {}
        if 'extension' in fields:
            self.active_cfile.info['extension'] = fields['extension']
        if 'sitemap' in fields:
            self.active_cfile.info['sitemap'] = fields['sitemap']
        for name, item in self.get_empty_context().items():
            if name in fields:
                context[name] = item
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
        print self.cfiles
        cf_id = 1
        existing_cf_ids = [cf.info['id'] for cf in self.cfiles.values() if 'id' in cf.info]
        if len(existing_cf_ids) > 0:
            cf_id = max(existing_cf_ids) + 1
        self.active_cfile.info['id'] = cf_id
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

class _SingleJSONFile(_File_Controller):
    DIR = ''
    EXTENSION = '.json'
    FILE_NAME = 'unknown.json'
    
    def _get_all_files(self):
        """
        Generates list of _File objects of all lib json files.
        """
        for repo, repo_path in get_all_repos():
            lib_file_path = os.path.join(repo_path, self.FILE_NAME)
            if os.path.exists(lib_file_path):
                yield _File(repo, self.DIR, self.FILE_NAME, self.EXTENSION)

class LibraryFiles(_SingleJSONFile):
    FILE_NAME = LIBRARY_JSON_FILE
                
    def delete_libs(self, output):
        output('deleting old static libraries...')
        for cf in self.cfiles.values():
            path = self.libs_dir(cf)
            if os.path.exists(path):
                shutil.rmtree(path)
        
    def download(self, output):
        libs_path = None
        for cf in self.cfiles.values():
            libs_path = self.libs_dir(cf)
            download_libraries(cf.path, libs_path, output = output)
        if libs_path:
            repeat_owners_permission(libs_path)
    
    def libs_dir(self, cf):
        return os.path.join(REPOS_DIR, cf.repo, STATIC_DIR, 'libs')

class GlobConFiles(_SingleJSONFile):
    FILE_NAME = GLOBCON_JSON_FILE
    
    def get_entire_context(self):
        context = {}
        for cf in self.cfiles.values():
            with open(cf.path, 'r') as fhandler:
                context.update(json.load(fhandler))
        return context

def chmod_own(path, perms):
#     http_id = pwd.getpwnam(settings.HTTP_USER).pw_uid
#     local_id = pwd.getpwnam(settings.LOCAL_USER).pw_uid
    os.chmod(path, perms)
#     os.lchown(path, -1, local_id)