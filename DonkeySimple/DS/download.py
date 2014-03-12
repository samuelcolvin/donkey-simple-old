import os, json, urllib2, zipfile, cStringIO, re

def download_libraries(libs_json_path, target, output = None, file_perm = None):
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
    
    def write(dest, content):
        open(dest, 'w').write(content)
        if file_perm:
            os.chmod(dest, file_perm)
    
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
                        write(dest, zipf.read(fn))
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
            write(dest, content)
        downloaded += 1
    outfunc('library download finished: %d files downloaded, %d existing and ignored' % (downloaded, ignored))
    return True

def _output(line):
    print line