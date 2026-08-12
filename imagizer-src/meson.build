subdir('app')

# Generate _version.py from the project version (single source of truth:
# the `version:` field of the top-level meson.build). __date__ reflects the
# last modification date of meson.build (git commit date, with a filesystem
# mtime fallback), computed at configure time; meson re-runs this whenever
# meson.build changes.
version_date = run_command(py,
  files('_get_date.py'),
  meson.project_source_root() / 'meson.build',
  check: true).stdout().strip()

version_py = configure_file(
  input: '_version.py.in',
  output: '_version.py',
  configuration: {'VERSION': meson.project_version(), 'DATE': version_date},
)
py.install_sources(version_py,
  pure: false,
  subdir: 'imagizer',
)

py.install_sources([
'blur.py',
'config.py',
'curator.py',
'dialogs.py',
'dirchooser.py',
'encoding.py',
'exif_gexiv2.py',
'exif.py',
'exif_py3exiv2.py',
'exif_pyexiv2.py',
'exiftran.py',
'fileutils.py',
'fix_comment.py',
'gtk.py',
'html.py',
'imagecache.py',
'imagemagick.py',
'imagizer.py',
'__init__.py',
'interface.py',
'myqt.py',
'parser.py',
'photo.py',
'pygtkmplayer.py',
'_pyqt6.py',
'pyside_dynamic.py',
'_qt.py',
'qt.py',
'search_day.py',
'search.py',
'selection.py',
'sqlitedict.py',
'template.py',
'tree.py',
'utils.py',
'video_gui.py',
'video.py',
'winpath.py',
],
  pure: false,    # Will be installed next to binaries
  subdir: 'imagizer'  # Folder relative to site-packages to install to
)

