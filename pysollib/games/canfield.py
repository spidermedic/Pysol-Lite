from pysollib.game import Game
from pysollib.gamedb import GI, GameInfo, registerGame
from pysollib.hint import CautiousDefaultHint
from pysollib.layout import Layout
from pysollib.pysoltk import MfxCanvasText
from pysollib.stack import (
    AC_RowStack,
    KingAC_RowStack,
    OpenStack,
    RK_RowStack,
    ReserveStack,
    SS_FoundationStack,
    SS_RowStack,
    StackWrapper,
    WasteStack,
    WasteTalonStack,
)
from pysollib.util import KING, QUEEN, RANKS, UNLIMITED_REDEALS


class Canfield_Hint(CautiousDefaultHint):
    # FIXME: demo is not too clever in this game

    # Score for moving a pile (usually a single card) from the WasteStack.
    def _getMoveWasteScore(self, score, color, r, t, pile, rpile):
        score, color = CautiousDefaultHint._getMovePileScore(
            self, score, color, r, t, pile, rpile)
        # we prefer moving cards from the waste over everything else
        return score + 100000, color


# ************************************************************************
# * a Canfield row stack only accepts a full other row stack
# * (cannot move part of a sequence from row to row)
# ************************************************************************

class Canfield_AC_RowStack(AC_RowStack):
    def basicAcceptsCards(self, from_stack, cards):
        if from_stack in self.game.s.rows:
            if len(cards) != 1 and len(cards) != len(from_stack.cards):
                return False
        return AC_RowStack.basicAcceptsCards(self, from_stack, cards)


class Canfield_SS_RowStack(SS_RowStack):
    def basicAcceptsCards(self, from_stack, cards):
        if from_stack in self.game.s.rows:
            if len(cards) != 1 and len(cards) != len(from_stack.cards):
                return False
        return SS_RowStack.basicAcceptsCards(self, from_stack, cards)


class Canfield_RK_RowStack(RK_RowStack):
    def basicAcceptsCards(self, from_stack, cards):
        if from_stack in self.game.s.rows:
            if len(cards) != 1 and len(cards) != len(from_stack.cards):
                return False
        return RK_RowStack.basicAcceptsCards(self, from_stack, cards)


# ************************************************************************
# * Canfield
# ************************************************************************

