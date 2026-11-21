# PyInstaller spec for the Windows and Linux builds of PySol Lite.
# Windows: scripts/build_windows.ps1. Linux: scripts/build_appimage.sh.
# Or `pyinstaller --noconfirm pysol.spec`. Not used on macOS (setup_osx.py).
import os
import sys

from PyInstaller.utils.hooks import collect_submodules

# the game modules are imported by package (pysollib.games, ...) at run time
hiddenimports = collect_submodules('pysollib')
# Pillow loads this dynamically; without it ImageTk fails in the frozen Linux app
hiddenimports.append('PIL._tkinter_finder')

datas = [
    ('data', 'data'),
    ('LICENSE.md', '.'),
    ('THIRD-PARTY-LICENSES.md', '.'),
    ('README.md', '.'),
]

a = Analysis(
    ['pysol.py'],
    pathex=['.'],
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=['setuptools', 'pkg_resources', 'distutils'],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PySol Lite',
    console=bool(os.environ.get('PYSOL_CONSOLE')),
    icon='data/pysol.ico' if sys.platform == 'win32' else None,
)
coll = COLLECT(exe, a.binaries, a.datas, name='PySol Lite')
