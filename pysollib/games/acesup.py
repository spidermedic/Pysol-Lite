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
from pysollib.games.montecarlo import MonteCarlo_RowStack
from pysollib.layout import Layout
from pysollib.stack import \
    AbstractFoundationStack, \
    AutoDealTalonStack, \
    BasicRowStack, \
    DealRowTalonStack, \
    OpenStack, \
    RK_RowStack, \
    Spider_RK_Foundation, \
    Stack, \
    StackWrapper
from pysollib.util import ACE, ANY_RANK, ANY_SUIT


# ************************************************************************
# * Aces Up
# ************************************************************************

class AcesUp_Foundation(AbstractFoundationStack):
    def acceptsCards(self, from_stack, cards):
        # Uncomment this if needed for testing - allows all cards to be
        # moved to the foundation, due to the difficulty in winning.
        # return cards[0].rank != ACE
        if not AbstractFoundationStack.acceptsCards(self, from_stack, cards):
            return False
        c = cards[0]
        for s in self.game.s.rows:
            if s is not from_stack and s.cards and s.cards[-1].suit == c.suit:
                if s.cards[-1].rank > c.rank or s.cards[-1].rank == ACE:
                    # found a higher rank or an Ace on the row stacks
                    return c.rank != ACE
        return False


class AcesUp_RowStack(BasicRowStack):
    def acceptsCards(self, from_stack, cards):
        if not BasicRowStack.acceptsCards(self, from_stack, cards):
            return False
        return len(self.cards) == 0

    clickHandler = BasicRowStack.doubleclickHandler


class AcesUp(Game):
    Foundation_Class = AcesUp_Foundation
    Talon_Class = DealRowTalonStack
    RowStack_Class = StackWrapper(AcesUp_RowStack, max_accept=1)

    #
    # game layout
    #

    def createGame(self, rows=4, reserve=False, **layout):
        # create layout
        l, s = Layout(self), self.s

        # set window
        self.setSize(l.XM + (rows+3)*l.XS, l.YM + 4*l.YS)

        # create stacks
        x, y, = l.XM, l.YM
        s.talon = self.Talon_Class(x, y, self)
        if reserve:
            l.createText(s.talon, "ne")
        else:
            l.createText(s.talon, "s")
        x = x + 3*l.XS//2
        for _ in range(rows):
            s.rows.append(self.RowStack_Class(x, y, self))
            x = x + l.XS
        x = x + l.XS//2
        stack = self.Foundation_Class(x, y, self, suit=ANY_SUIT, max_move=0,
                                      dir=0, base_rank=ANY_RANK,
                                      max_cards=self.gameinfo.ncards - 4)
        l.createText(stack, "s")
        s.foundations.append(stack)

        if reserve:
            x, y = l.XM, l.YM+l.YS
            s.reserves.append(self.ReserveStack_Class(x, y, self))

        # define stack-groups
        l.defaultStackGroups()

    #
    # game overrides
    #

    def startGame(self):
        self._startAndDealRow()

    def isGameWon(self):
        if len(self.s.foundations[0].cards) != self.gameinfo.ncards - 4:
            return False
        for s in self.s.rows:
            if len(s.cards) != 1 or s.cards[0].rank != ACE:
                return False
        return True

    def getAutoStacks(self, event=None):
        if event is None:
            # disable auto drop - this would ruin the whole gameplay
            return (self.sg.dropstacks, (), self.sg.dropstacks)
        # rightclickHandler
        return (self.sg.dropstacks, self.sg.dropstacks, self.sg.dropstacks)


# ************************************************************************
# * Perpetual Motion
# ************************************************************************


class Cover_RowStack(MonteCarlo_RowStack):
    def acceptsCards(self, from_stack, cards):
        if not OpenStack.acceptsCards(self, from_stack, cards):
            return False
        if not self.cards:
            return False
        return self.cards[-1].suit == cards[0].suit


class Cover(AcesUp):
    Foundation_Class = StackWrapper(AbstractFoundationStack, max_accept=0)
    Talon_Class = AutoDealTalonStack
    RowStack_Class = StackWrapper(Cover_RowStack, max_accept=1)

    FILL_STACKS_AFTER_DROP = 0          # for MonteCarlo_RowStack

    def fillStack(self, stack):
        if not self.s.talon.cards:
            return
        self.startDealSample()
        for r in self.s.rows:
            if not r.cards:
                self.flipMove(self.s.talon)
                self.moveMove(1, self.s.talon, r)
        self.stopSamples()

    def isGameWon(self):
        if self.s.talon.cards:
            return False
        return len(self.s.foundations[0].cards) == 48


class Deck(Cover):
    Talon_Class = DealRowTalonStack

    def fillStack(self, stack):
        pass


# ************************************************************************
# * Tabby Cat
# * Maine Coon
# ************************************************************************

class TabbyCatStack(RK_RowStack):
    def acceptsCards(self, from_stack, cards):
        if not RK_RowStack.acceptsCards(self, from_stack, cards):
            return False
        # Only allow a sequence if pile is empty
        if len(self.cards) > 0:
            return False
        return True

    getBottomImage = Stack._getReserveBottomImage


class TabbyCat(Game):
    Talon_Class = DealRowTalonStack
    Foundation_Class = Spider_RK_Foundation
    RowStack_Class = StackWrapper(RK_RowStack, mod=13)
    ReserveStack_Class = StackWrapper(TabbyCatStack, mod=13)

    #
    # game layout
    #

    def createGame(self, rows=4, playcards=20):
        # create layout
        l, s = Layout(self), self.s
        decks = self.gameinfo.decks

        # set window
        self.setSize(l.XM + (decks+rows+3.5)*l.XS,
                     l.YM + max(4*l.YS, l.YS+playcards*l.YOFFSET))

        # create stacks
        x = l.XM
        for _ in range(decks):
            y = l.YM
            for _ in range(4):
                s.foundations.append(self.Foundation_Class(x, y, self))
                y += l.YS
            x += l.XS

        x, y, = l.XM + (decks+0.5)*l.XS, l.YM
        for _ in range(rows):
            stack = self.RowStack_Class(x, y, self)
            s.rows.append(stack)
            stack.canDropCards = stack.spiderCanDropCards
            x += l.XS
        x += l.XS//2
        s.reserves.append(self.ReserveStack_Class(x, y, self))
        x += 1.5*l.XS
        s.talon = self.Talon_Class(x, y, self)
        l.createText(s.talon, "s")

        self.setRegion(s.foundations, (-999, -999, l.YS*decks-l.CH//2, 999999))

        # define stack-groups
        l.defaultStackGroups()

    def startGame(self):
        self._startAndDealRow()

    shallHighlightMatch = Game._shallHighlightMatch_RKW


# register the game
registerGame(GameInfo(903, AcesUp, "Aces Up",                   # was: 52
                      GI.GT_MISC_TYPE, 1, 0, GI.SL_MOSTLY_LUCK,
                      altnames=("Aces High", "Drivel", "Discard")))
registerGame(GameInfo(756, TabbyCat, "Tabby Cat",
                      GI.GT_SPIDER, 1, 0, GI.SL_MOSTLY_SKILL))
