#!/bin/sh
python setup.py --command-packages=stdeb.command bdist_deb
sudo dpkg -i deb_dist/python-imagizer_1.0-1*.deb
scp deb_dist/python-imagizer_1.0-1*.deb islay:/home/httpd/html/devel
scp deb_dist/imagizer_1.0-1.dsc islay:/home/httpd/html/devel
scp deb_dist/imagizer_1.0.orig.tar.gz islay:/home/httpd/html/devel
scp deb_dist/imagizer_1.0-1.diff.gz islay:/home/httpd/html/devel
scp deb_dist/imagizer_1.0-1_amd64.changes islay:/home/httpd/html/devel
