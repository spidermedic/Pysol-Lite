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
from pysollib.hint import FreeCellSolverWrapper
from pysollib.hint import (
    HINT_LEVEL_DEBUG,
    SpiderType_Hint,
    YukonType_Hint,
)
from pysollib.layout import Layout
from pysollib.mfxutil import kwdefault
from pysollib.stack import (
    AC_FoundationStack,
    AC_RowStack,
    AutoDealTalonStack,
    BasicRowStack,
    DealRowTalonStack,
    InitialDealTalonStack,
    KingAC_RowStack,
    OpenStack,
    RK_RowStack,
    ReserveStack,
    SS_FoundationStack,
    Spider_AC_Foundation,
    Spider_SS_Foundation,
    Spider_SS_RowStack,
    StackWrapper,
    SuperMoveStack_StackMethods,
    TalonStack,
    WasteStack,
    Yukon_AC_RowStack,
    Yukon_SS_RowStack,
    isAlternateColorSequence,
    isRankSequence,
)
from pysollib.util import ANY_RANK, ANY_SUIT, KING


class Spider_Hint(SpiderType_Hint):
    # FIXME: demo is not too clever in this game

    BONUS_SAME_SUIT_MOVE = 400

    def _preferHighRankMoves(self):
        return 1

    def shallMovePile(self, r, t, pile, rpile):
        # the pile we are going to move from r to t
        # could be moved back from t ro r - this is
        # dangerous for as we can create loops...
        if len(t.cards) == 0:
            return t.acceptsCards(r, pile)
        if not SpiderType_Hint.shallMovePile(self, r, t, pile, rpile):
            return False
        rr = self.ClonedStack(r, stackcards=rpile)
        if rr.acceptsCards(t, pile):
            if pile[0].suit == t.cards[-1].suit:
                # The pile will get moved onto the correct suit
                if len(rpile) == 0 or pile[0].suit != rpile[-1].suit:
                    return True
            # Uncovering a run that can drop is progress, not a shuffle.
            if rr.canDropCards(self.game.s.foundations)[0]:
                return True
            if self.level <= HINT_LEVEL_DEBUG and len(rpile) == 0:
                return True
            return False
        return True


class Spider_RowStack(Spider_SS_RowStack):
    canDropCards = BasicRowStack.spiderCanDropCards


class SuperMoveSpider_RowStack(SuperMoveStack_StackMethods, Spider_RowStack):
    def acceptsCards(self, from_stack, cards):
        if not Spider_RowStack.acceptsCards(self, from_stack, cards):
            return False
        num_seq = self._getNumSSSeq(cards)
        max_move = self._getMaxMove(len(self.cards))
        return num_seq <= max_move

    def canMoveCards(self, cards):
        if not self.basicCanMoveCards(cards):
            return False
        if not isRankSequence(cards, self.cap.mod, self.cap.dir):
            return False
        num_seq = self._getNumSSSeq(cards)
        max_move = self._getMaxMove(1)
        return num_seq <= max_move


# ************************************************************************
# * Relaxed Spider (the base of Spider and Scorpion; not a game by itself)
# ************************************************************************

class RelaxedSpider(Game):
    Layout_Method = staticmethod(Layout.klondikeLayout)
    Talon_Class = DealRowTalonStack
    Foundation_Class = Spider_SS_Foundation
    RowStack_Class = Spider_RowStack
    Hint_Class = Spider_Hint

    def createGame(self, **layout):
        # create layout
        l, s = Layout(self), self.s
        kwdefault(layout, rows=10, waste=0, texts=1, playcards=23)
        self.Layout_Method(l, **layout)
        # self.__class__.__dict__['Layout_Method'](l, **layout)
        # self.__class__.Layout_Method(l, **layout)
        self.setSize(l.size[0], l.size[1])
        # create stacks
        s.talon = self.Talon_Class(l.s.talon.x, l.s.talon.y, self)
        if l.s.waste:
            s.waste = WasteStack(l.s.waste.x, l.s.waste.y, self)
        for r in l.s.foundations:
            s.foundations.append(
                self.Foundation_Class(r.x, r.y, self, suit=ANY_SUIT))
        for r in l.s.rows:
            s.rows.append(self.RowStack_Class(r.x, r.y, self))
        # default
        l.defaultAll()

    def startGame(self, flip=0):
        for i in range(4):
            self.s.talon.dealRow(flip=flip, frames=0)
        r = self.s.rows
        rows = (r[0], r[3], r[6], r[9])
        self.s.talon.dealRow(rows=rows, flip=flip, frames=0)
        self._startAndDealRow()

    shallHighlightMatch = Game._shallHighlightMatch_RK
    getQuickPlayScore = Game._getSpiderQuickPlayScore


