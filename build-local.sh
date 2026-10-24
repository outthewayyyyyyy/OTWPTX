#!/bin/sh
# Build OTW PTX for this Mac, ad-hoc sign it and install it to /Applications.
set -e
cd "$(dirname "$0")"
[ -d .venv ] || { python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt; }
.venv/bin/pyinstaller --noconfirm --windowed --onedir --name "OTW PTX" --collect-all tkinterdnd2 \
  --osx-bundle-identifier com.otw.ptx app.py
APP="dist/OTW PTX.app"
plutil -insert CFBundleDocumentTypes -json \
  '[{"CFBundleTypeName":"Pro Tools Session","CFBundleTypeRole":"Viewer","CFBundleTypeExtensions":["ptx"]}]' \
  "$APP/Contents/Info.plist"
codesign --force --deep --sign - "$APP"
rm -rf "/Applications/OTW PTX.app"
cp -R "$APP" /Applications/
echo "Installed /Applications/OTW PTX.app"
