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
from pysollib.games.spider import Spider_Hint
from pysollib.hint import KlondikeType_Hint
from pysollib.layout import Layout
from pysollib.mfxutil import kwdefault
from pysollib.stack import (
    AC_RowStack,
    AbstractFoundationStack,
    BasicRowStack,
    DealRowTalonStack,
    InitialDealTalonStack,
    KingAC_RowStack,
    OpenStack,
    ReserveStack,
    SS_FoundationStack,
    SS_RowStack,
    Stack,
    StackWrapper,
    WasteStack,
    WasteTalonStack,
)
from pysollib.util import ACE, ANY_SUIT, UNLIMITED_ACCEPTS, UNLIMITED_MOVES

# ************************************************************************
# * Gypsy
# ************************************************************************


class Gypsy(Game):
    Layout_Method = staticmethod(Layout.gypsyLayout)
    Talon_Class = DealRowTalonStack
    Foundation_Class = SS_FoundationStack
    RowStack_Class = AC_RowStack
    Hint_Class = KlondikeType_Hint

    def createGame(self, rows=8, **layout):
        # create layout
        l, s = Layout(self), self.s
        kwdefault(layout, rows=rows, waste=0, texts=1)
        self.Layout_Method(l, **layout)
        self.setSize(l.size[0], l.size[1])
        # create stacks
        s.talon = self.Talon_Class(l.s.talon.x, l.s.talon.y, self)
        if l.s.waste:
            s.waste = WasteStack(l.s.waste.x, l.s.waste.y, self)
        for r in l.s.foundations:
            s.foundations.append(
                self.Foundation_Class(r.x, r.y, self, suit=r.suit))
        for r in l.s.rows:
            s.rows.append(self.RowStack_Class(r.x, r.y, self))
        # default
        l.defaultAll()

    def startGame(self, flip=0):
        for i in range(2):
            self.s.talon.dealRow(flip=flip, frames=0)
        self._startAndDealRow()

    shallHighlightMatch = Game._shallHighlightMatch_AC


class Gypsy3Decks(Gypsy):
    def createGame(self, **layout):
        Gypsy.createGame(self, rows=12)


# ************************************************************************
# * Giant
# ************************************************************************

class Giant_Foundation(SS_FoundationStack):
    def canMoveCards(self, cards):
        if not SS_FoundationStack.canMoveCards(self, cards):
            return False
        # can only move cards if the Talon is empty
        return len(self.game.s.talon.cards) == 0


class Giant(Gypsy):
    Foundation_Class = Giant_Foundation

    def startGame(self):
        self._startAndDealRow()


# ************************************************************************
# * Die Russische
# ************************************************************************

class DieRussische_Foundation(AbstractFoundationStack):
    def acceptsCards(self, from_stack, cards):
        if not AbstractFoundationStack.acceptsCards(self, from_stack, cards):
            return False
        if self.cards:
            # check the rank - an ACE equals a Six
            rank = self.cards[-1].rank
            if rank == ACE:
                rank = 5
            if (rank + self.cap.dir) % self.cap.mod != cards[0].rank:
                return False
        return True


class DieRussische_RowStack(AC_RowStack):
    def acceptsCards(self, from_stack, cards):
        if not AC_RowStack.acceptsCards(self, from_stack, cards):
            return False
        # when empty, only accept a single card
        return self.cards or len(cards) == 1


class DieRussische(Gypsy):
    Talon_Class = InitialDealTalonStack
    Foundation_Class = StackWrapper(
        DieRussische_Foundation, min_cards=1, max_cards=8)
    RowStack_Class = DieRussische_RowStack

    def createGame(self):
        Gypsy.createGame(self, rows=7, texts=0)

    def _shuffleHook(self, cards):
        # move one Ace to bottom of the Talon (i.e. last card to be dealt)
        return self._shuffleHookMoveToBottom(
            cards, lambda c: (c.rank == 0, c.suit), 1)

    def startGame(self):
        self._startDealNumRows(6)
        for i in range(3):
            self.s.talon.dealRow()
        c = self.s.talon.cards[-1]
        self.s.talon.dealRow(rows=(self.s.foundations[c.suit*2],))


# ************************************************************************
# * Miss Milligan
# ************************************************************************

class MissMilligan_ReserveStack(AC_RowStack):
    def acceptsCards(self, from_stack, cards):
        if not AC_RowStack.acceptsCards(self, from_stack, cards):
            return False
        # Note that this reserve stack accepts sequences if both
        # the reserve stack and the Talon are empty.
        return len(self.cards) == 0 and len(self.game.s.talon.cards) == 0

    getBottomImage = Stack._getReserveBottomImage


