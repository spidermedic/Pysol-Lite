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

import os
import tkinter

from pysollib.resource import CSI
from pysollib.settings import TITLE
from pysollib.ui.tktile.tkcanvas import MfxCanvas, MfxCanvasGroup
from pysollib.ui.tktile.tkcanvas import MfxCanvasImage, MfxCanvasRectangle
from pysollib.ui.tktile.tkutil import after, after_cancel
from pysollib.ui.tktile.tkutil import bind, makeImage, unbind_destroy


EMBLEMS_SIZE = (38, 34)


class FindCardDialog(tkinter.Toplevel):
    CARD_IMAGES = {}  # key: (type, rank, suit)

    HINT = ("Point at a card, or use the arrow keys, to find it on the "
            "table. Click or press Enter to keep it marked.")

    def __init__(self, parent, game, dir):
        tkinter.Toplevel.__init__(self)
        self.title("Find Card")
        self.wm_resizable(False, False)
        self.cardsettype = ''
        self.dir = dir
        self.images_dir = ''
        self.label_width, self.label_height = EMBLEMS_SIZE

        # the hint is packed first so the canvas cannot squeeze it out
        self.hint = tkinter.Label(
            self, text=self.HINT,
            bg='white', fg='#555555', anchor='center', justify='center')
        self.hint.pack(side='bottom', fill='x', pady=(0, 4))
        self.canvas = MfxCanvas(self, bg='white')
        self.canvas.pack(expand=True, fill='both')
        #
        self.groups = []
        self.cells = []         # one dict per emblem (see createCardLabel)
        self.shown = {}         # cell index -> highlight items on the table
        self.hovered = None     # cell under the pointer
        self.selected = None    # cell chosen with the keyboard (or last click)
        self.pinned = None      # cell kept marked by a click or Enter
        self.keyboard = False   # the selection counts as shown
        self.busy = False
        self.dirty = False
        self.poll = None
        self.signature = None
        self.connectGame(game)
        #
        bind(self, "WM_DELETE_WINDOW", self.destroy)
        bind(self, "<Escape>", self.escapeEvent)
        bind(self, "<Left>", lambda e: self.moveSelection(-1, 0))
        bind(self, "<Right>", lambda e: self.moveSelection(1, 0))
        bind(self, "<Up>", lambda e: self.moveSelection(0, -1))
        bind(self, "<Down>", lambda e: self.moveSelection(0, 1))
        for key in ("<Return>", "<KP_Enter>", "<space>"):
            bind(self, key, self.pinEvent)
        #

    def createCardLabel(self, suit, rank, x0, y0):
        dx, dy = self.label_width, self.label_height
        dir = self.images_dir
        canvas = self.canvas
        group = MfxCanvasGroup(canvas)
        #
        im = FindCardDialog.CARD_IMAGES.get((self.cardsettype, rank, suit))
        if im is None:
            r = '%02d' % (rank+1)
            suitletters = CSI.TYPE_SUITS[self.cardsettype]
            if suit < len(suitletters):
                s = suitletters[suit]
            else:
                s = "z"
            fn = os.path.join(dir, r+s+'.png')
            im = makeImage(file=fn)
            FindCardDialog.CARD_IMAGES[(self.cardsettype, rank, suit)] = im
        cim = MfxCanvasImage(canvas, x0, y0, image=im, anchor='nw')
        cim.addtag(group)
        cim.lower()
        #
        rect_width = 4
        x1, y1 = x0+dx, y0+dy
        rect = MfxCanvasRectangle(self.canvas, x0+1, y0+1, x1-1, y1-1,
                                  width=rect_width,
                                  fill=None,
                                  outline='red',
                                  state='hidden'
                                  )
        rect.addtag(group)
        #
        n = len(self.cells)
        self.cells.append(dict(suit=suit, rank=rank, rect=rect, x=x0, y=y0))
        bind(group, '<Enter>', lambda e, n=n: self.enterEvent(n))
        bind(group, '<Leave>', lambda e, n=n: self.leaveEvent(n))
        bind(group, '<Button-1>', lambda e, n=n: self.clickEvent(n))
        self.groups.append(group)

    def connectGame(self, game):
        self.clearHighlights()
        for group in self.groups:
            unbind_destroy(group)
        self.groups = []
        self.cells = []
        self.hovered = self.selected = self.pinned = None
        self.keyboard = False
        self.cardsettype = game.gameinfo.category
        cs_type = CSI.TYPE_ID[self.cardsettype]
        #
        # self.images_dir = dir
        self.images_dir = os.path.join(self.dir, 'finder', cs_type)
        self.canvas.delete('all')
        self.game = game
        suits = game.gameinfo.suits
        ranks = game.gameinfo.ranks
        trumps = game.gameinfo.trumps
        dx, dy = self.label_width, self.label_height
        uniq_suits = []
        i = 0
        for suit in suits:
            if suit in uniq_suits:
                continue
            uniq_suits.append(suit)
            j = 0
            for rank in ranks:
                x, y = dx*j+2, dy*i+2
                self.createCardLabel(suit=suit, rank=rank, x0=x, y0=y)
                j += 1
            i += 1

        if len(trumps) > 0:
            if len(ranks) == 0:
                j = min(10, len(trumps))
            else:
                i += .5
            k = 0
            for trump in trumps:
                x, y = dx * k + 2, dy * i + 2
                self.createCardLabel(suit=len(suits), rank=trump, x0=x, y0=y)
                k += 1
                if k >= j:
                    k = 0
                    i += 1
            if k > 0:
                i += 1

        w, h = dx*j+2, dy*i+2
        self.canvas.config(width=w, height=h)
        self.hint.config(wraplength=w - 8)
        self.wm_iconname(TITLE + " - " + game.getTitleName())
        self.wm_geometry('')            # cancel user-specified geometry

    # ----------------------------------------------------------------
    # what is marked: the cell under the pointer, the pinned cell, and
    # (while the keyboard is in use) the selected cell
    # ----------------------------------------------------------------

    def wanted(self):
        w = set()
        if self.hovered is not None:
            w.add(self.hovered)
        if self.pinned is not None:
            w.add(self.pinned)
        if self.keyboard and self.selected is not None:
            w.add(self.selected)
        return w

    def refresh(self):
        # Showing or hiding updates the canvas, which can deliver another
        # Enter or Leave event on the way; such an event only changes the
        # state and the loop below catches up.
        if self.busy:
            self.dirty = True
            return
        self.busy = True
        try:
            while True:
                self.dirty = False
                wanted = self.wanted()
                for n in list(self.shown):
                    if n not in wanted:
                        self.hideCell(n)
                for n in wanted:
                    if n not in self.shown:
                        self.showCell(n)
                if not self.dirty:
                    break
        finally:
            self.busy = False
        if self.shown and self.poll is None:
            self.signature = self.getSignature()
            self.poll = after(self, 200, self.pollEvent)
        elif not self.shown and self.poll is not None:
            after_cancel(self.poll)
            self.poll = None

    def showCell(self, n):
        if self.game.demo:
            return
        cell = self.cells[n]
        items = self.game.highlightCard(cell['suit'], cell['rank'])
        self.shown[n] = items or []
        cell['rect'].config(state='normal')
        self.canvas.update_idletasks()

    def hideCell(self, n):
        for i in self.shown.pop(n):
            i.delete()
        self.cells[n]['rect'].config(state='hidden')
        if self.game.canvas:
            self.game.canvas.update_idletasks()
        self.canvas.update_idletasks()

    def clearHighlights(self):
        # forget everything that is shown (the game may be gone already)
        for items in self.shown.values():
            for i in items:
                try:
                    i.delete()
                except Exception:
                    pass
        self.shown = {}
        if self.poll is not None:
            after_cancel(self.poll)
            self.poll = None

    def getSignature(self):
        # the marks sit at fixed places on the table: when a card moves
        # or the cards change size they have to be drawn again
        try:
            g = self.game
            return (g.moves.index, g.canvas.winfo_width(),
                    g.canvas.winfo_height(), g.app.images.getSize())
        except Exception:
            return None

    def pollEvent(self):
        self.poll = None
        if not self.shown:
            return
        sig = self.getSignature()
        if sig != self.signature:
            self.signature = sig
            for n in list(self.shown):
                self.hideCell(n)
            self.refresh()
        if self.shown and self.poll is None:
            self.poll = after(self, 200, self.pollEvent)

    # ----------------------------------------------------------------
    # events
    # ----------------------------------------------------------------

    def enterEvent(self, n):
        if self.game.demo:
            return
        self.keyboard = False
        self.hovered = n
        self.refresh()

    def leaveEvent(self, n):
        if self.hovered == n:
            self.hovered = None
            self.refresh()

    def clickEvent(self, n):
        self.keyboard = False
        self.selected = n
        self.pinned = None if self.pinned == n else n
        self.refresh()

    def pinEvent(self, event=None):
        if not self.cells:
            return
        if self.selected is None:
            self.selected = 0
        self.keyboard = True
        self.pinned = None if self.pinned == self.selected else self.selected
        self.refresh()

    def moveSelection(self, dx, dy):
        if not self.cells:
            return
        self.keyboard = True
        if self.selected is None:
            self.selected = 0
        elif dx:
            # the emblems are created row by row, so left and right
            # follow that order
            n = self.selected + dx
            self.selected = max(0, min(len(self.cells) - 1, n))
        else:
            cur = self.cells[self.selected]
            rows = [c for c in self.cells if (c['y'] - cur['y']) * dy > 0]
            if rows:
                ydist = min(abs(c['y'] - cur['y']) for c in rows)
                row = [c for c in rows if abs(c['y'] - cur['y']) == ydist]
                best = min(row, key=lambda c: abs(c['x'] - cur['x']))
                self.selected = self.cells.index(best)
        self.refresh()

    def escapeEvent(self, event=None):
        if self.pinned is not None:
            self.pinned = None
            self.refresh()
        else:
            self.destroy()

    def destroy(self, *args):
        for group in self.groups:
            unbind_destroy(group)
        unbind_destroy(self)
        self.wm_withdraw()
        self.clearHighlights()
        tkinter.Toplevel.destroy(self)


