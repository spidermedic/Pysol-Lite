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

import os

from pysollib.help import help_about, help_html
from pysollib.mfxutil import Struct
from pysollib.pysolrandom import construct_random
from pysollib.pysoltk import GameInfoDialog
from pysollib.pysoltk import MfxMessageDialog, MfxSimpleEntry
from pysollib.pysoltk import PysolMenubarTk, PysolToolbarTk
from pysollib.pysoltk import ToolbarButtonsDialog
from pysollib.pysoltk import create_find_card_dialog
from pysollib.pysoltk import create_full_picture_dialog
from pysollib.pysoltk import raise_find_card_dialog
from pysollib.pysoltk import raise_full_picture_dialog
from pysollib.settings import TITLE


# ************************************************************************
# * menubar
# ************************************************************************

class PysolMenubar(PysolMenubarTk):
    def __init__(self, app, top, progress=None):
        self.app = app
        self.top = top
        self.game = None
        # enabled/disabled - this is set by updateMenuState()
        self.menustate = Struct(
            save=0,
            save_as=0,
            undo=0,
            redo=0,
            restart=0,
            deal=0,
            hint=0,
            autofaceup=0,
            autodrop=0,
            shuffle=0,
            autodeal=0,
            quickplay=0,
            cardbackground=0,
            demo=0,
            highlight_piles=0,
            find_card=0,
            full_picture=0,
            rules=0,
            pause=0,
        )
        PysolMenubarTk.__init__(self, app, top, progress)

    #
    # delegation to Game
    #

    def _finishDrag(self):
        return self.game is None or self.game._finishDrag()

    def _cancelDrag(self, break_pause=True):
        if self.game is None:
            return True
        ret = self.game._cancelDrag(break_pause=break_pause)
        self._setPauseMenu(self.game.pause)
        return ret

    def changed(self, *args, **kw):
        assert self.game is not None
        return self.game.changed(*args, **kw)

    #
    # menu updates
    #

    def _clearMenuState(self):
        ms = self.menustate
        for k, v in ms.__dict__.items():
            if isinstance(v, list):
                ms.__dict__[k] = [0] * len(v)
            else:
                ms.__dict__[k] = 0

    # update self.menustate for menu items and toolbar
    def _updateMenuState(self):
        self._clearMenuState()
        game = self.game
        assert game is not None
        opt = self.app.opt
        ms = self.menustate
        # 0 = DISABLED, 1 = ENABLED
        ms.save_as = game.canSaveGame()
        if game.filename and ms.save_as:
            ms.save = 1
        if opt.undo:
            if game.canUndo() and game.moves.index > 0:
                ms.undo = 1
            if game.canRedo() and game.moves.index < len(game.moves.history):
                ms.redo = 1
        if game.moves.index > 0:
            ms.restart = 1
        if game.canDealCards():
            ms.deal = 1
        if game.getHintClass() is not None:
            if opt.hint:
                ms.hint = 1
            # if not game.demo:       # if not already running
            ms.demo = 1
        autostacks = game.getAutoStacks()
        if autostacks[0]:
            ms.autofaceup = 1
        if autostacks[1] and game.s.foundations:
            ms.autodrop = 1
        if game.s.waste:
            ms.autodeal = 1
        if autostacks[2]:
            ms.quickplay = 1
        if len(game.app.images.getCardbacks()) > 1:
            ms.cardbackground = 1
        if opt.highlight_piles and game.getHighlightPilesStacks():
            ms.highlight_piles = 1
        if game.canFindCard():
            ms.find_card = 1
        if game.canShowFullPicture():
            ms.full_picture = 1
        if game.app.getGameRulesFilename(game.id):  # note: this may return ""
            ms.rules = 1
        if not game.finished:
            ms.pause = 1
        if game.canShuffle():
            if opt.shuffle:
                ms.shuffle = 1

    # update menu items and toolbar
    def _updateMenus(self):
        if self.game is None:
            return
        ms = self.menustate
        # File menu
        self.setMenuState(ms.save, "file.save")
        self.setMenuState(ms.save_as, "file.saveas")
        # Edit menu
        self.setMenuState(ms.undo, "edit.undo")
        self.setMenuState(ms.redo, "edit.redo")
        self.updateBookmarkMenuState()
        self.setMenuState(ms.restart, "play.restart")
        # Game menu
        self.setMenuState(ms.deal, "play.dealcards")
        self.setMenuState(ms.autodrop, "play.autodrop")
        self.setMenuState(ms.shuffle, "play.shuffletiles")
        self.setMenuState(ms.pause, "play.pause")
        # Assist menu
        self.setMenuState(ms.hint, "play.hint")
        self.setMenuState(ms.highlight_piles, "play.highlightpiles")
        self.setMenuState(ms.find_card, "play.findcard")
        self.setMenuState(ms.full_picture, "play.showfullpicture")
        self.setMenuState(ms.demo, "play.demo")
        # Options menu
        self._autoplay_usable = {
            'autofaceup': bool(ms.autofaceup), 'autodrop': bool(ms.autodrop),
            'autodeal': bool(ms.autodeal), 'quickplay': bool(ms.quickplay)}
        if getattr(self, "_settings", None):
            self._settings.refresh()
        # Help menu
        self.setMenuState(
            ms.rules, self.help_menu_name + ".rulesforthisgame")
        # Toolbar
        self.setToolbarState(ms.restart, "restart")
        self.setToolbarState(ms.save_as, "save")
        self.setToolbarState(ms.undo, "undo")
        self.setToolbarState(ms.redo, "redo")
        self.setToolbarState(ms.autodrop, "autodrop")
        self.setToolbarState(ms.hint, "hint")
        self.setToolbarState(ms.shuffle, "shuffle")
        self.setToolbarState(ms.pause, "pause")
        self.setToolbarState(ms.rules, "rules")

    # update menu items and toolbar
    def updateMenus(self):
        if self.game is None:
            return
        self._updateMenuState()
        self._updateMenus()

    # disable menu items and toolbar
    def disableMenus(self):
        if self.game is None:
            return
        self._clearMenuState()
        self._updateMenus()

    #
    # File menu
    #

    def mNewGame(self, *args):
        if self._cancelDrag():
            return
        if self.changed():
            if not self.game.areYouSure("New game"):
                return
        if self.game.nextGameFlags(self.game.id) == 0:
            self.game.endGame()
            self.game.newGame()
        else:
            self.game.endGame()
            self.game.quitGame(self.game.id)

    def _mSelectGame(self, id, random=None, force=False):
        if self._cancelDrag():
            return
        if not force and self.game.id == id:
            return
        if self.changed():
            if not self.game.areYouSure("Select game"):
                return
        self.game.endGame()
        self.game.quitGame(id, random=random)

    def _mNewGameBySeed(self, seed, origin):
        try:
            random = construct_random(seed)
            if random is None:
                return
            id = self.game.id
            if not self.app.getGameInfo(id):
                raise ValueError
        except (ValueError, TypeError):
            MfxMessageDialog(self.top, title="Invalid game number",
                             text="Invalid game number\n" + str(seed),
                             bitmap="error")
            return
        f = self.game.nextGameFlags(id, random)
        if f & 17 == 0:
            return
        random.origin = origin
        if f & 15 == 0:
            self.game.endGame()
            self.game.newGame(random=random)
        else:
            self.game.endGame()
            self.game.quitGame(id, random=random)

    def mNewGameWithNextId(self, *args):
        if self._cancelDrag():
            return
        if self.changed():
            if not self.game.areYouSure("Select next game number"):
                return
        r = self.game.random
        seed = r.increaseSeed(r.initial_seed)
        seed = r.str(seed)
        self._mNewGameBySeed(seed, self.game.random.ORIGIN_NEXT_GAME)

    def mSelectGameById(self, *args):
        if self._cancelDrag(break_pause=False):
            return
        f = self.game.getGameNumber(format=0)
        d = MfxSimpleEntry(self.top, "Select new game number",
                           "\n\nEnter new game number", f,
                           strings=("&OK", "&Next number", "&Cancel"),
                           default=0, e_width=25)
        if d.status != 0:
            return
        if d.button == 2:
            return
        if d.button == 1:
            self.mNewGameWithNextId()
            return
        if self.changed():
            if not self.game.areYouSure("Select new game number"):
                return
        self._mNewGameBySeed(d.value, self.game.random.ORIGIN_SELECTED)

    def _mSelectNextGameFromList(self, gl, step):
        if self._cancelDrag():
            return
        id = self.game.id
        gl = list(gl)
        if len(gl) < 2 or (id not in gl):
            return
        if self.changed():
            if not self.game.areYouSure("Select next game"):
                return
        index = (gl.index(id) + step) % len(gl)
        self.game.endGame()
        self.game.quitGame(gl[index])

    def mSelectNextGameById(self, *args):
        self._mSelectNextGameFromList(self.app.gdb.getGamesIdSortedById(), 1)

    def mSelectPrevGameById(self, *args):
        self._mSelectNextGameFromList(self.app.gdb.getGamesIdSortedById(), -1)

    def mSelectNextGameByName(self, *args):
        self._mSelectNextGameFromList(self.app.gdb.getGamesIdSortedByName(), 1)

    def mSelectPrevGameByName(self, *args):
        self._mSelectNextGameFromList(
            self.app.gdb.getGamesIdSortedByName(), -1)

    def mSave(self, *args):
        if self._cancelDrag(break_pause=False):
            return
        if self.menustate.save_as:
            if self.game.filename:
                self.game.saveGame(self.game.filename)
            else:
                self.mSaveAs()

    def mQuit(self, *args):
        if self._cancelDrag():
            return
        if self.changed():
            if not self.game.areYouSure("Quit %s" % TITLE):
                return
        self.game.endGame()
        self.game.quitGame()

    #
    # Edit menu
    #

    def mUndo(self, *args):
        if self._cancelDrag():
            return
        if self.menustate.undo:
            self.game.playSample("undo")
            self.game.undo()

    def mRedo(self, *args):
        if self._cancelDrag():
            return
        if self.menustate.redo:
            self.game.playSample("redo")
            self.game.redo()
            self.game.checkForWin()

    def mSetBookmark(self, n, confirm=1):
        if self._cancelDrag():
            return
        if not self.app.opt.bookmarks:
            return
        if not (0 <= n <= 8):
            return
        self.game.setBookmark(n, confirm=confirm)
        self.game.updateMenus()

    def mGotoBookmark(self, n, confirm=-1):
        if self._cancelDrag():
            return
        if not self.app.opt.bookmarks:
            return
        if not (0 <= n <= 8):
            return
        self.game.gotoBookmark(n, confirm=confirm)
        self.game.updateMenus()

    def mRestart(self, *args):
        if self._cancelDrag():
            return
        if self.game.moves.index == 0:
            return
        if self.changed(restart=1):
            if not self.game.areYouSure("Restart game",
                                        "Restart this game?"):
                return
        self.game.restartGame()

    #
    # Game menu
    #

    def mDeal(self, *args):
        if self._cancelDrag():
            return
        self.game.dealCards()

    def mDrop(self, *args):
        if self._cancelDrag():
            return
        # self.game.autoPlay(autofaceup=-1, autodrop=1)
        self.game.autoDrop(autofaceup=-1)

    def mDrop1(self, *args):
        if self._cancelDrag():
            return
        # self.game.autoPlay(autofaceup=1, autodrop=1)
        self.game.autoDrop(autofaceup=1)

    def mShuffle(self, *args):
        if self._cancelDrag():
            return
        if self.menustate.shuffle:
            if self.game.canShuffle():
                self.game._mahjonggShuffle()

    def mFindCard(self, *args):
        if self.game.canFindCard():
            create_find_card_dialog(self.game.top, self.game,
                                    self.app.getFindCardImagesDir())
            raise_find_card_dialog(self.game)

    def mFullPicture(self, *args):
        if self.game.canShowFullPicture():
            create_full_picture_dialog(self.game.top, self.game)
            raise_full_picture_dialog(self.game)

    def mGameInfo(self, *args):
        wasPaused = False
        if not self.game.pause:
            self.game.doPause()
            wasPaused = True
        GameInfoDialog(self.top, "Game Info", self.app)
        if self.game.pause:
            if wasPaused:
                self.game.doPause()

    #
    # Assist menu
    #

    def mHint(self, *args):
        if self._cancelDrag():
            return
        if self.app.opt.hint:
            if self.game.showHint(0, self.app.opt.timeouts['hint']):
                self.game.stats.hints += 1

    def mHint1(self, *args):
        if self._cancelDrag():
            return
        if self.app.opt.hint:
            if self.game.showHint(1, self.app.opt.timeouts['hint']):
                self.game.stats.hints += 1

    def mHighlightPiles(self, *args):
        if self._cancelDrag():
            return
        if self.app.opt.highlight_piles:
            if self.game.highlightPiles(
                self.app.opt.timeouts['highlight_piles']
            ):
                self.game.stats.highlight_piles += 1

    def mDemo(self, *args):
        if self._cancelDrag():
            return
        if self.game.getHintClass() is not None:
            self._mDemo(mixed=0)

    def _mDemo(self, mixed):
        if self.changed():
            # only ask if there have been no demo moves or hints yet
            if self.game.stats.demo_moves == 0 and self.game.stats.hints == 0:
                if not self.game.areYouSure("Play demo"):
                    return
        # self.app.demo_counter = 0
        self.game.startDemo(mixed=mixed)

    def mOptToolbarButtons(self, *args):
        if self._cancelDrag(break_pause=False):
            return
        d = ToolbarButtonsDialog(
            self.top, "Visible toolbar buttons", self.app)
        if d.status == 0 and d.button == 0:
            for w, visible in d.visible.items():
                if bool(self.app.opt.toolbar_vars.get(w)) != visible:
                    self.toolbarConfig(w, visible)

    #
    # Help menu
    #

    def mHelpHtml(self, *args):
        print('mHelpHtml: %s' % str(args))
        if self._cancelDrag(break_pause=False):
            return
        help_html(self.app, args[0], "html")

    def mHelp(self, *args):
        if self._cancelDrag(break_pause=False):
            return
        help_html(self.app, "index.html", "html")

    def mHelpRules(self, *args):
        if self._cancelDrag(break_pause=False):
            return
        if not self.menustate.rules:
            return
        dir = os.path.join("html", "rules")
        # FIXME: plugins
        help_html(self.app, self.app.getGameRulesFilename(self.game.id), dir)

    def mHelpLicense(self, *args):
        if self._cancelDrag(break_pause=False):
            return
        help_html(self.app, "license.html", "html")

    def mHelpAbout(self, *args):
        if self._cancelDrag(break_pause=False):
            return
        help_about(self.app)

    #
    # misc
    #

    def mScreenshot(self, *args):
        if self._cancelDrag():
            return
        f = os.path.join(self.app.dn.config, "screenshots")
        if not os.path.isdir(f):
            return
        f = os.path.join(f, self.app.getGameSaveName(self.game.id))
        i = 1
        while 1:
            fn = "%s-%d.ppm" % (f, i)
            if not os.path.exists(fn):
                break
            i = i + 1
            if i >= 10000:      # give up
                return
        self.top.screenshot(fn)

    def mIconify(self, *args):
        if self._cancelDrag(break_pause=False):
            return
        self.top.wm_iconify()

    #
    # Keyboard play
    #

    def mKeyboardSelect(self, *args, **kw):
        direction = kw.get("dir", 0)
        self.game.keyboardSelect(direction)

    def mKeyboardSelectLayer(self, *args, **kw):
        direction = kw.get("dir", 0)
        self.game.keyboardSelectLayer(direction)

    def mKeyboardSelectMore(self, *args):
        self.game.keyboardSelectMoreCards()

    def mKeyboardSelectLess(self, *args):
        self.game.keyboardSelectLessCards()

    def mKeyboardSelectNextType(self, *args):
        self.game.keyboardSelectNextType()
        return "break"

    def mKeyboardSelectPrevType(self, *args):
        self.game.keyboardSelectNextType(dir=-1)
        return "break"

    def mKeyboardAction(self, *args):
        self.game.keyboardAction()

    def mKeyboardAction2(self, *args):
        self.game.keyboardAction(type=2)

    def mKeyboardGameInfo(self, *args):
        self.game.speakGameInfo()

    def mKeyboardStackInfo(self, *args):
        self.game.speakStackInfo()

    def mKeyboardCoordinates(self, *args):
        self.game.speakCoordinates()


