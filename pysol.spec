# PyInstaller spec for the Windows build of PySol Lite.
# Run from the repo root via scripts/build_windows.ps1 (or
# `pyinstaller --noconfirm pysol.spec`). Not used on macOS (setup_osx.py).
import os

from PyInstaller.utils.hooks import collect_submodules

# the game modules are imported by package (pysollib.games, ...) at run time
hiddenimports = collect_submodules('pysollib')

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
    icon='data/pysol.ico',
)
coll = COLLECT(exe, a.binaries, a.datas, name='PySol Lite')
