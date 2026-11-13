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
from pysollib.hint import AbstractHint, CautiousDefaultHint
from pysollib.layout import Layout
from pysollib.mfxutil import kwdefault
from pysollib.stack import \
    AutoDealTalonStack, \
    BasicRowStack, \
    InitialDealTalonStack, \
    OpenStack, \
    OpenTalonStack, \
    RK_RowStack, \
    SS_FoundationStack, \
    SS_RowStack, \
    StackWrapper, \
    WasteStack, \
    WasteTalonStack, \
    isRankSequence, \
    isSameSuitSequence
from pysollib.util import BLACK, KING, RED, UNLIMITED_ACCEPTS, UNLIMITED_MOVES

# ************************************************************************
# * Curds and Whey
# ************************************************************************


class CurdsAndWhey_RowStack(BasicRowStack):

    def acceptsCards(self, from_stack, cards):
        if not BasicRowStack.acceptsCards(self, from_stack, cards):
            return False
        if not self.cards:
            return True
        c1, c2 = self.cards[-1], cards[0]
        if c1.rank == c2.rank:
            return True
        if c1.suit == c2.suit:
            return c1.rank == c2.rank+1
        return False

    def canMoveCards(self, cards):
        return isSameSuitSequence(cards) or isRankSequence(cards, dir=0)

    def getHelp(self):
        return 'Tableau. Build down by suit or of the same rank.'


class CurdsAndWhey(Game):

    Hint_Class = CautiousDefaultHint
    RowStack_Class = StackWrapper(
        CurdsAndWhey_RowStack, base_rank=KING,
        max_move=UNLIMITED_MOVES, max_accept=UNLIMITED_ACCEPTS)

    #
    # game layout
    #

    def createGame(self, rows=13):
        # create layout
        l, s = Layout(self), self.s

        # set window
        w, h = l.XM+rows*l.XS, l.YM+l.YS+16*l.YOFFSET
        self.setSize(w, h)

        # create stacks
        x, y = l.XM, l.YM
        for i in range(rows):
            stack = self.RowStack_Class(x, y, self)
            s.rows.append(stack)
            x += l.XS

        s.talon = InitialDealTalonStack(w-l.XS, h-l.YS, self)

        # default
        l.defaultAll()

    #
    # game overrides
    #

    def startGame(self):
        self._startDealNumRowsAndDealSingleRow(3)

    def isGameWon(self):
        for s in self.s.rows:
            if s.cards:
                if len(s.cards) != 13 or not isSameSuitSequence(s.cards):
                    return False
        return True

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return card1.rank == card2.rank or (
            card1.suit == card2.suit and abs(card1.rank-card2.rank) == 1)


# ************************************************************************
# * Dumfries
# ************************************************************************

class Dumfries_TalonStack(OpenTalonStack):
    rightclickHandler = OpenStack.rightclickHandler
    doubleclickHandler = OpenStack.doubleclickHandler


class Dumfries_RowStack(BasicRowStack):

    def acceptsCards(self, from_stack, cards):
        if not BasicRowStack.acceptsCards(self, from_stack, cards):
            return False
        if not self.cards:
            return True
        c1, c2 = self.cards[-1], cards[0]
        if c1.color == c2.color:
            return False
        return c1.rank == c2.rank or c1.rank == c2.rank+1

    def canMoveCards(self, cards):
        return len(cards) == 1 or len(cards) == len(self.cards)


class Dumfries(Game):

    # Hint_Class = KlondikeType_Hint

    def createGame(self, **layout):
        # create layout
        l, s = Layout(self), self.s
        kwdefault(layout, rows=8, waste=0, texts=1, playcards=20)
        l.klondikeLayout(**layout)
        self.setSize(l.size[0], l.size[1])
        # create stacks
        s.talon = Dumfries_TalonStack(l.s.talon.x, l.s.talon.y, self)
        for r in l.s.foundations:
            s.foundations.append(SS_FoundationStack(r.x, r.y, self,
                                                    suit=r.suit))
        for r in l.s.rows:
            s.rows.append(Dumfries_RowStack(r.x, r.y, self,
                                            max_move=UNLIMITED_MOVES,
                                            max_accept=UNLIMITED_ACCEPTS))
        # default
        l.defaultAll()
        self.sg.dropstacks.append(s.talon)

    def startGame(self):
        self.startDealSample()
        self.s.talon.dealRow()
        self.s.talon.fillStack()

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return card1.color != card2.color and \
            abs(card1.rank-card2.rank) in (0, 1)


# ************************************************************************
# * German Patience
# ************************************************************************

class GermanPatience(Game):
    Hint_Class = CautiousDefaultHint

    def createGame(self, rows=8):

        l, s = Layout(self), self.s

        w, h = l.XM+rows*l.XS, l.YM+2*l.YS+14*l.YOFFSET
        self.setSize(w, h)

        x, y = l.XM, l.YM
        for i in range(rows):
            s.rows.append(
                RK_RowStack(
                    x, y, self, max_cards=13, mod=13, dir=1, max_move=1))
            x += l.XS
        x, y = l.XM, h-l.YS
        s.talon = WasteTalonStack(x, y, self, max_rounds=1)
        l.createText(s.talon, 'n')
        x += l.XS
        s.waste = WasteStack(x, y, self)
        l.createText(s.waste, 'n')

        l.defaultStackGroups()

    def startGame(self):
        self.startDealSample()
        self.s.talon.dealRow()
        self.s.talon.dealCards()

    def isGameWon(self):
        if self.s.waste.cards or self.s.talon.cards:
            return False
        for s in self.s.rows:
            if s.cards:
                if len(s.cards) != 13:  # or not isRankSequence(s.cards):
                    return False
        return True

    shallHighlightMatch = Game._shallHighlightMatch_RKW


