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
from pysollib.hint import Yukon_Hint
from pysollib.layout import Layout
from pysollib.mfxutil import kwdefault
from pysollib.pysoltk import MfxCanvasText
from pysollib.stack import (
    DealRowTalonStack,
    InitialDealTalonStack,
    RedealTalonStack,
    ReserveStack,
    SS_FoundationStack,
    StackWrapper,
    WasteStack,
    WasteTalonStack,
    Yukon_AC_RowStack,
    Yukon_SS_RowStack,
)
from pysollib.util import ANY_SUIT, KING


# ************************************************************************
# * Yukon
# ************************************************************************

class Yukon(Game):
    Layout_Method = staticmethod(Layout.yukonLayout)
    Talon_Class = InitialDealTalonStack
    Foundation_Class = SS_FoundationStack
    RowStack_Class = StackWrapper(Yukon_AC_RowStack, base_rank=KING)
    Hint_Class = Yukon_Hint

    DIFF_SUITS = True

    def createGame(self, rows=7, **layout):
        # create layout
        l, s = Layout(self), self.s
        kwdefault(layout, rows=rows, texts=0, playcards=25)
        self.Layout_Method(l, **layout)
        self.setSize(l.size[0], l.size[1])
        # create stacks
        s.talon = self.Talon_Class(l.s.talon.x, l.s.talon.y, self)
        for r in l.s.foundations:
            if self.DIFF_SUITS:
                s.foundations.append(
                    self.Foundation_Class(
                        r.x, r.y, self, suit=r.suit, max_move=0))
            else:
                s.foundations.append(
                    self.Foundation_Class(
                        r.x, r.y, self, suit=ANY_SUIT, max_move=0))
        for r in l.s.rows:
            s.rows.append(self.RowStack_Class(r.x, r.y, self))
        # default
        l.defaultAll()
        return l

    def startGame(self):
        for i in range(1, len(self.s.rows)):
            self.s.talon.dealRow(rows=self.s.rows[i:], flip=0, frames=0)
        for i in range(4):
            self.s.talon.dealRow(rows=self.s.rows[1:], flip=1, frames=0)
        self._startAndDealRow()

    def getHighlightPilesStacks(self):
        return ()

    shallHighlightMatch = Game._shallHighlightMatch_AC


# ************************************************************************
# * Russian Solitaire (like Yukon, but build down by suit)
# ************************************************************************

class RussianSolitaire(Yukon):
    RowStack_Class = StackWrapper(Yukon_SS_RowStack, base_rank=KING)

    shallHighlightMatch = Game._shallHighlightMatch_SS


# ************************************************************************
# * Grandfather
# ************************************************************************

class Grandfather_Talon(RedealTalonStack):
    def dealCards(self, sound=False):
        self.redealCards(sound=sound, shuffle=True)


class Grandfather(RussianSolitaire):
    Talon_Class = StackWrapper(Grandfather_Talon, max_rounds=3)

    def createGame(self):
        layout = Yukon.createGame(self)
        layout.createRoundText(self.s.talon, 'nn')

    def startGame(self):
        frames = 0
        sound = False
        for i,  j in ((1, 7), (1, 6), (2, 6), (2, 5), (3, 5), (3, 4)):
            if len(self.s.talon.cards) <= j-i:
                frames = -1
                sound = True
                self.startDealSample()
            self.s.talon.dealRowAvail(rows=self.s.rows[i:j],
                                      flip=0, frames=frames)
        if not sound:
            self.startDealSample()
        self.s.talon.dealRowAvail()
        for i in range(4):
            self.s.talon.dealRowAvail(rows=self.s.rows[1:])

    redealCards = startGame


# ************************************************************************
# * Alaska (like Russian Solitaire, but build up or down in suit)
# ************************************************************************