class Canfield(Game):
    Talon_Class = WasteTalonStack
    Foundation_Class = SS_FoundationStack
    RowStack_Class = StackWrapper(Canfield_AC_RowStack, mod=13)
    ReserveStack_Class = OpenStack
    Hint_Class = Canfield_Hint

    INITIAL_RESERVE_CARDS = 13
    INITIAL_RESERVE_FACEUP = 0
    FILL_EMPTY_ROWS = 1
    SEPARATE_FOUNDATIONS = True
    ALIGN_FOUNDATIONS = True

    #
    # game layout
    #

    def createGame(self, rows=4, max_rounds=-1, num_deal=3,
                   text=True, round_text=False, dir=-1):
        # create layout
        lay, s = Layout(self), self.s
        decks = self.gameinfo.decks

        # set window
        if self.INITIAL_RESERVE_FACEUP == 1:
            yoffset = lay.YOFFSET  # min(lay.YOFFSET, 14)
        else:
            yoffset = 10
            if self.INITIAL_RESERVE_CARDS > 30:
                yoffset = 5
        # (piles up to 20 cards are playable in default window size)
        h = max(3*lay.YS, lay.YS+self.INITIAL_RESERVE_CARDS*yoffset)
        if round_text:
            h += lay.TEXT_HEIGHT
        self.setSize(
            lay.XM + (2+max(rows, 4*decks))*lay.XS + lay.XM,
            lay.YM + lay.YS + lay.TEXT_HEIGHT + h)

        # extra settings
        self.base_card = None

        # create stacks
        x, y = lay.XM, lay.YM
        if round_text:
            y += lay.TEXT_HEIGHT
        s.talon = self.Talon_Class(x, y, self,
                                   max_rounds=max_rounds, num_deal=num_deal)
        lay.createText(s.talon, "s")
        if round_text:
            lay.createRoundText(s.talon, 'n')
        x += lay.XS
        s.waste = WasteStack(x, y, self)
        lay.createText(s.waste, "s")
        x += lay.XM
        y = lay.YM
        if round_text:
            y += lay.TEXT_HEIGHT
        if (self.SEPARATE_FOUNDATIONS):
            for i in range(4):
                for j in range(decks):
                    x += lay.XS
                    s.foundations.append(self.Foundation_Class(x, y,
                                                               self, i,
                                                               mod=13,
                                                               max_move=0))
        else:
            x += (lay.XS * rows)
            s.foundations.append(self.Foundation_Class(x, y, self, -1,
                                                       max_move=0))
        if text:
            if rows > 4 * decks:
                tx, ty, ta, tf = lay.getTextAttr(None, "se")
                tx, ty = x + tx + lay.XM, y + ty
            else:
                tx, ty, ta, tf = lay.getTextAttr(None, "s")
                tx, ty = x + tx, y + ty
            font = self.app.getFont("canvas_default")
            self.texts.info = MfxCanvasText(self.canvas, tx, ty,
                                            anchor=ta, font=font)
        x, y = lay.XM, lay.YM + lay.YS + lay.TEXT_HEIGHT
        if round_text:
            y += lay.TEXT_HEIGHT
        s.reserves.append(self.ReserveStack_Class(x, y, self))
        s.reserves[0].CARD_YOFFSET = yoffset
        x, y = lay.XM + 2 * lay.XS + lay.XM, lay.YM + lay.YS
        if round_text:
            y += lay.TEXT_HEIGHT
        if text:
            y += lay.TEXT_HEIGHT
        for i in range(rows):
            s.rows.append(self.RowStack_Class(x, y, self, dir=dir))
            x += lay.XS

        # define stack-groups
        lay.defaultStackGroups()

    #
    # game extras
    #

    def updateText(self):
        if self.preview > 1:
            return
        if not self.texts.info:
            return
        if not self.base_card:
            t = ""
        else:
            t = RANKS[self.base_card.rank]
        self.texts.info.config(text=t)

    #
    # game overrides
    #

    def startGame(self, num_rows=1):
        self.startDealSample()
        self.base_card = None
        self.updateText()
        if (self.SEPARATE_FOUNDATIONS):
            # deal base_card to Foundations, update foundations cap.base_rank
            self.base_card = self.s.talon.getCard()
            for s in self.s.foundations:
                s.cap.base_rank = self.base_card.rank
            if (self.ALIGN_FOUNDATIONS):
                n = self.base_card.suit * self.gameinfo.decks
            else:
                n = 0
            if self.s.foundations[n].cards:
                assert self.gameinfo.decks > 1
                n = n + 1
            self.flipMove(self.s.talon)
            self.moveMove(1, self.s.talon, self.s.foundations[n])
            self.updateText()
        # fill the Reserve
        for i in range(self.INITIAL_RESERVE_CARDS):
            if self.INITIAL_RESERVE_FACEUP:
                self.flipMove(self.s.talon)
            self.moveMove(
                1, self.s.talon, self.s.reserves[0], frames=4, shadow=0)
        if self.s.reserves[0].canFlipCard():
            self.flipMove(self.s.reserves[0])
        for i in range(num_rows-1):
            self.s.talon.dealRow(frames=0, flip=0)
        self.s.talon.dealRow(reverse=1)
        self.s.talon.dealCards()          # deal first 3 cards to WasteStack

    def fillStack(self, stack):
        if stack in self.s.rows and self.s.reserves:
            if self.FILL_EMPTY_ROWS:
                if not stack.cards and self.s.reserves[0].cards:
                    if not self.s.reserves[0].cards[-1].face_up:
                        self.s.reserves[0].flipMove()
                    self.s.reserves[0].moveMove(1, stack)

    shallHighlightMatch = Game._shallHighlightMatch_ACW

    def parseGameInfo(self):
        return "Base rank: " + RANKS[self.base_card.rank]

    def _restoreGameHook(self, game):
        self.base_card = self.cards[game.loadinfo.base_card_id]
        for s in self.s.foundations:
            s.cap.base_rank = self.base_card.rank

    def _loadGameHook(self, p):
        self.loadinfo.addattr(base_card_id=None)    # register extra load var.
        self.loadinfo.base_card_id = p.load()

    def _saveGameHook(self, p):
        p.dump(self.base_card.id)


