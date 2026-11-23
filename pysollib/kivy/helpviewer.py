# PySol Lite: a small in-app viewer for the Help pages (data/html).
#
# Android cannot open files from the app's private storage in a browser, and
# upstream's Tk-text emulation is not used by this fork, so the pages (plain
# headings, paragraphs, lists, links and a few images) are turned into Kivy
# widgets here.

import os
from html.parser import HTMLParser
from urllib.parse import unquote, urldefrag

from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

from pysollib.kivy.LApp import LTopLevel, make_button_row
from pysollib.kivy.mygettext import _

LINK_COLOR = '66ccb0'
TEXT = (0.93, 0.94, 0.95, 1)
FONT = {'h1': sp(26), 'h2': sp(21), 'h3': sp(18), 'p': sp(16)}


class _Page(HTMLParser):
    """HTML -> list of blocks: ('text', style, markup) or ('img', src, w)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self.title = ''
        self.cur = []
        self.style = 'p'
        self.indent = 0
        self.skip = 0
        self.in_title = False
        self.link = False
        self.pre = False
        self.lists = []

    def flush(self):
        text = ''.join(self.cur)
        self.cur = []
        if not self.pre:
            text = ' '.join(text.split())
            text = '\n'.join(p.strip() for p in text.split('\x00'))
        if text.strip():
            self.blocks.append(('text', self.style, text, self.indent))

    def esc(self, s):
        return s.replace('&', '&amp;').replace('[', '&bl;').replace(
            ']', '&br;')

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ('script', 'style', 'head'):
            self.skip += 1
        elif tag == 'title':
            self.in_title = True
        elif tag in ('h1', 'h2', 'h3', 'h4'):
            self.flush()
            self.style = 'h3' if tag == 'h4' else tag
            self.cur.append('[b]')
        elif tag in ('p', 'div', 'tr', 'table', 'dl'):
            self.flush()
        elif tag == 'br':
            self.cur.append('\x00')
        elif tag == 'hr':
            self.flush()
            self.blocks.append(('hr',))
        elif tag in ('ul', 'ol'):
            self.flush()
            self.lists.append([tag, 0])
            self.indent = len(self.lists)
        elif tag == 'li':
            self.flush()
            kind = self.lists[-1] if self.lists else ['ul', 0]
            kind[1] += 1
            self.cur.append(('%d. ' % kind[1]) if kind[0] == 'ol'
                            else '• ')
        elif tag == 'dt':
            self.flush()
            self.cur.append('[b]')
        elif tag == 'dd':
            self.flush()
            self.indent += 1
        elif tag in ('td', 'th'):
            if self.cur and not self.cur[-1].endswith(' | '):
                self.cur.append(' | ')
        elif tag in ('b', 'strong'):
            self.cur.append('[b]')
        elif tag in ('i', 'em', 'cite'):
            self.cur.append('[i]')
        elif tag in ('pre', 'code', 'tt'):
            if tag == 'pre':
                self.flush()
                self.pre = True
        elif tag == 'a' and a.get('href'):
            self.cur.append('[color=%s][ref=%s]' % (
                LINK_COLOR, a['href'].replace(']', '%5D')))
            self.link = True
        elif tag == 'img' and a.get('src'):
            self.flush()
            try:
                w = int(str(a.get('width', 0)).rstrip('px%') or 0)
            except ValueError:
                w = 0
            self.blocks.append(('img', a['src'], w))

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'head'):
            self.skip = max(0, self.skip - 1)
        elif tag == 'title':
            self.in_title = False
        elif tag in ('h1', 'h2', 'h3', 'h4'):
            self.cur.append('[/b]')
            self.flush()
            self.style = 'p'
        elif tag in ('p', 'div', 'tr', 'table', 'dl'):
            self.flush()
        elif tag in ('ul', 'ol'):
            self.flush()
            if self.lists:
                self.lists.pop()
            self.indent = len(self.lists)
        elif tag == 'li':
            self.flush()
        elif tag == 'dt':
            self.cur.append('[/b]')
            self.flush()
        elif tag == 'dd':
            self.flush()
            self.indent = max(0, self.indent - 1)
        elif tag in ('b', 'strong'):
            self.cur.append('[/b]')
        elif tag in ('i', 'em', 'cite'):
            self.cur.append('[/i]')
        elif tag == 'pre':
            self.flush()
            self.pre = False
        elif tag == 'a' and self.link:
            self.cur.append('[/ref][/color]')
            self.link = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        elif not self.skip:
            self.cur.append(self.esc(data))

    def close(self):
        super().close()
        self.flush()


def parse(path):
    with open(path, encoding='utf-8', errors='replace') as f:
        parser = _Page()
        parser.feed(f.read())
        parser.close()
    return parser.title.strip(), parser.blocks


class HelpViewer:
    TITLE = 'Help'
    KEY = 'HelpViewer'     # not the menu's key, which is also 'Help'

    def __init__(self, app, path):
        self.app = app
        self.main = app.top
        # the index is in data/html; a rules page is one folder below it
        here = os.path.dirname(os.path.abspath(path))
        self.home = os.path.join(here, 'index.html')
        if not os.path.isfile(self.home):
            self.home = os.path.join(os.path.dirname(here), 'index.html')
        self.history = []
        self.future = []
        self.path = None

        old = self.main.workStack.peek(self.KEY)
        if old is not None:
            self.main.popWork(self.KEY)
        window = self.window = LTopLevel(
            self.main, _(self.TITLE), size_hint=(1.0, 1.0))
        window.titleline.bind(on_press=lambda *a: self.close())
        # a full-window panel over the table
        window.is_overlay = True
        window.overlay_full = True
        self.main.pushWork(self.KEY, window)

        self.scroll = ScrollView(do_scroll_x=False, bar_width=dp(6))
        self.page = BoxLayout(orientation='vertical', size_hint_y=None,
                              padding=(dp(14), dp(10)), spacing=dp(8))
        self.page.bind(minimum_height=self.page.setter('height'))
        self.scroll.add_widget(self.page)
        window.content.add_widget(self.scroll)
        window.content.add_widget(make_button_row([
            (_('Back'), self.back, False),
            (_('Index'), self.go_home, False),
            (_('Forward'), self.forward, False),
            (_('Close'), self.close, True)]))
        Window.bind(size=self._relayout)
        self.show(path)

    # -- navigation --
    def close(self):
        Window.unbind(size=self._relayout)
        self.main.popWork(self.KEY)

    def go_home(self):
        self.goto(self.home)

    def goto(self, path):
        if not os.path.isfile(path):
            return
        if self.path:
            self.history.append(self.path)
        self.future = []
        self.show(path)

    def back(self):
        if self.history:
            if self.path:
                self.future.append(self.path)
            self.show(self.history.pop())

    def forward(self):
        if self.future:
            if self.path:
                self.history.append(self.path)
            self.show(self.future.pop())

    def on_ref(self, label, ref):
        if ref.startswith(('http:', 'https:', 'mailto:')):
            from pysollib.mfxutil import openURL
            openURL(ref)
            return
        target, _frag = urldefrag(unquote(ref))
        if not target:
            return
        path = os.path.normpath(os.path.join(
            os.path.dirname(self.path), target))
        if os.path.isfile(path):
            self.goto(path)

    # -- drawing --
    def _relayout(self, *a):
        pass

    def show(self, path):
        self.path = path
        title, blocks = parse(path)
        page = self.page
        page.clear_widgets()
        width = max(dp(200), Window.width - dp(60))
        for block in blocks:
            if block[0] == 'text':
                _k, style, text, indent = block
                label = Label(
                    text=text, markup=True, color=TEXT, halign='left',
                    valign='top', size_hint_y=None,
                    font_size=FONT.get(style, FONT['p']))
                pad = indent * dp(18)
                label.padding_x = pad
                label.bind(width=lambda w, v: setattr(
                    w, 'text_size', (max(v, 10), None)))
                label.bind(
                    texture_size=lambda w, s: setattr(w, 'height', s[1]))
                label.bind(on_ref_press=self.on_ref)
                page.add_widget(label)
            elif block[0] == 'hr':
                page.add_widget(Label(size_hint_y=None, height=dp(8)))
            else:
                src = os.path.normpath(os.path.join(
                    os.path.dirname(path), unquote(block[1])))
                if os.path.isfile(src):
                    img = Image(source=src, size_hint=(None, None),
                                fit_mode='contain')
                    w = min(width, dp(block[2]) if block[2] else dp(200))
                    img.width = w
                    img.height = w * 0.35
                    img.bind(texture_size=lambda i, s, w=w: setattr(
                        i, 'height', w * s[1] / s[0] if s[0] else 0))
                    # light backing: the logos have dark lettering
                    with img.canvas.before:
                        Color(0.96, 0.97, 0.98, 1)
                        back = Rectangle(pos=img.pos, size=img.size)
                    img.bind(pos=lambda i, v, b=back: setattr(b, 'pos', v),
                             size=lambda i, v, b=back: setattr(b, 'size', v))
                    page.add_widget(img)
        self.scroll.scroll_y = 1


def show_help(app, path):
    HelpViewer(app, path)
    return True
