# copyparty-hildon: settings of the file server of the N900 (folders, users, port, on/off), Python 3 + hildonlite. Targets and conventions: ../../mk/app.mk
override APP     := copyparty-hildon
VERSION ?= 0.1
REV     ?= 1maemo1
DEPS    := hildonlite
RUN_CMD := /usr/bin/copyparty-hildon
ICON_OUT := icons/64.png
include ../../mk/app.mk