# ************************************************************************
# * Superior Canfield
# ************************************************************************

class SuperiorCanfield(Canfield):
    INITIAL_RESERVE_FACEUP = 1
    FILL_EMPTY_ROWS = 0


# ************************************************************************
# * Rainbow
# ************************************************************************

class Rainbow(Canfield):
    RowStack_Class = StackWrapper(Canfield_RK_RowStack, mod=13)

    def createGame(self):
        Canfield.createGame(self, max_rounds=1, num_deal=1)

    shallHighlightMatch = Game._shallHighlightMatch_RKW

# ************************************************************************
# * Storehouse (aka Straight Up)
# ************************************************************************


class Storehouse(Canfield):
    RowStack_Class = StackWrapper(Canfield_SS_RowStack, mod=13)

    def createGame(self):
        Canfield.createGame(self, max_rounds=3, num_deal=1, round_text=True)

    def _shuffleHook(self, cards):
        # move Twos to top of the Talon (i.e. first cards to be dealt)
        return self._shuffleHookMoveToTop(
            cards, lambda c: (c.rank == 1, c.suit))

    def startGame(self):
        self.startDealSample()
        self.s.talon.dealRow(rows=self.s.foundations[:3])
        Canfield.startGame(self)

    shallHighlightMatch = Game._shallHighlightMatch_SSW

    def updateText(self):
        pass

    def parseGameInfo(self):
        return ""


# ************************************************************************
# * Gate
# * Doorway
# ************************************************************************

class Gate(Game):

    #
    # game layout
    #

    def createGame(self):
        # create layout
        lay, s = Layout(self), self.s

        # set window
        w = max(8*lay.XS, 6*lay.XS+8*lay.XOFFSET)
        h = lay.YM+3*lay.YS+12*lay.YOFFSET
        self.setSize(w+lay.XM, h)

        # create stacks
        y = lay.YM
        for x in (lay.XM, lay.XM+w-lay.XS-4*lay.XOFFSET):
            stack = OpenStack(x, y, self, max_accept=0)
            stack.CARD_XOFFSET, stack.CARD_YOFFSET = lay.XOFFSET, 0
            s.reserves.append(stack)
        x, y = lay.XM+(w-4*lay.XS)//2, lay.YM
        for i in range(4):
            s.foundations.append(SS_FoundationStack(x, y, self, suit=i))
            x += lay.XS
        x, y = lay.XM+(w-8*lay.XS)//2, lay.YM+lay.YS
        for i in range(8):
            s.rows.append(AC_RowStack(x, y, self))
            x += lay.XS
        s.talon = WasteTalonStack(lay.XM, h-lay.YS, self, max_rounds=1)
        lay.createText(s.talon, "n")
        s.waste = WasteStack(lay.XM+lay.XS, h-lay.YS, self)
        lay.createText(s.waste, "n")

        # define stack-groups
        lay.defaultStackGroups()

    #
    # game overrides
    #

    def startGame(self):
        for i in range(5):
            self.s.talon.dealRow(rows=self.s.reserves, frames=0)
        self.startDealSample()
        self.s.talon.dealRow()
        self.s.talon.dealCards()

    def fillStack(self, stack):
        r1, r2 = self.s.reserves
        if stack in self.s.rows and not stack.cards:
            from_stack = None
            if r1.cards or r2.cards:
                from_stack = r1
                if len(r1.cards) < len(r2.cards):
                    from_stack = r2
            elif self.s.waste.cards:
                from_stack = self.s.waste
            if from_stack:
                from_stack.moveMove(1, stack)

    shallHighlightMatch = Game._shallHighlightMatch_AC


