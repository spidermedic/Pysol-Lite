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
from pysollib.hint import CautiousDefaultHint
from pysollib.layout import Layout
from pysollib.stack import \
    BasicRowStack, \
    InitialDealTalonStack, \
    StackWrapper, \
    isRankSequence, \
    isSameSuitSequence
from pysollib.util import KING, UNLIMITED_ACCEPTS, UNLIMITED_MOVES

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
        return isSameSuitSequence(cards) or isRankSequence(cards, direction=0)

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
        for _ in range(rows):
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


# register the game
registerGame(GameInfo(294, CurdsAndWhey, "Curds and Whey",
                      GI.GT_SPIDER | GI.GT_OPEN, 1, 0, GI.SL_MOSTLY_SKILL))
