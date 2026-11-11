#!/usr/bin/env python3

import os
import sys

from pysollib.gamedb import GAME_DB
from pysollib.mfxutil import latin1_normalize
from pysollib.settings import VERSION
# outdir = '../html'
pysollib_dir = '../'

import pysollib.games  # noqa: E402,F402,I100,I202
import pysollib.games.mahjongg  # noqa: E402,F402
import pysollib.games.special  # noqa: E402,F401,F402

try:
    os.mkdir('html')
except Exception:
    pass

try:
    os.mkdir('html/rules')
except Exception:
    pass


def merge_dicts(x, y):
    ret = x.copy()
    ret.update(y)
    return ret


pysollib_path = os.path.join(sys.path[0], pysollib_dir)
sys.path[0] = os.path.normpath(pysollib_path)
# print sys.path


files = [
    ('credits.html', 'PySol Lite Credits'),
    ('credits_old.html', 'PySol Lite Credits'),
    ('faq.html', 'PySol Lite - FAQ'),
    ('general_rules.html', 'PySol Lite - General Rules'),
    ('glossary.html', 'PySol Lite - Glossary'),
    ('howtoplay.html', 'How to Use PySol Lite'),
    ('accessibility.html', 'PySol Lite - Accessibility'),
    ('index.html', 'PySol Lite - a Solitaire Game Collection'),
    ('intro.html', 'PySol Lite - Introduction'),
    ('license.html', 'PySol Software License'),
    # ('rules_alternate.html', 'PySol Lite - a Solitaire Game Collection'),
    # ('rules.html', 'PySol Lite - a Solitaire Game Collection'),
    ('settings.html', 'PySol Lite - Settings'),
    ('assist_options.html', 'PySol Lite - Assist Options'),
    ('cardset_customization.html', 'PySol Lite - Cardset Customization'),
    ]

rules_files = [
    ('mahjongg.html', 'PySol Lite - Rules for Mahjongg'),
    ('shisensho.html', 'PySol Lite - Rules for Shisen-Sho'),
    ('spider.html', 'PySol Lite - Rules for Spider'),
    ('freecell.html', 'PySol Lite - Rules for FreeCell'),
    ]


def _fmt(fmt, params):
    return fmt % merge_dicts(params, {'logo_url': "images/pysollogo03.png",
                                      'logo_alt': "PySol Lite Logo"})


main_header = '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2//EN">
<html>
<head>
<title>%(title)s</title>
<meta name="license" content="GNU General Public License">
<meta http-equiv="content-type" content="text/html; charset=utf-8">
</head>
<body text="#000000" bgcolor="#F7F3FF" link="#0000FF" vlink="#660099"
alink="#FF0000">
<img src="%(logo_url)s" alt="%(logo_alt)s">
<br>
'''
main_footer = '''
<p>
<br>
%(back_to_index_link)s
<hr>
<i>PySol Lite Documentation - version ''' + VERSION + '''</i>
</body>
</html>'''

rules_header = '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2//EN">
<html>
<head>
<title>%(title)s</title>
<meta name="license" content="GNU General Public License">
<meta http-equiv="content-type" content="text/html; charset=utf-8">
</head>
<body text="#000000" bgcolor="#F7F3FF" link="#0000FF" vlink="#660099"
link="#FF0000">
<img src="../%(logo_url)s" alt="%(logo_alt)s">
<br>
'''
rules_footer = '''
<p>
%(footer)s
<br>
<a href="../glossary.html">Glossary</a>
<br>
<a href="../general_rules.html">General rules</a>

<p>
<a href="../index.html">Back to the index</a>
<br>
<a href="../rules.html">Back to individual game rules</a>
<hr>
<i>PySol Lite Documentation - version ''' + VERSION + '''</i>
</body>
</html>'''

