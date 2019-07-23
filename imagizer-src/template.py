#!/usr/bin/python
# -*- coding: UTF8 -*-

__author__ = "Jérôme Kieffer"
__date__ = "2019-07-21"
__license__ = "GPL"

import sys
import os
import shutil
import logging
import re
from traceback import print_exception
from contextlib import contextmanager
from collections import namedtuple
PieceOfCode = namedtuple("PieceOfCode", "preamble compiled source")
logger = logging.getLogger(__name__)
from .config    import Config
config = Config()

#===============================================================================
# DEFAULT TEMPLATES
#===============================================================================

# Important Note: you can always save these with --save-templates and then edit
# them, and they will be used, without modifying this script. You can also put
# new common code in template-rc.py and use it from your templates.

html_preamble = \
"""<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0 Transitional//EN\">
<html>
<head>
   <meta http-equiv=\"Content-Type\" content=\"text/html\"; charset=\"""" + config.Coding + """\" >
   <link rel=stylesheet type=\"text/css\" href=\"<!--tag:rel(css_fn, cd)-->\">
   <title>%s</title>
</head>
<body>
<a name='begin'>
"""

html_postamble = """
<!--tagcode:
if 'footer' in globals():
    print(footer)
-->
<a name='end'>
</body>
</html>
"""

default_templates = {}


default_templates[ 'template-css' ] = """


BODY {
    background-color: #444444;
    font-family: Arial,Geneva,sans-serif;
    color: lightgray;
}

A:link { text-decoration: none;
         color: #FFFFFF;
     }
A:visited { text-decoration: none;
    color: #FFFFFF;
}

.arrownav { width: 100%; border: none; margin: 0; padding: 0; }
.arrow { font-weight: bold; text-decoration: none; }

.image { border: solid 7px black; }

.thumb {
       border-width: 3px;
       border-style: ridge;
       border-color: #AAAAAA;
}


.desctable { width: 100%; border: none; margin: 0; padding: 0; }

.titlecell { vertical-align: top; }
.title { font-size: 24px; }

.location { font-weight: bold; }

.description { font-family: Arial,Geneva,sans-serif;
    text-align: center;
 }

HR.sephr { background-color: black; height: 1px; width: 90%; }

.navtable { width: 100%; border: none }

.settingscell {
    width: 1%;
    vertical-align: top;
    text-align: right;
    white-space: nowrap;
}
.settingstitle {
    font-size: x-small;
    font-weight: bold;
}
.settings {
    font-size: x-small;
}

.tracksind { font-weight: bold; }

.toptable { width: 100%; background-color: black; }

.dirtop { background-color: black; }
.globaltop { background-color: black; }
.tracktop { background-color: black; }
.sortedtop { background-color: black; }

.toptitle { font-size: x-large; }
.topsubtitle { font-weight: bold; }

.mininav { text-align: right; font-size: smaller; }

"""