class LittleGate(Gate):

    RowStack_Class = AC_RowStack
    ReserveStack_Class = StackWrapper(OpenStack, max_accept=0)

    #
    # game layout
    #

    def createGame(self, rows=4):
        # create layout
        lay, s = Layout(self), self.s

        # set window
        max_rows = max(7, rows+3)
        w, h = lay.XM+max_rows*lay.XS, lay.YM+2*lay.YS+12*lay.YOFFSET
        self.setSize(w, h)

        # create stacks
        y = lay.YM+lay.YS+lay.TEXT_HEIGHT
        for x in (lay.XM, w-lay.XS):
            stack = self.ReserveStack_Class(x, y, self)
            stack.CARD_XOFFSET, stack.CARD_YOFFSET = 0, lay.YOFFSET
            s.reserves.append(stack)
        x, y = lay.XM+(max_rows-4)*lay.XS, lay.YM
        for i in range(4):
            s.foundations.append(SS_FoundationStack(x, y, self, suit=i))
            x += lay.XS
        x, y = lay.XM+(max_rows-rows)*lay.XS//2, lay.YM+lay.YS+lay.TEXT_HEIGHT
        for i in range(rows):
            s.rows.append(self.RowStack_Class(x, y, self))
            x += lay.XS
        s.talon = WasteTalonStack(lay.XM, lay.YM, self, max_rounds=1)
        lay.createText(s.talon, "s")
        s.waste = WasteStack(lay.XM+lay.XS, lay.YM, self)
        lay.createText(s.waste, "s")

        # define stack-groups
        lay.defaultStackGroups()

        return lay


class Doorway(LittleGate):

    Hint_Class = CautiousDefaultHint
    RowStack_Class = StackWrapper(RK_RowStack, max_move=1)
    ReserveStack_Class = ReserveStack

    def createGame(self):
        lay = LittleGate.createGame(self, rows=5)
        king_stack, queen_stack = self.s.reserves
        tx, ty, ta, tf = lay.getTextAttr(king_stack, "s")
        font = self.app.getFont("canvas_default")
        king_stack.texts.misc = MfxCanvasText(self.canvas, tx, ty,
                                              anchor=ta, font=font,
                                              text='King')
        tx, ty, ta, tf = lay.getTextAttr(queen_stack, "s")
        font = self.app.getFont("canvas_default")
        queen_stack.texts.misc = MfxCanvasText(self.canvas, tx, ty,
                                               anchor=ta, font=font,
                                               text='Queen')
        king_stack.cap.base_rank = KING
        queen_stack.cap.base_rank = QUEEN

    def startGame(self):
        self.startDealSample()
        self.s.talon.dealRow()
        self.s.talon.dealCards()

    def fillStack(self, stack):
        pass

    shallHighlightMatch = Game._shallHighlightMatch_RK


# ************************************************************************
# * Minerva
# ************************************************************************

