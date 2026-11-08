#!/usr/bin/env python
# -*- mode: python; coding: utf-8; -*-
# ---------------------------------------------------------------------------
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
# ---------------------------------------------------------------------------

import os

from pysollib.gamedb import GI, hideGame, loadGame
from pysollib.layout import Layout
from pysollib.stack import AC_FoundationStack, \
        AC_RowStack, \
        BO_FoundationStack, \
        BO_RowStack, \
        BasicRowStack, \
        DealFirstRowRedealTalonStack, \
        DealReserveRedealTalonStack, \
        DealRowRedealTalonStack, \
        GroundsForADivorceTalonStack, \
        InitialDealTalonStack, \
        RK_FoundationStack, \
        RK_RowStack, \
        SC_FoundationStack, \
        SC_RowStack, \
        SS_FoundationStack, \
        SS_RowStack, \
        SpiderTalonStack, \
        Spider_AC_Foundation, \
        Spider_AC_RowStack, \
        Spider_BO_Foundation, \
        Spider_BO_RowStack, \
        Spider_RK_Foundation, \
        Spider_SC_Foundation, \
        Spider_SC_RowStack, \
        Spider_SS_Foundation, \
        Spider_SS_RowStack, \
        UD_AC_RowStack, \
        UD_BO_RowStack, \
        UD_RK_RowStack, \
        UD_SC_RowStack, \
        UD_SS_RowStack, \
        WasteTalonStack, \
        Yukon_AC_RowStack, \
        Yukon_BO_RowStack, \
        Yukon_RK_RowStack, \
        Yukon_SC_RowStack, \
        Yukon_SS_RowStack
from pysollib.util import ACE, ANY_RANK, KING, NO_RANK, UNLIMITED_MOVES
from pysollib.wizardpresets import presets

# ************************************************************************
# *
# ************************************************************************


class WizSetting:
    def __init__(self, values_map, default, var_name,
                 label, widget='menu'):
        self.values_map = values_map
        self.default = default
        # self.values_dict = dict(self.values_map)
        self.translation_map = {}       # for backward translation
        if widget == 'menu':
            self.values = []
            for k, v in self.values_map:
                self.values.append(k)
                self.translation_map[k] = k
            assert self.default in self.values
        elif widget == 'preset':
            self.values = []
            for v in self.values_map:
                self.values.append(v)
                self.translation_map[v] = v
            assert self.default in self.values
        else:
            self.values = self.values_map
        self.var_name = var_name
        self.label = label
        self.widget = widget
        self.variable = None            # Tk variable
        self.current_value = None


WizardPresets = WizSetting(
    values_map=list(presets.keys()),
    default='None',
    widget='preset',
    label='Initial setting:',
    var_name='preset',
    )
GameName = WizSetting(
    values_map=(),
    default='My Game',
    widget='entry',
    label='Name:',
    var_name='name',
    )
SkillLevel = WizSetting(
    values_map=(('Luck only',    GI.SL_LUCK),
                ('Mostly luck',  GI.SL_MOSTLY_LUCK),
                ('Balanced',     GI.SL_BALANCED),
                ('Mostly skill', GI.SL_MOSTLY_SKILL),
                ('Skill only',   GI.SL_SKILL),
                ),
    default='Balanced',
    label='Skill level:',
    var_name='skill_level',
    )
NumDecks = WizSetting(
    values_map=(('One',   1),
                ('Two',   2),
                ('Three', 3),
                ('Four',  4)),
    default='One',
    label='Number of decks:',
    var_name='decks',
    )
LayoutType = WizSetting(
    values_map=(('FreeCell', Layout.freeCellLayout),
                ('Klondike', Layout.klondikeLayout),
                ('Gypsy',    Layout.gypsyLayout),
                ('Harp',     Layout.harpLayout),
                ),
    default='FreeCell',
    label='Layout:',
    var_name='layout',
    )
TalonType = WizSetting(
    values_map=(('Deal all cards at the beginning', InitialDealTalonStack),
                ('Deal to waste',         WasteTalonStack),
                ('Deal to tableau',       DealRowRedealTalonStack),
                ('Deal to first tableau', DealFirstRowRedealTalonStack),
                ('Deal to reserves',      DealReserveRedealTalonStack),
                ('Spider',                SpiderTalonStack),
                ('Grounds for a Divorce', GroundsForADivorceTalonStack),
                ),
    default='Deal all cards at the beginning',
    label='Type:',
    var_name='talon',
    )
Redeals = WizSetting(
    values_map=(('No redeals', 0),
                ('One redeal', 1),
                ('Two redeals', 2),
                ('Three redeals', 3),
                ('Unlimited redeals', -1),
                ),
    default='No redeals',
    label='Number of redeals:',
    var_name='redeals',
    )
