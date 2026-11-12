# PySol Lite on macOS 27: progress notes

Written 2026-11-07 as `pysolfc-handoff.md` and renamed `PROGRESS-NOTES.md` on 2026-11-11 (the project is now PySol Lite; sections 1 to 41 still use the old PySolFC names). Audience: another agent (or future session) continuing this work with no memory of it.
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

## 12. Update: launch performance (2026-11-07)

Profiled launch with a throwaway cProfile wrapper (isolated `HOME`, copy of the real `options.cfg`, splash screen off, stop right after the first deal). Source run on `.venv`:
- **Before:** 2.41 s to first dealt game. ~1.55 s of that was `PysolProgressBar.update()` calling Tk `update()` ~375 times (~4 ms each on macOS).
- **Fix (commit `bf7d7a60`):** redraw at most every 50 ms (`REDRAW_INTERVAL` in `pysollib/tile/progressbar.py` and `pysollib/tk/progressbar.py`).
- **After:** ~0.85 s. The user confirmed launch is much faster and card play is fine in the rebuilt, installed app.
- Remaining launch costs (not addressed): menubar build ~0.34 s (game menu with 1,390 entries, `ui/tktile/menubar.py:1094`), game registry import ~0.17 s, pygame mixer init ~0.08 s even with sound off (`pysolaudio.py:526`).
- Lazy-loading the game modules was evaluated and rejected: the whole registry imports in ~55 ms warm.
- Play: ~8 ms CPU per move in a demo-mode profile; no hot spot found. Demo delays are deliberate hint pauses.
- Rebuild and install after changes: section 10 steps, then quit the app and `rm -rf ~/Applications/PySolFC.app && ditto dist/PySolFC.app ~/Applications/PySolFC.app`.

## 13. Update: animation fixes (2026-11-07)

Both found by the user while using the installed build; both verified with throwaway scripts using an isolated `HOME`.
- **Animation speed could not be changed back from "Very slow"** (commit `21996132`: "Apply animation speed changes even while the game is busy"). `mOptAnimations` in `pysollib/ui/tktile/menubar.py` returned early when `game.busy` was set. At speed 5 the opening deal animation runs 8-25 s, during which the game is busy, so the radio button moved but `opt.animations` did not; every new game/relaunch repeated it. The handler now always applies the value. The sibling handlers `mRedealAnimation` and `mFlipAnimation` have the same early-return pattern and were **not** changed.
- **"Very fast" was slower than "Fast"** (commit `66bcc41e`). In `Game.animatedMoveTo` (`pysollib/game/__init__.py`), mode 1 had no clock and drew all 8 frames with a `canvas.update()` each; on macOS one update costs about 45 ms. Measured per card move: very fast 365 ms, fast 181 ms, medium 408 ms. Mode 1 now uses the clock with `frames // 4` (min 2) and half the per-frame time: 93 ms vs 182 ms (fast) vs 410 ms (medium). Slow and very slow are unchanged.
- **Open observation:** one `canvas.update()` costing ~45 ms is unusually slow and inflates every animation mode. The cause has not been investigated.
- Installed app uses these fixes; the user's saved setting is now `animations = 1` in `~/.PySolFC/options.cfg`.

## 14. Update: table tiles and non-macOS toolkits removed (2026-11-08)

Goal stated by the user: a much cleaner app than the upstream fork it started from.

- **Table background is solid color only** (commit `0cae197e`). The "Table tile..." dialog became a native "Table color..." picker (`mSelectTableColor` in `pysollib/ui/tktile/menubar.py`). Reason: Tk 8.6 on macOS repaints every image on screen at ~30 ns/pixel on each canvas update, so the 54-tile felt background was about half of every ~46 ms repaint (now ~23 ms). Old option files naming a tile still load; the name is ignored. Tk 9.0.4 does not have this slow repaint (card move: very fast 12 ms vs 93 ms) but still has the macOS 27 dialog bug until 9.0.5 (python.org 3.14.9+ installers); moving the build to Python 3.14.9 would likely give both fixes. Not attempted.
- **Toolkits removed** (commit `beaeda99`): `pysollib/kivy`, `pysollib/pysolgtk`, `pysollib/tk` (classic non-ttk Tk fallback), Android/Kivy packaging (`buildozer/`, `fastlane/`, `README.android`, `README.kivy`) and `data/tiles` (28 MB). `TOOLKIT` and `USE_TILE` no longer exist; every conditional on them was resolved to the Tk + ttk behavior (about 100 places in `stack.py`, `game/__init__.py`, `app.py`, `main.py`, `options.py`, `winsystems/`, and the mahjongg/special games). The Kivy audio client and the Kivy-only generator in `app.py` are gone, so `Application.mainloop` now just calls `mainproc`. Net: 240 files, 25,168 lines deleted. App bundle 182 MB -> 154 MB.
- **Not removed (candidates for further cleanup):** `pysollib/winsystems/win32.py` and `x11.py` (Windows/Linux window-system setup; they still import and compile), `Win32AudioClient`/`OSSAudioClient` in `pysolaudio.py`, Windows/Linux packaging (`setup.py` Linux install, `appdata.xml`, `pysol.desktop`, `.github` Windows jobs, appveyor), `options.toolbar_land/toolbar_port` (Kivy-only settings still parsed), historical mentions in `NEWS.asciidoc`/`AUTHORS.md`/`appdata.xml`.
- **Verification used:** `python -m unittest discover -s . -p 'test*.py'` gives 19 tests with 1 pre-existing failure (`test_version_flag`: `./pysol.py` finds no `python` in this shell); import of all 189 `pysollib` modules; 1,390 games registered; 25 games dealt in the real app via `--game NAME`, including Mahjongg (Double Mahjongg Big Castle), Shisen-Sho, Sudoku, Samegame, Lights Out, Match Three, Hanoi, Ishido and Fission.
- **Build/sign procedure that works (supersedes section 10 step 7):** the iCloud-synced Documents folder re-adds Finder attributes, so `codesign` on `dist/PySolFC.app` fails ("resource fork, Finder information... not allowed"). Copy first: `ditto --norsrc --noextattr --noqtn dist/PySolFC.app <scratch>/PySolFC.app`, run `codesign --force --deep --sign - <scratch>/PySolFC.app`, check `codesign -v`, then install with `ditto --norsrc --noextattr --noqtn <scratch>/PySolFC.app ~/Applications/PySolFC.app` (only when the app is not running).
- **`setup_osx.py` fix:** it generated `docs/all_games.html` with `./scripts/all_games.py > docs/all_games.html` using the system Python, which lacks `attrs`; the shell redirect then left the file empty (and bundled it). It now runs `sys.executable`.
- Installed app: arm64 only, 154 MB, ad-hoc signed.

## 15. Decision: keep Windows/Linux code (2026-11-08)

The user wants to keep the Windows and Linux code (`pysollib/winsystems/win32.py`, `x11.py`, `Win32AudioClient`/`OSSAudioClient`, Windows/Linux packaging and install text) because they may compile the cleaned-up version for those platforms too. Treat the "Not removed" list in section 14 as intentionally kept, not pending cleanup. Caveat: the toolkit removal was only run and tested on macOS. The Windows/Linux window-system files were edited (the `USE_TILE` / `TOOLKIT` conditionals now always take the themed-ttk path), compile and import, but have not been run on those platforms. The upstream install help text (`html-src/install.html`) still describes upstream Windows/Linux/Mac distribution.

## 16. Build gotcha: regenerate the help pages after editing `html-src/`

`setup_osx.py` only builds `data/html` when that directory does not exist, so after editing anything in `html-src/` an ordinary `py2app` run bundles the old, stale pages. Run `make rules` first (it deletes and regenerates `data/html`), then build. The `.build-venv` Python must be first on `PATH` when running it (`PATH=$PWD/.build-venv/bin:$PATH make rules`) because `make rules` calls `gen-html.py` through the shell and needs the packages installed there. Verify by grepping the staged bundle, e.g. `grep -c "Table color" <app>/Contents/Resources/data/html/settings.html`.

## 17. Update: demo statistics removed (2026-11-08)

Asked by the user while reviewing the Game menu ("Demo statistics", "Demo log", "Comments" - Comments was kept: it attaches a note to a deal and appends it to `~/.PySolFC/comments.txt`).

