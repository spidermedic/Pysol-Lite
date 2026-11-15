#!/usr/bin/env python
# -*- mode: python; coding: utf-8; -*-
# ---------------------------------------------------------------------------##
#
#  Copyright (C) 1998-2003 Markus Franz Xaver Johannes Oberhumer
#  Copyright (C) 2003 Mt. Hood Playing Card Co.
#  Copyright (C) 2005-2009 Skomoroh
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ---------------------------------------------------------------------------##

import locale
import os
import sys

import pysollib.settings

# ************************************************************************
# * init
# ************************************************************************


def init():

    locale.setlocale(locale.LC_ALL, '')

    # debug
    if 'PYSOL_CHECK_GAMES' in os.environ or 'PYSOL_DEBUG' in os.environ:
        pysollib.settings.CHECK_GAMES = True
        print('PySol debugging: set CHECK_GAMES to True')
    if 'PYSOL_DEBUG' in os.environ:
        try:
            pysollib.settings.DEBUG = int(os.environ['PYSOL_DEBUG'])
        except Exception:
            pysollib.settings.DEBUG = 1
        print(('PySol debugging: set DEBUG to', pysollib.settings.DEBUG))

    if '--version' in sys.argv:
        print("{} version {}".format(pysollib.settings.TITLE,
                                     pysollib.settings.VERSION))
        sys.exit(0)

    # init Tk
    import tkinter
    root = tkinter.Tk(className=pysollib.settings.TITLE_CLASS)
    root.withdraw()
    if tkinter.TkVersion < 8.4:
        # we need unicode support
        sys.exit("%s needs Tcl/Tk 8.4 or better (you have %s)" %
                 (pysollib.settings.TITLE, str(tkinter.TkVersion)))
    pysollib.settings.WIN_SYSTEM = root.tk.call('tk', 'windowingsystem')
    # "can't invoke event <<ThemeChanged>>: application has been destroyed"
    root.destroy()
    tkinter._default_root = None

    # run app without games menus (more fast start)
    if '--no-games-menu' in sys.argv:
        sys.argv.remove('--no-games-menu')
        pysollib.settings.SELECT_GAME_MENU = False
