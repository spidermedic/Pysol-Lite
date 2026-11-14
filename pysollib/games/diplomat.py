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
from pysollib.games.fortythieves import FortyThieves_Hint
from pysollib.layout import Layout
from pysollib.stack import (
    RK_RowStack,
    SS_FoundationStack,
    StackWrapper,
    WasteStack,
    WasteTalonStack,
)
from pysollib.util import ACE

# ************************************************************************
# * Diplomat
# ************************************************************************


class Diplomat(Game):
    Foundation_Class = SS_FoundationStack
    RowStack_Class = StackWrapper(RK_RowStack, max_move=1)
    Hint_Class = FortyThieves_Hint

    DEAL = (3, 1)
    FILL_EMPTY_ROWS = 0

    #
    # game layout
    #

    def createGame(self, max_rounds=1):
        # create layout
        l, s = Layout(self), self.s

        # set window
        self.setSize(l.XM+8*l.XS, l.YM+3*l.YS+12*l.YOFFSET+(2 * l.TEXT_HEIGHT))

        # create stacks
        x, y = l.XM, l.YM
        for i in range(8):
            s.foundations.append(self.Foundation_Class(x, y, self, suit=i//2))
            x = x + l.XS
        x, y = l.XM, y + l.YS
        for i in range(8):
            s.rows.append(self.RowStack_Class(x, y, self))
            x = x + l.XS
        x, y, = l.XM, self.height - l.YS - l.TEXT_HEIGHT
        s.talon = WasteTalonStack(x, y, self, max_rounds=max_rounds)
        l.createText(s.talon, "s")
        if max_rounds > 1:
            l.createRoundText(self.s.talon, 'n')
        x = x + l.XS
        s.waste = WasteStack(x, y, self)
        l.createText(s.waste, "s")

        # define stack-groups
        l.defaultStackGroups()

    #
    # game overrides
    #

    def startGame(self):
        for i in range(self.DEAL[0]):
            self.s.talon.dealRow(frames=0)
        self.startDealSample()
        for i in range(self.DEAL[1]):
            self.s.talon.dealRow()
        self.s.talon.dealCards()          # deal first card to WasteStack

    def fillStack(self, stack):
        if self.FILL_EMPTY_ROWS and stack in self.s.rows and not stack.cards:
            old_state = self.enterState(self.S_FILL)
            if self.s.waste.cards:
                self.s.waste.moveMove(1, stack)
            elif self.s.talon.canDealCards():
                self.s.talon.dealCards()
                self.s.waste.moveMove(1, stack)
            self.leaveState(old_state)

    shallHighlightMatch = Game._shallHighlightMatch_RK


# ************************************************************************
# * Congress
# * Parliament
# ************************************************************************

class Congress(Diplomat):
    DEAL = (0, 1)
    FILL_EMPTY_ROWS = 1

    Foundation_Classes = [SS_FoundationStack, SS_FoundationStack]

    #
    # game layout (just rearrange the stacks a little bit)
    #

    def createGame(self, max_rounds=1):
        # create layout
        l, s = Layout(self), self.s

        # set window
        self.setSize(l.XM + 7*l.XS, l.YM + 4*l.YS)

        # create stacks
        x = l.XM+4*l.XS
        for fnd_cls in self.Foundation_Classes:
            y = l.YM
            for i in range(4):
                s.foundations.append(fnd_cls(x, y, self, suit=i))
                y += l.YS
            x += l.XS
        for i in range(4):
            for j in range(2):
                x, y = l.XM + (3+3*j)*l.XS, l.YM + i*l.YS
                stack = self.RowStack_Class(x, y, self)
                stack.CARD_YOFFSET = 0
                s.rows.append(stack)
        x, y, = l.XM, l.YM
        s.talon = WasteTalonStack(x, y, self, max_rounds=max_rounds)
        l.createText(s.talon, "s")
        x = x + l.XS
        s.waste = WasteStack(x, y, self)
        l.createText(s.waste, "s")
        if max_rounds > 1:
            l.createRoundText(s.talon, 'ne', dx=l.XS)

        # define stack-groups
        l.defaultStackGroups()


class Parliament(Congress):

    def _shuffleHook(self, cards):
        # move Aces to top of the Talon (i.e. first cards to be dealt)
        return self._shuffleHookMoveToTop(
            cards, lambda c: (c.rank == ACE, (c.deck, c.suit)))

    def startGame(self):
        self.s.talon.dealRow(rows=self.s.foundations, frames=0)
        Congress.startGame(self)


# register the game
registerGame(GameInfo(149, Diplomat, "Diplomat",
                      GI.GT_FORTY_THIEVES, 2, 0, GI.SL_BALANCED))
registerGame(GameInfo(150, Congress, "Congress",
                      GI.GT_FORTY_THIEVES, 2, 0, GI.SL_MOSTLY_SKILL,
                      altnames=("President's Cabinet",)))
registerGame(GameInfo(548, Parliament, "Parliament",
                      GI.GT_FORTY_THIEVES, 2, 0, GI.SL_BALANCED))
