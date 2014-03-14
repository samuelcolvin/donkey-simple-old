from DonkeySimple.DS.download import download_libraries
import os

lib_static_dir = os.path.join('DonkeySimple', 'WebInterface', 'static', 'libs')
libs_json_path = 'static_libraries.json'
try:
    download_libraries(libs_json_path, lib_static_dir)
except Exception, e:
    print 'ERROR: %s' % str(e)
    print 'Problem downloading libraries, you may have problems with internet connection.\n\n'