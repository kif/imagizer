
DESTDIR=

install:
	install -d $(DESTDIR)/usr/share/imagizer
	install -d $(DESTDIR)/usr/share/doc/imagizer
	install -m 755 generator $(DESTDIR)/usr/bin
	install -m 755 selector $(DESTDIR)/usr/bin
	install -m 644 *.png $(DESTDIR)/usr/share/imagizer
	install -m 644 interface.glade $(DESTDIR)/usr/share/imagizer
	install -m 644 EXIF.py $(DESTDIR)/usr/share/imagizer
	install -m 644 README.txt $(DESTDIR)/usr/share/doc/imagizer
	cp -R doc/* $(DESTDIR)/usr/share/doc/imagizer
	chmod -R a+rX $(DESTDIR)/usr/share/doc/imagizer

uninstall:
	rm -rf $(DESTDIR)/usr/share/imagizer
	rm -rf $(DESTDIR)/usr/share/doc/imagizer
	rm -f $(DESTDIR)/usr/bin/generator
	rm -f $(DESTDIR)/usr/bin/selector
