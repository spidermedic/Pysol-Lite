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

from pysollib.game import Game
from pysollib.gamedb import GI, GameInfo, registerGame
from pysollib.games.spider import Spider_Hint
from pysollib.hint import KlondikeType_Hint
from pysollib.layout import Layout
from pysollib.mfxutil import kwdefault
from pysollib.stack import (
    AC_RowStack,
    BO_RowStack,
    KingAC_RowStack,
    SS_FoundationStack,
    SS_RowStack,
    Spider_SS_RowStack,
    StackWrapper,
    WasteStack,
    WasteTalonStack,
)
from pysollib.util import ACE, KING

# ************************************************************************
# * Double Klondike (Klondike with 2 decks and 9 rows)
# ************************************************************************


class DoubleKlondike(Game):
    Layout_Method = staticmethod(Layout.harpLayout)
    Foundation_Class = SS_FoundationStack
    RowStack_Class = KingAC_RowStack
    Hint_Class = KlondikeType_Hint

    def createGame(self, max_rounds=-1, num_deal=1, **layout):
        # create layout
        l, s = Layout(self), self.s
        kwdefault(layout, rows=9, waste=1, texts=1, playcards=19)
        self.Layout_Method(l, **layout)
        self.setSize(l.size[0], l.size[1])
        # create stacks
        s.talon = WasteTalonStack(l.s.talon.x, l.s.talon.y, self,
                                  max_rounds=max_rounds, num_deal=num_deal)
        s.waste = WasteStack(l.s.waste.x, l.s.waste.y, self)
        for r in l.s.foundations:
            s.foundations.append(
                self.Foundation_Class(r.x, r.y, self, suit=r.suit))
        for r in l.s.rows:
            s.rows.append(self.RowStack_Class(r.x, r.y, self))
        # default
        l.defaultAll()
        # extra
        if max_rounds > 1:
            anchor = 'n'
            l.createRoundText(s.talon, anchor)
        return l

    def startGame(self, flip=0):
        for i in range(len(self.s.rows)):
            self.s.talon.dealRow(rows=self.s.rows[i+1:], flip=flip, frames=0)
        self._startAndDealRowAndCards()

    shallHighlightMatch = Game._shallHighlightMatch_AC


# ************************************************************************
# * Gargantua (Double Klondike with one redeal)
# ************************************************************************

class Gargantua(DoubleKlondike):
    def createGame(self):
        DoubleKlondike.createGame(self, max_rounds=2)


# ************************************************************************
# * Harp (Double Klondike with 10 non-king rows and no redeal)
# ************************************************************************


class BigHarp(DoubleKlondike):
    RowStack_Class = AC_RowStack

    def createGame(self):
        DoubleKlondike.createGame(self, max_rounds=1, rows=10)

    #
    # game overrides
    #

    # no real need to override, but this way the layout
    # looks a little bit different
    def startGame(self):
        for i in range(len(self.s.rows)):
            self.s.talon.dealRow(rows=self.s.rows[:i], flip=0, frames=0)
        self._startAndDealRowAndCards()


# ************************************************************************
# * Triple Klondike
# * Triple Klondike by Threes
# * Chinese Klondike
# ************************************************************************

class TripleKlondike(DoubleKlondike):
    def createGame(self):
        DoubleKlondike.createGame(self, rows=13)


class ChineseKlondike(DoubleKlondike):
    RowStack_Class = StackWrapper(BO_RowStack, base_rank=KING)

    def createGame(self):
        DoubleKlondike.createGame(self, rows=12)


# ************************************************************************
# * Quadruple Klondike
# * Quadruple Klondike by Threes
# ************************************************************************

class QuadrupleKlondike(DoubleKlondike):
    def createGame(self):
        DoubleKlondike.createGame(self, rows=16)


# ************************************************************************
# * Lady Jane
# * Inquisitor
# ************************************************************************

class LadyJane(DoubleKlondike):
    Hint_Class = Spider_Hint
    RowStack_Class = Spider_SS_RowStack

    def createGame(self):
        DoubleKlondike.createGame(self, rows=10, max_rounds=2, num_deal=3)

    def startGame(self):
        DoubleKlondike.startGame(self, flip=1)

    shallHighlightMatch = Game._shallHighlightMatch_RK
    getQuickPlayScore = Game._getSpiderQuickPlayScore


