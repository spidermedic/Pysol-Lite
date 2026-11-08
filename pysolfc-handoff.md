# PySolFC on macOS 27: handoff

Written 2026-11-07. Audience: another agent (or future session) continuing this work with no memory of it.
Facts marked **(verified)** were observed on this Mac. Facts marked **(reported)** come from a CPython issue thread read by a fetch subagent, not seen directly.

## 1. Outcome in one paragraph

PySolFC.app 3.7.0 (the official py2app bundle) freezes with a spinning beachball whenever a settings dialog opens, on macOS 27.2. The cause is a Tk bug, not PySolFC code. The working fix is to run PySolFC from source in a venv built on python.org Python 3.13.17, whose Tk build has the fix. That setup is running and confirmed working by the user. The old `/Applications/PySolFC.app` was removed.

## 2. Current state (verified)

| Piece | Location |
|---|---|
| Launcher (Dock icon) | `~/Applications/PySolFC (fixed).app` |
| Program: PySolFC 3.7.0 from GitHub source + pillow, pygame-ce, random2 | `~/pysolfc-venv` |
| Data (html, cardset-*, 78 MB) | `~/pysolfc-venv/share/PySolFC` (real copies, not symlinks) |
| Python | `/Library/Frameworks/Python.framework` (python.org 3.13.17) |
| Settings, saves, stats | `~/.PySolFC` |
| Manual run | `~/pysolfc-venv/bin/pysol.py` |
| **Editable source (git clone of `spidermedic/pysol`, `master` = 3.7.0 + "Fix all games script")** | `~/Documents/Claude/pysol` |
| Dev venv for the clone (python.org 3.13.17, Tk 8.6.18; attrs, configobj, pysol_cards, pillow, pygame-ce) | `~/Documents/Claude/pysol/.venv` |

- The launcher is an AppleScript applet (made with `osacompile`) that runs `nohup ~/pysolfc-venv/bin/python ~/pysolfc-venv/bin/pysol.py &` with output discarded. It uses the PySolFC `PySol.icns` icon. The running game shows as "Python" in the Dock, which is cosmetic.
- `~/.PySolFC/options.cfg` has `sound = False`, `music = False`, and the standard 52-card entries (`0`, `1`, `1_1`, `10` under `[cardsets]`) set to `Standard`. Only edit this file while PySolFC is closed, because the app rewrites it on exit.
- Harmless warning at startup: `invalid theme name: ubuntu`.
- Do not delete `~/pysolfc-venv`, the launcher, or the python.org Python.

## 3. Diagnosis

1. The official app is a py2app bundle: a 184 KB compiled launcher (`Contents/MacOS/PySolFC`, universal arm64/x86_64) that embeds Python 3.11 and Tk 8.6 (`Resources/lib/python3.11`, `Contents/Frameworks`). The program is Python (`Resources/pysol.py`, `pysollib`). It does not use the system Python.
2. Symptom: main window works; opening any modal dialog from a menu item (Options, Cardsets, Sound) beachballs and nothing responds. CPU is about 0.3%, no crash log, no stderr output.
3. `sample <pid> 3` showed the main thread inside `MenuBarClientCore` -> `NSMenu` action -> Tk -> a nested `Tcl_DoOneEvent` that blocks in `mach_msg2_trap`. The menu callback never returns, so the dialog never gets events.
4. This matches **(reported)** python/cpython#158053, "IDLE on macOS 27 hangs when a menu command opens a dialog", Tk ticket 33b3af1ceac681ad0f77, Apple feedback FB24915676. macOS 27 delivers menu clicks through MenuBarClientCore while Tk is already in its event loop. Tk's fix defers menu commands with `after idle`. It was merged into Tk 8.6 and 9.0 branches in October 2026.
5. **(reported)** The fix ships in python.org installers 3.13.17, 3.14.9, 3.15.1 (released 2026-10-21), which include pre-release Tk 8.6.19 or 9.0.5 builds. The issue states there is no known workaround for older Tk on macOS 27.

## 4. What was tried

| Attempt | Result |
|---|---|
| Turn off sound (first guess) | Not related to the hang. The hang is any dialog. |
| Toolbar buttons instead of menu items | User reported menu items other than settings dialogs work; dialogs still hang. Not separately confirmed for toolbar. |
| Edit `options.cfg` to avoid dialogs | Works as a workaround (sound off, cardset set). |
| uv standalone Pythons 3.11 to 3.14 | All bundle **Tk 9.0.4**, which is affected. Dialogs still beachballed. Removed. |
| python.org Python 3.13.17 + venv | **Works.** `info patchlevel` reports `8.6.18`, but the build contains the fix (the version string is not a reliable indicator for this pre-release build). |

## 5. How to recreate from scratch

