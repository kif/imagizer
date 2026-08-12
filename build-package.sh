#!/bin/sh
# Build the imagizer wheel and the Debian package, then install it.
#
# The version is read from meson.build (the single source of truth) and stamped
# into the Debian packaging on the fly, so nothing here needs editing when the
# version is bumped.
set -e

export DEB_BUILD_OPTIONS=nocheck

if [ -d /usr/lib/ccache ]; then
    export PATH=/usr/lib/ccache:$PATH
fi

# --- version: single source of truth is meson.build ---------------------------
VERSION=$(sed -n "s/^[[:space:]]*version[[:space:]]*:[[:space:]]*'\([0-9.]*\)'.*/\1/p" meson.build | head -1)
if [ -z "$VERSION" ]; then
    echo "build-package.sh: could not read version from meson.build" >&2
    exit 1
fi
echo "Building imagizer $VERSION"

# --- build the wheel ----------------------------------------------------------
python3 -m build -w

WHEEL=$(ls dist/imagizer-"${VERSION}"-*linux_x86_64.whl 2>/dev/null | head -1)
if [ -z "$WHEEL" ]; then
    echo "build-package.sh: no wheel for $VERSION found in dist/" >&2
    exit 1
fi

# --- the Debian packaging tree (version-agnostic name) ------------------------
PKGDIR="packaging/python3-imagizer"
if [ ! -d "$PKGDIR" ]; then
    echo "build-package.sh: packaging directory $PKGDIR not found" >&2
    exit 1
fi

# --- stamp the version into the version-bearing debian files ------------------
# changelog drives the produced .deb version; install references the wheel's
# versioned dist-info directory.
sed -i "s/\(python3-imagizer (0:\)[0-9.]*\(-1~w2d0)\)/\1${VERSION}\2/; \
        s/\(Release 0:\)[0-9.]*\(-1~w2d0\)/\1${VERSION}\2/" "$PKGDIR/debian/changelog"
sed -i "s#imagizer-[0-9.]*\.dist-info#imagizer-${VERSION}.dist-info#" "$PKGDIR/debian/install"

# --- drop the freshly built wheel content into the packaging tree -------------
rm -rf "$PKGDIR/src"
mkdir -p "$PKGDIR/src"
unzip -q "$WHEEL" -d "$PKGDIR/src"

# --- build and install the .deb -----------------------------------------------
( cd "$PKGDIR" && dpkg-buildpackage -uc -us )
sudo dpkg -i "packaging/python3-imagizer_${VERSION}-1~w2d0_amd64.deb"