# ************************************************************************
# * toolbar
# ************************************************************************

class PysolToolbar(PysolToolbarTk):
    def __init__(self, *args, **kwargs):
        self.game = None
        PysolToolbarTk.__init__(self, *args, **kwargs)

    #
    # public methods
    #

    def connectGame(self, game):
        self.game = game

    #
    # button event handlers - delegate to menubar
    #

    def mNewGame(self, *args):
        if not self._busy():
            self.menubar.mNewGame()
        return 1

    def mOpen(self, *args):
        if not self._busy():
            self.menubar.mOpen()
        return 1

    def mRestart(self, *args):
        if not self._busy():
            self.menubar.mRestart()
        return 1

    def mSave(self, *args):
        if not self._busy():
            self.menubar.mSaveAs()
        return 1

    def mUndo(self, *args):
        if not self._busy():
            self.menubar.mUndo()
        return 1

    def mRedo(self, *args):
        if not self._busy():
            self.menubar.mRedo()
        return 1

    def mSetBookmark(self, *args):
        if not self._busy():
            self.menubar.mSetBookmark(0)
        return 1

    def mGotoBookmark(self, *args):
        if not self._busy():
            self.menubar.mGotoBookmark(0)
        return 1

    def mDrop(self, *args):
        if not self._busy():
            self.menubar.mDrop()
        return 1

    def mShuffle(self, *args):
        if not self._busy():
            self.menubar.mShuffle()
        return 1

    def mHint(self, *args):
        if not self._busy():
            self.menubar.mHint()
        return 1

    def mPause(self, *args):
        if not self._busy():
            self.menubar.mPause()
        return 1

    def mHelpRules(self, *args):
        if not self._busy():
            self.menubar.mHelpRules()
        return 1
