"""PySol Lite Android feasibility spike: a throwaway Klondike table.

Not connected to pysollib. It only tests whether Kivy on a real tablet
draws the cards sharply and follows a finger without lag. Tap the stock to
deal, drag cards (with the cards on top of them) between columns, tap
"Undo" to take the last move back. The FPS counter is in the top right.
"""
import os
import random

from kivy.clock import Clock
from kivy.graphics import Color, Line
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.app import App

HERE = os.path.dirname(os.path.abspath(__file__))
RED = 'dh'


def card_file(rank, suit):
    return os.path.join(HERE, 'cards', f'{rank:02d}{suit}.png')


class CardWidget(Image):
    def __init__(self, rank, suit, table, **kw):
        super().__init__(fit_mode='fill', size_hint=(None, None), **kw)
        self.rank, self.suit, self.table = rank, suit, table
        self.face_up = False
        self.pile = None
        self.refresh()

    def refresh(self):
        self.source = (card_file(self.rank, self.suit) if self.face_up
                       else os.path.join(HERE, 'cards', 'back111.png'))

    @property
    def red(self):
        return self.suit in RED


class Table(FloatLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.cards = [CardWidget(r, s, self) for s in 'cdhs'
                      for r in range(1, 14)]
        random.shuffle(self.cards)
        self.piles = {'stock': [], 'waste': []}
        for i in range(7):
            self.piles[f'c{i}'] = []
        for i in range(4):
            self.piles[f'f{i}'] = []
        self.drag = []          # cards being dragged
        self.drag_from = None
        self.drag_off = (0, 0)
        self.history = []       # (kind, cards, from_pile, to_pile, flipped)
        for c in self.cards:
            self.add_widget(c)
        self.fps = Label(size_hint=(None, None), size=(220, 40))
        self.add_widget(self.fps)
        self.undo = Button(text='Undo', size_hint=(None, None),
                           size=(140, 56))
        self.undo.bind(on_release=lambda *a: self.undo_move())
        self.add_widget(self.undo)
        self.deal()
        Clock.schedule_interval(self.tick, 0.5)
        self.bind(size=lambda *a: self.layout())

    def deal(self):
        deck = list(self.cards)
        for i in range(7):
            for j in range(i + 1):
                c = deck.pop()
                c.face_up = (j == i)
                c.refresh()
                self.piles[f'c{i}'].append(c)
        for c in deck:
            c.face_up = False
            c.refresh()
        self.piles['stock'] = deck
        self.layout()

    # ---- geometry ----
    def metrics(self):
        w, h = self.size
        cw = w / 8.2
        ch = cw * 96 / 71
        return cw, ch, cw * 0.15, min(ch * 0.30, (h - ch * 1.6) / 12)

    def col_x(self, i):
        cw, ch, gap, _ = self.metrics()
        return gap + i * (cw + gap)

    def top_y(self):
        cw, ch, gap, _ = self.metrics()
        return self.height - ch - gap

    def layout(self):
        if not self.width:
            return
        cw, ch, gap, dy = self.metrics()
        top = self.top_y()
        for c in self.cards:
            c.size = (cw, ch)
        for i in range(7):
            for k, c in enumerate(self.piles[f'c{i}']):
                c.pos = (self.col_x(i), top - ch * 0.15 - ch - k * dy)
        for c in self.piles['stock']:
            c.pos = (self.col_x(0), top)
        for c in self.piles['waste']:
            c.pos = (self.col_x(1), top)
        for i in range(4):
            for c in self.piles[f'f{i}']:
                c.pos = (self.col_x(3 + i), top)
        self.fps.pos = (self.width - 230, self.height - 44)
        self.undo.size = (cw, 56)
        self.undo.pos = (self.col_x(2), top + ch / 2 - 28)
        self.canvas.before.clear()
        with self.canvas.before:
            Color(1, 1, 1, 0.3)
            slots = [self.col_x(0), self.col_x(1)] + \
                [self.col_x(3 + i) for i in range(4)]
            for x in slots:
                Line(rectangle=(x, top, cw, ch), width=1.2)
            for i in range(7):
                Line(rectangle=(self.col_x(i), top - ch * 0.15 - ch, cw, ch),
                     width=1.2)
        self.restack()

    def restack(self):
        """Draw order = pile order, so face-up cards are never hidden by
        cards that are lower in the same pile."""
        order = []
        for name in ['stock', 'waste'] + [f'f{i}' for i in range(4)] + \
                [f'c{i}' for i in range(7)]:
            order.extend(self.piles[name])
        for c in order:
            self.remove_widget(c)
            self.add_widget(c)
        # keep the buttons above the cards
        for w in (self.fps, self.undo):
            self.remove_widget(w)
            self.add_widget(w)

    def tick(self, dt):
        self.fps.text = f'{Clock.get_fps():.0f} fps'

    # ---- rules (just enough to feel like Klondike) ----
    def can_drop_col(self, card, col):
        if not col:
            return card.rank == 13
        top = col[-1]
        return (top.face_up and top.rank == card.rank + 1
                and top.red != card.red)

    def can_drop_found(self, card, pile):
        if not pile:
            return card.rank == 1
        return pile[-1].suit == card.suit and pile[-1].rank + 1 == card.rank

    def pile_of(self, card):
        for name, pile in self.piles.items():
            if card in pile:
                return name
        return None

    # ---- touch ----
    def auto_foundation(self, name, card):
        """Move card to a foundation if it fits. Returns True if moved."""
        for i in range(4):
            if self.can_drop_found(card, self.piles[f'f{i}']):
                self.drag_from = name
                self.move([card], f'f{i}')
                return True
        return False

    def on_touch_down(self, touch):
        if super().on_touch_down(touch):
            return True
        if touch.is_double_tap:
            waste = self.piles['waste']
            if waste and waste[-1].collide_point(*touch.pos) \
                    and self.auto_foundation('waste', waste[-1]):
                return True
            for i in range(7):
                col = self.piles[f'c{i}']
                if col and col[-1].face_up \
                        and col[-1].collide_point(*touch.pos) \
                        and self.auto_foundation(f'c{i}', col[-1]):
                    return True
        stock = self.piles['stock']
        cw, ch, gap, _ = self.metrics()
        sx, sy = self.col_x(0), self.top_y()
        if sx <= touch.x <= sx + cw and sy <= touch.y <= sy + ch:
            self.deal_from_stock()      # also recycles an empty stock
            return True
        waste = self.piles['waste']
        if waste and waste[-1].collide_point(*touch.pos):
            self.begin_drag('waste', [waste[-1]], touch)
            return True
        for i in range(4):
            f = self.piles[f'f{i}']
            if f and f[-1].collide_point(*touch.pos):
                self.begin_drag(f'f{i}', [f[-1]], touch)
                return True
        for i in range(7):
            col = self.piles[f'c{i}']
            for k in range(len(col) - 1, -1, -1):
                if col[k].face_up and col[k].collide_point(*touch.pos):
                    self.begin_drag(f'c{i}', col[k:], touch)
                    return True
        return False

    def begin_drag(self, name, cards, touch):
        self.drag = cards
        self.drag_from = name
        self.drag_start = [c.pos[:] for c in cards]
        self.drag_off = (touch.x - cards[0].x, touch.y - cards[0].y)
        for c in cards:                # raise above everything
            self.remove_widget(c)
            self.add_widget(c)

    def on_touch_move(self, touch):
        if not self.drag:
            return super().on_touch_move(touch)
        _, _, _, dy = self.metrics()
        x, y = touch.x - self.drag_off[0], touch.y - self.drag_off[1]
        for k, c in enumerate(self.drag):
            c.pos = (x, y - k * dy)
        return True

    def drop_target(self, cards):
        cw, ch, gap, _ = self.metrics()
        cx = cards[0].x + cw / 2
        cy = cards[0].y + ch / 2
        if cy > self.height - ch * 1.6:             # top row: foundations
            if len(cards) == 1:
                for i in range(4):
                    if abs(cx - (self.col_x(3 + i) + cw / 2)) < cw * 0.6 \
                            and self.can_drop_found(cards[0],
                                                    self.piles[f'f{i}']):
                        return f'f{i}'
            return None
        for i in range(7):
            name = f'c{i}'
            if abs(cx - (self.col_x(i) + cw / 2)) < cw * 0.6 \
                    and name != self.drag_from \
                    and self.can_drop_col(cards[0], self.piles[name]):
                return name
        return None

    def on_touch_up(self, touch):
        if not self.drag:
            return super().on_touch_up(touch)
        cards, self.drag = self.drag, []
        target = self.drop_target(cards)
        if target is None or target == self.drag_from:
            for c, p in zip(cards, self.drag_start):
                c.pos = p
            self.restack()
            return True
        self.move(cards, target)
        return True

    def move(self, cards, target):
        src = self.piles[self.drag_from]
        for c in cards:
            src.remove(c)
            self.piles[target].append(c)
        flipped = None
        if self.drag_from.startswith('c') and src and not src[-1].face_up:
            src[-1].face_up = True
            src[-1].refresh()
            flipped = src[-1]
        self.history.append(('move', cards, self.drag_from, target, flipped))
        self.layout()

    def deal_from_stock(self):
        stock, waste = self.piles['stock'], self.piles['waste']
        if stock:
            c = stock.pop()
            c.face_up = True
            c.refresh()
            waste.append(c)
            self.history.append(('deal', [c], 'stock', 'waste', None))
        else:
            while waste:
                c = waste.pop()
                c.face_up = False
                c.refresh()
                stock.append(c)
            self.history.clear()
        self.layout()

    def undo_move(self):
        if not self.history:
            return
        kind, cards, frm, to, flipped = self.history.pop()
        if kind == 'deal':
            c = cards[0]
            self.piles['waste'].remove(c)
            c.face_up = False
            c.refresh()
            self.piles['stock'].append(c)
        else:
            if flipped is not None:
                flipped.face_up = False
                flipped.refresh()
            for c in cards:
                self.piles[to].remove(c)
                self.piles[frm].append(c)
        self.layout()


class SpikeApp(App):
    def build(self):
        Window.clearcolor = (0.0, 0.51, 0.0, 1)
        return Table()


if __name__ == '__main__':
    SpikeApp().run()
