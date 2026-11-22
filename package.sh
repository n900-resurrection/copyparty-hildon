#!/bin/bash
# Package copyparty-hildon as a .deb for Maemo 5: make -C apps/copyparty-hildon deb
# Output: /project/build/deb/copyparty-hildon_<VERSION>-<REV>_armel.deb
set -euo pipefail
PROJ=/project
. "$PROJ/scripts/debpack.sh"

PKG=copyparty-hildon
VERSION="${VERSION:-0.1}"
STAGE="$PROJ/build/deb/stage-$PKG"
HERE="$PROJ/apps/copyparty-hildon"

rm -rf "$STAGE"
mkdir -p "$STAGE/opt/$PKG" "$STAGE/usr/bin" "$STAGE/usr/share/applications/hildon" "$STAGE/DEBIAN"
install -m 755 "$HERE/copyparty-hildon" "$STAGE/opt/$PKG/"
install -m 644 "$HERE/copyparty_hildon.py" "$STAGE/opt/$PKG/"
for sz in 48 64; do
    mkdir -p "$STAGE/usr/share/icons/hicolor/${sz}x${sz}/apps"
    install -m 644 "$HERE/icons/$sz.png" "$STAGE/usr/share/icons/hicolor/${sz}x${sz}/apps/$PKG.png"
done
ln -s ../../opt/$PKG/copyparty-hildon "$STAGE/usr/bin/copyparty-hildon"
cat > "$STAGE/usr/share/applications/hildon/$PKG.desktop" <<'EOT'
[Desktop Entry]
Encoding=UTF-8
Version=1.0
Type=Application
Name=File server settings
Icon=copyparty-hildon
Exec=/usr/bin/copyparty-hildon
X-Osso-Type=application/x-executable
EOT

SECTION=user/network
DEPENDS="python3.11, python3-hildonlite (>= 0.5.0), copyparty (>= 1.20.26-1maemo2)"
DISPLAY_NAME="File server settings"
SHORT_DESC="Touch settings and the on/off switch of the copyparty file server"
LONG_DESC="Settings of the file server of the package copyparty: the shared folders (who may read and write), the users and their passwords, the port,
and a switch that starts and stops the server and shows the address to type in the browser of your computer. The settings are the file
~/.copyparty/share.conf, the same one the menu entry File server and the command copyparty-share use; lines that this application does not know
(flags of a folder, other sections) are kept, and a copy of the previous file is saved as share.conf.bak.
Upstream: this project (MIT)."
debpack_build
