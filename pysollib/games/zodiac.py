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
from pysollib.layout import Layout
from pysollib.stack import \
    ReserveStack, \
    SS_FoundationStack, \
    UD_SS_RowStack, \
    WasteStack, \
    WasteTalonStack
from pysollib.util import KING, NO_RANK, UNLIMITED_REDEALS


# ************************************************************************
# * Zodiac
# ************************************************************************

class Zodiac_Foundation(SS_FoundationStack):
    def acceptsCards(self, from_stack, cards):
        if not SS_FoundationStack.acceptsCards(self, from_stack, cards):
            return False
        if self.game.s.waste.cards or self.game.s.talon.cards:
            return False
        return True


class Zodiac_RowStack(UD_SS_RowStack):
    def acceptsCards(self, from_stack, cards):
        if not UD_SS_RowStack.acceptsCards(self, from_stack, cards):
            return False
        if from_stack in self.game.s.rows:
            return False
        return True


class Zodiac_ReserveStack(ReserveStack):
    def acceptsCards(self, from_stack, cards):
        if not ReserveStack.acceptsCards(self, from_stack, cards):
            return False
        if from_stack in self.game.s.rows:
            return False
        return True


class Zodiac(Game):

    def createGame(self):

        # create layout
        l, s = Layout(self), self.s

        # set window
        w, h = l.XM+12*l.XS, l.YM+5*l.YS
        self.setSize(w, h)

        # create stacks
        x = l.XM
        for i in range(12):
            for y in (l.YM, l.YM+4*l.YS):
                stack = Zodiac_RowStack(x, y, self, base_rank=NO_RANK)
                s.rows.append(stack)
                stack.CARD_XOFFSET, stack.CARD_YOFFSET = 0, 0
            x += l.XS

        x = l.XM+4*l.XS
        for i in range(4):
            y = l.YM+l.YS
            s.foundations.append(Zodiac_Foundation(x, y, self, suit=i))
            y += 2*l.YS
            s.foundations.append(Zodiac_Foundation(x, y, self, suit=i,
                                                   base_rank=KING, dir=-1))
            x += l.XS

        x, y = l.XM+2*l.XS, l.YM+2*l.YS
        for i in range(8):
            s.reserves.append(Zodiac_ReserveStack(x, y, self))
            x += l.XS

        x, y = l.XM+l.XS, l.YM+l.YS
        s.talon = WasteTalonStack(x, y, self,
                                  max_rounds=UNLIMITED_REDEALS)
        l.createText(s.talon, 'sw')
        x += l.XS
        s.waste = WasteStack(x, y, self)
        l.createText(s.waste, 'se')

        # define stack-groups
        l.defaultStackGroups()

    def startGame(self):
        self.startDealSample()
        self.s.talon.dealRow(rows=self.s.reserves)
        self.s.talon.dealRow()
        self.s.talon.dealCards()

    shallHighlightMatch = Game._shallHighlightMatch_SS


# register the game
registerGame(GameInfo(467, Zodiac, "Zodiac",
                      GI.GT_2DECK_TYPE, 2, -1, GI.SL_BALANCED))