class Minerva(Canfield):
    RowStack_Class = KingAC_RowStack

    FILL_EMPTY_ROWS = 0
    INITIAL_RESERVE_CARDS = 11

    def createGame(self):
        Canfield.createGame(self, rows=7, max_rounds=2, num_deal=1,
                            text=False, round_text=True)

    def startGame(self):
        self.s.talon.dealRow(frames=0, flip=0)
        self.s.talon.dealRow(frames=0)
        self.s.talon.dealRow(frames=0, flip=0)
        self.startDealSample()
        self.s.talon.dealRow()
        for i in range(self.INITIAL_RESERVE_CARDS):
            self.moveMove(
                1, self.s.talon, self.s.reserves[0], frames=4, shadow=0)
        self.flipMove(self.s.reserves[0])
        self.s.talon.dealCards()

    shallHighlightMatch = Game._shallHighlightMatch_AC

    def _restoreGameHook(self, game):
        pass

    def _loadGameHook(self, p):
        pass

    def _saveGameHook(self, p):
        pass


# ************************************************************************
# * Demon
# ************************************************************************

class Demon(Canfield):
    INITIAL_RESERVE_CARDS = 40
    RowStack_Class = StackWrapper(AC_RowStack, mod=13)

    def createGame(self):
        Canfield.createGame(
            self, rows=8, max_rounds=UNLIMITED_REDEALS, num_deal=3)


# ************************************************************************
# * Canfield Rush
# ************************************************************************

class CanfieldRush_Talon(WasteTalonStack):
    def dealCards(self, sound=False):
        self.num_deal = 4-self.round
        return WasteTalonStack.dealCards(self, sound=sound)


# ************************************************************************
# * Skippy
# ************************************************************************

class Skippy(Canfield):
    FILL_EMPTY_ROWS = 0

    def createGame(self):
        # create layout
        lay, s = Layout(self), self.s

        # set window
        playcards = 8
        w0 = lay.XS+playcards*lay.XOFFSET
        w = lay.XM+lay.XS//2+max(10*lay.XS, lay.XS+4*w0)
        h = lay.YM+5*lay.YS+lay.TEXT_HEIGHT
        self.setSize(w, h)

        # extra settings
        self.base_card = None

        # create stacks
        x, y = lay.XM, lay.YM
        s.talon = WasteTalonStack(x, y, self, max_rounds=1)
        lay.createText(s.talon, 's')
        x += lay.XS
        s.waste = WasteStack(x, y, self)
        lay.createText(s.waste, 's')
        x = self.width - 8*lay.XS
        for i in range(8):
            s.foundations.append(SS_FoundationStack(x, y, self,
                                                    suit=i % 4, mod=13))
            x += lay.XS
        tx, ty, ta, tf = lay.getTextAttr(None, "ss")
        tx, ty = x-lay.XS+tx, y+ty
        font = self.app.getFont("canvas_default")
        self.texts.info = MfxCanvasText(self.canvas, tx, ty,
                                        anchor=ta, font=font)
        x, y = lay.XM, lay.YM+lay.YS+lay.TEXT_HEIGHT
        for i in range(4):
            s.reserves.append(ReserveStack(x, y, self))
            y += lay.YS
        y = lay.YM+lay.YS+lay.TEXT_HEIGHT
        for i in range(4):
            x = lay.XM+lay.XS+lay.XS//2
            for j in range(4):
                stack = RK_RowStack(x, y, self, max_move=1, mod=13)
                s.rows.append(stack)
                stack.CARD_XOFFSET, stack.CARD_YOFFSET = lay.XOFFSET, 0
                x += w0
            y += lay.YS

        # define stack-groups
        lay.defaultStackGroups()

    def startGame(self):
        self.base_card = None
        self.updateText()
        # deal base_card to Foundations, update foundations cap.base_rank
        self.base_card = self.s.talon.getCard()
        for s in self.s.foundations:
            s.cap.base_rank = self.base_card.rank
        n = self.base_card.suit
        self.flipMove(self.s.talon)
        self.moveMove(1, self.s.talon, self.s.foundations[n], frames=0)
        self.updateText()
        # update rows cap.base_rank
        row_base_rank = (self.base_card.rank-1) % 13
        for s in self.s.rows:
            s.cap.base_rank = row_base_rank
        #
        self._startDealNumRowsAndDealRowAndCards(3)

    shallHighlightMatch = Game._shallHighlightMatch_RKW


