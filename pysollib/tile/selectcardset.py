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

import os
import tkinter.ttk as ttk

from pysollib.mfxutil import KwStruct, USE_PIL
from pysollib.mygettext import _
from pysollib.resource import CSI, getNaturalSortKey
from pysollib.speech import Speech
from pysollib.ui.tktile.selecttree import SelectDialogTreeData
from pysollib.ui.tktile.tkcanvas import MfxCanvasImage
from pysollib.ui.tktile.tkutil import bind, loadImage
from pysollib.util import CARDSET

from .selecttree import SelectDialogTreeCanvas
from .selecttree import SelectDialogTreeLeaf
from .tkwidget import MfxDialog, MfxScrolledCanvas, PysolText


# ************************************************************************
# * Nodes
# ************************************************************************

class SelectCardsetLeaf(SelectDialogTreeLeaf):
    pass


# ************************************************************************
# * Tree database
# ************************************************************************

class SelectCardsetData(SelectDialogTreeData):
    def __init__(self, manager, key):
        SelectDialogTreeData.__init__(self)
        self.all_objects = manager.getAllSortedByName()
        self.all_objects = [obj for obj in self.all_objects if not obj.error]
        self.no_contents = [SelectCardsetLeaf(
            None, None, _("(no cardsets)"), key=None), ]
        # one flat list, in alphanumeric order
        self.rootnodes = [
            SelectCardsetLeaf(None, None, text=obj.name, key=obj.index)
            for obj in sorted(self.all_objects,
                              key=lambda cs: getNaturalSortKey(cs.name))
        ] or self.no_contents


# ************************************************************************
# * Canvas that shows the tree
# ************************************************************************

class SelectCardsetTree(SelectDialogTreeCanvas):
    data = None


# ************************************************************************
# * Dialog
# ************************************************************************

