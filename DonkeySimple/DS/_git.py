import git, os, subprocess, traceback

class _Git(object):
    """
    Simple git controller class.
    """
    DEFAULT_FILES = {}
    def __init__(self, gdir, output=None):
        self.gdir = gdir
        self.dot_gdir = os.path.join(gdir, '.git')
        if output is not None:
            self._output = output
                
    def pull_clone_create(self, url = None):
        """
        Pulls, clones or creates based status of repo and url.
        """
        if os.path.exists(self.gdir):
            if os.path.exists(self.dot_gdir):
                self._output('Pulling:')
                self.pull()
            else:
                self._output('Not a git repo, not initialising')
                self.create_repo()
        else:
            if url:
                self._output('Cloning:')
                self.clone(url)
            else:
                self._output('Creating Repo:')
                self.create_repo()
                
    def open_create(self):
        """
        Open repo or create if it doesn't exist.
        
        returns whether or not repo already existed.
        """
        if os.path.exists(self.dot_gdir):
            self._output('Opening Repo')
            self.open_repo()
            return True
        else:
            self._output('Creating Repo')
            self.create_repo()
            return False
    
    def clone(self, url):
        self._output(git.Git().clone(url, self.gdir))
        # or self.repo.clone(folder)
        self.open_repo()
        
    def pull(self):
        response = None
        if self.has_remotes(self._open_repo()):
            response = self._output(git.cmd.Git(self.gdir).pull())
        else:
            self._output('No remotes, not pulling.')
        self.open_repo()
        return response
        # (or self.repo.remotes.origin.pull(), but cmd gives more details)
    
    def create_repo(self):
        self.repo = git.Repo.init(self.gdir)
        for fname, content in self.DEFAULT_FILES.items():
            path = os.path.join(self.gdir, fname)
            open(path, 'w').write(content)
        
    def open_repo(self):
        self.repo = self._open_repo()
    
    def _open_repo(self):
        return git.Repo(self.gdir)
                
    def status(self):
        return self._output(self.repo.git.status())
    
    def uptodate(self, status = None):
        """
        whether or not the repo is up-to-date eg. matches remotes
        with no untracked or modified files.
        """
        if status is None:
            status = self.status()
        return 'nothing to commit, working directory clean' in status \
                and 'Your branch is ahead' not in status
        
    def tracked_files(self):
        return [name for name, _ in self.repo.index.entries.keys()]
        
    def untracked_files(self):
        return self.repo.untracked_files
        
    def modified_files(self):
        return [diff.a_blob.name for diff in self.repo.index.diff(None)]
    
    
    def add_all(self, do_untracked=True):
        """
        Stage modified and (optionally) untracked files.
        """
        with Change2Directory(self.gdir):
            self._do_command('git add %s' % ('', '-A')[do_untracked])
        
    def commit(self, message, all=True):
        with Change2Directory(self.gdir):
            p=self._do_command('git commit %s -m "%s"' % (('', '-a')[all], message))
            return self._output(p.stdout.read())
#         return self._output(self.repo.git.commit(m= ' "%s"' % message, a=''))
#         return self._output(self.repo.index.commit(message))
        
    def push(self):
        #return self._output(self.repo.remotes.origin.push())
        return self._output(git.cmd.Git(self.gdir).push())
        
    def has_remotes(self, repo = None):
        if repo is None:
            repo = self.repo
        return len(repo.remotes) > 0
        
    def _output(self, *args):
        if len(args) == 1:
            print args[0]
            return args[0]
        for arg in args:
            print arg
        return args
    
    def set_user(self, email, name):
        with Change2Directory(self.gdir):
            commands = ('git config user.email "%s"' % email,
                        'git config user.name "%s"' % name)
            for c in commands:
                self._do_command(c)
            
    def _do_command(self, command):
        return subprocess.Popen(command, 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, 
                               shell=True)
        
class Git(_Git):
    DEFAULT_FILES = {'.gitignore': '/static/libs/'}
    
class Change2Directory(object):
    """
    change working directory and always return
    """
    def __init__(self, change_to):
        self.change_to = change_to
    
    def __enter__(self):
        self.working_path = os.getcwd()
        os.chdir(self.change_to)
    
    def __exit__(self, type, value, traceback):
        os.chdir(self.working_path)