"""
video_page is the tool to generate a web page with all videos
"""
__author__ = "Jérôme Kieffer"
__contact__ = "imagizer@terre-adelie.org"
__date__ = "14/09/2025"
__license__ = "GPL"

import time
import datetime
import os
import sys
import locale
from argparse import ArgumentParser
import logging
import sys
import glob
import cv2
from PIL import Image
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from .. import Html, unicode2html


EXTENSIONS = ["mp4", "avi"]

class Video:
    def __init__(self, filename, root):
        self.root = os.path.abspath(root)
        self.filename = filename
        self._duration = None
        self._timestamp = None

    
    def save_frame(self, filename=None, size=160):
        if filename is None:
            filename = os.path.splitext(self.abs_filename)[0] + "--Thumb.jpg"
        if not os.path.isfile(filename):
            cap = cv2.VideoCapture(self.abs_filename)
            if self._duration is None:
                fps = cap.get(cv2.CAP_PROP_FPS) 
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                self._duration = frame_count/fps
            is_read, frame = cap.read()
            if is_read:
                ratio = min(size/i for i in frame.shape[:2])
                thumb = cv2.resize(frame, (0,0), fx=ratio, fy=ratio, interpolation=cv2.INTER_AREA)
                cv2.imwrite(filename, thumb)
            else:
                logger.error(f"Unable to save frame `{filename}`.")
        return filename

    @property
    def abs_filename(self):
        return os.path.join(self.root, self.filename)

    @property
    def duration(self):
        if self._duration is None:
            cap = cv2.VideoCapture(self.abs_filename)
            fps = cap.get(cv2.CAP_PROP_FPS) 
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self._duration = frame_count/fps
        return self._duration
    
    @property
    def timestamp(self):
        if self._timestamp is None:
            timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(self.abs_filename))
            dirname = os.path.split(self.filename)[0]
            dirname = os.path.split(dirname)[1]
            dirdate = None
            if len(dirname) >= 10:
                if dirname[0] == "M": 
                    dirname = dirname[1:]
                try:
                    dirdate = datetime.datetime.fromtimestamp(time.mktime(time.strptime(dirname[:10], "%Y-%m-%d")))
                except:
                    print("unable to parse dirdate:", dirname)
                else:
                    print(dirdate.date(), timestamp.date(), dirdate.date() < timestamp.date())
                    if dirdate.date() < timestamp.date():
                        timestamp = datetime.datetime.combine(dirdate.date(), timestamp.time())
            self._timestamp = timestamp
        return self._timestamp
    
    @property
    def date(self):
        return self.timestamp.date().isoformat()
    
    @property
    def title(self):
        return os.path.splitext(os.path.split(self.filename)[1])[0]

class AllVideo:
    def __init__(self, root):
        if not os.path.isdir(root):
            raise RuntimeError(f"'{root}' is not a directory !")

        self.root = os.path.abspath(root)
        self.filenames = {filename: Video(filename, self.root) for filename in self.search()}

    def __repr__(self):
        return f"{len(self.filenames)} videos in directory `{self.root}`."

    def search(self):
        all = []
        for ext in EXTENSIONS:
            all += glob.glob(f"**/*.{ext}", recursive=True, root_dir=self.root)
        all.sort()
        return all
    
    def build_html(self):
        per_date = {}
        for video in self.filenames.values():
            date = video.date
            if date in per_date:
                per_date[date].append(video)
            else:
                per_date[date] = [video]                

        html = Html("Videos", enc="UTF-8")
        html.element("a name='begin'")

        for onedate in per_date.values():
            html.element("b", onedate[0].timestamp.date().strftime("%A, %d %B %Y").capitalize())
            html.start("table", {"cellspacing":10})
            for onevideo in onedate:
                thumb_name = onevideo.save_frame()
                html.start("tr")
                html.start("td", {"width":200})
                # print(RelativeName(onevideo.abs_filename))
                html.start("a", {"href": onevideo.filename})
                thumb = os.path.relpath(thumb_name, self.root)
                html.start("img", {"src":thumb, "alt":thumb})
                html.stop("img")
                html.stop("a")
                html.stop("td")
                html.start("td")
                html.data(onevideo.timestamp.time().strftime("%Hh%Mm%Ss"))
                html.start("br")
                html.data(f"Dur\xe9e {onevideo.duration:.1f}s")
                html.stop("td")
                html.element("td", onevideo.title)
                html.stop("tr")
            html.stop("table")
            html.start("hr/")
        html.element("a name='end'")
        html.write(os.path.join(self.root, "index.html"))


def parse():
    """parse the CLI options"""
    parser = ArgumentParser(prog="video_page",
                            description="Cree une page web avec les videos",
                            epilog="")
    parser.add_argument("-d", "--debug", help="mode debug tres verbeux", action="store_true", default=False)
    parser.add_argument("path", help="repertoires a traiter", default=(os.getcwd(),), nargs='*')
    args = parser.parse_args()
    if args.debug:
        logging.root.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger.debug("We are in debug mode ...First Debug message")
    else:
        logging.root.setLevel(logging.INFO)
        logger.setLevel(logging.INFO)
    return args


def main(args=sys.argv):
    args = parse()
    print(args.path)


if __name__ == "__main__":
    main()