class SelectCardsetDialogWithPreview(MfxDialog):
    Tree_Class = SelectCardsetTree
    TreeDataHolder_Class = SelectCardsetTree
    TreeData_Class = SelectCardsetData

    def __init__(self, parent, title, app, manager, key=None, **kw):
        kw = self.initKw(kw)
        MfxDialog.__init__(self, parent, title, kw.resizable, kw.default)
        top_frame, bottom_frame = self.createFrames(kw)
        self.createBitmaps(top_frame, kw)
        #
        if key is None:
            key = manager.getSelected()
        self.manager = manager
        self.key = key
        self.app = app
        # padx, pady = kw.padx, kw.pady
        padx, pady = 4, 4
        if self.TreeDataHolder_Class.data is None:
            self.TreeDataHolder_Class.data = self.TreeData_Class(manager, key)
        #

        pw = parent.winfo_width()
        ph = parent.winfo_height()
        py = parent.winfo_y()
        px = parent.winfo_x()

        h = int(ph * .8)
        w = int(pw * .8)
        w1 = int(min(275, pw / 2.5))
        geometry = ("%dx%d+%d+%d" % (w, h, px + ((pw - w) / 2),
                                     py + (int((ph - h) / 1.5))))
        self.top.wm_minsize(400, 200)

        paned_window = ttk.PanedWindow(top_frame, orient='horizontal')
        paned_window.pack(expand=True, fill='both', padx=8, pady=8)
        left_frame = ttk.Frame(paned_window)
        right_frame = ttk.Frame(paned_window)
        paned_window.add(left_frame)
        paned_window.add(right_frame)

        # Tree
        font = app.getFont("default")
        self.tree = self.Tree_Class(self, left_frame, key=key,
                                    default=kw.default,
                                    font=font, width=w1)
        self.tree.frame.grid(row=0, column=0, sticky='nsew',
                             padx=padx, pady=pady)

        #
        left_frame.rowconfigure(0, weight=1)
        left_frame.columnconfigure(0, weight=1)
        #
        self.preview = MfxScrolledCanvas(right_frame)
        bind(self.preview.parent, '<Configure>',
             lambda e: self._configureHandler())
        self.preview.setTile(app, app.tabletile_index,
                             app.opt.tabletile_scale_method, force=True)
        self.preview.pack(fill='both', expand=True, padx=padx, pady=pady)
        self.preview.canvas.preview = 1
        # create a preview of the current state
        self.preview_key = -1
        self.preview_images = []
        self.scale_images = []
        self.updatePreview(key, overrideScale=True)
        #
        focus = self.createButtons(bottom_frame, kw)
        focus = self.tree.frame
        self.mainloop(focus, kw.timeout, geometry=geometry)

    def destroy(self):
        self.tree.updateNodesWithTree(self.tree.rootnodes, None)
        self.tree.destroy()
        self.preview.unbind_all()
        self.preview_images = []
        MfxDialog.destroy(self)

    def initKw(self, kw):
        s = (_("&Info"), 10)
        kw = KwStruct(kw,
                      strings=(s, 'sep',
                               _("&Select"), _("&Cancel"),),
                      default=0,
                      resizable=True,
                      )
        return MfxDialog.initKw(self, kw)

    def mDone(self, button):
        if button in (0, 1):            # Load/Cancel
            self.key = self.tree.selection_key
            self.tree.n_expansions = 1  # save xyview in any case

            if button == 0:
                cardset = self.app.cardset_manager.get(self.key)
                if self.app.game is not None:
                    gi = self.app.getGameInfo(self.app.game.id)
                else:
                    gi = self.app.getGameInfo(self.app.nextgame.id)
                cs, cs_update_flag, t = \
                    self.app.getCompatibleCardset(gi, cardset, trychange=False)

                if cs is None:
                    self.app.requestCompatibleCardsetTypeDialog(cardset, gi, t)
                    return

        if button == 10:                # Info
            cs = self.manager.get(self.tree.selection_key)
            if not cs:
                return
            # title = CARDSET+" "+cs.name
            title = CARDSET.capitalize()+" "+cs.name
            CardsetInfoDialog(self.top, title=title, cardset=cs,
                              images=self.preview_images)
            return
        MfxDialog.mDone(self, button)

    _resizeHandlerID = None

    def _resizeHandler(self):
        self._resizeHandlerID = None
        self.updatePreview()

    def _configureHandler(self, event=None):
        if False:  # if not USE_PIL:
            return
        if not self.app:
            return
        if self._resizeHandlerID:
            self.preview.canvas.after_cancel(self._resizeHandlerID)
        self._resizeHandlerID = self.preview.canvas.after(300,
                                                          self._resizeHandler)
        # should return EVENT_HANDLED or EVENT_PROPAGATE explicitly.

    def updatePreview(self, key=None, overrideScale=False):
        if not hasattr(self, 'preview_key') or not hasattr(self, 'preview'):
            return
        if key == self.preview_key:
            return
        if key is None:
            key = self.key
        canvas = self.preview.canvas
        canvas.deleteAllItems()
        self.preview_images = []
        cs = self.manager.get(key)
        if not cs:
            self.preview_key = -1
            return
        names, columns = cs.getPreviewCardNames()

        try:
            # ???names, columns = cs.getPreviewCardNames()
            for n in names:
                f = os.path.join(cs.dir, n + cs.ext)
                self.preview_images.append(loadImage(file=f))
        except Exception:
            self.preview_key = -1
            self.preview_images = []
            return
        i, x, y, sx, sy, dx, dy = 0, 10, 10, 0, 0, cs.CARDW + 10, cs.CARDH + 10
        cx, cy = 0, 0
        if USE_PIL:
            if not overrideScale:
                vw = canvas.winfo_width()
                vh = canvas.winfo_height()
                iw = dx * columns
                ih = dy * 4
                xf = max(float(vw - 10) / iw, .01)
                yf = max(float(vh - 10) / ih, .01)
                xf = yf = min(xf, yf)
                if self.app.opt.center_layout:
                    cx, cy = self.app.images.getCenterOffset(vw - 10, vh - 10,
                                                             iw, ih, xf, yf,
                                                             True)
                    cx = int(cx * xf)
                    cy = int(cy * yf)
                    x += cx
                    y += cy
            else:
                xf = yf = 1.0
            dx = int(dx * xf)
            dy = int(dy * yf)
            self.scale_images = []
        for image in self.preview_images:
            if USE_PIL:
                image = image.resize(xf, yf)
                self.scale_images.append(image)
            MfxCanvasImage(canvas, x, y, anchor="nw", image=image)
            sx, sy = max(x, sx), max(y, sy)
            i = i + 1
            if i % columns == 0:
                x, y = 10 + cx, y + dy
            else:
                x += dx
        canvas.config(scrollregion=(0, 0, sx+dx, sy+dy),
                      width=sx+dx, height=sy+dy)
        # canvas.config(xscrollincrement=dx, yscrollincrement=dy)
        canvas.event_generate('<Configure>')  # update bg image
        self.preview_key = key
        self.key = key

