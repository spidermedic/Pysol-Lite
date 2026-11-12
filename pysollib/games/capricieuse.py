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
from pysollib.stack import (
    AC_RowStack,
    InitialDealTalonStack,
    RK_FoundationStack,
)
from pysollib.util import ANY_SUIT


# ************************************************************************
# * Choice
# ************************************************************************

class Choice_Foundation(RK_FoundationStack):
    def acceptsCards(self, from_stack, cards):
        if not RK_FoundationStack.acceptsCards(self, from_stack, cards):
            return False
        # check the suit
        num_cards = len(self.cards)
        for f in self.game.s.foundations:
            if len(f.cards) > num_cards:
                suit = f.cards[num_cards].suit
                break
        else:
            return True
        return cards[0].suit == suit


class Choice(Game):

    def createGame(self, rows=8, playcards=16):
        # create layout
        l, s = Layout(self), self.s

        # set window
        decks = self.gameinfo.decks
        max_rows = max(8, rows)
        self.setSize(l.XM + max_rows*l.XS,
                     l.YM + 2*l.YS + (playcards+4*decks)*l.YOFFSET)

        # create stacks
        x, y = l.XM + (max_rows-8)*l.XS//2, l.YM
        for i in range(8):
            stack = Choice_Foundation(x, y, self, base_rank=(i+5), dir=0,
                                      suit=ANY_SUIT, max_cards=(4*decks))
            stack.CARD_YOFFSET = l.YOFFSET
            s.foundations.append(stack)
            x += l.XS

        x = l.XM + (max_rows-rows)*l.XS//2
        y = l.YM + l.YS + (4*decks)*l.YOFFSET
        for i in range(rows):
            s.rows.append(AC_RowStack(x, y, self))
            x += l.XS

        x, y = self.width - l.XS, self.height - l.YS
        s.talon = InitialDealTalonStack(x, y, self)

        # define stack-groups
        l.defaultStackGroups()

    def startGame(self):
        for i in range(11):
            self.s.talon.dealRowAvail(frames=0)
        self.startDealSample()
        self.s.talon.dealRowAvail()

    shallHighlightMatch = Game._shallHighlightMatch_AC


# register the game
registerGame(GameInfo(755, Choice, "Choice",
                      GI.GT_3DECK_TYPE | GI.GT_OPEN | GI.GT_ORIGINAL |
                      GI.GT_STRIPPED, 3, 0, GI.SL_MOSTLY_SKILL,
                      ranks=(5, 6, 7, 8, 9, 10, 11, 12)))
