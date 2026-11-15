<p align="center">
  <img src="logo/pysol-lite-logo-horizontal.png" alt="PySol Lite" width="420">
</p>

# PySol Lite

A lighter PySol: 276 solitaire and patience games, written in Python with
Tkinter. This fork focuses on macOS on Apple Silicon. The Windows and Linux
code is kept but has not been run since the clean-up. The version number is
the year and month (for example 26.11).

PySol Lite is based on PySol by Markus F.X.J. Oberhumer, the PySol Fan Club
edition and [PySolFC](https://github.com/shlomif/PySolFC), and is licensed
under the GNU General Public License, version 3 (see `LICENSE.md`).
`PROGRESS-NOTES.md` is the working log of what has changed and why.

## What it has

- 276 games in 22 categories (Klondike, FreeCell, Spider, Yukon, Forty
  Thieves, Pairing, Mahjongg, Cribbage, Poker and more), each with its own
  rules page in the built-in help.
- A Select game dialog with a live preview, name search (including alternate
  names) and a category filter, plus Recent, Favorite and Popular games in
  the Games menu.
- Toolbar buttons for favorite (heart) and bookmark, unlimited undo and redo,
  hints, and optional automatic play.
- One Settings window, and screen reader support (see Accessibility in the
  help).

## Requirements

- Python 3.10 or later, with Tkinter (Tcl/Tk 8.6 or later).
- Pillow, `attrs`, `configobj` and `pysol-cards`.
- Optional: `pygame-ce` for sound, `accessible-output2` for screen readers.
- To build the macOS app: `py2app`, `setuptools` and `markdown`
  (the License page of the help is built from `LICENSE.md`), and the
  python.org Python 3.14.10 or later installer (Tk 9: it has the fix for
  dialogs opened from menus freezing on macOS 27, and it redraws the canvas
  about 25 times faster than Tk 8.6).

## Build and install the macOS app

This is the tested procedure (Apple Silicon, arm64 only). A folder that is
not iCloud-synced is best: iCloud adds duplicate folders and extended
attributes that break the build and the code signature (see the notes
below).

1. Create a build environment:

   ```
   python3 -m venv .build-venv
   .build-venv/bin/pip install py2app setuptools attrs configobj pillow \
       pygame-ce pysol-cards accessible-output2 markdown
   ```

2. Get the cardsets. They are a separate download and are not in git. Download
   `PySolFC-Cardsets--Minimal-3.1.0.tar.xz` from the
   [PySolFC cardsets page](https://sourceforge.net/projects/pysolfc/files/PySolFC-Cardsets/minimal/),
   extract it into its own empty folder, and copy `cardset-standard` and
   `cardset-uni-mahjongg` into `data/`. The build removes every other cardset
   and trims the card backs (`scripts/prune_card_backs.py`).

3. Generate the help pages with the build environment's Python (the system
   Python lacks the `attr` module and `make` then fails without saying so):

   ```
   PATH="$PWD/.build-venv/bin:$PATH" make rules
   ls data/html/rules/*.html | wc -l      # 256 pages
   ```

4. Build the app:

   ```
   PYTHONPATH=$PWD .build-venv/bin/python setup_osx.py py2app --arch arm64
   ```

   If py2app stops because `pygame_icon.icns` is missing from the `pygame`
   package, copy it from the pygame-ce source of the installed version
   (`src_py/pygame_icon.icns`, see pygame-ce issue 2780).

5. The bundled Python is still universal, so remove the Intel code from every
   Mach-O file:

   ```
   find "dist/PySol Lite.app" -type f -print0 | while IFS= read -r -d '' f; do
     if file "$f" | grep -q Mach-O && lipo -archs "$f" | grep -q x86_64 \
        && lipo -archs "$f" | grep -q arm64; then
       lipo -thin arm64 "$f" -output /tmp/thin && cat /tmp/thin > "$f"
     fi
   done
   ```

6. Sign a clean copy and install it. Quit PySol Lite first, since replacing a
   running app causes trouble:

   ```
   ditto --norsrc --noextattr --noqtn "dist/PySol Lite.app" /tmp/PySolLite/"PySol Lite.app"
   codesign --force --deep --sign - /tmp/PySolLite/"PySol Lite.app"
   codesign -v /tmp/PySolLite/"PySol Lite.app"
   ditto --norsrc --noextattr --noqtn /tmp/PySolLite/"PySol Lite.app" ~/Applications/"PySol Lite.app"
   ~/Applications/"PySol Lite.app"/Contents/MacOS/"PySol Lite" --version
   ```

Things that go wrong:

- **iCloud duplicates.** iCloud can create copies such as `data/html 2` or
  `accessibility 2.html`, and py2app then bundles them. Before building,
  `ls -d data/html*` should print only `data/html`; after building,
  `find dist -name "* [0-9].*" -o -name "* [0-9]"` should print nothing.
- **Settings.** The app stores its settings and saved games in `~/.pysol`.
  Checking a build with `--version` does not touch them; launching the app
  does.

`PROGRESS-NOTES.md` has the full history and more detail.

## Run from source

On macOS, with the cardsets in `data/` and the help pages generated as above:

```
PYTHONPATH=$PWD .build-venv/bin/python pysol.py
```

To run the tests:

```
PYTHONPATH=$PWD .build-venv/bin/python -m unittest discover -s . -p 'test*.py'
```

All 13 tests pass (`test_version_flag` runs `pysol.py --version` with the
same Python that runs the tests).

## Windows and Linux (untested)

The Windows and Linux code is still in the tree, but nothing has been run
there since the clean-up, and this fork provides no installers. If you want
to try, install Python, Tkinter and the packages above, put the cardsets in
`~/.pysol/cardsets`, generate the help pages with `make rules`, and run
`python pysol.py`. The upstream
[PySolFC](https://github.com/shlomif/PySolFC) README has install instructions
for those platforms; `contrib/install-pysolfc.sh` comes from there and has
not been tested here.

## Credits

The credits page in the built-in help (Help, Contents, then Credits) lists the
people who contributed to PySol, PySolFC and this fork. The toolbar icons are
[Phosphor Icons](https://phosphoricons.com/) (MIT license).
