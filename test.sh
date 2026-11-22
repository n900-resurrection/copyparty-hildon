TEST_NAME=copyparty-hildon
need_pkg copyparty-hildon
ok binary test -x /opt/copyparty-hildon/copyparty-hildon
ok launcher test -x /usr/bin/copyparty-hildon
ok desktop-entry grep -q "Exec=/usr/bin/copyparty-hildon" /usr/share/applications/hildon/copyparty-hildon.desktop
ok icons test -f /usr/share/icons/hicolor/48x48/apps/copyparty-hildon.png -a -f /usr/share/icons/hicolor/64x64/apps/copyparty-hildon.png
ok imports-as-user sh -c 'su user -c "cd /opt/copyparty-hildon && python3 -c \"import copyparty_hildon\""'
# the data side against the real configuration of the phone (read only)
ok reads-the-real-config sh -c 'su user -c "copyparty-share config" >/dev/null; su user -c "cd /opt/copyparty-hildon && python3 -c \"import copyparty_hildon as C; c = C.load(); assert c.accounts and c.volumes and c.port\""'
ok roundtrip-of-the-real-config sh -c 'su user -c "cd /opt/copyparty-hildon && python3 -c \"import copyparty_hildon as C; c = C.load(); d = C.parse(C.dump(c)); assert (d.port, d.accounts, [(v.name, v.path, v.access) for v in d.volumes]) == (c.port, c.accounts, [(v.name, v.path, v.access) for v in c.volumes])\""'
ok addresses sh -c 'su user -c "cd /opt/copyparty-hildon && python3 -c \"import copyparty_hildon as C; print(C.addresses(3923))\"" | grep -q "http://"'
ok server-state-agrees-with-copyparty-share sh -c 'copyparty-share stop >/dev/null 2>&1; su user -c "cd /opt/copyparty-hildon && python3 -c \"import copyparty_hildon as C; assert C.server_pid() is None\""'
# the window opens and closes by itself (a few seconds), as the user inside the Hildon session
ok window-opens sh -c 'su user -c "DISPLAY=:0 COPYPARTY_HILDON_TIMEOUT=4 copyparty-hildon"; [ $? = 0 ]'
summary
