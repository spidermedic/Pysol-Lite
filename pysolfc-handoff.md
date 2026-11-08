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
