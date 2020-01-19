ifndef TZ_PO_RULES_INCLUDED
TZ_PO_RULES_INCLUDED=1

TZMAKEFILE = po/timezones/Makefile
TZPODIR = $(dir $(TZMAKEFILE))
_TZMK = $(notdir $(TZMAKEFILE))

TZMAKE = $(MAKE) -C $(TZPODIR) -f $(_TZMK) $(1) $(2) $(3)

TZAUTOTARGETS = all clean install update-pot update-po refresh-po force-utf8 \
				report

$(patsubst %,tz-po-%,$(TZAUTOTARGETS)):
	@$(call TZMAKE,$(subst tz-po-,,$@))

endif
