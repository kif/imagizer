
DESTDIR=/usr

install:
	install -d $(DESTDIR)/share/imagizer
	install -d $(DESTDIR)/share/doc/imagizer
	install -m 755 generator $(DESTDIR)/bin
	install -m 755 selector $(DESTDIR)/bin
	install -m 644 *.png $(DESTDIR)/share/imagizer
	install -m 644 selector.glade $(DESTDIR)/share/imagizer
	install -m 644 EXIF.py $(DESTDIR)/share/imagizer
	install -m 644 imagizer.py $(DESTDIR)/share/imagizer
	install -m 644 signals.py $(DESTDIR)/share/imagizer
	install -m 644 README.txt $(DESTDIR)/share/doc/imagizer
	install -m 644 favicon.ico $(DESTDIR)/share/imagizer
	install -m 644 imagizer.conf /etc
	install -m 755 bin/exiftran $(DESTDIR)/share/imagizer
	cp -R doc/* $(DESTDIR)/share/doc/imagizer
	chmod -R a+rX $(DESTDIR)/share/doc/imagizer

uninstall:
	rm -rf $(DESTDIR)/share/imagizer
	rm -rf $(DESTDIR)/share/doc/imagizer
	rm -f $(DESTDIR)/bin/generator
	rm -f $(DESTDIR)/bin/selector
