import git, os

class Git(object):
    """
    Similar git controller class.
    """
    def __init__(self, gdir, url=None):
        self.gdir = gdir
        self.url = url
        if os.path.exists(gdir):
            self._pull()
        else:
            if url:
                self._clone()
            else:
                self._create_repo()
    
    def _clone(self, url):
        print git.Git().clone(self.url, self.gdir)
        # or self.repo.clone(folder)
        self.repo = self._open_repo()
        
    def _pull(self):
        print git.cmd.Git(self.gdir).pull()
        self.repo = self._open_repo()
        # (or self.repo.remotes.origin.pull(), but cmd gives more details)
    
    def _create_repo(self):
        self.repo = git.Repo.init(self.gdir)
    
    def _open_repo(self):
        return git.Repo(self.gdir)
    
    def add_all(self, do_untracked=True):
        """
        Stage modified and (optionally) untracked files.
        """
        # or could use self.repo.git.commit(m="message", a=True)
        if self.repo.is_dirty():
            modified = self.modified_files()
            print 'staging modified:', modified
            self.add(modified)
        if do_untracked:
            untracked = self.repo.untracked_files
            if len(untracked) > 0:
                print 'adding untracked:', untracked
                self.add(untracked)
                
    def get_status(self):
        return sel.repo.git.status()
        
    def tracked_files(self):
        return [name for name, _ in self.repo.index.entries.keys()]
        
    def untracked_files(self):
        return self.repo.untracked_files
        
    def modified_files(self):
        return [diff.a_blob.name for diff in self.repo.index.diff(None)]
    
    def add(self, rel_paths):
        """
        Stage list of files.
        """
        self.repo.index.add(rel_paths)
        
    def commit(self, msg):
        return self.repo.index.commit(msg)
        
    def push(self):
        return self.repo.remotes.origin.push()
        # or git.cmd.Git('testing2.git').push() gives no more details