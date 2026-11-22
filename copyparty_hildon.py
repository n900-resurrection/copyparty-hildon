"""copyparty-hildon: the data side (no GUI) of the settings application of the file server of the N900.

It reads and writes ~/.copyparty/share.conf, the configuration that `copyparty-share` (package copyparty) gives to copyparty, controls the
server with that same command, and finds the addresses of the phone. Pure Python 3, no dependencies, so it is tested without a phone.

The file has the format of copyparty ([global], [accounts], one [/name] section per shared folder); what this module does not understand
(flags of a folder, other sections, other options) is kept and written back unchanged. Comments of the file are not kept (a copy of the
previous file is saved as share.conf.bak before every save)."""
import os, re, secrets, socket, subprocess

HOME = os.path.expanduser("~")
DIR = os.environ.get("COPYPARTY_HILDON_DIR", os.path.join(HOME, ".copyparty"))
CONF = os.path.join(DIR, "share.conf")
PIDFILE = os.path.join(DIR, "server.pid")
SHARE = os.environ.get("COPYPARTY_HILDON_SHARE", "copyparty-share")      # the command that controls the server
IFCONFIG = os.environ.get("COPYPARTY_HILDON_IFCONFIG", "ifconfig")
DEFAULT_PORT = 3923
HEADER = ("# Settings of the file server (copyparty-share), written by the settings application (copyparty-hildon).\n"
          "# Format: https://github.com/9001/copyparty#accounts-and-volumes\n")
PW_ALPHABET = "abcdefghijkmnopqrstuvwxyz23456789"        # no l, 1, 0, o-like characters that are easy to mix up


class Error(ValueError):
    """A value the user typed is not usable; the text says why (shown in the application)."""


class Volume:
    """One shared folder: its address in the browser (name, "/" or "/music"), the real folder, who may do what, and the lines we do not understand."""

    def __init__(self, name="/", path="", access=None, extra=None):
        self.name = name
        self.path = path
        self.access = dict(access or {})          # user name ("*" = everybody) -> permission letters, e.g. "r", "rw", "rwmd"
        self.extra = list(extra or [])            # raw lines (flags: ...) kept as they were

    def level(self, user):
        """What a user may do here: "" (nothing), "r" (read), "rw" (read and write)."""
        p = self.access.get(user, "")
        if "w" in p or "a" in p:
            return "rw"
        return "r" if "r" in p or "g" in p or "G" in p else ""

    def set_level(self, user, level):
        if level == self.level(user):
            return                                # unchanged: keep the letters the file had (rwmd, ...)
        if level:
            self.access[user] = level
        else:
            self.access.pop(user, None)


class Config:
    def __init__(self):
        self.port = DEFAULT_PORT
        self.global_extra = []                    # raw lines of [global] other than the port
        self.accounts = []                        # [[name, password], ...]
        self.volumes = []                         # [Volume, ...]
        self.other = []                           # [(header, [raw lines])] sections we do not edit ([groups], ...)

    def users(self):
        return [n for n, _p in self.accounts]

    def password(self, name):
        for n, p in self.accounts:
            if n == name:
                return p
        return None

    def volume(self, name):
        for v in self.volumes:
            if v.name == name:
                return v
        return None


def indent_of(line):
    return len(line) - len(line.lstrip(" \t"))


def parse(text):
    """Parse the text of share.conf into a Config."""
    cfg = Config()
    sections = []                                 # [(header, [lines])]
    for line in text.splitlines():
        m = re.match(r"^\[(.+)\]\s*$", line)
        if m:
            sections.append((m.group(1).strip(), []))
        elif sections:
            sections[-1][1].append(line.rstrip())
    for header, lines in sections:
        body = [ln for ln in lines if ln.strip() and not ln.strip().startswith("#")]
        if header == "global":
            for ln in body:
                m = re.match(r"^\s*p\s*:\s*(\d+)\s*$", ln)
                if m:
                    cfg.port = int(m.group(1))
                else:
                    cfg.global_extra.append(ln.strip())
        elif header == "accounts":
            for ln in body:
                name, sep, pw = ln.strip().partition(":")
                if sep:
                    cfg.accounts.append([name.strip(), pw.strip()])
        elif header.startswith("/"):
            cfg.volumes.append(parse_volume(header, body))
        else:
            cfg.other.append((header, [ln for ln in lines]))
    return cfg


