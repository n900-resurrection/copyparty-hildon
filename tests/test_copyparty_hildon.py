"""Tests of the data side of copyparty-hildon: python3 -I tests/test_copyparty_hildon.py (no phone, no GUI)."""
import os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
tmp = tempfile.mkdtemp()
os.environ["COPYPARTY_HILDON_DIR"] = os.path.join(tmp, "cfg")
import copyparty_hildon as C

SAMPLE = """# Settings of the file server (copyparty-share). Edit it.
[global]
  p: 4000
  no-thumb
  no-robots
  hist: /home/user/.copyparty/hist

[accounts]
  n900: abcd1234ef
  guest: secret99

# Folder shared at the address of the server
[/]
  /home/user/MyDocs
  accs:
    rwmd: n900
    r: guest

[/music]
  /home/user/MyDocs/.sounds
  accs:
    r: *
  flags:
    nodupe
    e2d

[groups]
  family: n900, guest
"""


class ParseDump(unittest.TestCase):
    def test_parse(self):
        c = C.parse(SAMPLE)
        self.assertEqual(c.port, 4000)
        self.assertEqual(c.global_extra, ["no-thumb", "no-robots", "hist: /home/user/.copyparty/hist"])
        self.assertEqual(c.accounts, [["n900", "abcd1234ef"], ["guest", "secret99"]])
        self.assertEqual([v.name for v in c.volumes], ["/", "/music"])
        root, music = c.volumes
        self.assertEqual(root.path, "/home/user/MyDocs")
        self.assertEqual(root.access, {"n900": "rwmd", "guest": "r"})
        self.assertEqual(root.level("n900"), "rw")
        self.assertEqual(root.level("guest"), "r")
        self.assertEqual(root.level("nobody"), "")
        self.assertEqual(music.access, {"*": "r"})
        self.assertEqual([x.strip() for x in music.extra], ["flags:", "nodupe", "e2d"])
        self.assertEqual(c.other, [("groups", ["  family: n900, guest"])])

    def test_roundtrip_is_stable(self):
        once = C.dump(C.parse(SAMPLE))
        self.assertEqual(C.dump(C.parse(once)), once)
        c = C.parse(once)
        self.assertEqual(c.port, 4000)
        self.assertEqual(c.volume("/music").extra and [x.strip() for x in c.volume("/music").extra], ["flags:", "nodupe", "e2d"])
        self.assertIn("[groups]", once)
        self.assertIn("    rwmd: n900", once)          # the letters of the file are kept

    def test_unchanged_level_keeps_letters(self):
        c = C.parse(SAMPLE)
        c.volumes[0].set_level("n900", "rw")
        self.assertEqual(c.volumes[0].access["n900"], "rwmd")
        c.volumes[0].set_level("n900", "r")
        self.assertEqual(c.volumes[0].access["n900"], "r")
        c.volumes[0].set_level("n900", "")
        self.assertNotIn("n900", c.volumes[0].access)

    def test_groups_by_permission(self):
        v = C.Volume("/", "/x", {"a": "rw", "b": "rw", "*": "r"})
        c = C.Config(); c.volumes = [v]
        d = C.dump(c)
        self.assertIn("    r: *\n    rw: a, b\n", d)

    def test_empty_and_defaults(self):
        c = C.parse("")
        self.assertEqual((c.port, c.accounts, c.volumes), (C.DEFAULT_PORT, [], []))
        d = C.load(os.path.join(tmp, "nonexistent.conf"))
        self.assertEqual(d.volumes[0].name, "/")
        self.assertEqual(len(d.accounts[0][1]), 10)
        self.assertEqual(d.volumes[0].level("n900"), "rw")
        self.assertEqual(C.parse(C.dump(d)).accounts, d.accounts)

    def test_save_load_backup_private(self):
        p = os.path.join(tmp, "cfg", "share.conf")
        c = C.parse(SAMPLE)
        C.save(c, p)
        self.assertEqual(oct(os.stat(p).st_mode & 0o777), "0o600")
        self.assertFalse(os.path.exists(p + ".bak"))
        c.port = 4001
        C.save(c, p)
        self.assertEqual(C.load(p).port, 4001)
        self.assertEqual(C.parse(open(p + ".bak").read()).port, 4000)        # the previous file
        self.assertEqual(oct(os.stat(p + ".bak").st_mode & 0o777), "0o600")


