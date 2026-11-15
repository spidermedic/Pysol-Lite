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
from pysollib.games.numerica import Numerica_Hint
from pysollib.layout import Layout
from pysollib.pysoltk import MfxCanvasText
from pysollib.stack import (
    OpenStack,
    OpenTalonStack,
    ReserveStack,
    SS_FoundationStack,
)
from pysollib.util import (
    ACE,
    KING,
    UNLIMITED_CARDS,
)
# ************************************************************************
# * Sly Fox
# ************************************************************************


class SlyFox_Foundation(SS_FoundationStack):
    def acceptsCards(self, from_stack, cards):
        if not SS_FoundationStack.acceptsCards(self, from_stack, cards):
            return False
        if from_stack in self.game.s.rows:
            if len(self.game.s.talon.cards) == 0:
                return True
            return self.game.num_dealled <= 0
        return True


class SlyFox_Talon(OpenTalonStack):
    rightclickHandler = OpenStack.rightclickHandler
    doubleclickHandler = OpenStack.doubleclickHandler

    def moveMove(self, ncards, to_stack, frames=-1, shadow=-1):
        old_state = self.game.enterState(self.game.S_FILL)
        self.game.saveStateMove(2 | 16)            # for undo
        if old_state == self.game.S_PLAY and to_stack in self.game.s.rows:
            n = max(self.game.num_dealled, 0)
            self.game.num_dealled = (n+1) % 20
        self.game.saveStateMove(1 | 16)            # for redo
        self.game.leaveState(old_state)
        OpenTalonStack.moveMove(self, ncards, to_stack, frames, shadow)


class SlyFox_RowStack(ReserveStack):
    def acceptsCards(self, from_stack, cards):
        if not ReserveStack.acceptsCards(self, from_stack, cards):
            return False
        return from_stack is self.game.s.talon


class SlyFox(Game):
    Hint_Class = Numerica_Hint

    num_dealled = -1

    def createGame(self):
        l, s = Layout(self), self.s
        self.setSize(l.XM+9*l.XS, l.YM+4*l.YS)

        x, y = l.XM, l.YM
        s.talon = SlyFox_Talon(x, y, self)
        s.waste = s.talon
        l.createText(s.talon, 'ne')
        tx, ty, ta, _ = l.getTextAttr(s.talon, "ss")
        font = self.app.getFont("canvas_default")
        self.texts.misc = MfxCanvasText(self.canvas, tx, ty,
                                        anchor=ta, font=font)

        y = l.YM
        for i in range(4):
            x = l.XM+1.5*l.XS
            for _ in range(5):
                stack = SlyFox_RowStack(x, y, self, max_cards=UNLIMITED_CARDS)
                stack.CARD_YOFFSET = 0
                s.rows.append(stack)
                x += l.XS
            y += l.YS

        x, y = self.width-2*l.XS, l.YM
        for i in range(4):
            s.foundations.append(SlyFox_Foundation(x, y, self, suit=i))
            s.foundations.append(SlyFox_Foundation(x+l.XS, y, self, suit=i,
                                                   base_rank=KING, dir=-1))
            y += l.YS

        l.defaultStackGroups()

    def _shuffleHook(self, cards):
        return self._shuffleHookMoveToTop(
            cards,
            lambda c: (c.rank in (ACE, KING) and c.deck == 0,
                       (c.suit, c.rank)))

    def startGame(self):
        self.num_dealled = -1
        self.s.talon.dealRow(rows=self.s.foundations, frames=0)
        self.startDealSample()
        self.s.talon.dealRow()
        self.s.talon.fillStack()

    def _restoreGameHook(self, game):
        self.num_dealled = game.loadinfo.num_dealled

    def _loadGameHook(self, p):
        self.loadinfo.addattr(num_dealled=p.load())

    def _saveGameHook(self, p):
        p.dump(self.num_dealled)

    def setState(self, state):
        # restore saved vars (from undo/redo)
        self.num_dealled = state[0]

    def getState(self):
        # save vars (for undo/redo)
        return [self.num_dealled]

    def fillStack(self, stack):
        if self.num_dealled == -1 and stack in self.s.rows and not stack.cards:
            old_state = self.enterState(self.S_FILL)
            self.s.talon.moveMove(1, stack)
            self.leaveState(old_state)

    def updateText(self):
        if self.preview > 1:
            return
        n = max(self.num_dealled, 0)
        text = str(n)+'/20'
        self.texts.misc.config(text=text)


# register the game
registerGame(GameInfo(610, SlyFox, "Sly Fox",
                      GI.GT_NUMERICA, 2, 0, GI.SL_BALANCED))
