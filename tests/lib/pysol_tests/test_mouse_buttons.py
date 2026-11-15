# Tests for the mouse buttons of the card piles on macOS: Tk 8.6 reported the
# two-finger tap as button 2 and Tk 9 reports it as button 3, so the card piles
# exchange buttons 2 and 3 on a Mac with Tk 9 (a two-finger tap shows a
# partially covered card, as it always did).

import unittest
from unittest import mock

import pysollib.settings
from pysollib.options import Options, _mac_tk9_exchange


def _on(system, tk_version):
    return (mock.patch.object(pysollib.settings, 'WIN_SYSTEM', system),
            mock.patch('tkinter.TkVersion', tk_version))


class MouseButtonTests(unittest.TestCase):
    def _bind(self, fmt, cards, system, tk_version):
        p1, p2 = _on(system, tk_version)
        with p1, p2:
            return Options().calcCustomMouseButtonsBinding(fmt, cards=cards)

    def test_buttons_are_exchanged_for_cards_on_a_mac_with_tk9(self):
        self.assertEqual(self._bind('<{mouse_button1}>', True, 'aqua', 9.0),
                         '<1>')
        self.assertEqual(self._bind('<{mouse_button2}>', True, 'aqua', 9.0),
                         '<3>')
        self.assertEqual(self._bind('<{mouse_button3}>', True, 'aqua', 9.0),
                         '<2>')

    def test_nothing_changes_anywhere_else(self):
        for system, tk in (('aqua', 8.6), ('x11', 9.0), ('win32', 9.0),
                           ('x11', 8.6)):
            for n in (1, 2, 3):
                self.assertEqual(
                    self._bind('<{mouse_button%d}>' % n, True, system, tk),
                    '<%d>' % n, (system, tk, n))

    def test_the_toolbar_and_other_bindings_keep_the_real_numbers(self):
        for n in (1, 2, 3):
            self.assertEqual(
                self._bind('<{mouse_button%d}>' % n, False, 'aqua', 9.0),
                '<%d>' % n)

    def test_a_swapped_ini_setting_keeps_its_meaning(self):
        # an options file that swaps the buttons: the exchange is applied on
        # top, as for the default buttons
        p1, p2 = _on('aqua', 9.0)
        with p1, p2:
            o = Options()
            o.mouse_button2, o.mouse_button3 = 3, 2
            self.assertEqual(
                o.calcCustomMouseButtonsBinding('<{mouse_button2}>', True),
                '<2>')
            self.assertEqual(
                o.calcCustomMouseButtonsBinding('<{mouse_button3}>', True),
                '<3>')

    def test_only_buttons_2_and_3_are_exchanged(self):
        p1, p2 = _on('aqua', 9.0)
        with p1, p2:
            self.assertEqual([_mac_tk9_exchange(b) for b in (1, 2, 3, 4, 5)],
                             [1, 3, 2, 4, 5])


if __name__ == '__main__':
    unittest.main()
