"""Fictional demo data for the emulator (make hildon-run APP=copyparty-hildon): python3 make_demo.py DIR
Makes DIR/share.conf with two folders and two users, a folder tree to share, a fake ifconfig and a fake copyparty-share."""
import os, sys
d = sys.argv[1]
os.makedirs(d, exist_ok=True)
for sub in ("MyDocs", "MyDocs/DCIM", "MyDocs/.sounds", "MyDocs/Notes"):
    os.makedirs(os.path.join(d, sub), exist_ok=True)
open(os.path.join(d, "share.conf"), "w").write("""[global]
  p: 3923
  no-thumb
  no-robots

[accounts]
  n900: tg4k7w2m9x
  anna: bluebird42

[/]
  %(d)s/MyDocs
  accs:
    rw: n900

[/music]
  %(d)s/MyDocs/.sounds
  accs:
    r: *
    rw: anna

[/photos]
  %(d)s/MyDocs/DCIM
  accs:
    r: anna
""" % {"d": d})
open(os.path.join(d, "ifconfig"), "w").write("""#!/bin/sh
cat <<'EOT'
lo        Link encap:Local Loopback
          inet addr:127.0.0.1  Mask:255.0.0.0
wlan0     Link encap:Ethernet  HWaddr 00:11:22:33:44:55
          inet addr:192.168.1.50  Bcast:192.168.1.255  Mask:255.255.255.0
EOT
""")
# a stand-in for copyparty-share: "start" makes a pid file of a process whose command line has "copyparty", and a listener on the port
open(os.path.join(d, "copyparty-share"), "w").write("""#!/bin/sh
D=%(d)s
case "$1" in
  start) nohup sh -c 'exec env -u PYTHONHOME -u QEMU_LD_PREFIX -u PYTHONPATH python3 -c "import socket,time; s=socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.bind((\\"127.0.0.1\\", 3923)); s.listen(1); time.sleep(3600)" copyparty-fake' >/dev/null 2>&1 &
         echo $! > $D/server.pid; echo started ;;
  stop) [ -f $D/server.pid ] && kill $(cat $D/server.pid) 2>/dev/null; rm -f $D/server.pid; echo Stopped. ;;
  config) echo config ;;
esac
""" % {"d": d})
for f in ("ifconfig", "copyparty-share"):
    os.chmod(os.path.join(d, f), 0o755)
