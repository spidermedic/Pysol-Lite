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
import sys
import traceback

import configobj

import pysollib.settings
from pysollib.mfxutil import USE_PIL, \
    get_default_resampling, print_err
from pysollib.mygettext import _
from pysollib.mygettext import myGettext
from pysollib.pysoltk import TOOLBAR_BUTTONS
from pysollib.resource import CSI

import validate

# ************************************************************************
# * Options
# ************************************************************************

_global_settings = {
    'mouse_button1': 1,
    'mouse_button2': 2,
    'mouse_button3': 3,
}


def calcCustomMouseButtonsBinding(binding_format):
    assert _global_settings['mouse_button1']
    return binding_format.format(
        mouse_button1=_global_settings['mouse_button1'],
        mouse_button2=_global_settings['mouse_button2'],
        mouse_button3=_global_settings['mouse_button3'],
    )


configspec = '''
[general]
last_version = list
confirm = boolean
autofaceup = boolean
autodrop = boolean
autodeal = boolean
quickplay = boolean
mahjongg_show_removed = boolean
mahjongg_create_solvable = integer(0, 2)
shisen_show_hint = boolean
shisen_show_matching = boolean
match_three_cascade = boolean
animations = integer(0, 5)
shade = boolean
toolbar = integer(0, 4)
toolbar_land = integer(0, 4)
toolbar_port = integer(0, 4)
toolbar_relief = string
toolbar_compound = string
toolbar_size = integer(0, 2)
statusbar = boolean
num_recent_games = integer(10, 100)
last_gameid = integer
game_holded = integer
wm_maximized = boolean
splashscreen = boolean
date_format = string
mouse_type = string
use_cardset_bottoms = boolean
game_geometry = int_list(min=2, max=2)
window_geometry = int_list(min=4, max=4)
sound = boolean
sound_sample_buffer_size = integer(1, 4)
tabletile_name = string
tabletile_scale_method = integer
recent_gameid = int_list
favorite_gameid = int_list
visible_buttons = string_list
visible_status = string_list
translate_game_names = boolean
solver_presets = string_list
solver_show_progress = boolean
solver_max_iterations = integer
solver_iterations_output_step = integer
solver_preset = string
display_win_message = boolean
language = string
table_zoom = list

[colors]
piles = string
text = string
table = string
hintarrow = string
cards_1 = string
cards_2 = string
samerank_1 = string
samerank_2 = string
not_matching = string
keyboard_sel = string

[cardsets]
0 = string_list(min=2, max=2)
1 = string_list(min=2, max=2)
1_1 = string_list(min=2, max=2)
2 = string_list(min=2, max=2)
3 = string_list(min=2, max=2)
4 = string_list(min=2, max=2)
5 = string_list(min=2, max=2)
6 = string_list(min=2, max=2)
7 = string_list(min=2, max=2)
8 = string_list(min=2, max=2)
9 = string_list(min=2, max=2)
10 = string_list(min=2, max=2)
11_3 = string_list(min=2, max=2)
11_4 = string_list(min=2, max=2)
11_5 = string_list(min=2, max=2)
11_6 = string_list(min=2, max=2)
11_7 = string_list(min=2, max=2)
11_8 = string_list(min=2, max=2)
11_9 = string_list(min=2, max=2)
11_10 = string_list(min=2, max=2)
12 = string_list(min=2, max=2)
spread_stacks = boolean
'''.splitlines()


# A saved image set whose directory is missing is replaced with these.


