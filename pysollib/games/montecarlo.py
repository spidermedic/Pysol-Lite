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

import math

from pysollib.game import Game
from pysollib.gamedb import GI, GameInfo, registerGame
from pysollib.hint import DefaultHint
from pysollib.layout import Layout
from pysollib.stack import (
    AbstractFoundationStack,
    AutoDealTalonStack,
    BasicRowStack,
    InitialDealTalonStack,
    OpenStack,
    StackWrapper,
    TalonStack,
)
from pysollib.util import ANY_RANK, ANY_SUIT, JACK, KING, NO_RANK, QUEEN

# ************************************************************************
# *
# ************************************************************************


class MonteCarlo_Hint(DefaultHint):
    # FIXME: demo is not too clever in this game
    pass


# ************************************************************************
# * Monte Carlo
# * Monte Carlo (2 Decks)
# ************************************************************************

class MonteCarlo_Talon(TalonStack):
    def canDealCards(self):
        free = 0
        for r in self.game.s.rows:
            if not r.cards:
                free = 1
            elif free:
                return True
        return free and len(self.cards)

    def dealCards(self, sound=False):
        self.game.updateStackMove(self.game.s.talon, 2 | 16)  # for undo
        n = self.game.fillEmptyStacks()
        self.game.updateStackMove(self.game.s.talon, 1 | 16)  # for redo
        return n


class MonteCarlo_RowStack(BasicRowStack):
    def acceptsCards(self, from_stack, cards):
        if not OpenStack.acceptsCards(self, from_stack, cards):
            return False
        # check the rank
        if self.cards[-1].rank != cards[0].rank:
            return False
        # now look if the stacks are neighbours
        return self.game.isNeighbour(from_stack, self)

    def moveMove(self, ncards, to_stack, frames=-1, shadow=-1):
        assert ncards == 1 and to_stack in self.game.s.rows
        if to_stack.cards:
            self._dropPairMove(ncards, to_stack, frames=-1, shadow=shadow)
        else:
            BasicRowStack.moveMove(
                self, ncards, to_stack, frames=frames, shadow=shadow)

    def _dropPairMove(self, n, other_stack, frames=-1, shadow=-1):
        game = self.game
        old_state = game.enterState(game.S_FILL)
        f = game.s.foundations[0]
        game.updateStackMove(game.s.talon, 2 | 16)            # for undo
        if not game.demo:
            game.playSample("droppair", priority=200)
        game.moveMove(n, self, f, frames=frames, shadow=shadow)
        game.moveMove(n, other_stack, f, frames=frames, shadow=shadow)
        self.fillStack()
        other_stack.fillStack()
        if self.game.FILL_STACKS_AFTER_DROP:
            game.fillEmptyStacks()
        game.updateStackMove(game.s.talon, 1 | 16)            # for redo
        game.leaveState(old_state)


