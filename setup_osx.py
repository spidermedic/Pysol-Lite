"""
Command to create a macOS app bundle:
    PYTHONPATH=. python3 setup_osx.py py2app
"""

import os
import shutil
import sys
from subprocess import CalledProcessError, call, check_output

from pysollib.settings import COPYRIGHT_LINES, TITLE, VERSION

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

# libwebp (a Pillow dependency) depends on libsharpyuv via a bare
# @rpath reference that py2app's dependency walker doesn't follow.
# Bundle it explicitly.
SHARPYUV_LIB_PATH = None
try:
    _webp_prefix = check_output(
        ["brew", "--prefix", "webp"]).decode().strip()
    _candidate = os.path.join(_webp_prefix, "lib", "libsharpyuv.0.dylib")
    if os.path.exists(_candidate):
        SHARPYUV_LIB_PATH = _candidate
except (OSError, CalledProcessError):
    pass

COPYRIGHT = ' '.join(COPYRIGHT_LINES)
# The app's own identifier (macOS keys the Dock entry, Launch Services, the
# code signature and notarization to it). It was upstream PySolFC's
# net.sourceforge.pysolfc. Nothing in the program reads it: the settings
# folder and the saved games do not depend on it.
BUNDLE_ID = 'io.github.spidermedic.pysol-lite'
GETINFO_STRING = f"{TITLE} {VERSION}, a lighter PySol. {COPYRIGHT}"
PLIST = dict(
    CFBundleDevelopmentRegion='en_US',
    CFBundleExecutable=BUNDLE,
    CFBundleDisplayName=TITLE,
    CFBundleGetInfoString=GETINFO_STRING,
    CFBundleIdentifier=BUNDLE_ID,
    CFBundleName=BUNDLE,
    CFBundleVersion=f'{VERSION}',
    CFBundleShortVersionString=f'{VERSION}',
    NSHumanReadableCopyright=COPYRIGHT,
    )
APP = ['pysol.py']
ICON_FILE = 'data/PySol.icns'
DATA_FILES = ['data', 'LICENSE.md', 'THIRD-PARTY-LICENSES.md', 'README.md']
RESOURCES = []
FRAMEWORKS = [SHARPYUV_LIB_PATH] if SHARPYUV_LIB_PATH else []
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

# Tk 9 frameworks carry static stub libraries that codesign cannot sign, which
# makes py2app's own signing step fail. py2app already skips the Tk 8.6 names;
# add the Tk 9 ones.
if "py2app" in sys.argv:
    try:
        import py2app.build_app as _py2app_build
        _py2app_build._IGNORE_FILES.extend(['libtkstub.a', 'libtclstub.a'])
    except (ImportError, AttributeError):
        pass

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    )

#
top = os.getcwd()

# Drop the parts of the pygame package that nothing imports (docs, tests
# and examples, about 15 MB); the app only uses pygame.mixer. This runs
# before the bundle is signed below.
if "py2app" in sys.argv:
    _pygame_dir = os.path.join(
        top, 'dist', f'{BUNDLE}.app', 'Contents', 'Resources', 'lib',
        f'python{sys.version_info[0]}.{sys.version_info[1]}', 'pygame')
    for _name in ('docs', 'tests', 'examples'):
        shutil.rmtree(os.path.join(_pygame_dir, _name), ignore_errors=True)
    # pygame's default font (GNU FreeFont, 2002): pygame.font is not used, and
    # leaving the file out leaves one license less to describe
    _font = os.path.join(_pygame_dir, 'freesansbold.ttf')
    if os.path.exists(_font):
        os.remove(_font)
    # the Tk scripts in data/tcl are loaded only on X11 (winsystems/x11.py)
    shutil.rmtree(os.path.join(
        top, 'dist', '%s.app' % BUNDLE, 'Contents', 'Resources', 'data',
        'tcl'), ignore_errors=True)
    # python314.zip holds unused copies of PIL's .dylibs (PIL loads the ones
    # next to its .so in lib-dynload) and a test archive. Apple's notary
    # service looks inside zips and rejects the unsigned copies.
    _zip = os.path.join(
        top, 'dist', f'{BUNDLE}.app', 'Contents', 'Resources', 'lib',
        f'python{sys.version_info[0]}{sys.version_info[1]}.zip')
    if os.path.exists(_zip):
        call(['zip', '-q', '-d', _zip, 'PIL/.dylibs/*',
              'test/certdata/distrusted.zip'])
# Point libwebp at the bundled libsharpyuv instead of its broken
# original rpath.
if SHARPYUV_LIB_PATH and "py2app" in sys.argv:
    frameworks_dir = os.path.join(
        top, 'dist', f'{BUNDLE}.app', 'Contents', 'Frameworks')
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
if SHARPYUV_LIB_PATH and "py2app" in sys.argv:
    call([
        'codesign', '--force', '--deep', '--sign', '-',
        os.path.join(top, 'dist', f'{BUNDLE}.app'),
        ])

# py2app records the Python it was built with, which puts the build
# machine's path (and user name) into Info.plist. Nothing reads it at run
# time. Editing Info.plist breaks py2app's ad-hoc signature, so the build
# steps in the README sign the bundle again afterwards.
if "py2app" in sys.argv:
    import plistlib
    _plist_path = os.path.join(
        top, 'dist', f'{BUNDLE}.app', 'Contents', 'Info.plist')
    if os.path.exists(_plist_path):
        with open(_plist_path, 'rb') as _f:
            _info = plistlib.load(_f)
        if _info.get('PythonInfoDict', {}).pop('PythonExecutable', None):
            with open(_plist_path, 'wb') as _f:
                plistlib.dump(_info, _f)
