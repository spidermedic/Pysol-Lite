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
    AbstractFoundationStack, \
    BasicRowStack, \
    FullStackWrapper, \
    WasteStack, \
    WasteTalonStack
from pysollib.util import ANY_RANK, ANY_SUIT


class Osmium_Foundation(AbstractFoundationStack):
    def acceptsCards(self, from_stack, cards):
        if not AbstractFoundationStack.acceptsCards(self, from_stack, cards):
            return False
        # search foundation with max number of cards
        assert len(cards) == 1
        max_s, max_cards = None, -1
        for s in self.game.s.foundations:
            if len(s.cards) > max_cards:
                max_s, max_cards = s, len(s.cards)
        # if we have less cards, then rank must match the card in this
        # foundation
        if len(self.cards) < max_cards:
            if cards[0].rank != max_s.cards[len(self.cards)].rank:
                return False
        #
        return True

    def getHelp(self):
        return 'Foundation. Build in suit regardless of rank.'


class Osmium(Game):
    Foundation_Class = Osmium_Foundation

    #
    # game layout
    #

    def createGame(self, max_rounds=-1, num_deal=1):
        # create layout
        l, s = Layout(self), self.s

        # set window
        w, h = 3*l.XM+3*l.XS+(4+13)*l.XOFFSET, l.YM+4*l.YS
        self.setSize(w, h)

        # create stacks
        x, y, = l.XM, l.YM
        for i in range(4):
            stack = BasicRowStack(x, y, self, max_move=1, max_accept=0)
            stack.CARD_XOFFSET, stack.CARD_YOFFSET = l.XOFFSET, 0
            s.rows.append(stack)
            y = y + l.YS
        x, y, = 2*l.XM+l.XS+4*l.XOFFSET, l.YM
        for i in range(4):
            stack = self.Foundation_Class(x, y, self, suit=i,
                                          base_rank=ANY_RANK, max_move=0)
            stack.CARD_XOFFSET, stack.CARD_YOFFSET = l.XOFFSET, 0
            s.foundations.append(stack)
            y = y + l.YS
        x, y, = self.width - l.XS, l.YM + l.YS
        s.talon = WasteTalonStack(x, y, self,
                                  max_rounds=max_rounds, num_deal=num_deal)
        l.createText(s.talon, "sw")
        y = y + l.YS
        s.waste = WasteStack(x, y, self)
        l.createText(s.waste, "sw")

        # define stack-groups
        l.defaultStackGroups()

    #
    # game overrides
    #

    def startGame(self, flip=0):
        # deal first card to foundation
        base_card = self.s.talon.getCard()
        n = base_card.suit * self.gameinfo.decks
        to_stack = self.s.foundations[n]
        self.startDealSample()
        self.flipMove(self.s.talon)
        self.moveMove(1, self.s.talon, to_stack)
        # deal cards
        for i in range(3):
            self.s.talon.dealRow(flip=flip)
        self.s.talon.dealRow()
        self.s.talon.dealCards()          # deal first card to WasteStack


# ************************************************************************
# * Osmosis
# * Peek
# ************************************************************************

class Osmosis_Foundation(AbstractFoundationStack):
    def acceptsCards(self, from_stack, cards):
        if not AbstractFoundationStack.acceptsCards(self, from_stack, cards):
            return False
        assert len(cards) == 1
        indx = list(self.game.s.foundations).index(self)
        c0 = cards[0]
        below_found = self.game.s.foundations[indx-1]
        if indx == 0:
            if not self.cards:
                return True
            return c0.suit == self.cards[0].suit
        if not below_found.cards:
            return False
        if not self.cards:
            return c0.rank == below_found.cards[0].rank
        if c0.suit != self.cards[0].suit:
            return False
        for c1 in below_found.cards:
            if c0.rank == c1.rank:
                return True
        return False

    def getHelp(self):
        return 'Foundation. Build in suit regardless of rank.'


class Osmosis(Osmium):
    Foundation_Class = FullStackWrapper(
        Osmosis_Foundation, base_rank=ANY_RANK, suit=ANY_SUIT, max_move=0)

    def createGame(self, max_rounds=-1, num_deal=3):
        Osmium.createGame(self, num_deal=3)

    def startGame(self, flip=0):
        self.startDealSample()
        # deal cards
        for i in range(3):
            self.s.talon.dealRow(flip=flip)
        self.s.talon.dealRow()
        # deal one card to foundation
        self.s.talon.dealRow(rows=self.s.foundations[:1])
        # deal cards to WasteStack
        self.s.talon.dealCards()


class Peek(Osmosis):
    def startGame(self):
        Osmosis.startGame(self, flip=1)


# register the game
registerGame(GameInfo(715, Osmosis, "Osmosis",
                      GI.GT_1DECK_TYPE, 1, -1, GI.SL_MOSTLY_LUCK,
                      altnames=("Treasure Trove",)))
registerGame(GameInfo(716, Peek, "Peek",
                      GI.GT_1DECK_TYPE, 1, -1, GI.SL_MOSTLY_LUCK))
