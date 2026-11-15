#!/usr/bin/env python
# -*- mode: python; coding: utf-8; -*-
# ---------------------------------------------------------------------------##
#
#  Copyright (C) 1998-2003 Markus Franz Xaver Johannes Oberhumer
#  Copyright (C) 2003 Mt. Hood Playing Card Co.
#  Copyright (C) 2005-2009 Skomoroh
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ---------------------------------------------------------------------------##


# imports

# PySol imports
import pathlib

from pysollib.mfxutil import openURL
from pysollib.pysoltk import MfxMessageDialog
from pysollib.pysoltk import PysolAboutDialog
from pysollib.settings import PACKAGE_URL, TITLE, VERSION


# ************************************************************************
# *
# ************************************************************************

def help_about(app, timeout=0, sound=True):
    if sound:
        app.audio.playSample("about")
    strings = ("&Nice", "&Credits")
    if timeout:
        strings = ("&Enjoy",)
    title_version = "%s v%s" % (TITLE, VERSION)
    d = PysolAboutDialog(app, app.top, title="About %s" % TITLE,
                         timeout=timeout,
                         text=('''%(title)s

Based on PySol, PySol Fan Club edition and PySolFC.
Copyright (C) 1998 - 2003 Markus F.X.J. Oberhumer.
Copyright (C) 2003 Mt. Hood Playing Card Co.
Copyright (C) 2005 - 2009 Skomoroh.
Copyright (C) 2020 - 2026 PySolFC contributors.
Modifications Copyright (C) 2026 the PySol Lite authors.
All Rights Reserved.

PySol is free software distributed under the terms
of the GNU General Public License.

For more information about this application visit''') %
                         {'title': title_version},
                         url=PACKAGE_URL,
                         image=app.gimages.logos[1],
                         strings=strings, default=0,
                         separator=True)
    if d.status == 0 and d.button == 1:
        help_html(app, "credits.html", "html")
    return d.status


# ************************************************************************
# *
# ************************************************************************

def help_html(app, document, dir_, top=None):
    """Open a help page in the default web browser."""
    if not document:
        return False
    try:
        doc = app.dataloader.findFile(document, dir_)
    except EnvironmentError:
        MfxMessageDialog(app.top, title="%s HTML Problem" % TITLE,
                         text="Cannot find help document\n%s" % document,
                         bitmap="warning")
        return False
    # a file:// URL; as_uri() percent-encodes the space in "PySol Lite.app"
    return openURL(pathlib.Path(doc).resolve().as_uri())
