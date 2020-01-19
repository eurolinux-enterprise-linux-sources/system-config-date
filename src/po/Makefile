#
# Makefile for the PO files (translation) catalog
#
# $Id: Makefile,v 1.16 2006/10/17 10:21:13 nphilipp Exp $

TOP	 = ../..

# What is this package?
NLSPACKAGE	= system-config-date
POTFILE		= $(NLSPACKAGE).pot
INSTALL		= /usr/bin/install -c
INSTALL_DATA	= $(INSTALL) -m 644
INSTALL_DIR	= /usr/bin/install -d

# destination directory
INSTALL_NLS_DIR = $(DESTDIR)/usr/share/locale

# commands
DIFF		= /usr/bin/diff
GREP		= /bin/grep
EGREP		= $(GREP) -E

# PO catalog handling
MSGMERGE	= msgmerge -v -N
XGETTEXT	= xgettext --default-domain=$(NLSPACKAGE) \
		  --add-comments		  
MSGFMT		= msgfmt --statistics --verbose

# What do we need to do
POFILES		= $(wildcard *.po)
MOFILES		= $(patsubst %.po,%.mo,$(POFILES))
PYSRC		= $(wildcard ../src/*.py)
GLADESRC	= $(wildcard ../src/*.glade)
CSRC		= ../config/system-config-date.desktop.in.h
SRCFILES	= $(PYSRC) $(GLADESRC) $(CSRC)

all::  update-po $(MOFILES)

po_diff_and_mv_or_rm	= \
	if [ ! -f "$(1)" ] || ($(DIFF) "$(1)" "$(2)" | $(GREP) -v '^. "POT-Creation-Date:' | $(EGREP) -q "^[<>] ([^\#]|\#[^:])"); then \
		echo "Creating/updating $(1)"; \
	    mv -f $(2) $(1); \
	else \
	    rm -f $(2); \
	fi

po_diff_and_mv_or_rm_func = \
	po_diff_and_mv_or_rm () { \
		$(call po_diff_and_mv_or_rm,$$1,$$2) \
	}

$(POTFILE): $(SRCFILES)
	$(XGETTEXT) --omit-header    --keyword --keyword=_ --keyword=N_ --language=python $(PYSRC)
	$(XGETTEXT) --omit-header -j --keyword --keyword=_ --keyword=N_ --language=Glade $(GLADESRC)
	$(XGETTEXT)               -j --keyword --keyword=_ --keyword=N_ --language=C $(CSRC)
	@$(call po_diff_and_mv_or_rm,$(POTFILE),$(NLSPACKAGE).po)

update-po: Makefile $(POTFILE)

refresh-po: Makefile
	@$(po_diff_and_mv_or_rm_func); \
	for cat in $(POFILES); do \
		lang=`basename $$cat .po`; \
		if $(MSGMERGE) $$lang.po $(POTFILE) > $$lang.pot ; then \
			echo "$(MSGMERGE) of $$lang succeeded" ; \
			po_diff_and_mv_or_rm $$lang.po $$lang.pot; \
		else \
			echo "$(MSGMERGE) of $$lang failed" ; \
			rm -f $$lang.pot ; \
		fi; \
	done

clean:
	@rm -fv *mo *~ .depend

install: $(MOFILES)
	@for n in $(MOFILES); do \
	    l=`basename $$n .mo`; \
	    $(INSTALL_DIR) $(INSTALL_NLS_DIR)/$$l/LC_MESSAGES; \
	    $(INSTALL_DATA) --verbose $$n $(INSTALL_NLS_DIR)/$$l/LC_MESSAGES/$(NLSPACKAGE).mo; \
	done

%.mo: %.po
	$(MSGFMT) -o $@ $<

# stub: grab timezone comments from anaconda translations
#       if anaconda translations found it merged with zone.tab strings to
#       produce only timezone translations. 
	@lang=`basename $< .po` ; \
	msgunfmt /usr/share/locale/$$lang/LC_MESSAGES/anaconda.mo -o anaconda_$$lang.po ;\
	included_timezone_po="" ;\
	if [ -f "anaconda_$$lang.po" ]; then \
	  included_timezone_po="$$lang.timezone.po" ;\
	  cat /usr/share/zoneinfo/zone.tab | cut -f4 | grep "^[a-zA-Z]" | sort -u |\
	  while read line; do echo -e "\n#. generated from zone.tab\nmsgid \"$$line\"\nmsgstr \"\""; done |\
	  msgmerge anaconda_$$lang.po - > $$included_timezone_po ;\
	fi; \
	\
	if [ -f "timezones/$<" ]; then \
		msgcat --use-first $< timezones/$< $$included_timezone_po ; \
	else \
		msgcat --use-first $< $$included_timezone_po; \
	fi | msgfmt --check -o $@ - ; \
	\
	if [ -f "$$included_timezone_po" ] ; then rm -f $$included_timezone_po; fi; \
	if [ -f "anaconda_$$lang.po"     ] ; then rm -f anaconda_$$lang.po;     fi;

.PHONY: missing depend

