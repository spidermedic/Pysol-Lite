#!/usr/bin/env python
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
from pysollib.layout import Layout
from pysollib.stack import \
    BasicRowStack, \
    DealRowTalonStack, \
    InitialDealTalonStack, \
    OpenStack, \
    RK_FoundationStack, \
    ReserveStack, \
    SS_FoundationStack, \
    WasteStack, \
    WasteTalonStack
from pysollib.util import ACE, ANY_SUIT, JACK, KING, QUEEN


# ************************************************************************
# * Sultan
# ************************************************************************

class Sultan(Game):

    #
    # game layout
    #

    def createGame(self, reserves=6):
        # create layout
        l, s = Layout(self), self.s

        # set window
        w, h = 3 * l.XM + 5 * l.XS, l.YM + 4 * l.YS + \
            (2 * l.TEXT_HEIGHT) + l.TEXT_MARGIN
        self.setSize(w, h)

        # create stacks
        lay = ((0, 0, 0, 1, 13),
               (2, 0, 0, 1, 13),
               (0, 1, 1, 1, 13),
               (2, 1, 1, 1, 13),
               (1, 1, 2, 0, 1),
               (1, 2, 2, 1, 13),
               (0, 2, 3, 1, 13),
               (2, 2, 3, 1, 13),
               (1, 0, 2, 1, 12),
               )
        for i, j, suit, max_accept, max_cards in lay:
            x, y = 2*l.XM+l.XS+i*l.XS, l.YM+j*l.YS
            stack = SS_FoundationStack(
                x, y, self, suit=suit,
                max_move=0, max_accept=max_accept, max_cards=max_cards, mod=13)
            s.foundations.append(stack)

        x, y = l.XM, l.YM
        for i in range(reserves//2):
            s.rows.append(ReserveStack(x, y, self))
            y += l.YS

        x, y = 3*l.XM+4*l.XS, l.YM
        for i in range(reserves//2):
            s.rows.append(ReserveStack(x, y, self))
            y += l.YS

        x, y = 2*l.XM+1.5*l.XS, l.YM+3*l.YS + l.TEXT_HEIGHT
        s.talon = WasteTalonStack(x, y, self, max_rounds=3)
        l.createText(s.talon, "s")
        l.createRoundText(self.s.talon, 'n')
        x += l.XS
        s.waste = WasteStack(x, y, self)
        l.createText(s.waste, "s")

        # define stack-groups
        l.defaultStackGroups()

    #
    # game overrides
    #

    def _shuffleHook(self, cards):
        cards = self._shuffleHookMoveToTop(
            cards,
            lambda c: (c.rank == ACE and c.suit == 2 and c.deck == 0, c.suit))
        cards = self._shuffleHookMoveToTop(
            cards,
            lambda c: (c.rank == KING, c.suit))
        return cards

    def startGame(self):
        self.s.talon.dealRow(rows=self.s.foundations, frames=0)
        self._startAndDealRowAndCards()

    def getAutoStacks(self, event=None):
        return (self.sg.dropstacks, (), self.sg.dropstacks)


# ************************************************************************
# * Lady of the Manor
# ************************************************************************

class LadyOfTheManor_RowStack(BasicRowStack):
    clickHandler = BasicRowStack.doubleclickHandler


class LadyOfTheManor_Reserve(OpenStack):
    clickHandler = OpenStack.doubleclickHandler


class LadyOfTheManor(Game):
    Foundation_Class_1 = RK_FoundationStack
    Foundation_Class_2 = RK_FoundationStack

    Talon_Class = InitialDealTalonStack

    ACE_STACK = False

    def createGame(self):

        l, s = Layout(self), self.s
        cols = 8
        if self.ACE_STACK:
            cols += 1
        self.setSize(l.XM + cols * l.XS,
                     l.YM + max(4 * l.YS, 3 * l.YS + 14 * l.YOFFSET))

        x, y = l.XM, self.height-l.YS
        for i in range(4):
            suit = i
            if self.Foundation_Class_1 is RK_FoundationStack:
                suit = ANY_SUIT
            s.foundations.append(
                self.Foundation_Class_1(x, y, self, suit=suit))
            x += l.XS
        for i in range(4):
            suit = i
            if self.Foundation_Class_1 is RK_FoundationStack:
                suit = ANY_SUIT
            s.foundations.append(
                self.Foundation_Class_2(x, y, self, suit=suit))
            x += l.XS
        x, y = l.XM + 2 * l.XS, l.YM + l.YS
        if self.ACE_STACK:
            x += (l.XS / 2)
        for i in range(4):
            s.rows.append(LadyOfTheManor_RowStack(x, y, self, max_accept=0))
            x += l.XS
        if self.ACE_STACK:
            reservelocs = ((0, 2), (0, 1), (0, 0),
                           (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0),
                           (7, 0), (8, 0), (8, 1), (8, 2), )
        else:
            reservelocs = ((0, 2), (0, 1), (0, 0),
                           (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0),
                           (7, 0), (7, 1), (7, 2),)

        for i, j in reservelocs:
            x, y = l.XM+i*l.XS, l.YM+j*l.YS
            s.reserves.append(LadyOfTheManor_Reserve(x, y, self, max_accept=0))

        s.talon = self.Talon_Class(
            self.width-l.XS, self.height-l.YS, self)

        l.defaultAll()

    def _shuffleHook(self, cards):
        # move Aces to top of the Talon (i.e. first cards to be dealt)
        return self._shuffleHookMoveToTop(
            cards,
            lambda c: (c.rank == ACE, c.suit))

    def startGame(self, flip=False):
        self.s.talon.dealRow(rows=self.s.foundations, frames=0)
        for _ in range(11):
            self.s.talon.dealRow(frames=0, flip=flip)
        self.s.talon.dealRow(frames=0)
        self.startDealSample()
        while self.s.talon.cards:
            self.flipMove(self.s.talon)
            c = self.s.talon.cards[-1]
            if self.ACE_STACK:
                r = self.s.reserves[c.rank]
            else:
                r = self.s.reserves[c.rank - 1]
            self.moveMove(1, self.s.talon, r, frames=4)


# ************************************************************************
# * Matrimony
# ************************************************************************

class Matrimony_Talon(DealRowTalonStack):

    def canDealCards(self):
        if self.round == self.max_rounds and not self.cards:
            return False
        return not self.game.isGameWon()

    def _redeal(self):
        num_cards = 0
        assert len(self.cards) == 0
        r = self.game.s.rows[-self.round]
        for _ in range(len(r.cards)):
            num_cards += 1
            self.game.moveMove(1, r, self, frames=4)
            self.game.flipMove(self)
        assert len(self.cards) == num_cards
        self.game.nextRoundMove(self)
        return num_cards

    def dealCards(self, sound=False):
        if sound:
            self.game.startDealSample()
        num_cards = 0
        if len(self.cards) == 0:
            num_cards += self._redeal()
        if self.round == 1:
            num_cards += self.dealRowAvail(sound=False)
        else:
            rows = self.game.s.rows[-self.round+1:]
            num_cards += self.dealRowAvail(rows=rows, sound=False)
            while self.cards:
                num_cards += self.dealRowAvail(
                    rows=self.game.s.rows, sound=False)
        if sound:
            self.game.stopSamples()
        return num_cards


class Matrimony(Game):

    def createGame(self):

        l, s = Layout(self), self.s
        self.setSize(l.XM+8*l.XS, l.YM+4*l.YS)

        s.talon = Matrimony_Talon(l.XM, l.YM, self, max_rounds=17)
        l.createText(s.talon, 'se')
        l.createRoundText(s.talon, 'ne')

        x, y = l.XM+2*l.XS, l.YM
        for i in range(4):
            s.foundations.append(SS_FoundationStack(x, y, self, suit=i,
                                 base_rank=JACK, dir=-1, mod=13))
            x += l.XS
        x, y = l.XM+2*l.XS, l.YM+l.YS
        for i in range(4):
            s.foundations.append(SS_FoundationStack(x, y, self, suit=i,
                                 base_rank=QUEEN, dir=1, mod=13))
            x += l.XS
        y = l.YM+2*l.YS
        for i in range(2):
            x = l.XM
            for _ in range(8):
                stack = LadyOfTheManor_RowStack(x, y, self, max_accept=0)
                stack.CARD_XOFFSET, stack.CARD_YOFFSET = 0, 0
                s.rows.append(stack)
                x += l.XS
            y += l.YS

        l.defaultStackGroups()

    def _shuffleHook(self, cards):
        return self._shuffleHookMoveToTop(
            cards,
            lambda c: (c.rank in (JACK, QUEEN) and c.deck == 0 and c.suit == 3,
                       (c.rank, c.suit)))

    def startGame(self):
        self.s.talon.dealRow(rows=[self.s.foundations[3],
                                   self.s.foundations[7]], frames=0)
        self._startAndDealRow()

    def getSnapshotHash(self):
        # Takes the round into account - a single card redeal can result
        # in an identical snapshot.
        return Game.getSnapshotHash(self) + str(self.s.talon.round)


# register the game
registerGame(GameInfo(330, Sultan, "Sultan",
                      GI.GT_MISC_TYPE, 2, 2, GI.SL_MOSTLY_LUCK,
                      altnames=("Sultan of Turkey",
                                "Emperor of Germany")))
registerGame(GameInfo(423, LadyOfTheManor, "Lady of the Manor",
                      GI.GT_MISC_TYPE, 2, 0, GI.SL_MOSTLY_LUCK,
                      altnames=("Vassal", "La Chatelaine")))
registerGame(GameInfo(424, Matrimony, "Matrimony",
                      GI.GT_MISC_TYPE, 2, 16, GI.SL_MOSTLY_LUCK))
