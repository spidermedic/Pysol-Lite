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
    OpenStack, \
    SS_FoundationStack, \
    SS_RowStack
from pysollib.util import KING

# ************************************************************************
# * Heads and Tails
# ************************************************************************


class HeadsAndTails_Reserve(OpenStack):
    def canFlipCard(self):
        return False


class HeadsAndTails(Game):
    Hint_Class = CautiousDefaultHint

    #
    # game layout
    #

    def createGame(self):

        # create layout
        l, s = Layout(self), self.s

        # set window
        h = l.YS + 7*l.YOFFSET
        self.setSize(l.XM+10*l.XS, l.YM+l.YS+2*h)

        # create stacks
        x, y = self.width - l.XS, self.height - l.YS
        s.talon = InitialDealTalonStack(x, y, self)

        x, y = l.XM+l.XS, l.YM
        for i in range(8):
            s.rows.append(SS_RowStack(x, y, self,
                          dir=1, max_move=1, max_accept=1))
            x += l.XS
        x, y = l.XM+l.XS, l.YM+l.YS+h
        for i in range(8):
            s.rows.append(SS_RowStack(x, y, self,
                          dir=-1, max_move=1, max_accept=1))
            x += l.XS

        x, y = l.XM+l.XS, l.YM+h
        for i in range(8):
            stack = HeadsAndTails_Reserve(x, y, self)
            s.reserves.append(stack)
            l.createText(stack, "n")
            x += l.XS

        x, y = l.XM, l.YM
        for i in range(4):
            s.foundations.append(SS_FoundationStack(x, y, self, suit=i))
            y += l.YS
        x, y = l.XM+9*l.XS, l.YM
        for i in range(4):
            s.foundations.append(SS_FoundationStack(x, y, self,
                                 suit=i, base_rank=KING, dir=-1))
            y += l.YS

        # define stack-groups
        l.defaultStackGroups()

    #
    # game overrides
    #

    def startGame(self):
        for i in range(11):
            self.s.talon.dealRow(rows=self.s.reserves, frames=0, flip=0)
        self._startAndDealRow()

    def fillStack(self, stack):
        if stack in self.s.rows and not stack.cards:
            reserves = self.s.reserves
            si = list(self.s.rows).index(stack) % 8
            from_stack = None
            if reserves[si].cards:
                from_stack = reserves[si]
            else:
                for i in range(1, 8):
                    n = si+i
                    if n < 8 and reserves[n].cards:
                        from_stack = reserves[n]
                        break
                    n = si-i
                    if n >= 0 and reserves[n].cards:
                        from_stack = reserves[n]
                        break
            if not from_stack:
                return
            old_state = self.enterState(self.S_FILL)
            from_stack.flipMove()
            from_stack.moveMove(1, stack)
            self.leaveState(old_state)

    shallHighlightMatch = Game._shallHighlightMatch_SS


# register the game

registerGame(GameInfo(307, HeadsAndTails, "Heads and Tails",
                      GI.GT_2DECK_TYPE, 2, 0, GI.SL_BALANCED,
                      altnames=("Regiment",)))