default_templates[ 'template-image' ] = \
(html_preamble % 'Image: <!--tag:unicode2html(image._title)-->') + \
"""

<!-- quick navigator at the top -->
<table class="arrownav">
<tr><td width=50% align="left">
<!--tagcode:
pi = prev(image, allimages)
if pi:
    print('<a class="arrow" href="%s">&lt;&lt;&lt;</a>'%rel(pi._pagefn, cd))
-->

</td><td width="50%" align="right">
<!--tagcode:
ni = next(image, allimages)
if ni:
    print('<a class="arrow" href="%s">&gt;&gt;&gt;</a>'%rel(ni._pagefn, cd))
-->
</td></tr></table>

<center>
<!--tagcode:

if image._pagefn:

    if image._size:
        (w,h)=image._size
        use_map = 1
        # smart image map
        w4 = w / 4
        ht = h / 10

        print('<map name="navmap">')
        s = 0
        e = w
        pi = prev(image, allimages)
        if pi:
            print '<area shape=rect coords="%d,%d,%d,%d" href="%s">' %                   (0, 0, w4, h, rel(pi._pagefn, cd))
            s = w4

        ni = next(image, allimages)
        if ni:
            print '<area shape=rect coords="%d,%d,%d,%d" href="%s">' %                   (3*w4, 0, w, h, rel(ni._pagefn, cd))
            e = 3*w4

        print '<area shape=rect coords="%d,%d,%d,%d" href="%s">' %               (s, 0, e, ht, rel(image._dir._pagefn, cd))

        print '</map>'

    else:
        use_map = 0
    use_map = 0
    xtra = 'class="image"'
    if use_map:
        xtra += '  usemap="#%s"' % 'navmap'
    print(scaledImage(cd, image, xtra))
-->
</center>

<p>

<!--description and camera settings, in a table-->
<!--tagcode:
if image._attr:
    description = image._attr.get('description')
    settings = image._attr.get('settings')
    if not settings:
        settings = image._attr.get('info')

    print('<table class="desctable">')
    print('<tr>')
    print('<td class="titlecell">')

-->

<!--title and location in big, if available, to the left-->
<div class="title">
<!--tag:image._base--><br>
</div>
<!--tagcode:
if image._attr:
    location = image._attr.get('location')
    if location:
        print('<span class="location">%s</span><br>' % location)
-->
<p>

<!--tagcode:

description = None
if image._attr:
    description = image._attr.get('description')
elif image._comment:
    description = image._comment

if description:
    print('<p class="description">')
    print(unicode2html(description))
    print('</p>')

-->

<center>
<table>
<!--tagcode:

exif_tag=['Marque','Modele','Date','Focale','Ouverture','Vitesse',\
          'Iso', 'Flash']
exif_key={'Marque' : 'Exif.Image.Make' , 'Modele' : 'Exif.Image.Model' , \
          'Date' : 'Exif.Photo.DateTimeOriginal' , 'Focale' : 'Exif.Photo.FocalLength' ,\
          'Vitesse' :  'Exif.Photo.ExposureTime' , 'Ouverture' : 'Exif.Photo.FNumber' ,\
          'Iso' : 'Exif.Photo.ISOSpeedRatings' , 'Flash' : 'Exif.Photo.Flash' }

if image._exif:
    print('<tr>')
    print('<td class="settingscell" >')
    print('<span class="settingstitle">PARAMETRES PHOTO:</span></td></tr>')
    for s in exif_tag:
        if exif_key[s] in image._exif:
            print('<tr><td class="settings">%s:</td> \
            <td class="settings"> %s </td></tr>' % (s,image._exif[exif_key[s]]))
-->

</table>
</center>



<!--previous and next thumbnails, with text in between-->
<br>
<center>
<hr class="sephr">
<table class="navtable">
<tr>

<!--tagcode:
pi = prev(image, allimages)

if pi and pi._thumbsize:
    pw = pi._thumbsize[0]
else:
    pw = opts.thumb_size

print('<td width="%d">' % pw)
if pi:
    print(thumbImage(cd, pi, 'align="left"'))
-->

</td><td align="center" CELLPADDING="5">

<!--dirnav, alternative representations and navigation,
    between the floating thumbs-->

<b>
<!--tag:dirnav(cd, image._dir)-->
<!--tag:dirnavsep-->
<a href="<!--tag:rel(image._filename, cd)-->">
<!--tag:basename(image._filename)--></a>
</b><br>

<!--tagcode:
if len(image._altrepns) > 0:
    print("Alternative representations:")
    for rep in image._altrepns.keys():
        print('<a href="%s">%s</a>&nbsp;'%(urlquote(rel(join(image._dir._path,image._altrepns[ rep ]), cd)), rep))
    print('<p>')
-->

<br>
<!--tagcode:
print(textnav(cd, image, image._dir._images,
              "dir", rel(image._dir._pagefn, cd) ))
if len(image._tracks) > 0:
    print('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;',)
    print('<span class="tracksind">tracks:</span>')
    for t in image._tracks:
        print('&nbsp;&nbsp;&nbsp;&nbsp;')
        print(textnav(cd, image, trackmap[t], t, rel(trackindex_fns[t], cd)))
--><p>

</td>

<!--tagcode:
ni = next(image, allimages)

if ni and ni._thumbsize:
    nw = ni._thumbsize[0]
else:
    nw = opts.thumb_size

print('<td width="%d">' % nw)
if ni:
    print(thumbImage(cd, ni, 'align="right"'))
-->

</td></tr></table>
</center>


""" + html_postamble

