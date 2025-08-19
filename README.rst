Purpose:
=========

Imagizer is a toolbox written in Python made of two main executable programs
called selector and generator which can handle a large set of pictures 
(in JPEG file-format) from different digital cameras, sort them, archive them on CDs 
or DVDs and publish them on the internet with static pages (no dependencies on any 
PHP or whatever). Special care has been put on preserving the (original) image 
quality, modifications are only done on meta-data (exif and jpeg tags) and on 
the filename, rotation of the image is done without decompressing and recompressing 
them, by re-arrangement of compressed blocks.    

* Selector is the GUI part, it should run on a graphical workstation, it searches the 
sub-directories for JPEG files and sorts them according to their date/time and camera 
model. After this initial step occuring during the splash screen, Selector offers 
a GUI for rotating, adding comments, selecting images for publication (or archiving)
and displaying slideshows.  

* Generator is a CLI-program designed to run on server computer (web server) to
generate static web pages (HTML) for all images on the web-repository. It heavily
relies on a program written by Martin Blais  http://curator.sourceforge.net/ 

Installation :
==============

For debian/ubuntu users: there is a script to build a deb package and install it:
./build-package.sh

For all the other :
# python setup.py install

Dependences
-----------


Detailed description of selector
================================

Selector as four main modes of working: initialization, image selection, slide show, and publication.

Initialization
--------------
At selector's start-up all new images (JPEG files) in the repository (not compliant
with the naming convention of imagizer) are renamed and rotated automatically. 
If the current directory does not look like to an imagizer repository (i.e. no .selected file),
a warning message is displayed to prevent you setting the mess on your hard-disk.
The new files are also decompressed and set into a cache for further use.

Image Selection
---------------

Once the images are sorted, the first new image (or the first image if no new image)
is displayed and you can add a title or rotate it if needed.
In the default selector GUIm you have access to informations on 
-Camera:	Model, version.
-Image:	resolution, size, time , focal length, aperture, speed, flash and iso.

Each image can also be selected for subsequent batch processing.

Modification available on images:
---------------------------------
Title:		give a name of the image. This title will be stored inside the meta-data
			of the file so there is no need to have an external database or whatever.
			the title is stored inside the JPEG title part, so oher information can 
			be stored in the EXIF-title metadata part if needed. The title is encoded 
			in UTF8 thatever the convention of the current system are.

Previous:	switches to the previous image. (CTRL-Up)

Next:		Switches to the next image. (CTRL-Down)

Left-Rotation: Rotate the image counter-clockwise by 90°. (Ctrl-Left)

Right-Rotation: Rotate the image cockwise by 90°. (Ctrl-Right)

Select: 	Add the current image to the selection for subsequent batch processing (Ctrl-s).

Trash:		Move the image into the folder named "Trash" for a future removal. 
			Imagizer does not remove images itself.


Publication
-----------

The menu file/execute contains hooks for exporting images ...
Synchronize:	run the rsync program for synchronizing two repositories, possibly 
				on two different computers. You can chose to synchronize all files 
				or just the selected ones or the newer/older ones.  

Copy:			Just make a copy of all files selected into the "Selected" directory.
				this is useful for preparing a set of images to give them away for 
				someone else ... before copying the to a USB-key

Copy&Burn		Starts with "Copy" then goes on with mkisofs and cdrecord to burn a 
				CD or a DVD from the set of selected images. This is used for 
				archiving images, together with the selection/CD-DVD-newer.

Copy&Resize		Copy all files and creates for each full-size image, two smaller images
				one for screen display (800x600) and one thumbnail (160x120).  				 

PublishToWeb	The same as Copy&Resize then runs generator to create web pages automatically



Detailed description of generator
=================================

"Generator" is the program for creating web pages (static HTML) from a set of 
images. As it has no graphical user interface it is usable on a (web-) server different 
from the graphical workstation running "selector"








 