def place_beside(dialog, parent):
    """Put the dialog next to the main window (right side, else left side)
    so it does not cover the cards; fall back to the bottom right corner
    inside the window when the screen has no room beside it."""
    dialog.update_idletasks()
    dw, dh = dialog.winfo_reqwidth(), dialog.winfo_reqheight()
    px, py = parent.winfo_rootx(), parent.winfo_rooty()
    pw = parent.winfo_width()
    sw, sh = dialog.winfo_screenwidth(), dialog.winfo_screenheight()
    gap = 12
    if px + pw + gap + dw <= sw:
        x = px + pw + gap
    elif px - gap - dw >= 0:
        x = px - gap - dw
    else:
        x = px + pw - dw - gap
    y = max(0, min(py, sh - dh - 40))
    dialog.wm_geometry("+%d+%d" % (x, y))


find_card_dialog = None


def create_find_card_dialog(parent, game, dir):
    global find_card_dialog
    try:
        find_card_dialog.wm_deiconify()
        find_card_dialog.tkraise()
        find_card_dialog.focus_set()
    except Exception:
        # traceback.print_exc()
        find_card_dialog = FindCardDialog(parent, game, dir)
        place_beside(find_card_dialog, parent)


def connect_game_find_card_dialog(game):
    try:
        find_card_dialog.connectGame(game)
    except Exception:
        pass


def raise_find_card_dialog(game):
    try:
        if game.app.opt.topmost_dialogs:
            find_card_dialog.tkraise()
            find_card_dialog.attributes("-topmost", True)
        else:
            find_card_dialog.attributes("-topmost", False)
    except Exception:
        pass


def unraise_find_card_dialog():
    try:
        find_card_dialog.attributes("-topmost", False)
    except Exception:
        pass


def destroy_find_card_dialog():
    global find_card_dialog
    try:
        find_card_dialog.destroy()
    except Exception:
        # traceback.print_exc()
        pass
    find_card_dialog = None
