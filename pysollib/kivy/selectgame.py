#!/usr/bin/env python
# -*- mode: python; coding: utf-8; -*-
# ---------------------------------------------------------------------------#
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
# ---------------------------------------------------------------------------#

# PySol Lite: "All games" as on the desktop: one alphabetical list of all
# games with a search box and a category filter (the Select game dialog of
# upstream's Kivy UI was a tree of categories this fork does not have).

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.properties import NumericProperty, ObjectProperty

from pysollib.gamedb import GI
from pysollib.kivy.LApp import DLG_ACCENT, DLG_SECONDARY, DLG_TEXT
from pysollib.kivy.LApp import DLG_ON_ACCENT, LTopLevel
from pysollib.kivy.mygettext import _
from pysollib.resource import getNaturalSortKey

ALL_CATEGORIES = "All categories"
ROW_BG = ((0, 0, 0, 0), (0, 0, 0, 0))


class GameRow(RecycleDataViewBehavior, Button):
    index = NumericProperty(0)
    gameid = NumericProperty(0)
    current = NumericProperty(0)
    dialog = ObjectProperty(None, allownone=True)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.background_normal = ''
        self.background_down = ''
        self.halign = 'left'
        self.valign = 'middle'
        self.padding_x = dp(14)
        self.color = DLG_TEXT
        self.font_size = dp(16)
        self.bind(size=lambda w, s: setattr(w, 'text_size', s))

    def refresh_view_attrs(self, rv, index, data):
        cur = bool(data.get('current'))
        self.bold = cur
        self.color = DLG_ON_ACCENT if cur else DLG_TEXT
        self.background_color = (
            DLG_ACCENT if cur else ROW_BG[index % 2])
        return super().refresh_view_attrs(rv, index, data)

    def on_release(self):
        if self.dialog is not None:
            self.dialog.select(self.gameid)


class SelectGameDialog:

    def __init__(self, parent, title, app, gameid, **kw):
        super().__init__()
        self.parent = parent
        self.app = app
        self.gameid = gameid
        self.random = None
        self.status = 1          # nothing to do for the menubar afterwards
        self.button = 1
        self.key = 'SelectGame'

        if parent.workStack.peek(self.key) is not None:
            parent.popWork(self.key)
            return

        window = self.window = LTopLevel(parent, title)
        window.titleline.bind(on_press=lambda *a: self.close())
        parent.pushWork(self.key, window)

        row = BoxLayout(orientation='horizontal', size_hint_y=None,
                        height=dp(52), spacing=dp(8),
                        padding=(dp(8), dp(4)))
        self.search = TextInput(
            hint_text=_('Search'), multiline=False, write_tab=False,
            size_hint_x=0.55, padding=(dp(10), dp(14)), font_size=dp(16),
            background_normal='', background_active='',
            background_color=(0.21, 0.20, 0.22, 1),
            foreground_color=DLG_TEXT, cursor_color=DLG_ACCENT,
            hint_text_color=(0.6, 0.63, 0.68, 1))
        self.search.bind(text=lambda w, v: self.refresh())
        categories = [ALL_CATEGORIES] + sorted(
            set(GI.TYPE_NAMES.values()), key=str.lower)
        self.category = Spinner(
            text=ALL_CATEGORIES, values=categories, size_hint_x=0.45,
            background_normal='', background_color=DLG_SECONDARY,
            color=DLG_TEXT, font_size=dp(16))
        self.category.bind(text=lambda w, v: self.refresh())
        row.add_widget(self.search)
        row.add_widget(self.category)
        window.content.add_widget(row)

        self.count = Label(size_hint_y=None, height=dp(28),
                           color=(0.8, 0.82, 0.85, 1), font_size=dp(14),
                           halign='left')
        self.count.bind(size=lambda w, s: setattr(w, 'text_size', s))
        window.content.add_widget(self.count)

        self.rv = RecycleView(do_scroll_x=False, bar_width=dp(6))
        layout = RecycleBoxLayout(
            default_size=(None, dp(56)), default_size_hint=(1, None),
            size_hint_y=None, orientation='vertical')
        layout.bind(minimum_height=layout.setter('height'))
        self.rv.add_widget(layout)
        self.rv.viewclass = GameRow
        window.content.add_widget(self.rv)
        self.refresh()
        # start at the current game
        for i, d in enumerate(self.rv.data):
            if d['current']:
                self.rv.scroll_y = 1 - i / max(1, len(self.rv.data) - 1)
                break

    def close(self):
        self.parent.popWork(self.key)

    def select(self, gameid):
        self.close()
        self.app.menubar._mSelectGame(gameid)

    def refresh(self):
        text = self.search.text
        category = self.category.text
        gtype = None
        if category != ALL_CATEGORIES:
            for k, v in GI.TYPE_NAMES.items():
                if v == category:
                    gtype = k
        results = []
        matched = set()
        for game in self.app.gdb.getAllGames():
            if gtype is not None and game.si.game_type != gtype:
                continue
            if self.app.checkSearchString(text, game.name):
                results.append((game.name, game.id))
                matched.add(game.id)
            # alternate names are listed only while searching
            if text:
                for alt in game.altnames:
                    if self.app.checkSearchString(text, alt):
                        results.append((alt, game.id))
                        matched.add(game.id)
        results.sort(key=lambda r: getNaturalSortKey(r[0]))
        cur = self.app.game.id if self.app.game else self.gameid
        self.rv.data = [
            {'text': name, 'gameid': gid, 'current': int(gid == cur),
             'dialog': self}
            for name, gid in results]
        n = len(matched)
        self.count.text = ('  ' + (
            _('No games found') if n == 0 else
            _('1 game') if n == 1 else _('%d games') % n))