default_templates[ 'template-dirindex' ] = \
(html_preamble % 'Directory Index: <!--tag:dir._path-->') + \
"""
<table class="toptable dirtop"><tr><td>
<p class="toptitle"><!--tag:dirnav(cd, dir)--></p>
<!--tagcode:
desc_page = dir._attrfile
if desc_page:
    if 'title' in desc_page:
        print("<p><center><h3>")
        print(unicode2html(desc_page['title']))
        print("</h3></center></p>")
    if 'date' in desc_page:
        print("<p><h4>")
        print(unicode2html(desc_page['date']))
        print("</h4></p>")
    if desc_page.has_key('comment'):
        print("<p>")
        print(unicode2html(desc_page['comment'].replace(u"<BR>",u"\\n")).replace("\\n","<BR>"))
        print("</p>")
-->
</td></tr></table>

<div class="mininav">
<!--tagcode:
if dir._parent:
    sname = list((dir._parent)._subdirs)
    icur = sname.index(dir)
    if icur > 0:
       iprev = icur - 1
       dprev = sname[iprev]
       print '<a href="%s">%s</a>|' % ( rel(dprev._pagefn,cd), dprev._basename )
    print '<a href="%s">Haut</a>' % rel(rootdir._pagefn, cd)
    if icur < len(sname)-1:
       inext = icur + 1
       dnext = sname[inext]
       print '|<a href="%s">%s</a>' % ( rel(dnext._pagefn,cd), dnext._basename )
-->
</div>


<!--tagcode:
import sys
import os.path as op
try:
    from PIL import Image
except ImportError:
    import Image
if len( dir._subdirs ) > 0:
    print '<h3>Sous-repertoires:</h3>'
    # sort subdirs by time
    subdirs = list(dir._subdirs)
    if config.WebDirIndexStyle=="table":
        print "<table>"
        for d in subdirs:
            print "<tr>"
            if d._attrfile.has_key("image"):
                temp=op.splitext(d._attrfile["image"])[0]+opts.separator+config.Thumbnails["Suffix"]+config.Extensions[0]
                temp1,temp2=op.split(temp)
                filename=op.join(op.split(d._curdir)[1],temp1,config.Thumbnails["Suffix"],temp2)
                longfilename=op.join(opts.root,op.split(cd)[0],filename)
                if op.isfile(longfilename):
                    im = Image.open(longfilename)
                    width,height = im.size
                else:
                    width=config.Thumbnails["Size"]
                    height=3*width/4
                print '<td><center><a href="%s"><img CLASS="thumb" src="%s" alt="%s" height=%i width=%i></a></center></td>'%(rel(d._pagefn,cd),rel(filename,op.split(cd)[1]),op.split(filename)[1],height,width)
            else:
                print "<td> </td>"
            if d._attrfile.has_key("date") and d._attrfile.has_key("title"):
                print  '<td><center><a href="%s">%s<br>%s</a></center></td>'%(rel(d._pagefn,cd),unicode2html(d._attrfile["date"]),unicode2html(d._attrfile["title"]))
            else:
                if len(d._basename)>11:
                    if d._basename[10] in [" ","_","-"]:
                        print '<td><a href="%s">%s<br>%s</a></td>'%(rel(d._pagefn,cd),d._basename[:10],d._basename[11:])
                    else:
                        print '<td><a href="%s">%s</a></td>'%(rel(d._pagefn,cd),d._basename)
            if d._attrfile.has_key("comment"):
                print "<td>%s</td>"%(unicode2html(d._attrfile["comment"].replace("<BR>","\\n")).replace("\\n","<BR>"))
            else:
                print "<td> </td>"
            print "</tr>"
        print "</table>"

    else: # WebDirStyle is old fashion list
        print '<ul>'
        for d in subdirs:
                comment=""
                if  d._attrfile.has_key("comment"):
                    if len(d._attrfile["comment"])>50:
                        words=unicode2html(d._attrfile["comment"].replace("<BR>"," ")).split()
                        for w in words:
                            comment+=w+" "
                            if len(comment)>47:
                                comment+="..."
                                break
                    else:
                        comment=unicode2html(d._attrfile["comment"].replace("<BR>"," "))
                if d._attrfile.has_key("date") and d._attrfile.has_key("title"):
                    if len(d._attrfile["date"])>0:
                        print '<li><a href="%s">%s : %s.</a> <i>%s</i></li>' %( rel(d._pagefn,cd),unicode2html(d._attrfile["date"]),unicode2html(d._attrfile["title"]), comment)
                    else:
                        print '<li><a href="%s">%s.</a>  <i>%s</i></li>' %( rel(d._pagefn,cd), d._basename,comment)
                else:
                    print '<li><a href="%s">%s.</a>  <i>%s</i></li>' %( rel(d._pagefn,cd), d._basename,comment)
        print '</ul><p>'
-->

<!--tagcode:
if desc_page:
  if desc_page.get('description'):
    print('<p><div class="description">')
    print(unicode2html(desc_page.get('description')))
    print('</div></p>')

if len( dir._images ) > 0:
    print('<h3>Images:</h3>')
    print(table( cd, dir._images, sous_titre ))

-->

<div class="mininav">
<!--tagcode:
if dir._parent:
    sname = list((dir._parent)._subdirs)
    icur = sname.index(dir)
    if icur > 0:
       iprev = icur - 1
       dprev = sname[iprev]
       print '<a href="%s">%s</a>|' % ( rel(dprev._pagefn,cd), dprev._basename )
    print '<a href="%s">Haut</a>' % rel(rootdir._pagefn, cd)
    if icur < len(sname)-1:
       inext = icur + 1
       dnext = sname[inext]
       print '|<a href="%s">%s</a>' % ( rel(dnext._pagefn,cd), dnext._basename )
-->
</div>



""" + html_postamble

