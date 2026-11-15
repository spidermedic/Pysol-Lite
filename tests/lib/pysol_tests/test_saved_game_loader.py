# Tests for the restricted loader of saved games and the old options file.

import io
import os
import pickle
import tempfile
import unittest

import pysollib.games  # noqa: F401  (registers the games)
from pysollib.game import GameMoves, _alt_unpickler, _safe_getattr
from pysollib.mfxutil import Struct, unpickle


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

    def test_known_class_loads_in_every_protocol(self):
        # bookmarks are written with protocol 1, which builds a plain
        # object with copy_reg._reconstructor and names the built-in
        # module __builtin__ (go to bookmark broke on both)
        for protocol in range(0, 6):
            moves = GameMoves()
            moves.index = 3
            got = _alt_unpickler(io.BytesIO(_dumps(moves, protocol))).load()
            self.assertEqual((type(got), got.index), (GameMoves, 3), protocol)

    def test_struct_and_bytes_load_in_every_protocol(self):
        for protocol in range(0, 6):
            data = Struct(a=1, b=[2, 3], c=b"\x00\xffabc")
            got = _alt_unpickler(io.BytesIO(_dumps(data, protocol))).load()
            self.assertEqual((got.a, got.b, got.c),
                             (1, [2, 3], b"\x00\xffabc"))

    def test_old_names_still_only_allow_the_known_functions(self):
        u = _alt_unpickler(io.BytesIO(b""))
        for module in ('builtins', '__builtin__'):
            self.assertIs(u.find_class(module, 'getattr'), _safe_getattr)
            self.assertIs(u.find_class(module, 'object'), object)
            for name in ('eval', 'exec', 'open', '__import__', 'compile'):
                with self.assertRaises(pickle.UnpicklingError):
                    u.find_class(module, name)
        self.assertEqual(u.find_class('_codecs', 'encode')("abc", "latin1"),
                         b"abc")
        for args in (("abc", "rot13"), ("abc", "zlib"), (b"abc", "latin1")):
            with self.assertRaises(pickle.UnpicklingError):
                u.find_class('_codecs', 'encode')(*args)
        with self.assertRaises(pickle.UnpicklingError):
            _safe_getattr(object(), 'system')

    def test_old_protocol_payloads_are_refused(self):
        payloads = [
            # copy_reg._reconstructor builds only classes that pass the check
            b"ccopy_reg\n_reconstructor\n(csubprocess\nPopen\n"
            b"c__builtin__\nobject\nNtR.",
            b"ccopy_reg\n_reconstructor\n(c__builtin__\neval\n"
            b"c__builtin__\nobject\nNtR.",
            b"c__builtin__\neval\n(S'1'\ntR.",
            b"c__builtin__\ngetattr\n(cos\nsystem\nS'x'\ntR.",
            b"c_codecs\nencode\n(S'x'\nS'zlib'\ntR.",
        ]
        for payload in payloads:
            with self.assertRaises(pickle.UnpicklingError):
                _alt_unpickler(io.BytesIO(payload)).load()

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
