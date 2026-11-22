# Name: File server settings (copyparty-hildon)
# Sourced by scripts/hildon-run.sh (INSIDE the Workshop) for: make hildon-run APP=copyparty-hildon. Fictional demo folders and users in a scratch directory;
# the server is a stand-in that only opens the port.
RUN_SCRIPT=/project/apps/copyparty-hildon/copyparty-hildon
export COPYPARTY_HILDON_DIR=/tmp/copyparty-hildon-demo HOME=/tmp/copyparty-hildon-demo-home
export COPYPARTY_HILDON_SHARE=$COPYPARTY_HILDON_DIR/copyparty-share COPYPARTY_HILDON_IFCONFIG=$COPYPARTY_HILDON_DIR/ifconfig
rm -rf "$COPYPARTY_HILDON_DIR" "$HOME"; mkdir -p "$HOME"
python3 /project/apps/copyparty-hildon/tests/make_demo.py "$COPYPARTY_HILDON_DIR"