def parse_volume(name, body):
    v = Volume(name)
    i = 0
    base = indent_of(body[0]) if body else 0
    while i < len(body):
        ln = body[i]
        s = ln.strip()
        ind = indent_of(ln)
        block = []
        j = i + 1
        while j < len(body) and indent_of(body[j]) > ind:
            block.append(body[j]); j += 1
        if ind == base and s == "accs:":
            for b in block:
                perm, _sep, users = b.strip().partition(":")
                for u in users.split(","):
                    if u.strip():
                        v.access[u.strip()] = perm.strip()
        elif not v.path and ind == base and not s.endswith(":"):
            v.path = s
        else:
            v.extra.append(ln)
            v.extra.extend(block)
        i = j
    return v


def group_access(access):
    """{"a": "rw", "b": "rw", "*": "r"} -> [("r", ["*"]), ("rw", ["a", "b"])] in the order of the permissions."""
    by = {}
    for u, p in access.items():
        by.setdefault(p, []).append(u)
    return sorted(by.items())


def dump(cfg):
    """The text of share.conf for a Config (parse(dump(c)) gives the same Config)."""
    out = [HEADER, "[global]", "  p: %d" % cfg.port]
    out += ["  " + ln for ln in cfg.global_extra]
    out += ["", "[accounts]"] + ["  %s: %s" % (n, p) for n, p in cfg.accounts]
    for v in cfg.volumes:
        out += ["", "[%s]" % v.name, "  " + v.path]
        if v.access:
            out.append("  accs:")
            out += ["    %s: %s" % (perm, ", ".join(users)) for perm, users in group_access(v.access)]
        out += [ln if ln.startswith(" ") else "  " + ln for ln in v.extra]
    for header, lines in cfg.other:
        out += ["", "[%s]" % header] + lines
    return "\n".join(out) + "\n"


def load(path=None):
    """The Config of the file, or a new default one when there is no file (copyparty-share config makes the real default)."""
    try:
        with open(path or CONF, encoding="utf-8") as f:
            return parse(f.read())
    except FileNotFoundError:
        return default_config()


def save(cfg, path=None):
    path = path or CONF
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        with open(path, "rb") as f:
            old = f.read()
        with open(path + ".bak", "wb") as f:
            f.write(old)
        os.chmod(path + ".bak", 0o600)
    except FileNotFoundError:
        pass
    tmp = path + ".new"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(dump(cfg))
    os.chmod(tmp, 0o600)                           # passwords are in it
    os.replace(tmp, path)


def default_config():
    cfg = Config()
    cfg.global_extra = ["no-thumb", "no-robots"]
    cfg.accounts = [["n900", random_password()]]
    cfg.volumes = [Volume("/", os.path.join(HOME, "MyDocs"), {"n900": "rw"})]
    return cfg


# ---- values typed by the user ----

def random_password(n=10):
    return "".join(secrets.choice(PW_ALPHABET) for _ in range(n))


def check_user(cfg, name, old=None):
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,32}", name):
        raise Error("A user name has 1 to 32 letters, digits, dots, dashes or underscores.")
    if name != old and name in cfg.users():
        raise Error("There is a user %s already." % name)
    return name


def check_password(pw):
    if not re.fullmatch(r"[^\s#:]{4,64}", pw):
        raise Error("A password has 4 to 64 characters, without spaces, # and colons.")
    return pw