class Alaska_RowStack(Yukon_SS_RowStack):
    def _isYukonSequence(self, c1, c2):
        return (c1.suit == c2.suit and
                ((c1.rank + self.cap.dir) % self.cap.mod == c2.rank or
                 (c2.rank + self.cap.dir) % self.cap.mod == c1.rank))

    def getHelp(self):
        return ('Tableau. Build up or down by suit, can move any face-up '
                'cards regardless of sequence.')


class Alaska(RussianSolitaire):
    RowStack_Class = StackWrapper(Alaska_RowStack, base_rank=KING)


# ************************************************************************
# * Chinese Discipline
# * Chinese Solitaire
# ************************************************************************

class ChineseDiscipline(Yukon):
    Layout_Method = staticmethod(Layout.klondikeLayout)
    Talon_Class = DealRowTalonStack

    def createGame(self):
        return Yukon.createGame(self, waste=0, texts=1)

    def startGame(self):
        for i in (3, 3, 3, 4, 5, 6):
            self.s.talon.dealRow(rows=self.s.rows[:i], flip=1, frames=0)
            self.s.talon.dealRow(rows=self.s.rows[i:], flip=0, frames=0)
        self._startAndDealRow()


class ChineseSolitaire(ChineseDiscipline):
    RowStack_Class = Yukon_AC_RowStack      # anything on an empty space


# ************************************************************************
# * Queenie
# ************************************************************************

class Queenie(Yukon):
    Layout_Method = staticmethod(Layout.klondikeLayout)
    Talon_Class = DealRowTalonStack

    def createGame(self):
        return Yukon.createGame(self, waste=0, texts=1)

    def startGame(self, flip=1, reverse=1):
        for i in range(1, len(self.s.rows)):
            self.s.talon.dealRow(
                rows=self.s.rows[i:], flip=flip, frames=0, reverse=reverse)
        self.startDealSample()
        self.s.talon.dealRow(reverse=reverse)


# ************************************************************************
# * Rushdike (like Queenie, but built down by suit)
# ************************************************************************

class Rushdike(RussianSolitaire):
    Layout_Method = staticmethod(Layout.klondikeLayout)
    Talon_Class = DealRowTalonStack

    def createGame(self):
        return RussianSolitaire.createGame(self, waste=0, texts=1)

    def startGame(self, flip=0, reverse=1):
        for i in range(1, len(self.s.rows)):
            self.s.talon.dealRow(
                rows=self.s.rows[i:], flip=flip, frames=0, reverse=reverse)
        self.startDealSample()
        self.s.talon.dealRow(reverse=reverse)


# ************************************************************************
# * Abacus
# ************************************************************************

class Abacus_Foundation(SS_FoundationStack):
    def __init__(self, x, y, game, suit, **cap):
        kwdefault(cap, base_rank=suit, mod=13, dir=suit+1, max_move=0)
        SS_FoundationStack.__init__(self, x, y, game, suit, **cap)


class Abacus_RowStack(Yukon_SS_RowStack):
    def _isYukonSequence(self, c1, c2):
        dir, mod = -(c1.suit + 1), 13
        return c1.suit == c2.suit and (c1.rank + dir) % mod == c2.rank


class Abacus(Rushdike):
    Foundation_Class = Abacus_Foundation
    RowStack_Class = Abacus_RowStack

    def createGame(self):
        layout = Rushdike.createGame(self)
        help = (('''\
Club:    A 2 3 4 5 6 7 8 9 T J Q K
Spade:   2 4 6 8 T Q A 3 5 7 9 J K
Heart:   3 6 9 Q 2 5 8 J A 4 7 T K
Diamond: 4 8 Q 3 7 J 2 6 T A 5 9 K'''))
        self.texts.help = MfxCanvasText(self.canvas,
                                        layout.XM, self.height - layout.YM,
                                        text=help,
                                        anchor="sw",
                                        font=self.app.getFont("canvas_fixed"))

    def _shuffleHook(self, cards):
        # move Twos to top of the Talon (i.e. first cards to be dealt)
        return self._shuffleHookMoveToTop(
            cards, lambda c: (c.id in (0, 14, 28, 42), c.suit))

    def startGame(self, flip=1, reverse=1):
        self.s.talon.dealRow(rows=self.s.foundations, frames=0)
        for i in range(1, len(self.s.rows)):
            self.s.talon.dealRow(
                rows=self.s.rows[i:], flip=flip, frames=0, reverse=reverse)
        self.startDealSample()
        self.s.talon.dealRow(reverse=reverse)

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        dir, mod = -(card1.suit + 1), 13
        return (card1.suit == card2.suit and
                ((card1.rank + dir) % mod == card2.rank or
                 (card2.rank + dir) % mod == card1.rank))