# ************************************************************************
# * Trusty Twelve
# ************************************************************************

class TrustyTwelve_Hint(AbstractHint):
    def computeHints(self):
        game = self.game
        for r in game.s.rows:
            for t in game.s.rows:
                if r is t:
                    continue
                card = r.cards[-1]
                if len(r.cards) == 1 and t.acceptsCards(r, [card]):
                    if len(t.cards) > 1:
                        self.addHint(6000+card.rank, 1, r, t)
                    else:
                        self.addHint(5000+card.rank, 1, r, t)


class TrustyTwelve(Game):
    Hint_Class = TrustyTwelve_Hint

    TALON_CLASS = AutoDealTalonStack
    ROWSTACK_CLASS = RK_RowStack

    def createGame(self, rows=12):
        l, s = Layout(self), self.s
        self.setSize((2 * l.XM) + (rows + 1) * l.XS,
                     l.YM + l.YS + 12 * l.YOFFSET)
        x, y = l.XM, l.YM
        s.talon = self.TALON_CLASS(x, y, self)
        l.createText(s.talon, "s")
        x += (l.XS + l.XM)
        for i in range(rows):
            s.rows.append(self.ROWSTACK_CLASS(x, y, self, max_move=1))
            x += l.XS
        l.defaultStackGroups()

    def startGame(self):
        self._startAndDealRow()

    def fillStack(self, stack):
        if not stack.cards and stack in self.s.rows:
            if self.s.talon.cards:
                old_state = self.enterState(self.S_FILL)
                if not self.s.talon.cards[-1].face_up:
                    self.s.talon.flipMove()
                self.s.talon.moveMove(1, stack)
                self.leaveState(old_state)

    def isGameWon(self):
        return len(self.s.talon.cards) == 0

    shallHighlightMatch = Game._shallHighlightMatch_RK


# ************************************************************************
# * Eight Packs (ex. Four Packs)
# ************************************************************************

class EightPacks(Game):
    RowStack_Class = SS_RowStack

    def createGame(self, max_rounds=3, width=10, playcards=14):
        l, s = Layout(self), self.s
        self.setSize(l.XM + width * l.XS,
                     l.YM + 2 * l.YS + (2 * l.TEXT_HEIGHT) +
                     playcards * l.YOFFSET)

        x, y = l.XM, l.YM
        for i in range(10):
            s.rows.append(self.RowStack_Class(x, y, self, dir=1))
            x += l.XS

        x, y = self.width - l.XS, self.height - l.YS - l.TEXT_HEIGHT
        s.talon = WasteTalonStack(x, y, self, max_rounds=max_rounds)
        l.createText(s.talon, 's')
        l.createRoundText(s.talon, 'n')

        x -= l.XS
        s.waste = WasteStack(x, y, self)
        l.createText(s.waste, 's')

        l.defaultStackGroups()

    def startGame(self):
        self.startDealSample()
        self.s.talon.dealRow()
        self.s.talon.dealCards()

    def isGameWon(self):
        if self.s.talon.cards or self.s.waste.cards:
            return False
        for s in self.s.rows:
            if s.cards:
                if len(s.cards) != 13:
                    return False
        return True

    shallHighlightMatch = Game._shallHighlightMatch_SS


# ************************************************************************
# * Fire and Ice
# ************************************************************************

class FireAndIce(Game):
    RowStack_Class = RK_RowStack

    def createGame(self, playcards=18):
        l, s = Layout(self), self.s
        self.setSize(l.XM + (10.5 * l.XS),
                     l.YM + l.YS + playcards * l.YOFFSET)

        x, y = l.XM, l.YM
        for i in range(5):
            s.rows.append(self.RowStack_Class(x, y, self))
            x += l.XS

        x += l.XS / 2

        for i in range(5):
            s.rows.append(self.RowStack_Class(x, y, self))
            x += l.XS

        x, y = self.width - l.XS, self.height - l.YS
        s.talon = InitialDealTalonStack(x, y, self)

        l.defaultStackGroups()

    def startGame(self):
        for i in range(4):
            self.s.talon.dealRow(frames=0)
        r = self.s.rows
        rows = (r[0], r[9])
        self.s.talon.dealRow(rows=rows, frames=0)
        self._startAndDealRow()

    def isGameWon(self):
        for i in self.s.rows[0:5]:
            for j in i.cards:
                if j.color != RED:
                    return False
        for i in self.s.rows[5:10]:
            for j in i.cards:
                if j.color != BLACK:
                    return False


# register the game
registerGame(GameInfo(294, CurdsAndWhey, "Curds and Whey",
                      GI.GT_SPIDER | GI.GT_OPEN, 1, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(311, Dumfries, "Dumfries",
                      GI.GT_1DECK_TYPE, 1, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(414, GermanPatience, "German Patience",
                      GI.GT_2DECK_TYPE, 2, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(480, TrustyTwelve, "Trusty Twelve",
                      GI.GT_1DECK_TYPE, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(724, EightPacks, "Eight Packs",
                      GI.GT_2DECK_TYPE | GI.GT_ORIGINAL, 2, 2,
                      GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(830, FireAndIce, "Fire and Ice",
                      GI.GT_1DECK_TYPE | GI.GT_OPEN, 1, 0, GI.SL_SKILL))
