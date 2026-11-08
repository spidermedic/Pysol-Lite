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
from pysollib.mygettext import _
from pysollib.ui.tktile.tkconst import ASSIST_OPTIONS, ASSIST_GAME_OPTIONS

from .tkwidget import MfxDialog, PysolCheckbutton


class AssistLevelDialog(MfxDialog):
    """Choose the assist options, several at once.

    ``values`` maps each option key to its current True/False value.
    """

    def __init__(self, parent, title, app, values, **kw):
        kw = self.initKw(kw)
        MfxDialog.__init__(self, parent, title, kw.resizable, kw.default)
        top_frame, bottom_frame = self.createFrames(kw)

        frame = ttk.Frame(top_frame)
        frame.pack(expand=True, fill='both', padx=5, pady=10)
        self.vars = {}
        row = 0
        for key, label, handler in ASSIST_OPTIONS:
            row = self._addCheck(frame, row, key, label, values)
        ttk.Separator(frame, orient='horizontal').grid(
            row=row, column=0, sticky='ew', padx=10, pady=6)
        row += 1
        for key, label, handler in ASSIST_GAME_OPTIONS:
            row = self._addCheck(frame, row, key, label, values)
        frame.columnconfigure(0, weight=1)
        #
        focus = self.createButtons(bottom_frame, kw)
        self.mainloop(focus, kw.timeout)
        #
        self.values = dict((k, v.get()) for k, v in self.vars.items())

    def _addCheck(self, frame, row, key, label, values):
        var = tkinter.BooleanVar()
        var.set(bool(values.get(key)))
        self.vars[key] = var
        PysolCheckbutton(frame, variable=var, text=_(label)
                         ).grid(row=row, column=0, sticky='w',
                                padx=10, pady=1)
        return row + 1

    def initKw(self, kw):
        kw = KwStruct(kw,
                      strings=(_("&OK"), _("&Cancel")), default=0,
                      padx=10, pady=10,
                      )
        return MfxDialog.initKw(self, kw)
