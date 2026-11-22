"""Stage the files for the Android build into ./stage (run before buildozer).

    python android_app/stage.py

Copies pysollib (without the Tk-only code), the data the Kivy UI needs, and
main.py. The Standard cardset is converted from GIF to PNG, because the
Kivy UI cannot load GIFs reliably (upstream PySolFC does the same).
Needs Pillow.
"""
import os
import re
import shutil
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STAGE = os.path.join(HERE, 'stage')


def ignore_code(dirpath, names):
    skip = {'__pycache__', '.DS_Store'}
    rel = os.path.relpath(dirpath, ROOT)
    if rel == 'pysollib':
        skip |= {'tile', 'ui'}              # Tk only
    return [n for n in names if n in skip or n.endswith('.pyc')]


def ignore_data(dirpath, names):
    return [n for n in names if n == '.DS_Store' or n.endswith('.gif')]


def convert_cardset(src, dst):
    shutil.copytree(src, dst, ignore=ignore_data)
    for name in sorted(os.listdir(src)):
        base, ext = os.path.splitext(name)
        if ext == '.gif':
            Image.open(os.path.join(src, name)).convert('RGBA').save(
                os.path.join(dst, base + '.png'))
    cfg = os.path.join(dst, 'config.txt')
    with open(cfg, encoding='utf-8') as f:
        text = f.read()
    with open(cfg, 'w', encoding='utf-8') as f:
        f.write(text.replace('.gif', '.png'))


def main():
    if os.path.isdir(STAGE):
        shutil.rmtree(STAGE)
    os.makedirs(STAGE)
    shutil.copytree(os.path.join(ROOT, 'pysollib'),
                    os.path.join(STAGE, 'pysollib'), ignore=ignore_code)
    shutil.copy(os.path.join(HERE, 'main.py'), STAGE)
    data = os.path.join(STAGE, 'data')
    os.makedirs(data)
    for name in ('images', 'sound', 'html', 'cardset-uni-mahjongg'):
        shutil.copytree(os.path.join(ROOT, 'data', name),
                        os.path.join(data, name), ignore=ignore_data)
    convert_cardset(os.path.join(ROOT, 'data', 'cardset-standard'),
                    os.path.join(data, 'cardset-standard'))
    # keep the version in one place: settings.py
    with open(os.path.join(ROOT, 'pysollib', 'settings.py'),
              encoding='utf-8') as f:
        m = re.search(r"^VERSION_TUPLE = \((\d+), (\d+)\)", f.read(), re.M)
    version = f"{m.group(1)}.{m.group(2)}" if m else '0.0'
    with open(os.path.join(STAGE, 'version.txt'), 'w') as f:
        f.write(f"VERSION = {version}\n")
    n = sum(len(files) for _, _, files in os.walk(STAGE))
    print(f"staged {n} files in {STAGE}")


if __name__ == '__main__':
    sys.exit(main())
