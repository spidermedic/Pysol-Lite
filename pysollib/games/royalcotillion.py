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
from pysollib.layout import Layout
from pysollib.stack import \
    AC_RowStack, \
    BasicRowStack, \
    DealRowTalonStack, \
    OpenStack, \
    RK_FoundationStack, \
    ReserveStack, \
    SS_FoundationStack, \
    Stack, \
    StackWrapper, \
    UD_RK_RowStack, \
    UD_SS_RowStack, \
    WasteStack, \
    WasteTalonStack
from pysollib.util import ACE, ANY_RANK, KING, NO_RANK

# ************************************************************************
# * Royal Cotillion
# ************************************************************************


class RoyalCotillion_Foundation(SS_FoundationStack):
    def getBottomImage(self):
        if self.cap.base_rank == 1:
            return self.game.app.images.getLetter(1)
        return self.game.app.images.getSuitBottom(self.cap.base_suit)


class RoyalCotillion(Game):
    Foundation_Class = RoyalCotillion_Foundation

    #
    # game layout
    #

    def createGame(self):
        # create layout
        l, s = Layout(self), self.s

        # set window
        self.setSize(l.XM + 10*l.XS, l.YM + 4*l.YS)

        # create stacks
        for i in range(4):
            x, y, = l.XM + i*l.XS, l.YM
            s.rows.append(BasicRowStack(x, y, self, max_accept=0))
        for i in range(4):
            x, y, = l.XM + 4*l.XS, l.YM + i*l.YS
            s.foundations.append(
                self.Foundation_Class(x, y, self, i, dir=2, mod=13))
            x += l.XS
            s.foundations.append(
                self.Foundation_Class(
                    x, y, self, i, dir=2, mod=13, base_rank=1))
        for i in range(4):
            for j in range(4):
                x, y, = l.XM + (j+6)*l.XS, l.YM + i*l.YS
                s.reserves.append(ReserveStack(x, y, self, max_accept=0))
        x, y = l.XM + l.XS, self.height - l.YS
        s.talon = WasteTalonStack(x, y, self, max_rounds=1)
        l.createText(s.talon, "sw")
        x += l.XS
        s.waste = WasteStack(x, y, self)
        l.createText(s.waste, "se")

        # define stack-groups
        l.defaultStackGroups()

    #
    # game overrides
    #

    def startGame(self):
        self.s.talon.dealRow(rows=self.s.reserves, frames=0)
        self.startDealSample()
        for i in range(3):
            self.s.talon.dealRow()
        self.s.talon.dealCards()          # deal first card to WasteStack

    def fillStack(self, stack):
        if not stack.cards:
            old_state = self.enterState(self.S_FILL)
            if stack is self.s.waste and self.s.talon.cards:
                self.s.talon.dealCards()
            elif stack in self.s.reserves and self.s.waste.cards:
                self.s.waste.moveMove(1, stack)
            self.leaveState(old_state)

    def getHighlightPilesStacks(self):
        return ()

    def getAutoStacks(self, event=None):
        if event is None:
            # disable auto drop - this would ruin the whole gameplay
            return (self.sg.dropstacks, (), self.sg.dropstacks)
        # rightclickHandler
        return (self.sg.dropstacks, self.sg.dropstacks, self.sg.dropstacks)


# ************************************************************************
# * Noumea
# ************************************************************************

class Noumea(RoyalCotillion):
    Foundation_Class = SS_FoundationStack

    def createGame(self):
        # create layout
        l, s = Layout(self), self.s

        # set window
        self.setSize(l.XM + 5*l.XS, l.YM + 6*l.YS)

        # create stacks
        x, y, = l.XM + .5 * l.XS, l.YM
        for i in range(4):
            s.foundations.append(self.Foundation_Class(x, y, self, i))
            x += l.XS
        x, y, = l.XM, y + l.YS
        for j in range(4):
            for i in range(5):
                s.reserves.append(ReserveStack(x, y, self, max_accept=0))
                x += l.XS
            x = l.XM
            y += l.YS
        x, y = l.XM + 1.5 * l.XS, l.YM + 5 * l.YS
        s.talon = WasteTalonStack(x, y, self, max_rounds=3, num_deal=3)
        l.createText(s.talon, "sw")
        x += l.XS
        s.waste = WasteStack(x, y, self)
        l.createText(s.waste, "se")

        # define stack-groups
        l.defaultStackGroups()

    #
    # game overrides
    #

    def _shuffleHook(self, cards):
        # move Aces to top of the Talon (i.e. first cards to be dealt)
        return self._shuffleHookMoveToTop(
            cards, lambda c: (c.rank == ACE, c.suit))

    def startGame(self):
        self.s.talon.dealRow(rows=self.s.foundations, frames=0)
        self.startDealSample()
        self.s.talon.dealRow(rows=self.s.reserves)
        self.s.talon.dealCards()          # deal first card to WasteStack


