subdir('pyexiv2')

py.extension_module('libexiv2python',
        'exiv2wrapper_python.cpp', 'exiv2wrapper.cpp', 'exiv2wrapper.hpp',
         dependencies : [py_dep, boost_dep, exiv2_dep],
#        include_directories : ['include'],
        install: true,
        subdir: 'imagizer/pyexiv2',
        )

