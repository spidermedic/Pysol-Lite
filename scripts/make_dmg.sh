#!/bin/bash
# Package the notarized "PySol Lite.app" into a signed, notarized, stapled dmg.
#
# Usage:  scripts/make_dmg.sh [path/to/"PySol Lite.app"]
# Run scripts/notarize.sh on the app first. Settings (SIGN_ID, NOTARY_PROFILE)
# are the same as in notarize.sh.
set -euo pipefail

SIGN_ID="${SIGN_ID:-Developer ID Application: Doug Martin (2DF2S79HA9)}"
NOTARY_PROFILE="${NOTARY_PROFILE:-pysol-notary}"
APP="${1:-dist/PySol Lite.app}"
VERSION="$(/usr/libexec/PlistBuddy -c 'Print CFBundleShortVersionString' "$APP/Contents/Info.plist")"
DMG="$(dirname "$APP")/PySol-Lite-$VERSION.dmg"

xcrun stapler validate "$APP" >/dev/null ||
  { echo "app is not notarized and stapled; run scripts/notarize.sh first" >&2; exit 1; }

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
ditto --norsrc --noextattr --noqtn "$APP" "$STAGE/PySol Lite.app"
ln -s /Applications "$STAGE/Applications"

rm -f "$DMG"
hdiutil create -volname "PySol Lite $VERSION" -srcfolder "$STAGE" -ov -format UDZO "$DMG"
codesign --force --timestamp --sign "$SIGN_ID" "$DMG"
xcrun notarytool submit "$DMG" --keychain-profile "$NOTARY_PROFILE" --wait
xcrun stapler staple "$DMG"
xcrun stapler validate "$DMG"
spctl --assess --type open --context context:primary-signature -vv "$DMG"
echo "done: $DMG"
