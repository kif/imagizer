# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Imagizer is a toolbox for managing a repository of JPEG photos: sorting by date/camera, renaming, lossless rotation, commenting, selecting, archiving, and publishing static HTML galleries. It ships two main programs:

- **selector** — the PyQt6 GUI (workstation) for browsing, rotating, titling and selecting images.
- **generator** — a CLI (no GUI, runs on a web server) that builds static HTML pages from a repository. Historically derived from Martin Blais' `curator`.

Design principle threaded through the code: **never recompress image pixels**. Rotations are lossless (JPEG block rearrangement via the `pyexiftran` C extension); only metadata (EXIF/JPEG tags) and filenames are modified.

## Build & run

The build backend is **meson-python** (`pyproject.toml` → `meson.build`), not setuptools. There is no `setup.py`. Building compiles Cython (`.pyx`) and C extensions that link system libraries: `libjpeg`, `libexif`, `exiv2`, and `boost::python3`. These dev packages must be present.

Run from a source checkout **without installing** using `bootstrap.py`, which invokes `meson setup/install` into `build/` and patches `sys.path`:

```sh
./bootstrap.py selector          # launch the GUI
./bootstrap.py generator --help  # run the CLI generator
./bootstrap.py                   # drops into IPython with imagizer importable
```

`bootstrap.py` resolves the argument first as a file path, then as an entry point from `pyproject.toml` (`selector`, `generator`, `Gen_HTML`). Rerun after editing `.pyx`/C sources to recompile.

Build a wheel and a Debian package (Debian/Ubuntu):

```sh
python3 -m build -w      # wheel only
./build-package.sh       # wheel + .deb, then dpkg -i (uses sudo)
```

## Tests

Unit tests for the imagizer package live in the `imagizer/test/` submodule (source: `imagizer-src/test/`). They are self-contained — each loads the module under test by file path with minimal stubs, so they need neither a configured `~/.imagizer` nor a Qt/graphical environment, and run straight from a source checkout:

```sh
python3 -m unittest discover -s imagizer-src/test -p 'test_*.py'   # from source
python3 -m imagizer.test                                           # once installed
```

The vendored `py3exiv2/` subproject has its own separate tests:

```sh
cd py3exiv2 && python test/TestsRunner.py
```

## Architecture

The importable Python package is named `imagizer` but its source lives in **`imagizer-src/`** (mapped to `subdir: 'imagizer'` at install time by `imagizer-src/meson.build`). Executable entry points live in `imagizer-src/app/` (`selector.py`, `generator.py`, `video_page.py`, plus standalone utilities).

Compiled extensions come from three subprojects, each with its own `meson.build`, all installed into the `imagizer` package:

- **`src/`** — Cython: `down_sampler` (fast image downscaling) and `_tree` (directory tree walking).
- **`pyexiftran/`** — C + Cython (`pyexiftran.pyx`) wrapping jpegtran-style lossless JPEG transforms; links `libjpeg`/`libexif`. This is what makes rotation lossless.
- **`py3exiv2/`** — a **vendored** copy of the py3exiv2 library (EXIF/IPTC/XMP read-write via `exiv2` + boost::python). Treat it as a third-party dependency, not core imagizer code.

Core modules and cross-cutting patterns worth knowing before editing:

- **`photo.py`** — the central `Photo` class; nearly all per-image operations (rotation, resize, EXIF read/write, comment/title handling, trash) route through here. Uses PIL/pillow for pixels and `pyexiftran` for lossless ops.
- **`config.py`** — the `config` object is a **Borg** (shared-state singleton): every `Config()` instance shares the same attributes. Reads `/etc/imagizer.conf` and `~/.imagizer` (POSIX) or the equivalent `imagizer.conf` files on Windows. Sample configs are the top-level `imagizer.conf-*` files.
- **Qt abstraction** — GUI code imports from `qt.py`, which loads **PyQt6** through `_qt.py` (a silx-style binding shim). Import Qt symbols from `imagizer.qt`, not directly from `PyQt6`. `.ui` files live in `gui/` and are loaded at runtime via `buildUI`/`loadUi`.
- **EXIF backend abstraction** — code imports `from .exif import Exif`; `exif.py` re-exports one backend. Alternatives exist (`exif_py3exiv2.py` — current default, `exif_gexiv2.py`, `exif_pyexiv2.py`). Change the backend in `exif.py`.
- **`interface.py`** — the large selector GUI controller (main window logic, keyboard shortcuts, batch actions).
- **`imagecache.py`** — `ImageCache`/`image_cache`/`title_cache` provide in-memory caches of decoded images and titles, populated during the selector splash screen.

A directory is treated as an imagizer repository only if it contains a **`.selected`** file; selector warns before operating on directories that lack it, to avoid scattering renamed files across a disk.

## Conventions & gotchas

- Much of the code, comments, and docs are in **French** (e.g. `LISEZ-MOI.txt`, `nomme_video.py`). Docstrings mix French and English.
- The tree carries legacy Python-2 compatibility shims (`from __future__ import ...`, `try/except` around `configparser`/PIL imports). New code targets Python 3 (`requires-python >=3.7`), but keep additions tolerant of the existing style.
- `*.orig` files (e.g. `photo.py.orig`, `interface.py.orig`) are stale merge artifacts — ignore them; edit the non-`.orig` file.
- Generated artifacts checked into the tree (`*.c`/`*.html` next to `.pyx`, `build/`, `dist/`, `deb_dist/`, many `*.tar.gz`/`*.deb`/`*.whl`) are not source — edit the `.pyx`/`.py` originals.
- The version has a single source of truth: `version:` in `meson.build`. At build time meson generates `imagizer/_version.py` from `imagizer-src/_version.py.in`, and `imagizer-src/__init__.py` imports `__version__` (and `__date__`) from it. `__date__` is computed from the modification date of `meson.build` at configure time. Bump the version in `meson.build` only.
- License is mixed: `pyproject.toml` declares MIT, but most imagizer source files carry a GPL header.
