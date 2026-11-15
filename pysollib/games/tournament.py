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
    BasicRowStack, \
    DealRowRedealTalonStack, \
    ReserveStack, \
    SS_FoundationStack
from pysollib.util import ACE, KING

# ************************************************************************
# * Tournament
# ************************************************************************


class Tournament_Talon(DealRowRedealTalonStack):
    def dealCards(self, sound=False):
        num_cards = 0
        if sound and self.game.app.opt.animations:
            self.game.startDealSample()
        if len(self.cards) == 0:
            num_cards = self._redeal(reverse=True, frames=0)
            self.game.nextRoundMove(self)
        for r in self.game.s.rows:
            for _ in range(4):
                if not self.cards:
                    break
                num_cards += self.dealRow([r], sound=False, frames=4)
        if sound:
            self.game.stopSamples()
        return num_cards


class Tournament(Game):

    ROW_YOFFSET = True

    #
    # game layout
    #

    def createGame(self):

        # create layout
        l, s = Layout(self), self.s

        # set window
        self.setSize(l.XM+10*l.XS, max(l.YM+l.YS+20*l.YOFFSET, 2*l.YM+5*l.YS))

        # create stacks
        x, y, = l.XM+2*l.XS, l.YM
        for i in range(4):
            s.foundations.append(SS_FoundationStack(x, y, self, suit=i))
            x = x + l.XS
        for i in range(4):
            s.foundations.append(SS_FoundationStack(x, y, self, suit=i,
                                                    base_rank=KING, dir=-1))
            x = x + l.XS
        x, y = l.XM+2*l.XS, 2*l.YM+l.YS
        for i in range(6):
            stack = BasicRowStack(x, y, self, max_move=1, max_accept=0)
            s.rows.append(stack)
            if not self.ROW_YOFFSET:
                stack.CARD_YOFFSET = 0
            x = x + l.XS

        x, y = l.XM, 2*l.YM+l.YS
        for i in range(4):
            self.s.reserves.append(ReserveStack(x, y, self))
            y += l.YS
        x, y = l.XM+9*l.XS, 2*l.YM+l.YS
        for i in range(4):
            self.s.reserves.append(ReserveStack(x, y, self))
            y += l.YS

        s.talon = Tournament_Talon(l.XM, l.YM, self, max_rounds=3)
        l.createText(s.talon, "se")
        l.createRoundText(s.talon, 'ne')

        # define stack-groups
        l.defaultStackGroups()

    #
    # game overrides
    #

    def _shuffleHook(self, cards):
        for c in cards[-8:]:
            if c.rank in (ACE, KING):
                return cards
        #
        for c in cards:
            if c.rank in (ACE, KING):
                break
        cards.remove(c)
        return cards+[c]

    def startGame(self):
        self.startDealSample()
        self.s.talon.dealRow(self.s.reserves, frames=4)
        self.s.talon.dealCards()

    def fillStack(self, stack):
        if stack in self.s.rows and not stack.cards:
            if not self.demo:
                self.startDealSample()
            for _ in range(4):
                if not self.s.talon.cards:
                    break
                self.s.talon.dealRow([stack])
            if not self.demo:
                self.stopSamples()


# register the game
registerGame(GameInfo(303, Tournament, "Tournament",
                      GI.GT_MISC_TYPE, 2, 2, GI.SL_MOSTLY_LUCK,
                      altnames=("Marechal Saxe", ),))
