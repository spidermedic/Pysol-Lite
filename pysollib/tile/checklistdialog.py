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

from .tkwidget import MfxDialog, PysolCheckbutton


class ChecklistDialog(MfxDialog):
    """Choose several on/off options at once.

    ``groups`` is a list of groups of (key, label, ...) entries, shown with
    a divider between groups. ``values`` maps each key to its current
    True/False value, and keys in ``disabled`` are shown greyed out. After
    the dialog closes, ``values`` is replaced by the chosen values in
    ``self.values``.
    """

    def __init__(self, parent, title, groups, values, disabled=(), **kw):
        kw = self.initKw(kw)
        MfxDialog.__init__(self, parent, title, kw.resizable, kw.default)
        top_frame, bottom_frame = self.createFrames(kw)

        frame = ttk.Frame(top_frame)
        frame.pack(expand=True, fill='both', padx=5, pady=10)
        self.vars = {}
        row = 0
        for n, group in enumerate(groups):
            if n:
                ttk.Separator(frame, orient='horizontal').grid(
                    row=row, column=0, sticky='ew', padx=10, pady=6)
                row += 1
            for entry in group:
                key, label = entry[0], entry[1]
                var = tkinter.BooleanVar()
                var.set(bool(values.get(key)))
                self.vars[key] = var
                w = PysolCheckbutton(frame, variable=var, text=label)
                w.grid(row=row, column=0, sticky='w', padx=10, pady=1)
                if key in disabled:
                    w.state(['disabled'])
                row += 1
        frame.columnconfigure(0, weight=1)
        #
        focus = self.createButtons(bottom_frame, kw)
        self.mainloop(focus, kw.timeout)
        #
        self.values = dict((k, v.get()) for k, v in self.vars.items())

    def initKw(self, kw):
        kw = KwStruct(kw,
                      strings=("&OK", "&Cancel"), default=0,
                      padx=10, pady=10,
                      )
        return MfxDialog.initKw(self, kw)