class MonteCarlo(Game):
    Talon_Class = MonteCarlo_Talon
    Foundation_Class = StackWrapper(
        AbstractFoundationStack, max_accept=0)
    RowStack_Class = MonteCarlo_RowStack
    Hint_Class = MonteCarlo_Hint

    FILL_STACKS_AFTER_DROP = False
    FILL_STACKS_BEFORE_SHIFT = False

    #
    # game layout
    #

    def createGame(self, rows=5, cols=5):
        # create layout
        l, s = Layout(self), self.s

        # set window
        self.setSize(l.XM + (cols+1.5)*l.XS, l.YM + rows*l.YS)

        # create stacks
        for i in range(rows):
            for j in range(cols):
                x, y = l.XM + j*l.XS, l.YM + i*l.YS
                s.rows.append(self.RowStack_Class(x, y, self,
                                                  max_accept=1, max_cards=2,
                                                  dir=0, base_rank=NO_RANK))
        x, y = self.width - l.XS, l.YM
        s.foundations.append(self.Foundation_Class(x, y, self, suit=ANY_SUIT,
                             max_move=0, base_rank=ANY_RANK,
                             max_cards=self.gameinfo.ncards))
        l.createText(s.foundations[0], "s")
        y += 2*l.YS
        s.talon = self.Talon_Class(x, y, self, max_rounds=1)
        l.createText(s.talon, "s", text_format="%D")

        # define stack-groups
        l.defaultStackGroups()

    #
    # game overrides
    #

    def startGame(self):
        self._startAndDealRow()

    def getAutoStacks(self, event=None):
        return ((), (), self.sg.dropstacks)

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return card1.rank == card2.rank

    #
    # game extras
    #

    def isNeighbour(self, stack1, stack2):
        if not (0 <= stack1.id <= 24 and 0 <= stack2.id <= 24):
            return False
        column = stack2.id % 5
        diff = stack1.id - stack2.id
        if column == 0:
            return diff in (-5, -4, 1, 5, 6)
        if column == 4:
            return diff in (-6, -5, -1, 4, 5)
        return diff in (-6, -5, -4, -1, 1, 4, 5, 6)

    def fillEmptyStacks(self):
        n = 0
        self.startDealSample()
        free = self.shiftCards()
        remcards = free > len(self.s.talon.cards) > 0
        if free > 0:
            for r in self.s.rows:
                if not r.cards:
                    if not self.s.talon.cards:
                        break
                    self.flipMove(self.s.talon)
                    self.moveMove(1, self.s.talon, r)
                    n += 1
        if remcards and self.FILL_STACKS_BEFORE_SHIFT:
            self.shiftCards()
        self.stopSamples()
        return n + free

    def shiftCards(self):
        free = 0
        for r in self.s.rows:
            assert len(r.cards) <= 1
            if not r.cards:
                free += 1
            elif free > 0 and (not self.FILL_STACKS_BEFORE_SHIFT
                               or not self.s.talon.cards):
                to_stack = self.allstacks[r.id - free]
                self.moveMove(1, r, to_stack, frames=4, shadow=0)
        return free


# ************************************************************************
# * Simple Pairs
# ************************************************************************

class SimplePairs(MonteCarlo):
    def createGame(self):
        # create layout
        l, s = Layout(self), self.s

        # set window
        self.setSize(l.XM + 6*l.XS, l.YM + 4*l.YS)

        # create stacks
        for i in range(3):
            for j in range(3):
                x, y = l.XM + (2*j+3)*l.XS//2, l.YM + (2*i+1)*l.YS//2
                s.rows.append(self.RowStack_Class(x, y, self,
                                                  max_accept=1, max_cards=2,
                                                  dir=0, base_rank=NO_RANK))
        x, y = l.XM, l.YM + 3*l.YS//2
        s.talon = AutoDealTalonStack(x, y, self, max_rounds=1)
        l.createText(s.talon, "s")
        x = x + 5*l.XS
        s.foundations.append(self.Foundation_Class(x, y, self, suit=ANY_SUIT,
                             max_move=0, max_cards=52, base_rank=ANY_RANK))
        l.createText(s.foundations[0], "s")

        # define stack-groups
        l.defaultStackGroups()

    def fillStack(self, stack):
        if stack in self.s.rows:
            if len(stack.cards) == 0 and len(self.s.talon.cards) > 0:
                self.flipMove(self.s.talon)
                self.moveMove(1, self.s.talon, stack)

    def isNeighbour(self, stack1, stack2):
        return 0 <= stack1.id <= 15 and 0 <= stack2.id <= 15


# ************************************************************************
# * Block Ten
# ************************************************************************

class BlockTen_RowStack(MonteCarlo_RowStack):
    def acceptsCards(self, from_stack, cards):
        if not OpenStack.acceptsCards(self, from_stack, cards):
            return False
        # check the rank
        if self.cards[-1].rank + cards[0].rank + 2 == 10:
            return True
        if self.cards[-1].rank > 9 and self.cards[-1].rank == cards[0].rank:
            return True

        return False


