ifndef CONSOLE_USE_CONFIG_UTIL
CONSOLE_SEDSCRIPT		= s,@CONSOLE_PERMISSIONS_DIRECTIVE@,USER=root,g
else
CONSOLE_SEDSCRIPT		= s,@CONSOLE_PERMISSIONS_DIRECTIVE@,. config-util,g
endif

%.console:	%.console.in
	sed -e "$(CONSOLE_SEDSCRIPT)" < $< > $@

console-clean:
	rm -f $(PKGNAME).console
