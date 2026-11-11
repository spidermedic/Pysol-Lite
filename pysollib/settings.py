#!/usr/bin/env python
# -*- mode: python; coding: utf-8; -*-
# ---------------------------------------------------------------------------##
#
# Copyright (C) 1998-2003 Markus Franz Xaver Johannes Oberhumer
# Copyright (C) 2003 Mt. Hood Playing Card Co.
# Copyright (C) 2005-2009 Skomoroh
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ---------------------------------------------------------------------------##

import os


# PACKAGE is stored in saved games and checked when loading them, and names
# the data directories; keep it stable. The settings folder is ~/.pysol.
PACKAGE = 'PySolFC'
# Releases are versioned by date: version 26.MM[.DD].
# VERSION_TUPLE is (YY, MM) for a monthly release and (YY, MM, DD) for an
# interim update in the same month.
VERSION_TUPLE = (26, 11)
VERSION = '.'.join(['%d' % VERSION_TUPLE[0]] +
                   ['%02d' % x for x in VERSION_TUPLE[1:]])
# Class name for the Tk windows and the X11 resource database (no year).
TITLE_CLASS = 'PySol'
TITLE = 'PySol Lite'
PACKAGE_URL = 'https://github.com/spidermedic/pysol'

# Tk windowing system (auto set up in init.py)
WIN_SYSTEM = 'x11'                      # win32, x11, aqua, classic

# sound
# available values:
#   'pss' - PySol-Sound-Server (all)
#   'pygame' - PyGame (all)
#   'oss' (*nix)
#   'win' (windows)
#   'none' - disable
SOUND_MOD = 'auto'

# freecell-solver
USE_FREECELL_SOLVER = True
FCS_COMMAND = 'fc-solve'
# FCS_HOME = None                         # path to fcs presets files

# data dirs
DATA_DIRS = []
# you can add your extra directories here
if os.name == 'posix':
    DATA_DIRS = [
        '/app/share/PySolFC',
        '/usr/share/PySolFC',
        '/usr/local/share/PySolFC',
        '/usr/share/games/PySolFC',
        '/usr/local/share/games/PySolFC',
        ]
if os.name == 'nt':
    pass

TOP_SIZE = 10
TOP_TITLE = 'Top 10'

# use menu for select game
SELECT_GAME_MENU = True

# i18n, see also options.py
TRANSLATE_GAME_NAMES = True

# debug
DEBUG = 0                               # must be integer
CHECK_GAMES = False                     # check duplicated names and classes