class Checks(unittest.TestCase):
    def setUp(self):
        self.c = C.parse(SAMPLE)

    def test_user(self):
        self.assertEqual(C.check_user(self.c, "anna"), "anna")
        for bad in ("", "a b", "x" * 33, "a:b", "ž"):
            with self.assertRaises(C.Error):
                C.check_user(self.c, bad)
        with self.assertRaises(C.Error):
            C.check_user(self.c, "guest")
        self.assertEqual(C.check_user(self.c, "guest", old="guest"), "guest")      # renaming to itself is fine

    def test_password(self):
        self.assertEqual(C.check_password("abcd"), "abcd")
        for bad in ("abc", "a b c d", "ab#cd", "ab:cd", "x" * 65, ""):
            with self.assertRaises(C.Error):
                C.check_password(bad)
        for _ in range(20):
            C.check_password(C.random_password())
        self.assertEqual(len(C.random_password(14)), 14)
        self.assertNotEqual(C.random_password(), C.random_password())

    def test_port(self):
        self.assertEqual(C.check_port("3923"), 3923)
        for bad in ("80", "70000", "abc", "", "1023"):
            with self.assertRaises(C.Error):
                C.check_port(bad)

    def test_volume(self):
        d = os.path.join(tmp, "share-me"); os.makedirs(d, exist_ok=True)
        self.assertEqual(C.check_volume(self.c, "pics", d), ("/pics", d))
        self.assertEqual(C.check_volume(self.c, "/pics/", d + "/"), ("/pics", d))
        for bad_name in ("a b", "a/b", "č"):
            with self.assertRaises(C.Error):
                C.check_volume(self.c, bad_name, d)
        with self.assertRaises(C.Error):
            C.check_volume(self.c, "music", d)                  # exists
        self.assertEqual(C.check_volume(self.c, "music", d, old="/music")[0], "/music")
        with self.assertRaises(C.Error):
            C.check_volume(self.c, "x", os.path.join(tmp, "missing"))
        with self.assertRaises(C.Error):
            C.check_volume(self.c, "x", "relative/path")
        with self.assertRaises(C.Error):
            C.check_volume(self.c, "", d)                       # "/" exists
        self.assertEqual(C.check_volume(C.Config(), "", d)[0], "/")

    def test_rename_remove_user(self):
        C.rename_user(self.c, "guest", "visitor")
        self.assertEqual(self.c.users(), ["n900", "visitor"])
        self.assertEqual(self.c.volumes[0].access["visitor"], "r")
        self.assertNotIn("guest", self.c.volumes[0].access)
        C.remove_user(self.c, "n900")
        self.assertEqual(self.c.users(), ["visitor"])
        self.assertNotIn("n900", self.c.volumes[0].access)

    def test_summary(self):
        self.assertEqual(C.summary(self.c, self.c.volumes[0]), "read+write: n900; read: guest")
        self.assertEqual(C.summary(self.c, self.c.volumes[1]), "read: everybody")
        self.assertEqual(C.summary(self.c, C.Volume("/e", "/e")), "nobody")


IFCONFIG = """lo        Link encap:Local Loopback
          inet addr:127.0.0.1  Mask:255.0.0.0
phonet0   Link encap:UNSPEC  HWaddr 15-00
wlan0     Link encap:Ethernet  HWaddr 80:50:1B:4C:D5:CF
          inet addr:192.168.1.50  Bcast:192.168.1.255  Mask:255.255.255.0
usb0      Link encap:Ethernet  HWaddr 02:00:00:00:00:01
          inet addr:192.168.2.15  Bcast:192.168.2.255  Mask:255.255.255.0
"""


class Network(unittest.TestCase):
    def test_parse_ifconfig(self):
        self.assertEqual(C.parse_ifconfig(IFCONFIG), [("wlan0", "192.168.1.50"), ("usb0", "192.168.2.15")])
        self.assertEqual(C.parse_ifconfig("lo Link encap:Local Loopback\n inet addr:127.0.0.1 Mask:255.0.0.0"), [])
        self.assertEqual(C.parse_ifconfig(""), [])

    def test_addresses(self):
        fake = os.path.join(tmp, "ifconfig"); open(fake, "w").write("#!/bin/sh\ncat <<'E'\n" + IFCONFIG + "E\n"); os.chmod(fake, 0o755)
        C.IFCONFIG = fake
        self.assertEqual(C.addresses(3923), ["http://192.168.1.50:3923/", "http://192.168.2.15:3923/"])
        C.IFCONFIG = "/nonexistent/ifconfig"
        self.assertEqual(C.addresses(3923), [])


class Server(unittest.TestCase):
    def test_pid_file(self):
        os.makedirs(C.DIR, exist_ok=True)
        self.assertIsNone(C.server_pid())                                  # no file
        import subprocess
        other = subprocess.Popen(["sleep", "30"])
        try:
            open(C.PIDFILE, "w").write(str(other.pid))
            self.assertIsNone(C.server_pid())                              # a live process that is not copyparty
            fake = os.path.join(tmp, "copyparty-fake"); open(fake, "w").write("#!/bin/sh\nsleep 30\n"); os.chmod(fake, 0o755)
            srv = subprocess.Popen(["sh", fake])                           # its command line contains "copyparty"
            try:
                open(C.PIDFILE, "w").write(str(srv.pid))
                self.assertEqual(C.server_pid(), srv.pid)
            finally:
                srv.kill(); srv.wait()
        finally:
            other.kill(); other.wait()
        open(C.PIDFILE, "w").write("garbage")
        self.assertIsNone(C.server_pid())
        open(C.PIDFILE, "w").write("999999")
        self.assertIsNone(C.server_pid())                                  # no such process

    def test_share_command(self):
        fake = os.path.join(tmp, "fake-share"); open(fake, "w").write("#!/bin/sh\necho \"called $*\"\n"); os.chmod(fake, 0o755)
        C.SHARE = fake
        self.assertEqual(C.start(), "called start")
        self.assertEqual(C.stop(), "called stop")
        C.SHARE = "/nonexistent/share"
        with self.assertRaises(C.Error):
            C.start()

    def test_port_open(self):
        import socket
        s = socket.socket(); s.bind(("127.0.0.1", 0)); s.listen(1)
        self.assertTrue(C.port_open(s.getsockname()[1]))
        s.close()
        self.assertFalse(C.port_open(1))


if __name__ == "__main__":
    unittest.main(verbosity=1)
