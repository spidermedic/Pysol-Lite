#!/usr/bin/env python3
"""Trim the card back choices in the cardsets under data/.

Every cardset keeps only its default back (line 5 of config.txt), except
the ones listed in KEEP below, which also keep the backs named there. Backs that are dropped are removed from the list on line 6 of
config.txt and their image files are deleted. Safe to run repeatedly.

The cardsets are a separate download and are not in git, so setup_osx.py
runs this before every build.

    python3 scripts/prune_card_backs.py [data-dir]
"""
import os
import sys

# cardset directory -> backs to keep besides the default one.
KEEP = {
    # Standard: these seven of the original ten are kept.
    'cardset-standard': ['back101.gif', 'back102.gif', 'back111.gif',
                         'back121.gif', 'back122.gif', 'back191.gif',
                         'back192.gif'],
}


def prune(data_dir):
    removed = 0
    for name in sorted(os.listdir(data_dir)):
        cfg = os.path.join(data_dir, name, 'config.txt')
        if not name.startswith('cardset-') or not os.path.isfile(cfg):
            continue
        with open(cfg, encoding='latin-1', newline='') as f:
            lines = f.read().split('\n')
        if len(lines) < 6:
            continue
        cr = '\r' if lines[5].endswith('\r') else ''
        default = lines[4].strip()
        listed = [b.strip() for b in lines[5].strip().split(';') if b.strip()]
        keep = [b for b in listed if b == default or b in KEEP.get(name, [])]
        drop = [b for b in listed if b not in keep]
        if not drop:
            continue
        lines[5] = ';'.join(keep) + cr
        with open(cfg, 'w', encoding='latin-1', newline='') as f:
            f.write('\n'.join(lines))
        for b in drop:
            path = os.path.join(data_dir, name, b)
            if os.path.exists(path):
                os.remove(path)
                removed += 1
    return removed


if __name__ == '__main__':
    n = prune(sys.argv[1] if len(sys.argv) > 1 else 'data')
    print('removed %d card back files' % n)
