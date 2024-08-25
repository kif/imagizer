project('imagizer',
  'c', 'cython', 'cpp',
  license: 'MIT',
  meson_version: '>= 0.60',
  version: '8.0.0'
)


# Seek the backend
if meson.backend() != 'ninja'
  error('Ninja backend required')
endif

cc = meson.get_compiler('c')
cpp = meson.get_compiler('cpp')
cy = meson.get_compiler('cython')
m_dep = cc.find_library('m', required : false)
if m_dep.found()
  add_project_link_arguments('-lm', language : 'c')
endif

# https://mesonbuild.com/Python-module.html
py_mod = import('python')
py = py_mod.find_installation()
py_dep = py.dependency()
boost_dep = dependency('boost', modules : ['python3'])
exiv2_dep = dependency('exiv2')
exif_dep = dependency('libexif')
jpeg_dep = dependency('libjpeg')
subdir('imagizer-src')
subdir('src')
subdir('py3exiv2/src')
subdir('pyexiftran')
subdir('gui')
subdir('pixmaps')