# ************************************************************************
# * Double Yukon
# * Double Russian Solitaire
# ************************************************************************

class DoubleYukon(Yukon):
    def createGame(self):
        Yukon.createGame(self, rows=10)

    def startGame(self):
        for i in range(1, len(self.s.rows)-1):
            self.s.talon.dealRow(rows=self.s.rows[i:], flip=0, frames=0)
        # self.s.talon.dealRow(rows=self.s.rows, flip=0, frames=0)
        for i in range(5):
            self.s.talon.dealRow(flip=1, frames=0)
        self._startAndDealRow()


class DoubleRussianSolitaire(DoubleYukon):
    RowStack_Class = StackWrapper(Yukon_SS_RowStack, base_rank=KING)

    shallHighlightMatch = Game._shallHighlightMatch_SS


# ************************************************************************
# * Triple Yukon
# * Triple Russian Solitaire
# ************************************************************************

class TripleYukon(Yukon):
    def createGame(self):
        Yukon.createGame(self, rows=13, playcards=34)

    def startGame(self):
        for i in range(1, len(self.s.rows)):
            self.s.talon.dealRow(rows=self.s.rows[i:], flip=0, frames=0)
        for i in range(5):
            self.s.talon.dealRow(rows=self.s.rows, flip=1, frames=0)
        self._startAndDealRow()


class TripleRussianSolitaire(TripleYukon):
    RowStack_Class = StackWrapper(Yukon_SS_RowStack, base_rank=KING)

    shallHighlightMatch = Game._shallHighlightMatch_SS


# ************************************************************************
# * Quadruple Yukon
# ************************************************************************

class QuadrupleYukon(Yukon):
    def createGame(self):
        Yukon.createGame(self, rows=16, playcards=34)

    def startGame(self):
        for i in range(1, len(self.s.rows)):
            self.s.talon.dealRow(rows=self.s.rows[i:], flip=0, frames=0)
        self.s.talon.dealRow(rows=self.s.rows[1:13], flip=1, frames=0)
        for i in range(4):
            self.s.talon.dealRow(rows=self.s.rows[1:], flip=1, frames=0)
        self._startAndDealRow()


# ************************************************************************
# * Australian Patience
# * Outback Patience
# * Raw Prawn
# ************************************************************************

class AustralianPatience(RussianSolitaire):

    RowStack_Class = StackWrapper(Yukon_SS_RowStack, base_rank=KING)

    def createGame(self, rows=7, max_rounds=1, num_deal=1, playcards=16):
        l, s = Layout(self), self.s
        Layout.klondikeLayout(l, rows=rows, waste=1, playcards=playcards)
        self.setSize(l.size[0], l.size[1])
        s.talon = WasteTalonStack(l.s.talon.x, l.s.talon.y, self,
                                  max_rounds=max_rounds, num_deal=num_deal)
        s.waste = WasteStack(l.s.waste.x, l.s.waste.y, self)
        for r in l.s.foundations:
            s.foundations.append(
                SS_FoundationStack(r.x, r.y, self, suit=r.suit))
        for r in l.s.rows:
            s.rows.append(self.RowStack_Class(r.x, r.y, self))
        l.defaultAll()

    def startGame(self):
        self._startDealNumRowsAndDealRowAndCards(3)


