#!/usr/bin/env python
# -*- mode: python; coding: utf-8; -*-
# ---------------------------------------------------------------------------##
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

import tkinter
import tkinter.ttk as ttk

from pysollib.mfxutil import USE_PIL
from pysollib.mygettext import _
from pysollib.ui.tktile.tkconst import (
    ASSIST_GAME_OPTIONS, ASSIST_OPTIONS, AUTOMATIC_PLAY_OPTIONS, COMPOUNDS,
    PLAY_OPTIONS)
from pysollib.ui.tktile.tkutil import makeToplevel

ANIMATIONS = (("Off", 0), ("Slow", 3), ("Medium", 2), ("Fast", 1))
TOOLBAR_SIDES = (("Top", 1), ("Bottom", 2), ("Left", 3), ("Right", 4))
TOOLBAR_SIZES = (("Small", 0), ("Medium", 1), ("Large", 2))


class SettingsWindow:
    """The one window for all settings.

    It is not modal and applies every change at once, through the same
    menubar handlers the Options menu items used.
    """

    def __init__(self, menubar):
        self.mb = menubar
        self.top = makeToplevel(menubar.top, title=_("Settings"))
        self.top.wm_resizable(False, False)
        self.top.protocol("WM_DELETE_WINDOW", self.close)
        self.top.bind("<Escape>", self.close)
        self.top.bind("<FocusIn>", self._focusIn)
        self.auto = {}          # key -> checkbutton, greyed out per game
        tk = menubar.tkopt

        outer = ttk.Frame(self.top, padding=10)
        outer.pack(expand=True, fill="both")
        nb = self.nb = ttk.Notebook(outer)
        nb.pack(expand=True, fill="both")

        # General
        page = self._page(nb, _("General"))
        for key, label, handler in PLAY_OPTIONS:
            self._check(page, key, label, handler)
        self._check(page, "sound", _("Sound"), "mOptSound")
        ttk.Separator(page).pack(fill="x", pady=8)
        self.animations = self._choice(
            page, _("Animation speed:"),
            [(_(n), v) for n, v in ANIMATIONS], tk.animations,
            menubar.mOptAnimations)

        # Assist
        page = self._page(nb, _("Assist"))
        for key, label, handler in AUTOMATIC_PLAY_OPTIONS:
            self.auto[key] = self._check(page, key, label, handler)
        for key, label, handler in ASSIST_OPTIONS:
            self._check(page, key, label, handler)
        ttk.Separator(page).pack(fill="x", pady=8)
        ttk.Label(page, text=_("Specific games")).pack(anchor="w")
        for key, label, handler in ASSIST_GAME_OPTIONS:
            self._check(page, key, label, handler)

        # Appearance
        page = self._page(nb, _("Appearance"))
        row = ttk.Frame(page)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=_("Deck:")).pack(side="left")
        self.deck = ttk.Label(row)
        self.deck.pack(side="left", padx=6)
        ttk.Button(row, text=_("Choose"),
                   command=menubar.mSelectCardsetDialog).pack(side="right")
        self.backs_row = ttk.Frame(page)
        self.backs_row.pack(fill="x", pady=6)
        row = ttk.Frame(page)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=_("Background color:")).pack(side="left")
        self.swatch = tkinter.Label(row, width=3, relief="sunken", bd=1)
        self.swatch.pack(side="left", padx=6)
        ttk.Button(row, text=_("Choose"),
                   command=menubar.mSelectTableColor).pack(side="right")
        if USE_PIL:
            ttk.Separator(page).pack(fill="x", pady=8)
            self._check(page, "spread_stacks", _("Spread stacks"),
                        "mOptSpreadStacks")

        # Toolbar
        page = self._page(nb, _("Toolbar"))
        self.side = tkinter.IntVar()
        self.sidebox = self._choice(
            page, _("Position:"), [(_(n), v) for n, v in TOOLBAR_SIDES],
            self.side, self._setSide)
        self.size = self._choice(
            page, _("Icon size:"), [(_(n), v) for n, v in TOOLBAR_SIZES],
            tk.toolbar_size, menubar.mOptToolbarSize)
        self.compound = self._choice(
            page, _("Button style:"), [(_(n), v) for v, n in COMPOUNDS],
            tk.toolbar_compound, menubar.mOptToolbarCompound)
        ttk.Button(page, text=_("Visible buttons"),
                   command=menubar.mOptToolbarButtons).pack(
                       anchor="w", pady=8)

        self.refresh()

    # helpers

    def _page(self, nb, title):
        page = ttk.Frame(nb, padding=12)
        nb.add(page, text=title)
        return page

    def _check(self, page, key, label, handler):
        w = ttk.Checkbutton(page, text=_(label),
                            variable=getattr(self.mb.tkopt, key),
                            command=getattr(self.mb, handler))
        w.pack(anchor="w", pady=1)
        return w

    def _choice(self, page, label, choices, var, handler):
        """A labelled drop-down; ``choices`` is a list of (label, value)."""
        row = ttk.Frame(page)
        row.pack(fill="x", pady=3)
        ttk.Label(row, text=label).pack(side="left")
        box = ttk.Combobox(row, state="readonly", width=14,
                           values=[c[0] for c in choices])
        box.pack(side="right")
        box.choices = choices
        box.var = var

        def selected(event=None):
            var.set(choices[box.current()][1])
            handler()
        box.bind("<<ComboboxSelected>>", selected)
        return box

    def _setSide(self):
        self.mb.setToolbarSide(self.side.get())

    def _sync(self, box):
        value = box.var.get()
        for i, (label, v) in enumerate(box.choices):
            if str(v) == str(value):
                box.current(i)
                return

    # state

    def _focusIn(self, event=None):
        if event is None or event.widget is self.top:
            self.refresh()

    def refresh(self):
        """Bring the window up to date with the current game and options."""
        mb = self.mb
        if self.top is None:
            return
        usable = getattr(mb, "_autoplay_usable", {})
        for key, w in self.auto.items():
            w.state(["!disabled" if usable.get(key, True) else "disabled"])
        for box in (self.animations, self.size, self.compound):
            self._sync(box)
        self.side.set(getattr(mb, "_toolbar_side", 1))
        self._sync(self.sidebox)
        app = mb.app
        cs = getattr(app, "cardset", None)
        self.deck.config(text=cs.name if cs else "")
        try:
            self.swatch.config(bg=app.opt.colors["table"])
        except (tkinter.TclError, KeyError, AttributeError):
            pass
        self._fillBacks()

    def _fillBacks(self):
        for w in self.backs_row.winfo_children():
            w.destroy()
        images = getattr(self.mb.app, "images", None)
        backs = images.getCardbacks() if images else []
        if len(backs) < 2:
            return
        ttk.Label(self.backs_row, text=_("Back:")).pack(side="left")
        for i, back in enumerate(backs):
            ttk.Radiobutton(
                self.backs_row, style="Toolbutton", image=back.menu_image,
                variable=self.mb.tkopt.cardback, value=i,
                command=self.mb.mOptCardback).pack(side="left", padx=1)

    # window

    def show(self):
        self.refresh()
        self.top.deiconify()
        self.top.lift()
        self.top.focus_force()

    def close(self, event=None):
        top, self.top = self.top, None
        self.mb._settings = None
        top.destroy()
