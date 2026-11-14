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
from pysollib.hint import CautiousDefaultHint, DefaultHint
from pysollib.layout import Layout
from pysollib.pysoltk import MfxCanvasText
from pysollib.stack import (
    AbstractFoundationStack,
    BasicRowStack,
    InitialDealTalonStack,
    OpenStack,
    RK_FoundationStack,
    RK_RowStack,
    SC_FoundationStack,
    SS_FoundationStack,
    Stack,
    StackWrapper,
    WasteStack,
    WasteTalonStack,
)
from pysollib.util import ANY_SUIT, KING, UNLIMITED_CARDS


class Numerica_Hint(DefaultHint):
    # FIXME: demo is clueless

    # def _getDropCardScore(self, score, color, r, t, ncards):
    # FIXME: implement this method

    def _getMoveWasteScore(self, score, color, r, t, pile, rpile):
        assert r in (self.game.s.waste, self.game.s.talon) and len(pile) == 1
        score = self._computeScore(r, t)
        return score, color

    def _computeScore(self, r, t):
        score = 30000
        if len(t.cards) == 0:
            score = score - (KING - r.cards[0].rank) * 1000
        elif t.cards[-1].rank < r.cards[0].rank:
            # FIXME: add intelligence here
            score = 10000 + t.cards[-1].rank - len(t.cards)
        elif t.cards[-1].rank == r.cards[0].rank:
            score = 20000
        else:
            score = score - (t.cards[-1].rank - r.cards[0].rank) * 1000
        return score


# ************************************************************************
# *
# ************************************************************************

class Numerica_RowStack(BasicRowStack):
    def acceptsCards(self, from_stack, cards):
        if not BasicRowStack.acceptsCards(self, from_stack, cards):
            return False
        # this stack accepts any one card from the Waste pile
        return from_stack is self.game.s.waste and len(cards) == 1

    getBottomImage = Stack._getReserveBottomImage

    def getHelp(self):
        # return _('Tableau. Accepts any one card from the Waste.')
        return 'Tableau. Build regardless of rank and suit.'


# ************************************************************************
# * Numerica
# ************************************************************************

