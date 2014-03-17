from DonkeySimple.DS.download import download_libraries
import os, re

lib_static_dir = os.path.join('DonkeySimple', 'WebInterface', 'static', 'libs')
libs_json_path = 'static_libraries.json'
try:
    download_libraries(libs_json_path, lib_static_dir)
except Exception, e:
    print 'ERROR: %s' % str(e)
    print 'Problem downloading libraries, you may have problems with internet connection.\n\n'
    
print 'generating long_descriptions docs for PyPi...'
import pandoc
pandoc.core.PANDOC_PATH = '/usr/bin/pandoc'
doc = pandoc.Document()
readme_file = 'README.md'
doc.markdown = open(readme_file, 'r').read()
docs_file = 'DonkeySimple/docs.txt'
open(docs_file,'w').write(doc.rst)
print '%s converted to rst and written to %s' % (readme_file, docs_file)
print 'changing version number'
setup_text = open('setup.py','r').read()
s=re.search("version='(.+?)'", setup_text)
v = s.groups()[0]
print 'setting version to: %s' % v
init_file = 'DonkeySimple/__init__.py'
init_text = "__version__ = 'v%s'" % v
open(init_file,'w').write(init_text)