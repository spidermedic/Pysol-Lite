# Android feasibility spike (throwaway)

A self-contained Kivy Klondike table that does not use `pysollib`. It only
tests whether Kivy on a real Android tablet draws cards sharply and follows
a finger. Tested 2026-11-22 on a Samsung Galaxy Tab A11 (SM-X133, 8-inch,
800x1340) at about 73 fps. See `PROGRESS-NOTES.md` section 133.

Build and install (macOS, Apple Silicon):

1. `brew install openjdk@17 autoconf automake libtool pkg-config cmake openssl@3`
   and `brew install --cask android-platform-tools`.
2. `python3.14 -m venv .android-venv` in the repo root (kept out of git), set
   `include-system-site-packages = true` in its `pyvenv.cfg` (Buildozer runs
   `pip install --user`), then `pip install buildozer cython certifi`.
3. `python prepare.py` (writes `cards/*.png` from the bundled Standard cardset).
4. Delete `.buildozer/android/platform/build-arm64-v8a/build/venv` before every
   build (a reused one has a broken pip), then run, from this folder:
   `SSL_CERT_FILE=<certifi cacert.pem> JAVA_HOME=/opt/homebrew/opt/openjdk@17
   PATH=<.android-venv/bin>:$JAVA_HOME/bin:$PATH buildozer -v android debug`.
5. `adb install -r bin/pysolspike-0.1-arm64-v8a-debug.apk`
   (USB debugging on, the tablet authorized; if `adb` crashes on start, run
   `adb kill-server` and `adb start-server`).

`buildozer.spec` writes `charset_normalizer` with an underscore on purpose:
python-for-android otherwise picks an Android-only wheel that pip on the Mac
refuses to install.