class Inquisitor(DoubleKlondike):
    RowStack_Class = SS_RowStack

    def createGame(self):
        DoubleKlondike.createGame(self, rows=10, max_rounds=3, num_deal=3)

    def startGame(self):
        DoubleKlondike.startGame(self, flip=1)
    shallHighlightMatch = Game._shallHighlightMatch_SS


# ************************************************************************
# * Arabella
# ************************************************************************

class Arabella(DoubleKlondike):
    Hint_Class = Spider_Hint
    RowStack_Class = StackWrapper(Spider_SS_RowStack, base_rank=KING)

    def createGame(self):
        DoubleKlondike.createGame(self, rows=13, max_rounds=1, playcards=24)

    def startGame(self):
        DoubleKlondike.startGame(self, flip=1)

    shallHighlightMatch = Game._shallHighlightMatch_RK
    getQuickPlayScore = Game._getSpiderQuickPlayScore


# ************************************************************************
# * Double Kingsley
# ************************************************************************

class DoubleKingsley(DoubleKlondike):
    Foundation_Class = StackWrapper(SS_FoundationStack, base_rank=KING, dir=-1)
    RowStack_Class = StackWrapper(KingAC_RowStack, base_rank=ACE, dir=1)

    def createGame(self):
        DoubleKlondike.createGame(self, max_rounds=1)


# ************************************************************************
# * Thieves of Egypt
# ************************************************************************

class ThievesOfEgypt(DoubleKlondike):
    Layout_Method = staticmethod(Layout.klondikeLayout)

    def createGame(self):
        DoubleKlondike.createGame(self, rows=10, max_rounds=2)

    def startGame(self):
        # rows: 1 3 5 7 9 10 8 6 4 2
        row = 0
        for i in (0, 2, 4, 6, 8, 9, 7, 5, 3, 1):
            for j in range(i):
                self.s.talon.dealRow(rows=[self.s.rows[row]], frames=0)
            row += 1
        self._startAndDealRowAndCards()


# ************************************************************************
# * Churchill Solitaire
# ************************************************************************
# https://boardgames.stackexchange.com/questions/29254/rules-for-churchill-solitaire


# register the game
registerGame(GameInfo(21, DoubleKlondike, "Double Klondike",
                      GI.GT_KLONDIKE, 2, -1, GI.SL_BALANCED))
registerGame(GameInfo(25, Gargantua, "Gargantua",
                      GI.GT_KLONDIKE, 2, 1, GI.SL_BALANCED,
                      altnames=("Jumbo",)))
registerGame(GameInfo(15, BigHarp, "Big Harp",
                      GI.GT_KLONDIKE, 2, 0, GI.SL_BALANCED,
                      altnames=("Die grosse Harfe", "Die Pyramide", "Harp")))
registerGame(GameInfo(273, TripleKlondike, "Triple Klondike",
                      GI.GT_KLONDIKE, 3, -1, GI.SL_BALANCED))
registerGame(GameInfo(495, LadyJane, "Lady Jane",
                      GI.GT_KLONDIKE, 2, 1, GI.SL_BALANCED))
registerGame(GameInfo(496, Inquisitor, "Inquisitor",
                      GI.GT_KLONDIKE, 2, 2, GI.SL_BALANCED))
registerGame(GameInfo(497, Arabella, "Arabella",
                      GI.GT_KLONDIKE, 3, 0, GI.SL_BALANCED))
registerGame(GameInfo(590, ChineseKlondike, "Chinese Klondike",
                      GI.GT_KLONDIKE | GI.GT_STRIPPED, 3, -1, GI.SL_BALANCED,
                      suits=(0, 1, 2)))
registerGame(GameInfo(668, DoubleKingsley, "Double Kingsley",
                      GI.GT_KLONDIKE, 2, 0, GI.SL_BALANCED))
registerGame(GameInfo(678, ThievesOfEgypt, "Thieves of Egypt",
                      GI.GT_KLONDIKE, 2, 1, GI.SL_BALANCED,
                      altnames=('Upside-Down Pyramid')))
registerGame(GameInfo(920, QuadrupleKlondike, "Quadruple Klondike",
                      GI.GT_KLONDIKE, 4, -1, GI.SL_BALANCED))
