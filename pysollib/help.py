#!/usr/bin/env python
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
from pysollib.settings import COPYRIGHT_LINES, PACKAGE_URL, TITLE, VERSION


# ************************************************************************
# *
# ************************************************************************

def help_about(app, timeout=0, sound=True):
    if sound:
        app.audio.playSample("about")
    strings = ("&Nice", "&Credits")
    if timeout:
        strings = ("&Enjoy",)
    title_version = f"{TITLE} v{VERSION}"
    copyright_lines = "\n".join(COPYRIGHT_LINES)
    # (text, justify) blocks: the copyright lines are left aligned, the rest
    # is centred
    parts = (
        (title_version + "\n\n"
         "Based on PySol, PySol Fan Club edition and PySolFC.", "center"),
        (copyright_lines, "left"),
        ("\nPySol Lite is free software, distributed under the terms of the\n"
         "GNU General Public License. It comes with NO WARRANTY.\n\n"
         "For more information about this application visit", "center"),
    )
    d = PysolAboutDialog(app, app.top, title=f"About {TITLE}",
                         timeout=timeout,
                         text="\n".join(p[0] for p in parts),
                         parts=parts,
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
    except OSError:
        MfxMessageDialog(app.top, title=f"{TITLE} HTML Problem",
                         text=f"Cannot find help document\n{document}",
                         bitmap="warning")
        return False
    # a file:// URL; as_uri() percent-encodes the space in "PySol Lite.app"
    return openURL(pathlib.Path(doc).resolve().as_uri())
