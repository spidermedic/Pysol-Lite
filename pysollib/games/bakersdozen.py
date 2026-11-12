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
from pysollib.hint import CautiousDefaultHint
from pysollib.hint import FreeCellSolverWrapper
from pysollib.layout import Layout
from pysollib.mfxutil import kwdefault
from pysollib.stack import (
    AC_FoundationStack,
    AC_RowStack,
    InitialDealTalonStack,
    InvisibleStack,
    RK_RowStack,
    SS_FoundationStack,
    SS_RowStack,
    StackWrapper,
    SuperMoveAC_RowStack,
    TalonStack,
)
from pysollib.util import KING, NO_RANK, UNLIMITED_ACCEPTS, UNLIMITED_MOVES


# ************************************************************************
# * Castles in Spain
# ************************************************************************

class CastlesInSpain(Game):
    Layout_Method = staticmethod(Layout.bakersDozenLayout)
    Talon_Class = InitialDealTalonStack
    Foundation_Class = SS_FoundationStack
    RowStack_Class = SuperMoveAC_RowStack
    Hint_Class = CautiousDefaultHint
    Solver_Class = FreeCellSolverWrapper()

    GAME_VERSION = 2

    #
    # game layout
    #

    def createGame(self, **layout):
        # create layout
        l, s = Layout(self), self.s
        kwdefault(layout, rows=13, playcards=9)
        self.Layout_Method(l, **layout)
        self.setSize(l.size[0], l.size[1])
        # create stacks
        s.talon = self.Talon_Class(l.s.talon.x, l.s.talon.y, self)
        for r in l.s.foundations:
            s.foundations.append(
                self.Foundation_Class(r.x, r.y, self, suit=r.suit))
        for r in l.s.rows:
            s.rows.append(self.RowStack_Class(r.x, r.y, self))
        # default
        self.s.internals.append(InvisibleStack(self))
        l.defaultAll()
        return l

    def startGame(self, flip=(0, 0, 0)):
        for f in flip:
            self.s.talon.dealRow(flip=f, frames=0)
        self._startAndDealRow()

    shallHighlightMatch = Game._shallHighlightMatch_AC


# ************************************************************************
# * Martha
# ************************************************************************

class Martha_RowStack(AC_RowStack):
    def acceptsCards(self, from_stack, cards):
        if not AC_RowStack.acceptsCards(self, from_stack, cards):
            return False
        # when empty, only accept a single card
        return self.cards or len(cards) == 1


class Martha(CastlesInSpain):
    Solver_Class = None
    RowStack_Class = Martha_RowStack

    def createGame(self):
        CastlesInSpain.createGame(self, rows=12, playcards=13)

    def _shuffleHook(self, cards):
        # move Aces to bottom of the Talon (i.e. last cards to be dealt)
        return self._shuffleHookMoveToBottom(
            cards, lambda c: (c.rank == 0, c.suit))

    def startGame(self):
        CastlesInSpain.startGame(self, flip=(0, 1, 0))
        self.s.talon.dealRow(rows=self.s.foundations)


# ************************************************************************
# * Baker's Dozen
# ************************************************************************

class BakersDozen(CastlesInSpain):
    RowStack_Class = StackWrapper(RK_RowStack, max_move=1, max_accept=1,
                                  base_rank=NO_RANK)
    Solver_Class = FreeCellSolverWrapper(preset='bakers_dozen')

    def _shuffleHook(self, cards):
        # move Kings to bottom of each stack
        i, n = 0, len(self.s.rows)
        kings = []
        for c in cards:
            if c.rank == KING:
                kings.append(i)
            i = i + 1
        for i in kings:
            j = i % n
            while j < i:
                if cards[j].rank != KING:
                    cards[i], cards[j] = cards[j], cards[i]
                    break
                j = j + n
        cards.reverse()
        return cards

    def startGame(self):
        CastlesInSpain.startGame(self, flip=(1, 1, 1))

    shallHighlightMatch = Game._shallHighlightMatch_RK


# ************************************************************************
# * Spanish Patience
# ************************************************************************

class SpanishPatience(BakersDozen):
    Foundation_Class = AC_FoundationStack
    Solver_Class = None


# ************************************************************************
# * Cruel
# ************************************************************************

