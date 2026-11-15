# Tests for the restricted loader of saved games and the old options file.

import io
import os
import pickle
import tempfile
import unittest

import pysollib.games  # noqa: F401  (registers the games)
from pysollib.game import GameMoves, _alt_unpickler
from pysollib.mfxutil import unpickle


def _dumps(obj, protocol=1):
    f = io.BytesIO()
    pickle.Pickler(f, protocol).dump(obj)
    return f.getvalue()


class SavedGameLoaderTests(unittest.TestCase):
    def test_plain_data_loads(self):
        data = {'a': [1, 2.5, "x", (3, 4)], 'b': {"c": None}}
        for protocol in (0, 1, 2, 5):
            got = _alt_unpickler(io.BytesIO(_dumps(data, protocol))).load()
            self.assertEqual(got, data)

    def test_known_class_loads(self):
        moves = GameMoves()
        moves.index = 7
        got = _alt_unpickler(io.BytesIO(_dumps(moves, 5))).load()
        self.assertEqual((type(got), got.index), (GameMoves, 7))

    def test_calls_are_refused(self):
        payloads = [
            b"cbuiltins\nprint\n(S'x'\ntR.",
            b"cos\nsystem\n(S'echo x'\ntR.",
            b"cpysollib.mfxutil\nopenURL\n(S'file:///x'\ntR.",
            b"cbuiltins\ngetattr\n(cbuiltins\nstr\nS'upper'\ntR.",
        ]
        for payload in payloads:
            with self.assertRaises(pickle.UnpicklingError):
                _alt_unpickler(io.BytesIO(payload)).load()


class OldOptionsLoaderTests(unittest.TestCase):
    def _write(self, data):
        fd, name = tempfile.mkstemp()
        self.addCleanup(os.remove, name)
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
        return name

    def test_calls_are_refused(self):
        name = self._write(b"cos\nsystem\n(S'echo x'\ntR.")
        with self.assertRaises(pickle.UnpicklingError):
            unpickle(name)

    def test_plain_data_loads(self):
        self.assertEqual(unpickle(self._write(_dumps([1, "a"]))), [1, "a"])


if __name__ == '__main__':
    unittest.main()