1. Download `https://www.python.org/ftp/python/3.13.17/python-3.13.17-macos11.pkg` (3.13.18 has no installer). Check with `pkgutil --check-signature` (signed by Python Software Foundation, notarized). Install with `sudo installer -pkg <file> -target /`. This needs a real TTY for the password, so the user must run it (`! sudo ...`).
2. Get the source. Original recipe: `curl -sL https://api.github.com/repos/shlomif/PySolFC/tarball/pysolfc-3.7.0 | tar -xz -C <empty dir> --strip-components=1`. For the user's own fork, use `git clone https://github.com/spidermedic/pysol.git` instead (this is what `~/Documents/Claude/pysol` is). PySolFC is **not on PyPI** (`pip install pysolfc` fails).
3. `/Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13 -m venv ~/pysolfc-venv`, then `~/pysolfc-venv/bin/pip install <src dir> pillow pygame-ce random2`.
4. The source install lacks the `html` folder and the `cardset-*` folders. Generate html with `make rules all_games_html` (verified on the clone). Cardsets must still be copied into `~/pysolfc-venv/share/PySolFC` from an official `PySolFC.app/Contents/Resources/data` (the PySolFC release DMG). Without them startup fails: `OSError: DataLoader could not find ('html/license.html',)`.
5. Run `~/pysolfc-venv/bin/pysol.py`.

## 6. Gotchas

- **zsh:** `"$i:tile-data"` is parsed as the `:t` modifier. Use `${i}` in strings (this broke a PlistBuddy command once).
- **Dock icons** point at a file path. Moving the app requires editing `com.apple.dock` `persistent-apps[*].tile-data.file-data._CFURLString` (PlistBuddy), then `killall cfprefsd; killall Dock`.
- **Downloads:** extract archives into their own empty directory and run nothing from inside it.
- **sudo** needs a real TTY in this environment.
- Don't run the app launcher and a hand-started instance at once: they share `~/.PySolFC/options.cfg`. This includes the dev copy (`.venv` in the clone).
- **Two copies of the program exist.** The launcher runs the pip-installed copy in `~/pysolfc-venv`, not the clone. Edits in the clone have no effect on the Dock app. Run the clone with `cd ~/Documents/Claude/pysol && source .venv/bin/activate && python pysol.py`.
- **Dev copy needs generated docs:** `export PYTHONPATH=$PWD && make rules all_games_html` creates `data/html` (gitignored). Without it: `DataLoader could not find ('html/license.html',)`. This replaces copying `html` out of the official app (section 5, step 4).
- **Cardsets are not in the repo; they are a separate download (verified by reading the repo, not by downloading).** The upstream macOS CI (`.github/workflows/macos-package.yml`, step "Get cardsets") fetches `https://sourceforge.net/projects/pysolfc/files/PySolFC-Cardsets/minimal/PySolFC-Cardsets--Minimal-3.1.0.tar.xz/download`, extracts it, and moves `PySolFC-Cardsets--Minimal-3.1.0/cardset-*` into `data/`. The "minimal" set is the list in `scripts/cardsets_to_bundle` (28 sets, built by `scripts/repack-min-cardsets.bash` from the full `PySolFC-Cardsets-3.0` archive). The full set is also on SourceForge (`PySolFC-Cardsets-3.0.tar.bz2`), with sources at https://github.com/shlomif/PySolFC-Cardsets. For a plain source run, README says to unpack the full set and symlink it to `~/.PySolFC/cardsets`. Not yet downloaded in the clone.
- **`msgfmt` is not installed**, so `make mo` fails and the dev copy has no translations (English only). `brew install gettext` fixes it.
- Attempting to script menu clicks with `osascript`/System Events fails (-1719, no assistive access), so dialog testing needs a human click.

## 7. Plans and open items

The user says they are recreating and expanding this project. Their expansion goals were **not** stated in this session, so the items below are candidates from the discussion, not commitments. Confirm with the user before acting.

