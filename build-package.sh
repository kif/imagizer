#!/bin/sh
python setup.py --command-packages=stdeb.command bdist_deb
sudo dpkg -i deb_dist/python-imagizer_1.*.deb
scp deb_dist/python-imagizer_1.*.deb jerome@islay:/home/httpd/html/devel
scp deb_dist/imagizer_1.*-1.dsc jerome@islay:/home/httpd/html/devel
scp deb_dist/imagizer_1.*.orig.tar.gz jerome@islay:/home/httpd/html/devel
scp deb_dist/imagizer_1.*-1.diff.gz jerome@islay:/home/httpd/html/devel
scp deb_dist/imagizer_1.*-1_amd64.changes jerome@islay:/home/httpd/html/devel
