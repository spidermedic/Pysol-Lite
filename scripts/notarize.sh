#!/bin/bash
# Sign (Developer ID, hardened runtime), notarize and staple "PySol Lite.app".
#
# Usage:  scripts/notarize.sh [path/to/"PySol Lite.app"]
#
# One-time setup: create an app-specific password at appleid.apple.com, then
#   xcrun notarytool store-credentials "$NOTARY_PROFILE" \
#       --apple-id <your Apple ID> --team-id <TEAM ID> --password <app password>
#
# Settings (override from the environment):
#   SIGN_ID         certificate name, as shown by: security find-identity -v -p codesigning
#   NOTARY_PROFILE  notarytool keychain profile name
set -euo pipefail

SIGN_ID="${SIGN_ID:-Developer ID Application: Doug Martin (2DF2S79HA9)}"
NOTARY_PROFILE="${NOTARY_PROFILE:-pysol-notary}"
APP="${1:-dist/PySol Lite.app}"
HERE="$(cd "$(dirname "$0")" && pwd)"
ENT="$HERE/entitlements.plist"
ZIP="$(dirname "$APP")/PySolLite-notarize.zip"

[ -d "$APP" ] || { echo "no such app: $APP" >&2; exit 1; }

echo "== signing nested code (inside-out)"
# Every Mach-O file, deepest first, then the frameworks, then the app itself.
find "$APP" -type f \( -name '*.so' -o -name '*.dylib' -o -perm +111 \) -print0 |
  while IFS= read -r -d '' f; do
    if file -b "$f" | grep -q 'Mach-O'; then
      codesign --force --options runtime --timestamp --sign "$SIGN_ID" "$f"
    fi
  done
find "$APP/Contents/Frameworks" -maxdepth 2 -name '*.framework' -print0 |
  while IFS= read -r -d '' f; do
    codesign --force --options runtime --timestamp --sign "$SIGN_ID" "$f"
  done
codesign --force --options runtime --timestamp --entitlements "$ENT" \
  --sign "$SIGN_ID" "$APP"

echo "== verifying signature"
codesign --verify --deep --strict --verbose=2 "$APP"

echo "== submitting for notarization (waits for Apple)"
rm -f "$ZIP"
ditto -c -k --keepParent "$APP" "$ZIP"
xcrun notarytool submit "$ZIP" --keychain-profile "$NOTARY_PROFILE" --wait
rm -f "$ZIP"

echo "== stapling"
xcrun stapler staple "$APP"
xcrun stapler validate "$APP"
spctl --assess --type execute -vv "$APP"
echo "done: $APP is signed, notarized and stapled"