wikipedia_header = '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2//EN">
<html>
<head>
<title>%(title)s</title>
<meta name="license" content="GNU General Public License">
<meta http-equiv="content-type" content="text/html; charset=utf-8">
</head>
<body text="#000000" bgcolor="#F7F3FF" link="#0000FF" vlink="#660099"
alink="#FF0000">
<img src="../%(logo_url)s" alt="%(logo_alt)s">
<br>
'''


def _get_game_rules_filename(n):
    if n.startswith('Mahjongg'):
        return 'mahjongg.html'
    return latin1_normalize(n) + '.html'


def gen_main_html():
    for infile, title in files:
        outfile = open(os.path.join('html', infile), 'w', encoding='utf-8')
        print(_fmt(main_header, {'title': title}), file=outfile)
        with open(infile, 'r', encoding='utf-8') as file:
            print(file.read(), file=outfile)
        s = '<a href="index.html">Back to the index</a>'
        if infile == 'index.html':
            s = ''
        print(_fmt(main_footer, {'back_to_index_link': s}), file=outfile)
        outfile.close()


def gen_rules_html():
    # ls = glob(os.path.join('rules', '*.html'))
    rules_ls = sorted(os.listdir('rules'))
    wikipedia_ls = sorted(os.listdir('wikipedia'))

    games = GAME_DB.getGamesIdSortedByName()
    rules_list = []
    files_list = []
    for fn, tt in rules_files:
        rules_list.append(('rules', fn, tt, ''))
        files_list.append(fn)
    altnames = []

    # open file of list of all rules
    out_rules = open(os.path.join('html', 'rules.html'), 'w', encoding='utf-8')
    print(_fmt(main_header, {'title': 'PySol Lite - a Solitaire Game Collection'}),
          file=out_rules)
    with open('rules.html', 'r', encoding='utf-8') as file:
        print(file.read(), file=out_rules)

    for id in games:
        # create list of rules

        gi = GAME_DB.get(id)

        rules_fn = gi.rules_filename
        if not rules_fn:
            rules_fn = _get_game_rules_filename(gi.name)

        if rules_fn in rules_ls:
            rules_dir = 'rules'
        elif rules_fn in wikipedia_ls:
            rules_dir = 'wikipedia'
        else:
            print('missing rules for %s (file: %s)'
                  % (gi.name, rules_fn))
            continue

        # print '>>>', rules_fn
        if rules_fn not in files_list:
            title = 'PySol Lite - Rules for ' + gi.name
            s = ''
            rules_list.append((rules_dir, rules_fn, title, s))
        files_list.append(rules_fn)
        # rules_list.append((rules_fn, gi.name))
        print('<li><a href="rules/%s">%s</a>'
              % (rules_fn, gi.name), file=out_rules)
        for n in gi.altnames:
            altnames.append((n, rules_fn))

    print('</ul>\n' + _fmt(main_footer,
          {'back_to_index_link':
           '<a href="index.html">Back to the index</a>'}),
          file=out_rules)

    out_rules.close()

    # create file of altnames
    out_rules_alt = open(os.path.join('html', 'rules_alternate.html'), 'w',
                         encoding='utf-8')
    print(_fmt(main_header, {'title': 'PySol Lite - a Solitaire Game Collection'}),
          file=out_rules_alt)
    with open('rules_alternate.html', 'r', encoding='utf-8') as file:
        print(file.read(), file=out_rules_alt)
    altnames.sort(key=lambda x: x[0].lower())
    for name, fn in altnames:
        print('<li> <a href="rules/%s">%s</a>'
              % (fn, name), file=out_rules_alt)
    print('</ul>\n' + _fmt(main_footer,
          {'back_to_index_link':
           '<a href="index.html">Back to the index</a>'}),
          file=out_rules_alt)
    out_rules_alt.close()

    # create rules
    for dir, filename, title, footer in rules_list:
        outfile = open(
            os.path.join('html', 'rules', filename), 'w', encoding='utf-8')
        if dir == 'rules':
            print(_fmt(rules_header, {'title': title}), file=outfile)
        else:  # d == 'wikipedia'
            print(_fmt(wikipedia_header, {'title': title}), file=outfile)
        with open(os.path.join(dir, filename), 'r', encoding='utf-8') as file:
            print(file.read(), file=outfile)
        print(_fmt(rules_footer, {'footer': footer}), file=outfile)
        outfile.close()


gen_main_html()
gen_rules_html()