class BlockTen(SimplePairs):
    RowStack_Class = BlockTen_RowStack

    def isGameWon(self):
        return len(self.s.foundations[0].cards) == 48

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return (card1.rank + card2.rank == 8 or
                (9 < card1.rank == card2.rank > 9))


PICTURE_DESTS = {
    KING: (1, 2, 13, 14),
    QUEEN: (4, 7, 8, 11),
    JACK: (0, 3, 12, 15),
}


# ************************************************************************
# * Fourteen
# ************************************************************************

class Fourteen_RowStack(MonteCarlo_RowStack):
    def acceptsCards(self, from_stack, cards):
        if not OpenStack.acceptsCards(self, from_stack, cards):
            return False
        # check the rank
        return self.cards[-1].rank + cards[0].rank == 12


class Fourteen(Game):
    Foundation_Class = StackWrapper(AbstractFoundationStack, max_accept=0)
    RowStack_Class = Fourteen_RowStack

    FILL_STACKS_AFTER_DROP = False

    #
    # game layout
    #

    def createGame(self, colsperrow=6):
        # create layout
        l, s = Layout(self), self.s

        # set window
        self.setSize(l.XM + (colsperrow + 1) * l.XS, l.YM + 5 * l.YS)

        # create stacks
        for i in (0, 2.5):
            for j in range(colsperrow):
                x, y = l.XM + j*l.XS, l.YM + i*l.YS
                s.rows.append(self.RowStack_Class(x, y, self,
                                                  max_move=1, max_accept=1,
                                                  dir=0, base_rank=NO_RANK))
        x, y = l.XM + colsperrow * l.XS, l.YM
        s.foundations.append(self.Foundation_Class(x, y, self, suit=ANY_SUIT,
                             max_move=0, max_cards=(52 * self.gameinfo.decks),
                                                   base_rank=ANY_RANK))
        l.createText(s.foundations[0], "s")
        x, y = self.width - l.XS, self.height - l.YS
        s.talon = InitialDealTalonStack(x, y, self)

        # define stack-groups
        l.defaultStackGroups()

    #
    # game overrides
    #

    def startGame(self):
        self._startDealNumRows(3)
        self.s.talon.dealRow()
        self.s.talon.dealRow(rows=self.s.rows[:4])

    def getAutoStacks(self, event=None):
        return ((), (), self.sg.dropstacks)

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return card1.rank + card2.rank == 12


# ************************************************************************
# * Nestor
# ************************************************************************

class Nestor_RowStack(MonteCarlo_RowStack):
    def acceptsCards(self, from_stack, cards):
        if not OpenStack.acceptsCards(self, from_stack, cards):
            return False
        # check the rank
        return self.cards[-1].rank == cards[0].rank


