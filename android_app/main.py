"""Entry point of the Android app (Buildozer needs a file named main.py).

Starts PySol Lite with the Kivy user interface."""
import os
import sys

if '--kivy' not in sys.argv:
    sys.argv.append('--kivy')

from pysollib.init import init  # noqa: E402

init()

from pysollib.main import main  # noqa: E402

os.environ['KIVY_NO_CONSOLELOG'] = "No"
sys.exit(main(sys.argv))
