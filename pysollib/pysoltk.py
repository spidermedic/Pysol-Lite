#!/usr/bin/env python
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

from pysollib.settings import TOOLKIT

if TOOLKIT == 'kivy':
    from pysollib.kivy.tkconst import *  # noqa: F401,F403
    from pysollib.kivy.tkutil import *  # noqa: F401,F403
    from pysollib.kivy.card import *  # noqa: F401,F403
    from pysollib.kivy.tkcanvas import *  # noqa: F401,F403
    from pysollib.kivy.tkwrap import *  # noqa: F401,F403
    from pysollib.kivy.findcarddialog import *  # noqa: F401,F403
    from pysollib.kivy.fullpicturedialog import *  # noqa: F401,F403
    from pysollib.kivy.tkwidget import *  # noqa: F401,F403
    from pysollib.kivy.tkhtml import *  # noqa: F401,F403
    from pysollib.kivy.edittextdialog import *  # noqa: F401,F403
    from pysollib.kivy.tkstats import *  # noqa: F401,F403
    from pysollib.kivy.playeroptionsdialog import *  # noqa: F401,F403
    from pysollib.kivy.timeoutsdialog import *  # noqa: F401,F403
    from pysollib.kivy.colorsdialog import *  # noqa: F401,F403
    from pysollib.kivy.fontsdialog import *  # noqa: F401,F403
    from pysollib.kivy.solverdialog import *  # noqa: F401,F403
    from pysollib.kivy.gameinfodialog import *  # noqa: F401,F403
    from pysollib.kivy.toolbarbuttonsdialog import *  # noqa: F401,F403
    from pysollib.kivy.toolbar import *  # noqa: F401,F403
    from pysollib.kivy.statusbar import *  # noqa: F401,F403
    from pysollib.kivy.progressbar import *  # noqa: F401,F403
    from pysollib.kivy.menubar import *  # noqa: F401,F403
    from pysollib.kivy.selectcardset import *  # noqa: F401,F403
    from pysollib.kivy.selecttree import *  # noqa: F401,F403

else:
    from pysollib.ui.tktile.tkconst import *  # noqa: F401,F403
    from pysollib.ui.tktile.tkutil import *  # noqa: F401,F403
    from pysollib.ui.tktile.card import *  # noqa: F401,F403
    from pysollib.ui.tktile.tkcanvas import *  # noqa: F401,F403
    from pysollib.ui.tktile.tkwrap import *  # noqa: F401,F403
    from pysollib.ui.tktile.findcarddialog import *  # noqa: F401,F403
    from pysollib.tile.tkwidget import *  # noqa: F401,F403
    from pysollib.tile.toolbarbuttonsdialog import *  # noqa: F401,F403
    from pysollib.tile.toolbar import *  # noqa: F401,F403
    from pysollib.tile.statusbar import *  # noqa: F401,F403
    from pysollib.tile.progressbar import *  # noqa: F401,F403
    from pysollib.tile.menubar import *  # noqa: F401,F403
    from pysollib.tile.selectcardset import *  # noqa: F401,F403