class MissMilligan(Gypsy):
    Foundation_Class = StackWrapper(SS_FoundationStack, max_move=0)
    RowStack_Class = KingAC_RowStack
    ReserveStack_Class = MissMilligan_ReserveStack

    def createGame(self, rows=8, reserves=1):
        # create layout
        l, s = Layout(self), self.s

        # set window
        self.setSize(
            l.XM + (1+max(8, rows))*l.XS,
            l.YM + (1+max(4, reserves))*l.YS+l.TEXT_HEIGHT)

        # create stacks
        x, y = l.XM, l.YM
        s.talon = self.Talon_Class(x, y, self)
        for i in range(8):
            x = x + l.XS
            s.foundations.append(self.Foundation_Class(x, y, self, suit=i//2))
        x, y = l.XM, y + l.YS
        rx, ry = x + l.XS - l.CW//2, y - l.CH//2
        for i in range(reserves):
            s.reserves.append(
                self.ReserveStack_Class(x, y+l.TEXT_HEIGHT, self))
            y = y + l.YS
        l.createText(s.talon, "s")
        if s.reserves:
            self.setRegion(s.reserves, (-999, ry+l.TEXT_HEIGHT, rx-1, 999999))
        else:
            rx = -999
        x, y = l.XM + (8-rows)*l.XS//2, l.YM + l.YS
        for i in range(rows):
            x = x + l.XS
            s.rows.append(self.RowStack_Class(x, y, self))
        self.setRegion(s.rows, (rx, ry, 999999, 999999))

        # define stack-groups
        l.defaultStackGroups()

    def startGame(self):
        self._startAndDealRow()


# ************************************************************************
# * Milligan Cell
# ************************************************************************

class MilliganCell(MissMilligan):
    ReserveStack_Class = ReserveStack

    def createGame(self):
        MissMilligan.createGame(self, reserves=4)

    def startGame(self):
        self._startAndDealRow()


# ************************************************************************
# * Milligan Harp
# * Carlton
# ************************************************************************

class MilliganHarp(Gypsy):
    Foundation_Class = StackWrapper(SS_FoundationStack, max_move=0)

    def startGame(self, flip=0):
        for i in range(len(self.s.rows)):
            self.s.talon.dealRow(rows=self.s.rows[i+1:], flip=flip, frames=0)
        self._startAndDealRow()


class Carlton(MilliganHarp):
    def startGame(self):
        MilliganHarp.startGame(self, flip=1)


# ************************************************************************
# * Blockade
# ************************************************************************

class Blockade(Gypsy):
    Layout_Method = staticmethod(Layout.klondikeLayout)
    RowStack_Class = SS_RowStack

    def createGame(self):
        Gypsy.createGame(self, rows=12)

    def startGame(self):
        self._startAndDealRow()

    def fillStack(self, stack):
        if stack in self.s.rows and not stack.cards and self.s.talon.cards:
            old_state = self.enterState(self.S_FILL)
            self.s.talon.flipMove()
            self.s.talon.moveMove(1, stack)
            self.leaveState(old_state)

    shallHighlightMatch = Game._shallHighlightMatch_SS


# ************************************************************************
# * Surprise
# ************************************************************************

class Surprise_ReserveStack(ReserveStack):
    def acceptsCards(self, from_stack, cards):
        if not ReserveStack.acceptsCards(self, from_stack, cards):
            return False
        return len(self.game.s.talon.cards) == 0


class Surprise(Gypsy):

    def createGame(self, rows=8, reserves=1):
        # create layout
        l, s = Layout(self), self.s

        # set window
        self.setSize(l.XM+11*l.XS, l.YM+2*l.YS+12*l.YOFFSET+20)

        # create stacks
        x, y = l.XM, l.YM
        s.talon = self.Talon_Class(x, y, self)
        l.createText(s.talon, 's')
        x += l.XS
        stack = Surprise_ReserveStack(x, y, self, max_cards=3)
        xoffset = min(l.XOFFSET, l.XS//3)
        stack.CARD_XOFFSET = xoffset
        s.reserves.append(stack)
        x += 2*l.XS
        for i in range(8):
            s.foundations.append(SS_FoundationStack(x, y, self, suit=i//2))
            x += l.XS
        x, y = l.XM, l.YM+l.YS+l.TEXT_HEIGHT
        for i in range(11):
            s.rows.append(KingAC_RowStack(x, y, self))
            x += l.XS

        # define stack-groups
        l.defaultStackGroups()

    def startGame(self):
        for i in range(1, 6):
            self.s.talon.dealRow(rows=self.s.rows[i:-i], flip=0, frames=0)
        self._startAndDealRow()


# ************************************************************************
# * Hypotenuse
# ************************************************************************

class Hypotenuse(Gypsy):
    Layout_Method = staticmethod(Layout.klondikeLayout)
    RowStack_Class = KingAC_RowStack

    def createGame(self, rows=10, playcards=24):
        Gypsy.createGame(self, rows=rows, playcards=playcards)

    def startGame(self, flip=0, rows=10):
        for i in range(1, rows):
            self.s.talon.dealRow(rows=self.s.rows[i:], flip=flip, frames=0)
        self._startAndDealRow()


# ************************************************************************
# * Eclipse
# ************************************************************************

class Eclipse(Gypsy):
    Layout_Method = staticmethod(Layout.klondikeLayout)
    RowStack_Class = SS_RowStack

    def createGame(self):
        Gypsy.createGame(self, rows=13)

    def startGame(self):
        self._startDealNumRowsAndDealSingleRow(3)

    shallHighlightMatch = Game._shallHighlightMatch_SS


# ************************************************************************
# * Brazilian Patience
# * (Removed as it's a duplicate of Hypotenuse)
# ************************************************************************

# class BrazilianPatience(Gypsy):
#     Layout_Method = staticmethod(Layout.klondikeLayout)
#     RowStack_Class = KingAC_RowStack

#     def createGame(self):
#         Gypsy.createGame(self, rows=10, playcards=22)

#     def startGame(self, flip=0, reverse=1):
#         for i in range(1, 10):
#             self.s.talon.dealRow(rows=self.s.rows[i:], flip=0, frames=0)
#         self._startAndDealRow()


# ************************************************************************
# * Locked Cards
# ************************************************************************

class LockedCards_Reserve(OpenStack):
    def canFlipCard(self):
        if not OpenStack.canFlipCard(self):
            return False
        i = list(self.game.s.reserves).index(self)
        return len(self.game.s.foundations[i].cards) == 13


class LockedCards_Foundation(SS_FoundationStack):
    def acceptsCards(self, from_stack, cards):
        if not SS_FoundationStack.acceptsCards(self, from_stack, cards):
            return False
        if self.cards:
            # check suit
            return self.cards[-1].suit == cards[0].suit
        return True


class LockedCards(Game):
    Foundation_Class = LockedCards_Foundation
    RowStack_Class = AC_RowStack

    def createGame(self):

        # create layout
        l, s = Layout(self), self.s

        # set window
        self.setSize(l.XM+10*l.XS, l.YM+3*l.YS+14*l.YOFFSET)

        # create stacks
        x, y = l.XM, l.YM
        for i in range(7):
            s.reserves.append(LockedCards_Reserve(x, y, self))
            x += l.XS

        x, y = l.XM, l.YM+l.YS
        for i in range(8):
            s.foundations.append(self.Foundation_Class(x, y, self,
                                 suit=ANY_SUIT, max_move=0))
            x += l.XS

        x, y = l.XM, l.YM+2*l.YS
        for i in range(8):
            s.rows.append(self.RowStack_Class(x, y, self))
            x += l.XS

        x, y = self.width - l.XS, self.height - l.YS - l.TEXT_HEIGHT
        s.talon = WasteTalonStack(x, y, self, max_rounds=3)
        l.createText(s.talon, 's')
        l.createRoundText(s.talon, 'n')

        x -= l.XS
        s.waste = WasteStack(x, y, self)
        l.createText(s.waste, 's')

        # define stack-groups
        l.defaultStackGroups()

    def startGame(self, rows=5):
        self.s.talon.dealRow(rows=self.s.reserves, flip=0, frames=0)
        self._startDealNumRowsAndDealRowAndCards(rows-1)

    shallHighlightMatch = Game._shallHighlightMatch_AC


# ************************************************************************
# * Thirty
# ************************************************************************

class Thirty_RowStack(BasicRowStack):
    def acceptsCards(self, from_stack, cards):
        if not BasicRowStack.acceptsCards(self, from_stack, cards):
            return False
        if self.cards:
            # check the rank - an ACE equals a Six
            rank = self.cards[-1].rank
            if rank == ACE:
                rank = 5
            if (rank + self.cap.dir) % self.cap.mod != cards[0].rank:
                return False
        return True

    def canMoveCards(self, cards):
        if not BasicRowStack.canMoveCards(self, cards):
            return False
        c1 = cards[0]
        for c2 in cards[1:]:
            if c1.suit != c2.suit:
                return False
            # check the rank - an ACE equals a Six
            rank = c1.rank
            if rank == ACE:
                rank = 5
            if (rank + self.cap.dir) % self.cap.mod != c2.rank:
                return False
            c1 = c2
        return True


class Thirty(Game):
    Hint_Class = Spider_Hint

    def createGame(self):

        l, s = Layout(self), self.s
        self.setSize(l.XM+7*l.XS, l.YM+2*l.YS+12*l.YOFFSET)

        x, y = l.XM, l.YM
        for i in range(2):
            s.reserves.append(OpenStack(x, y, self))
            x += l.XS

        x, y = l.XM+3*l.XS, l.YM
        for i in range(4):
            s.foundations.append(DieRussische_Foundation(x, y, self,
                                                         suit=i, max_cards=8))
            x += l.XS

        x, y = l.XM+l.XS//2, l.YM+l.YS
        for i in range(6):
            s.rows.append(Thirty_RowStack(x, y, self,
                          max_move=UNLIMITED_MOVES,
                          max_accept=UNLIMITED_ACCEPTS))
            x += l.XS

        x, y = self.width-l.XS, self.height-l.YS
        s.talon = InitialDealTalonStack(x, y, self)

        l.defaultAll()

    def startGame(self):
        self._startDealNumRows(4)
        self.s.talon.dealRow()
        self.s.talon.dealRow(rows=self.s.reserves)

    shallHighlightMatch = Game._shallHighlightMatch_RK
    getQuickPlayScore = Game._getSpiderQuickPlayScore


# register the game
registerGame(GameInfo(1, Gypsy, "Gypsy",
                      GI.GT_GYPSY, 2, 0, GI.SL_MOSTLY_SKILL,
                      altnames=("Double Easthaven", "Normandy",)))
registerGame(GameInfo(65, Giant, "Giant",
                      GI.GT_GYPSY, 2, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(174, DieRussische, "Russian Patience",
                      GI.GT_KLONDIKE | GI.GT_OPEN | GI.GT_STRIPPED,
                      2, 0, GI.SL_MOSTLY_SKILL,
                      ranks=(0, 6, 7, 8, 9, 10, 11, 12),
                      altnames=("Die Russische",)))
registerGame(GameInfo(62, MissMilligan, "Miss Milligan",
                      GI.GT_GYPSY, 2, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(78, MilliganCell, "Milligan Cell",
                      GI.GT_GYPSY, 2, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(217, MilliganHarp, "Milligan Harp",
                      GI.GT_GYPSY, 2, 0, GI.SL_BALANCED))
registerGame(GameInfo(218, Carlton, "Carlton",
                      GI.GT_GYPSY, 2, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(226, Blockade, "Blockade",
                      GI.GT_GYPSY, 2, 0, GI.SL_BALANCED))
registerGame(GameInfo(453, Gypsy3Decks, "Gypsy (3 Decks)",
                      GI.GT_GYPSY, 3, 0, GI.SL_MOSTLY_SKILL,
                      altnames=("Triple Easthaven",)))
registerGame(GameInfo(463, Surprise, "Surprise",
                      GI.GT_GYPSY, 2, 0, GI.SL_BALANCED))
registerGame(GameInfo(566, Hypotenuse, "Hypotenuse",
                      GI.GT_GYPSY, 2, 0, GI.SL_MOSTLY_SKILL,
                      altnames=("Brazilian Patience",)))
registerGame(GameInfo(584, Eclipse, "Eclipse",
                      GI.GT_GYPSY, 2, 0, GI.SL_MOSTLY_SKILL))
# registerGame(GameInfo(640, BrazilianPatience, "Brazilian Patience",
#                       GI.GT_GYPSY, 2, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(718, LockedCards, "Locked Cards",
                      GI.GT_2DECK_TYPE, 2, 2, GI.SL_BALANCED,
                      altnames=("Prisoners",)))
registerGame(GameInfo(721, Thirty, "Thirty",
                      GI.GT_1DECK_TYPE | GI.GT_OPEN | GI.GT_STRIPPED, 1, 0,
                      GI.SL_MOSTLY_SKILL, ranks=(0, 6, 7, 8, 9, 10, 11, 12)))
