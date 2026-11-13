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
from pysollib.hint import CautiousDefaultHint
from pysollib.layout import Layout
from pysollib.stack import \
    InitialDealTalonStack, \
    SS_FoundationStack, \
    StackWrapper, \
    UD_AC_RowStack, \
    UD_RK_RowStack, \
    UD_SS_RowStack, \
    WasteStack, \
    WasteTalonStack
from pysollib.util import ACE, KING, NO_RANK, UNLIMITED_REDEALS


# ************************************************************************
# * Bisley
# ************************************************************************

class Bisley(Game):

    #
    # game layout
    #

    def createGame(self):
        # create layout
        l, s = Layout(self), self.s

        # set window
        w, h = 2*l.XM+8*l.XS, max(2*(l.YM+l.YS+8*l.YOFFSET), l.YM+5*l.YS)
        self.setSize(w, h)

        # create stacks
        x, y = l.XM, l.YM
        for i in range(6):
            s.rows.append(UD_SS_RowStack(x, y, self, base_rank=NO_RANK))
            x += l.XS
        x, y = l.XM, l.YM+l.YS+8*l.YOFFSET
        for i in range(6):
            s.rows.append(UD_SS_RowStack(x, y, self, base_rank=NO_RANK))
            x += l.XS
        y = l.YM
        for i in range(4):
            x = l.XM+6*l.XS+l.XM
            s.foundations.append(SS_FoundationStack(x, y, self, i, max_move=0))
            x += l.XS
            s.foundations.append(SS_FoundationStack(x, y, self, i,
                                 base_rank=KING, max_move=0, dir=-1))
            y += l.YS

        s.talon = InitialDealTalonStack(w-l.XS, h-l.YS, self)

        # default
        l.defaultAll()

    #
    # game overrides
    #

    def startGame(self):
        self._startDealNumRows(3)
        self.s.talon.dealRow()
        self.s.talon.dealRow(rows=self.s.foundations[::2])

    def _shuffleHook(self, cards):
        # move Aces to bottom of the Talon (i.e. last cards to be dealt)
        return self._shuffleHookMoveToBottom(
            cards, lambda c: (c.rank == ACE, c.suit))

    shallHighlightMatch = Game._shallHighlightMatch_SS


# ************************************************************************
# * Realm
# * Mancunian
# ************************************************************************

class Realm(Game):

    Hint_Class = CautiousDefaultHint
    RowStack_Class = StackWrapper(UD_AC_RowStack, base_rank=NO_RANK)

    def createGame(self):
        # create layout
        l, s = Layout(self), self.s

        # set window
        w, h = 3*l.XM+8*l.XS, l.YM+2*l.YS+15*l.YOFFSET
        self.setSize(w, h)

        # create stacks
        x, y = 2*l.XM, l.YM+l.YS
        for i in range(8):
            s.rows.append(self.RowStack_Class(x, y, self))
            x += l.XS
        y = l.YM
        for i in range(4):
            x = l.XM+i*l.XS
            s.foundations.append(SS_FoundationStack(x, y, self, i, max_move=0))
            x += 2*l.XM+4*l.XS
            s.foundations.append(SS_FoundationStack(x, y, self, i,
                                 base_rank=KING, max_move=0, dir=-1))

        s.talon = InitialDealTalonStack(w-l.XS, h-l.YS, self)

        # default
        l.defaultAll()

    def startGame(self):
        self._startDealNumRows(5)
        self.s.talon.dealRow()
        self.s.talon.dealRowAvail()

    shallHighlightMatch = Game._shallHighlightMatch_AC


class Mancunian(Realm):
    RowStack_Class = StackWrapper(UD_RK_RowStack, base_rank=NO_RANK)

    shallHighlightMatch = Game._shallHighlightMatch_RK


# ************************************************************************
# * Hospital Patience
# ************************************************************************

class HospitalPatience(Game):

    def createGame(self):
        l, s = Layout(self), self.s
        self.setSize(l.XM+6*l.XS, l.YM+2*l.YS)

        x, y = l.XM, l.YM
        s.talon = WasteTalonStack(x, y, self,
                                  max_rounds=UNLIMITED_REDEALS, num_deal=3)
        l.createText(s.talon, 'ne')
        y += l.YS
        s.waste = WasteStack(x, y, self)
        l.createText(s.waste, 'ne')

        x = l.XM + 2 * l.XS
        for i in range(4):
            y = l.YM
            s.foundations.append(SS_FoundationStack(x, y, self, i, max_move=0))
            y += l.YS
            s.foundations.append(SS_FoundationStack(x, y, self, i,
                                 base_rank=KING, max_move=0, dir=-1))
            x += l.XS

        l.defaultStackGroups()

    def startGame(self, flip=0, reverse=1):
        self.startDealSample()
        self.s.talon.dealCards()      # deal first card to WasteStack


# register the game
registerGame(GameInfo(290, Bisley, "Bisley",
                      GI.GT_BAKERS_DOZEN | GI.GT_OPEN, 1, 0,
                      GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(374, Realm, "Realm",
                      GI.GT_1DECK_TYPE | GI.GT_OPEN | GI.GT_ORIGINAL,
                      1, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(375, Mancunian, "Mancunian",
                      GI.GT_1DECK_TYPE | GI.GT_OPEN | GI.GT_ORIGINAL,
                      1, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(686, HospitalPatience, "Hospital Patience",
                      GI.GT_1DECK_TYPE, 1, -1, GI.SL_MOSTLY_LUCK))
