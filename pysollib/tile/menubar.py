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


from pysollib.ui.tktile.findcarddialog import connect_game_find_card_dialog
from pysollib.ui.tktile.findcarddialog import destroy_find_card_dialog
from pysollib.ui.tktile.fullpicturedialog import \
    connect_game_full_picture_dialog
from pysollib.ui.tktile.fullpicturedialog import destroy_full_picture_dialog
from pysollib.ui.tktile.menubar import PysolMenubarTkCommon
from pysollib.ui.tktile.solverdialog import connect_game_solver_dialog

from .tkwidget import MfxMessageDialog

# ************************************************************************
# * - create menubar
# * - update menubar
# * - menu actions
# ************************************************************************


class PysolMenubarTk(PysolMenubarTkCommon):
    def __init__(self, app, top, progress=None):
        PysolMenubarTkCommon.__init__(self, app, top, progress)

    def _connect_game_find_card_dialog(self, game):
        return connect_game_find_card_dialog(game)

    def _destroy_find_card_dialog(self):
        return destroy_find_card_dialog()

    def _connect_game_full_picture_dialog(self, game):
        return connect_game_full_picture_dialog(game)

    def _destroy_full_picture_dialog(self):
        return destroy_full_picture_dialog()

    def _connect_game_solver_dialog(self, game):
        return connect_game_solver_dialog(game)

    def _calcSelectGameDialog(self):
        from .selectgame import SelectGameDialog
        return SelectGameDialog

    def _calcSelectGameDialogWithPreview(self):
        from .selectgame import SelectGameDialogWithPreview
        return SelectGameDialogWithPreview

    def _calc_MfxMessageDialog(self):
        return MfxMessageDialog

    #
    # create the menubar
    #

    def mSelectCardsetDialog(self, *event):
        if self._cancelDrag(break_pause=False):
            return
        key = self.app.nextgame.cardset.index
        cs = self.app.selectCardset("Select deck", key)
        if not cs:
            return
        self.app.nextgame.cardset = cs
        self._cancelDrag()
        self.game.endGame(bookmark=1)
        self.game.quitGame(bookmark=1)
        self.updateMenus()
