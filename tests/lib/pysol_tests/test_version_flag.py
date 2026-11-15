# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2022 Shlomi Fish <shlomif@cpan.org>
#
# Written by Shlomi Fish, under the MIT Expat License.

import os
import re
import subprocess
import sys
import unittest

# the repository root: tests/lib/pysol_tests/ is three levels below it
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))


class CliFlagsTests(unittest.TestCase):
    def test_main(self):
        if os.name == 'nt':
            self.assertTrue(True)
            return
        # Run it with the interpreter running the tests, not whatever
        # "python" is on the PATH (there may be none), and from the root.
        env = dict(os.environ, PYTHONPATH=ROOT)
        o = subprocess.check_output(
            [sys.executable, os.path.join(ROOT, "pysol.py"), "--version"],
            cwd=ROOT, env=env, stderr=subprocess.DEVNULL)
        assert o
        string = o.decode('utf-8')
        self.assertTrue(
            re.match("\\APySol Lite version [0-9]+\\.[0-9]+", string),
            string)