class Cruel_Talon(TalonStack):
    def canDealCards(self):
        # FIXME: this is to avoid loops in the demo
        # if self.game.demo and self.game.moves.index >= 100:
        #    return False
        if self.round == self.max_rounds:
            return False
        return not self.game.isGameWon()

    def dealCards(self, sound=False):
        lr = len(self.game.s.rows)
        # move all cards to the Talon and redeal (no shuffling)
        num_cards = 0
        assert len(self.cards) == 0
        rows = list(self.game.s.rows)[:]
        # rows.reverse()
        for r in rows:
            for i in range(len(r.cards)):
                num_cards = num_cards + 1
                self.game.moveMove(1, r, self.game.s.internals[0], frames=0)

        if len(self.game.s.internals[0].cards) % 4 != 0:
            self.game.moveMove(len(self.game.s.internals[0].cards) % 4,
                               self.game.s.internals[0], self, frames=0)

        while len(self.game.s.internals[0].cards) > 0:
            self.game.moveMove(4, self.game.s.internals[0], self, frames=0)

        assert len(self.cards) == num_cards

        if num_cards == 0:          # game already finished
            return 0

        # redeal in packs of 4 cards
        self.game.nextRoundMove(self)
        n, i = num_cards, 0
        deal = [4] * lr
        extra_cards = n - 4 * lr
        while extra_cards > 0:
            # note: this can only happen in Tarock games like Nasty
            deal[i] = deal[i] + 1
            i = (i + 1) % lr
            extra_cards = extra_cards - 1
        # print n, deal
        self.game.startDealSample()
        for i in range(lr):
            k = min(deal[i], n)
            frames = (0, 4)[n <= 3*4]
            for j in range(k):
                self.game.moveMove(1, self, self.game.s.rows[i], frames=frames)
            n = n - k
            if n == 0:
                break
        # done
        self.game.stopSamples()
        assert n == len(self.cards) == 0
        return num_cards


class Cruel(CastlesInSpain):
    Talon_Class = StackWrapper(Cruel_Talon, max_rounds=-1)
    RowStack_Class = StackWrapper(SS_RowStack,
                                  max_move=1, max_accept=1, base_rank=NO_RANK)

    # Solver_Class = FreeCellSolverWrapper(preset='cruel')
    Solver_Class = None

    def createGame(self):
        return CastlesInSpain.createGame(self, rows=12)

    def _shuffleHook(self, cards):
        # move Aces to bottom of the Talon (i.e. last cards to be dealt)
        return self._shuffleHookMoveToBottom(
            cards, lambda c: (c.rank == 0, c.suit))

    def startGame(self):
        CastlesInSpain.startGame(self, flip=(1, 1, 1))
        self.s.talon.dealRow(rows=self.s.foundations)

    shallHighlightMatch = Game._shallHighlightMatch_SS


# ************************************************************************
# * Perseverance
# ************************************************************************

class Perseverance(Cruel, BakersDozen):
    Talon_Class = StackWrapper(Cruel_Talon, max_rounds=3)
    RowStack_Class = StackWrapper(SS_RowStack, base_rank=NO_RANK, dir=-1,
                                  max_move=UNLIMITED_MOVES,
                                  max_accept=UNLIMITED_ACCEPTS)
    Solver_Class = None

    def createGame(self):
        lay = Cruel.createGame(self)
        lay.createRoundText(self.s.talon, 'sw')

    def _shuffleHook(self, cards):
        # move Kings to bottom of each stack (???)
        # cards = BakersDozen._shuffleHook(self, cards)
        # move Aces to bottom of the Talon (i.e. last cards to be dealt)
        cards = Cruel._shuffleHook(self, cards)
        return cards

#      def dealCards(self, sound=True):
#          Cruel.dealCards(self, sound)


# register the game
registerGame(GameInfo(83, CastlesInSpain, "Castles in Spain",
                      GI.GT_BAKERS_DOZEN, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(84, Martha, "Martha",
                      GI.GT_BAKERS_DOZEN, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(31, BakersDozen, "Baker's Dozen",
                      GI.GT_BAKERS_DOZEN | GI.GT_OPEN, 1, 0,
                      GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(85, SpanishPatience, "Spanish Patience",
                      GI.GT_BAKERS_DOZEN | GI.GT_OPEN, 1, 0,
                      GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(104, Cruel, "Cruel",
                      GI.GT_BAKERS_DOZEN | GI.GT_OPEN, 1, -1, GI.SL_BALANCED))
registerGame(GameInfo(404, Perseverance, "Perseverance",
                      GI.GT_BAKERS_DOZEN | GI.GT_OPEN, 1, 2, GI.SL_BALANCED))
