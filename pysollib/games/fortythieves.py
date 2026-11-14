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
from pysollib.games.gypsy import DieRussische_Foundation
from pysollib.hint import CautiousDefaultHint
from pysollib.layout import Layout
from pysollib.stack import (
    AC_FoundationStack,
    AC_RowStack,
    BO_RowStack,
    RK_RowStack,
    ReserveStack,
    SS_FoundationStack,
    SS_RowStack,
    Spider_SS_RowStack,
    StackWrapper,
    WasteStack,
    WasteTalonStack,
)
from pysollib.util import (
    ACE,
    KING,
    NO_RANK,
    UNLIMITED_MOVES,
    UNLIMITED_REDEALS,
)


class FortyThieves_Hint(CautiousDefaultHint):
    # FIXME: demo is not too clever in this game
    pass


# ************************************************************************
# * Forty Thieves
# *   rows build down by suit
# ************************************************************************

class FortyThieves(Game):
    Foundation_Class = SS_FoundationStack
    RowStack_Class = SS_RowStack
    Hint_Class = FortyThieves_Hint

    FOUNDATION_MAX_MOVE = 1
    ROW_MAX_MOVE = 1
    DEAL = (0, 4)
    FILL_EMPTY_ROWS = 0

    #
    # game layout
    #

    def createGame(self, max_rounds=1, num_deal=1, rows=10,
                   playcards=12, XCARDS=64, XOFFSET=None):
        # create layout
        if XOFFSET is None:
            l, s = Layout(self), self.s
        else:
            l, s = Layout(self, XOFFSET=XOFFSET), self.s

        # set window
        # (compute best XOFFSET - up to 64/72 cards can be in the Waste)
        decks = self.gameinfo.decks
        maxrows = max(rows, 4*decks)
        if maxrows <= 12:
            maxrows += 1
        w1, w2 = maxrows*l.XS+l.XM, 2*l.XS
        if w2 + XCARDS * l.XOFFSET > w1:
            l.XOFFSET = int((w1 - w2) / XCARDS)
        # (piles up to 12 cards are playable without overlap
        #   in default window size)
        h = max(2*l.YS, l.YS+(playcards-1)*l.YOFFSET)
        self.setSize(w1, l.YM + l.YS + h + l.YS + (2 * l.TEXT_HEIGHT))

        # create stacks
        # foundations
        x = l.XM + (maxrows - 4*decks) * l.XS // 2
        y = l.YM
        for i in range(4*decks):
            s.foundations.append(
                self.Foundation_Class(
                    x, y, self,
                    suit=i//decks, max_move=self.FOUNDATION_MAX_MOVE))
            x = x + l.XS
        # rows
        x = l.XM + (maxrows - rows) * l.XS // 2
        y = l.YM + l.YS
        for i in range(rows):
            s.rows.append(self.RowStack_Class(x, y, self,
                                              max_move=self.ROW_MAX_MOVE))
            x = x + l.XS
        # talon, waste
        x = self.width - l.XS
        y = self.height - l.YS - l.TEXT_HEIGHT
        s.talon = WasteTalonStack(x, y, self,
                                  max_rounds=max_rounds, num_deal=num_deal)
        l.createText(s.talon, "s")
        if max_rounds > 1:
            l.createRoundText(s.talon, 'n')
        x -= l.XS
        s.waste = WasteStack(x, y, self)
        s.waste.CARD_XOFFSET = -l.XOFFSET
        l.createText(s.waste, "s")

        # define stack-groups
        l.defaultStackGroups()

    #
    # game overrides
    #

    def startGame(self):
        for i in range(self.DEAL[0]):
            self.s.talon.dealRow(flip=0, frames=0)
        for i in range(self.DEAL[1] - 1):
            self.s.talon.dealRow(frames=0)
        self._startAndDealRowAndCards()

    def fillStack(self, stack):
        if self.FILL_EMPTY_ROWS and stack in self.s.rows and not stack.cards:
            old_state = self.enterState(self.S_FILL)
            if self.s.waste.cards:
                self.s.waste.moveMove(1, stack)
            elif self.s.talon.canDealCards():
                self.s.talon.dealCards()
                self.s.waste.moveMove(1, stack)
            self.leaveState(old_state)

    shallHighlightMatch = Game._shallHighlightMatch_SS


# ************************************************************************
# * Busy Aces
# * Limited
# * Courtyard
# * Waning Moon
# * Lucas
# * Napoleon's Square
# * Josephine
# * Marie Rose
# * Malmaison
# * Sixty Thieves
# * Eighty Thieves
# *   rows build down by suit
# ************************************************************************

class BusyAces(FortyThieves):
    DEAL = (0, 1)

    def createGame(self):
        FortyThieves.createGame(self, rows=12)


class Limited(BusyAces):
    DEAL = (0, 3)


class Courtyard(BusyAces):
    ROW_MAX_MOVE = UNLIMITED_MOVES
    FILL_EMPTY_ROWS = 1


class WaningMoon(FortyThieves):
    def createGame(self):
        FortyThieves.createGame(self, rows=13)


class Lucas(WaningMoon):
    ROW_MAX_MOVE = UNLIMITED_MOVES


class NapoleonsSquare(FortyThieves):
    ROW_MAX_MOVE = UNLIMITED_MOVES

    def createGame(self):
        FortyThieves.createGame(self, rows=12)


class Josephine(FortyThieves):
    ROW_MAX_MOVE = UNLIMITED_MOVES


class MarieRose(Josephine):
    DEAL = (0, 5)

    def createGame(self):
        FortyThieves.createGame(self, rows=12, playcards=16, XCARDS=96)


class Malmaison(MarieRose):
    DEAL = (0, 8)

    def createGame(self):
        FortyThieves.createGame(self, rows=10, playcards=16, XCARDS=128)


class SixtyThieves(FortyThieves):
    DEAL = (0, 5)

    def createGame(self):
        FortyThieves.createGame(self, rows=12, playcards=16, XCARDS=96)


class EightyThieves(FortyThieves):
    DEAL = (0, 8)

    def createGame(self):
        FortyThieves.createGame(self, rows=10, playcards=16, XCARDS=128)


# ************************************************************************
# * Deuces
# * Pluto
# ************************************************************************

class Deuces(FortyThieves):
    Foundation_Class = StackWrapper(SS_FoundationStack, mod=13, base_rank=1)
    RowStack_Class = StackWrapper(SS_RowStack, mod=13)

    DEAL = (0, 1)

    def _shuffleHook(self, cards):
        # move Twos to top of the Talon (i.e. first cards to be dealt)
        return self._shuffleHookMoveToTop(
            cards, lambda c: (c.rank == 1, c.suit))

    def startGame(self):
        self.startDealSample()
        self.s.talon.dealRow(rows=self.s.foundations)
        FortyThieves.startGame(self)

    shallHighlightMatch = Game._shallHighlightMatch_SSW


class Pluto(Deuces):
    def createGame(self):
        FortyThieves.createGame(self, rows=12)

    def _shuffleHook(self, cards):
        return FortyThieves._shuffleHook(self, cards)

    def startGame(self):
        self.startDealSample()
        FortyThieves.startGame(self)


# ************************************************************************
# * Corona
# * Quadrangle
# ************************************************************************

class Corona(FortyThieves):
    FOUNDATION_MAX_MOVE = 0
    DEAL = (0, 3)
    FILL_EMPTY_ROWS = 1

    def createGame(self):
        FortyThieves.createGame(self, rows=12)


class Quadrangle(Corona):
    Foundation_Class = StackWrapper(
        SS_FoundationStack, mod=13, base_rank=NO_RANK)
    RowStack_Class = StackWrapper(SS_RowStack, mod=13)

    def startGame(self):
        FortyThieves.startGame(self)
        self.s.talon.dealSingleBaseCard()

    shallHighlightMatch = Game._shallHighlightMatch_SSW


# ************************************************************************
# * Forty and Eight
# ************************************************************************

class FortyAndEight(FortyThieves):
    def createGame(self):
        FortyThieves.createGame(self, max_rounds=2, rows=8, XCARDS=72)


# ************************************************************************
# * Little Forty
# ************************************************************************

class LittleForty(FortyThieves):
    RowStack_Class = Spider_SS_RowStack

    ROW_MAX_MOVE = UNLIMITED_MOVES
    FILL_EMPTY_ROWS = 1

    def createGame(self):
        FortyThieves.createGame(self, max_rounds=4, num_deal=3, XOFFSET=0)

    shallHighlightMatch = Game._shallHighlightMatch_RK
    getQuickPlayScore = Game._getSpiderQuickPlayScore


# ************************************************************************
# * Streets
# * Maria
# * Number Ten
# * Rank and File
# * Emperor
# *   rows build down by alternate color
# ************************************************************************

class Streets(FortyThieves):
    RowStack_Class = AC_RowStack

    shallHighlightMatch = Game._shallHighlightMatch_AC


class Maria(Streets):
    def createGame(self):
        Streets.createGame(self, rows=9)


class NumberTen(Streets):
    ROW_MAX_MOVE = UNLIMITED_MOVES
    DEAL = (2, 2)


class RankAndFile(Streets):
    ROW_MAX_MOVE = UNLIMITED_MOVES
    DEAL = (3, 1)


class Emperor(Streets):
    DEAL = (3, 1)


class Roosevelt(Streets):
    DEAL = (0, 4)

    def createGame(self):
        Streets.createGame(self, rows=7)


# ************************************************************************
# * Red and Black
# * Zebra
# *   rows build down by alternate color, foundations up by alternate color
# ************************************************************************

class RedAndBlack(Streets):
    Foundation_Class = AC_FoundationStack

    ROW_MAX_MOVE = UNLIMITED_MOVES
    DEAL = (0, 1)

    def createGame(self):
        FortyThieves.createGame(self, rows=8)

    def _shuffleHook(self, cards):
        # move Aces to top of the Talon (i.e. first cards to be dealt)
        return self._shuffleHookMoveToTop(
            cards, lambda c: (c.rank == 0, c.suit))

    def startGame(self):
        self.startDealSample()
        self.s.talon.dealRow(rows=self.s.foundations)
        Streets.startGame(self)


class Zebra(RedAndBlack):
    FOUNDATION_MAX_MOVE = 0
    ROW_MAX_MOVE = 1
    FILL_EMPTY_ROWS = 1

    def createGame(self):
        FortyThieves.createGame(self, max_rounds=2, rows=8, XOFFSET=0)


# ************************************************************************
# * Napoleon's Folly
# * Indian
# * Midshipman
# *   rows build down by any suit but own
# ************************************************************************

class NapoleonsFolly(FortyThieves):
    RowStack_Class = BO_RowStack

    shallHighlightMatch = Game._shallHighlightMatch_BO


class Indian(NapoleonsFolly):
    DEAL = (1, 2)

    def createGame(self):
        FortyThieves.createGame(self, XCARDS=74)

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return (card1.suit != card2.suit and
                (card1.rank + 1 == card2.rank or
                 card2.rank + 1 == card1.rank))


class Midshipman(Indian):
    DEAL = (2, 2)

    def createGame(self):
        FortyThieves.createGame(self, rows=9)


# ************************************************************************
# * Napoleon's Exile
# * Double Rail
# * Single Rail (1 deck)
# *   rows build down by rank
# ************************************************************************

class NapoleonsExile(FortyThieves):
    RowStack_Class = RK_RowStack

    DEAL = (0, 4)

    shallHighlightMatch = Game._shallHighlightMatch_RK


class DoubleRail(NapoleonsExile):
    ROW_MAX_MOVE = UNLIMITED_MOVES
    DEAL = (0, 1)

    def createGame(self):
        FortyThieves.createGame(self, rows=5)


class SingleRail(DoubleRail):
    def createGame(self):
        FortyThieves.createGame(self, rows=4, XCARDS=48)


# ************************************************************************
# * Fortune's Favor
# ************************************************************************

class FortunesFavor(Game):
    ROWS = 2
    COLS = 6

    def createGame(self):

        l, s = Layout(self), self.s

        w, h = l.XM + (2 + self.COLS) * l.XS, 2 * l.YM + (1 + self.ROWS) * l.YS
        self.setSize(w, h)

        offset = 2 + ((self.COLS - 4) / 2)

        x, y = l.XM + offset * l.XS, l.YM
        for i in range(4):
            s.foundations.append(SS_FoundationStack(x, y, self, suit=i))
            x += l.XS
        x, y = l.XM, l.YM
        s.talon = WasteTalonStack(x, y, self, max_rounds=1)
        l.createText(s.talon, 'se')
        y += l.YS
        s.waste = WasteStack(x, y, self)
        l.createText(s.waste, 'se')
        y = 2*l.YM+l.YS
        for i in range(self.ROWS):
            x = l.XM+2*l.XS
            for j in range(self.COLS):
                stack = SS_RowStack(x, y, self, max_move=1)
                stack.CARD_XOFFSET, stack.CARD_YOFFSET = 0, 0
                s.rows.append(stack)
                x += l.XS
            y += l.YS

        l.defaultStackGroups()

    def _shuffleHook(self, cards):
        # move Aces to top of the Talon (i.e. first cards to be dealt)
        return self._shuffleHookMoveToTop(cards,
                                          lambda c: (c.rank == ACE, c.suit))

    def startGame(self):
        self.s.talon.dealRow(rows=self.s.foundations, frames=0)
        self._startAndDealRowAndCards()

    def fillStack(self, stack):
        if len(stack.cards) == 0:
            if stack is self.s.waste and self.s.talon.cards:
                self.s.talon.dealCards()
            elif stack in self.s.rows and self.s.waste.cards:
                self.s.waste.moveMove(1, stack)

    shallHighlightMatch = Game._shallHighlightMatch_SS


# ************************************************************************
# * Octagon
# ************************************************************************

class Octagon(Game):
    Hint_Class = CautiousDefaultHint

    def createGame(self):

        l, s = Layout(self), self.s

        w1 = max(l.XS + 12 * l.XOFFSET, l.XM + 2 * l.XS + l.XS // 2)
        w, h = l.XM + 2 * l.XS + 2 * w1, l.YM + 4 * l.YS
        self.setSize(w, h)

        for x, y in ((l.XM,                l.YM),
                     (l.XM+w1+2*l.XS+l.XM, l.YM),
                     (l.XM,                l.YM+3*l.YS),
                     (l.XM+w1+2*l.XS+l.XM, l.YM+3*l.YS),):
            stack = SS_RowStack(x, y, self, max_move=1)
            stack.CARD_XOFFSET, stack.CARD_YOFFSET = l.XOFFSET, 0
            s.rows.append(stack)
        i = 0
        for x, y in ((l.XM+w1,                    l.YM),
                     (l.XM+w1+l.XS,               l.YM),
                     (l.XM+w1-2*l.XS-l.XS//2-l.XM, l.YM+1.5*l.YS),
                     (l.XM+w1-l.XS-l.XS//2-l.XM,   l.YM+1.5*l.YS),
                     (l.XM+w1+2*l.XS+l.XS//2+l.XM, l.YM+1.5*l.YS),
                     (l.XM+w1+3*l.XS+l.XS//2+l.XM, l.YM+1.5*l.YS),
                     (l.XM+w1,                    l.YM+3*l.YS),
                     (l.XM+w1+l.XS,               l.YM+3*l.YS),):
            s.foundations.append(SS_FoundationStack(x, y, self, suit=i % 4))
            i += 1
        x, y = l.XM+w1, l.YM+1.5*l.YS
        s.talon = WasteTalonStack(x, y, self, max_rounds=4)
        l.createText(s.talon, 's')
        l.createRoundText(s.talon, 'nn')
        x += l.XS
        s.waste = WasteStack(x, y, self)
        l.createText(s.waste, 's')

        l.defaultStackGroups()

    def _shuffleHook(self, cards):
        # move Aces to top of the Talon (i.e. first cards to be dealt)
        return self._shuffleHookMoveToTop(
            cards, lambda c: (c.rank == ACE, (c.deck, c.suit)))

    def startGame(self):
        self.s.talon.dealRow(rows=self.s.foundations, frames=0)
        self.startDealSample()
        for i in range(5):
            self.s.talon.dealRow()
        self.s.talon.dealCards()          # deal first card to WasteStack

    def fillStack(self, stack):
        if stack in self.s.rows and not stack.cards:
            if not self.s.waste.cards:
                self.s.talon.dealCards()
            if self.s.waste.cards:
                self.s.waste.moveMove(1, stack)

    shallHighlightMatch = Game._shallHighlightMatch_SS


# ************************************************************************
# * Squadron
# ************************************************************************

class Squadron(FortyThieves):
    RowStack_Class = SS_RowStack
    Foundation_Class = SS_FoundationStack

    ROWS = 10
    RESERVES = 3

    def createGame(self):
        l, s = Layout(self), self.s
        decks = self.gameinfo.decks

        self.setSize(l.XM + (2 + self.ROWS) * l.XS, l.YM
                     + max(4.5 * l.YS, 2 * l.YS + 12 * l.YOFFSET))

        x, y = l.XM, l.YM
        s.talon = WasteTalonStack(x, y, self, max_rounds=1)
        l.createText(s.talon, 's')
        x += l.XS
        s.waste = WasteStack(x, y, self)
        l.createText(s.waste, 's')
        x += 2 * l.XS
        for i in range(4 * decks):
            s.foundations.append(self.Foundation_Class(x, y, self,
                                                       suit=i // decks))
            x += l.XS
        x, y = l.XM, l.YM + l.YS * 3//2
        for i in range(self.RESERVES):
            s.reserves.append(ReserveStack(x, y, self))
            y += l.YS
        x, y = l.XM+2*l.XS, l.YM+l.YS
        for i in range(self.ROWS):
            s.rows.append(self.RowStack_Class(x, y, self, max_move=1))
            x += l.XS

        l.defaultStackGroups()

    def startGame(self):
        self.s.talon.dealRow(rows=self.s.reserves, frames=0)
        self._startDealNumRows(3)
        self.s.talon.dealRow()
        self.s.talon.dealCards()          # deal first card to WasteStack


# ************************************************************************
# * Waterloo
# ************************************************************************

class Waterloo(FortyThieves):

    RowStack_Class = Spider_SS_RowStack

    ROW_MAX_MOVE = UNLIMITED_MOVES
    DEAL = (0, 1)

    def createGame(self):
        FortyThieves.createGame(self, rows=6)

    def _shuffleHook(self, cards):
        # move Aces to top of the Talon (i.e. first cards to be dealt)
        return self._shuffleHookMoveToTop(
            cards, lambda c: (c.rank == ACE, (c.deck, c.suit)))

    def startGame(self):
        self.startDealSample()
        self.s.talon.dealRow(rows=self.s.foundations)
        self.s.talon.dealRow()
        self.s.talon.dealCards()          # deal first card to WasteStack

    getQuickPlayScore = Game._getSpiderQuickPlayScore
    shallHighlightMatch = Game._shallHighlightMatch_RK


# ************************************************************************
# * Junction
# * Crossroads
# ************************************************************************

class Junction(Game):
    Foundation_Class = StackWrapper(DieRussische_Foundation, max_cards=8)

    def createGame(self, rows=7):

        l, s = Layout(self), self.s

        self.setSize(l.XM+10*l.XS, l.YM+3*l.YS+12*l.YOFFSET)

        y = l.YM
        for i in range(2):
            x = l.XM+2*l.XS
            for j in range(8):
                s.foundations.append(self.Foundation_Class(x, y, self,
                                                           suit=j % 4))
                x += l.XS
            y += l.YS

        x, y = l.XM+(10-rows)*l.XS//2, l.YM+2*l.YS
        for i in range(rows):
            s.rows.append(AC_RowStack(x, y, self))
            x += l.XS

        x, y = l.XM, l.YM
        s.talon = WasteTalonStack(x, y, self, max_rounds=1)
        l.createText(s.talon, 'ne')
        y += l.YS
        s.waste = WasteStack(x, y, self)
        l.createText(s.waste, 'ne')

        l.defaultStackGroups()

    def startGame(self):
        self.startDealSample()
        self.s.talon.dealRow()
        self.s.talon.dealCards()

    shallHighlightMatch = Game._shallHighlightMatch_AC


class Crossroads(Junction):
    Foundation_Class = StackWrapper(SS_FoundationStack, max_cards=13)

    def startGame(self):
        for i in range(3):
            self.s.talon.dealRow(frames=0)
            self.s.talon.dealRow(flip=0, frames=0)
        self.startDealSample()
        self.s.talon.dealRow()
        self.s.talon.dealCards()


# ************************************************************************
# * Interchange
# * Unlimited
# * Alternation
# * Triple Interchange
# ************************************************************************

class Interchange(FortyThieves):

    RowStack_Class = StackWrapper(SS_RowStack, base_rank=KING)

    ROW_MAX_MOVE = UNLIMITED_MOVES

    def createGame(self):
        FortyThieves.createGame(self, rows=7)

    def startGame(self):
        for i in (0, 1, 2):
            self.s.talon.dealRow(frames=0)
            self.s.talon.dealRow(flip=0, frames=0)
        self.startDealSample()
        self.s.talon.dealRow()
        self.s.talon.dealCards()


class Unlimited(Interchange):
    def createGame(self):
        FortyThieves.createGame(self, rows=7, XOFFSET=0,
                                max_rounds=UNLIMITED_REDEALS)


class Alternation(Interchange):
    RowStack_Class = AC_RowStack
    shallHighlightMatch = Game._shallHighlightMatch_AC


class TripleInterchange(Interchange):
    RowStack_Class = SS_RowStack

    def createGame(self):
        FortyThieves.createGame(self, rows=9, XOFFSET=0,
                                max_rounds=UNLIMITED_REDEALS)

    def startGame(self):
        for i in (0, 1, 2, 3):
            self.s.talon.dealRow(frames=0)
            self.s.talon.dealRow(flip=0, frames=0)
        self.startDealSample()
        self.s.talon.dealRow()
        self.s.talon.dealCards()


# register the game
registerGame(GameInfo(13, FortyThieves, "Forty Thieves",
                      GI.GT_FORTY_THIEVES, 2, 0, GI.SL_MOSTLY_SKILL,
                      altnames=("Napoleon at St. Helena", "Le Cadran",
                                "Roosevelt at San Juan")))
registerGame(GameInfo(80, BusyAces, "Busy Aces",
                      GI.GT_FORTY_THIEVES, 2, 0, GI.SL_BALANCED))
registerGame(GameInfo(228, Limited, "Limited",
                      GI.GT_FORTY_THIEVES, 2, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(79, WaningMoon, "Waning Moon",
                      GI.GT_FORTY_THIEVES, 2, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(125, Lucas, "Lucas",
                      GI.GT_FORTY_THIEVES, 2, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(109, Deuces, "Deuces",
                      GI.GT_FORTY_THIEVES, 2, 0, GI.SL_MOSTLY_SKILL,
                      altnames=("Twos", "Les Deux")))
registerGame(GameInfo(196, Corona, "Corona",
                      GI.GT_FORTY_THIEVES, 2, 0, GI.SL_BALANCED,
                      altnames=("Round Dozen")))
registerGame(GameInfo(195, Quadrangle, "Quadrangle",
                      GI.GT_FORTY_THIEVES, 2, 0, GI.SL_BALANCED))
registerGame(GameInfo(110, Courtyard, "Courtyard",
                      GI.GT_FORTY_THIEVES, 2, 0, GI.SL_BALANCED))
registerGame(GameInfo(23, FortyAndEight, "Forty and Eight",
                      GI.GT_FORTY_THIEVES, 2, 1, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(115, LittleForty, "Little Forty",         # was: 72
                      GI.GT_FORTY_THIEVES, 2, 3, GI.SL_BALANCED))
registerGame(GameInfo(76, Streets, "Streets",
                      GI.GT_FORTY_THIEVES, 2, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(73, Maria, "Maria",
                      GI.GT_FORTY_THIEVES, 2, 0, GI.SL_BALANCED,
                      altnames=("Maria Luisa", "Thirty-Six Card Tableau")))
registerGame(GameInfo(70, NumberTen, "Number Ten",
                      GI.GT_FORTY_THIEVES, 2, 0, GI.SL_BALANCED))
registerGame(GameInfo(71, RankAndFile, "Rank and File",
                      GI.GT_FORTY_THIEVES, 2, 0, GI.SL_BALANCED,
                      altnames=("Dress Parade")))
registerGame(GameInfo(126, RedAndBlack, "Red and Black",        # was: 75
                      GI.GT_FORTY_THIEVES, 2, 0, GI.SL_BALANCED))
registerGame(GameInfo(113, Zebra, "Zebra",
                      GI.GT_FORTY_THIEVES, 2, 1, GI.SL_BALANCED))
registerGame(GameInfo(69, Indian, "Indian",
                      GI.GT_FORTY_THIEVES, 2, 0, GI.SL_BALANCED))
registerGame(GameInfo(74, Midshipman, "Midshipman",
                      GI.GT_FORTY_THIEVES, 2, 0, GI.SL_BALANCED))
registerGame(GameInfo(131, DoubleRail, "Double Rail",
                      GI.GT_FORTY_THIEVES, 2, 0, GI.SL_BALANCED))
registerGame(GameInfo(199, SingleRail, "Single Rail",
                      GI.GT_FORTY_THIEVES, 1, 0, GI.SL_MOSTLY_LUCK,
                      altnames=("Auxiliary Sequences")))
registerGame(GameInfo(295, NapoleonsSquare, "Napoleon's Square",
                      GI.GT_FORTY_THIEVES, 2, 0, GI.SL_BALANCED))
registerGame(GameInfo(310, Emperor, "Emperor",
                      GI.GT_FORTY_THIEVES, 2, 0, GI.SL_BALANCED,
                      altnames=("Deauville")))
registerGame(GameInfo(416, FortunesFavor, "Fortune's Favor",
                      GI.GT_FORTY_THIEVES, 1, 0, GI.SL_LUCK))
registerGame(GameInfo(426, Octagon, "Octagon",
                      GI.GT_FORTY_THIEVES, 2, 3, GI.SL_BALANCED))
registerGame(GameInfo(440, Squadron, "Squadron",
                      GI.GT_FORTY_THIEVES, 2, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(462, Josephine, "Josephine",
                      GI.GT_FORTY_THIEVES, 2, 0, GI.SL_MOSTLY_SKILL,
                      altnames=("Forty Bandits", "Pack of Thieves")))
registerGame(GameInfo(493, MarieRose, "Marie Rose",
                      GI.GT_FORTY_THIEVES, 3, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(540, Waterloo, "Waterloo",
                      GI.GT_FORTY_THIEVES, 2, 0, GI.SL_BALANCED))
registerGame(GameInfo(574, Interchange, "Interchange",
                      GI.GT_FORTY_THIEVES, 2, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(575, Unlimited, "Unlimited",
                      GI.GT_FORTY_THIEVES, 2, -1, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(628, Crossroads, "Crossroads",
                      GI.GT_FORTY_THIEVES, 4, 0, GI.SL_BALANCED))
registerGame(GameInfo(631, Alternation, "Alternation",
                      GI.GT_FORTY_THIEVES, 2, 0, GI.SL_BALANCED))
registerGame(GameInfo(679, TripleInterchange, "Triple Interchange",
                      GI.GT_FORTY_THIEVES, 3, -1, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(775, SixtyThieves, "Sixty Thieves",
                      GI.GT_FORTY_THIEVES, 3, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(776, EightyThieves, "Eighty Thieves",
                      GI.GT_FORTY_THIEVES, 4, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(847, Pluto, "Pluto",
                      GI.GT_FORTY_THIEVES, 2, 0, GI.SL_MOSTLY_SKILL,
                      altnames=("Square")))
registerGame(GameInfo(848, Malmaison, "Malmaison",
                      GI.GT_FORTY_THIEVES, 4, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(981, NapoleonsFolly, "Napoleon's Folly",
                      GI.GT_FORTY_THIEVES, 2, 0, GI.SL_MOSTLY_SKILL))