DealToWaste = WizSetting(
    values_map=(1, 5),
    default=1,
    widget='spin',
    label='# of cards dealt to the waste:',
    var_name='deal_to_waste',
    )
SingleCardWaste = WizSetting(
    values_map=(0, 1),
    default=0,
    label='Single card waste:',
    var_name='single_card_waste',
    widget='check',
    )
TalonShuffle = WizSetting(
    values_map=(0, 1),
    default=0,
    label='Shuffle during redeal:',
    var_name='talon_shuffle',
    widget='check',
    )
FoundType = WizSetting(
    values_map=(('Same suit',                       SS_FoundationStack),
                ('Alternate color',                 AC_FoundationStack),
                ('Same color',                      SC_FoundationStack),
                ('Rank',                            RK_FoundationStack),
                ('Any suit but the same',           BO_FoundationStack),
                ('Spider same suit',                Spider_SS_Foundation),
                ('Spider alternate color',          Spider_AC_Foundation),
                ('Spider same color',               Spider_SC_Foundation),
                ('Spider rank',                     Spider_RK_Foundation),
                ('Spider any suit but the same',    Spider_BO_Foundation),
                ),
    default='Same suit',
    label='Type:',
    var_name='found_type',
    )
FoundBaseCard = WizSetting(
    values_map=(('Ace',  ACE),
                ('King', KING),
                ('Any',  ANY_RANK),
                ),
    default='Ace',
    label='Base card:',
    var_name='found_base_card',
    )
FoundDir = WizSetting(
    values_map=(('Up', 1), ('Down', -1)),
    default='Up',
    label='Direction:',
    var_name='found_dir',
    )
FoundMaxMove = WizSetting(
    values_map=(('None', 0,), ('Top card', 1)),
    default='Top card',
    label='Move:',
    var_name='found_max_move',
    )
FoundEqual = WizSetting(
    values_map=(0, 1),
    default=1,
    label='First card sets base cards:',
    var_name='found_equal',
    widget='check',
    )
RowsNum = WizSetting(
    values_map=(1, 20),
    default=8,
    widget='spin',
    label='Number of tableau piles:',
    var_name='rows_num',
    )
RowsType = WizSetting(
    values_map=(('No building',                        BasicRowStack),

                ('Same suit',                          SS_RowStack),
                ('Alternate color',                    AC_RowStack),
                ('Same color',                         SC_RowStack),
                ('Rank',                               RK_RowStack),
                ('Any suit but the same',              BO_RowStack),

                ('Up or down by same suit',            UD_SS_RowStack),
                ('Up or down by alternate color',      UD_AC_RowStack),
                ('Up or down by same color',           UD_SC_RowStack),
                ('Up or down by rank',                 UD_RK_RowStack),
                ('Up or down by any suit but the same', UD_BO_RowStack),

                ('Spider same suit',                   Spider_SS_RowStack),
                ('Spider alternate color',             Spider_AC_RowStack),
                ('Spider same color',                  Spider_SC_RowStack),
                ('Spider any suit but the same',       Spider_BO_RowStack),

                ('Yukon same suit',                    Yukon_SS_RowStack),
                ('Yukon alternate color',              Yukon_AC_RowStack),
                ('Yukon same color',                   Yukon_SC_RowStack),
                ('Yukon rank',                         Yukon_RK_RowStack),
                ('Yukon any suit but the same',        Yukon_BO_RowStack),
                ),
    default='Alternate color',
    label='Type:',
    var_name='rows_type',
    )
RowsBaseCard = WizSetting(
    values_map=(('Ace',  ACE),
                ('King', KING),
                ('Any',  ANY_RANK),
                ('None', NO_RANK),
                ),
    default='Any',
    label='Base card:',
    var_name='rows_base_card',
    )
RowsDir = WizSetting(
    values_map=(('Up', 1), ('Down', -1), ('Same rank', 0)),
    default='Down',
    label='Direction:',
    var_name='rows_dir',
    )
RowsMaxMove = WizSetting(
    values_map=(('Top card', 1), ('Sequence', UNLIMITED_MOVES)),
    default='Sequence',
    label='Move:',
    var_name='rows_max_move',
    )
RowsWrap = WizSetting(
    values_map=(0, 1),
    default=0,
    label='Wrapping:',
    var_name='rows_wrap',
    widget='check',
    )
RowsSuperMove = WizSetting(
    values_map=(0, 1),
    default=0,
    label='Use "Super Move" feature:',
    var_name='rows_super_move',
    widget='check',
    )
ReservesNum = WizSetting(
    values_map=(0, 20),
    default=4,
    widget='spin',
    label='Number of reserves:',
    var_name='reserves_num',
    )
