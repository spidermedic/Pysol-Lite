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
from pysollib.hint import CautiousDefaultHint
from pysollib.hint import FreeCellSolverWrapper
from pysollib.layout import Layout
from pysollib.mfxutil import kwdefault
from pysollib.pysoltk import MfxCanvasText
from pysollib.stack import (
    InitialDealTalonStack,
    ReserveStack,
    SS_FoundationStack,
    StackWrapper,
    SuperMoveRK_RowStack,
    UD_SS_RowStack,
    WasteStack,
)
from pysollib.util import ANY_RANK, RANKS


class BeleagueredCastleType_Hint(CautiousDefaultHint):
    # FIXME: demo is not too clever in this game
    pass


# ************************************************************************
# * Streets and Alleys
# ************************************************************************

class StreetsAndAlleys(Game):
    Hint_Class = BeleagueredCastleType_Hint
    Solver_Class = FreeCellSolverWrapper(preset='streets_and_alleys')

    Foundation_Class = SS_FoundationStack
    # RowStack_Class = RK_RowStack
    RowStack_Class = SuperMoveRK_RowStack

    #
    # game layout
    #

    def createGame(self, playcards=13, reserves=0, texts=False):
        # create layout
        l, s = Layout(self), self.s

        # set window
        # (set size so that at least 13 cards are fully playable)
        w = max(3*l.XS, l.XS+(playcards-1)*l.XOFFSET)
        x0 = l.XM
        x1 = x0 + w + 2*l.XM
        x2 = x1 + l.XS + 2*l.XM
        x3 = x2 + w + l.XM
        h = l.YM + (4+int(reserves != 0))*l.YS + int(texts)*l.TEXT_HEIGHT
        self.setSize(x3, h)

        # create stacks
        y = l.YM
        if reserves:
            x = x1 - int(l.XS*(reserves-1)/2)
            for i in range(reserves):
                s.reserves.append(ReserveStack(x, y, self))
                x += l.XS
            y += l.YS
        x = x1
        for i in range(4):
            s.foundations.append(
                self.Foundation_Class(x, y, self, suit=i, max_move=0))
            y += l.YS
        if texts:
            tx, ty, ta, tf = l.getTextAttr(None, "ss")
            tx, ty = x+tx, y-l.YS+ty
            font = self.app.getFont("canvas_default")
            self.texts.info = MfxCanvasText(self.canvas, tx, ty,
                                            anchor=ta, font=font)
        for x in (x0, x2):
            y = l.YM+l.YS*int(reserves != 0)
            for i in range(4):
                stack = self.RowStack_Class(x, y, self)
                stack.CARD_XOFFSET, stack.CARD_YOFFSET = l.XOFFSET, 0
                s.rows.append(stack)
                y += l.YS
        x, y = self.width - l.XS, self.height - l.YS
        s.talon = InitialDealTalonStack(x, y, self)
        if reserves:
            l.setRegion(
                s.rows[:4], (-999, l.YM+l.YS-l.CH//2, x1-l.CW//2, 999999))
        else:
            l.setRegion(s.rows[:4], (-999, -999, x1-l.CW//2, 999999))

        # default
        l.defaultAll()

    #
    # game overrides
    #

    def startGame(self):
        self._startDealNumRows(4)
        for i in range(3):
            self.s.talon.dealRowAvail()

    shallHighlightMatch = Game._shallHighlightMatch_RK


# ************************************************************************
# * Beleaguered Castle
# ************************************************************************

class BeleagueredCastle(StreetsAndAlleys):
    def _shuffleHook(self, cards):
        # move Aces to bottom of the Talon (i.e. last cards to be dealt)
        return self._shuffleHookMoveToBottom(
            cards, lambda c: (c.rank == 0, c.suit))

    def startGame(self):
        self._startDealNumRows(4)
        for i in range(2):
            self.s.talon.dealRow()
        self.s.talon.dealRow(rows=self.s.foundations)


# ************************************************************************
# * Citadel
# ************************************************************************

class Citadel(StreetsAndAlleys):
    def _shuffleHook(self, cards):
        # move Aces to top of the Talon (i.e. first cards to be dealt)
        return self._shuffleHookMoveToTop(
            cards, lambda c: (c.rank == 0, c.suit))

    # move cards to the Foundations during dealing
    def startGame(self):
        frames = 4
        talon = self.s.talon
        self.startDealSample()
        talon.dealRow(rows=self.s.foundations, frames=frames)
        while talon.cards:
            for r in self.s.rows:
                self.flipMove(talon)
                for s in self.s.foundations:
                    if s.acceptsCards(self, talon.cards[-1:]):
                        self.moveMove(1, talon, s, frames=frames)
                        break
                else:
                    self.moveMove(1, talon, r, frames=frames)
                if not talon.cards:
                    break


# ************************************************************************
# * Fortress
# ************************************************************************

class Fortress(Game):
    Layout_Method = staticmethod(Layout.klondikeLayout)
    Talon_Class = InitialDealTalonStack
    Foundation_Class = SS_FoundationStack
    RowStack_Class = UD_SS_RowStack
    Hint_Class = BeleagueredCastleType_Hint

    #
    # game layout
    #

    def createGame(self, **layout):
        # create layout
        l, s = Layout(self), self.s
        kwdefault(layout, rows=10, waste=0, texts=0, playcards=16)
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
        return l

    #
    # game overrides
    #

    def startGame(self):
        self._startDealNumRows(3)
        for i in range(3):
            self.s.talon.dealRowAvail()

    shallHighlightMatch = Game._shallHighlightMatch_SSW


# ************************************************************************
# * Bastion
# ************************************************************************

class Bastion(Game):
    Layout_Method = staticmethod(Layout.freeCellLayout)
    Talon_Class = InitialDealTalonStack
    Foundation_Class = SS_FoundationStack
    RowStack_Class = UD_SS_RowStack
    ReserveStack_Class = ReserveStack
    Hint_Class = BeleagueredCastleType_Hint

    #
    # game layout
    #

    def createGame(self, **layout):
        # create layout
        l, s = Layout(self), self.s
        kwdefault(layout, rows=10, reserves=2, texts=0, playcards=16)
        self.Layout_Method(l, **layout)
        self.setSize(l.size[0], l.size[1])
        # create stacks
        s.talon = self.Talon_Class(l.s.talon.x, l.s.talon.y, self)
        for r in l.s.foundations:
            s.foundations.append(
                self.Foundation_Class(r.x, r.y, self, suit=r.suit))
        for r in l.s.rows:
            s.rows.append(self.RowStack_Class(r.x, r.y, self))
        for r in l.s.reserves:
            s.reserves.append(self.ReserveStack_Class(r.x, r.y, self))
        # default
        l.defaultAll()
        return l

    #
    # game overrides
    #

    def startGame(self):
        self._startDealNumRows(3)
        for i in range(2):
            self.s.talon.dealRow()
        self.s.talon.dealRow(rows=self.s.reserves)

    shallHighlightMatch = Game._shallHighlightMatch_SS


# ************************************************************************
# * Chessboard
# ************************************************************************

class Chessboard_Foundation(SS_FoundationStack):
    def __init__(self, x, y, game, suit, **cap):
        kwdefault(cap, mod=13, min_cards=1, max_move=0, base_rank=ANY_RANK)
        SS_FoundationStack.__init__(self, x, y, game, suit, **cap)

    def acceptsCards(self, from_stack, cards):
        if not SS_FoundationStack.acceptsCards(self, from_stack, cards):
            return False
        if not self.cards:
            for s in self.game.s.foundations:
                if s.cards:
                    return cards[0].rank == s.cards[0].rank
        return True


class Chessboard_RowStack(UD_SS_RowStack):
    def canDropCards(self, stacks):
        if self.game.demo:
            return UD_SS_RowStack.canDropCards(self, stacks)
        for s in self.game.s.foundations:
            if s.cards:
                return UD_SS_RowStack.canDropCards(self, stacks)
        return (None, 0)


class Chessboard(Fortress):
    Foundation_Class = Chessboard_Foundation
    RowStack_Class = StackWrapper(Chessboard_RowStack, mod=13)

    def createGame(self):
        lay = Fortress.createGame(self)
        tx, ty, ta, tf = lay.getTextAttr(self.s.foundations[-1], "e")
        font = self.app.getFont("canvas_default")
        self.texts.info = MfxCanvasText(
            self.canvas, tx + lay.XM, ty, anchor=ta, font=font)

    def updateText(self):
        if self.preview > 1:
            return
        t = ""
        for s in self.s.foundations:
            if s.cards:
                t = RANKS[s.cards[0].rank]
                break
        self.texts.info.config(text=t)


# register the game
registerGame(GameInfo(146, StreetsAndAlleys, "Streets and Alleys",
                      GI.GT_BELEAGUERED_CASTLE | GI.GT_OPEN, 1, 0,
                      GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(34, BeleagueredCastle, "Beleaguered Castle",
                      GI.GT_BELEAGUERED_CASTLE | GI.GT_OPEN, 1, 0,
                      GI.SL_MOSTLY_SKILL,
                      altnames=("Laying Siege", "Sham Battle",)))
registerGame(GameInfo(145, Citadel, "Citadel",
                      GI.GT_BELEAGUERED_CASTLE | GI.GT_OPEN, 1, 0,
                      GI.SL_MOSTLY_SKILL, altnames=('Under Siege',)))
registerGame(GameInfo(147, Fortress, "Fortress",
                      GI.GT_BELEAGUERED_CASTLE | GI.GT_OPEN, 1, 0,
                      GI.SL_SKILL))
registerGame(GameInfo(148, Chessboard, "Chessboard",
                      GI.GT_BELEAGUERED_CASTLE | GI.GT_OPEN, 1, 0,
                      GI.SL_SKILL))
registerGame(GameInfo(324, Bastion, "Bastion",
                      GI.GT_BELEAGUERED_CASTLE | GI.GT_OPEN, 1, 0,
                      GI.SL_MOSTLY_SKILL))
