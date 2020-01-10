# License: GPL v2 or later
# Copyright Red Hat Inc.  2001 - 2009
# Copyright Brent Fox <bfox@redhat.com> 2001, 2002

PKGNAME=system-config-date

SCM_REMOTEREPO_RE = ^ssh://(.*@)?git.fedorahosted.org/git/$(PKGNAME).git$
UPLOAD_URL = ssh://fedorahosted.org/$(PKGNAME)

SUBDIRS=man po

PREFIX=/usr

BINDIR=${PREFIX}/bin
SBINDIR=${PREFIX}/sbin
MANDIR=${DATADIR}/man
DATADIR=${PREFIX}/share
SYSCONFDIR=/etc

PKGDATADIR=${DATADIR}/${PKGNAME}

PAMD_DIR        = ${SYSCONFDIR}/pam.d
SECURITY_DIR    = ${SYSCONFDIR}/security/console.apps

PY_SRC_DIR              = src
PY_SRC_APPS             = date_gui.py scdMainWindow.py system-config-date.py timezone_gui.py timezone_map_gui.py
_PY_SRC_APPS            = $(patsubst %,$(PY_SRC_DIR)/%,$(PY_SRC_APPS))
PY_SRC_MODULES          = scdate
_PY_SRC_MODULE_FILES    = $(shell find $(patsubst %,$(PY_SRC_DIR)/%,$(PY_SRC_MODULES)) -type f -a -name "*.py")
PY_SOURCES              = $(_PY_SRC_APPS) $(_PY_SRC_MODULE_FILES)

all:    $(PKGNAME).desktop $(PKGNAME).console src/ntp.conf.template py-build

include rpmspec_rules.mk
include py_rules.mk
include console_rules.mk
include git_rules.mk
include upload_rules.mk

po/$(PKGNAME).pot:: subdirs

subdirs:	$(PKGNAME).desktop.in.h
	for d in $(SUBDIRS); do make -C $$d; [ $$? = 0 ] || exit 1; done

%.desktop.in.h: %.desktop.in
	intltool-extract --type=gettext/ini $<

%.desktop: %.desktop.in po/$(PKGNAME).pot po/*.po
	intltool-merge -u -d po/ $< $@

src/ntp.conf.template:	src/ntp.conf.template.in
	if [ -z "$(POOL_NTP_ORG_VENDOR)" ]; then \
		fgrep -v '@DEFAULT_NTP_SERVERS@' < $< > $@ ; \
	else \
		awk '{ if ($$0 ~ "@DEFAULT_NTP_SERVERS@") { \
			for (i=0; i<=2; i++) { print "server " i ".$(POOL_NTP_ORG_VENDOR).pool.ntp.org"; } \
			} else { print; } }' < $< > $@ ; \
	fi

install: all py-install
	mkdir -p $(DESTDIR)$(BINDIR)
	mkdir -p $(DESTDIR)$(PKGDATADIR)
	mkdir -p $(DESTDIR)$(PAMD_DIR)
	mkdir -p $(DESTDIR)$(SECURITY_DIR)
	mkdir -p $(DESTDIR)$(PKGDATADIR)/pixmaps
	mkdir -p $(DESTDIR)$(DATADIR)/applications
	mkdir -p $(DESTDIR)$(DATADIR)/icons/hicolor/

	install -m 0644 $(_PY_SRC_APPS) $(DESTDIR)$(PKGDATADIR)
	chmod 0755 $(DESTDIR)$(PKGDATADIR)/system-config-date.py
	install -m 0644 src/ntp.conf.template $(DESTDIR)$(PKGDATADIR)
	install -m 0644 src/${PKGNAME}.glade $(DESTDIR)$(PKGDATADIR)
	install -m 0644 ${PKGNAME}.pam $(DESTDIR)$(PAMD_DIR)/${PKGNAME}
	install -m 0644 ${PKGNAME}.console $(DESTDIR)$(SECURITY_DIR)/${PKGNAME}
	install -m 0644 pixmaps/map*.png $(DESTDIR)$(PKGDATADIR)/pixmaps
	for src in pixmaps/icons/*/apps/system-config-date.png; do \
		dst="$(DESTDIR)$(DATADIR)/icons/hicolor/$${src#pixmaps/icons/}"; \
		dir="$${dst%/system-config-date.png}"; \
		install -m 0755 -d "$$dir" && install -m 0644 "$$src" "$$dst"; \
	done
	install -m 0755 -d $(DESTDIR)$(DATADIR)/icons/hicolor/scalable/apps
	install -m 0644 pixmaps/icons/scalable/apps/system-config-date.svg $(DESTDIR)$(DATADIR)/icons/hicolor/scalable/apps/system-config-date.svg
	install -m 0644 ${PKGNAME}.desktop $(DESTDIR)$(DATADIR)/applications/${PKGNAME}.desktop
	ln -sf consolehelper $(DESTDIR)$(BINDIR)/${PKGNAME}
	for d in $(SUBDIRS); do \
	(cd $$d; $(MAKE) DESTDIR=$(DESTDIR) MANDIR=$(MANDIR) install) \
		|| case "$(MFLAGS)" in *k*) fail=yes;; *) exit 1;; esac; \
	done && test -z "$$fail"

clean: console-clean py-clean
	rm -fv $(PKGNAME).desktop
	rm -fv *~
	rm -fv *.pyc
	rm -fv src/ntp.conf.template
