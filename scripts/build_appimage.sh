#!/bin/bash
# Build the Linux AppImage: dist/PySol-Lite-<version>-x86_64.AppImage
# Run on Linux (best on the oldest distro you want to support, e.g.
# Ubuntu 22.04, so the glibc is old enough for newer systems).
# Prerequisites: apt install python3 python3-venv python3-tk wget file
# and a .venv with: attrs configobj pillow pygame-ce pysol-cards markdown
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD"
PY=.venv/bin/python

# help pages (data/html is generated and git-ignored)
if [ ! -d data/html ]; then
    (cd html-src && ../$PY gen-html.py)
    cp -r html-src/images html-src/html/images
    mv html-src/html data/html
fi

$PY -m pip install -q pyinstaller
$PY -m PyInstaller --noconfirm --clean pysol.spec

VERSION=$($PY -c "from pysollib.settings import VERSION; print(VERSION)")
APPDIR=build/AppDir
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/lib" "$APPDIR/usr/share/applications" \
         "$APPDIR/usr/share/icons/hicolor/512x512/apps"
cp -a "dist/PySol Lite" "$APPDIR/usr/lib/pysol-lite"

cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/lib/pysol-lite/PySol Lite" "$@"
EOF
chmod +x "$APPDIR/AppRun"

cat > "$APPDIR/pysol-lite.desktop" <<'EOF'
[Desktop Entry]
Name=PySol Lite
Comment=276 solitaire card games
Exec=AppRun
Terminal=false
Type=Application
Categories=Game;CardGame;
Keywords=solitaire;patience;cards;pysol;klondike;
Icon=pysol-lite
EOF
cp "$APPDIR/pysol-lite.desktop" "$APPDIR/usr/share/applications/"
cp data/images/icons/512x512/*.png "$APPDIR/pysol-lite.png"
cp data/images/icons/512x512/*.png "$APPDIR/usr/share/icons/hicolor/512x512/apps/pysol-lite.png"

# appimagetool is pinned to a release and verified by SHA256 before it runs
TOOL_VERSION=1.9.1
TOOL_SHA256=ed4ce84f0d9caff66f50bcca6ff6f35aae54ce8135408b3fa33abfc3cb384eb0
TOOL=build/appimagetool-$TOOL_VERSION-x86_64.AppImage
if [ ! -f "$TOOL" ]; then
    wget -q -O "$TOOL"       "https://github.com/AppImage/appimagetool/releases/download/$TOOL_VERSION/appimagetool-x86_64.AppImage"
fi
echo "$TOOL_SHA256  $TOOL" | sha256sum -c -
chmod +x "$TOOL"
# --appimage-extract-and-run: works where FUSE is missing (WSL, containers)
ARCH=x86_64 "$TOOL" --appimage-extract-and-run "$APPDIR" \
    "dist/PySol-Lite-$VERSION-x86_64.AppImage"
echo "Built dist/PySol-Lite-$VERSION-x86_64.AppImage"