def check_port(text):
    try:
        port = int(text)
    except ValueError:
        raise Error("The port is a number, 1024 to 65535.")
    if not 1024 <= port <= 65535:
        raise Error("The port is a number, 1024 to 65535.")
    return port


def check_volume(cfg, name, path, old=None):
    """Check the address and the folder of a shared folder; the address is made to start with a slash."""
    name = "/" + name.strip().strip("/")
    if not re.fullmatch(r"/[A-Za-z0-9_.-]*", name):
        raise Error("The address is letters, digits, dots and dashes, e.g. /music (or / for the top).")
    if name != old and cfg.volume(name):
        raise Error("There is a shared folder %s already." % name)
    path = os.path.expanduser(path.strip())
    if not os.path.isabs(path):
        raise Error("The folder is a full path, e.g. %s." % os.path.join(HOME, "MyDocs"))
    if not os.path.isdir(path):
        raise Error("There is no folder %s." % path)
    return name, os.path.normpath(path)


def rename_user(cfg, old, new):
    for acc in cfg.accounts:
        if acc[0] == old:
            acc[0] = new
    for v in cfg.volumes:
        if old in v.access:
            v.access = {(new if u == old else u): p for u, p in v.access.items()}


def remove_user(cfg, name):
    cfg.accounts = [a for a in cfg.accounts if a[0] != name]
    for v in cfg.volumes:
        v.access.pop(name, None)


LEVELS = {"": "No access", "r": "Read", "rw": "Read and write"}


def summary(cfg, v):
    """One line for the list: who may do what in the folder v."""
    parts = []
    for level, word in (("rw", "read+write"), ("r", "read")):
        who = [("everybody" if u == "*" else u) for u in list(v.access) if v.level(u) == level]
        if who:
            parts.append("%s: %s" % (word, ", ".join(who)))
    return "; ".join(parts) or "nobody"


def common_folders():
    """(label, path) of the folders of the phone worth offering, only those that exist."""
    docs = os.path.join(HOME, "MyDocs")
    cands = [("MyDocs (all your files)", docs), ("Camera pictures", docs + "/DCIM"), ("Pictures", docs + "/.images"),
             ("Music and sounds", docs + "/.sounds"), ("Videos", docs + "/.videos"), ("Documents", docs + "/.documents"),
             ("Home folder", HOME)]
    return [(label, p) for label, p in cands if os.path.isdir(p)]


# ---- the network ----

def parse_ifconfig(text):
    """(interface, address) pairs from the output of ifconfig (busybox style), without the loopback."""
    found, iface = [], None
    for line in text.splitlines():
        m = re.match(r"^(\S+)\s+Link encap", line)
        if m:
            iface = m.group(1)
        m = re.search(r"inet addr:(\d+\.\d+\.\d+\.\d+)", line)
        if m and iface and not m.group(1).startswith("127."):
            found.append((iface, m.group(1)))
    return found


def addresses(port):
    """The URLs to type in the browser of the computer, one per network connection that has an address."""
    try:
        text = subprocess.run([IFCONFIG], capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    return ["http://%s:%d/" % (ip, port) for _i, ip in parse_ifconfig(text)]


# ---- the server (it is controlled by copyparty-share, so the menu entry File server and this application agree) ----

def server_pid():
    """The pid of the running server, or None; the pid file counts only when that process is copyparty."""
    try:
        with open(PIDFILE) as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)
        with open("/proc/%d/cmdline" % pid, "rb") as f:
            return pid if b"copyparty" in f.read() else None
    except (OSError, ValueError):
        return None


def port_open(port):
    try:
        socket.create_connection(("127.0.0.1", port), 0.5).close()
        return True
    except OSError:
        return False


def share(*args):
    """Run copyparty-share with arguments; returns its text. Raises Error when the command is missing."""
    try:
        r = subprocess.run([SHARE, *args], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as e:
        raise Error("copyparty-share did not run: %s" % e)
    return (r.stdout + r.stderr).strip()


def start():
    return share("start")


def stop():
    return share("stop")
