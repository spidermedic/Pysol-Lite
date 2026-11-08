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

import tkinter
import tkinter.ttk as ttk

from pysollib.mfxutil import KwStruct
from pysollib.ui.tktile.tkconst import TOOLBAR_BUTTONS

from .tkwidget import MfxDialog, PysolCheckbutton


class ToolbarButtonsDialog(MfxDialog):
    """Choose which buttons the toolbar shows, several at once."""

    def __init__(self, parent, title, app, **kw):
        kw = self.initKw(kw)
        MfxDialog.__init__(self, parent, title, kw.resizable, kw.default)
        top_frame, bottom_frame = self.createFrames(kw)

        frame = ttk.Frame(top_frame)
        frame.pack(expand=True, fill='both', padx=5, pady=10)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        self.vars = {}
        for i, w in enumerate(TOOLBAR_BUTTONS):
            var = tkinter.BooleanVar()
            var.set(bool(app.opt.toolbar_vars.get(w, False)))
            self.vars[w] = var
            PysolCheckbutton(frame, variable=var, text=(w.capitalize())
                             ).grid(row=i // 2, column=i % 2, sticky='w',
                                    padx=10, pady=2)
        #
        focus = self.createButtons(bottom_frame, kw)
        self.mainloop(focus, kw.timeout)
        #
        self.visible = dict((w, v.get()) for w, v in self.vars.items())

    def initKw(self, kw):
        kw = KwStruct(kw,
                      strings=("&OK", "&Cancel"), default=0,
                      padx=10, pady=10,
                      )
        return MfxDialog.initKw(self, kw)
