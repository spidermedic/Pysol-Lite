"""Copy the bundled Standard cardset into ./cards as PNG (Kivy on Android
loads PNG reliably). Run once before building: python prepare.py"""
import os
from PIL import Image

SRC = os.path.join(os.path.dirname(__file__), '..', 'data', 'cardset-standard')
DST = os.path.join(os.path.dirname(__file__), 'cards')
os.makedirs(DST, exist_ok=True)
n = 0
for name in sorted(os.listdir(SRC)):
    base, ext = os.path.splitext(name)
    if ext != '.gif' or base == 'bottom01':
        continue
    if not (base.startswith('back111') or (len(base) == 3 and base[:2].isdigit()
                                          and base[2] in 'cdhs')):
        continue
    Image.open(os.path.join(SRC, name)).convert('RGBA').save(
        os.path.join(DST, base + '.png'))
    n += 1
print('wrote', n, 'card images to', DST)