# ************************************************************************
# * Spider
# ************************************************************************

class Spider(RelaxedSpider):
    def canDealCards(self):
        if not RelaxedSpider.canDealCards(self):
            return False
        # no row may be empty
        for r in self.s.rows:
            if not r.cards:
                return False
        return True


class Spider1Suit(Spider):
    pass


class Spider2Suits(Spider):
    pass


# ************************************************************************
# * Scheidungsgrund (aka Grounds for a Divorce)
# ************************************************************************

class GroundsForADivorce_Talon(TalonStack):
    # A single click deals a new cards to each non-empty row.
    def dealCards(self, sound=True):
        if self.cards:
            rows = [r for r in self.game.s.rows if r.cards]
            if not rows:
                # deal one card to first row if all rows are emtpy
                rows = self.game.s.rows[:1]
            return self.dealRowAvail(rows=rows, sound=sound)
        return 0


class GroundsForADivorce(RelaxedSpider):
    Layout_Method = staticmethod(Layout.harpLayout)
    Talon_Class = GroundsForADivorce_Talon
    Foundation_Class = StackWrapper(
        Spider_SS_Foundation, base_rank=ANY_RANK, mod=13)
    RowStack_Class = StackWrapper(Spider_RowStack, mod=13)

    def createGame(self):
        RelaxedSpider.createGame(self, playcards=22)

    def startGame(self):
        self._startDealNumRowsAndDealSingleRow(4)

    shallHighlightMatch = Game._shallHighlightMatch_RKW


# ************************************************************************
# * Spiderette (Spider with one deck and 7 rows)
# ************************************************************************

class Spiderette(Spider):
    def createGame(self):
        Spider.createGame(self, rows=7, playcards=20)

    def startGame(self):
        for i in range(1, len(self.s.rows)):
            self.s.talon.dealRow(rows=self.s.rows[i:], flip=0, frames=0)
        self._startAndDealRow()


# ************************************************************************
# * Simple Simon
# ************************************************************************

class SimpleSimon(Spider):
    Talon_Class = InitialDealTalonStack
    RowStack_Class = SuperMoveSpider_RowStack
    Solver_Class = FreeCellSolverWrapper(preset='simple_simon', base_rank=0)

    def createGame(self):
        Spider.createGame(self, rows=10, texts=0)

    def startGame(self):
        for i in (9, 8, 7, 6, 5, 4, 3):
            self.s.talon.dealRow(rows=self.s.rows[:i], frames=0)
        self._startAndDealRow()


class SimpleSimonII(SimpleSimon):
    Solver_Class = None
    Foundation_Class = StackWrapper(Spider_SS_Foundation,
                                    base_rank=ANY_RANK, mod=13)
    RowStack_Class = StackWrapper(SuperMoveSpider_RowStack, mod=13)


# ************************************************************************
# * Scorpion - move cards like in Russian Solitaire
# ************************************************************************

class Scorpion_RowStack(Yukon_SS_RowStack, Spider_RowStack):
    canDropCards = Spider_RowStack.canDropCards
    canMoveCards = OpenStack.canMoveCards


class Scorpion(RelaxedSpider):
    Hint_Class = YukonType_Hint
    RowStack_Class = StackWrapper(Scorpion_RowStack, base_rank=KING)

    FACEDOWNS = (4, 4, 4, 0, 0, 0)

    def createGame(self):
        RelaxedSpider.createGame(self, rows=7, playcards=20)

    def startGame(self):
        for i in self.FACEDOWNS:
            self.s.talon.dealRow(rows=self.s.rows[:i], flip=0, frames=0)
            self.s.talon.dealRow(rows=self.s.rows[i:], flip=1, frames=0)
        self._startAndDealRow()

    shallHighlightMatch = Game._shallHighlightMatch_SS

    def getHighlightPilesStacks(self):
        return ()


