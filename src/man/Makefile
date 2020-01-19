
MANDIR=/usr/share/man

all:

install:
	mkdir -p $(DESTDIR)$(MANDIR)/man8
	install -m 644 en/system-config-date.8 $(DESTDIR)$(MANDIR)/man8
	mkdir -p $(DESTDIR)$(MANDIR)/fr/man8
	install -m 644 fr/system-config-date.8 $(DESTDIR)$(MANDIR)/fr/man8
	mkdir -p $(DESTDIR)$(MANDIR)/ja/man8
	install -m 644 ja/system-config-date.8 $(DESTDIR)$(MANDIR)/ja/man8

clean:
