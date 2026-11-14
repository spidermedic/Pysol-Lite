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
from pysollib.hint import AbstractHint
from pysollib.hint import BlackHoleSolverWrapper
from pysollib.layout import Layout
from pysollib.mfxutil import kwdefault
from pysollib.pysoltk import MfxCanvasText
from pysollib.stack import (
    AbstractFoundationStack,
    AutoDealTalonStack,
    BasicRowStack,
    InitialDealTalonStack,
    OpenStack,
    RK_FoundationStack,
    RK_RowStack,
    ReserveStack,
    SS_FoundationStack,
    StackWrapper,
    WasteStack,
    WasteTalonStack,
)
from pysollib.util import ANY_RANK, ANY_SUIT, KING, NO_RANK, RANKS


class Golf_Hint(AbstractHint):
    # FIXME: this is very simple

    def computeHints(self):
        game = self.game
        # for each stack
        for r in game.sg.dropstacks:
            # try if we can drop a card to the Waste
            w, ncards = r.canDropCards(game.s.foundations)
            if not w:
                continue
            # this assertion must hold for Golf
            assert ncards == 1
            # clone the Waste (including the card that will be dropped) to
            # form our new foundations
            ww = (self.ClonedStack(w, stackcards=w.cards+[r.cards[-1]]), )
            # now search for a stack that would benefit from this card
            score, color = 10000 + r.id, None
            for t in game.sg.dropstacks:
                if not t.cards:
                    continue
                if t is r:
                    t = self.ClonedStack(r, stackcards=r.cards[:-1])
                if t.canFlipCard():
                    score = score + 100
                elif t.canDropCards(ww)[0]:
                    score = score + 100
            # add hint
            self.addHint(score, ncards, r, w, color)


# ************************************************************************
# *
# ************************************************************************

class Golf_Talon(WasteTalonStack):
    def canDealCards(self):
        if not WasteTalonStack.canDealCards(self):
            return False
        return not self.game.isGameWon()


class Golf_Waste(WasteStack):
    def __init__(self, x, y, game, **cap):
        kwdefault(cap, max_move=0, max_accept=1)
        WasteStack.__init__(self, x, y, game, **cap)

    def acceptsCards(self, from_stack, cards):
        if from_stack is self.game.s.talon:
            return True
        if not WasteStack.acceptsCards(self, from_stack, cards):
            return False
        # if there are jokers, they're wild
        if self.cards[-1].suit == 4 or cards[0].suit == 4:
            return True
        # check cards
        r1, r2 = self.cards[-1].rank, cards[0].rank
        if self.game.getStrictness() == 1:
            # nothing on a King
            if r1 == KING:
                return False
        return (r1 + 1) % self.cap.mod == r2 or (r2 + 1) % self.cap.mod == r1

    def getHelp(self):
        return 'Waste. Build up or down regardless of suit.'


class Golf_RowStack(BasicRowStack):
    def clickHandler(self, event):
        return self.doubleclickHandler(event)

    def getHelp(self):
        return 'Tableau. No building.'


# ************************************************************************
# * Golf
# ************************************************************************

class Golf(Game):
    Solver_Class = BlackHoleSolverWrapper(preset='golf', base_rank=0,
                                          queens_on_kings=True)
    Talon_Class = Golf_Talon
    Waste_Class = Golf_Waste
    Hint_Class = Golf_Hint
    Reserve_Class = None

    ROUNDS = 1

    #
    # game layout
    #

    def createGame(self, columns=7):
        # create layout
        layout, s = Layout(self), self.s

        # set window
        playcards = 5
        w1, w2 = (columns + 1) * layout.XS + layout.XM, 2 * layout.XS

        totalcards = 52 * self.gameinfo.decks
        if w2 + totalcards * layout.XOFFSET > w1:
            layout.XOFFSET = int((w1 - w2) / totalcards)
        self.setSize(w1, layout.YM + 3 * layout.YS +
                     (playcards - 1) * layout.YOFFSET + layout.TEXT_HEIGHT)

        # create stacks
        x, y = layout.XM + layout.XS // 2, layout.YM
        for i in range(columns):
            s.rows.append(Golf_RowStack(x, y, self))
            x += layout.XS
        x, y = layout.XM, self.height - layout.YS
        s.talon = self.Talon_Class(x, y, self, max_rounds=self.ROUNDS)
        layout.createText(s.talon, "n")
        x += layout.XS
        s.waste = self.Waste_Class(x, y, self)
        if self.Reserve_Class is None:
            s.waste.CARD_XOFFSET = layout.XOFFSET
        else:
            x += layout.XS
            s.reserves.append(self.Reserve_Class(x, y, self))
            layout.createText(s.reserves[0], "n")
        layout.createText(s.waste, "n")
        # the Waste is also our only Foundation in this game
        s.foundations.append(s.waste)

        # define stack-groups (non default)
        self.sg.openstacks = [s.waste]
        self.sg.talonstacks = [s.talon]
        self.sg.dropstacks = s.rows
        if self.Reserve_Class is not None:
            self.sg.openstacks += s.reserves
            self.sg.reservestacks = s.reserves

    #
    # game overrides
    #

    def startGame(self, num_rows=5):
        self._startDealNumRows(num_rows - 1)
        self.s.talon.dealRow()
        self.s.talon.dealCards()          # deal first card to WasteStack

    def isGameWon(self):
        for r in self.s.rows:
            if r.cards:
                return False
        return True

    shallHighlightMatch = Game._shallHighlightMatch_RK

    def getHighlightPilesStacks(self):
        return ()

    def getAutoStacks(self, event=None):
        if event is None:
            # disable auto drop and auto flip
            # auto drop would ruin the gameplay
            # auto flip causes issues with undo when multiple cards are flipped
            return ([], (), ())
        # rightclickHandler
        return (self.sg.dropstacks, self.sg.dropstacks, ())

    def fillStack(self, stack):
        old_state = self.enterState(self.S_FILL)
        for r in self.s.rows:
            if r.canFlipCard():
                r.flipMove(animation=True)
        self.leaveState(old_state)


# ************************************************************************
# * Thieves
# ************************************************************************

class Thieves(Golf):
    pass


# ************************************************************************
# * Relaxed Golf
# ************************************************************************


class RelaxedGolf(Golf):
    Solver_Class = BlackHoleSolverWrapper(preset='golf', base_rank=0,
                                          wrap_ranks=True)
    Waste_Class = StackWrapper(Golf_Waste, mod=13)

    shallHighlightMatch = Game._shallHighlightMatch_RKW


# ************************************************************************
# * Elevator - Relaxed Golf in a Pyramid layout
# ************************************************************************

class Elevator_RowStack(Golf_RowStack):
    STEP = (1, 2, 2, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6, 6)

    def basicIsBlocked(self):
        r, step = self.game.s.rows, self.STEP
        i, n, mylen = self.id, 1, len(step)
        while i < mylen:
            i = i + step[i]
            n = n + 1
            for j in range(i, i+n):
                if r[j].cards:
                    return True
        return False

    def canSelect(self):
        return len(self.cards) > 0 and self.cards[-1].face_up


class Elevator(RelaxedGolf):

    #
    # game layout
    #

    def createGame(self):
        # create layout
        layout, s = Layout(self), self.s

        # set window
        self.setSize(9*layout.XS+layout.XM, 4*layout.YS+layout.YM)

        # create stacks
        for i in range(7):
            x = layout.XM + (8-i) * layout.XS // 2
            y = layout.YM + i * layout.YS // 2
            for j in range(i+1):
                s.rows.append(Elevator_RowStack(x, y, self))
                x = x + layout.XS
        x, y = layout.XM, layout.YM
        s.talon = Golf_Talon(x, y, self, max_rounds=1)
        layout.createText(s.talon, "s")
        x = x + layout.XS
        s.waste = self.Waste_Class(x, y, self)
        layout.createText(s.waste, "s")
        # the Waste is also our only Foundation in this game
        s.foundations.append(s.waste)

        # define stack-groups (non default)
        self.sg.openstacks = [s.waste]
        self.sg.talonstacks = [s.talon]
        self.sg.dropstacks = s.rows

    #
    # game overrides
    #

    def startGame(self):
        self.startDealSample()
        self.s.talon.dealRow(rows=self.s.rows[:21], flip=0)
        self.s.talon.dealRow(rows=self.s.rows[21:])
        self.s.talon.dealCards()          # deal first card to WasteStack

    def getStackSpeech(self, stack, cardindex):
        if stack not in self.s.rows:
            return Game.getStackSpeech(self, stack, cardindex)
        if len(stack.cards) == 0:
            return self.parseEmptyStack(stack)
        mainCard = self.parseCard(stack.cards[cardindex])
        coverCards = ()
        r, step = self.s.rows, stack.STEP
        i, mylen = stack.id, len(stack.STEP)
        if i < mylen:
            i = i + step[i]
            for j in range(2):
                if r[j + i].cards:
                    coverCards += (r[j + i],)
        if len(coverCards) > 0:
            mainCard += " - " + "Covered by"
            for c in coverCards:
                mainCard += " - " + self.parseCard(c.cards[0])
        return mainCard


# ************************************************************************
# * Black Hole
# ************************************************************************

class BlackHole_Foundation(AbstractFoundationStack):
    def acceptsCards(self, from_stack, cards):
        if not AbstractFoundationStack.acceptsCards(self, from_stack, cards):
            return False
        # check the rank
        if self.cards:
            r1, r2 = self.cards[-1].rank, cards[0].rank
            return (r1 + 1) % self.cap.mod == r2 or \
                (r2 + 1) % self.cap.mod == r1
        return True

    def getHelp(self):
        return 'Foundation. Build up or down regardless of suit.'


class BlackHole_RowStack(ReserveStack):
    def clickHandler(self, event):
        return self.doubleclickHandler(event)

    def getHelp(self):
        return 'Tableau. No building.'


class BlackHole(Game):
    RowStack_Class = StackWrapper(
        BlackHole_RowStack, max_accept=0, max_cards=3)
    Hint_Class = Golf_Hint
    Solver_Class = BlackHoleSolverWrapper(preset='black_hole')

    FOUNDATIONS = 1

    #
    # game layout
    #

    def createGame(self, playcards=5):
        # create layout
        layout, s = Layout(self), self.s

        # set window
        w = max((1 + self.FOUNDATIONS) * layout.XS,
                layout.XS + (playcards - 1) * layout.XOFFSET)
        self.setSize(layout.XM + 5 * w, layout.YM + 4 * layout.YS)

        # create stacks
        y = layout.YM
        for i in range(5):
            x = layout.XM + i*w
            s.rows.append(self.RowStack_Class(x, y, self))
        for i in range(2):
            y = y + layout.YS
            for j in (0, 1, 3, 4):
                x = layout.XM + j*w
                s.rows.append(self.RowStack_Class(x, y, self))
        y = y + layout.YS
        for i in range(4):
            x = layout.XM + i*w
            s.rows.append(self.RowStack_Class(x, y, self))
        for r in s.rows:
            r.CARD_XOFFSET = layout.XOFFSET
            r.CARD_YOFFSET = 0
        x, y = layout.XM + 2*w, layout.YM + 3*layout.YS//2
        for f in range(self.FOUNDATIONS):
            s.foundations.append(BlackHole_Foundation(x, y, self,
                                 suit=ANY_SUIT, dir=0, mod=13, max_move=0,
                                 max_cards=52 * self.gameinfo.decks))
            layout.createText(s.foundations[f], "s")
            x += layout.XS
        x, y = layout.XM + 4*w, self.height - layout.YS
        s.talon = InitialDealTalonStack(x, y, self)

        # define stack-groups
        layout.defaultStackGroups()

    #
    # game overrides
    #

    def _shuffleHook(self, cards):
        # move Ace to bottom of the Talon (i.e. last cards to be dealt)
        return self._shuffleHookMoveToBottom(
            cards, lambda c: (c.id == 13, c.suit), 1)

    def startGame(self):
        self._startDealNumRows(2)
        self.s.talon.dealRow()
        self.s.talon.dealRow(rows=self.s.foundations)

    def getAutoStacks(self, event=None):
        if event is None:
            # disable auto drop - this would ruin the whole gameplay
            return ((), (), self.sg.dropstacks)
        # rightclickHandler
        return ((), self.sg.dropstacks, self.sg.dropstacks)


# ************************************************************************
# * Binary Star
# ************************************************************************

class BinaryStar(BlackHole):
    RowStack_Class = StackWrapper(
        ReserveStack, max_accept=0, max_cards=6)
    # TODO: Solver support
    Solver_Class = BlackHoleSolverWrapper(preset='binary_star')
    FOUNDATIONS = 2

    def _shuffleHook(self, cards):
        # move Ace and king to bottom of the Talon
        # (i.e. last cards to be dealt)
        return self._shuffleHookMoveToBottom(
            cards, lambda c: (c.id in (13, 38), c.suit), 2)

    def startGame(self):
        self._startDealNumRows(5)
        self.s.talon.dealRow()
        self.s.talon.dealRow(rows=self.s.foundations)


# ************************************************************************
# * All in a Row
# ************************************************************************

class AllInARow(BlackHole):

    Solver_Class = BlackHoleSolverWrapper(preset='all_in_a_row')

    def createGame(self):
        # create layout
        layout, s = Layout(self), self.s

        # set window
        h = layout.YM+layout.YS+4*layout.YOFFSET
        self.setSize(layout.XM+7*layout.XS, 3*layout.YM+2*h+layout.YS)

        # create stacks
        x, y = layout.XM, layout.YM
        for i in range(7):
            s.rows.append(self.RowStack_Class(x, y, self))
            x += layout.XS
        x, y = layout.XM, layout.YM+h
        for i in range(6):
            s.rows.append(self.RowStack_Class(x, y, self))
            x += layout.XS
        for r in s.rows:
            r.CARD_XOFFSET, r.CARD_YOFFSET = 0, layout.YOFFSET

        x, y = layout.XM, self.height-layout.YS
        stack = BlackHole_Foundation(
            x, y, self, ANY_SUIT, dir=0, mod=13, max_move=0, max_cards=52,
            base_rank=ANY_RANK)
        s.foundations.append(stack)
        stack.CARD_XOFFSET, stack.CARD_YOFFSET = (self.width-layout.XS)//51, 0
        layout.createText(stack, 'n')
        x = self.width-layout.XS
        s.talon = InitialDealTalonStack(x, y, self)

        # define stack-groups
        layout.defaultStackGroups()

    def startGame(self):
        self._startDealNumRowsAndDealSingleRow(3)


# ************************************************************************
# * Robert
# ************************************************************************

