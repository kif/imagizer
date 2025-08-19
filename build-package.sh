#!/bin/sh
#m -rf deb_dist/imagizer-*
export DEB_BUILD_OPTIONS=nocheck

if [ -d /usr/lib/ccache ];
then
   export PATH=/usr/lib/ccache:$PATH
fi

python3 -m build -w
rm -rf packaging/python3-imagizer_8.0.0-1~w2d0_amd64/src/*
unzip dist/imagizer-*linux_x86_64.whl -d packaging/python3-imagizer_8.0.0-1~w2d0_amd64/src
cd packaging
cd python3-imagizer*_amd64
dpkg-buildpackage -uc -us
cd ..
sudo dpkg -i python3-imagizer_*.deb
cd ..
