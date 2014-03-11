import shutil, os, json, urllib2
import _controllers as con

def create_ds(path):
    if os.path.exists(path):
        if len(os.listdir(path)) != 0:
            raise Exception('Path "%s" already exists and is not empty, please specify a new or empty path' % path)
        else:
            os.rmdir(path)
    this_dir = os.path.dirname(os.path.realpath(__file__))
    site_template = os.path.realpath(os.path.join(this_dir, '../site-template'))
    shutil.copytree(site_template, path)
    con.repeat_owners_permission(path)
    full_path = os.path.realpath(path)
    print 'Site generated at:\n%s' % full_path
    print 'default username: donkey, password: simple'
    print 'run "donkeysimple edituser" to change the password, or login and change.'
    
def download_libraries(libs_json_path, target, output = None):
    
    if output:
        outfunc = output
    else:
        outfunc = _output
#     libs_json_path = os.path.join(THIS_PATH, 'libraries.json')
    url_files = json.load(open(libs_json_path, 'r'))
    downloaded = 0
    ignored = 0
    for url, path in url_files.items():
        #self._output('DOWNLOADING: %s\n             --> %s...' % (url, path))
        dest = os.path.join(target, 'external', path)
        if os.path.exists(dest):
            #self._output('file already exists at ./%s' % path)
            #self._output('*** IGNORING THIS DOWNLOAD ***\n')
            ignored += 1
            continue
        dest_dir = os.path.dirname(dest)
        if not os.path.exists(dest_dir):
            # self._output('mkdir: %s' % dest_dir)
            os.makedirs(dest_dir)
        try:
            response = urllib2.urlopen(url)
            content = response.read()
        except Exception, e:
            outfunc('\nURL: %s\nProblem occured during download: %r' % (url, e))
            outfunc('*** ABORTING ***')
            return False
        open(dest, 'w').write(content.encode('utf8'))
        downloaded += 1
        #self._output('Successfully downloaded %s\n' % os.path.basename(path))
    outfunc('library download finish: %d files downloaded, %d existing and ignored' % (downloaded, ignored))
    return True

def _output(line):
    print line