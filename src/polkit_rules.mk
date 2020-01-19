# License: GPL v2 or later
# Copyright Red Hat Inc. 2009, 2012

ifdef PO_RULES_INCLUDED
$(error po_rules.mk must be included after $(lastword $(MAKEFILE_LIST)))
endif

ifndef PKGNAME
$(error PKGNAME must be set before including $(lastword $(MAKEFILE_LIST)))
endif

ifndef PO_INTLTOOLEXTRACT
PO_INTLTOOLEXTRACT = intltool-extract
endif

ifndef PO_INTLTOOLMERGE
PO_INTLTOOLMERGE = intltool-merge
endif

ifndef POLKIT_POLICY_DIR
POLKIT_POLICY_DIR	= $(DATADIR)/polkit-1/actions
endif

ifndef POLKIT_INSTALL
POLKIT_INSTALL		= $(if $(INSTALL),$(INSTALL),install --verbose)
endif

ifndef POLKIT_INSTALL_D
POLKIT_INSTALL_D	= $(POLKIT_INSTALL) -D
endif

ifndef PKEXEC
PKEXEC = $(BINDIR)/pkexec
endif

ifdef PKEXEC_SCRIPT
ifndef PKEXEC_SCRIPT_IN
$(error PKEXEC_SCRIPT_IN must be set)
endif
ifndef PKEXEC_SCRIPT_DEST
$(error PKEXEC_SCRIPT_DEST must be set)
endif
PKEXEC_SCRIPT_SRC = $(patsubst %.in,%,$(PKEXEC_SCRIPT_IN))

$(PKEXEC_SCRIPT_SRC): $(PKEXEC_SCRIPT_IN)
	sed -e 's|@PKEXEC@|$(PKEXEC)|g; s|@PKEXEC_SCRIPT_DEST@|$(PKEXEC_SCRIPT_DEST)|g' < $< > $@

$(DESTDIR)/$(PKEXEC_SCRIPT): $(PKEXEC_SCRIPT_SRC)
	@$(POLKIT_INSTALL_D) -m 0755 "$(PKEXEC_SCRIPT_SRC)" "$(DESTDIR)/$(PKEXEC_SCRIPT)"

pkexec-all: $(PKEXEC_SCRIPT_SRC)
pkexec-install: $(DESTDIR)/$(PKEXEC_SCRIPT)
pkexec-clean:
	@rm -fv "$(PKEXEC_SCRIPT_SRC)"
else
pkexec-all:
pkexec-install:
pkexec-clean:
endif

POLKITIN_FILES		= $(patsubst %,%.in,$(POLKIT_FILES))
POLKITINH_FILES		= $(patsubst %.in,%.in.h,$(POLKITIN_FILES))

%.policy.in.h: %.policy.in
	$(PO_INTLTOOLEXTRACT) -t gettext/xml $<

%.policy:	%.policy.in po-update-pot po/*.po
	$(PO_INTLTOOLMERGE) -u -x po/ $< $@

polkit-all: $(POLKIT_FILES) pkexec-all

polkit-install: $(POLKIT_FILES) pkexec-install
	@$(foreach file,$(POLKIT_FILES),$(POLKIT_INSTALL_D) -m 0644 "$(file)" "$(DESTDIR)$(POLKIT_POLICY_DIR)/$(notdir $(file))"; )

polkit-clean: pkexec-clean
	@rm -fv $(POLKITINH_FILES) $(POLKIT_FILES)
