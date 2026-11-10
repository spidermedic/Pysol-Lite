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

import tkinter


# ************************************************************************
# * constants
# ************************************************************************

EVENT_HANDLED = "break"
EVENT_PROPAGATE = None

CURSOR_DRAG = "hand1"
CURSOR_WATCH = "watch"
CURSOR_DOWN_ARROW = 'sb_down_arrow'

ANCHOR_CENTER = tkinter.CENTER
ANCHOR_N = tkinter.N
ANCHOR_NW = tkinter.NW
ANCHOR_NE = tkinter.NE
ANCHOR_S = tkinter.S
ANCHOR_SW = tkinter.SW
ANCHOR_SE = tkinter.SE
ANCHOR_W = tkinter.W
ANCHOR_E = tkinter.E

COMPOUNDS = (
    (tkinter.NONE,   'Icons only'),
    ('text',         'Text only'),
    (tkinter.TOP,    'Icons and text'),     # text below the icon
    )

# The Automatic play choices (same layout as ASSIST_OPTIONS).
AUTOMATIC_PLAY_OPTIONS = (
    ('autofaceup', 'Auto face-up', 'mOptAutoFaceUp'),
    ('autodrop', 'Auto drop', 'mOptAutoDrop'),
    ('autodeal', 'Auto deal', 'mOptAutoDeal'),
    ('quickplay', 'Quick play', 'mOptQuickPlay'),
)

# The Assist choices: (option and tkopt name, label, menubar handler).
ASSIST_OPTIONS = (
    ('shade', 'Shade legal moves', 'mOptShade'),
)

# General play choices: click to move instead of dragging, and asking before
# a game is thrown away.
PLAY_OPTIONS = (
    ('click_to_move', 'Click to move cards', 'mOptClickToMove'),
    ('confirm', 'Confirm before quitting', 'mOptConfirm'),
)

# Assist options that only matter for some games. The first one restarts
# the game when it changes, so it is applied last.
ASSIST_GAME_OPTIONS = (
    ('shisen_show_hint', 'Show hint arrow (in Shisen-Sho games)',
     'mOptShisenShowHint'),
    ('accordion_deal_all', 'Deal all cards (in Accordion type games)',
     'mOptAccordionDealAll'),
    ('mahjongg_show_removed', 'Show removed tiles (in Mahjongg games)',
     'mOptMahjonggShowRemoved'),
)

TOOLBAR_BUTTONS = (
    "new",
    "restart",
    "open",
    "save",
    "undo",
    "redo",
    "bookmark",
    "gotobookmark",
    "autodrop",
    "shuffle",
    "hint",
    "pause",
    "rules",
    )