class Nestor(Game):
    Foundation_Class = StackWrapper(AbstractFoundationStack, max_accept=0)
    RowStack_Class = Nestor_RowStack

    FILL_STACKS_AFTER_DROP = False

    COLS = 8
    COLCARDS = 6

    #
    # game layout
    #

    def createGame(self):
        # create layout
        l, s = Layout(self), self.s

        # set window
        self.setSize(l.XM + self.COLS * l.XS,
                     l.YM + 2 * l.YS + (self.COLCARDS + 6) * l.YOFFSET)

        # create stacks
        x, y = l.XM, l.YM
        for i in range(self.COLS):
            s.rows.append(self.RowStack_Class(x, y, self,
                                              max_move=1, max_accept=1,
                                              dir=0, base_rank=NO_RANK))
            x += l.XS
        x, y = l.XM + ((self.COLS / 2) - 2) * l.XS, self.height-l.YS
        for i in range(4):
            s.rows.append(self.RowStack_Class(x, y, self,
                                              max_move=1, max_accept=1,
                                              dir=0, base_rank=NO_RANK))
            x += l.XS
        x, y = self.width-l.XS, self.height-l.YS
        s.foundations.append(self.Foundation_Class(x, y, self, suit=ANY_SUIT,
                             max_move=0, max_cards=(52 * self.gameinfo.decks),
                                                   base_rank=ANY_RANK))
        l.createText(s.foundations[0], "n")
        x, y = l.XM, self.height - l.YS
        s.talon = InitialDealTalonStack(x, y, self)

        # define stack-groups
        l.defaultStackGroups()

    #
    # game overrides
    #

    def _checkRow(self, cards):
        first_index = {}
        for ind, card in enumerate(cards):
            if card.rank in first_index:
                return first_index[card.rank]
            first_index[card.rank] = ind
        return -1

    def _shuffleHook(self, cards):
        # no row will have two cards of the same rank
        for i in range(self.COLS):
            for t in range(1000):  # just in case
                j = self._checkRow(cards[i * self.COLCARDS:(i + 1)
                                   * self.COLCARDS])
                if j < 0:
                    break
                j += i * self.COLCARDS
                k = self.random.choice(list(range((i+1) * self.COLCARDS,
                                                  (52 * self.gameinfo.decks))))
                cards[j], cards[k] = cards[k], cards[j]
        cards.reverse()
        return cards

    def startGame(self):
        for r in self.s.rows[:self.COLS]:
            for j in range(self.COLCARDS):
                self.s.talon.dealRow(rows=[r], frames=0)
        self.startDealSample()
        self.s.talon.dealRow(rows=self.s.rows[self.COLS:])

    def getAutoStacks(self, event=None):
        return ((), (), self.sg.dropstacks)

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return card1.rank == card2.rank


# ************************************************************************
# * Vertical
# ************************************************************************

class Vertical(Nestor):

    def createGame(self):
        # create layout
        l, s = Layout(self), self.s

        # set window
        self.setSize(l.XM+9*l.XS, l.YM+2*l.YS+12*l.YOFFSET)

        # create stacks
        x, y = l.XM, l.YM
        for i in range(7):
            s.rows.append(self.RowStack_Class(x, y, self,
                                              max_move=1, max_accept=1,
                                              dir=0, base_rank=NO_RANK))
            x += l.XS
        x, y = l.XM, self.height-l.YS
        for i in range(9):
            s.rows.append(self.RowStack_Class(x, y, self,
                                              max_move=1, max_accept=1,
                                              dir=0, base_rank=NO_RANK))
            x += l.XS
        x, y = self.width-l.XS, l.YM
        s.foundations.append(self.Foundation_Class(x, y, self, suit=ANY_SUIT,
                             max_move=0, max_cards=52, base_rank=ANY_RANK))
        l.createText(s.foundations[0], "s")
        x -= l.XS
        s.talon = InitialDealTalonStack(x, y, self)

        # define stack-groups
        l.defaultStackGroups()

    def startGame(self):
        self.s.talon.dealRow(frames=0)
        for i in range(4):
            self.s.talon.dealRow(rows=self.s.rows[:7], frames=0)
        self.startDealSample()
        self.s.talon.dealRow(rows=self.s.rows[:7])
        self.s.talon.dealRow(rows=[self.s.rows[3]])


# ************************************************************************
# * The Wish
# ************************************************************************

class TheWish(Game):

    FILL_STACKS_AFTER_DROP = False
    ROWS = 8

    def createGame(self):
        # create layout
        l, s = Layout(self), self.s

        # set window
        self.setSize(l.XM + ((self.ROWS / 2) + 2) * l.XS,
                     2 * l.YM + 2 * l.YS + 6 * l.YOFFSET)

        currentrow = 0
        # create stacks
        for i in range(2):
            for j in range(math.ceil(self.ROWS / 2)):
                if currentrow < self.ROWS:
                    x, y = l.XM + j*l.XS, l.YM+i*(l.YM+l.YS+3*l.YOFFSET)
                    s.rows.append(Nestor_RowStack(x, y, self,
                                                  max_move=1, max_accept=1,
                                                  dir=0, base_rank=NO_RANK))
                    currentrow += 1

        x, y = self.width - l.XS, l.YM
        s.talon = InitialDealTalonStack(x, y, self)

        x, y = self.width - l.XS, self.height - l.YS
        s.foundations.append(
            AbstractFoundationStack(
                x, y, self, suit=ANY_SUIT,
                max_move=0, max_cards=32, max_accept=0, base_rank=ANY_RANK))
        l.createText(s.foundations[0], "n")

        # define stack-groups
        l.defaultStackGroups()

    #
    # game overrides
    #

    def startGame(self):
        for i in range(3):
            self.s.talon.dealRow(flip=0, frames=0)
        self._startAndDealRow()

    def fillStack(self, stack):
        if stack.cards:
            self.flipMove(stack)

    def getAutoStacks(self, event=None):
        return ((), (), self.sg.dropstacks)

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return card1.rank == card2.rank