class ScorpionTail_RowStack(Yukon_AC_RowStack, Spider_RowStack):
    canDropCards = Spider_RowStack.canDropCards
    canMoveCards = OpenStack.canMoveCards


# ************************************************************************
# * Wasp
# ************************************************************************

class Wasp(Scorpion):
    RowStack_Class = Scorpion_RowStack      # anything on an empty space


# ************************************************************************
# * Rouge et Noir
# ************************************************************************

class RougeEtNoir_RowStack(KingAC_RowStack):
    def canDropCards(self, stacks):
        if not self.cards:
            return (None, 0)
        for s in stacks:
            for cards in (self.cards[-1:], self.cards[-13:]):
                if s is not self and s.acceptsCards(self, cards):
                    return (s, len(cards))
        return (None, 0)


class RougeEtNoir(Game):
    Layout_Method = staticmethod(Layout.klondikeLayout)
    Talon_Class = DealRowTalonStack
    RowStack_Class = RougeEtNoir_RowStack

    def createGame(self, **layout):
        # create layout
        l, s = Layout(self), self.s
        kwdefault(layout, rows=10, waste=0, texts=1, playcards=23)
        self.Layout_Method(l, **layout)
        self.setSize(l.size[0], l.size[1])
        # create stacks
        s.talon = self.Talon_Class(l.s.talon.x, l.s.talon.y, self)
        if l.s.waste:
            s.waste = WasteStack(l.s.waste.x, l.s.waste.y, self)
        for i in range(4):
            r = l.s.foundations[i]
            s.foundations.append(
                AC_FoundationStack(r.x, r.y, self, suit=i, max_move=0))
        for i in range(4):
            r = l.s.foundations[i+4]
            s.foundations.append(Spider_AC_Foundation(r.x, r.y, self))
        for r in l.s.rows:
            s.rows.append(self.RowStack_Class(r.x, r.y, self))
        # default
        l.defaultAll()
        return l

    def startGame(self, flip=0, reverse=1):
        for i in range(3, len(self.s.rows)):
            self.s.talon.dealRow(
                rows=self.s.rows[:-i], flip=flip, frames=0, reverse=reverse)
        self.startDealSample()
        self.s.talon.dealRow(rows=self.s.rows[:-1], reverse=reverse)

    shallHighlightMatch = Game._shallHighlightMatch_AC


# ************************************************************************
# * Trillium
# ************************************************************************