# ************************************************************************
# * Alhambra
# ************************************************************************

class Alhambra_Hint(CautiousDefaultHint):
    def _getDropCardScore(self, score, color, r, t, ncards):
        return 93000, color


class Alhambra_RowStack(UD_SS_RowStack):
    getBottomImage = Stack._getReserveBottomImage

    def getHelp(self):
        return 'Waste. Build up or down by suit.'


class Alhambra_Talon(DealRowTalonStack):
    def canDealCards(self):
        r_cards = sum(len(r.cards) for r in self.game.s.rows)
        if self.cards:
            return True
        if r_cards and self.round != self.max_rounds:
            return True
        return False

    def _deal(self):
        num_cards = 0
        for r in self.game.s.rows:
            if self.cards:
                self.game.flipAndMoveMove(self, r)
                num_cards += 1
        return num_cards

    def dealCards(self, sound=False):
        old_state = self.game.enterState(self.game.S_DEAL)
        num_cards = 0
        rows = self.game.s.rows
        r_cards = sum(len(r.cards) for r in self.game.s.rows)
        if self.cards:
            if sound and not self.game.demo:
                self.game.playSample("dealwaste")
            if len(self.game.s.rows) > 1:
                num_cards = self.dealRowAvail(sound=False, frames=4)
            else:
                num_cards = self._deal()
        elif r_cards and self.round != self.max_rounds:
            if sound:
                self.game.playSample("turnwaste", priority=20)
            for r in rows:
                for i in range(len(r.cards)):
                    self.game.moveMove(1, r, self, frames=0)
                    self.game.flipMove(self)
            if len(self.game.s.rows) > 1:
                num_cards = self.dealRowAvail(sound=False, frames=4)
            else:
                num_cards = self._deal()
            self.game.nextRoundMove(self)
        self.game.leaveState(old_state)
        return num_cards


class Alhambra(Game):
    Hint_Class = Alhambra_Hint

    RowStack_Class = StackWrapper(Alhambra_RowStack, base_rank=ANY_RANK)

    def createGame(self, rows=1, reserves=8, playcards=3):
        # create layout
        l, s = Layout(self), self.s

        # set window
        w, h = l.XM+8*l.XS, l.YM+3.5*l.YS+playcards*l.YOFFSET
        h += l.TEXT_HEIGHT
        self.setSize(w, h)

        # create stacks
        x, y, = l.XM, l.YM
        for i in range(4):
            s.foundations.append(SS_FoundationStack(x, y, self, suit=i,
                                                    max_move=0))
            x += l.XS
        for i in range(4):
            s.foundations.append(SS_FoundationStack(x, y, self, suit=i,
                                 max_move=0, base_rank=KING, dir=-1))
            x += l.XS
        x, y, = l.XM+(8-reserves)*l.XS//2, y+l.YS
        for i in range(reserves):
            stack = OpenStack(x, y, self, max_accept=0)
            stack.CARD_XOFFSET, stack.CARD_YOFFSET = 0, l.YOFFSET
            s.reserves.append(stack)
            x += l.XS
        x, y = l.XM+(8-1-rows)*l.XS//2, self.height-l.YS
        s.talon = Alhambra_Talon(x, y, self, max_rounds=3)
        if rows == 1:
            l.createText(s.talon, 'sw')
        else:
            l.createText(s.talon, 'n')
        anchor = 'nn'
        if rows > 1:
            anchor = 'sw'
        l.createRoundText(s.talon, anchor)

        x += l.XS
        for i in range(rows):
            stack = self.RowStack_Class(x, y, self, mod=13, max_accept=1)
            stack.CARD_XOFFSET, stack.CARD_YOFFSET = 0, 0
            s.rows.append(stack)
            x += l.XS
            if rows == 1:
                l.createText(stack, 'se')
            else:
                l.createText(stack, 'n')

        # define stack-groups (non default)
        l.defaultStackGroups()

    #
    # game overrides
    #

    def _shuffleHook(self, cards):
        # move one Aces and Kings of first deck to top of the Talon (i.e. first
        # card to be dealt)
        return self._shuffleHookMoveToTop(
            cards, lambda c: (c.deck == 0 and
                              c.rank in (ACE, KING), (c.rank, c.suit)), 8)

    def startGame(self):
        self.s.talon.dealRow(rows=self.s.foundations, frames=0)
        for i in range(3):
            self.s.talon.dealRow(rows=self.s.reserves, frames=0)
        self.startDealSample()
        self.s.talon.dealRow(rows=self.s.reserves)
        self.s.talon.dealCards()

    shallHighlightMatch = Game._shallHighlightMatch_SSW


class Reserves_RowStack(UD_RK_RowStack):
    getBottomImage = Stack._getReserveBottomImage

    def getHelp(self):
        return 'Waste. Build up or down regardless of suit.'


class Reserves(Alhambra):
    RowStack_Class = StackWrapper(Reserves_RowStack, base_rank=NO_RANK)

    def createGame(self):
        Alhambra.createGame(self, reserves=4, playcards=11)

    def startGame(self):
        self.s.talon.dealRow(rows=self.s.foundations, frames=0)
        for i in range(11):
            self.s.talon.dealRow(rows=self.s.reserves, frames=0)
        self.startDealSample()
        self.s.talon.dealRow(rows=self.s.reserves)
        self.s.talon.dealCards()

    shallHighlightMatch = Game._shallHighlightMatch_RKW


# ************************************************************************
# * Big Alhambra
# ************************************************************************

class BigAlhambra(Alhambra):

    def createGame(self, rows=1, reserves=10, playcards=3):
        # create layout
        l, s = Layout(self), self.s

        # set window
        w, h = l.XM + 12 * l.XS, l.YM + 3.5 * l.YS + playcards * l.YOFFSET
        h += l.TEXT_HEIGHT
        self.setSize(w, h)

        # create stacks
        x, y, = l.XM, l.YM
        for i in range(4):
            s.foundations.append(SS_FoundationStack(x, y, self, suit=i,
                                                    max_move=0))
            x += l.XS
        for i in range(2):
            s.foundations.append(SS_FoundationStack(x, y, self, suit=i,
                                                    max_move=0))
            x += l.XS
        for i in range(2, 4):
            s.foundations.append(SS_FoundationStack(x, y, self, suit=i,
                                 max_move=0, base_rank=KING, dir=-1))
            x += l.XS
        for i in range(4):
            s.foundations.append(SS_FoundationStack(x, y, self, suit=i,
                                 max_move=0, base_rank=KING, dir=-1))
            x += l.XS
        x, y, = l.XM + l.XS, y + l.YS
        for i in range(10):
            stack = OpenStack(x, y, self, max_accept=0)
            stack.CARD_XOFFSET, stack.CARD_YOFFSET = 0, l.YOFFSET
            s.reserves.append(stack)
            x += l.XS
        x, y = l.XM + 5 * l.XS, self.height - l.YS
        s.talon = Alhambra_Talon(x, y, self, max_rounds=3)
        if rows == 1:
            l.createText(s.talon, 'sw')
        else:
            l.createText(s.talon, 'n')
        anchor = 'nn'
        if rows > 1:
            anchor = 'sw'
        l.createRoundText(s.talon, anchor)

        x += l.XS
        for i in range(rows):
            stack = self.RowStack_Class(x, y, self, mod=13, max_accept=1)
            stack.CARD_XOFFSET, stack.CARD_YOFFSET = 0, 0
            s.rows.append(stack)
            x += l.XS
            if rows == 1:
                l.createText(stack, 'se')
            else:
                l.createText(stack, 'n')

        # define stack-groups (non default)
        l.defaultStackGroups()

    #
    # game overrides
    #

    def _shuffleHook(self, cards):
        # move the appropriate aces and kings to top of the Talon
        # (i.e. first card to be dealt)
        return self._shuffleHookMoveToTop(
            cards, lambda c: (c.id in (0, 13, 26, 39, 52, 65, 90, 103, 116,
                                       129, 142, 155), c.id), 12)


# ************************************************************************
# * Carpet
# ************************************************************************

class Carpet(Game):
    Foundation_Class = SS_FoundationStack

    #
    # game layout
    #

    def createGame(self):
        # create layout
        l, s = Layout(self), self.s

        # set window
        self.setSize(l.XM + 9*l.XS, l.YM + 4*l.YS)

        # create stacks
        for i in range(4):
            for j in range(5):
                x, y = l.XM + (j+3)*l.XS, l.YM + i*l.YS
                s.rows.append(ReserveStack(x, y, self))
        for i in range(4):
            dx, dy = ((2, 1), (8, 1), (2, 2), (8, 2))[i]
            x, y = l.XM + dx*l.XS, l.YM + dy*l.YS
            s.foundations.append(self.Foundation_Class(x, y, self, i))
        x, y = l.XM, l.YM
        s.talon = WasteTalonStack(x, y, self, max_rounds=1)
        l.createText(s.talon, "se")
        y = y + l.YS
        s.waste = WasteStack(x, y, self)
        l.createText(s.waste, "se")

        # define stack-groups
        l.defaultStackGroups()

    #
    # game overrides
    #

    def _shuffleHook(self, cards):
        # move Aces to top of the Talon (i.e. first cards to be dealt)
        return self._shuffleHookMoveToTop(
            cards, lambda c: (c.rank == 0, c.suit))

    def startGame(self):
        self.startDealSample()
        self.s.talon.dealRow(rows=self.s.foundations)
        self.s.talon.dealRow()
        self.s.talon.dealCards()          # deal first card to WasteStack


# ************************************************************************
# * British Constitution
# ************************************************************************

class BritishConstitution_RowStackMethods:
    def acceptsCards(self, from_stack, cards):
        if self in self.game.s.rows[:8] and \
                from_stack in self.game.s.rows[8:16]:
            return True
        if self in self.game.s.rows[8:16] and \
                from_stack in self.game.s.rows[16:24]:
            return True
        if self in self.game.s.rows[16:24] and \
                from_stack in self.game.s.rows[24:]:
            return True
        if self in self.game.s.rows[24:] and from_stack is self.game.s.waste:
            return True
        return False


class BritishConstitution_RowStack(BritishConstitution_RowStackMethods,
                                   AC_RowStack):
    def acceptsCards(self, from_stack, cards):
        if not AC_RowStack.acceptsCards(self, from_stack, cards):
            return False
        return BritishConstitution_RowStackMethods.acceptsCards(
            self, from_stack, cards)


class BritishConstitution_Foundation(SS_FoundationStack):
    def acceptsCards(self, from_stack, cards):
        if not SS_FoundationStack.acceptsCards(self, from_stack, cards):
            return False
        if from_stack in self.game.s.rows[:8]:
            return True
        return False


