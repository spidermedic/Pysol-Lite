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

from pysollib.mygettext import n_

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
    (tkinter.NONE,   n_('Icons only')),
    ('text',         n_('Text only')),
    (tkinter.TOP,    n_('Icons and text')),     # text below the icon
    )

# The Automatic play choices (same layout as ASSIST_OPTIONS below).
AUTOMATIC_PLAY_OPTIONS = (
    ('autofaceup', n_('Auto face-up'), 'mOptAutoFaceUp'),
    ('autodrop', n_('Auto drop'), 'mOptAutoDrop'),
    ('autodeal', n_('Auto deal'), 'mOptAutoDeal'),
    ('quickplay', n_('Quick play'), 'mOptQuickPlay'),
)

# The Assist level choices: (option and tkopt name, label, menubar handler).
ASSIST_OPTIONS = (
    ('undo', n_('Enable undo'), 'mOptEnableUndo'),
    ('bookmarks', n_('Enable bookmarks'), 'mOptEnableBookmarks'),
    ('hint', n_('Enable hint'), 'mOptEnableHint'),
    ('shuffle', n_('Enable shuffle'), 'mOptEnableShuffle'),
    ('free_hint', n_('Free hints'), 'mOptFreeHints'),
    ('highlight_piles', n_('Enable highlight piles'),
     'mOptEnableHighlightPiles'),
    ('highlight_cards', n_('Enable highlight cards'),
     'mOptEnableHighlightCards'),
    ('highlight_samerank', n_('Enable highlight same rank/suit'),
     'mOptEnableHighlightSameRank'),
    ('peek_facedown', n_('Enable face-down peek'),
     'mOptEnablePeekFacedown'),
    ('highlight_not_matching', n_('Highlight no matching'),
     'mOptEnableHighlightNotMatching'),
    ('shade', n_('Shade legal moves'), 'mOptShade'),
    ('stuck_notification', n_('Stuck notification'),
     'mOptEnableStuckNotification'),
)

# Assist options that only matter for some games. The first one restarts
# the game when it changes, so it is applied last.
ASSIST_GAME_OPTIONS = (
    ('shisen_show_hint', n_('Show hint arrow (in Shisen-Sho games)'),
     'mOptShisenShowHint'),
    ('match_three_cascade', n_('Show cascade (in Match Three games)'),
     'mOptMatchThreeCascade'),
    ('accordion_deal_all', n_('Deal all cards (in Accordion type games)'),
     'mOptAccordionDealAll'),
    ('pegged_auto_remove', n_('Auto-remove first card (in Pegged games)'),
     'mOptPeggedAutoRemove'),
    ('mahjongg_show_removed', n_('Show removed tiles (in Mahjongg games)'),
     'mOptMahjonggShowRemoved'),
)

TOOLBAR_BUTTONS = (
    "new",
    "restart",
    "open",
    "save",
    "undo",
    "redo",
    "autodrop",
    "shuffle",
    "hint",
    "pause",
    "rules",
    )

