import shutil, os, json, urllib2, zipfile, cStringIO, re
import _controllers as con
from random_string import get_random_string

def create_ds(path):
    if os.path.exists(path):
        if len(os.listdir(path)) != 0:
            raise Exception('Path "%s" already exists and is not empty, please specify a new or empty path' % path)
        else:
            os.rmdir(path)
    this_dir = os.path.dirname(os.path.realpath(__file__))
    site_template = os.path.realpath(os.path.join(this_dir, '../site-template'))
    shutil.copytree(site_template, path)
    full_path = os.path.realpath(path)
    print 'Site template copied, Downloading static files...'
    external_static_dir = os.path.join(path, 'edit', 'static', 'external')
    libs_json_path = os.path.join(os.path.dirname(__file__), '../static_libraries.json')
    try:
        download_libraries(libs_json_path, external_static_dir)
    except Exception, e:
        print 'ERROR: %s' % str(e)
        print 'Problem downloading libraries, you may have problems with internet connection.\n\n'
    print 'Generating short random variable for cookies...'
    settings_file = os.path.join(path, 'edit', 'settings.py')
    text = open(settings_file, 'r').read()
    random_text = get_random_string(8)
    text = text.replace('short_random_var', random_text)
    open(settings_file, 'w').write(text)
    print 'Changing files to replicate owner permissions for all'
    con.repeat_owners_permission(path)
    print '==========================='
    print 'SITE GENERATED SUCCESSFULLY'
    print '==========================='
    print 'location: %s' % full_path
    print 'default username: donkey, password: simple'
    print 'run "donkeysimple edituser" to change the password, or login and change.'
    
def download_libraries(libs_json_path, target, output = None):
    def generate_path(*path_args):
        dest = os.path.join(*path_args)
        if os.path.exists(dest):
            return True, None
        dest_dir = os.path.dirname(dest)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        return False, dest
    
    def get_url(url):
        try:
            response = urllib2.urlopen(url)
            return response.read()
        except Exception, e:
            raise Exception('URL: %s\nProblem occurred during download: %r\n*** ABORTING ***' % (url, e))
    
    if output:
        outfunc = output
    else:
        outfunc = _output
    url_files = json.load(open(libs_json_path, 'r'))
    downloaded = 0
    ignored = 0
    for url, value in url_files.items():
        if url.endswith('zip') and type(value) == dict:
            if all([os.path.exists(os.path.join(target, p)) for p in value.values()]):
                ignored += 1
                continue
            outfunc('DOWNLOADING ZIP: %s...' % url)
            content = get_url(url)
            zipinmemory = cStringIO.StringIO(content)
            with zipfile.ZipFile(zipinmemory) as zipf:
                print '%d file in zip archive' % len(zipf.namelist())
                zcopied = 0
                for fn in zipf.namelist():
                    for regex, dest_path in value.items():
                        m = re.search(regex, fn)
                        if not m:
                            continue
                        new_fn = m.groupdict()['file']
                        _, dest = generate_path(target, dest_path, new_fn)
                        open(dest, 'w').write(zipf.read(fn))
                        zcopied += 1
                        break
            outfunc('%d files copied from zip archive to target' % zcopied)
        else:
            fn_replace = '{{ *filename *}}'
            if re.search(fn_replace, value):
                filename = re.search('.*/(.*)',url).groups()[0]
                path = re.sub(fn_replace, filename, value)
            else:
                path = value
            exists, dest = generate_path(target, path)
            if exists:
                ignored += 1
                continue
            outfunc('DOWNLOADING: %s' % path)
            content = get_url(url)
            try: content = content.encode('utf8')
            except: pass
            open(dest, 'w').write(content)
        downloaded += 1
    outfunc('library download finished: %d files downloaded, %d existing and ignored' % (downloaded, ignored))
    return True

def _output(line):
    print line