# ************************************************************************
# * Club
# ************************************************************************

class Club_RowStack(AC_RowStack):
    def acceptsCards(self, from_stack, cards):
        if self.id > 2 and from_stack.id < 3:
            return False
        return AC_RowStack.acceptsCards(self, from_stack, cards)


class Club(Game):

    def createGame(self):
        # create layout
        lay, s = Layout(self), self.s

        # set window
        playcards = 8
        w0 = lay.XS+playcards*lay.XOFFSET
        w = lay.XM+lay.XS//2+max(10*lay.XS, lay.XS+4*w0)
        h = lay.YM+4*lay.YS+lay.TEXT_HEIGHT
        self.setSize(w, h)

        # create stacks
        y = lay.YM + lay.YS + lay.TEXT_HEIGHT
        x = lay.XM + lay.XS + lay.XS // 2 + (w0 // 2)
        for j in range(3):
            stack = Club_RowStack(x, y, self, max_move=1)
            s.rows.append(stack)
            stack.CARD_XOFFSET, stack.CARD_YOFFSET = lay.XOFFSET, 0
            x += w0
        y += lay.YS
        for i in range(2):
            x = lay.XM + lay.XS + lay.XS // 2
            for j in range(4):
                stack = Club_RowStack(x, y, self, max_move=1)
                s.rows.append(stack)
                stack.CARD_XOFFSET, stack.CARD_YOFFSET = lay.XOFFSET, 0
                x += w0
            y += lay.YS

        x, y = lay.XM, lay.YM
        s.talon = WasteTalonStack(x, y, self, max_rounds=1)
        lay.createText(s.talon, 's')
        x += lay.XS
        s.waste = WasteStack(x, y, self)
        lay.createText(s.waste, 's')
        x = self.width - 8*lay.XS
        for i in range(8):
            s.foundations.append(SS_FoundationStack(x, y, self,
                                                    suit=i % 4, mod=13))
            x += lay.XS

        # define stack-groups
        lay.defaultStackGroups()

    def startGame(self):
        self.startDealSample()
        self.s.talon.dealRow(rows=self.s.rows, flip=0, frames=0)
        self.s.talon.dealRow(rows=self.s.rows, flip=1, frames=0)
        self.s.talon.dealRow()
        self.s.talon.dealCards()


# register the game
registerGame(GameInfo(105, Canfield, "Canfield",                # was: 262
                      GI.GT_CANFIELD | GI.GT_CONTRIB, 1, -1, GI.SL_BALANCED))
registerGame(GameInfo(101, SuperiorCanfield, "Superior Canfield",
                      GI.GT_CANFIELD, 1, -1, GI.SL_BALANCED))
registerGame(GameInfo(108, Rainbow, "Rainbow",
                      GI.GT_CANFIELD, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(100, Storehouse, "Storehouse",
                      GI.GT_CANFIELD, 1, 2, GI.SL_BALANCED,
                      altnames=("Provisions", "Straight Up", "Thirteen Up",
                                "The Reserve")))
registerGame(GameInfo(315, Gate, "Gate",
                      GI.GT_CANFIELD, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(422, Minerva, "Minerva",
                      GI.GT_CANFIELD, 1, 1, GI.SL_BALANCED))
registerGame(GameInfo(476, Demon, "Demon",
                      GI.GT_CANFIELD, 2, -1, GI.SL_BALANCED))
registerGame(GameInfo(527, Doorway, "Doorway",
                      GI.GT_KLONDIKE, 1, 0, GI.SL_BALANCED,
                      altnames=('Solstice',)))
registerGame(GameInfo(605, Skippy, "Skippy",
                      GI.GT_FAN_TYPE, 2, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(947, Club, "Club",
                      GI.GT_FAN_TYPE, 2, 0, GI.SL_BALANCED))