- **Menu:** "Demo statistics..." and "Demo log..." removed from the Game menu (commit `98ea46bb`). They were the only way to open the statistics window in demo mode (the dialogs' own buttons all return codes below 1000). The Assist help text that pointed to the Demo Statistics window was updated.
- **Display code removed** (commit `4b74a102`): the demo branch in `mPlayerStats` and `_mStatsSave` (`pysollib/actions.py`), the "Demo Statistics"/"Demo Log"/"Demo games" labels in `pysollib/tile/tkstats.py`, the `player = _('Demo')` fallbacks in `pysollib/stats.py`. Also removed mode 102 (all-games statistics) and the `AllGames_StatsDialog` alias: nothing reached it, and it raised `TypeError` (StatsDialog requires a `gameid`) in the unmodified upstream code too.
- **Recording removed** (commit `e5d6b00a`): `Game.updateStats(demo=1)` no longer calls `app.stats.updateStats(None, ...)`, so no demo "player" is written to `statistics.dat`. Deliberately kept: `stats.demo_updated` is still set for a finished pure-demo game, because `updateStats` uses it to avoid adding a session-log entry for the player when that game is ended later.
- **Old entries:** the user's real `~/.PySolFC/statistics.dat` was inspected read-only and contained only the player `doug` (no `None`/demo player), so nothing needed clearing and no purge code was added. A file from elsewhere that has a `None` player would keep that harmless, unreachable entry.
- **Verified:** every statistics window (status, game stats, full log, session log, top results, progression) and the three save-to-file exports open and run with a real player in a throwaway `HOME`; a demo game with no player moves leaves the statistics unchanged; unit tests unchanged (19 ran, the one pre-existing `--version` failure); all 189 modules import; Klondike, FreeCell and Double Mahjongg deal.
- **Installed app:** built from commit `4b74a102` (menu entries and display code gone). It does **not** include `e5d6b00a` (recording removal) - rebuild and install to pick that up; there is no visible difference.

## 18. Update: music and sound settings removed (2026-11-08)

Asked by the user: no background music, one on/off sound setting, no per-sound toggles or volume (device volume is enough), and no sounds on dialogs or end of game.

- **`.mo` catalogs** (commit `5e9b353c`): the six tracked `locale/*/pysol.mo` were stale against the 2026 `.po` sources; committed the ones `make mo` regenerated. `po/<lang>.po` are git-ignored intermediates.
- **Music removed** (commit "Remove background music"): checkbox and slider in the Sound dialog, player thread and `playContinuousMusic`/`playNextMusic` in the audio clients, `initMusic`/`refreshMusicPlaylist`, `Music`/`MusicManager`, `~/.PySolFC/music`, Ctrl-U and Ctrl-End shortcuts, `music` and `sound_music_volume` options, README and help text. The "Music" cardset category in `resource.py` is unrelated and kept. Not touched: credits line "Carl Larsson for the background music" in `help.py`, man pages (`docs/pysol*.6`), old news/credits pages.
- **Single sound switch** (commit "Make sound a single on/off menu item"): the Sound dialog (`pysollib/tile/soundoptionsdialog.py`) is deleted. Options menu now has a checkable "Sound" item (`mOptSound` in `pysollib/ui/tktile/menubar.py`; turning it off also stops playing samples). Removed options: `sound_samples`, `sound_sample_volume`, `sound_mode`, plus the DirectX checkbox and `CAN_PLAY_MUSIC`/`CAN_SET_VOLUME`. Playback volume is the constant `SAMPLE_VOLUME = 75` (of 128) in `pysolaudio.py`. `sound_sample_buffer_size` is kept. Old option files still load; unknown keys are kept in the file and ignored.
- **Silenced sounds** (commits "Silence dialog and end-of-game sounds" and "Sound menu item: apply even when paused or dragging"): removed the `playSample` calls for `areyousure` (discard-game confirmation), `gamewon`, `gameperfect`, `gamefinished`, `gamelost` (also the "You are stuck" dialog), `autopilotwon`, `autopilotlost`; deleted those seven `.wav` files from `data/sound`. The unused `win*.wav` files remain. A bug found by testing: the first `mOptSound` ignored the toggle while paused or dragging (it called `_cancelDrag()`); fixed.
- **Remaining sounds:** gameplay only (deal, move, drop, flip, undo/redo, edge, etc.). The user's saved setting is `sound = False`; they must tick Options > Sound to hear them.
- **Verification:** all 188 modules import, 19 unit tests pass (the earlier `--version` failure did not appear in these runs), pyflakes clean on the touched files. Driven in the real app via a throwaway script: Sound toggle changes `opt.sound`, a sample plays when on and not when off, options save and reload. Not verified by ear.
- **Installed app:** rebuilt and installed after the last commit above (`make rules`, py2app, thin to arm64, copy out of iCloud, ad-hoc sign, `ditto` to `~/Applications`), 154 MB, arm64.
- **Test stub:** the pre-existing `pygame.error: mixer not initialized` traceback printed when the app is killed by `timeout` comes from `AbstractAudioClient.__del__`; it was present before these changes.

## 19. Update: animations, theme and graphics menus simplified (2026-11-08)

All asked by the user while cleaning up the Options menu. Each change was committed separately and the installed app was rebuilt after the last one.

- **Animation speeds** ("Simplify animation speeds to Fast, Medium and Slow"): the menu is Off / Fast / Medium / Slow. Internal values stay `opt.animations` 0, 1, 2, 3 (old very fast, fast, medium keep their timing); preview still uses 10. Slow and very slow (4, 5) are gone, so are `deal04.wav`/`deal08.wav`. A saved 4 or 5 loads as 3 (`min(..., 3)` in `Options.load`). Fresh-install default is now 2 (Medium); the old default 3 would now be labeled "Slow".
- **Redeal, flip and winning animations removed** (commit "Remove redeal, flip and winning animation options and code"): they had been defaulted off first. Deleted the three check items, options, `redealAnimation`, `animatedFlip`/`animatedFlipAndMove`/`doAnimatedFlipAndMove`, `winAnimation`/`winAnimationEvent`/`stopWinAnimation`, `GameWinAnimation`, and the DEBUG-only win animation test block. `AFlipAndMoveMove` in `move.py` now always uses `animatedMoveTo` for the move. "None" was renamed "Off". Tested by running Klondike, Pyramid, Golf and Monte Carlo at all four speeds with an old options file that had all three on. The win dialog without the animation was not exercised.
- **Native theme only** (commit "Always use the native ttk theme; remove the Window theme menu"): the theme is fixed per platform in `Options.setDefaults` (aqua on macOS, winnative/xpnative on Windows, clam on X11) and is no longer a saved option. The 30 themes came from Tk (5) plus the `ttkthemes` package (25) plus `data/themes` (blue, clearlooks); on macOS only `aqua` looks native. Removed the menu, `ttkthemes` from README, appveyor and the macOS workflow, `data/themes` and its MANIFEST/setup lines, and `init_tile`. `set_theme` uses plain `ttk.Style`. The bundle dropped from 153 MB to 140 MB. The user's saved `classic` is ignored. Windows and Linux paths were edited only, not run.
- **Other graphics menu removed** (commit "Remove the Other graphics menu; fix the icon styles"): fixed styles are dialog icons `material`, tree icons `material`, redeal icons `modern`, pause text `komika` (hard-coded in `app.py`; no options). Button icons were `none` and the demo logo was off (`demo_logo = False` in the user's file), so both features were removed (button images loading, `createDemoLogo`, `gimages.demo`). I had told the user the demo logo was "Komika"; it was actually off, and this was disclosed. Deleted the other image sets under `data/images/{buttons,demo,dialog,pause,redealicons,tree}`; `data/images` is now 5.6 MB. `resolve_image_style` and `_selectImageStyle` are gone. Toolbar icon style is unchanged and still has its own menu. The "Redeal icons" are the stock-pile symbols, not the removed redeal animation.
- **Installed app:** rebuilt from the last commit above, 140 MB, arm64, ad-hoc signed.
- **Verification:** 188 modules import; unit tests pass; the real app was driven with a copy of the user's options file (pause/resume, demo, dialog/tree/redeal/pause images loaded, Options menu ends at Toolbar/Statusbar). Nothing was checked by eye.
- **Lesson on installs:** check `pgrep -fl PySolFC` before replacing `~/Applications/PySolFC.app`. Once an install replaced a running copy. Also, the 8-second launch check leaves a respawned child behind (py2app's `__boot__` forks), so it must be stopped by hand afterwards; `timeout` only kills the parent.
- **Left alone:** the Toolbar menu, the "Window t&heme" and other removed labels still appear in the `po` files (harmless), and `docs/` man pages still describe removed features.

## 20. Update: status bar, card size and toolbar menus simplified (2026-11-08)

More Options-menu cleanup asked by the user. Each item was committed separately; the installed app was rebuilt after the last one (`e0250a90`).

- **Status bar** (commit "Make the status bar a simple on/off item; drop the game number"): the submenu is now one check item "Statusbar". All other fields (stuck, time, moves, stats, info, help) are always shown. The game number label and its `updateStatus(gamenumber=...)` plumbing are removed (the number is still stored with statistics and logs). `STATUSBAR_ITEMS`, `statusbar_vars` and the saved `visible_status` are gone; old files still load.
- **Card size menu removed** (commit "Remove the Card size menu; card scaling is fixed"): cards always scale to the window (`auto_scale`), previews scale, aspect ratio is kept, and resampling is the library default (Lanczos). Removed: the Card size submenu (increase/decrease/reset, auto scaling, preview scaling, preserve aspect, resampling), Ctrl +/-/0, the scale sliders and checkboxes in the Select Cardset dialog's Card Size tab (the X/Y offset sliders stay), and the saved scale options. `opt.auto_scale`, `preview_scale`, `preserve_aspect_ratio`, `scale_x/y`, `resampling` still exist as fixed, non-saved attributes, and the `if opt.auto_scale` branches in `game/__init__.py`, `stack.py`, `selectgame.py`, `selectcardset.py` and mahjongg are now always true but not stripped (candidate follow-up). Manual card size is gone; the window size decides it.
- **Toolbar icons** (commit "Toolbar icons: SF Symbols on macOS, bluecurve elsewhere"): the other eight styles and the Icon style menu are deleted, and `toolbar_style` is no longer an option. `App.getToolbarImagesDir` picks `sfsymbols` when `pysollib.settings.WIN_SYSTEM == 'aqua'` and `bluecurve` otherwise (`DEFAULT_TOOLBAR_STYLE` now lives in `app.py`). The SF Symbols PNGs in `data/images/toolbar/sfsymbols/{small,large,xlarge}` (24/32/48 px, black) and `light/` (white, used when `interface_is_dark`) are generated by `scripts/render_sf_symbols.swift`, built with `swiftc` and run on macOS: `swiftc -O scripts/render_sf_symbols.swift -o /tmp/r && /tmp/r data/images/toolbar/sfsymbols`. 13 buttons; "player" is a text label and needs no icon. **License note:** Apple's SF Symbols terms limit use to Apple platforms. These PNGs sit in the shared `data/` folder, so Windows/Linux packaging should exclude `data/images/toolbar/sfsymbols`; not done yet. The stale "Other Graphics" help section was also removed here. Not seen on screen: screenshots were not permitted, so the 24 px size in particular is unchecked.
- **Toolbar menu** (commits "Toolbar menu: Small/Medium/Large sizes and a simpler Button style" and "Toolbar menu: put the position choices in a Position submenu"): Icon size is Small / Medium / Large (internal values 0, 1, 2 and image folders are unchanged, so old "Large" is now Medium and old "Extra large" is now Large). "Compound" became "Button style" with Icons only / Text only / Icons and text (text below the icon; `COMPOUNDS` in `tkconst.py`); a saved `bottom` or `left` loads as `top` (check in `Options.load`). Top/Bottom/Left/Right and Hide are in a "Position" submenu (Hide is last, after a separator, because it shares the same setting).
- **User's saved toolbar settings** changed by themselves from text-below/large to icons-only/small between sessions (the app saves on quit); left as found.
- **Verification:** unit tests pass (19) and all 188 modules import after each change; the real app was driven with copies of the user's options file (menu labels, every size, style and position, old saved values, dialog open). Nothing was checked by eye.
- **Installed app:** rebuilt after the last commit above, 138 MB, arm64, ad-hoc signed. A running copy is now quit before install (the user gave standing permission); see the memory note. The launch-check copy must be stopped by hand afterwards.
- **Still open:** strip the dead `auto_scale` branches; keep `sfsymbols` out of Windows/Linux packages; `docs/` man pages and `po` files still mention removed features; the "Statusbar", "Button style" and "Position" labels have no translations.

## 21. Update: toolbar buttons, mouse, card view, card backs (2026-11-08)

More Options-menu cleanup. Each item is its own commit; the installed app was rebuilt after the last one (`f8dda69a`, 128 MB).

- **Visible toolbar buttons** (commit "Toolbar: choose visible buttons in a dialog"): the submenu closed after every click, so it is now a `Visible buttons...` item that opens `ToolbarButtonsDialog` (`pysollib/tile/toolbarbuttonsdialog.py`, exported through `pysoltk.py`, opened by `mOptToolbarButtons` in `actions.py`). Checkboxes for all buttons, applied together on OK. The per-item `tkopt.toolbar_vars` and `mOptToolbarConfig` are gone.
- **Toolbar Quit button removed** (commit "Remove the toolbar Quit button"): removed from `TOOLBAR_BUTTONS`, `tile/toolbar.py`, the bluecurve and sfsymbols icons, `scripts/render_sf_symbols.swift` and the toolbar `mQuit` wrapper in `actions.py`. Quit is still Cmd+Q and the app menu. A saved `visible_buttons` that lists `quit` is ignored.
- **Mouse menu** (commits "Remove the drag cards cursor option", "Mouse menu: one Point-and-click toggle; remove sticky mouse and mouse undo", "Rename the Point-and-click toggle to Click to move"): one check item "Click to move" (`tkopt.mouse_type` with onvalue `point-n-click`, offvalue `drag-n-drop`). Removed: the sticky-mouse mode (saved value loads as `drag-n-drop`, check in `Options.load`), "Use mouse for undo/redo" and its `Game.undoHandler`/`redoHandler`/`dropHandler`/`_defaultHandler`, the three canvas bindings, `event_handled`, and the drag cursor option (the hand cursor is always used). Reasoning recorded: click-to-move is an accessibility feature that the keyboard movement and VoiceOver announcements share; sticky mouse duplicates macOS drag lock; empty-table undo caused accidental undos.
- **Card view** (commits "Replace the Card view submenu with two items; fix the other settings" and "Remove the Card shadow option; the shadow is always shown"): the submenu is gone. `Shade legal moves` is a check item directly in the Options menu. Fixed and no longer saved: card shadow on, shrink face-down cards on, compact long stacks on, shade filled stacks on, negative empty-stack images on (the user's value; white borders), randomize placement off. They are plain attributes in `Options.__init__`.
- **Card back** (commit "Rename the Card background menu to Card back"): the menu is `Card &back`, so the internal menu path is `options.cardback` (used in `actions.py` and `updateBackgroundImagesMenu`). It lists the backs the cardset offers and is greyed out when there is only one. The cardset parser (`cardsetparser.py`) reads the default back from line 5 of `config.txt` and the full list from line 6; only the default is required, and a missing listed file just prints a warning.
- **Card backs trimmed** (commit "Trim card back choices: one per cardset, seven for Standard"): `scripts/prune_card_backs.py`, run by `setup_osx.py` before every build, keeps only each cardset's default back, except Standard keeps `back101`, `back102`, `back111`, `back121`, `back122`, `back191`, `back192` (it drops `back041`, `back131`, `back132`; the user asked to remove "1, 7, 8" of the ten, read as list positions). The cardsets are **not in git** (excluded in `.git/info/exclude`; they are a separate download copied into `data/`), so the rule lives in the script and is idempotent. 118 files were removed and the app went from 138 MB to 128 MB, mostly the three Neo cardsets that had 30 backs each. A backup of the full cardsets from before the trim is in the session scratchpad only (`cardsets-backup`); re-downloading the cardsets restores them.
- **Verification:** unit tests pass (19) and all 188 modules import after each change; the real app was driven with copies of the user's options file (menus, toggles, dialogs, demo play, and for card backs all 33 cardsets load with every listed back present). Nothing was checked by eye.
- **Housekeeping:** iCloud created duplicate build folders (`build 2`, `dist 2`, `data/html 6`) in the repo; they were untracked and have been deleted. The standing install rule is now: force quit a running app with `pkill -9 -x PySolFC` (see the memory note), because a graceful quit shows a confirmation dialog. This skips the app's save-on-quit.
- **Still open:** the dead `auto_scale` branches (section 20); keep `data/images/toolbar/sfsymbols` out of Windows/Linux packages; `docs/` man pages and `po` files still describe removed features; the new labels ("Click to move", "Visible buttons...", "Card back", "Shade legal moves") have no translations.

## 22. Update: one cardset per family, simpler cardset dialog (2026-11-08)

Installed app rebuilt after the last commit below (`28ab44e2`), 121 MB.

- **Which cardsets games need** (analysis, no code): every game was checked against every cardset with `checkCompatibleCardsetType`. Only the eight picture puzzle sizes (3x3 to 10x10) are the sole option for some games (Picture Matrix and Tile Puzzle at that size). Every other family has interchangeable cardsets: French 52/54-card (2000, Dondorf, Neo, Oxymoron, Standard, Tuxedo; eight joker games need a 54-card set, so not 2000 or Tuxedo), Mahjongg (3), Hanafuda (2), Tarock (2), Hex A Deck (2), Matrix (2), Mughal Ganjifa (2), Dashavatara Ganjifa (2), Matching (2), Ishido (2).
- **One cardset per family** (commit "Keep one cardset per game family; fix starting a Matching game first"): `scripts/prune_card_backs.py` now also deletes every `data/cardset-*` folder not in `KEEP_CARDSETS`. Kept (18): `standard` (French, kept at the user's request), `uni-mahjongg`, `louie-mantia-hanafuda`, `neo-tarock`, `neo-hex`, `mughal-ganjifa-xl`, `dashavatara-ganjifa-xl`, `next-matrix`, `matching-xl`, `simple-ishido-xl`, and the eight puzzle sets. Each choice matches what the user already had selected in `options.cfg`, except Matching (unset; XL chosen like the other XL picks). `setup_osx.py` runs the script before every build. The cardsets are not in git (see section 21), so a full re-download is trimmed again at build time. `data/` went from 38 MB to 30 MB; the app from 128 MB to 121 MB. The full original cardsets are only in the session scratchpad (`cardsets-backup`, from before the card back trim).
- **Defaults follow the kept sets** (`Options.__init__` PIL branch): French uses Standard (was Neo), Matching uses Matching XL (was Neo, a French set). The non-PIL branch still names removed cardsets; it is dead code on this build.
- **Matching crash fixed** (same commit): `checkCompatibleCardsetType` dereferenced `cs.ncards` when no cardset was loaded, so starting directly in a Matching game (for example launching into Memory 16 as the last-played game) raised `AttributeError`. Reproduced with the original cardsets, so it predates this work. The check is now `if cs is None or cs.ncards < ...`.
- **Select Cardset dialog** (commits "Select cardset dialog: one alphabetical list" and "Select cardset dialog: remove the Search tab"): the grouped tree (All Cardsets, by Size, Type, Style, Date, Nationality) is replaced by a flat list of root leaves sorted with `getNaturalSortKey` in `SelectCardsetData`. The unused by-type dialog variant is deleted. The Search tab is gone with its search box, `SearchCriteria`, `SelectCardsetAdvancedSearch`, `initial_tab` plumbing (`App.selectCardset`, `mSelectCardsetDialog`) and the Shift-Ctrl-E shortcut. Tabs are now "Cardsets" and "Card Size" (X/Y offset sliders). The Select Game dialog keeps its own search tab. A first cut deleted `CardsetInfoDialog` by mistake; pyflakes caught it and it was restored from git before the commit.
- **Verification:** unit tests pass (19) and all 188 modules import; a game from every family dealt with the right cardset using both the user's options file and a fresh one; the cardset dialog was opened in the real app (two tabs, ordered list, selection works, Info dialog opens). Nothing was checked by eye.
- **Still open:** the dead `auto_scale` branches (section 20); keep `data/images/toolbar/sfsymbols` out of Windows/Linux packages; `docs/` man pages, `po` files and the `graft data/cardset-*` lines in `MANIFEST.in` still describe removed cardsets and features; new labels have no translations.

## 23. Update: Card Size tab removed from the cardset dialog (2026-11-08)

Commit "Select cardset dialog: remove the Card Size tab" (`a35ec06d`); the installed app was rebuilt after it (121 MB).

- **What the tab did:** the "Card Size" tab held two sliders, X offset and Y offset (5 to 100 px). They set how far each card in an overlapping pile is shifted from the one beneath (Y for columns, X for horizontally fanned piles), starting from the cardset's own values in `config.txt` (Standard: 14 and 18). They were applied only on Select, saved per cardset in the `[offsets]` section of `options.cfg`, and not shown in the preview. The name was misleading once the scale sliders were removed (section 20).
- **Removed:** the tab, the `PysolNotebook` (the cardset list now sits directly in `left_frame` with `grid`), `x_offset`/`y_offset`, `cardset_values`, the offset handling in `App.selectCardset`, the `[offsets]` load and save and `Options.offsets`, and the code in `App._readCardsetConfig` that applied saved offsets. Every cardset now always uses its built-in spacing. The dialog is the alphabetical list plus the preview. `PysolScale`, `PysolNotebook`, `tkinter` and `USE_PIL` imports in `selectcardset.py`/`app.py` went with it. An old `options.cfg` that still has an `[offsets]` section loads fine (tested with an entry).
- **Help page:** the sentence about the Card Size tab was removed from the Card Size section of `settings.html`.
- **Verification:** unit tests pass (19) and all 188 modules import; the dialog was opened in the real app (no tab bar, ordered list, Standard selects, Info dialog opens) with a plain options file and one that has an `[offsets]` entry. Nothing was checked by eye.
- **iCloud duplicates:** build output keeps getting duplicate folders from iCloud sync of the repo (`build 2`, `dist 2`, `data/html 6` and `data/html 8` as untracked copies, and empty `data/html 2` to `7`). The user said to delete these whenever they appear; use `rm -rf` on the exact numbered folder after checking `git status` and `git ls-files` show it is untracked, and `rmdir` for the empty ones.
- **Still open:** as in section 22.

## 24. Update: Cards submenu and checklist dialogs (2026-11-08)

Installed app rebuilt after the last commit below (`5120172a`), 121 MB.

- **Cards submenu** (commits "Options menu: group Cardset and Card back in a Cards submenu", "Rename the Cardset... menu item to Deck...", "Move Shade legal moves into Assist level; rename Decks and Backs"): Options > Cards holds `Decks...` (Cmd+E, opens the "Select deck" dialog) and `Backs` (the card back grid; greyed out when the cardset has one back). Table color stays directly in Options. The internal menu paths changed: the backs submenu is `options.cards.backs` (used by `actions.py` `setMenuState` and `updateBackgroundImagesMenu`). The word "cardset" still appears in less visible places (error messages, the Info dialog).
- **Shade legal moves** moved into the Assist level options (it is a gameplay aid, not a card look). The same setting `opt.shade`. Card shadow was already fixed on (section 21).
- **Checklist dialogs** (commits "Assist level: choose the options in a dialog" and "Automatic play: choose the options in a dialog"): menus close after each click on macOS, so both submenus are now commands, `Assist level...` and `Automatic play...`, that open a `ChecklistDialog` (`pysollib/tile/checklistdialog.py`) with check boxes applied together on OK, like the toolbar `Visible buttons...` dialog (section 21; that one still has its own two-column `ToolbarButtonsDialog`). The option tables live in `pysollib/ui/tktile/tkconst.py` as `ASSIST_OPTIONS`, `ASSIST_GAME_OPTIONS` and `AUTOMATIC_PLAY_OPTIONS`: (option and `tkopt` name, label, menubar handler). `mOptAssistLevel`, `mOptAutomaticPlay` and `_applyChecklist` in `actions.py` set the `tkopt` variable and call the existing `mOpt...` handler for each changed option only, so their side effects (`updateMenus`, `autoPlay`) are unchanged. The Mahjongg "show removed tiles" option restarts the game, so it is last in the list. Options that do not apply to the current game are greyed out in the Automatic play dialog: `updateMenus` now stores `self._autoplay_usable` instead of calling `setMenuState` on the old submenu entries. The old per-item menu entries and the `assistleveldialog.py` first draft are gone.
- **`.gitignore`:** `.DS_Store` added.
- **Verification:** unit tests pass (19) and all 188 modules import; both dialogs were driven in the real app (17 Assist check boxes, 4 Automatic play check boxes, only changed options applied, `tkopt` stays in sync, Automatic play greyed out in a Mahjongg game). The Mahjongg restart path and everything on screen were not checked.
- **Still open:** as in section 22. Toolbar > Position and the other submenus were left as menus because they are one-choice radio groups, not multi-select lists.

## 25. Update: Phosphor toolbar icons, SF Symbols removed, history cleaned (2026-11-08)

Installed app rebuilt after the Phosphor commit (120 MB). Supersedes the toolbar icon parts of sections 20 and 21.

- **Why:** the repo is public and Apple's SF Symbols licence only allows the symbols inside apps for Apple platforms, so the pre-rendered SF Symbols PNGs could not be published. The licences of the candidates were read from their repositories: Phosphor (MIT), Lucide (ISC plus MIT for the few icons derived from Feather), Tabler (MIT), Fluent UI (MIT) and Google Material (Apache 2.0) are all compatible with this GPL v3 project; the only condition is keeping the copyright and licence text with the icons.
- **Result (commit "Toolbar icons: Phosphor only; remove SF Symbols and bluecurve"):** `data/images/toolbar/phosphor` is the only toolbar set on every platform: `small`/`large`/`xlarge` (24/32/48 px, black, for light interfaces) and `light/<size>` (white, for dark interfaces; chosen by `interface_is_dark`), 12 icons each (new, restart, open, save, undo, redo, autodrop, shuffle, hint, pause, statistics, rules; "player" is a text label, and "quit" was removed in section 21). The Phosphor "regular" icons used: file-plus, arrow-counter-clockwise, folder-open, floppy-disk, arrow-u-up-left, arrow-u-up-right, arrow-line-down, shuffle, lightbulb, pause, chart-bar, book-open. `DEFAULT_TOOLBAR_STYLE` is now `'phosphor'` in `app.py` and `getToolbarImagesDir` no longer looks at the platform. The bluecurve and sfsymbols folders, and `scripts/render_sf_symbols.swift`, are gone.
- **Regenerating:** the SVG sources and the MIT `LICENSE` are in `scripts/phosphor-icons/` (the licence is also copied next to the PNGs with a short `README`). `scripts/render_toolbar_icons.swift` renders them with AppKit (macOS only): `swiftc -O scripts/render_toolbar_icons.swift -o /tmp/r && /tmp/r scripts/phosphor-icons data/images/toolbar/phosphor`. The SVGs came from `phosphor-icons/core` (`assets/regular/`). The 24 px size is the one to check by eye.
- **Git history rewritten before the first push of this work:** the SF Symbols images and their render script were removed from all 42 unpushed commits with `git filter-branch --index-filter 'git rm -r -q --cached --ignore-unmatch data/images/toolbar/sfsymbols scripts/render_sf_symbols.swift' origin/master..HEAD`. The final tree was identical before and after the rewrite, nothing on GitHub was touched, and no commit in `master` contains an SF Symbols file now. The local branch `backup-before-phosphor` and Git's `refs/original/refs/heads/master` still hold the old commits (with the SF images). They are local only; do not push them, and delete them once the push is confirmed (`git branch -D backup-before-phosphor` and `git update-ref -d refs/original/refs/heads/master`). Commit hashes in this file's older sections refer to the pre-rewrite history.
- **Verification:** unit tests pass (19) and all 188 modules import; the real app was driven through all three icon sizes and all three button styles with every toolbar button showing an image, and the icons were viewed on light and dark backgrounds. Nothing was checked in the real window.
- **Still open:** the dead `auto_scale` branches (section 20); `docs/` man pages, `po` files and the `graft data/cardset-*` lines in `MANIFEST.in` mention removed features and cardsets; new labels have no translations; the SF Symbols mention in section 21 about keeping the images out of Windows/Linux packages no longer applies.

## 26. Update: Layout submenu (2026-11-08)

Commit "Options menu: Layout submenu with Table color and Spread stacks" (`862751a3` in the rewritten history); the installed app was rebuilt after it (120 MB).

- **Asked by the user:** make a Layout dropdown with Table color and Spread stacks; remove everything else in the old Game layout submenu, with Center layout and Save games geometry on.
- **What the old items did:** Fullscreen (F11) toggled `-fullscreen`; Spread stacks keeps the card images at one uniform scale but spaces the piles with separate horizontal and vertical factors, so a wide window gets wider gaps (`Game.resizeImages`); Center layout centers the scaled layout when Spread stacks is off; Save games geometry remembers the window size and position per game (`[games_geometry]`); Keep dialogs on top keeps Find card, Help, Solver and the card picture above the main window.
- **Now:** Options > Layout holds `Table color...` (moved from the top level of Options) and `Spread stacks`. Removed: the Fullscreen item, the F11 binding, `togglefullscreen` and `App.wm_toggle_fullscreen` (macOS still has its own full-screen button). `center_layout`, `save_games_geometry`, `topmost_dialogs` and `wm_fullscreen` are fixed attributes in `Options.__init__` (True, True, True and 0), no longer saved or loaded, and their menu variables and handlers are gone; the code that reads them (`app.py`, `game/__init__.py`, the dialogs) is unchanged. `save_games_geometry` used to default to off, so fresh installs now also remember each game's window size. An old `options.cfg` with any of those keys loads fine (tested with all three turned off and fullscreen on).
- **Help page:** the "Game Layout" section became a short "Layout" section and the Table color instructions use the new path.
- **Verification:** unit tests pass (19) and all 188 modules import; the real app showed the new Options menu and Layout submenu, toggled Spread stacks and resized the window without errors. Nothing was checked by eye.
- **Push state:** commits up to the handoff in section 25 were pushed to `origin/master` (`bf3c29c0`). The Layout commit and this entry are local until the next push.
- **Still open:** as in section 25.

## 27. Update: Background color, no ellipses, Fonts and Colors removed (2026-11-08)

Installed app rebuilt after the last commit below (120 MB).

- **Background color** (commit "Rename Table color to Background color"): the Options > Layout item and the picker title say "Background color"; the saved key is still `colors['table']`.
- **Ellipses removed** (commits "Remove the ellipsis from menu item names" and "Remove the ellipsis from dialog button names"): the "..." is gone from 25 menu labels in `ui/tktile/menubar.py` and from the dialog buttons Change (fonts and colors dialogs, now deleted), Info (deck dialog), Reset and Statistics (statistics windows) and the top-results button. Menu paths are unaffected because `MfxMenu.labeltoname` strips non-alphanumerics. Kept on purpose: ellipses inside sentences (for example "Loading cardset %s...", "There are no moves left...") and the "..." advanced-search button in the Select Game dialog, whose whole label it is.
- **Fonts and Colors dialogs removed** (commit "Remove the Fonts and Colors dialogs"): `FontsDialog`, `FontChooserDialog`, `ColorsDialog` and their menu items, `mOptFonts` and `mOptColors` are gone. Fonts are no longer options: `Options.__init__` holds fallbacks and `Options.setDefaults(top)` replaces them with Tk's `TkDefaultFont` and `TkFixedFont` families (San Francisco `.AppleSystemUIFont` and Menlo on this Mac; Segoe UI and Consolas or the fontconfig default elsewhere, not run): help text 14, fixed text 13, table text (`canvas_default`) 13, `canvas_fixed` 12, `canvas_large` 18, `canvas_small` 11 (they were Times 12, Courier 12, Helvetica 12, Courier 12, Helvetica 16, Helvetica 10). The unused `small` font is deleted. The old `[fonts]` section of an options file is ignored. Colors: only `colors['table']` is saved or loaded; the highlight, hint arrow, not-matching and keyboard selector colors are fixed at their old defaults. The text colour on the table is now computed in `MfxScrolledCanvas.setTile` (`tile/tkwidget.py`): black when the background's luminance is above 0.6, otherwise white, stored in `colors['text']` at run time. Verified with `#f0f0f0` (black), `#202020` and `#006d04` (white).
- **A mistake worth knowing about:** the first edit to `options.py` sliced out too much and removed the colors, timeouts and many other defaults; the next test run failed at once and the file was restored from git and redone. When editing `Options.__init__`, slice between exact markers.
- **Verification:** unit tests pass (19) and all 188 modules import; the real app showed the new Options menu (no Fonts or Colors), started with the user's old options file, opened the help viewer with the new font, and dealt Klondike, Canfield, Calculation, Yukon, Memory 16, Cribbage Square, Poker Square, Scoundrel, Matriarchy and 10 x 8 with the new fonts. Nothing was checked by eye.
- **Environment note:** the sandbox's safety check refuses `rm`/`rmdir` on targets built from shell variables (for example the duplicate-folder cleanup loop). Use literal paths or `"${var:?}/..."`.
- **Push state:** `origin/master` is at the Phosphor handoff (section 25). Everything after it is local: the Layout menu and its handoff (section 26), the two renames, both ellipsis commits, the Fonts and Colors removal and this entry.
- **Still open:** as in section 25.

## 28. Update: Timeouts removed; launch checks touched real settings (2026-11-08)

Installed app rebuilt after commit "Remove the Timeouts dialog; the delays are fixed at 1 second" (120 MB, arm64).

- **Timeouts removed:** `TimeoutsDialog` (`tile/timeoutsdialog.py`), the Options > Timeouts item and `mOptTimeouts` are gone, and the `[timeouts]` option section is no longer saved or loaded (old files still load). `Options.timeouts` stays as a fixed dict of six 1.0 s delays: `demo` (pause between demo moves), `hint` and `highlight_piles` (the Hint command and Assist > Highlight piles, in `actions.py`), `highlight_cards`, `highlight_samerank` (also the Find card blink) and `raise_card` (how long a middle-click peek holds a card up). Hint also drives the Shisen-Sho arrow and Match Three highlight. The user's values were all 1.0, so behaviour is unchanged. The help page section "Timeouts" became "Fonts and Colors".
- **Correction to what was said while deciding:** the assistant first said Highlight piles was unused and Hint only mattered in two games. Both were wrong because the search skipped `actions.py`; always search the whole `pysollib` tree.
- **Launch checks were not isolated:** the installed app ignores `HOME=<temp>` because py2app's `emulate_shell_environment` re-sources the login shell, so every "throwaway home" launch check of the installed app (about 20 this session, each ended with `timeout`/SIGTERM) actually loaded the real `~/.PySolFC`, and ending them may have re-saved `options.cfg` and `statistics.dat`. Evidence: the temp home stayed empty and the real files' modification times matched the launch times. Unknown which values changed; `statusbar = False` and the toolbar `icons only / small` values differ from earlier in the session and may be the user's own changes. The statistics file shows no games recorded for the user (`doug`), so no results were polluted. Source runs with `HOME=<temp>` (the `.venv` harness scripts) did honour the temp home. The only checks of the installed app after this are `codesign -v` and `PySolFC.app/Contents/MacOS/PySolFC --version` (prints the version and exits; verified not to touch `options.cfg`). This is also in the memory note about macOS builds.
- **Verification:** unit tests pass (19) and all 188 modules import; a source run with an options file that had `hint = 5.0`, `demo = 7.0` and `highlight_piles = 6.0` ignored them (all 1.0), the Hint and Highlight piles commands each took 1 second and a demo ran. The Options menu now has Player options, Automatic play, Assist level, Sound, Layout, Cards, Animations, Click to move, Toolbar and Statusbar. Nothing was checked by eye.
- **Push state:** `origin/master` is still at the Phosphor handoff (section 25); sections 26 to 28 and the commits since are local.
- **Still open:** as in section 25.

## 29. Update: statistics and player options removed; Toolbar and Statusbar under Layout (2026-11-08)

Installed app rebuilt after commit "Move Toolbar and Statusbar into the Layout submenu" (120 MB, arm64, ad-hoc signed).

- **Asked by the user:** keep the confirmation (renamed "Confirm before quitting"), remove statistics entirely, and remove the player stuff with it. The user's saved `update_player_stats = False` meant statistics were already off, so the removal changes no behaviour for them.
- **Deleted modules:** `pysollib/stats.py`, `app_stat.py`, `app_stat_result.py`, `app_statistics.py`, `tile/tkstats.py` (all statistics windows) and `tile/playeroptionsdialog.py`. `~/.PySolFC/statistics.dat` is no longer read, written or listed in `App.fn`.
- **UI removed:** the Game menu items Status, Statistics and Log; Options > Player options (and Ctrl-P); the Ctrl-Y and Ctrl-T shortcuts; the toolbar `statistics` button and the `player` label (and its `updateText`/`config` branches, and the `statistics.png` icons, the `chart-bar` SVG and its line in `scripts/render_toolbar_icons.swift`; the script now needs eleven SVGs); the status bar `stats` field; File > Select random game's played/won/not won/not played choices (it is now one item); the Select Game dialog's Statistics panel, its "Play history" filter and the won/lost/time/moves rows in the game info.
- **Logic removed:** `Application.stats`, `loadStatistics`/`saveStatistics`/`__saveObject`, the `getGamesIdSortedBy{Played,Won,Lost,Percent,PlayingTime,Moves}` helpers, `getAllUserNames`, and in `game/__init__.py` the `app.stats.updateStats`/`getStats` calls and the "reached the top N" message. `Game.updateStats` now only records `gstats.updated` and `stats.demo_updated`. The `player` and `stats` keys are gone from `updateStatus`. `wizardutil.delete_game` no longer clears statistics. `update_player_stats` is no longer an option.
- **Kept on purpose:** the per-game counters `Game.stats` (`GameStatsStruct`: moves, hints, undo and demo counts, elapsed time), which the "game won/finished" logic and the moves display use, and `gstats`. `Options.player` still exists and is set at startup from the account name (`app.py`); it is not saved or shown and is only used inside saved games. The casino balance (Klondike/Canfield "Balance $") used `app.stats.gameid_balance`; it is now `app.gameid_balance`, reset when a game is loaded or started.
- **New:** Options > `Confirm before quitting` (check item at the top of Options, handler `mOptConfirm`, still the saved `opt.confirm`). The "/" key opens the Game Info dialog through the new `mGameInfo` in `actions.py` (it used to be a mode of the statistics window).
- **Toolbar and Statusbar** (commit "Move Toolbar and Statusbar into the Layout submenu"): Options > Layout now holds Background color, Spread stacks, a divider, Toolbar (Icon size, Button style, Visible buttons, Position) and Statusbar. The toolbar's right-click popup is unchanged. Options is now: Confirm before quitting, Automatic play, Assist level, Sound, Layout, Cards, Animations, Click to move.
- **Process notes:** a bulk cut-and-paste helper (`cutmethod`) mangled `actions.py` once (its `^` matched at the start of the sliced text), so the file was restored from git and redone; a leftover `Ctrl-P` binding to the removed `mOptPlayerOptions` crashed the menu build and was caught by the first real-app run. The installed app was checked with `--version` and `codesign -v` only; the user's `options.cfg` kept the same modification time across that check (it changed between other steps, most likely from the user using the app).
- **Verification:** unit tests pass (19) and all 179 modules import; real-app source runs started Klondike, Double Mahjongg Big Castle, Memory 16 and Thieves with an old options file, showed the new menus (toolbar 11 buttons; status fields help, info, moves, stuck, time), and ran a demo, a hint and end-of-game without errors; 1,389 games are offered to Select random game. Statusbar and toolbar position were toggled under Layout. Nothing was checked by eye.
- **Help pages:** the Player Options section became "Confirm Before Quitting"; statistics mentions were removed from the assist options, intro and install pages; the toolbar/status bar section says they are under Options > Layout.
- **Push state:** `origin/master` is still at the Phosphor handoff (section 25). Sections 26 to 29 and every commit since are local.
- **Still open:** as in section 25. The "Some notes about scoring" list in `howtoplay.html` still describes win/loss rules in terms of the removed statistics ("Loaded games don't count") and could be rewritten.

## 30. Update: Layout submenu order (2026-11-08)

Installed app rebuilt after commit "Layout submenu order: Toolbar, Statusbar, Background color, Spread stacks" (120 MB, arm64, ad-hoc signed).

- **Change:** Options > Layout is now Toolbar (Icon size, Button style, Visible buttons, Position), Statusbar, a divider, Background color, Spread stacks. It was Background color, Spread stacks, a divider, Toolbar, Statusbar (section 29). The code is the `layout = MfxMenu(menu, label=n_("&Layout"))` block in `ui/tktile/menubar.py`; the menu path for Backs is unaffected (`options.cards.backs`).
- **Verification:** unit tests pass (19); a real-app source run printed the new order, toggled Statusbar, moved the toolbar between positions and confirmed the toolbar right-click popup still exists. The installed app was checked with `--version` and `codesign -v` only. Nothing was checked by eye.
- **Push state:** `origin/master` is still at the Phosphor handoff (section 25). Sections 26 to 30 and every commit since are local (the last count was 13 commits before this entry).
- **Still open:** as in sections 25 and 29.

## 31. Update: Options menu reordered; Automatic play and Assist level merged into Play options (2026-11-08)

Installed app rebuilt after commit "Merge Automatic play and Assist level into Play options" (120 MB, arm64, ad-hoc signed).

- **Menu changes** (commits "Options menu: Click to move cards, and Confirm before quitting at the bottom" and the merge): the Options menu is now Play options, a divider, Sound, Layout, Cards, Animations, Click to move cards, Confirm before quitting. "Click to move" became "Click to move cards"; "Confirm before quitting" moved to the bottom and its keyboard hint is `Con&firm`.
- **Play options** (`mOptPlayOptions` in `actions.py`, using `_applyChecklist` and `ChecklistDialog`): one window with three groups separated by dividers. `AUTOMATIC_PLAY_OPTIONS` (auto face-up, auto drop, auto deal, quick play; greyed out per game through `_autoplay_usable`), `ASSIST_OPTIONS` (now only shade legal moves and stuck notification) and `ASSIST_GAME_OPTIONS` (Shisen-Sho hint arrow, Match Three cascade, Accordion deal all, Pegged auto-remove, Mahjongg removed tiles, applied last because it restarts the game). The tables are in `ui/tktile/tkconst.py`. `mOptAssistLevel` and `mOptAutomaticPlay` are gone.
- **Removed and fixed (not saved or loaded):** the assist switches `undo`, `bookmarks`, `hint` and `shuffle`, `highlight_piles`, `highlight_cards`, `highlight_samerank` and `highlight_not_matching` are always on; `peek_facedown` is always off; `free_hint` is removed and fixed off (the user's value), so a hint still makes a win show "Game finished, but not without my help" (`getWinStatus`). They are plain attributes in `Options.__init__`; their `tkopt` variables and `mOptEnable*`/`mOptFreeHints` handlers are deleted. Reasoning: those switches existed to impose "no help" play for statistics, which are gone; the highlights fire only on Ctrl-click, Shift-click or an explicit Assist menu command. To make hints free, set `free_hint = True` there.
- **Help pages:** the Automatic Play and Assist Level sections became one "Play Options" section; the shade legal moves text became a one-line "Shadows" note; `assist_options.html` and `howtoplay.html` no longer mention free hints or the peek option.
- **Build finding:** iCloud sometimes drops a duplicate `data/html 2` (a copy of the generated rules pages) into the source folder while `make rules` runs, and py2app then bundles it (about 1.1 MB, visible as `Contents/Resources/data/html 2`). The first build of this session had it. Remove any `data/html [0-9]*` folder after `make rules` and before `py2app`, and check `ls <app>/Contents/Resources/data | grep " [0-9]"` after building.
- **Verification:** unit tests pass (19) and all 179 modules import; real-app source runs showed the new Options menu, the 11-item dialog (all four automatic items usable in Klondike and greyed out in Double Mahjongg Big Castle), applied three changes, and ran Hint and Highlight piles; an old options file with undo and hint off, peek on and free hints on was ignored. The installed app was checked with `--version` and `codesign -v`; the user's `options.cfg` kept its modification time. Nothing was checked by eye.
- **Push state:** `origin/master` is still at the Phosphor handoff (section 25). Sections 26 to 31 and every commit since are local (about 17 commits).
- **Still open:** as in sections 25 and 29.

## 32. Update: Click to move and Confirm moved into Play options; Stuck notification removed (2026-11-08)

Installed app rebuilt after commit "Remove the Stuck notification option; the dialog says No moves left!" (120 MB, arm64, ad-hoc signed).

- **Moved into Play options** (commit "Move Click to move cards and Confirm before quitting into Play options"): the Options menu is now Play options, a divider, Sound, Layout, Cards, Animations. The Play options window has four groups: `AUTOMATIC_PLAY_OPTIONS`, `ASSIST_OPTIONS`, the new `PLAY_OPTIONS` (click to move cards, confirm before quitting) and `ASSIST_GAME_OPTIONS`. "Click to move cards" is now a boolean `tkopt.click_to_move` with the handler `mOptClickToMove`, which writes `opt.mouse_type` as `point-n-click` or `drag-n-drop` (the saved option is still `mouse_type`); `mOptMouseType` and the old string variable are gone. "Confirm before quitting" is unchanged (`opt.confirm`, `mOptConfirm`). The help page folds the Mouse and Confirm sections into Play Options.
- **Stuck notification removed** (commit "Remove the Stuck notification option; the dialog says No moves left!"): `opt.stuck_notification` and its menu variable and handler are gone. `Game.updateStuck` now always shows the dialog when `getStuck()` is false, once per stuck position (it sets `self.stuck`), never during a demo and never when the game is won. Title "No moves", text "No moves left!", buttons New game, Restart and Cancel. Cancel leaves the game playable and undo available; undo clears the flag and the `failed_snapshots` list. The status bar `stuck` field still shows an `x` while stuck. The user's old setting was off, so this is new behaviour for them.
- **Verification:** unit tests pass (19) and all 179 modules import; a real-app source run showed the new menu, flipped click to move and confirm in the 13-item dialog (only those changed), forced a stuck position with `getStuck` patched and a fake dialog (title and text checked; Cancel kept undo available; the dialog did not repeat), and showed the 12-item dialog after the removal. The installed app was checked with `--version` and `codesign -v`; the user's `options.cfg` kept its modification time. The `data/html N` duplicate cleanup before py2app found nothing this time. Nothing was checked by eye.
- **Push state:** `origin/master` is still at the Phosphor handoff (section 25). Sections 26 to 32 and every commit since are local (about 20 commits).
- **Still open:** as in sections 25 and 29.

## 33. Update: Cards under Layout, Sound last, and the File menu reordered (2026-11-08)

Installed app rebuilt after commit "Reorder the File menu and move game-picking items to Select and Game" (120 MB, arm64, ad-hoc signed).

- **Layout and Options** (commits "Move the Cards submenu into Layout, under Statusbar, without the divider" and "Options menu: Sound at the bottom"): Options is now Play options, a divider, Layout, Animations, Sound. Layout is Toolbar, Statusbar, Cards (Decks, Backs), Background color, Spread stacks, with no divider. The Backs menu path is `options.layout.cards.backs` (used in `actions.py` `setMenuState` and `updateBackgroundImagesMenu`).
- **File menu** (commit above): File is New game, Open, a divider, Save, Save as, a divider, Hold and quit (plus Quit when `WIN_SYSTEM != 'aqua'`; on macOS Quit is in the app menu). This follows the macOS layout of New, Open, Save, Save As, with Quit in the app menu. Moved to **Select**: Select random game, Recent games, Favorite games, Add to favorites, Remove from favorites (they are created in `_addSelectGameMenu`, so their menu paths are `.menubar.select.recentgames`, `.favoritegames`, `.addtofavorites`, `.removefromfavorites`, used by `updateRecentGamesMenu` and `updateFavoriteGamesMenu`). Moved to **Game**: Select game by number (Cmd-M). **Removed:** Next game by number (the number dialog keeps its "Next number" button, so `mNewGameWithNextId` stays; its Cmd-N binding is gone), Export current layout and Import starting layout (`mExportCurrentLayout`, `mImportStartingLayout`). The solver export and import code in `hint.py` (`PySolHintLayoutImportError` and the layout parsers) is now unreachable and is a cleanup candidate.
- **Verification:** unit tests pass (19) and all 179 modules import; real-app source runs printed every menu in the new order, added and removed a favorite, showed 7 recent games and 1,389 random-game candidates, and toggled Sound, Statusbar and the toolbar position; the Backs menu was enabled in Klondike and greyed out in Double Mahjongg. The installed app was checked with `--version` and `codesign -v`; the user's `options.cfg` kept its modification time. The pre-bundle duplicate cleanup (`data/html N`) found nothing this time. Nothing was checked by eye.
- **Process note:** the cut-out helper stops a method at the next line that starts in column 0, so it cut `mImportStartingLayout` short because that method contains a multi-line string with unindented text. The file was restored from git and redone with a helper that stops only at the next `    def`. Use that rule for methods with multi-line strings.
- **Push state:** `origin/master` is still at the Phosphor handoff (section 25). Sections 26 to 33 and every commit since are local (about 25 commits).
- **Still open:** as in sections 25 and 29, plus the unreachable solver import/export code in `hint.py`.

## 34. Update: Hold and quit replaced by Quit (2026-11-08)

Installed app rebuilt after commit "Replace Hold and quit with a plain Quit" (120 MB, arm64, ad-hoc signed).

- **Asked by the user:** "it should just be quit; the user can save it on their own." File is now New game, Open, a divider, Save, Save as, a divider, Quit (Cmd-Q) on every platform. Before, the item was hidden on macOS, where the app menu has its own Quit.
- **What "Hold and quit" did:** it wrote the full game state to `~/.PySolFC/holdgame.dat` and set `opt.game_holded`; the next launch loaded it (`_load_held_or_saved_game`) and then cleared the hold.
- **Removed:** `mHoldAndQuit`, the `hold_and_quit` menu state, the Cmd-X binding, `fn.holdgame`, `nextgame.holdgame`, the save-on-quit block in `Application._main_loop`, `_load_held_or_saved_game` and the startup check on `game_holded`, the `holdgame` parameter of `Game.endGame` and `Game.quitGame`, `GameGlobalStatsStruct.holded`, and the `game_holded` option (also dropped from the check in `main.py`). Old option files with `game_holded` load fine, and old saved games that carry a `holded` field in their pickled global stats load too, because the struct is restored from its `__dict__`.
- **Verification (limited, on purpose):** pyflakes, the unit tests (19) and the import of all 179 modules pass, and a source run with an old options file that had `game_holded` set to a game id started and built the new File menu. A Save and Open round trip in the test harness hung, most likely a problem in the harness itself (nothing in the save or open code changed apart from deleting one unused line); it was not chased and is unconfirmed. The installed app was checked with `--version` and `codesign -v` only.
- **Process note:** the user questioned how much testing went into a one-item menu change. Keep the checks proportionate to the change and do not build large harnesses for simple menu edits.
- **Push state:** `origin/master` is still at the Phosphor handoff (section 25). Sections 26 to 34 and every commit since are local (about 26 commits).
- **Still open:** as in sections 25, 29 and 33.

## 35. Update: Assist merged into Game; Comments, Demo (all games) and Solver removed (2026-11-08)

Installed app rebuilt after commit "Merge the Assist menu into Game; remove Comments, Demo (all games) and Solver" (120 MB, arm64, ad-hoc signed).

- **Menu bar:** File, Select, Edit, Game, Options, Help (there is no Assist menu now). Game is Deal cards, Auto drop, Shuffle tiles, Pause, a divider, Hint, Highlight piles, Find card, Show full picture, Piles description, a divider, Demo, Select game by number. Shortcuts are unchanged (D, A, F, P, H, I, F2, F3, Cmd-D, Cmd-M). The menu paths that `actions.py` passes to `setMenuState` changed from `assist.*` to `game.hint`, `game.highlightpiles`, `game.findcard`, `game.showfullpicture` and `game.demo`.
- **What each removed item was:** Comments (`mEditGameComment`) attached a note to a deal and appended it to `~/.PySolFC/comments.txt`; Demo (all games) (`mMixedDemo`) played random games one after another; Solver (`mSolver`) opened the solver window, but the menu item was always greyed out in this build because `fc-solve` is not installed or bundled (`USE_FREECELL_SOLVER` is False). The saved-game field `gsaveinfo.comment`, the solver dialog code (`tile/solverdialog.py`, `ui/tktile/solverdialog.py`, `create_solver_dialog` and friends in the game and app code) and the hint-layout import/export code remain but are unreachable; they are cleanup candidates.
- **Reasoning recorded:** macOS has no standard Game or Assist menu, so merging two small menus into one is a judgement call; the user approved it.
- **Help:** the Demo paragraph in `assist_options.html` no longer mentions Demo (all games).
- **Verification (proportionate):** pyflakes and the unit tests (19) pass; a real-app source run printed the full menu bar and the Game menu in the order above. The installed app was checked with `--version` and `codesign -v`; the pre-bundle `data/html N` cleanup found nothing. Nothing was checked by eye.
- **Push state:** `origin/master` is at the Hold and quit handoff (section 34, `0895eba1`). Sections 35 and the commits since are local.
- **Still open:** as in sections 25, 29 and 33, plus the unreachable solver and comment code above.

## 36. Update: Select menu simplified; Edit moved next to File (2026-11-08)

Installed app rebuilt after commit "Menu bar order: File, Edit, Select, Game, Options, Help" (120 MB, arm64, ad-hoc signed).

- **Select menu** (commit "Select menu: remove All games by name and Select random game"): it is now Recent games, Favorite games, Add to favorites, Remove from favorites, a divider, All games (Cmd-V), Popular games, French games, Mahjongg games, Oriental games, Special games, Custom games. Removed: the "All games by name" A to Z submenu (its builder `_addSelectAllGameSubMenu` stays because `updateGamesMenu` still uses it to split a long list; its menu path `.menubar.select.allgamesbyname` and the `menu2` update in `updateCustomGamesMenu` are gone), Select random game (`mSelectRandomGame`, `_mGetPossibleRandomGames`, `Application.chooseRandomOutOfGames` and the Cmd-R binding). `Application.getRandomGameId` and the `--random-game` command-line option are separate and still work.
- **Menu bar order** (commit above): File, Edit, Select, Game, Options, Help. This follows the macOS convention of Edit directly after File, with the app's own menus after it. It only reorders the creation of the menus in `ui/tktile/menubar.py`; contents and shortcuts are unchanged.
- **Decision recorded:** Recent games stays in Select, not File. It lists recently played game types, not files, and "Open Recent" in File would suggest saved game files. If saved-file history is wanted later, it needs new code (the app does not track recently opened files).
- **Verification (light):** pyflakes and the unit tests (19) pass; real-app source runs printed the Select menu and the menu bar order, and added and removed a favorite. The installed app was checked with `--version` and `codesign -v`; the pre-bundle `data/html N` cleanup removed one stray `data/html 2`. Nothing was checked by eye.
- **Still open:** as in sections 25, 29, 33 and 35.

## 37. Update: Edit menu slimmed down; Wizard, Custom games and Solver help removed (2026-11-08)

Installed app rebuilt after commit "Help: remove the Solitaire Wizard and Solver pages" (120 MB, arm64, ad-hoc signed).

- **Edit menu** (commit "Slim the Edit menu; Restart moves to Game; Wizard and Custom games removed"): Undo, Redo, a divider, Set bookmark, Go to bookmark, Clear bookmarks. Removed: Redo all (`mRedoAll`), Replay (`mReplay`; `Game.startReplay` itself stays), Solitaire Wizard, Edit current game, Delete current game (`wizardDialog`, `mWizard`, `mWizardEdit`, `mWizardDelete`, `_calcWizardDialog`, `tile/wizarddialog.py`), and the `ms.replay` and `ms.custom_game` menu states.
- **Restart** (Cmd-G) moved from Edit to the Game menu, right after Pause; its menu path is now `game.restart` (`setMenuState` in `actions.py`); the toolbar Restart button is unchanged.
- **Select menu:** no Custom games submenu (`_addSelectCustomGameSubMenu` and `updateCustomGamesMenu` are gone). It is now Recent games, Favorite games, Add to favorites, Remove from favorites, a divider, All games, Popular, French, Mahjongg, Oriental and Special games.
- **Left in place on purpose:** `pysollib/wizardutil.py` (`WizardWidgets` is used by `customgame.py` when loading custom game files from the plugins folders) and the solver window code; both are unreachable from the UI and are cleanup candidates.
- **Help pages** (commit "Help: remove the Solitaire Wizard and Solver pages"): deleted `html-src/solitaire_wizard.html` and `solver.html`, dropped them from `gen-html.py` and the index, and removed the "a solitaire wizard" feature line and the Wizard references in `plugins.html`. The regenerated `data/html` and the installed bundle contain neither page.
- **Verification (light):** pyflakes and the unit tests (19) pass; all 178 modules import; a real-app source run printed the new menu bar and every menu (Restart greys out correctly through its new path, favorites still add and remove). The installed app was checked with `--version` and `codesign -v`; the pre-bundle `data/html N` cleanup was clean and a later `make rules` left one empty `data/html 3`, which was removed. Nothing was checked by eye.
- **Current menu bar:** File (New game, Open, Save, Save as, Quit), Edit (Undo, Redo, bookmarks), Select, Game (Deal cards, Auto drop, Shuffle tiles, Pause, Restart, Hint, Highlight piles, Find card, Show full picture, Piles description, Demo, Select game by number), Options (Play options, Layout, Animations, Sound), Help.
- **Still open:** as in sections 25, 29, 33 and 35, plus the unreachable wizard and solver code above.

## 38. Update: menus renamed; one bookmark with toolbar buttons (2026-11-08)

Installed app rebuilt after commit "Toolbar: add Set bookmark and Go to bookmark buttons" (120 MB, arm64, ad-hoc signed).

- **Menu renames** (commit "Rename the Select menu to Games and the Game menu to Play"): the old Select menu is now **Games** and the old Game menu is now **Play** (the user chose "Games"; "Play" was my pick because everything in it is done during a game). Menu bar: File, Edit, Games, Play, Options, Help. Because menu paths come from the labels, the `setMenuState` paths in `actions.py` became `play.restart`, `play.dealcards`, `play.autodrop`, `play.shuffletiles`, `play.pause`, `play.hint`, `play.highlightpiles`, `play.findcard`, `play.showfullpicture`, `play.demo`, and the favorites and recent paths in `ui/tktile/menubar.py` became `.menubar.games.*`. The dead `menu.name == "select"` branch in `_addSelectAllGameSubMenu` was removed.
- **One bookmark** (commit "Bookmarks: one bookmark with Set bookmark and Go to bookmark"): Edit is now Undo, Redo, a divider, Set bookmark (Cmd-K) and Go to bookmark (Cmd-J). The nine-slot submenus, Clear bookmarks (`mClearBookmarks`) and the Cmd-1 to Cmd-9 shortcuts are gone; the user-facing bookmark is slot 0 (`mSetBookmark(0)`, `mGotoBookmark(0)`). The prompts are "Replace the bookmark?" and "Go to the bookmark?". The internal slots -1 (undo of go-to) and -2 (used when the All games window opens) in `Game.setBookmark` and `gotoBookmark` are unchanged. `updateBookmarkMenuState` greys Go to bookmark until slot 0 exists. The help page describes one bookmark. The Cmd-B shortcut was left for cycling card backs.
- **Toolbar buttons** (commit "Toolbar: add Set bookmark and Go to bookmark buttons"): the buttons `bookmark` (outline Phosphor `bookmark-simple`) and `gotobookmark` (filled `bookmark-simple-fill`) follow Redo. `PysolToolbarTk._createButton` gained a `name` argument for the second one. `PysolToolbar` in `actions.py` has `mSetBookmark` and `mGotoBookmark` wrappers, and `updateBookmarkMenuState` also sets the buttons' states through `setToolbarState`. `TOOLBAR_BUTTONS` lists both, so they appear in Visible buttons. `scripts/render_toolbar_icons.swift` now renders thirteen icons and uses `scripts/phosphor-icons/bookmark-simple.svg` and `bookmark-simple-fill.svg` (the fill icon comes from `assets/fill/` in `phosphor-icons/core`).
- **Options migration:** `visible_buttons` alone cannot tell "hidden" from "added later", so `Options.save` now writes `known_buttons` (all `TOOLBAR_BUTTONS`) and `Options.load` shows any button missing from it. A file without `known_buttons` is read as written before the bookmark buttons existed. Verified: the user's old file shows both buttons; a file listing both as known with `bookmark` unlisted keeps it hidden.
- **Verification (light):** pyflakes and the unit tests (19) pass; real-app source runs showed the new menu bar, the Play menu states, the bookmark flow (set at move 1, played to move 3, Go to bookmark returned to move 1 from both the menu path and the toolbar button) and the toolbar button order and states. The installed app was checked with `--version` and `codesign -v` (both new icons are in the bundle); the pre-bundle `data/html N` cleanup removed one stray folder. Nothing was checked by eye; the 24 px bookmark icons are the ones to look at.
- **Push state:** pushed through section 37 earlier; sections 38 and the commits since go out with this entry.
- **Still open:** as in sections 25, 29, 33, 35 and 37.

## 39. Update: Help menu slimmed; stale help pages deleted (2026-11-08)

Installed app rebuilt after commit "Help menu: remove How to use PySol, What's new and Report a bug; delete stale help pages" (120 MB, arm64, ad-hoc signed).

- **Help menu** is now PySolFC Help (on macOS Tk adds this item itself and calls `mHelp`; Windows and Linux show Contents, Cmd/Ctrl-F1), Rules for this game (F1), a divider, License terms; Windows and Linux still add About. Removed `mHelpHowToPlay`, `mHelpNews` and `mHelpReportBug`.
- **Deleted pages:** `html-src/install.html`, `news.html`, `news_old.html`, `plugins.html`, `report_bug.html`. They are gone from `gen-html.py`, the help index and the Settings page. `howtoplay.html` stays and is linked from the index. `credits_old.html` stays (linked from Credits).
- **Verification (light):** AST parse of the changed files; `make rules` output has none of the deleted pages; installed bundle has none; `--version` and `codesign -v` pass. Not launched or checked by eye.
- **Still open:** as in sections 25, 29, 33, 35 and 37; plus `howtoplay.html` scoring notes and the `help.py` credits line about music; `docs/`, `po` and `MANIFEST.in` may still name the deleted pages.

## 40. Update: View menu added (2026-11-08)

Installed app rebuilt after commit "Add a View menu with Show toolbar, Show status bar and Full screen" (120 MB, arm64, ad-hoc signed).

- **View menu** sits between Edit and Games: Show toolbar, Show status bar, a divider, Full screen (F11; Ctrl-Cmd-F on macOS), all check items. Menu bar: File, Edit, View, Games, Play, Options, Help.
- **Show toolbar** uses `tkopt.toolbar_shown` and `mViewToolbar`; `opt.toolbar` 0 still means hidden, and `_toolbar_side` remembers the last side so re-showing returns there. `setToolbarSide` keeps the check item in sync. The "Hide" entry was removed from the Position submenu.
- **Show status bar** is the old Layout checkbutton (`mOptStatusbar`), moved here.
- **Full screen** is `mViewFullscreen` / `_toggleFullscreen`: sets `opt.wm_fullscreen` and `top.attributes('-fullscreen')`. Session-only; `wm_fullscreen` is still a fixed, unsaved option. The check item does not follow fullscreen changes made outside the app (for example the green window button).
- **Options > Layout** is now Toolbar (position, size, button style, visible buttons), Cards (Decks, Backs), Background color, Spread stacks. The Settings help page was updated.
- **Verification (light):** py_compile; a source run built the menu bar without errors; the installed app passes `--version` and `codesign -v`. The View menu was not opened or toggled by hand.
- **Idea discussed, not done:** a single Settings window (Cmd-comma on macOS via `tk::mac::ShowPreferences`) with General, Assist, Appearance and Toolbar tabs, replacing the Options menu on macOS.
- **Still open:** as in sections 25, 29, 33, 35, 37 and 39.

## 41. Update: View menu uses the native macOS full screen item (2026-11-08)

Installed app rebuilt after commit "View menu: leave Full screen to macOS; keep F11 item on other platforms" (120 MB, arm64, ad-hoc signed).

- **Problem:** macOS adds its own "Enter Full Screen" (Ctrl-Cmd-F) to any menu titled View, so section 40's Full screen item appeared twice.
- **Fix:** on macOS the View menu is now Show toolbar, Show status bar, plus the native item; the app's own Full screen check item and its Ctrl-Cmd-F binding exist only when `sys.platform != "darwin"` (Windows and Linux keep "Full screen", F11). The native item's text ("Enter Full Screen" / "Exit Full Screen") is set by macOS and cannot be renamed without renaming the View menu. The Settings help page mentions both.
- **Verification (light):** py_compile; the installed app passes `--version` and `codesign -v`. The native item was not clicked, so whether it toggles the game window correctly is unconfirmed.
- **Still open:** as in section 40.

## 42. Update: rebrand to PySol 26 with year-based versions (2026-11-08)

Installed app rebuilt as `~/Applications/PySol.app` (120 MB, arm64, ad-hoc signed). The old `~/Applications/PySolFC.app` was deleted, so the Dock tile that pointed at it is dead and must be re-added.

- **Name:** the product is "PySol 26" (the year); the tagline is "A reimagining of PySolFC". `settings.TITLE` is `'PySol %d' % year`, used in window titles, About, dialogs and the bundle display name. New `TITLE_CLASS = 'PySol'` (no year) is used for the Tk root class, `Toplevel` class and the X11 option lookup. The window title no longer appends the version.
- **Version:** `VERSION_TUPLE = (26, 11)` is YY.MM; an interim update is `(YY, MM, DD)`. `VERSION` zero-pads month and day ('26.11', '26.11.08'). `--version` prints "PySol 26 version 26.11" (`tests/lib/pysol_tests/test_version_flag.py` updated). Saved options store `last_version` as a list; nothing compares it, and old saved games only check `< (2, 20, 0)`, so 3.7.0 files and games still load.
- **Fixed identifiers (do not change each year):** `PACKAGE = 'PySolFC'` (the `~/.PySolFC` settings folder and data directories), bundle ID `net.sourceforge.pysolfc`, bundle file `PySol.app`, executable `PySol` (`BUNDLE` in `setup_osx.py`). The year appears only in `CFBundleDisplayName`, the About box, window titles and the version. Tk's app menu uses `CFBundleName` ("PySol"), so the macOS app menu and Help item say "PySol", not "PySol 26".
- **About box:** "PySol 26 / A reimagining of PySolFC / Version 26.11", "Based on PySol, PySol Fan Club edition and PySolFC", keeps the Oberhumer, Mt. Hood and Skomoroh copyrights, "PySolFC contributors", and adds "Modifications Copyright (C) 2026 the PySol 26 authors". The random "A World Domination Project" line is gone. `PACKAGE_URL` (About link) now points at `https://github.com/spidermedic/pysol` instead of the upstream site.
- **Each January:** change the year in `VERSION_TUPLE`; the name follows. For an interim update use a three-part tuple.
- **Not renamed:** the repo and local folder, help pages and rules text that say "PySol", `docs/`, man pages, `po` files and Windows/Linux installer scripts (`scripts/create_iss.py`, `scripts/linux-install.py` still say PySolFC), `README.md`, and the `.PySolFC` folder.
- **Verification (light):** py_compile on the changed modules; a source `--version` and a short source launch with no traceback; the installed bundle passes `--version` and `codesign -v` and its Info.plist shows the new name, executable and version. The About box and menu bar were not looked at.
- **Still open:** as in sections 39 to 41, plus the renaming leftovers above.

## 43. Update: About in the Help menu (2026-11-08)

Installed app rebuilt after commit "Help menu: show About on every platform" (120 MB, arm64, ad-hoc signed).

- **Help menu** is now PySolFC Help (added by Tk on macOS; Contents on Windows and Linux), Rules for this game (F1), a divider, License terms, a divider, About PySol 26. On macOS About also stays in the app menu.
- **Verification (light):** py_compile; the installed app passes `--version` and `codesign -v`. The menu was not opened by hand.
- **Still open:** as in section 42.

## 44. Update: Settings window replaces the Options menu (2026-11-08)

Installed app rebuilt after commit "macOS: put Settings in the app menu" (120 MB, arm64, ad-hoc signed).

- **Settings window** (new `pysollib/tile/settingswindow.py`, class `SettingsWindow`): one non-modal window, live-applied, with tabs General (Click to move cards, Confirm before quitting, Sound, Animation speed Off/Slow/Medium/Fast), Assist (Automatic play, Shade legal moves, the per-game options; inapplicable ones greyed out per game), Appearance (Deck name plus Choose, card Backs as thumbnail buttons, Background color swatch plus Choose, Spread stacks) and Toolbar (Position, Icon size, Button style, Visible buttons). It binds the existing `tkopt` variables and calls the existing menubar handlers (`mOptSound`, `mOptAnimations`, `mOptToolbarSize`, `mSelectCardsetDialog`, ...), so saved options are unchanged. `refresh()` re-reads the current state; it runs on window focus, from `updateMenus` (autoplay greying) and from `updateBackgroundImagesMenu` (rebuilds the Backs row when the deck changes). One instance is kept in `menubar._settings`; `mOptSettings` opens or raises it.
- **Menus:** the Options menu is gone on macOS. Settings (Cmd-comma, also bound in the app) is in the custom `apple` app menu under About, because that custom menu replaces Tk's own Preferences item (`tk::mac::ShowPreferences` is not used). Windows and Linux get an Options menu with only Settings (Ctrl-comma). `createToolbarMenu` stays because the toolbar's right-click menu uses it.
- **Removed:** `mOptPlayOptions` and `_applyChecklist` in `actions.py` (the Play options dialog; `ChecklistDialog` and the option tables in `tkconst.py` remain, the tables feed the new window), and the `options.layout.cards.backs` menu path.
- **Help:** `settings.html` rewritten for the window; `assist_options.html` and `faq.html` point at Settings.
- **Mistake and fix:** the first build had no Settings item on macOS because the custom app menu hid Tk's built-in one; fixed by adding the item to that menu. A stray empty `data/html 3` (iCloud) was in the first installed bundle and was removed from it.
- **Verification (light):** a scripted source run opened the window and changed animation speed, toolbar side, icon size and button style and set sound, all applied; the installed app passes `--version` and `codesign -v`. The window and the app menu were not looked at by eye; Deck, Background color and Visible buttons buttons and the autoplay greying were not exercised.
- **Still open:** as in section 42, plus the unused option tables if the Play options dialog is never coming back.

## 45. Update: About only in the app menu on macOS (2026-11-08)

Installed app rebuilt after commit "Help menu: About only in the app menu on macOS" (120 MB, arm64, ad-hoc signed).

- **Help menu on macOS** is now PySolFC Help, Rules for this game (F1), a divider, License terms. About PySol 26 is in the app menu only (macOS convention). Windows and Linux still show About at the bottom of Help. This reverses the macOS part of section 43.
- **Verification (light):** py_compile; the installed app passes `--version` and `codesign -v`; no stray `html N` folder in the bundle. The menus were not looked at by eye.
- **Still open:** as in sections 42 and 44.

## 46. Update: clean-up pass (2026-11-08)

Installed app rebuilt after commit "Clean up stale docs and leftovers" plus the dead-method removal below (120 MB, arm64, ad-hoc signed).

- **Help pages:** removed the "Some notes about scoring" section from `howtoplay.html` (statistics are gone), the Shift-Ctrl-V "search tab" shortcut line, and the "persistent bookmarks" wording in `intro.html` (now "a bookmark").
- **Shortcut:** removed the Shift-Ctrl-V binding in `menubar.py` (it opened the removed Search tab). Ctrl-V still opens the preview game list.
- **Credits:** `help_credits` no longer thanks Carl Larsson for background music.
- **Man page:** `docs/pysolfc.6` no longer mentions player statistics, a solitaire wizard, `statistics.dat`, `comments.dat`, music folders, `PYSOL_MUSIC` or the player name from USER/LOGNAME.
- **Build:** `setup_osx.py` ran `scripts/all_games.py` without `pysollib` on the path, so the bundled `docs/all_games.html` was empty (0 bytes); it now sets `PYTHONPATH` (274,865 bytes in the bundle).
- **Dead code removed** (no references anywhere): `mHelpWebSite`, `mOptNumCards`, `mOptHelpbar`, `updateProgress`, and the then-unused `openURL` and `PACKAGE_URL` imports in `actions.py`.
- **Install-script lesson:** a zsh "no matches found" error from an unmatched glob in an `&&` chain silently skipped the arm64 thinning once (157 MB app); always confirm the bundle is 120 MB.
- **Verification (light):** py_compile; a scripted source run of the Settings window still works; unit tests give 19 tests with the one known failure (`test_version_flag`: no `python` on PATH in this shell, exit 127); installed app passes `--version` and `codesign -v`.
- **Still open (not done on purpose, larger or riskier):** unreachable solver window and its game hooks (`tile/solverdialog.py`, `ui/tktile/solverdialog.py`), `wizardutil.py` (still used by `customgame.py` for plugin games), comment and hint import/export code; dead `auto_scale` branches; `po` files and untranslated new labels (Settings window strings are passed through `_()` but not extracted); Windows and Linux installer scripts, `README.md` and the repo still say PySolFC; commented-out music lines in `MANIFEST.in`.

## 47. Update: Python modernization pass, minimum Python 3.10 (2026-11-08)

Installed app rebuilt from commit `754c557f` (120 MB, arm64, ad-hoc signed, `--version` and `codesign -v` pass). The user confirmed the app is working.

- **Scope chosen by the user:** minimum Python 3.10, and only real issues plus safe mechanical changes. Not done on purpose: f-string conversion of the ~233 `%`-format strings, `pathlib`, type hints, `match`/`dataclass` rewrites, anything in the pickled save-game format. Four commits, one per group, so any can be reverted alone.
- **Dead Python 2 code** (`97cdb1c0`): removed the `sys.version_info` branches in `move.py` (`cmp` is now unconditional), `mfxutil.py` (`latin1_to_ascii` is `return n`), `options.py`, `init.py` and `mygettext.py` (no `ungettext`/`ugettext` fallbacks), and `class _Grid(object)` in `sudoku_gen.py`. `gamedb.to_unicode` was kept: it decodes bytes, it is not an identity function. The 189 `-*- coding` cookies were left alone.
- **Bugs and deprecations** (`d2a47935`):
  - `uclock` in `mfxutil.py` was overridden with `time.time` on macOS and Linux, so animation timing used a non-monotonic clock; it is now `time.perf_counter` everywhere and the `time.clock` fallback is gone.
  - `get_default_resampling` preferred `Image.ANTIALIAS` (removed in Pillow 10); it now uses `Image.Resampling.LANCZOS`.
  - `tkhtml.basejoin` had an `if 0:` branch calling `urllib.basejoin`, which does not exist; deleted.
  - `setup_osx.py` no longer uses `shell=True`; `scripts/create_iss.py` closes the file it execs.
- **Encodings** (`3c9f673f`): text-mode `open()` calls now say `encoding='utf-8'` (default is locale-dependent, cp1252 on Windows). Cardset `config.txt` and `COPYRIGHT` readers use `errors='replace'` so a stray latin-1 byte in a user cardset cannot crash loading. `tkhtml` uses `open` instead of `codecs.open`.
- **Metadata** (`754c557f`): `setup.py` has `python_requires='>=3.10'` and classifiers 3.10 to 3.14; CI matrix is 3.10 to 3.14 (3.7 to 3.9 and the old `flake8-import-order` branch removed); README says Python 3.10 or later.
- **Left alone, with reasons:** `shell=True` for the FreeCell solver in `hint.py` and `init.py` (`FCS_COMMAND` is user-configurable and may carry arguments); `getopt` in `main.py` (not deprecated); `import *` in `pysoltk.py`; the `__del__` methods in `hint.py` and `pysolaudio.py`.
- **Verification:** 19 unit tests with the same results as before (run with `.venv/bin/python -m unittest`; the system Python lacks `attr`), all 170 `pysollib` modules import with `DeprecationWarning` as error, no compile warnings, flake8 clean on touched lines (a few older warnings in `options.py`, `init.py`, `setup_osx.py` and `tkconst.py` were already there). The dev copy started and drew the Standard cardset without a traceback. The installed bundle's `mfxutil` has no `ANTIALIAS` or `time.clock`. Nothing was checked by eye.
- **Smoke test script (deleted, never committed):** a script that drove the real app through Klondike, FreeCell, Spider and Pyramid with a throwaway `HOME` passed every Klondike check (deal, animated and dragged moves, undo/redo, autoplay, save/load, hint, help viewer, gettext, resampling), then hung: `quitGame(next_id)` did not end the Tk loop, so the second game never started. The same hang happened on the commit before this pass (`dcb38d26`, checked in a throwaway worktree), so it was the script, not these changes. The user had it deleted on 2026-11-08. If a scripted full-app check is wanted again, run one process per game.
- **Unclosed-file warnings (fixed in `4bc522fb`, see section 49):** `-W default` showed `ResourceWarning: unclosed file` from `tkutil.py` (`Image.open(file).convert('RGBA')`) and the `fc-solve` probe pipes in `init()`.
- **Theme question:** the dev-copy test runs looked different from the installed app. No theme code was touched (the only `options.py` change was a dead branch in `save()`). Likely causes: the smoke test used fresh default settings (table `#008200`, not the saved `#006d04`) and the dev copy runs under python.org's `Python.app`, not the py2app bundle, on a Mac in Dark mode. Not confirmed by comparing screenshots.
- **Settings touched:** the first dev launch of this pass used the real `~/.PySolFC`; `options.cfg` was rewritten at 16:47. Probably the app saving on exit, possibly the user. Contents were not compared.
- **iCloud:** a stray untracked `data/html 2` appeared during the test runs and was deleted (it was not in `git ls-files`). None in the final bundle.
- **Still open:** as in section 46.

## 48. Update: plain Help menu on macOS (2026-11-08)

Installed app rebuilt after commit `2137523e` (120 MB, arm64, ad-hoc signed). The user confirmed the icon is gone.

- **Problem:** on macOS the "PySol Help" item in the Help menu had an icon that no other menu item has. It was not our item: macOS treats a menu whose Tk name is `help` as the system Help menu, and Tk adds its own `<app> Help` item there (bound through `tk::mac::ShowHelp`), which the system decorates because it is a standard action.
- **Fix:** on macOS the menu is named `helpmenu` (`pysollib/ui/tktile/menubar.py`) and contains our own `PySol Help` item (`mHelp`, accelerator Cmd-F1), Rules for this game, a divider and License terms. The `tk::mac::ShowHelp` command is no longer registered. Windows and Linux are unchanged (menu `help`, with Contents and About). The menu name is stored in `self.help_menu_name`, and `actions.py` uses it for the "Rules for this game" state path (`helpmenu.rulesforthisgame` on macOS, `help.rulesforthisgame` elsewhere).
- **Trade-off:** the system Help menu's search box is gone, because macOS no longer sees this as its Help menu.
- **Build note:** an iCloud duplicate `data/html 2` appeared in the source folder and the bundle again during this build. Removed from both, re-signed, then installed.
- **Pushed:** `origin/master` now includes the modernization pass (section 47) and this change.

## 49. Update: unclosed files and pipes (2026-11-08)

Commit `4bc522fb`; installed app rebuilt after it.

- **Cause:** `Image.open(file).convert('RGBA')` in `pysollib/ui/tktile/tkutil.py` (`PIL_Image.__init__` and the card-back code) kept one file handle open per card image until garbage collection. The `fc-solve` probe in `pysollib/init.py` never closed its stdout/stderr pipes and used `os.wait()`.
- **Fix:** `with Image.open(...) as im:` before `convert`; the probe closes both pipes and uses `p.wait()` on posix (still no wait on Windows). `TileManager.register` in `resource.py` got the same `with` (effectively dead code since tiles are solid colors). The stored background image in `tkcanvas.py` is kept open on purpose and was not changed.
- **Verification:** a 25-second source run with `-W default` and a fresh `HOME` printed zero `ResourceWarning`s (before: one per card image); unit tests unchanged (19, the one known `--version` error); flake8 clean on the touched lines. The card display was not checked by eye.

## 50. Update: stale leftovers removed (2026-11-08)

Commit "Remove stale leftovers: manifest, man page, readmes, tile folders". Not rebuilt or installed: the only code change is in `main.py` (no longer creates empty `~/.PySolFC/tiles/*` folders at startup; existing ones are harmless and can be deleted by hand).

- **`MANIFEST.in`:** removed the `android/` includes and the commented-out music lines; the cardset `graft` lines now list the 18 `data/cardset-*` folders that exist (`setup.py` reads these lines to decide which cardsets to install, so a stale list would have shipped nothing for the new sets). Added `scripts/prune_card_backs.py`.
- **Docs:** `docs/pysol.6` deleted (the original PySol man page, describing `~/.pysol`, music and player statistics; `pysolfc.6` is the real one). `pysolfc.6` no longer mentions table tiles or `PYSOL_TILES`. `docs/README.SOURCE` lost the `stats.py` and `tkstats.py` entries and the tiles and music wording. `README.md` points at `dist/PySol.app`, says Tk 8.6, and no longer links the old music repository.
- **Left alone on purpose:** `po/*.po`, `po/*.pot` and `locale/*/pysol.mo`. They still contain removed strings and lack the new labels ("Click to move cards", "Visible buttons", "Layout", Settings window and so on), so those show in English. Fixing that means `make pot` (needs xgettext) plus real translations in five languages; `docs/README` (the 2002 PySol readme); the name "PySolFC" in README prose, `scripts/create_iss.py` and `scripts/linux-install.py`; `pysolfc.6` file name and its sound-mod option text.
- **Verification (light):** `setup.py`'s cardset parsing finds all 18 folders and none is missing; `mandoc -Tlint` shows only the warnings that were already there; unit tests unchanged (19, the one known `--version` error); a source run with a fresh home stayed up 15 s.
- **Still open:** the unreachable solver, wizard, comment and layout import/export code, and the dead `auto_scale` branches (section 46); translations of the new labels.

## 51. Update: translations removed (2026-11-08)

Commit "Remove the translations and their build steps" (`6713d6ac`). Not rebuilt or installed yet; the installed app still ships `locale/` until the next build.

- **Asked by the user:** get rid of the translations, revisit them once the app is where they want it.
- **Deleted:** `po/` (the per-language `*_pysol.po` and `*_games.po`, `pysol.pot`, `games.pot`) and `locale/` (compiled `pysol.mo` for de, fr, it, pl, pt_BR, ru). They were already stale: they lacked the new Settings, View, Layout and other labels and still held removed strings.
- **Build and packaging:** the `pot` and `mo` Makefile targets are gone and `dist`/`rpm` no longer depend on `mo`; `setup.py` and `setup_osx.py` no longer ship `locale`; `MANIFEST.in` lost `po/*` and `graft locale`; the macOS workflow runs `make rules` instead of `make rules mo`; the README build steps and the `.gitignore` `po/*.po` lines were updated. `gettext` (the Homebrew package) is no longer needed to build.
- **Kept on purpose:** the `_()` and `n_()` markers throughout the code, `pysollib/mygettext.py`, the gettext binding in `init.py` and the unused `language` option. With no catalogs the lookups fall back to the English text. This keeps a later restore cheap. Side effect worth knowing: every `_()` call still tries to find a catalog on disk before falling back, so making `mygettext` a plain pass-through would be a small startup speed-up; not done.
- **Not touched:** `contrib/help-pages-translation-to-french` (a separate help-page translation tool), `data/pysolfc.glade`.
- **To bring translations back:** the old files are in git history: `git checkout 0c597444 -- po locale Makefile` restores the catalogs and the `pot`/`mo` targets (then re-add `locale` to the `DATA_FILES` list in `setup_osx.py`, the data files in `setup.py` and `MANIFEST.in`). Expect to run `make pot`, translate the new labels, then `make mo`; needs `gettext` from Homebrew.
- **Verification (light):** unit tests unchanged (19, the one known `--version` error); `setup.py --version` works; source runs with a fresh home under `en_US.UTF-8` and `de_DE.UTF-8` stayed up 15 s with no traceback (German now shows English); `_()` and `ungettext` return the English text.
- **Still open:** as in section 50.

## 52. Update: stray config files and the PySol name in the docs (2026-11-08)

Commit `145f047b` (docs and packaging only; no app code). Not rebuilt or installed.

- **`~/.PySolFC` clean-up:** deleted the empty `music` folder and the empty `tiles` folder tree. `tiles` had reappeared at 17:42 because the installed app is an older build that still creates it; a rebuild stops that. **`statistics.dat` was NOT deleted**: the deletion was blocked by the permission check. It is 1 KB, no longer read by anything, and holds player `doug` with 2 games played, 0 won (game 11). Delete it by hand (`rm ~/.PySolFC/statistics.dat`) or tell the next session to.
- **README.md:** new opening ("PySol 26 - a reimagining of PySolFC", credit to PySol, the Fan Club edition and PySolFC, GPL, pointer to this log). Removed the old "PySol Fan Club" logo, the upstream "Call for Contributors" text, the imgur screenshot of the old interface and the shields for the upstream CI. The two `git clone` examples now use `https://github.com/spidermedic/pysol.git`.
- **Renamed in prose:** `docs/pysolfc.6` is now `docs/pysol.6` (name, description and platform text reworded; paths and copyright lines unchanged); `CONTRIBUTING.md` title and intro; `data/pysol.desktop` (Name=PySol, 1200 games); `appdata.xml` `<name>`; the title in `scripts/all_games.py`; the Windows installer name and message in `scripts/create_iss.py`.
- **CI fix:** `.github/workflows/macos-package.yml` still looked for `dist/PySolFC.app` and `Contents/MacOS/PySolFC` (the bundle is `PySol.app` / `PySol` since section 42) and would have failed; it now uses PySol names for the app, zip, dmg and volume. Not run on GitHub.
- **Deliberately unchanged:** `PACKAGE = 'PySolFC'`, `~/.PySolFC`, the `/usr/share/PySolFC` data paths, the upstream URLs (shlomif/PySolFC, sourceforge, cardset archives), `NEWS.asciidoc` and the release history in `appdata.xml`, the AppStream id `io.sourceforge.pysolfc.PySolFC`, the "PySolFC contributors" credit, the rest of `CONTRIBUTING.md` (upstream release steps) and the tests and scripts that name old PySolFC archives.
- **Still open:** the logo. `html-src/images/high_res/logo_horizontal.png` (and the other logos under `html-src/images`) still say "PySol Fan Club"; they appear in the generated help pages. A new logo needs to be made. Also `contrib/` scripts and `.appveyor.yml`/`.travis.yml` still use the old name (not touched; the CI files are upstream leftovers).

## 53. Update: no translation functions in the app (2026-11-08)

Commit `a9e48d55`. Supersedes the "kept on purpose" part of section 51. Not rebuilt or installed yet.

- **Asked by the user:** fix the translation lookup; "I don't want any translation function in the app". Every `_()` call did a disk search for a catalog before falling back to English.
- **What was removed:** all ~1,200 `_("text")` and `n_("text")` calls were rewritten to the plain string (a token-based script, so `_` used as a variable name in `hint.py`, `setup.py` and `matchthree.py` was untouched); the 27 dynamic calls (`_(name)`, `_(CSI.TYPE[...])`, `_(text + ...)`) became the plain expression. `ungettext(one, many, n)` became `one if n == 1 else many` (game won texts, Mahjongg and Shisen-Sho status, `stack.py` card and redeal counts, solver dialog); `pgettext("size", "Medium")` became "Medium". All `from pysollib.mygettext import ...` lines are gone and `pysollib/mygettext.py` is deleted. `n_` is gone from `settings.py`.
- **Also removed:** the gettext binding and the locale-folder search in `init.py` (and the `LANG` fix-up for Windows and Android that only existed for it; `locale.setlocale` stays), the `language` option (`options.py`; old option files that still have `language = ...` load fine and the key is left in the file), the gettext mode of `scripts/all_games.py` and its `builtins._` shims, the `builtins._` shims in both `gen-html.py` scripts, the dead `gettext.install` blocks in `tile/statusbar.py` and `tile/tkhtml.py`, and the `<translation>` line in `appdata.xml`.
- **Style fixes:** removing `_(` broke the visual alignment of many continuation lines; `autopep8` (dev tool, installed into `.venv` only) fixed E127/E128/E303/E501 on the touched files, and a few long plural expressions were written as plain `if`/`else`. flake8 on the whole repo is back to three old warnings (`math` unused in `ui/tktile/menubar.py`, a long line in `scripts/prune_card_backs.py`, `setup_osx.py` import order).
- **Things that no longer work:** user plugins or custom game files that do `from pysollib.mygettext import _` will fail to import. The plugin help page was deleted earlier and the plugins folder is empty here. Bringing translations back now means re-adding a wrapper module and wrapping the strings again (the old `_()` calls are in git history, commit before `a9e48d55`); it is no longer a quick restore.
- **Verification:** unit tests unchanged (19, the one known `--version` error); flake8 reports no undefined names; all 169 `pysollib` modules import with `DeprecationWarning` as error; source runs with a fresh home started Klondike, FreeCell, Spider, Pyramid, Double Mahjongg Big Castle, Memory 16 and Ishido without errors; a scripted run opened the Settings window and the help viewer and called the stack help texts, game and cardset type names, the full game list and the win status without errors; a run with an old options file containing `language = de` started normally. The win and finished dialogs and the Mahjongg status text were not shown on screen.
- **Still open:** as in section 52.

## 54. Update: rebuilt and installed after the clean-up commits (2026-11-08)

Installed app rebuilt from commit `8b013ecc` (120 MB, arm64, ad-hoc signed, `codesign -v` passes, `--version` prints `PySol 26 version 26.11`). It includes everything from sections 47 to 53: the Python 3.10 pass, the Help menu change, the closed files and pipes, the stale-leftover clean-up, no translations and no translation functions, and the PySol name in the docs. `locale/` and `pysollib/mygettext.py` are no longer in the bundle. The standard-library `gettext` module is still in it because other libraries import it; PySol does not use it. No stray `data/html N` folders this time. `docs/all_games.html` regenerated at 274,863 bytes.

- **Not looked at on screen:** the installed app has not been launched by the assistant (it reads the real `~/.PySolFC`). Worth a quick look: Help menu, Settings window, a deal in a few games, the win dialog text.
- **`~/.PySolFC/tiles` and `music`:** gone. The rebuilt app no longer creates `tiles`.
- **`~/.PySolFC/statistics.dat`:** deleted by the user after the assistant's delete was blocked by the permission check. Nothing read it.
- **Still open:** the logos that say "PySol Fan Club" (`html-src/images`); the unreachable solver, wizard, comment and layout import/export code and the dead `auto_scale` branches (section 46); the slow canvas redraw (section 13); Windows and Linux paths have never been run since the toolkit removal.
- **Pushed:** `origin/master` includes everything above.

## 55. Update: no more `~/.PySolFC/boards` (2026-11-08)

The app no longer creates the `boards` folder at startup (`app.dn.boards` is gone from `pysollib/app.py` and `pysollib/main.py`). It was only for exporting and importing starting layouts, which were removed in section 33. A fresh source run creates `cardsets`, `plugins` and `savegames` only. The user removes their existing empty `boards` folder themselves. Not rebuilt: the installed app still creates it until the next build.

## 56. Update: settings folder renamed to `~/.pysol` (2026-11-08)

Asked by the user. Not rebuilt or installed: the installed app still uses `~/.PySolFC` until the next build; **the first launch of the new build will move `~/.PySolFC` to `~/.pysol`** (options, saved games, cardsets and plugins folders come along).

- **Change:** `getprefdir` in `pysollib/mfxutil.py` returns `~/.pysol` on macOS and Linux and `%APPDATA%\PySol` on Windows (was `~/.PySolFC` and `%APPDATA%\PySolFC`; the Windows part is untested). New `_adopt_old_prefdir(old, new)`: if the new folder does not exist and the old one does, it renames the old one to the new name. If the rename fails (permissions, say) the app keeps using the old folder, so nothing is lost. If both exist, the new one wins and the old one is left alone.
- **Not changed:** `PACKAGE = 'PySolFC'` in `settings.py` is stored inside every saved game and checked on load (`game/__init__.py`), so changing it would make old saves "invalid or damaged". It also names the data directories (`/usr/share/PySolFC`, `share/PySolFC` in `setup.py`). The AppStream id and the bundle id are also unchanged. Error messages from `print_err` still start with `PySolFC:`.
- **Docs and scripts updated:** README (cardset instructions), `docs/pysol.6` (FILES section), `scripts/linux-install.py`. Not updated: `contrib/help-pages-translation-to-french/howtoplay.html` (a stale French page about table tiles) and the history in earlier sections of this file, which still say `~/.PySolFC`.
- **Verification:** throwaway homes only, never the real `~/.PySolFC`. Fresh run creates `.pysol` only; an old folder with `options.cfg` and a saved game is moved with both intact and the old folder is gone; with both present the old one is untouched; a failing rename falls back to the old folder (mocked). Unit tests unchanged (19, the one known `--version` error).
- **Things that read the old name:** `PROGRESS-NOTES.md` sections 2 to 52 mention `~/.PySolFC` as the settings folder; read them as `~/.pysol` from now on. Standing rule for launch checks stays: use `HOME=<temp>` only with source runs.

## 57. Update: stuck detection and the "No moves left" dialog removed (2026-11-08)

Commit `e3ecc00e`. Not rebuilt or installed: the installed app still has the dialog. Supersedes the stuck parts of section 32.

- **Asked by the user:** the "No moves left!" dialog came up while moves were still available; disable the feature and remove the dialog.
- **Why it was wrong:** `Game.getStuck` decided "stuck" from a special hint search (`HINT_LEVEL_STUCK`) after every move, so any move the hint search missed, or a position it judged a repeat, produced the dialog. It also ran that search after every move, so removing it saves some time per move (not measured).
- **Removed:** `Game.updateStuck`, `Game.getStuck`, `Stuck_Class` (and its creation in the game start), `Game.stuck`, `failed_snapshots`, the `stuck` status key and the status bar "You are stuck" label (the status bar now has time, moves and info), the calls after a new game, a move, undo and redo, the per-game `getStuck` overrides in `golf.py`, `grandfathersclock.py` and `special/memory.py`, the matching calls in `larasgame.py`, the code in `finishMove` that detected a manual undo (it only fed the stuck check) and the now unused `cmpForUndo` methods in `move.py`.
- **Left in place (dead now):** `HINT_LEVEL_STUCK` and `hint_level_is_stuck` in `hint.py`, `interlock.py` and `spider.py`, and the "stuck" comments in `hanoi.py`, `matrix.py` and `hitormiss.py`. Candidates for the dead-code pass.
- **Behaviour change:** the game no longer tells the player when no moves are left, in any game, and the status bar has no indicator. The win dialog and "game finished" logic are unchanged.
- **Verification:** unit tests unchanged (19, the one known `--version` error); flake8 clean on the touched files; all 169 modules import with `DeprecationWarning` as error; scripted source runs of Klondike, Golf, Grandfather's Clock, Memory 16 and Yukon with a spy on the message dialog: started, played up to 40 legal moves (Golf, Grandfather's Clock and Memory had no simple moves to play), undo and redo, no dialog and no error. A position with no moves left was not reproduced. Nothing was looked at on screen.
- **Still open:** as in section 56 plus the dead stuck-level hint code above.

## 58. Update: Select game by number and Piles description removed (2026-11-08)

Commit `c047752e`. Not rebuilt or installed. Sections 33 and 37 mention these two items.

- **Asked by the user:** remove "Select game by number" and "Piles description" from the Play menu, with the functions underneath.
- **Select game by number:** the menu item and Cmd-M; `mSelectGameById`, `mNewGameWithNextId` and `_mNewGameBySeed` in `actions.py` (the number entry dialog with its "Next number" button); `MfxSimpleEntry` in `tile/tkwidget.py` (only user); the unused `construct_random` and `MfxMessageDialog` imports in `actions.py`. Kept: `Game.getGameNumber` (used for default save file names), `ORIGIN_SELECTED` and the `--deal` / `--gameid` command line options. There is now no way to enter a specific deal number from the menus; the command line still works.
- **Piles description:** the menu item and F2; `mStackDesk` in `ui/tktile/menubar.py`; `Game.showStackDesc`, `Game.deleteStackDesc`, `stackdesc_list` and the two `deleteStackDesc` calls in `game/__init__.py`; the `StackDesc` class in `tile/tkwidget.py`; and every `getBaseCard`, `_getBaseCard` and `varyGetBaseCard` method (`stack.py`, `games/fan.py`, `games/terrace.py`, `games/special/hanafuda_common.py`, the assignment in `customgame.py`), which only existed for that popup. Kept: `getHelp` on stacks (it still feeds the hover text in the status bar).
- **Play menu is now:** Deal cards, Auto drop, Shuffle tiles, Pause, Restart, a divider, Hint, Highlight piles, Find card, Show full picture, a divider, Demo.
- **Verification:** unit tests unchanged (19, the one known `--version` error); flake8 clean on the touched files (two unused imports it flagged were removed); all 169 modules import with `DeprecationWarning` as error; a scripted run printed the new Play menu, found no F2 or Cmd-M binding and called `getHelp` on every stack; Klondike, Terrace, Fan, Spider and Big Easy (Hanafuda, 12356) start, and Klondike and Big Easy played moves with undo and redo, no error and no dialog. Nothing was looked at on screen.
- **Test note:** an app started with `timeout 7` (SIGTERM) once did not die and sat idle for six minutes; it died to `kill -9`. The same game behaves the same on the previous commit. Use `timeout -s KILL` for launch checks.
- **Still open:** as in section 57.

## 59. Update: rebuilt and installed with the settings-folder rename, no stuck dialog, and the two Play items removed (2026-11-08)

Installed app rebuilt from commit `38abd267` (120 MB, arm64, ad-hoc signed, `codesign -v` passes, `--version` prints `PySol 26 version 26.11`). It adds sections 56 to 58 to what section 54 installed: the `~/.pysol` settings folder, no stuck detection or "No moves left" dialog, and no Select game by number or Piles description. The bundle's compiled code contains none of `updateStuck`, `showStackDesc`, `mSelectGameById` or `mStackDesk`. No `data/html N` duplicates appeared this build, and no copy of the app was running.

- **Settings folder:** the user had already launched the previous build, so `~/.PySolFC` has been moved to `~/.pysol` (options, savegames, cardsets, plugins and the old empty `boards` folder came along). `~/.PySolFC` no longer exists. The user said they would delete `~/.pysol/boards` themselves; the app no longer creates it.
- **Not looked at on screen by the assistant:** the Play menu, the missing stuck indicator in the status bar, and the first play of a game on the new build.
- **Local only:** commits after `92fa8520` are not pushed (the folder rename, the stuck removal, the two Play items removal and their handoff notes).
- **Still open:** the logos that say "PySol Fan Club"; the dead code listed in sections 46 and 57 (solver window and hooks, wizard and custom game files and plugin loading, comment field, hint import/export, `auto_scale` branches, stuck hint level); the slow canvas redraw (section 13); Windows and Linux paths never run.

## 60. Deferred on purpose (2026-11-08)

The user parked three items to revisit in about two weeks (around 2026-11-22): the slow canvas redraw (section 13; Python 3.14.9 and Tk 9.0.5 may fix it, a build change), the Windows and Linux code paths (never run since the toolkit removal), and bringing translations back (no translation functions exist now, section 53). Do not start these before then unless the user asks. The user checked the installed app (section 59) and was satisfied. Open and active: the dead-code pass (sections 46 and 57) and a new logo (the logos under `html-src/images` still say "PySol Fan Club").

## 61. Update: dead-code pass (2026-11-08)

Five commits (`c743c4c5`, `2e635559`, `f8b16940`, `0a33adfa`, `845ac123`), 34 files, about 1,460 lines removed (excluding this log). Asked by the user, with the instruction to double check that nothing damages the build. The staged test build was installed afterwards at the user's request (120 MB, arm64, ad-hoc signed, `codesign -v` passes, `--version` prints `PySol 26 version 26.11`; none of the removed modules are in the bundle, no `data/html N` duplicate; no copy of the app was running; the settings folder `~/.pysol` was not touched by the checks).

**Removed, by commit**
1. **Solver window** (`c743c4c5`): `tile/solverdialog.py` and `ui/tktile/solverdialog.py` plus the hooks in `app.py`, `game/__init__.py`, `pysoltk.py` and both menubars. Nothing could create the dialog (`create_solver_dialog` was never called). Kept: the fc-solve hint classes in `hint.py` (`FreeCellSolver_Hint`, `Base_Solver_Hint`, `HINT_LEVEL_SOLVER`), which work when fc-solve is installed.
2. **Layout import code** (`2e635559`): `importFile`, the three `importFileHelper` methods and `PySolHintLayoutImportError` in `hint.py`, `tests/lib/pysol_tests/test_import_file.py` (6 tests) and `tests/unit/data/*` (board files), and the `recursive-include tests/unit/data` line in `MANIFEST.in`. Unit tests are now 13 (one known `--version` error).
3. **Always-true scaling flags** (`f8b16940`): `auto_scale`, `preview_scale` and `preserve_aspect_ratio` (fixed True since section 20) and every branch that tested them in `game/__init__.py`, `stack.py`, `games/mahjongg/mahjongg.py`, `tile/selectgame.py` and `ui/tktile/menubar.py`; `getCenterOffset` lost its always-true parameter. Also the unused `comments.dat` path in `app.py`. **Kept on purpose:** `GameSaveInfo.comment` (it is pickled into saved games; removing it could break loading old saves), and `scale_x`, `scale_y`, `resampling` (still used).
4. **Stuck hint level** (`0a33adfa`): `HINT_LEVEL_STUCK`, `hint_level_is_stuck`, `hint_level_avoids_move_loops` (now `hint_level_is_demo_or_above`), the `DefaultHint.shallMovePile` override and stuck branches in `computeHints`, the Interlock `step010b_getPiles` override, the stuck branch in Spider's `shallMovePile`, and the whole Yukon stuck search (`YukonType_Hint.getHints` and the `_yukon_*` helpers).
5. **Unused helpers** (`845ac123`): the Replay feature (`startReplay`, `replayEvent`, `_showReplayHint`, `_isTalonDealAtomic`, and the demo-loop guard), `undoGotoBookmark` and the extra bookmark slot -1 it needed, `ChecklistDialog` (`tile/checklistdialog.py`), `EditTextDialog` (`tile/edittextdialog.py` and `ui/tktile/edittextdialog.py`), `help_credits`, `HelpStatusbar`, `TkinterScale`, `PysolRadiobutton`, `refreshToolbarImages`, `getGameMenuitemName`, `notYetImplemented`, `resizeBottom`, `Resource.saveSettings`, `getByBasename`, `getGamesIdSortedByShortName`; `docs/README.SOURCE` no longer lists `edittextdialog.py`.

**How each step was checked (all in throwaway homes)**
- After every step: unit tests, flake8 on the whole repo (only the 3 old warnings), all `pysollib` modules import with `DeprecationWarning` as error, a scripted run of the Settings window, help viewer and text lookups, and one launch of a game from each of the 97 game modules (any traceback fails). A baseline run of the same launches was clean before the first edit.
- Scaling change: stack positions, image scale factors and centre offsets were dumped at three window sizes, with Spread stacks on and off, for Klondike and FreeCell on the previous commit and the edited tree: identical. The Select Game preview and the deck dialog were opened and closed without errors.
- Stuck hint change: with a fixed deal for twelve games (Klondike, Yukon, Spider, FreeCell, Golf, Canfield, Interlock, Russian Solitaire, Gypsy, Scorpion, Baker's Game, Seahaven Towers), the hint lists at player, debug and demo level were compared on the previous commit and the edited tree, playing the top hint after each round: identical for every hint printed (my script stops early in some games on a harness assertion, the same way on both trees).
- Replay and bookmarks: set a bookmark, played two moves, went back (correct move index, no leftover slot -1), then ran a demo for a few seconds: no error.
- **Build:** `make rules` then py2app (`--arch arm64`) succeeds with the same 47 "missing module" notices as the earlier build (none from PySol); the bundle holds 171 of the 174 `pysollib` modules. The three not bundled (`customgame`, `wizardutil`, `wizardpresets`, the plugin and custom-game code) are also absent from the app installed in section 59: nothing imports them statically, so py2app skips them. Staged bundle: 118 MB, no `data/html N` duplicate (an iCloud copy `data/html 2` appeared again in the source and the bundle; removed), `codesign -v` passes, `--version` prints `PySol 26 version 26.11`. The installed copy was only started with `--version`: a normal launch reads the real settings folder.

**Looked at and deliberately left**
- `_foofoo` in `game/__init__.py` (the two `attrs` default factories, not dead).
- Plugin and custom-game code (`customgame.py`, `wizardutil.py`, `wizardpresets.py`): the user said to leave plugins for now.
- Game-variant classes the usage scanner called unused (for example `Stewart`, `StrictEiffelTower`, `SimpleSimonII`, `SalicLaw_Talon_2`, the Dashavatara and Mughal stack classes, `GolfType_Hint`, `TowerOfHanoy_Hint`) and the unused stack classes in `stack.py` (`FreeCell_RK_RowStack`, `KingRK_RowStack`, `WeakStackWrapper`): removing game code could change game ids or saved games, and the gain is small.
- HTML parser handlers in `htmllib2.py`, `formatter.py` and `ui/tktile/tkhtml.py` (called by tag name, so a usage scan cannot see them), `Canvas2.py` (used by the canvas), and the `mOpt*` handlers in `ui/tktile/menubar.py` (called by name from the Settings window).
- Small unused methods in `stack.py`, `tile/tkwidget.py`, `images.py`, `layout.py`, `mfxutil.py` and `speech.py`, and the dev helpers in `sudoku_gen.py`: low value, not touched.
- `options.dat` fallback in `app.py` (reads an old pickled options file); old option keys that are ignored on load.
- **Process notes:** one test launched `pkill -9 -x PySol` after the staged `--version` check without first looking for a running copy, which would also have stopped the user's own copy if it was open (it is allowed when replacing the install, but the install did not happen). `timeout` (SIGTERM) can leave an idle app running; use `timeout -s KILL`.
- **Still open:** the "PySol Fan Club" logos; the deferred items in section 60.

## 62. Update: game set cut from 1,390 to 941 (2026-11-09)

Goal stated by the user: get rid of lower quality games. Seven commits after `3b2f3454`; all are pushed to `origin/master` (2026-11-09). Count is the number of registered games in a full import of `pysollib.games`, `.special` and `.mahjongg`.

| Commit | What went | Games after |
|---|---|---|
| `2c7c4d49` | Sudoku (4 levels, generator, rules page, game type) | 1,386 |
| `e6135dfe` | Non-card puzzles: Lights Out, Match Three, Samegame, Pegged, Tower of Hanoi, Tile Puzzle, Matrix, Ishido, Memory; options `match_three_cascade`, `pegged_auto_remove` | 1,300 |
| `04390cfb` | Five special-deck families: Hanafuda, Tarock, Hex A Deck, Dashavatara Ganjifa, Mughal Ganjifa (136 games, incl. the deck variants of Lara's Game); Oriental games menu | 1,164 |
| `10faa864` | Mahjongg solitaire layouts 221 -> 10 | 953 |
| `ce989d60` | Shisen-Sho variants: No Gravity, Not Shisen-Sho, Four Rivers (12 games) | 941 |

- **Rollback tag:** `before-special-decks` (pushed) is `e6135dfe`, the state with the puzzles removed and the special decks still in. `3b2f3454` is the last state with all 1,390 games.
- **Mahjongg kept (10):** Traditional (5034, the Turtle), Pyramid 1 (5250), Butterfly 1 (5013), Castle (5014), Hourglass (5603), Bridge 1 (5203), Cross (5206), Arena 1 (5002), Spider (5415), Altar (5001). They were picked by drawing each layout from its data and by name recognition; nothing was play-tested. The four layout files were merged into `pysollib/games/mahjongg/mahjongg1.py`. Backups if any should be swapped: Five Pyramids 1, Dragon 2, Wedges, Fortress Towers, X-Shape.
- **Shisen-Sho kept (3):** the plain ones, 14x6, 18x8, 24x12 (ids 11001 to 11003). They have gravity (tiles slide down). Assumption: "original" meant the plain-named games; the No Gravity ones were removed. The gravity and adjacency switches and the `NotShisen_Hint` class were folded into the single behavior (`AbstractShisenGame` used `NotShisen_Hint` by default, so `Shisen_Hint` now scores like it did).
- **Wrong turn caught:** `pysollib/games/larasgame.py` registers three French-deck games (Lara's Game, Relaxed, Doubled). It was deleted by mistake with the special-deck files, noticed because the count was 1,161 instead of 1,164, and restored. Lesson: compare the id list against the tag, not just the count.
- **Checks used each time:** all `pysollib` modules import with `DeprecationWarning` as error; unit tests (13, one known `--version` failure); flake8 (only the old unused `math` import in `ui/tktile/menubar.py` and a long line in `scripts/prune_card_backs.py`); source runs of several games with a copy of the real `options.cfg` in a temporary `HOME`. The Shisen-Sho hint class was not exercised beyond launching (a scripted hint check failed on a bug in the check itself).

## 63. Update: cardsets and cardset types removed (2026-11-09)

Commit `b12d15b3`. Only `cardset-standard` (French, 54 cards, seven backs) and `cardset-uni-mahjongg` (42 tiles) remain.

- **Deleted cardsets (local folders under `data/`, not tracked):** Hanafuda, Tarock, Hex, two Ganjifa, Next Matrix, Matching XL, Simple Ishido XL and the eight picture-puzzle sets (3x3 to 10x10). `scripts/prune_card_backs.py` (`KEEP_CARDSETS`), `scripts/cardsets_to_bundle` and `MANIFEST.in` were trimmed to match.
- **Cardset types:** only `TYPE_FRENCH` (1) and `TYPE_MAHJONGG` (4) remain in `CSI` (`pysollib/resource.py`); the type numbers were not renumbered. The puzzle size subtypes, the cardset style names for removed decks, the per-type default cardsets in `options.py`, the "needs 100 cards" check and the matching branches in `app.py` and `gamedb.py` are gone. `GI.NUM_CATEGORIES` is `CSI.TYPE_MAHJONGG`.
- **Show full picture** (menu item, `ui/tktile/fullpicturedialog.py`, hooks in `actions.py`, `app.py`, both menubars, `pysoltk.py`) was removed: only the picture puzzles used it. `Game.canFindCard()` now always returns True.
- **Old option files** keep stale `[cardsets]` keys (types 2, 3, 5 to 12). The loader only reads keys that exist in the defaults, so they are ignored and dropped on the next save.
- **Menus:** the Oriental games menu and tree node are gone; the Special games menu used to test the Oriental list by mistake and now tests its own (Cribbage, Poker, Shisen-Sho).

## 64. Update: help pages after the removals (2026-11-09)

Commit `1e126b32` plus the cardset guide in `b12d15b3`. Deleted `ganjifa.html`, `hanafuda.html`, `hexadeck.html`, the unreferenced `html-src/all.htm` (213 KB of old rules text) and the rules pages of every removed game (exact set from comparing each game's rules file name; 136 for the special decks alone). Glossary entries for removed decks are gone, the intro says "more than 1,100" games (now fewer: update it if the count matters), and `gen-html.py` no longer references removed game types. Six old broken links remain (typos such as `austalianpatience.html`); two links caused by the removals were fixed. Some rules pages are orphaned from before this work (`concentration`, `families`, `glenwood`, wikipedia `agnes` and `treasuretrove`) and were left.

## 65. Update: rebuilt and installed (2026-11-09)

Installed app rebuilt from commit `ce989d60` (101 MB, arm64, ad-hoc signed, `codesign -v` passes, `--version` prints `PySol 26 version 26.11`; bundle holds 914 rules pages, only the two cardsets, and no special-deck, `mahjongg2/3/L` or full-picture modules; no `data/html N` duplicate). No copy of the app was running. Same procedure as sections 14, 16 and 59 (`make rules`, py2app `--arch arm64`, thin to arm64, `ditto --norsrc --noextattr --noqtn` to a scratch folder, ad-hoc sign, install).

- **Not looked at on screen by the assistant:** the cardset dialog, the Special games menu, the Select Game tree, a Mahjongg game and a Shisen-Sho game in the installed app.
- **Left on purpose:** stale ids in `gamedb.py` tables (the Mahjongg compatibility groups, `GAMES_BY_PYSOL_VERSION`, the obsolete-id remap block) do nothing now; saved games and statistics for removed games in `~/.pysol` are orphaned and cannot be loaded; the plugin and custom-game code from section 61.
- **Pushed:** `10faa864`, `ce989d60` and this note were pushed with the rest on 2026-11-09 (see section 67).
- **Still open:** the "PySol Fan Club" logos; the deferred items in section 60 (about 2026-11-22); further quality cuts among the French-deck games were discussed as a possible next step but no rule was chosen.

## 66. Update: flat Mahjongg menu, layout renames, rebuilt and installed (2026-11-09)

Installed app rebuilt from commit `a1147d71` (101 MB, arm64, ad-hoc signed, `codesign -v` passes, `--version` prints `PySol 26 version 26.11`, no `data/html N` duplicate). No copy of the app was running. Same procedure as section 65.

- **Games > Mahjongg games** (commit `1ff9f03e`, `_addSelectMahjonggGameSubMenu` in `ui/tktile/menubar.py`) lists the 10 games directly, sorted by short name, instead of alphabetical range submenus. Read back from a source run: Altar, Arena, Bridge, Butterfly, Castle, Cross, Hourglass, Pyramid, Spider, Traditional. Shisen-Sho is not in this menu; it is under Games > Special games > Shisen-Sho type.
- **Renames** (commit `a1147d71`): Pyramid 1, Butterfly 1, Bridge 1, Arena 1 lost the "1" (now Mahjongg Pyramid, Butterfly, Bridge, Arena). Ids 5250, 5013, 5203, 5002 are unchanged, so saves and statistics still match; recent-games and favorites store ids and show the new names. All 941 game names are unique.
- **Not looked at on screen by the assistant:** the installed app's Games menu, the cardset dialog, a Mahjongg game and a Shisen-Sho game.
- **Pushed:** everything after `b12d15b3` (the Mahjongg cut, the Shisen-Sho cut, the handoff notes, `1ff9f03e`, `a1147d71`) was pushed later; see section 67.
- **Still open:** as in section 65.

## 67. Update: everything pushed (2026-11-09)

`origin/master` now has all the game-cut work, from `3b2f3454` through the Mahjongg cut, the Shisen-Sho cut, the flat Mahjongg menu, the layout renames and the handoff notes. The `before-special-decks` tag (`e6135dfe`) was pushed earlier. The installed app is the build from `a1147d71` (section 66). Earlier notes that call these commits local or unpushed are historical.

## 68. Update: app size breakdown, slimming parked (2026-11-09)

Installed app is 101 MB (`Contents/Resources` 76 MB, `Frameworks` 24 MB). Of `Resources`, `lib` is 64 MB and `data` is 11 MB. History: 229 MB first arm64 build, 182 MB after arm64 thinning, 154 MB before the dead-code pass, 120 MB before the cardset removal, 101 MB now.

`lib` breakdown (measured on the installed bundle):
- `python3.13/` 50 MB: `pygame` 30 MB (docs 6.7, tests 5.6, examples 2.8, hidden `.dylibs` 10 for SDL2 and audio/image codecs, about 5 of native modules and icons); `lib-dynload` 12 MB (PIL native 5.3, sqlite 1.1, unicodedata 0.7, plus `_testcapi` and `_testlimitedcapi`); `setuptools` 6.9; `ctypes` 0.3.
- `python313.zip` 14 MB compressed (37.5 MB unpacked): PIL 4.4, stdlib `test` package 3.1, `pysollib` 1.4, `accessible_output2` 0.8, the rest about 4.

**Parked by the user ("leave it for now").** Candidate trim, about 26 MB (101 MB to about 75 MB), not tried or tested: delete pygame `docs`, `tests`, `examples` (about 15 MB, nothing imports them); drop `setuptools` (about 7 MB; check nothing imports `pkg_resources`); drop the stdlib `test` package (about 3 MB); drop `accessible_output2` (0.8 MB; its VoiceOver backend already fails to load and speech is off); drop `_testcapi` and `_testlimitedcapi` (0.4 MB). Plan was a post-build trim step so a normal build still works, then check the app starts and deals games. Keep pygame `.dylibs` (sound) and PIL (card images).

**State at the end of the session:** the installed app is the build from `a1147d71` (section 66) and matches `origin/master` apart from handoff-only commits; the working tree is clean. This note is the only local commit if it has not been pushed. Next candidates: the size trim above, more quality cuts among the French-deck games (no rule chosen yet), the "PySol Fan Club" logos, and the items deferred to about 2026-11-22 (section 60).

## 69. Update: rebranded as PySol Lite, French category assessed (2026-11-10)

**Rebrand (commit `e607c8ee`, pushed).** The app is now **PySol Lite**, replacing the "PySol 26" name from section 42. `TITLE = 'PySol Lite'` in `pysollib/settings.py` (no year); versions stay YY.MM (26.11). Every user-visible "PySol", "PySolFC" and "PySol FC" in the app strings and help pages (`html-src`, `gen-html.py`) became "PySol Lite"; the About tagline is "A lighter PySol". Also updated: README, CONTRIBUTING, `docs/pysol.6`, `data/pysol.desktop`, `appdata.xml`.

**Kept on purpose:** `PACKAGE = 'PySolFC'` (saved games and data directories), bundle ID `net.sourceforge.pysolfc`, the cardset file header `PySolFC solitaire cardset;...` (the parser reads it), the "Based on PySol, PySol Fan Club edition and PySolFC" credit and copyright lines, author credits, `credits_old.html`, upstream URLs, the FAQ's mentions of old PySolFC versions, NEWS, the CI workflows. `html-src/rules` and `html-src/wikipedia` were not checked or changed.

**Bundle rename (this supersedes the `PySol.app` names in earlier sections).** `BUNDLE` in `setup_osx.py` is now `'PySol Lite'`, so the build produces `dist/PySol Lite.app` with executable `PySol Lite` (py2app names the bundle from `CFBundleName`, and the post-build `install_name_tool` and `codesign` steps use `BUNDLE`, so all three must agree). Installed to `~/Applications/PySol Lite.app`; the old `~/Applications/PySol.app` was deleted and the Dock tile must be re-added by hand. Force-quit names are now `pkill -9 -x "PySol Lite"` (and `-x PySol` for a stale old copy). Check a build with `"PySol Lite.app/Contents/MacOS/PySol Lite" --version` (prints `PySol Lite version 26.11`). Installed app: 101 MB, arm64, ad-hoc signed, built after `make rules` (the Makefile has no `mo` target, so translations were not regenerated).

**French category assessment (read-only, nothing changed).**
- 941 games registered: 928 French-deck, 13 Mahjongg. The French menu holds 915: 690 in the 19 named types plus 225 in the deck-count catch-all groups (One-Deck 110, Two-Deck 109, Three-Deck 4, Four-Deck 2). Each game is in exactly one group. The 13 Poker and Cribbage games are in the Special menu instead.
- 920 distinct game classes; only one class backs more than one ID. No missing rules pages, no duplicate names. 704 games have no redeals.
- The database flags only 21 games as popular and there are no play statistics, so a "top 100 standard games" list was a judgment call (Klondike, Spider, FreeCell, Yukon, Forty Thieves, Canfield and their well-known relatives). It was given in chat and not saved to a file.
- Biggest families: Forty Thieves 82, Spider 72, Klondike 67, Pairing 54, FreeCell 49. About 300 games in the Klondike, Spider, Forty Thieves, Yukon and Gypsy families are small variants of each other, the most likely place for a further quality cut.
- **Correction:** an earlier message said there were "63 three- and four-deck games" in the menu groups. That was the count of games using 3 or 4 decks across all types (41 + 22). The Three-Deck and Four-Deck menu groups hold only 6 games.
- The "Simple games" bucket in `GI.SELECT_GAME_BY_TYPE` is always empty (dead definition).
- No playability test was run; the earlier full-app smoke test hung (section 47) and a per-game run would need one process per game.

**State at the end of the session:** `origin/master` is at `e607c8ee` plus this note; the installed app is the build of that commit. Next candidates: the parked size trim (section 68), further game cuts by family, and deciding on the name of this notes file (it still says "pysolfc").

## 70. Update: five more type cuts, 941 to 808 games; GitHub repo renamed (2026-11-10 to 2026-11-11)

Goal, as in section 62: fewer, better games. For each game type the user was shown the games grouped into families with a suggested keep list, then chose the keepers. Each cut removed the other games' registrations (`registerGame`), the classes and helper stacks only they used, leftover imports and `# * Name` section comments, and their rules pages in `html-src/rules`. Base classes that kept games need stay even when they stop being games.

| Commit | Type | Kept | Removed | Games after |
|---|---|---|---|---|
| `fe19855d` | Spider | Spider, Spider (1 Suit), Spider (2 Suits), Scorpion, Spiderette, Simple Simon, Wasp, Grounds for a Divorce, Daddy Longlegs, Astrocyte, Spidercells, Trillium, Curds and Whey (13) | 59 | 882 |
| `1fefb977` | Beleaguered Castle | Beleaguered Castle, Streets and Alleys, Citadel, Fortress, Bastion, Chessboard, Somerset, Canister (8) | 22 | 860 |
| `e4400758` | Raglan | King Albert, Raglan, Flower Garden, Stonewall, Agnes Bernauer, Jane, Phoenix (7) | 15 | 845 |
| `b3edab24` | Baker's Dozen | Baker's Dozen, Spanish Patience, Castles in Spain, Martha, Cruel, Perseverance, Bisley (7) | 18 | 827 |
| `1eca2094` | Canfield | Canfield, Storehouse, Rainbow, Superior Canfield, Demon, Dutchess, Gate, Minerva (8) | 19 | 808 |

Rollback tags (pushed 2026-11-11): `before-spider-cut`, `before-bc-cut`, `before-raglan-cut`, `before-bakersdozen-cut` (the Canfield cut has none: it sat on the uncommitted Baker's Dozen change when it was made). The earlier pushed tag `before-special-decks` (`e6135dfe`) and the last all-games commit `3b2f3454` (1,390 games) still apply.

**Things that went wrong or need knowing**
- **Module deletion took an unrelated game.** Deleting `capricieuse.py` (all four of its Baker's Dozen-type games) also removed Choice (id 755, a 3-deck game of a different type). Caught because the count was one lower than expected (826, not 827). Restored the file with only Choice in it. Same lesson as section 62: compare the full id list against the previous state, not just the count. `bisley13.py` (Bisley 13 only) was deleted outright and its import removed from `pysollib/games/__init__.py`.
- **Dead-class removal tool.** Classes were removed with a script that deletes a class when nothing references its name outside comments, repeated until nothing changes. It ignores classes that were already unreferenced before the cut. Names that also appear in strings or docstrings elsewhere survive and were removed by hand (Morehead, York, Capricieuse, Fifteen). `SimpleSimonII` (unregistered before this work) was left alone. `Little Gate` (Canfield) was removed but its class stays because Doorway, a different type, builds on it.
- **Dangling help link.** `html-src/rules/demon.html` linked to the deleted Double Canfield page; its description now reads "Like Canfield, but with two decks, eight tableau piles...". The FAQ sentence pointing at Relaxed Spider was removed. The contrib French copy (`contrib/help-pages-translation-to-french`) still lists the removed games; unmaintained, left as is.
- **Hard-kill in launch checks.** Launch checks use `timeout -s KILL 5 .build-venv/bin/python pysol.py --gameid N` with `HOME=<temp dir>`. A plain `timeout` (SIGTERM) once left a Somerset window idle for minutes. Tooling used: `pyflakes` and `pycodestyle` were pip-installed into `.build-venv` (not in the repo); system Python has neither.
- **One commit split.** The Baker's Dozen and Canfield cuts were first committed together by mistake (the unstage did not take); the commit was undone locally before pushing and redone as two.
- **Unit tests:** 12 of 13 pass; the failure is the old `--version` test (`./pysol.py` not found, exit 127) and predates all of this.

**Remaining Select-menu types not yet reviewed:** Fan, Forty Thieves, FreeCell, Golf, Gypsy, Klondike, Montana, Napoleon, Numerica, Pairing, Picture Gallery, Terrace, Yukon, plus the catch-all One-Deck and Two-Deck groups. Each is a family cut like the five above.

**Repo renamed.** The GitHub repo is now `spidermedic/Pysol-Lite` (GitHub's own spelling, with a lowercase y; the user typed it that way). `origin`, `PACKAGE_URL` and the README use `PySol-Lite`, which still works because GitHub ignores case in repo names; changing them to the exact spelling is a pending optional cleanup (a rebuild is needed for the About link). `origin` was changed to `git@github.com:spidermedic/PySol-Lite.git`; `PACKAGE_URL` in `pysollib/settings.py` and the two `git clone`/`cd` lines in README follow it (commit `afb23dc6`). The old address redirects. The local folder is still `~/Documents/Claude/pysol`, left alone on purpose (renaming it would move the Claude project path the saved memory lives under).

**State at the end of the session (2026-11-11):** `origin/master` is at `afb23dc6` plus this note and the commit that records the repo spelling; the installed app (`~/Applications/PySol Lite.app`, 100 MB, arm64, ad-hoc signed, version 26.11) is the build of `afb23dc6`. This file was renamed from `pysolfc-handoff.md`; README and the saved memory notes now point at `PROGRESS-NOTES.md`.
