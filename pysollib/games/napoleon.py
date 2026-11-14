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

from pysollib.game import Game
from pysollib.gamedb import GI, GameInfo, registerGame
from pysollib.games.braid import Braid_Foundation
from pysollib.hint import CautiousDefaultHint
from pysollib.layout import Layout
from pysollib.mfxutil import kwdefault
from pysollib.stack import (
    BasicRowStack,
    InitialDealTalonStack,
    ReserveStack,
    Stack,
    StackWrapper,
    UD_SS_RowStack,
)
from pysollib.util import RANKS


# ************************************************************************
# * stacks
# ************************************************************************


class Napoleon_RowStack(UD_SS_RowStack):
    getBottomImage = Stack._getReserveBottomImage


class Napoleon_ReserveStack(BasicRowStack):
    def __init__(self, x, y, game, **cap):
        kwdefault(cap, max_move=1, max_accept=0)
        BasicRowStack.__init__(self, x, y, game, **cap)


class Napoleon_SingleFreeCell(ReserveStack):
    def acceptsCards(self, from_stack, cards):
        #         if from_stack.id >= 8:
        #             # from_stack must be a Napoleon_RowStack
        #             return False
        return ReserveStack.acceptsCards(self, from_stack, cards)

    def canMoveCards(self, cards):
        if self.game.s.rows[8].cards and self.game.s.rows[9].cards:
            return False
        return ReserveStack.canMoveCards(self, cards)


class Napoleon_FreeCell(ReserveStack):
    def canMoveCards(self, cards):
        if self.game.s.rows[self.id-2].cards:
            return False
        return ReserveStack.canMoveCards(self, cards)


# ************************************************************************
# * Der kleine Napoleon
# ************************************************************************

class DerKleineNapoleon(Game):

    Hint_Class = CautiousDefaultHint
    Foundation_Class = Braid_Foundation
    RowStack_Class = StackWrapper(Napoleon_RowStack, mod=13)

    #
    # game layout
    #

    def createGame(self, cells=1):
        # create layout
        l, s = Layout(self), self.s

        # set window
        self.setSize(l.XM + 2*24 + 2*l.XM + 11*l.XS, l.YM + 5*l.YS + 2*l.XM)
        x0 = l.XM + 24 + 4*l.XS
        x1 = x0 + l.XS + l.XM
        x2 = x1 + l.XS + l.XM

        # create stacks
        y = l.YM
        for i in range(4):
            s.rows.append(self.RowStack_Class(x0, y, self))
            s.rows.append(self.RowStack_Class(x2, y, self))
            y = y + l.YS
        y = self.height - l.YS
        if cells == 1:
            s.rows.append(Napoleon_ReserveStack(x0, y, self))
            s.rows.append(Napoleon_ReserveStack(x2, y, self))
            s.reserves.append(Napoleon_SingleFreeCell(x1, y, self))
        else:
            s.rows.append(Napoleon_ReserveStack(x0 - l.XS, y, self))
            s.rows.append(Napoleon_ReserveStack(x2 + l.XS, y, self))
            s.reserves.append(Napoleon_FreeCell(x0, y, self))
            s.reserves.append(Napoleon_FreeCell(x2, y, self))
        # foundations
        x, y = x1, l.YM
        for i in range(4):
            s.foundations.append(self.Foundation_Class(x, y, self, i))
            y = y + l.YS
        # talon
        if cells == 1:
            # x, y = l.XM, self.height - l.YS
            y = self.height + l.YS
        else:
            y = self.height - l.YS
        s.talon = InitialDealTalonStack(x, y, self)

        # update stack building direction
        for r in s.rows:
            if r.id & 1 == 0:
                r.CARD_XOFFSET = 4*[-l.XS] + 13*[-2]
            else:
                r.CARD_XOFFSET = 4*[l.XS] + 13*[2]
            r.CARD_YOFFSET = 0

        # define stack-groups
        l.defaultStackGroups()

    #
    # game overrides
    #

    def _shuffleHook(self, cards):
        # move 4 cards of the same rank to bottom of the Talon (i.e.
        #   last cards to be dealt)
        rank = cards[-1].rank
        return self._shuffleHookMoveToBottom(
            cards, lambda c, rank=rank: (c.rank == rank, c.suit))

    def startGame(self):
        for i in range(4):
            self.s.talon.dealRow(rows=self.s.rows[:8], frames=0)
        self.startDealSample()
        self.s.talon.dealRow(rows=self.s.rows[:8])
        for i in range(4):
            self.s.talon.dealRow(rows=self.s.rows[8:])
        self.s.talon.dealBaseCards(ncards=4)

    shallHighlightMatch = Game._shallHighlightMatch_SSW

    #
    # game extras
    #

    def updateText(self):
        if self.preview > 1 or not self.texts.info:
            return
        t = ""
        f = self.s.foundations[0]
        if f.cards:
            t = RANKS[f.cards[0].rank]
            dir = self.getFoundationDir()
            if dir == 1:
                t = t + " Ascending"
            elif dir == -1:
                t = t + " Descending"
        self.texts.info.config(text=t)


# ************************************************************************
# * Napoleon (two FreeCells instead of one SingleFreeCell)
# ************************************************************************

class Napoleon(DerKleineNapoleon):
    def createGame(self):
        DerKleineNapoleon.createGame(self, cells=2)


# register the game
registerGame(GameInfo(167, DerKleineNapoleon, "Der kleine Napoleon",
                      GI.GT_NAPOLEON | GI.GT_OPEN, 1, 0, GI.SL_MOSTLY_SKILL))