class Trillium(Game):

    Hint_Class = Spider_Hint
    RowStack_Class = StackWrapper(AC_RowStack, base_rank=ANY_RANK)

    def createGame(self, rows=13):
        # create layout
        l, s = Layout(self), self.s

        # set window
        w, h = l.XM+rows*l.XS, l.YM+l.YS+24*l.YOFFSET
        self.setSize(w, h)

        # create stacks
        x, y = l.XM, l.YM
        for i in range(rows):
            s.rows.append(self.RowStack_Class(x, y, self))
            x += l.XS

        s.talon = DealRowTalonStack(l.XM+(rows-1)*l.XS//2, h-l.YS, self)
        l.createText(s.talon, "se")

        # define stack-groups
        l.defaultStackGroups()

    def startGame(self):
        self.s.talon.dealRow(frames=0, flip=0)
        self.s.talon.dealRow(frames=0)
        self.s.talon.dealRow(frames=0, flip=0)
        self._startAndDealRow()

    shallHighlightMatch = Game._shallHighlightMatch_AC

    def isGameWon(self):
        for s in self.s.rows:
            if s.cards:
                if len(s.cards) != 13 or not isAlternateColorSequence(s.cards):
                    return False
        return True


# ************************************************************************
# * Bebop
# ************************************************************************

class Bebop(Game):

    def createGame(self):
        l, s = Layout(self), self.s
        self.setSize(l.XM+10*l.XS, l.YM+2*l.YS+18*l.YOFFSET)

        x, y = l.XM+2*l.XS, l.YM
        for i in range(8):
            s.foundations.append(SS_FoundationStack(x, y, self, suit=i//2))
            x += l.XS
        x, y = l.XM+l.XS, l.YM+l.YS
        for i in range(8):
            s.rows.append(RK_RowStack(x, y, self))
            x += l.XS
        x, y = l.XM, l.YM
        s.talon = AutoDealTalonStack(x, y, self)
        l.createText(s.talon, 'ne')

        l.defaultStackGroups()

    def startGame(self):
        for i in range(len(self.s.rows)-1):
            self.s.talon.dealRow(frames=0, flip=0)
        self._startAndDealRow()

    def fillStack(self, stack):
        if stack in self.s.rows:
            if len(stack.cards) == len(self.s.rows)-1:
                for c in stack.cards:
                    if c.face_up:
                        return
                old_state = self.enterState(self.S_FILL)
                for s in self.s.rows:
                    if s is stack:
                        continue
                    stack.flipMove()
                    stack.moveMove(1, s, frames=4)
                for i in range(len(self.s.rows)-1):
                    if self.s.talon.cards:
                        self.s.talon.dealRow(rows=[stack], frames=4, flip=0)
                if self.s.talon.cards:
                    self.s.talon.dealRow(rows=[stack])
                self.leaveState(old_state)

    shallHighlightMatch = Game._shallHighlightMatch_RK


# ************************************************************************
# * Astrocyte
# ************************************************************************

class Astrocyte(Game):
    Hint_Class = Spider_Hint

    def createGame(self):

        # create layout
        l, s = Layout(self), self.s

        # set window
        self.setSize(l.XM + 14 * l.XS, l.YM + 2 * l.YS + 20 * l.YOFFSET)

        # create stacks
        x, y = l.XM + 1.5 * l.XS, l.YM
        for i in range(4):
            stack = ReserveStack(x, y, self, max_cards=1)
            s.reserves.append(stack)
            stack.CARD_YOFFSET = l.YOFFSET
            x += l.XS

        x, y = l.XM + 6 * l.XS, l.YM
        for i in range(8):
            s.foundations.append(Spider_SS_Foundation(x, y, self))
            x += l.XS

        x, y = l.XM + 3 * l.XS, l.YM + l.YS
        for i in range(8):
            s.rows.append(Spider_RowStack(x, y, self))
            x += l.XS

        x, y = l.XM, l.YM
        s.talon = DealRowTalonStack(x, y, self)
        l.createText(s.talon, "ne")

        # define stack-groups
        l.defaultStackGroups()

    def startGame(self):
        for i in range(7):
            self.s.talon.dealRow(flip=0, frames=0)
        self._startAndDealRow()


# register the game
registerGame(GameInfo(11, Spider, "Spider",
                      GI.GT_SPIDER, 2, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(14, GroundsForADivorce, "Grounds for a Divorce",
                      GI.GT_SPIDER, 2, 0, GI.SL_MOSTLY_SKILL,
                      altnames=('Scheidungsgrund',)))
registerGame(GameInfo(24, Spiderette, "Spiderette",
                      GI.GT_SPIDER, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(50, SimpleSimon, "Simple Simon",
                      GI.GT_SPIDER | GI.GT_OPEN, 1, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(29, Scorpion, "Scorpion",
                      GI.GT_SPIDER, 1, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(185, Wasp, "Wasp",
                      GI.GT_SPIDER, 1, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(220, RougeEtNoir, "Rouge et Noir",
                      GI.GT_GYPSY, 2, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(269, Spider1Suit, "Spider (1 Suit)",
                      GI.GT_SPIDER, 2, 0, GI.SL_MOSTLY_SKILL,
                      suits=(0, 0, 0, 0),
                      rules_filename="spider.html"))
registerGame(GameInfo(270, Spider2Suits, "Spider (2 Suits)",
                      GI.GT_SPIDER, 2, 0, GI.SL_MOSTLY_SKILL,
                      suits=(0, 0, 2, 2),
                      rules_filename="spider.html"))
registerGame(GameInfo(342, Trillium, "Trillium",
                      GI.GT_SPIDER, 2, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(710, Bebop, "Bebop",
                      GI.GT_2DECK_TYPE | GI.GT_ORIGINAL, 2, 0,
                      GI.SL_MOSTLY_SKILL))
# registerGame(GameInfo(000, SimpleSimonII, "Simple Simon II",
#                      GI.GT_SPIDER | GI.GT_OPEN, 1, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(917, Astrocyte, "Astrocyte",
                      GI.GT_SPIDER, 2, 0, GI.SL_MOSTLY_SKILL))