class OutbackPatience(AustralianPatience):
    def createGame(self):
        AustralianPatience.createGame(self, rows=8, playcards=25)

    def startGame(self):
        self._startDealNumRowsAndDealRowAndCards(6)


class RawPrawn(AustralianPatience):
    RowStack_Class = Yukon_SS_RowStack


# ************************************************************************
# * Geoffrey
# ************************************************************************

class Geoffrey(Yukon):
    Layout_Method = staticmethod(Layout.klondikeLayout)
    RowStack_Class = StackWrapper(Yukon_SS_RowStack, base_rank=KING)

    def createGame(self):
        Yukon.createGame(self, rows=8, waste=0)

    def startGame(self):
        for i in (4, 4, 4, 4, 8):
            self.s.talon.dealRow(rows=self.s.rows[:i], flip=1, frames=0)
            self.s.talon.dealRow(rows=self.s.rows[i:], flip=0, frames=0)
        self.startDealSample()
        self.s.talon.dealRow()
        self.s.talon.dealRow(rows=self.s.rows[:4])

    shallHighlightMatch = Game._shallHighlightMatch_SS


# ************************************************************************
# * Brisbane
# ************************************************************************

class Brisbane_RowStack(Yukon_AC_RowStack):
    def _isYukonSequence(self, c1, c2):
        return (c1.rank + self.cap.dir) % self.cap.mod == c2.rank

    def getHelp(self):
        return ('Tableau. Build down regardless of suit, can move any '
                'face-up cards regardless of sequence.')


class Brisbane(Yukon):
    RowStack_Class = Brisbane_RowStack

    def startGame(self):
        for i in range(1, len(self.s.rows)):
            self.s.talon.dealRow(rows=self.s.rows[i:], flip=0, frames=0)
        self._startDealNumRows(3)
        self.s.talon.dealRow()
        self.s.talon.dealRowAvail()

    def getHighlightPilesStacks(self):
        return ()

    shallHighlightMatch = Game._shallHighlightMatch_RK


# ************************************************************************
# * Wave
# ************************************************************************

class WaveTalon(DealRowTalonStack):
    def dealCards(self, sound=False):
        if sound and self.game.app.opt.animations:
            self.game.startDealSample()
        n = self.dealRowAvail(flip=0, sound=False)
        n += self.dealRowAvail(sound=False)
        if sound:
            self.game.stopSamples()
        return n


class Wave(Game):
    Hint_Class = Yukon_Hint

    def createGame(self, rows=8):
        l, s = Layout(self), self.s
        l.klondikeLayout(rows=rows, waste=0, playcards=25)
        self.setSize(l.size[0], l.size[1])
        s.talon = WaveTalon(l.s.talon.x, l.s.talon.y, self)
        for r in l.s.foundations:
            s.foundations.append(SS_FoundationStack(r.x, r.y, self,
                                                    suit=r.suit))
        for r in l.s.rows:
            s.rows.append(Yukon_AC_RowStack(r.x, r.y, self))
        l.defaultAll()

    def startGame(self):
        self.s.talon.dealRow(frames=0)
        self.s.talon.dealRow(frames=0, flip=0)
        self._startAndDealRow()

    shallHighlightMatch = Game._shallHighlightMatch_AC


# ************************************************************************
# * Yukon Cells
# * Russian Cell
# ************************************************************************