class Options:
    GENERAL_OPTIONS = [
        ('last_version', 'list'),
        ('confirm', 'bool'),
        ('autofaceup', 'bool'),
        ('autodrop', 'bool'),
        ('autodeal', 'bool'),
        ('quickplay', 'bool'),
        ('mahjongg_show_removed', 'bool'),
        ('mahjongg_create_solvable', 'int'),
        ('shisen_show_hint', 'bool'),
        ('shisen_show_matching', 'bool'),
        ('match_three_cascade', 'bool'),
        ('accordion_deal_all', 'bool'),
        ('pegged_auto_remove', 'bool'),
        ('animations', 'int'),
        ('shade', 'bool'),
        ('toolbar', 'int'),
        ('toolbar_land', 'int'),
        ('toolbar_port', 'int'),
        ('toolbar_relief', 'str'),
        ('toolbar_compound', 'str'),
        ('toolbar_size', 'int'),
        ('statusbar', 'bool'),
        # ('num_cards', 'bool'),
        # ('helpbar', 'bool'),
        ('num_recent_games', 'int'),
        ('last_gameid', 'int'),
        ('game_holded', 'int'),
        ('wm_maximized', 'bool'),
        ('splashscreen', 'bool'),
        ('date_format', 'str'),
        ('mouse_type', 'str'),
        ('use_cardset_bottoms', 'bool'),
        # ('save_cardsets', 'bool'),
        ('sound', 'bool'),
        ('sound_sample_buffer_size', 'int'),
        ('tabletile_name', 'str'),
        ('tabletile_scale_method', 'int'),
        ('translate_game_names', 'bool'),
        ('solver_presets', 'list'),
        ('solver_show_progress', 'bool'),
        ('solver_max_iterations', 'int'),
        ('solver_iterations_output_step', 'int'),
        ('solver_preset', 'string'),
        ('mouse_button1', 'int'),
        ('mouse_button2', 'int'),
        ('mouse_button3', 'int'),
        # ('toolbar_vars', 'list'),
        # ('recent_gameid', 'list'),
        # ('favorite_gameid', 'list'),
        ('display_win_message', 'bool'),
        ('language', 'str'),
        # ('table_zoom', 'list'),
        ('fontscale', 'str'),
        # ('fontsizefactor', 'float'),
        ]

    def __init__(self):
        self._config = None             # configobj.ConfigObj instance
        self._config_encoding = 'utf-8'

        self.version_tuple = pysollib.settings.VERSION_TUPLE  # XXX
        self.saved = 0                  # XXX

        self.last_version = (2, 20, 1)
        # options menu:
        # the player name is the account name, set at startup (not saved)
        self.player = _("Unknown")
        self.confirm = True
        self.autofaceup = True
        self.autodrop = False
        self.autodeal = True
        self.quickplay = True
        # Assist features that are fixed (not saved or loaded)
        self.shuffle = True
        self.undo = True
        self.bookmarks = True
        self.hint = True
        self.free_hint = False
        self.highlight_piles = True
        self.highlight_cards = True
        self.highlight_samerank = True
        self.highlight_not_matching = True
        self.peek_facedown = False
        self.mahjongg_show_removed = False
        self.mahjongg_create_solvable = 2  # 0 - none, 1 - easy, 2 - hard
        self.accordion_deal_all = True
        self.pegged_auto_remove = True
        self.shisen_show_hint = True
        self.shisen_show_matching = False
        self.match_three_cascade = True
        # 0 none, 1 fast, 2 medium, 3 slow
        self.animations = 2             # default to Medium
        self.shadow = True              # fixed: not saved or loaded
        self.shade = True
        self.tile_theme = 'default'
        self.default_tile_theme = 'default'
        self.toolbar = 1       # 0 == hide, 1,2,3,4 == top, bottom, left, right
        self.toolbar_land = 4  # (landscape)
        self.toolbar_port = 2  # (portrait)
        # 0 == hide,
        # 1,2,3,4 == top, bottom, left, right
        self.toolbar_relief = 'flat'
        self.toolbar_compound = 'none'  # icons only
        self.toolbar_size = 0
        self.toolbar_vars = {}
        for w in TOOLBAR_BUTTONS:
            self.toolbar_vars[w] = True  # show all buttons
        self.statusbar = True
        # self.num_cards = False
        # self.helpbar = False
        self.splashscreen = True
        self.date_format = '%m-%d'
        self.mouse_button1 = 1
        self.mouse_button2 = 2
        self.mouse_button3 = 3
        # mouse_type:  'drag-n-drop' or 'point-n-click'
        self.mouse_type = 'drag-n-drop'
        self.translate_game_names = True
        self.display_win_message = True
        self.language = ''
        self.table_zoom = [1.0, 0.0, 0.0]
        self.fontscale = 'default'
        # self.fontsizefactor = 1.0
        # sound
        self.sound = True
        self.sound_sample_buffer_size = 1  # 1 - 4 (1024 - 4096 bytes)
        # Fonts are fixed (not saved or loaded). These are replaced by the
        # system fonts in setDefaults() once Tk is running.
        self.fonts = {
            "default": None,
            "sans": ("helvetica", 14),          # help text
            "fixed": ("courier", 13),           # help code, logs
            "canvas_default": ("helvetica", 13),
            "canvas_fixed": ("courier", 12),
            "canvas_large": ("helvetica", 18),
            "canvas_small": ("helvetica", 11),
            }
        # colors
        self.colors = {
            'table':        '#008200',
            'text':         '#ffffff',
            'piles':        '#ffc000',
            'cards_1':      '#ffc000',
            'cards_2':      '#0000ff',
            'samerank_1':   '#ffc000',
            'samerank_2':   '#0000ff',
            'hintarrow':    '#303030',
            'not_matching': '#ff0000',
            'keyboard_sel': '#bf40bf',
            }
        # delays
        # delays in seconds: fixed (not saved or loaded)
        self.timeouts = {
            'hint':               1.0,
            'demo':               1.0,
            'raise_card':         1.0,
            'highlight_piles':    1.0,
            'highlight_cards':    1.0,
            'highlight_samerank': 1.0,
            }
        # additional startup information
        self.num_recent_games = 15
        self.recent_gameid = []
        self.favorite_gameid = []
        self.last_gameid = 0            # last game played
        self.game_holded = 0            # gameid or 0
        self.wm_maximized = 1
        # saved games geometry (gameid: (width, height))
        self.games_geometry = {}
        self.game_geometry = (0, 0)  # game geometry before exit
        self.window_geometry = (0, 0, 0, 0)
        #
        self.use_cardset_bottoms = False
        # self.save_cardsets = True
        #
        # Card scaling is fixed: always scale to the window, keep the aspect
        # ratio, and use the best resampling filter. Not saved or loaded.
        # Window and layout settings that are fixed (not saved or loaded).
        self.wm_fullscreen = 0
        self.save_games_geometry = True
        self.topmost_dialogs = True
        self.center_layout = True
        # Card view settings that are fixed (not saved or loaded).
        self.compact_stacks = True
        self.shrink_face_down = True
        self.shade_filled_stacks = True
        self.negative_bottom = True
        self.randomize_place = False
        self.scale_cards = False
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.auto_scale = True
        self.preview_scale = True
        self.spread_stacks = False
        self.preserve_aspect_ratio = True
        self.tabletile_scale_method = 0
        self.resampling = 0
        if USE_PIL:
            self.resampling = int(get_default_resampling())

        # solver
        self.solver_presets = [
            'none',
            'abra-kadabra',
            'blue-yonder',
            'conspiracy-theory',
            'cookie-monster',
            'cool-jives',
            'crooked-nose',
            'fools-gold',
            'good-intentions',
            'hello-world',
            'john-galt-line',
            'looking-glass',
            'one-big-family',
            'rin-tin-tin',
            'slick-rock',
            'the-last-mohican',
            'video-editing',
            'yellow-brick-road',
            ]
        self.solver_show_progress = True
        self.solver_max_iterations = 100000
        self.solver_iterations_output_step = 100
        self.solver_preset = 'video-editing'

    def setDefaults(self, top=None):
        WIN_SYSTEM = pysollib.settings.WIN_SYSTEM
        # fonts: the system UI font and the system monospace font
        if top is not None:
            try:
                import tkinter.font
                ui = tkinter.font.nametofont('TkDefaultFont').actual('family')
                mono = tkinter.font.nametofont('TkFixedFont').actual('family')
            except Exception:
                ui = mono = None
            if ui and mono:
                for key, (family, size) in (
                        ('sans', (ui, 14)), ('fixed', (mono, 13)),
                        ('canvas_default', (ui, 13)),
                        ('canvas_fixed', (mono, 12)),
                        ('canvas_large', (ui, 18)),
                        ('canvas_small', (ui, 11))):
                    self.fonts[key] = (family, size)
        # tile theme
        if WIN_SYSTEM == 'win32':
            self.tile_theme = self.default_tile_theme = 'winnative'
            if sys.getwindowsversion() >= (5, 1):  # xp
                self.tile_theme = 'xpnative'
        elif WIN_SYSTEM == 'x11':
            self.tile_theme = 'clam'
            self.default_tile_theme = 'default'
        elif WIN_SYSTEM == 'aqua':
            self.tile_theme = self.default_tile_theme = 'aqua'
        #
        sw, sh = 0, 0
        if top:
            sw, sh = (top.winfo_screenwidth(),
                      top.winfo_screenheight())
        # bg
        self.tabletile_name = None      # solid color only
        # cardsets
        c = "Standard"
        m = "Crystal Mahjongg"
        if sw < 800 or sh < 600:
            c = "2000"

        # if sw > 1024 and sh > 768:
        #    c = 'Dondorf'
        if USE_PIL:
            self.cardset = {
                0:                  {0: ("Standard", "")},
                CSI.TYPE_FRENCH:    {0: ("Standard", ""), 1: ("Standard", "")},
                CSI.TYPE_HANAFUDA:  {0: ("Louie Mantia Hanafuda", "")},
                CSI.TYPE_MAHJONGG:  {0: ("Uni Mahjongg", "")},
                CSI.TYPE_TAROCK:    {0: ("Neo Tarock", "")},
                CSI.TYPE_HEXADECK:  {0: ("Neo Hex", "")},
                CSI.TYPE_MUGHAL_GANJIFA: {0: ("Mughal Ganjifa XL", "")},
                # CSI.TYPE_NAVAGRAHA_GANJIFA: {0: ("Navagraha Ganjifa", "")},
                CSI.TYPE_NAVAGRAHA_GANJIFA:
                    {0: ("Dashavatara Ganjifa XL", "")},
                CSI.TYPE_DASHAVATARA_GANJIFA:
                    {0: ("Dashavatara Ganjifa XL", "")},
                CSI.TYPE_TRUMP_ONLY: {0: ("Next Matrix", "")},
                CSI.TYPE_MATCHING: {0: ("Matching XL", "")},
                CSI.TYPE_PUZZLE: {3: ("Dojouji Ukiyo E (3x3)", ""),
                                  4: ("Knave of Hearts (4x4)", ""),
                                  5: ("Victoria Falls (5x5)", ""),
                                  6: ("Hokusai Ukiyo E (6x6)", ""),
                                  7: ("Blaren (7x7)", ""),
                                  8: ("Mid Winter's Eve (8x8)", ""),
                                  9: ("The Card Players (9x9)", ""),
                                  10: ("Players Trumps (10x10)", "")},
                CSI.TYPE_ISHIDO: {0: ("Simple Ishido XL", "")},
            }
        else:
            self.cardset = {
                # game_type:        (cardset_name, back_file)
                0:                  {0: (c, "")},
                CSI.TYPE_FRENCH:    {0: (c, ""), 1: (c, "")},
                CSI.TYPE_HANAFUDA:  {0: ("Kintengu", "")},
                CSI.TYPE_MAHJONGG:  {0: (m, "")},
                CSI.TYPE_TAROCK:    {0: ("Vienna 2K", "")},
                CSI.TYPE_HEXADECK:  {0: ("Hex A Deck", "")},
                CSI.TYPE_MUGHAL_GANJIFA: {0: ("Mughal Ganjifa", "")},
                # CSI.TYPE_NAVAGRAHA_GANJIFA: {0: ("Navagraha Ganjifa", "")},
                CSI.TYPE_NAVAGRAHA_GANJIFA: {0: ("Dashavatara Ganjifa", "")},
                CSI.TYPE_DASHAVATARA_GANJIFA: {0: ("Dashavatara Ganjifa", "")},
                CSI.TYPE_TRUMP_ONLY: {0: ("Matrix", "")},
                CSI.TYPE_MATCHING: {0: (c, "")},
                CSI.TYPE_PUZZLE: {3: ("Dojouji Ukiyo E (3x3)", ""),
                                  4: ("Knave of Hearts (4x4)", ""),
                                  5: ("Victoria Falls (5x5)", ""),
                                  6: ("Hokusai Ukiyo E (6x6)", ""),
                                  7: ("Blaren (7x7)", ""),
                                  8: ("Mid Winter's Eve (8x8)", ""),
                                  9: ("The Card Players (9x9)", ""),
                                  10: ("Players Trumps (10x10)", "")},
                CSI.TYPE_ISHIDO: {0: ("Simple Ishido", "")},
            }

    # not changeable options
    def setConstants(self):
        if 'shuffle' not in self.toolbar_vars:
            # new in v.1.1
            self.toolbar_vars['shuffle'] = True
        if isinstance(self.mahjongg_create_solvable, bool):
            # changed in v.1.1
            self.mahjongg_create_solvable = 2

    def copy(self):
        opt = Options()
        opt.__dict__.update(self.__dict__)
        opt.setConstants()
        return opt

    def save(self, filename):
        config = self._config

        self.last_version = self.version_tuple

        # general
        for key, t in self.GENERAL_OPTIONS:
            val = getattr(self, key)
            if isinstance(val, str):
                if sys.version_info < (3,):
                    val = str(val, 'utf-8')
            config['general'][key] = val

        config['general']['recent_gameid'] = self.recent_gameid
        config['general']['favorite_gameid'] = self.favorite_gameid
        config['general']['table_zoom'] = self.table_zoom
        config['general']['visible_buttons'] = [
            b for b, is_visible in self.toolbar_vars.items() if is_visible
        ]
        if 'none' in config['general']['solver_presets']:
            config['general']['solver_presets'].remove('none')

        # colors: only the background color can be changed
        config['colors'] = {'table': self.colors['table']}


        # cardsets
        for key, val in self.cardset.items():
            for key2, val2 in val.items():
                if key2 > 0:
                    config['cardsets'][str(key) + "_" + str(key2)] = val2
                else:
                    config['cardsets'][str(key)] = val2
        config['cardsets']['spread_stacks'] = self.spread_stacks

        # games_geometry
        config['games_geometry'].clear()
        for key, val in self.games_geometry.items():
            config['games_geometry'][str(key)] = val
        config['general']['game_geometry'] = self.game_geometry
        config['general']['window_geometry'] = self.window_geometry


        config.write()
        # config.write(sys.stdout); print

    def _getOption(self, section, key, t):
        config = self._config
        try:
            if config[section][key] is None:
                # invalid value
                return None
            if t == 'bool':
                val = config[section].as_bool(key)
            elif t == 'int':
                val = config[section].as_int(key)
            elif t == 'float':
                val = config[section].as_float(key)
            elif t == 'list':
                val = config[section][key]
                assert isinstance(val, (list, tuple))
            else:  # str
                val = config[section][key]
        except KeyError:
            val = None
        except Exception:
            print_err('load option error: %s: %s' % (section, key))
            traceback.print_exc()
            val = None
        return val

    def load(self, filename):

        # create ConfigObj instance
        try:
            config = configobj.ConfigObj(filename,
                                         configspec=configspec,
                                         encoding=self._config_encoding)
        except configobj.ParseError:
            traceback.print_exc()
            config = configobj.ConfigObj(configspec=configspec,
                                         encoding=self._config_encoding)
        self._config = config

        # create sections
        for section in (
            'general',
            'colors',
            'cardsets',
            'games_geometry',
                ):
            if section not in config:
                config[section] = {}

        # add initial comment
        if not os.path.exists(filename):
            config.initial_comment = ['-*- coding: %s -*-' %
                                      self._config_encoding]
            return

        # validation
        vdt = validate.Validator()
        res = config.validate(vdt)
        # from pprint import pprint; pprint(res)
        if isinstance(res, dict):
            for section, data in res.items():
                if data is True:
                    continue
                for key, value in data.items():
                    if value is False:
                        config[section][key] = None

        # general
        for key, t in self.GENERAL_OPTIONS:
            val = self._getOption('general', key, t)
            if val == 'None':
                setattr(self, key, None)
            elif val is not None:
                setattr(self, key, val)

        # The two slowest speeds were removed; older files may hold 4 or 5.
        self.animations = min(self.animations, 3)

        # The sticky mouse mode was removed.
        if self.mouse_type not in ('drag-n-drop', 'point-n-click'):
            self.mouse_type = 'drag-n-drop'

        # The text above/beside icon placements were removed.
        if self.toolbar_compound not in ('none', 'top', 'text'):
            self.toolbar_compound = 'top'

        pysollib.settings.TRANSLATE_GAME_NAMES = self.translate_game_names

        recent_gameid = self._getOption('general', 'recent_gameid', 'list')
        if recent_gameid is not None:
            try:
                self.recent_gameid = [int(i) for i in recent_gameid]
            except Exception:
                traceback.print_exc()

        favorite_gameid = self._getOption('general', 'favorite_gameid', 'list')
        if favorite_gameid is not None:
            try:
                self.favorite_gameid = [int(i) for i in favorite_gameid]
            except Exception:
                traceback.print_exc()

        table_zoom = self._getOption('general', 'table_zoom', 'list')
        if table_zoom is not None:
            try:
                self.table_zoom = [float(i) for i in table_zoom]
            except Exception:
                traceback.print_exc()

        visible_buttons = self._getOption('general', 'visible_buttons', 'list')
        if visible_buttons is not None:
            for key in TOOLBAR_BUTTONS:
                self.toolbar_vars[key] = (key in visible_buttons)

        myGettext.language = self.language

        # solver
        solver_presets = self._getOption('general', 'solver_presets', 'list')
        if solver_presets is not None:
            if 'none' not in solver_presets:
                solver_presets.insert(0, 'none')
            self.solver_presets = solver_presets

        # colors: only the background color is saved
        for key in ('table',):
            val = self._getOption('colors', key, 'str')
            if val is not None:
                self.colors[key] = val

        # cardsets
        for key, cur_cardset in self.cardset.items():
            for key2 in cur_cardset:
                if key2 > 0:
                    val = self._getOption('cardsets',
                                          str(key) + "_" + str(key2), 'list')
                else:
                    val = self._getOption('cardsets', str(key), 'list')
                if val is not None:
                    try:
                        self.cardset[int(key)][int(key2)] = val
                    except Exception:
                        traceback.print_exc()
        for key, t in (('spread_stacks', 'bool'),):
            val = self._getOption('cardsets', key, t)
            if val is not None:
                setattr(self, key, val)

        # games_geometry
        for key, val in config['games_geometry'].items():
            try:
                val = [int(i) for i in val]
                assert len(val) == 2
                self.games_geometry[int(key)] = val
            except Exception:
                traceback.print_exc()
        game_geometry = self._getOption('general', 'game_geometry', 'list')
        if game_geometry is not None:
            try:
                self.game_geometry = tuple(int(i) for i in game_geometry)
            except Exception:
                traceback.print_exc()
        window_geometry = self._getOption(
            'general', 'window_geometry', 'list')
        if window_geometry is not None:
            try:
                self.window_geometry = tuple(int(i) for i in window_geometry)
            except Exception:
                traceback.print_exc()

        # mouse buttons swap
        def _positive(button):
            return max([button, 1])
        _global_settings['mouse_button1'] = _positive(self.mouse_button1)
        _global_settings['mouse_button2'] = _positive(self.mouse_button2)
        _global_settings['mouse_button3'] = _positive(self.mouse_button3)

    def calcCustomMouseButtonsBinding(self, binding_format):
        """docstring for calcCustomMouseButtonsBinding"""
        def _positive(button):
            return max([button, 1])
        return binding_format.format(
            mouse_button1=_positive(self.mouse_button1),
            mouse_button2=_positive(self.mouse_button2),
            mouse_button3=_positive(self.mouse_button3),
        )