class Numerica(Game):
    Hint_Class = Numerica_Hint
    Foundation_Class = StackWrapper(RK_FoundationStack, suit=ANY_SUIT)
    RowStack_Class = StackWrapper(Numerica_RowStack, max_accept=1)

    #
    # game layout
    #

    def createGame(self, rows=4, reserve=False, max_rounds=1,
                   waste_max_cards=1):
        # create layout
        l, s = Layout(self), self.s
        decks = self.gameinfo.decks
        foundations = 4*decks

        # set window
        # (piles up to 20 cards are playable in default window size)
        h = max(2.5 * l.YS, 20 * l.YOFFSET)
        max_rows = max(rows, foundations)
        self.setSize(l.XM + (1.5 + max_rows) * l.XS + l.XM, l.YM + l.YS + h)

        # create stacks
        x0 = l.XM + l.XS * 3 // 2
        if decks == 1:
            x = x0 + (rows-4)*l.XS//2
        else:
            x = x0
        y = l.YM
        for i in range(foundations):
            s.foundations.append(self.Foundation_Class(x, y, self, suit=i))
            x = x + l.XS
        x, y = x0, l.YM + l.YS
        for i in range(rows):
            s.rows.append(self.RowStack_Class(x, y, self))
            x = x + l.XS
        self.setRegion(s.rows, (x0-l.XS//2, y-l.CH//2, 999999, 999999))
        x, y = l.XM, l.YM+l.YS+l.YS//2*int(reserve)
        s.talon = WasteTalonStack(x, y, self, max_rounds=max_rounds)
        if reserve or waste_max_cards > 1:
            l.createText(s.talon, 'ne')
        else:
            l.createText(s.talon, 'n')
        y = y + l.YS
        s.waste = WasteStack(x, y, self, max_cards=waste_max_cards)
        if waste_max_cards > 1:
            l.createText(s.waste, 'ne')
        if reserve:
            s.reserves.append(self.ReserveStack_Class(l.XM, l.YM, self))

        # define stack-groups
        l.defaultStackGroups()

        return l

    #
    # game overrides
    #

    def startGame(self):
        self.startDealSample()
        self.s.talon.dealCards()          # deal first card to WasteStack

    shallHighlightMatch = Game._shallHighlightMatch_SS

    def getHighlightPilesStacks(self):
        return ()


# ************************************************************************
# * Lady Betty
# * Colours
# ************************************************************************

class LadyBetty(Numerica):
    Foundation_Class = SS_FoundationStack

    def createGame(self):
        Numerica.createGame(self, rows=6)


class Colours(LadyBetty):
    Foundation_Class = StackWrapper(SC_FoundationStack, mod=13, suit=ANY_SUIT)

    def startGame(self):
        self.startDealSample()
        self.s.talon.dealRow(rows=self.s.foundations)
        self.s.talon.dealCards()          # deal first card to WasteStack

    def _shuffleHook(self, cards):
        # prepare first cards
        topcards = [None] * 4
        evencolor = -1
        oddcolor = -1
        for c in cards[:]:
            if 0 < c.rank <= 4 and topcards[c.rank - 1] is None:
                if c.rank % 2 == 0:
                    if evencolor != -1 and c.color != evencolor:
                        continue
                    if oddcolor != -1 and c.color == oddcolor:
                        continue
                    evencolor = c.color
                elif c.rank % 2 == 1:
                    if oddcolor != -1 and c.color != oddcolor:
                        continue
                    if evencolor != -1 and c.color == evencolor:
                        continue
                    oddcolor = c.color

                topcards[c.rank - 1] = c
                cards.remove(c)
        topcards.reverse()
        return cards + topcards


# ************************************************************************
# * Assembly
# ************************************************************************

class Assembly_RowStack(RK_RowStack):
    def acceptsCards(self, from_stack, cards):
        if not RK_RowStack.acceptsCards(self, from_stack, cards):
            return False
        if not self.cards:
            return from_stack is self.game.s.waste
        return True


class Assembly(Numerica):
    Hint_Class = CautiousDefaultHint

    Foundation_Class = StackWrapper(RK_FoundationStack, suit=ANY_SUIT)
    RowStack_Class = StackWrapper(Assembly_RowStack, max_move=1)

    def createGame(self):
        Numerica.createGame(self, waste_max_cards=UNLIMITED_CARDS)

    def startGame(self):
        self.startDealSample()
        self.s.talon.dealRow()
        self.s.talon.dealCards()

    shallHighlightMatch = Game._shallHighlightMatch_RK


# ************************************************************************
# * Ladybug
# ************************************************************************

class Ladybug_RowStack(Numerica_RowStack):
    def acceptsCards(self, from_stack, cards):
        return Numerica_RowStack.acceptsCards(self, from_stack, cards) \
               and self.game.isValidPlay(self.id, cards[0].rank)


class Ladybug_Talon(WasteTalonStack):
    def canDealCards(self):
        if not self.game.used and len(self.game.s.waste.cards) > 0:
            return False
        return WasteTalonStack.canDealCards(self)

    def dealCards(self, sound=False):
        game = self.game
        old_state = game.enterState(game.S_FILL)
        game.saveStateMove(2 | 16)  # for undo
        game.used = False
        game.saveStateMove(1 | 16)  # for redo
        game.leaveState(old_state)
        return WasteTalonStack.dealCards(self, sound)


class Ladybug_Waste(WasteStack):
    def moveMove(self, ncards, to_stack, frames=-1, shadow=-1):
        game = self.game
        if to_stack in game.s.rows:
            old_state = game.enterState(game.S_FILL)
            game.saveStateMove(2 | 16)  # for undo
            game.used = True
            game.saveStateMove(1 | 16)  # for redo
            game.leaveState(old_state)
        WasteStack.moveMove(self, ncards, to_stack, frames, shadow)
        game.s.talon.updateText(self)


class Ladybug(Game):
    used = False

    def createGame(self, rows=7):
        self.used = False
        # create layout
        l, s = Layout(self), self.s

        # set window
        # (piles up to 4 cards are playable in default window size)
        h = max(2 * l.YS, (4 * l.YOFFSET) + l.TEXT_HEIGHT)
        self.setSize(l.XM + (1.5 + rows) * l.XS + l.XM, l.YM + h)

        # create stacks
        x0 = l.XM + (l.XS * 1.5)
        x = x0
        y = l.YM + l.TEXT_HEIGHT

        font = self.app.getFont("canvas_default")
        for i in range(rows):
            stack = Ladybug_RowStack(x, y, self, max_cards=4,
                                     max_accept=1, max_move=0)
            if self.preview <= 1:
                tx, ty, ta, tf = l.getTextAttr(stack, anchor="n")
                stack.texts.misc = MfxCanvasText(self.canvas,
                                                 tx, ty,
                                                 anchor=ta,
                                                 font=font)
            s.rows.append(stack)
            x = x + l.XS
        self.setRegion(s.rows, (x0-l.XS//2, y-l.CH//2, 999999, 999999))
        x, y = l.XM, l.YM
        s.talon = Ladybug_Talon(x, y, self, max_rounds=-2, num_deal=3)
        l.createText(s.talon, 'ne')
        y = y + l.YS
        s.waste = Ladybug_Waste(x, y, self)
        l.createText(s.waste, 'ne')

        # define stack-groups
        l.defaultStackGroups()

        return l

    def isValidPlay(self, row, playRank):
        total = self.getTotal(self.s.rows[row], playRank)

        if total > 10:
            return False
        if total < 10 and len(self.s.rows[row].cards) == 3:
            return False
        return True

    def getTotal(self, row, extraRank=-1):
        cards = row.cards
        total = 0
        hasTen = False

        for card in cards:
            if card.rank < 9:
                total += card.rank + 1
            elif card.rank == 9:
                hasTen = True

        if extraRank > -1:
            if extraRank < 9:
                total += extraRank + 1
            elif extraRank == 9:
                hasTen = True

        if hasTen and total < 10:
            return 10

        return total

    #
    # game overrides
    #

    def startGame(self):
        self.startDealSample()
        self.s.talon.dealRow(rows=self.s.rows)
        self.s.talon.dealCards()

    shallHighlightMatch = Game._shallHighlightMatch_SS

    def updateText(self):
        if self.preview > 1:
            return
        for row in self.s.rows:
            row.texts.misc.config(text=str(self.getTotal(row)))

    def isGameWon(self):
        for row in self.s.rows:
            if len(row.cards) != 4:
                return False
        return True

    def _restoreGameHook(self, game):
        self.used = game.loadinfo.used

    def _loadGameHook(self, p):
        self.loadinfo.addattr(used=p.load())

    def _saveGameHook(self, p):
        p.dump(self.used)

    def getHighlightPilesStacks(self):
        return ()

    def setState(self, state):
        # restore saved vars (from undo/redo)
        self.used = state[0]

    def getState(self):
        # save vars (for undo/redo)
        return [self.used]


# ************************************************************************
# * Ninety-One
# ************************************************************************

class NinetyOne_RowStack(OpenStack):

    def moveMove(self, ncards, to_stack, frames=-1, shadow=-1):
        OpenStack.moveMove(self, ncards, to_stack, frames=frames,
                           shadow=shadow)
        if to_stack in self.game.s.rows:
            self.game.checkTotal()


class NinetyOne(Game):
    Hint_Class = None

    def createGame(self):
        # create layout
        l, s = Layout(self), self.s

        self.setSize(l.XM + 7 * l.XS, l.YM + 2 * l.YS)

        x, y = l.XM, l.YM
        # create stacks
        for j in range(7):
            s.rows.append(NinetyOne_RowStack(x, y, self, max_move=1,
                                             max_accept=1))
            x += l.XS
        x, y = l.XM, l.YM + l.YS
        for j in range(6):
            s.rows.append(NinetyOne_RowStack(x, y, self, max_move=1,
                                             max_accept=1))
            x += l.XS

        # create text
        if self.preview <= 1:
            y += l.YS // 2
            self.texts.score = MfxCanvasText(
                self.canvas, x, y, anchor="sw",
                font=self.app.getFont("canvas_large"))

        x, y = self.getInvisibleCoords()
        s.talon = InitialDealTalonStack(x, y, self)
        s.foundations.append(AbstractFoundationStack(x, y, self,
                                                     max_move=0,
                                                     max_accept=0,
                                                     suit=ANY_SUIT))

        # define stack-groups
        l.defaultStackGroups()

    def startGame(self):
        for i in range(3):
            self.s.talon.dealRow(frames=0)
        self._startAndDealRow()

    def updateText(self):
        if self.preview > 1 or not self.texts.score:
            return
        self.texts.score.config(text=str(self.getTotal()))

    def getTotal(self):
        total = 0
        for r in self.s.rows:
            if len(r.cards) == 0:
                continue
            total += r.cards[-1].rank + 1
        return total

    def checkTotal(self):
        self.updateText()
        if self.getTotal() == 91:
            for r in self.s.rows:
                if len(r.cards) == 0:
                    return
            self.startDealSample()
            old_state = self.enterState(self.S_FILL)
            for r in self.s.rows:
                r.moveMove(1, self.s.foundations[0])
            self.leaveState(old_state)
            self.stopSamples()
            self.checkTotal()

    def getAutoStacks(self, event=None):
        return ((), (), ())


# register the game
registerGame(GameInfo(257, Numerica, "Numerica",
                      GI.GT_NUMERICA | GI.GT_CONTRIB, 1, 0, GI.SL_BALANCED,
                      altnames=("Sir Tommy", "Old Patience", "Try Again")))
registerGame(GameInfo(599, Assembly, "Assembly",
                      GI.GT_NUMERICA, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(836, Ladybug, "Ladybug",
                      GI.GT_1DECK_TYPE, 1, -2, GI.SL_BALANCED))
registerGame(GameInfo(958, NinetyOne, "Ninety-One",
                      GI.GT_1DECK_TYPE, 1, 0, GI.SL_MOSTLY_SKILL))