default_templates[ 'template-trackindex' ] = \
(html_preamble % 'Track Index: <!--tag:track-->') + \
"""

<table class=\"toptable tracktop\"><tr><td>
<p class=\"toptitle\">Track index: <!--tag:track--></p>
</td></tr></table>

<div class=\"mininav\">
<a href=\"<!--tag:rel(rootdir._pagefn, cd)-->\">Root</a> |
<a href=\"<!--tag:rel(allindex_fn, cd)-->\">Global</a> |
<a href=\"<!--tag:rel(sortindex_fn, cd)-->\">Sorted</a>
</div>

<!--tagcode:
images = trackmap[track]

if len(images) > 0:
    print '<h3>Images:</h3>'
    print imagePile( cd, images )

    print '<h3>Images by name:</h3>'
    print twoColumns(cd, images)
-->
""" + html_postamble

default_templates[ 'template-allindex' ] = \
(html_preamble % 'Global Index') + \
"""

<table class=\"toptable globaltop\"><tr><td>
<p class=\"toptitle\">Global Index</p>
</td></tr></table>

<div class=\"mininav\">
<a href=\"<!--tag:rel(rootdir._pagefn, cd)-->\">Root</a> |
<a href=\"<!--tag:rel(allindex_fn, cd)-->\">Global</a> |
<a href=\"<!--tag:rel(sortindex_fn, cd)-->\">Sorted</a>
</div>

<!--tagcode:
if len(alldirs) > 0:
    print '<H3>Directories:</H3>'
    print '<UL>'
    for d in alldirs:
        if d._parent:
            pname = d._path
        else:
            pname = '(root)'
        print '<li><a href=\"%s\">%s</a></li>' % \
            ( rel(d._pagefn, cd), pname )
    print '</ul><p>'
-->

<!--tagcode:
if len(tracks) > 0:
    print '<h3>Tracks:</h3>'
    print '<ul>'
    for t in tracks:
        print '<li><a href=\"%s\">%s</a></li>' % (trackindex_fns[t], t)
    print '</ul>'
-->

<!--tagcode:
if len(allimages) > 0:
    print '<h3>Images:</h3>'
    print imagePile( cd, allimages )

    print '<h3>Images by name:</h3>'
    print twoColumns(cd, allimages)
-->
""" + html_postamble