ReservesMaxAccept = WizSetting(
    values_map=(0, 20),
    default=1,
    widget='spin',
    label='Max # of accepted cards:',
    var_name='reserves_max_accept',
    )
DealType = WizSetting(
    values_map=(('Triangle',  'triangle'),
                ('Rectangle', 'rectangle'),
                ('Pyramid', 'pyramid')
                ),
    default='Rectangle',
    label='Type:',
    var_name='deal_type',
    )
DealFaceDown = WizSetting(
    values_map=(0, 20),
    default=0,
    widget='spin',
    label='# of face-down cards dealt to the tableau pile:',
    var_name='deal_face_down',
    )
DealFaceUp = WizSetting(
    values_map=(0, 20),
    default=8,
    widget='spin',
    label='# of face-up cards dealt to the tableau pile:',
    var_name='deal_face_up',
    )
DealToReseves = WizSetting(
    values_map=(0, 208),
    default=0,
    widget='spin',
    label='# of cards dealt to the reserve:',
    var_name='deal_to_reserves',
    )
DealMaxCards = WizSetting(
    values_map=(0, 208),
    default=52,
    widget='spin',
    label='Max # of dealt cards:',
    var_name='deal_max_cards',
    )
DealToFound = WizSetting(
    values_map=(0, 1),
    default=0,
    label='Deal first cards to the foundations:',
    var_name='deal_found',
    widget='check',
    )

WizardWidgets = (
    'General',
    WizardPresets,
    GameName,
    SkillLevel,
    NumDecks,
    LayoutType,
    'Talon',
    TalonType,
    Redeals,
    DealToWaste,
    SingleCardWaste,
    TalonShuffle,
    'Foundations',
    FoundType,
    FoundBaseCard,
    FoundDir,
    FoundMaxMove,
    FoundEqual,
    'Tableau',
    RowsNum,
    RowsType,
    RowsBaseCard,
    RowsDir,
    RowsMaxMove,
    RowsWrap,
    RowsSuperMove,
    'Reserves',
    ReservesNum,
    ReservesMaxAccept,
    'Opening deal',
    DealType,
    DealFaceDown,
    DealFaceUp,
    DealToReseves,
    DealMaxCards,
    DealToFound,
    )


def write_game(app, game=None):
    import pysollib.customgame                   # for py2exe
    pysollib.customgame.no_use()
    if game is None:
        # new game
        d = app.dn.plugins
        n = 1
        while True:
            fn = os.path.join(d, 'customgame%d.py' % n)  # file name
            mn = 'customgame%d' % n         # module name
            gameid = 200000+n
            if not os.path.exists(fn):
                break
            n += 1
        check_game = True
    else:
        # edit current game
        fn = game.MODULE_FILENAME
        mn = game.__module__
        gameid = game.SETTINGS['gameid']
        check_game = False

    # print '===>', fn
    with open(fn, 'w', encoding='utf-8') as fd:

        fd.write('''\
## -*- coding: utf-8 -*-
## THIS FILE WAS GENERATED AUTOMATICALLY BY THE SOLITAIRE WIZARD
## DO NOT EDIT

from pysollib.customgame import CustomGame, registerCustomGame

class MyCustomGame(CustomGame):
    WIZARD_VERSION = 1
    SETTINGS = {
''')

        for w in WizardWidgets:
            if isinstance(w, str):
                continue
            v = w.variable.get()
            if w.widget in ('menu', 'preset'):
                v = w.translation_map[v]
            if v == w.default:
                # save only unique values
                continue
            if isinstance(v, int):
                fd.write("        '%s': %i,\n" % (w.var_name, v))
            else:
                if w.var_name == 'name':
                    # escape
                    v = v.replace('\\', '\\\\')
                    v = v.replace("'", "\\'")
                    v = v.replace("\n", "\\n")
                    v = v.replace("\r", "\\r")
                    v = v.replace("\t", "\\t")
                    # See: https://github.com/shlomif/PySolFC/issues/177
                    # if isinstance(v, str):
                    #     v = v.encode('utf-8')
                    if not v:
                        v = 'Invalid Game Name'
                fd.write("        '{}': '{}',\n".format(w.var_name, v))
        fd.write("        'gameid': %i,\n" % gameid)

        fd.write('''\
            }

registerCustomGame(MyCustomGame)
''')

    loadGame(mn, fn, check_game=check_game)

    return gameid


def delete_game(app, game):
    hideGame(game)
    fn = game.MODULE_FILENAME
    os.remove(fn)


def reset_wizard(game):
    for w in WizardWidgets:
        if isinstance(w, str):
            continue
        if game is None:
            # set to default
            v = w.default
        else:
            # set from current game
            if w.var_name in game.SETTINGS:
                v = game.SETTINGS[w.var_name]
            else:
                v = w.default
        w.current_value = v