class YukonCells(Yukon):
    Reserve_Stack = ReserveStack

    RESERVES = 2
    RESERVE_TEXT = False

    def createGame(self):
        # create layout
        l, s = Layout(self), self.s

        ROWS = 7

        # set size so that at least 2//3 of a card is visible with 20 cards
        h = l.CH * 2 // 27 * l.YOFFSET
        h = l.YM + max(h, 5 * l.YS)

        # create rows
        x, y = l.XM, l.YM

        w1, w2 = (7 * (l.XS + l.XM)), (2 * l.XS)
        if w2 + 13 * l.XOFFSET > w1:
            l.XOFFSET = int((w1 - w2) / 13)

        x2 = x * 3
        for i in range(self.RESERVES):
            reserve = self.Reserve_Stack(x2, y, self)
            reserve.CARD_XOFFSET = l.XOFFSET
            if self.RESERVE_TEXT:
                l.createText(reserve, "sw")
            s.reserves.append(reserve)
            x2 += l.XS

        y += l.YS
        for i in range(ROWS):
            self.s.rows.append(self.RowStack_Class(x, y, self))
            x += l.XS

        # Don't know why this is necessary for the Yukon layout.
        # But we should probably figure out how to get this to work
        # like other games.
        self.setRegion(self.s.rows + self.s.reserves,
                       (-999, -999, x - l.CW // 2, 999999))

        # create foundations
        y = l.YM
        for suit in range(4):
            self.s.foundations.append(self.Foundation_Class(
                x, y, self, suit=suit, max_move=0))
            y += l.YS

        x, y = l.XM, h - l.YS
        self.s.talon = self.Talon_Class(x, y, self)

        # set window
        self.setSize(l.XM + 8 * l.XS, h)
        l.defaultAll()


class RussianCell(YukonCells):
    RowStack_Class = StackWrapper(Yukon_SS_RowStack, base_rank=KING)

    shallHighlightMatch = Game._shallHighlightMatch_SS


# register the game
registerGame(GameInfo(19, Yukon, "Yukon",
                      GI.GT_YUKON, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(20, RussianSolitaire, "Russian Solitaire",
                      GI.GT_YUKON, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(186, Alaska, "Alaska",
                      GI.GT_YUKON, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(187, ChineseDiscipline, "Chinese Discipline",
                      GI.GT_YUKON | GI.GT_XORIGINAL, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(188, ChineseSolitaire, "Chinese Solitaire",
                      GI.GT_YUKON | GI.GT_XORIGINAL, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(189, Queenie, "Queenie",
                      GI.GT_YUKON | GI.GT_XORIGINAL, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(190, Rushdike, "Rushdike",
                      GI.GT_YUKON | GI.GT_XORIGINAL, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(192, Abacus, "Abacus",
                      GI.GT_YUKON | GI.GT_XORIGINAL, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(271, DoubleYukon, "Double Yukon",
                      GI.GT_YUKON, 2, 0, GI.SL_BALANCED))
registerGame(GameInfo(272, TripleYukon, "Triple Yukon",
                      GI.GT_YUKON, 3, 0, GI.SL_BALANCED))
registerGame(GameInfo(447, AustralianPatience, "Australian Patience",
                      GI.GT_YUKON, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(450, RawPrawn, "Raw Prawn",
                      GI.GT_YUKON, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(466, DoubleRussianSolitaire, "Double Russian Solitaire",
                      GI.GT_YUKON, 2, 0, GI.SL_BALANCED))
registerGame(GameInfo(488, TripleRussianSolitaire, "Triple Russian Solitaire",
                      GI.GT_YUKON, 3, 0, GI.SL_BALANCED))
registerGame(GameInfo(492, Geoffrey, "Geoffrey",
                      GI.GT_YUKON, 1, 0, GI.SL_MOSTLY_SKILL,
                      altnames=('Thornq',)))
registerGame(GameInfo(526, OutbackPatience, "Outback Patience",
                      GI.GT_YUKON, 2, 0, GI.SL_BALANCED))
registerGame(GameInfo(603, Brisbane, "Brisbane",
                      GI.GT_YUKON, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(925, YukonCells, "Yukon Cells",
                      GI.GT_YUKON, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(942, QuadrupleYukon, "Quadruple Yukon",
                      GI.GT_YUKON, 4, 0, GI.SL_BALANCED))
registerGame(GameInfo(964, RussianCell, "Russian Cell",
                      GI.GT_YUKON, 1, 0, GI.SL_BALANCED,
                      altnames=('Finnish Solitaire',)))
