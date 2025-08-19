include_jpeg_dirs='jpeg/62'

#message(jpeg_dep)
message(include_jpeg_dirs)
py.extension_module('pyexiftran',
        'pyexiftran.pyx', 'exiftran.c', 'filter.c', 'op.c', 'read-bmp.c', 'readers.c', 'read-jpeg.c',
        include_jpeg_dirs+'/transupp.c', 'jpegtools.c', 'genthumbnail.c',
        dependencies : [py_dep, exif_dep, jpeg_dep],
        include_directories : [include_jpeg_dirs],
        install: true,
        subdir: 'imagizer',
        )