# ************************************************************************
# * Cardset Info
# ************************************************************************


class CardsetInfoDialog(MfxDialog):
    def __init__(self, parent, title, cardset, images, **kw):
        kw = self.initKw(kw)
        MfxDialog.__init__(self, parent, title, kw.resizable, kw.default)
        top_frame, bottom_frame = self.createFrames(kw)
        self.createBitmaps(top_frame, kw)
        frame = ttk.Frame(top_frame)
        frame.pack(fill="both", expand=True, padx=5, pady=10)
        #
        #
        row = 0
        self.speech = Speech()
        info_frame = ttk.LabelFrame(frame, text=_('About cardset'))
        info_frame.grid(row=row, column=0, columnspan=2, sticky='ew',
                        padx=0, pady=5, ipadx=5, ipady=5)
        row += 1
        styles = nationalities = year = None
        if cardset.si.styles:
            styles = '\n'.join(sorted([CSI.STYLE[i]
                                       for i in cardset.si.styles]))
        if cardset.si.nationalities:
            nationalities = '\n'.join(sorted([CSI.NATIONALITY[i]
                                              for i in
                                              cardset.si.nationalities]))
        if cardset.year:
            year = str(cardset.year)
        frow = 0
        screenreadertext = ""
        for n, t in (
            (_('Type:'),          CSI.TYPE[cardset.type]),
            (_('Styles:'),        styles),
            (_('Nationality:'),   nationalities),
            (_('Year:'),          year),
            (_('Num. cards:'),    str(cardset.ncards)),
            (_('Size:'), '%d x %d (%s)' % (cardset.CARDW, cardset.CARDH,
                                           CSI.SIZE_NAME.get(cardset.si.size)))
                ):
            if t is not None:
                label = ttk.Label(info_frame, text=n,
                                  anchor='w', justify='left')
                label.grid(row=frow, column=0, sticky='nw', padx=4)
                label = ttk.Label(info_frame, text=t,
                                  anchor='w', justify='left')
                label.grid(row=frow, column=1, sticky='nw', padx=4)
                frow += 1
                screenreadertext += n + '\r\n' + t + '\r\n\r\n'
        parent.after(600, lambda: self.speech.speak(screenreadertext))
        if images:
            try:
                from random import choice
                im = choice(images)
                f = os.path.join(cardset.dir, cardset.backname)
                self.back_image = loadImage(file=f)  # store the image
                label = ttk.Label(info_frame, image=im, padding=5)
                label.grid(row=0, column=2, rowspan=frow+1, sticky='ne')
                label = ttk.Label(info_frame, image=self.back_image,
                                  padding=(0, 5, 5, 5))  # left margin = 0
                label.grid(row=0, column=3, rowspan=frow+1, sticky='ne')

                info_frame.columnconfigure(2, weight=1)
                info_frame.rowconfigure(frow, weight=1)
            except Exception:
                pass

            row += 1

        # bg = top_frame["bg"]
        bg = 'white'
        text_w = PysolText(frame, bd=1, relief="sunken", wrap="word",
                           padx=4, width=66, height=8, bg=bg)
        text_w.grid(row=row, column=0, sticky='nsew')
        sb = ttk.Scrollbar(frame)
        sb.grid(row=row, column=1, sticky='ns')
        text_w.configure(yscrollcommand=sb.set)
        sb.configure(command=text_w.yview)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        #
        text = ''
        fn = os.path.join(cardset.dir, "COPYRIGHT")
        try:
            with open(fn, "rt", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except Exception:
            pass
        if text:
            text_w.config(state="normal")
            text_w.insert("insert", text)
        text_w.config(state="disabled")
        #
        focus = self.createButtons(bottom_frame, kw)
        # focus = text_w
        self.mainloop(focus, kw.timeout)
