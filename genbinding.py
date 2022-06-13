import os
import subprocess
from pathlib import Path
import argparse

try:
    import cppyy
except:
    print('Failed to import cppyy. Please make sure cppyy is installed correctly')
    exit(1)

parser = argparse.ArgumentParser(description='UTAP Python binding generator')
parser.add_argument('--home', dest='home', default=None,
                    help='Where UTAP\'s header folder is located')
parser.add_argument('--cxx', dest='cxx', default='c++',
                    help='the c++ compiler you use')
parser.add_argument('--out-dir', dest='out_dir',
                    default='.', help='output directory')

args = parser.parse_args()

user_home = args.home
cxx = args.cxx
rfldct = 'utap'

utap_homes = ['/usr/local/include',
              '/usr/include'] if user_home is None else [user_home]
utap_headers = []
utap_home = ''
# Attempt to find a valid home
for home in utap_homes:
    utap_headers = [os.path.relpath(x, home) for x in
                    Path(os.path.join(home, 'utap')).rglob('*.h')]
    if len(utap_headers) != 0:
        utap_home = home
        break
if utap_home == '':  # not found
    raise IOError('Cannot find UTAP headers in ' + str(utap_homes))

# Filter unwanted headers
utap_headers = [
    x for x in utap_headers if
    'signalflow' not in x    # does not work when generated, don't know why
]

print('---------generator information----------')
print('UTAP home   : %s' % utap_home)
print('C++ compiler  : %s' % cxx)
print('Generating wrapper via cppyy...')

# First we generate the redlection data
cmd = ' '.join(
    ['genreflex',                           # utility installed by pip when installing cppyy
        '--verbose',                        # Show information (somehow genreflex fail without this)
        '-s', 'selection.xml',              # selection file
        '-o', '%s_rflx.cpp' % rfldct,       # intermediate output file
        '-I/usr/include/libxml2',           # libxml2 include directory
        '--rootmap-lib=%s' % rfldct] +      # generate rootmap
    utap_headers)                           # headers themselves

ret = os.system(cmd)
if ret != 0:
    print("genereflex failed. Exit code {}".format(ret))
    exit(ret)
else:
    print("genreflex done")

# Next we build the Python module itself
print('Compiling binding...')
clingflags = subprocess.check_output(
    ['cling-config',                    # utility installed by pip when installing cppyy
        '--cppflags'])

try:
    subprocess.check_output(
        [cxx] +                                 # C++ compiler
        clingflags.split() + [                  # extra flags provided by cling
            '-fPIC',                            # require position independent code
            '-shared',                          # generate shared library
            '-std=c++1z',                       # cppyy should have set this but to be safe.
            '-o', '%s_rflx.so' % rfldct,        # output file
            '-I'+utap_home,                     # include search path for UTAP headers
            '-I/usr/include/libxml2',
            '%s_rflx.cpp' % rfldct] +           # intermediate file to compile
        ['-lutap', '-lxml2'])                   # link to UTAP

except subprocess.CalledProcessError as e:
    print('compilation failed (%d):' % e.returncode, e.output)
    exit(e.returncode)
else:
    print('compilation done')

    if not os.path.exists('libta/rfiles'):
        os.mkdir('libta/rfiles')

    os.rename('%s_rflx.so' % rfldct, 'libta/rfiles/' + '%s_rflx.so' % rfldct)
    os.rename('%s_rflx_rdict.pcm' %
              rfldct, 'libta/rfiles/' + '%s_rflx_rdict.pcm' % rfldct)
    os.rename('%s.rootmap' % rfldct, 'libta/rfiles/' + '%s.rootmap' % rfldct)
    os.remove('%s_rflx.cpp' % rfldct)
