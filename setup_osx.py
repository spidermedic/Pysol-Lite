"""
Command to create a macOS app bundle:
    PYTHONPATH=. python3 setup_osx.py py2app
"""

import os
import shutil
import sys
from subprocess import CalledProcessError, call, check_output

from pysollib.settings import TITLE, VERSION

# The bundle (PySol.app) and its executable keep the same name every year;
# only the display name carries the year.
BUNDLE = 'PySol Lite'

from setuptools import setup  # noqa: E402


# build the rule pages
if not os.path.exists('data/html'):
    os.chdir('html-src')
    call([sys.executable, './gen-html.py'])
    os.chdir(os.pardir)
    shutil.copytree('html-src/images', 'html-src/html/images')
    try:
        shutil.rmtree('data/html')
    except OSError:
        pass
    shutil.copytree('html-src/html', 'data/html')

# trim the card back choices in the (separately downloaded) cardsets
call([sys.executable, './scripts/prune_card_backs.py', 'data'])

# Use Freecell Solver, if it is installed.
# http://fc-solve.berlios.de/
SOLVER_LIB_PATH = "/usr/local/lib/libfreecell-solver.0.dylib"
SOLVER = ["/usr/local/bin/fc-solve"]
if not os.path.exists(SOLVER_LIB_PATH):
    SOLVER_LIB_PATH = None
    SOLVER = []

# libwebp (a Pillow dependency) depends on libsharpyuv via a bare
# @rpath reference that py2app's dependency walker doesn't follow.
# Bundle it explicitly, same as the solver lib above.
SHARPYUV_LIB_PATH = None
try:
    _webp_prefix = check_output(
        ["brew", "--prefix", "webp"]).decode().strip()
    _candidate = os.path.join(_webp_prefix, "lib", "libsharpyuv.0.dylib")
    if os.path.exists(_candidate):
        SHARPYUV_LIB_PATH = _candidate
except (OSError, CalledProcessError):
    pass

GETINFO_STRING = "%s %s, a lighter PySol. \
                (C) 1998-2003 Markus F.X.J Oberhumer \
                (C) 2005-2009 Skomoroh" % (TITLE, VERSION)
PLIST = dict(
    CFBundleDevelopmentRegion='en_US',
    CFBundleExecutable=BUNDLE,
    CFBundleDisplayName=TITLE,
    CFBundleGetInfoString=GETINFO_STRING,
    CFBundleIdentifier='net.sourceforge.pysolfc',
    CFBundleName=BUNDLE,
    CFBundleVersion='%s' % VERSION,
    CFBundleShortVersionString='%s' % VERSION,
    NSHumanReadableCopyright="Copyright (C) 1998-2003 Markus F.X.J. Oberhumer",
    )
APP = ['pysol.py']
ICON_FILE = 'data/PySol.icns'
DATA_FILES = ['data', 'COPYING', 'README.md',
              ] + SOLVER
RESOURCES = []
FRAMEWORKS = ([SOLVER_LIB_PATH] if SOLVER_LIB_PATH else []) + \
             ([SHARPYUV_LIB_PATH] if SHARPYUV_LIB_PATH else [])
# with argv_emulation=True, the app window is not shown when launched
OPTIONS = dict(argv_emulation=False,
               # off: it starts the login shell in a pseudo-tty at every launch
               # (about 1 s) and the app needs none of that environment
               emulate_shell_environment=False,
               plist=PLIST,
               iconfile=ICON_FILE,
               resources=RESOURCES,
               frameworks=FRAMEWORKS,
               # not needed at run time (about 7 MB)
               excludes=['setuptools', 'pkg_resources', 'distutils']
               )

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    )

#
top = os.getcwd()
# Modify the fc-solve binary with install_name_tool to use the dependent
# libfreecell-solver dynamic library in the app bundle.
if SOLVER and "py2app" in sys.argv:
    os.chdir('dist/%s.app/Contents/Resources' % BUNDLE)
    call(["install_name_tool", "-change",
          "/usr/local/lib/libfreecell-solver.0.dylib",
          "@executable_path/../Frameworks/libfreecell-solver.0.dylib",
          "fc-solve"])
    os.chdir(top)

# Point libwebp at the bundled libsharpyuv instead of its broken
# original rpath.
if SHARPYUV_LIB_PATH and "py2app" in sys.argv:
    frameworks_dir = os.path.join(
        top, 'dist', '%s.app' % BUNDLE, 'Contents', 'Frameworks')
    for name in os.listdir(frameworks_dir):
        if name.startswith('libwebp'):
            call([
                'install_name_tool', '-change',
                '@rpath/libsharpyuv.0.dylib',
                '@executable_path/../Frameworks/libsharpyuv.0.dylib',
                os.path.join(frameworks_dir, name),
                ])

# install_name_tool invalidates py2app's ad-hoc signature above, and
# macOS refuses to launch a bundle whose seal doesn't match its
# contents. Re-sign after any post-processing.
if (SOLVER or SHARPYUV_LIB_PATH) and "py2app" in sys.argv:
    call([
        'codesign', '--force', '--deep', '--sign', '-',
        os.path.join(top, 'dist', '%s.app' % BUNDLE),
        ])

# py2app records the Python it was built with, which puts the build
# machine's path (and user name) into Info.plist. Nothing reads it at run
# time. Editing Info.plist breaks py2app's ad-hoc signature, so the build
# steps in the README sign the bundle again afterwards.
if "py2app" in sys.argv:
    import plistlib
    _plist_path = os.path.join(
        top, 'dist', '%s.app' % BUNDLE, 'Contents', 'Info.plist')
    if os.path.exists(_plist_path):
        with open(_plist_path, 'rb') as _f:
            _info = plistlib.load(_f)
        if _info.get('PythonInfoDict', {}).pop('PythonExecutable', None):
            with open(_plist_path, 'wb') as _f:
                plistlib.dump(_info, _f)