# ************************************************************************
# * Aces Square
# ************************************************************************

class AcesSquare_RowStack(MonteCarlo_RowStack):
    def acceptsCards(self, from_stack, cards):
        if not OpenStack.acceptsCards(self, from_stack, cards):
            return False
        if self.cards[-1].rank == 0 or cards[0].rank == 0:
            return False

        return (self.game.isNeighbour(from_stack, self)
                and self.cards[-1].suit == cards[0].suit)


class AcesSquare(MonteCarlo):
    Talon_Class = AutoDealTalonStack
    RowStack_Class = AcesSquare_RowStack

    def createGame(self):
        MonteCarlo.createGame(self, rows=4, cols=4)

    def isGameWon(self):
        return len(self.s.foundations[0].cards) == 48

    def fillStack(self, stack):
        if stack in self.s.rows:
            if len(stack.cards) == 0 and len(self.s.talon.cards) > 0:
                self.flipMove(self.s.talon)
                self.moveMove(1, self.s.talon, stack)

    def isNeighbour(self, stack1, stack2):
        return (stack1.id // 4 == stack2.id // 4 or
                stack1.id % 4 == stack2.id % 4)

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return (card1.suit == card2.suit and
                card1.rank != card2.rank != 0)


# register the game
registerGame(GameInfo(89, MonteCarlo, "Monte Carlo",
                      GI.GT_PAIRING_TYPE, 1, 0, GI.SL_MOSTLY_LUCK,
                      altnames=("Quilt",)))
registerGame(GameInfo(91, SimplePairs, "Simple Pairs",
                      GI.GT_PAIRING_TYPE | GI.GT_CHILDREN, 1, 0,
                      GI.SL_LUCK, altnames=("Jamestown", "Pirate Gold",
                                            "Treasure Hunt", "Hunter")))
registerGame(GameInfo(96, Fourteen, "Fourteen",
                      GI.GT_PAIRING_TYPE | GI.GT_OPEN | GI.GT_CHILDREN, 1, 0,
                      GI.SL_MOSTLY_LUCK, altnames=("Fourteen Out",
                                                   "Fourteen Puzzle",
                                                   "Take Fourteen")))
registerGame(GameInfo(235, Nestor, "Nestor",
                      GI.GT_PAIRING_TYPE | GI.GT_OPEN, 1, 0,
                      GI.SL_MOSTLY_LUCK))
registerGame(GameInfo(328, TheWish, "The Wish",
                      GI.GT_PAIRING_TYPE | GI.GT_STRIPPED | GI.GT_CHILDREN,
                      1, 0, GI.SL_MOSTLY_LUCK,
                      ranks=(0, 6, 7, 8, 9, 10, 11, 12)))
registerGame(GameInfo(368, Vertical, "Vertical",
                      GI.GT_PAIRING_TYPE | GI.GT_OPEN, 1, 0,
                      GI.SL_MOSTLY_LUCK))
registerGame(GameInfo(829, BlockTen, "Block Ten",
                      GI.GT_PAIRING_TYPE, 1, 0, GI.SL_LUCK))
registerGame(GameInfo(898, AcesSquare, "Aces Square",
                      GI.GT_1DECK_TYPE, 1, 0, GI.SL_BALANCED,
                      altnames=("Miner",)))