class BritishConstitution(Game):
    RowStack_Class = BritishConstitution_RowStack

    def createGame(self):
        # create layout
        l, s = Layout(self), self.s

        # set window
        self.setSize(l.XM + 9*l.XS, l.YM + 5*l.YS)

        # create stacks
        x, y = l.XM+l.XS, l.YM
        for i in range(8):
            s.foundations.append(BritishConstitution_Foundation(x, y, self,
                                 suit=int(i//2), max_cards=11))
            x += l.XS

        y = l.YM+l.YS
        for i in range(4):
            x = l.XM+l.XS
            for j in range(8):
                stack = self.RowStack_Class(x, y, self, max_move=1)
                stack.CARD_XOFFSET, stack.CARD_YOFFSET = 0, 0
                s.rows.append(stack)
                x += l.XS
            y += l.YS

        x, y = l.XM, l.YM
        s.talon = WasteTalonStack(x, y, self, max_rounds=1)
        l.createText(s.talon, "s")
        y += l.YS+l.TEXT_HEIGHT
        s.waste = WasteStack(x, y, self)
        l.createText(s.waste, "s")

        # define stack-groups
        l.defaultStackGroups()

    def startGame(self):
        self.s.talon.dealRow(rows=self.s.foundations, frames=0)
        self._startAndDealRowAndCards()

    def _shuffleHook(self, cards):
        # move Aces to top of the Talon (i.e. first cards to be dealt)
        return self._shuffleHookMoveToTop(
            cards, lambda c: (c.rank == ACE, c.suit))

    def fillStack(self, stack):
        if not stack.cards:
            if stack in self.s.rows[:24]:
                return
            old_state = self.enterState(self.S_FILL)
            if stack is self.s.waste and self.s.talon.cards:
                self.s.talon.dealCards()
            elif stack in self.s.rows[24:] and self.s.waste.cards:
                self.s.waste.moveMove(1, stack)
            self.leaveState(old_state)

    shallHighlightMatch = Game._shallHighlightMatch_AC


# ************************************************************************
# * Twenty
# ************************************************************************

class Twenty_RowStack(BasicRowStack):
    def acceptsCards(self, from_stack, cards):
        if not BasicRowStack.acceptsCards(self, from_stack, cards):
            return False
        return len(self.cards) == 0

    def getHelp(self):
        return 'Tableau. Empty piles can be filled with any card.'


class Twenty(Game):
    def createGame(self):
        # create layout
        l, s = Layout(self), self.s

        # set window
        self.setSize(l.XM+10*l.XS, l.YM+3*l.YS+10*l.YOFFSET)

        # create stacks
        x, y = l.XM, l.YM
        s.talon = DealRowTalonStack(x, y, self)
        l.createText(s.talon, 'se')
        x += 2*l.XS
        for i in range(4):
            s.foundations.append(SS_FoundationStack(x, y, self, suit=i))
            x += l.XS
        for i in range(4):
            s.foundations.append(SS_FoundationStack(x, y, self, suit=i,
                                 base_rank=KING, dir=-1))
            x += l.XS

        for y in (l.YM+l.YS, l.YM+2*l.YS+5*l.YOFFSET):
            x = l.XM
            for i in range(10):
                s.rows.append(Twenty_RowStack(x, y, self,
                              base_rank=ANY_RANK, max_accept=1))
                x += l.XS

        # define stack-groups
        l.defaultStackGroups()

    def _shuffleHook(self, cards):
        return self._shuffleHookMoveToTop(
            cards,
            lambda c: (c.rank in (ACE, KING) and c.deck == 1,
                       (c.rank, c.suit)))

    def startGame(self):
        self.s.talon.dealRow(rows=self.s.foundations, frames=0)
        self._startAndDealRow()

    def fillStack(self, stack):
        if not stack.cards and stack in self.s.rows and self.s.talon.cards:
            old_state = self.enterState(self.S_FILL)
            self.flipMove(self.s.talon)
            self.s.talon.moveMove(1, stack)
            self.leaveState(old_state)


# ************************************************************************
# * Four Winds
# * Boxing the Compass
# ************************************************************************

class FourWinds(Game):

    def createGame(self):
        l, s = Layout(self), self.s
        self.setSize(l.XM+9*l.XS, l.YM+6*l.YS)

        # vertical rows
        x = l.XM+l.XS
        for i in (0, 1):
            y = l.YM+l.YS
            for j in range(4):
                stack = ReserveStack(x, y, self, base_suit=i)
                stack.getBottomImage = stack._getSuitBottomImage
                s.rows.append(stack)
                y += l.YS
            x += 6*l.XS
        # horizontal rows
        y = l.YM+l.YS
        for i in (2, 3):
            x = l.XM+2.5*l.XS
            for j in range(4):
                stack = ReserveStack(x, y, self, base_suit=i)
                stack.getBottomImage = stack._getSuitBottomImage
                s.rows.append(stack)
                x += l.XS
            y += 3*l.YS
        # foundations
        decks = self.gameinfo.decks
        for k in range(decks):
            suit = 0
            for i, j in ((0, 3-decks*0.5+k),
                         (8, 3-decks*0.5+k),
                         (4.5-decks*0.5+k, 0),
                         (4.5-decks*0.5+k, 5)):
                x, y = l.XM+i*l.XS, l.YM+j*l.YS
                s.foundations.append(SS_FoundationStack(x, y, self,
                                     suit=suit, max_move=0))
                suit += 1
        # talon & waste
        x, y = l.XM+3.5*l.XS, l.YM+2.5*l.YS
        s.talon = WasteTalonStack(x, y, self, max_rounds=2)
        l.createText(s.talon, 's')
        l.createRoundText(self.s.talon, 'nn')
        x += l.XS
        s.waste = WasteStack(x, y, self)
        l.createText(s.waste, 's')

        l.defaultStackGroups()

    def startGame(self):
        self.s.talon.dealRow(rows=self.s.foundations, frames=0)
        self.startDealSample()
        self.s.talon.dealRow()
        self.s.talon.dealCards()

    def _shuffleHook(self, cards):
        # move Aces to top of the Talon (i.e. first cards to be dealt)
        return self._shuffleHookMoveToTop(
            cards,
            lambda c: (c.rank == ACE, (c.deck, c.suit)))


class BoxingTheCompass(FourWinds):
    pass


# ************************************************************************
# * Rosamund's Bower
# ************************************************************************

class RosamundsBower_Talon(WasteTalonStack):
    def _redeal(self):
        game, num_cards = self.game, len(self.cards)
        if len(self.waste.cards) > 0:
            game.moveMove(1, self.waste, game.s.reserves[3], frames=2)
        rows = list(game.s.reserves)[3:6]
        rows.reverse()
        for r in rows:
            while r.cards:
                num_cards = num_cards + 1
                game.moveMove(1, r, self, frames=2)
                if self.cards[-1].face_up:
                    game.flipMove(self)
        assert len(self.cards) == num_cards
        self.game.nextRoundMove(self)

    def canDealCards(self):
        return (len(self.cards) > 0 or self.round != self.max_rounds) and \
            (len(self.cards) == 0 or len(self.waste.cards) == 0)

    def dealCards(self, sound=False):
        if self.cards:
            return WasteTalonStack.dealCards(self, sound=sound)
        if sound:
            self.game.startDealSample()
        self._redeal()
        if sound:
            self.game.stopSamples()
        return


class RosamundsBower_Guards(OpenStack):
    def canFlipCard(self):
        return False


class RosamundsBower_WasteReserve(ReserveStack):
    def acceptsCards(self, from_stack, cards):
        return from_stack == self.game.s.waste


class RosamundsBower_KingQueen(OpenStack):
    def acceptsCards(self, from_stack, cards):
        return False

    def canMoveCards(self, cards):
        return len(self.game.s.foundations[0].cards) > 49


class RosamundsBower(Game):

    def createGame(self):
        l, s = Layout(self), self.s
        self.setSize(l.XM + 7.5 * l.XS, l.YM + l.TEXT_HEIGHT + 5.5 * l.YS)

        # vertical rows
        x = l.XM + l.XS * 2
        for i in (0, 1):
            y = l.YM + l.YS
            for j in range(2):
                stack = BasicRowStack(x, y, self)
                s.rows.append(stack)
                y += l.YS
            x += 3 * l.XS
        # horizontal rows
        y = l.YM
        for i in (2, 3):
            x = l.XM + l.XS * 3
            for j in range(2):
                stack = BasicRowStack(x, y, self)
                s.rows.append(stack)
                x += l.XS
            y += 3 * l.YS
        # Fair Rosamund and the king
        x, y = l.XM + 6.5 * l.XS, l.YM
        s.reserves.append(RosamundsBower_KingQueen(x, y, self))
        x, y = l.XM + 3.5 * l.XS, l.YM + 1.5 * l.YS
        s.reserves.append(RosamundsBower_KingQueen(x, y, self))

        # Other stacks
        x, y = l.XM + 6.5 * l.XS, l.YM + l.YS
        s.reserves.append(RosamundsBower_Guards(x, y, self))
        l.createText(s.reserves[2], 's')

        x, y = l.XM, l.YM + 3 * l.YS
        s.foundations.append(RK_FoundationStack(x, y, self,
                                                dir=-1, max_cards=52,
                                                mod=13))
        y = l.YM + 4.5 * l.YS
        s.talon = RosamundsBower_Talon(x, y, self, max_rounds=4)
        l.createText(s.talon, 's')
        l.createRoundText(self.s.talon, 'n')
        x += l.XS
        s.waste = WasteStack(x, y, self)
        l.createText(s.waste, 's')
        x += .5 * l.XS

        for i in range(3):
            x += l.XS
            s.reserves.append(RosamundsBower_WasteReserve(x, y, self,
                                                          max_cards=52))

        l.defaultStackGroups()

    def startGame(self):
        self.s.talon.dealRow(rows=self.s.foundations, frames=0)
        self.s.talon.dealRow(rows=self.s.reserves[:2], frames=0)
        for i in range(7):
            self.s.talon.dealRow(rows=[self.s.reserves[2]], frames=0, flip=0)
        self.startDealSample()
        self.s.talon.dealRow()
        self.s.talon.dealCards()

    def fillStack(self, stack):
        if not stack.cards and stack in self.s.rows:
            if self.s.reserves[2].cards:
                old_state = self.enterState(self.S_FILL)
                self.s.reserves[2].flipMove()
                self.s.reserves[2].moveMove(1, stack)
                self.leaveState(old_state)

    def _shuffleHook(self, cards):
        # move Fair Rosamund, the king, and the knave to the top of
        # the deck.
        return self._shuffleHookMoveToTop(
            cards, lambda c: (c.id in (23, 37, 25), c.id), 3)

    def _autoDeal(self, sound=True):
        # only autodeal if there are cards in the talon.
        if len(self.s.talon.cards) > 0:
            return Game._autoDeal(self, sound=sound)


# register the game
registerGame(GameInfo(54, RoyalCotillion, "Royal Cotillion",
                      GI.GT_2DECK_TYPE, 2, 0, GI.SL_LUCK,
                      altnames=("Lords and Ladies",)))
registerGame(GameInfo(234, Alhambra, "Alhambra",
                      GI.GT_2DECK_TYPE, 2, 2, GI.SL_BALANCED))
registerGame(GameInfo(97, Carpet, "Carpet",
                      GI.GT_1DECK_TYPE | GI.GT_CHILDREN, 1, 0,
                      GI.SL_MOSTLY_LUCK))
registerGame(GameInfo(391, BritishConstitution, "British Constitution",
                      GI.GT_2DECK_TYPE | GI.GT_STRIPPED, 2, 0, GI.SL_BALANCED,
                      ranks=list(range(11)),  # without Queens and Kings
                      altnames=("Constitution",)))
registerGame(GameInfo(443, Twenty, "Twenty",
                      GI.GT_NUMERICA, 2, 0, GI.SL_BALANCED))
registerGame(GameInfo(675, FourWinds, "Four Winds",
                      GI.GT_1DECK_TYPE, 1, 1, GI.SL_BALANCED))
registerGame(GameInfo(676, BoxingTheCompass, "Boxing the Compass",
                      GI.GT_2DECK_TYPE, 2, 1, GI.SL_BALANCED))
registerGame(GameInfo(943, RosamundsBower, "Rosamund's Bower",
                      GI.GT_1DECK_TYPE, 1, 3, GI.SL_BALANCED,
                      altnames=("Rosamund",)))
registerGame(GameInfo(952, BigAlhambra, "Big Alhambra",
                      GI.GT_3DECK_TYPE, 3, 2, GI.SL_BALANCED))
registerGame(GameInfo(978, Noumea, "Noumea",
                      GI.GT_1DECK_TYPE, 1, 2, GI.SL_MOSTLY_LUCK))