class Robert(Game):
    Foundation_Stack = BlackHole_Foundation

    def createGame(self, max_rounds=3, num_deal=1, num_foundations=1):
        layout, s = Layout(self), self.s
        self.setSize(layout.XM + max(4, num_foundations) * layout.XS,
                     layout.YM + layout.TEXT_HEIGHT + 2 * layout.YS)
        x, y = layout.XM, layout.YM
        if num_foundations == 1:
            x += 3 * layout.XS // 2
        elif num_foundations == 2:
            x += layout.XS
        for f in range(num_foundations):
            stack = self.Foundation_Stack(x, y, self, ANY_SUIT,
                                          dir=0, mod=13, max_move=0,
                                          max_cards=52,
                                          base_rank=ANY_RANK)
            s.foundations.append(stack)
            layout.createText(stack, 's')
            x += layout.XS

        x, y = layout.XM + (layout.XS * max((num_foundations // 2) - 1, 1)), \
            layout.YM + layout.YS + layout.TEXT_HEIGHT
        s.talon = WasteTalonStack(x, y, self,
                                  max_rounds=max_rounds, num_deal=num_deal)
        layout.createText(s.talon, 'nw')
        if max_rounds > 0:
            layout.createRoundText(self.s.talon, 'se', dx=layout.XS)
        x += layout.XS
        s.waste = WasteStack(x, y, self)
        layout.createText(s.waste, 'ne')

        # define stack-groups
        layout.defaultStackGroups()

    def startGame(self):
        self.startDealSample()
        self.s.talon.dealRow(rows=self.s.foundations)
        self.s.talon.dealCards()


# ************************************************************************
# * Vague
# ************************************************************************

class Vague_RowStack(BasicRowStack):
    clickHandler = BasicRowStack.doubleclickHandler


class Vague(Game):
    Foundation_Classes = [StackWrapper(SS_FoundationStack,
                                       base_rank=ANY_RANK, mod=13)]

    SEPARATE_FOUNDATIONS = True
    SPREAD_FOUNDATION = False

    def createGame(self, rows=3, columns=6):
        layout, s = Layout(self), self.s
        decks = self.gameinfo.decks
        maxrows = max(columns, 2+decks*4)
        self.setSize(layout.XM+maxrows*layout.XS, layout.YM+(rows+1)*layout.YS)

        x, y = layout.XM, layout.YM
        s.talon = AutoDealTalonStack(x, y, self)
        layout.createText(s.talon, 'ne')

        x, y = layout.XM+2*layout.XS, layout.YM
        for found in self.Foundation_Classes:
            if self.SEPARATE_FOUNDATIONS:
                for i in range(4):
                    s.foundations.append(found(x, y, self, suit=i))
                    x += layout.XS
            else:
                s.foundations.append(found(x, y, self, suit=ANY_SUIT))
                if self.SPREAD_FOUNDATION:
                    w1, w2 = 6 * layout.XS + layout.XM, 2 * layout.XS

                    totalcards = self.gameinfo.ncards
                    if w2 + totalcards * layout.XOFFSET > w1:
                        layout.XOFFSET = int((w1 - w2) / totalcards)
                    s.foundations[0].CARD_XOFFSET = layout.XOFFSET

        y = layout.YM+layout.YS
        for i in range(rows):
            x = layout.XM + (maxrows-columns)*layout.XS//2
            for j in range(columns):
                s.rows.append(Vague_RowStack(x, y, self))
                x += layout.XS
            y += layout.YS

        layout.defaultStackGroups()

    def startGame(self):
        self.startDealSample()
        self.s.talon.dealRow()

    def fillStack(self, stack):
        if stack in self.s.rows and not stack.cards:
            if self.s.talon.cards:
                old_state = self.enterState(self.S_FILL)
                if not self.s.talon.cards[-1].face_up:
                    self.s.talon.flipMove()
                self.s.talon.moveMove(1, stack)
                self.leaveState(old_state)

    def getAutoStacks(self, event=None):
        if event is None:
            # disable auto drop - this would ruin the whole gameplay
            return ((), (), self.sg.dropstacks)
        # rightclickHandler
        return ((), self.sg.dropstacks, self.sg.dropstacks)


# ************************************************************************
# * Devil's Solitaire
# ************************************************************************

class DevilsSolitaire_Foundation(RK_FoundationStack):
    def acceptsCards(self, from_stack, cards):
        if not RK_FoundationStack.acceptsCards(self, from_stack, cards):
            return False
        if self.cards:
            return True
        if self.game.s.reserves[0].cards:
            c = self.game.s.reserves[0].cards[-1]
            return (c.rank+1) % 13 == cards[-1].rank
        return True


class DevilsSolitaire_WasteStack(WasteStack):
    clickHandler = WasteStack.doubleclickHandler


class DevilsSolitaire(Game):

    def createGame(self):
        layout, s = Layout(self), self.s
        self.setSize(
            layout.XM+9*layout.XS,
            layout.YM+3*layout.YS+7*layout.YOFFSET+2*layout.TEXT_HEIGHT)

        x, y = layout.XM+4*layout.XS, layout.YM
        stack = DevilsSolitaire_Foundation(
            x, y, self, suit=ANY_SUIT, base_rank=ANY_RANK, mod=13)
        tx, ty, ta, tf = layout.getTextAttr(stack, 'nw')
        font = self.app.getFont('canvas_default')
        stack.texts.misc = MfxCanvasText(self.canvas, tx, ty,
                                         anchor=ta, font=font)
        s.foundations.append(stack)

        x, y = self.width-layout.XS, layout.YM
        stack = AbstractFoundationStack(
            x, y, self,
            suit=ANY_SUIT, max_move=0, max_cards=104,
            max_accept=0, base_rank=ANY_RANK)
        layout.createText(stack, 'nw')
        s.foundations.append(stack)

        x, y = layout.XM, layout.YM+layout.YS
        for i in range(4):
            s.rows.append(Vague_RowStack(x, y, self))
            x += layout.XS
        x += layout.XS
        for i in range(4):
            s.rows.append(Vague_RowStack(x, y, self))
            x += layout.XS

        x, y = layout.XM+4*layout.XS, layout.YM+layout.YS
        stack = OpenStack(x, y, self)
        stack.CARD_YOFFSET = layout.YOFFSET
        s.reserves.append(stack)

        x, y = layout.XM+4.5*layout.XS, self.height-layout.YS
        s.talon = WasteTalonStack(x, y, self, max_rounds=3)
        layout.createText(s.talon, 'se')
        layout.createRoundText(s.talon, 'n')
        x -= layout.XS
        s.waste = DevilsSolitaire_WasteStack(x, y, self)
        layout.createText(s.waste, 'sw')

        layout.defaultStackGroups()

    def startGame(self):
        for i in range(8):
            self.s.talon.dealRow(rows=self.s.reserves, frames=0)
        self.startDealSample()
        self.s.talon.dealRow()
        self.s.talon.dealCards()

    def fillStack(self, stack):
        old_state = self.enterState(self.S_FILL)
        if stack in self.s.rows and not stack.cards:
            if not self.s.waste.cards:
                self.s.talon.dealCards()
            if self.s.waste.cards:
                self.s.waste.moveMove(1, stack)
        f0 = self.s.foundations[0]
        if len(f0.cards) == 12:
            self.moveMove(1, self.s.reserves[0], f0, frames=4)
            f1 = self.s.foundations[1]
            for i in range(13):
                self.moveMove(1, f0, f1, frames=4)
        self.leaveState(old_state)

    def updateText(self):
        if self.preview > 1:
            return
        f = self.s.foundations[0]
        r = self.s.reserves[0]
        if not r.cards:
            t = ''
        else:
            c = r.cards[-1]
            t = RANKS[(c.rank+1) % 13]
        f.texts.misc.config(text=t)


# ************************************************************************
# * Beacon
# ************************************************************************

class Beacon(Game):

    def createGame(self, rows=8):
        # create layout
        layout, s = Layout(self), self.s

        # set window
        playcards = 12
        self.setSize(
            layout.XM+rows*layout.XS,
            layout.YM + 3 * layout.YS + playcards * layout.YOFFSET)

        # create stacks
        x, y = layout.XM + (rows - 1) * layout.XS // 2, layout.YM
        stack = RK_FoundationStack(x, y, self, base_rank=ANY_RANK,
                                   max_cards=52, mod=13)
        s.foundations.append(stack)
        layout.createText(stack, 'ne')

        x, y = layout.XM, layout.YM+layout.YS
        for i in range(rows):
            s.rows.append(RK_RowStack(x, y, self, base_rank=NO_RANK, mod=13))
            x += layout.XS

        x, y = layout.XM, self.height-layout.YS
        s.talon = AutoDealTalonStack(x, y, self)
        layout.createText(s.talon, 'se')

        # define stack-groups
        layout.defaultStackGroups()

    def startGame(self):
        self._startDealNumRowsAndDealSingleRow(3)

    def fillStack(self, stack):
        if stack in self.s.rows and not stack.cards:
            if self.s.talon.cards:
                old_state = self.enterState(self.S_FILL)
                self.s.talon.flipMove()
                self.s.talon.moveMove(1, stack)
                self.leaveState(old_state)

    shallHighlightMatch = Game._shallHighlightMatch_RKW


# register the game
registerGame(GameInfo(36, Golf, "Golf",
                      GI.GT_GOLF, 1, 0, GI.SL_BALANCED,
                      altnames=("One Foundation",)))
registerGame(GameInfo(260, RelaxedGolf, "Relaxed Golf",
                      GI.GT_GOLF | GI.GT_RELAXED, 1, 0, GI.SL_BALANCED,
                      altnames=("Putt Putt",)))
registerGame(GameInfo(40, Elevator, "Elevator",
                      GI.GT_GOLF, 1, 0, GI.SL_BALANCED,
                      altnames=("Egyptian Solitaire", "Pyramid Golf")))
registerGame(GameInfo(98, BlackHole, "Black Hole",
                      GI.GT_GOLF | GI.GT_OPEN, 1, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(405, AllInARow, "All in a Row",
                      GI.GT_GOLF | GI.GT_OPEN, 1, 0, GI.SL_MOSTLY_SKILL,
                      altnames=("Quasar",)))
registerGame(GameInfo(720, Vague, "Vague",
                      GI.GT_1DECK_TYPE, 1, 0, GI.SL_MOSTLY_LUCK))
registerGame(GameInfo(723, DevilsSolitaire, "Devil's Solitaire",
                      GI.GT_2DECK_TYPE, 2, 2, GI.SL_BALANCED,
                      altnames=('Banner',)))
registerGame(GameInfo(764, Beacon, "Beacon",
                      GI.GT_1DECK_TYPE | GI.GT_ORIGINAL, 1, 0,
                      GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(941, BinaryStar, "Binary Star",
                      GI.GT_GOLF | GI.GT_OPEN, 2, 0, GI.SL_MOSTLY_SKILL,
                      altnames=("Black Holes",)))
