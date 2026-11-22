# copyparty-hildon

Touch settings of the file server of the N900 ([copyparty](https://github.com/9001/copyparty), package `copyparty`). Python 3 + [hildonlite](../hildonlite).

- **Start / Stop** the server with one button; the address to type in the browser of the computer and the user are shown under it.
- **Shared folders:** add a folder of the phone under an address (`/`, `/music`, ...), say who may read or read and write (everybody without a login, or a user).
- **Users and passwords:** add, rename, remove, a random password with one tap.
- **Port.**

A change is saved at once and a running server is restarted. The settings are `~/.copyparty/share.conf`, the same file the menu entry *File server*
and the command `copyparty-share` use. The application keeps lines it does not know (flags of a folder, other sections of copyparty) and saves a copy of the
previous file as `share.conf.bak`; comments of the file are not kept.

## Development
```bash
make hildon-run APP=copyparty-hildon VNC=1     # in the emulator, demo data (fictional users and folders), the server is a stand-in
python3 -I tests/test_copyparty_hildon.py      # the data side, no phone needed
make -C apps/copyparty-hildon deb install test
```
`copyparty_hildon.py` is the data side (parse and write the configuration, checks, addresses, the server through `copyparty-share`), `copyparty-hildon` the windows.