default_templates[ 'template-sortindex' ] = \
(html_preamble % '\"Sorted index\"') + \
"""
<table class=\"toptable sortedtop\"><tr><td>
<p class=\"toptitle\">Sorted index</p>
</td></tr></table>

<div class=\"mininav\">
<a href=\"<!--tag:rel(rootdir._pagefn, cd)-->\">Root</a> |
<a href=\"<!--tag:rel(allindex_fn, cd)-->\">Global</a> |
<a href=\"<!--tag:rel(sortindex_fn, cd)-->\">Sorted</a>
</div>

<!--tagcode:
if len(allimages) > 0:
    import os
    import os.path as op
    print '<h3>Images sorted by name:</h3>'
    ilist = list(allimages)
    ilist.sort( lambda x,y: cmp( x._base, y._base ) )

    for i in ilist:
        print '<p>'
        print thumbImage( cd, i, 'align=\"middle\"' )
        print '<a href=\"%s\">%s</a>' %( rel(i._pagefn, cd), i._base )
        print
-->
""" + html_postamble



@contextmanager
def custom_redirection(fileobj):
    old = sys.stdout
    sys.stdout = fileobj
    try:
        yield fileobj
    finally:
        sys.stdout = old


class Templates(object):
    "A class responsible for reading and providing all kind of templates"
    def __init__(self):
        """Constructor ... behaves like a dictionary


        :param opts: an option parser object with the command line options
        """
        self.opts = None
        self.templates = {}  # key: type of template, value=list of PieceOfCode

    def set_opts(self, opts):
        self.opts = opts
        self.read_all()


    def read_all(self):
        """Reads the template files."""

        if self.opts is None:
            raise RuntimeError("You need to first set the parsed command line options")

        # Compile HTML templates.

        for tt in [ 'image', 'dirindex', 'allindex', 'trackindex', 'sortindex' ]:
            fn = 'template-%s' % tt + self.opts.htmlext
            templatetxt = self.read_one(fn)
            self.templates[ tt ] = self.compile_template(templatetxt, fn)

        fn = 'template-css.css'
        templatetxt = self.read_one(fn)
        self.templates[ 'css' ] = self.compile_template(templatetxt, fn)

        # Compile user-specified rc file.
        rcsfx = 'rc'
        self.templates[ rcsfx ] = []
        if self.opts.rc:
            try:
                with  open(opts.rc, "r") as tfile:
                    orc = tfile.read()
            except IOError as error:
                logger.error("Error: can't open user rc file: %s; %s", self.opts.rc, error)
                sys.exit(1)
            self.templates[rcsfx].append(self.compile_code('', orc, self.opts.rc))

        # Compile user-specified code.
        if self.opts.rccode:
            self.templates[rcsfx].append(self.compile_code('', opts.rccode, "rccode option"))

        # Compile global rc file without HTML tags, just python code.
        tt = 'template-%s.py' % rcsfx
        code = self.read_one(tt)
        self.templates[rcsfx].append(self.compile_code('', code, tt))

    def read_one(self, tfn):

        """Reads a template file.
        :param tfn: a simple filename.
        :return: some text file which was read

        """
        logger.debug("Fetching template %s", tfn)

        found = 0
        foundInRoot = 0

        # check in user-specified template root.
        if self.opts.templates:
            fn = os.path.join(self.opts.templates, tfn)
            logger.debug("  looking in %s", fn)
            if os.path.exists(fn):
                found = 1

        # check in hierarchy root
        if not found:
            fn = os.path.join(self.opts.root, tfn)
            logger.debug("  looking in %s", fn)
            if os.path.exists(fn):
                foundInRoot = 1
                found = 1

        # look for it in the environment var path
        if not found:
            try:
                curatorPath = os.environ[ 'CURATOR_TEMPLATE' ]
                pathlist = curatorPath.split(os.pathsep)
                for p in pathlist:
                    fn = os.path.join(p, tfn)
                    logger.debug("  looking in %s", fn)
                    if exists(fn):
                        found = 1
                        break
            except KeyError:
                pass

        if found:
            # read the file
            try:
                with open(fn, "r") as tfile:
                    t = tfile.read()
            except IOError as e:
                logger.error("Can't open image template file: %s; %s", fn, e)
                sys.exit(1)
            logger.debug("  succesfully loaded template %s", tfn)

        else:
            # bah... can't load it, use fallback templates
            logger.debug("  falling back on simplistic default templates.")
            t = default_templates.get(os.path.splitext(tfn)[0], "")

        # Save templates in root, if it was requested.
        if self.opts.save_templates and not foundInRoot:
            rootfn = join(opts.root, tfn)
            logger.debug("  saving template in %s", rootfn)

            # saving the file template
            if exists(rootfn):
                bakfn = join(opts.root, tfn + '.bak')
                logger.debug("  making backup in %s", bakfn)

                try:
                    shutil.copy(rootfn, bakfn)
                except:
                    logger.error("Can't copy backup template %s", bakfn)

            try:
                with open(rootfn, "w") as ofile:
                    ofile.write(t)
            except IOError as e:
                logger.error("Can't save template file to: %s ; %s", rootfn, e)
        return t

    def compile_template(self, templatetxt, filename):
        """Compiles template text and return a list of piece of html and


        :param templatetxt: string with the template in it
        :param filename: name of the file
        :return: list of PieceOfCode (3-tuple with text, compiled code and the source)
        """
        output = []
        mre1 = re.compile("<!--tag(?P<code>code)?:\s*")
        mre2 = re.compile("-->")
        pos = 0
        errors = 0

        while pos < len(templatetxt):
            mo1 = mre1.search(templatetxt, pos)
            if not mo1:
                break
            mo2 = mre2.search(templatetxt, mo1.end())
            if not mo2:
                logger.error("Error: unfinished tag.")
                sys.exit(1)

            pretext = templatetxt[ pos : mo1.start() ]
            code = templatetxt[ mo1.end() : mo2.start() ]
            if not mo1.group('code'):
                code = "print(%s, end='')" % code
            output.append(self.compile_code(pretext, code, filename))
            pos = mo2.end()

        if pos < len(templatetxt):
            # Finally the last piece of text ...
            output.append(PieceOfCode(templatetxt[pos:], None, None))

        if errors == 1 and not self.opts.ignore_errors:
            sys.exit(1)

        return output

    def compile_code(self, preamble, source, filename):

        """Compile a chunk of code.

        :param preamble: piece of pure html text not compiled
        :param source: the actual python source code to be compiles
        :param filename: an indication of the filename ... mainly to help debugging
        :return: a PieceOfCode which contains the (preamble,compiled,source)
        """

        try:
            if source:
                co = compile(source, filename, "exec")
                poc = PieceOfCode(preamble, co, source)
            else:
                poc = PieceOfCode(preamble, None, source)
        except Exception as error:
            poc = PieceOfCode(preamble, None, source)

            logger.error("Error %s compiling template %s in the following code:", error, filename)
            logger.error(source)

            try:
                etype, value, tb = sys.exc_info()
                print_exception(etype, value, tb, None, sys.stderr)
            finally:
                etype = value = tb = None
            if not self.opts.ignore_errors:
                errors = 1

        return poc

    def execute(self, fileobj, template_name, env):
        """Executes template text.  Output is written to outfile.
        :param fileobj: opened file object to write to
        :param template_name: the name of the template to use
        :param env: the environment of the execution
        """
        errors = 0
        for poc in self.templates[template_name]:
            fileobj.write(poc.preamble)
            if poc.compiled:
                try:
                    with custom_redirection(fileobj):
                        eval(poc.compiled, env)

                        # Note: this is a TERRIBLE hack to flush the comma cache of the
                        # python interpreter's print statement between tags when outfile
                        # is a string stream.
                        #
                        # Note: we don't need this anymore, since we're outputting to a
                        # real file object.  However, keep this around in case we change
                        # it back to output to a string.
                        # if hack:
                        #    ss.ignoreNextChar()

                except Exception as err:
                    logger.error("Error: %s executing template in the following code:\n%s", err, poc.source)
                    try:
                        etype, value, tb = sys.exc_info()
                        print_exception(etype, value, tb, None, sys.stderr)
                    finally:
                        etype = value = tb = None
                    if not self.opts.ignore_errors:
                        errors = 1

        if errors == 1 and not self.opts.ignore_errors:
            sys.exit(1)
