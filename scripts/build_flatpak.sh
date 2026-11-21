#!/bin/bash
# Build the Linux Flatpak: dist/PySol-Lite-<version>-x86_64.flatpak
# Prerequisites (Ubuntu): apt install flatpak flatpak-builder, the Flathub
# remote, and the runtime: flatpak install flathub org.freedesktop.Platform//25.08
# org.freedesktop.Sdk//25.08. Needs network (pip downloads the wheels).
set -euo pipefail
cd "$(dirname "$0")/.."
APP=io.github.spidermedic.PySolLite
PY=${PY:-python3}
export PYTHONPATH="$PWD"

# help pages (data/html is generated and git-ignored; needs the attr module)
if [ ! -d data/html ]; then
    (cd html-src && $PY gen-html.py)
    cp -r html-src/images html-src/html/images
    mv html-src/html data/html
fi

VERSION=$($PY -c "from pysollib.settings import VERSION; print(VERSION)")
flatpak-builder --force-clean --user --disable-rofiles-fuse \
    --repo=build/flatpak-repo build/flatpak-build \
    scripts/flatpak/$APP.yml
mkdir -p dist
flatpak build-bundle build/flatpak-repo \
    "dist/PySol-Lite-$VERSION-x86_64.flatpak" $APP
echo "Built dist/PySol-Lite-$VERSION-x86_64.flatpak"
echo "Install: flatpak install --user dist/PySol-Lite-$VERSION-x86_64.flatpak"