0. **Dialog test of the dev copy (`.venv` in the clone) is pending.** It launched and stayed up, but no menu dialog (Options, Cardsets, Sound) has been opened yet. Same Python/Tk as the working launcher, so it should pass, but confirm by hand before building on it.
1. **Primary goal (stated by the user): stop using the launcher and build the program from the clone.** Rebuild a proper `PySolFC.app` with py2app on python.org Python 3.13.17, using `setup_osx.py` from the clone The upstream recipe already exists in `.github/workflows/macos-package.yml`: install python.org Python, `pip install --no-binary=Pillow Pillow attrs configobj py2app pycotap pygame-ce pysol-cards setuptools ttkthemes accessible-output2`, restore pygame-ce's missing `freesansbold.ttf` and `pygame_icon.icns` (pygame-ce#2780), fetch the minimal cardsets into `data/`, run `make rules mo`, then `PYTHONPATH=. python3 setup_osx.py py2app`, verify universal2 with `lipo -archs`, and package with `create-dmg`. **That CI pins `PYVER: '3.11.9'`, which is why the official app has the Tk bug.** Bumping it to 3.13.17 is the likely whole fix. Needs `gettext` (for `mo`) locally. Benefits: correct Dock name and icon, one self-contained bundle. Risks: the build script may be stale for a new Python/py2app, data packaging (html, cardsets), Gatekeeper/quarantine and code signing for an unsigned local app. Not attempted.
2. **Report to PySolFC upstream** (github.com/shlomif/PySolFC) so the official app is rebuilt with a fixed Tk. Draft the issue text for the user to post. Do not post it for them. Cite python/cpython#158053 and Tk ticket 33b3af1cea.
3. **Re-check the official app later.** When a PySolFC release after 3.7.0 appears with Tk 8.6.19+ or 9.0.5+, test dialogs and consider going back to the stock app.
4. **Cosmetic:** make the Dock name "PySolFC" instead of "Python" (a py2app rebuild fixes this).
5. **Optional cleanup:** the startup `invalid theme name: ubuntu` warning comes from the saved theme in `options.cfg`. Setting a valid ttk theme would silence it. Untested.

## 8. Related notes

- Memory note: `/Users/doug/.claude/projects/-Users-doug/memory/pysolfc_macos27_tk_hang.md`, indexed in `MEMORY.md` (keyed to the `/Users/doug` project folder; sessions started in `~/Documents/Claude/pysol` do not load it automatically).
- Shorter summary: `~/pysolfc-venv/README-setup.md`.

## 9. Sources

- https://github.com/python/cpython/issues/158053
- https://core.tcl-lang.org/tk/tktview/33b3af1ceac681ad0f77
- https://github.com/shlomif/PySolFC/issues/100 (older, unrelated macOS startup issue)

## 10. Update 2026-11-07: arm64 py2app build from the clone (verified)

Built `dist/PySolFC.app` from `~/Documents/Claude/pysol` on python.org 3.13.17. Gameplay confirmed working by the user. The dialog (Options/Cardsets/Sound) check had not been reported when this was written.

Build steps (all from the clone; env: `PYTHONPATH=$PWD`, `PATH=/opt/homebrew/opt/gettext/bin:$PATH`):
1. `brew install gettext`; create `.build-venv` with python.org 3.13 and `pip install py2app setuptools attrs configobj pillow pycotap pygame-ce pysol-cards ttkthemes accessible-output2`.
2. Download `PySolFC-Cardsets--Minimal-3.1.0.tar.xz` (URL in section 6), extract into a separate empty dir, move `cardset-*` into `data/`.
3. Copy `pygame_icon.icns` from `https://raw.githubusercontent.com/pygame-community/pygame-ce/<version>/src_py/pygame_icon.icns` into the venv's `pygame/` dir (pygame-ce#2780).
4. `make rules mo` (rebuilds tracked `locale/*/pysol.mo`; new gettext changes their bytes, not committed).
5. `.build-venv/bin/python setup_osx.py py2app --arch arm64`.
6. **arm64 only (no Rosetta/x86_64):** `--arch arm64` only affects the stub launcher; python.org's Python, Tk and OpenSSL stay universal. Run `lipo -thin arm64` on every Mach-O file that has an x86_64 slice (loop over all files with `lipo -archs`; write back with `cat thin > file` to keep the exec bit). 229 MB -> 182 MB.
7. `xattr -cr dist/PySolFC.app` then `codesign --force --deep --sign - dist/PySolFC.app` (iCloud-synced Documents adds xattrs that break the seal).

**Bug found and fixed:** the first bundle let cards be dropped anywhere. Cause: `accessible_output2` was bundled but its VoiceOver backend imports `appscript` lazily; py2app missed it (and `appscript`'s relative `.pth` does not work on Python 3.13 anyway), so `pysollib/speech.py` raised `ModuleNotFoundError` on every card release and aborted the drop handler. Fix: `speech.py` now treats any speech-backend failure as "unsupported". Side effect: no VoiceOver speech in this build.

Still open: dialog check on the built app; upstream `.github/workflows/macos-package.yml` still pins Python 3.11.9 and builds universal2; app not yet installed to `~/Applications` or the Dock.

## 11. Update: old setup removed (2026-11-07)

The user confirmed gameplay and cardset dialogs work in the new build. Installed to `~/Applications/PySolFC.app` (arm64, ad-hoc signed) and the Dock tile now points to it. **Deleted:** `~/Applications/PySolFC (fixed).app` and `~/pysolfc-venv`. Sections 2, 5 and the "do not delete" note above describe that retired setup and are historical. Still required for rebuilding: python.org Python 3.13.17 and the clone's `.build-venv`. To update the installed app after a rebuild: `ditto dist/PySolFC.app ~/Applications/PySolFC.app`, then `xattr -cr` and `codesign --force --deep --sign -` on it.
