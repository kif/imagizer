'''
Created on 7 avr. 2014

@author: jerome
'''
import os
import os.path as op
import logging
from .config import Config
config = Config()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("imagizer.selection")

class Selected(list):
    """
    Basically a list of files
    """
    def get_nbytes(self):
        """Return the size of the selection in byte (octets)"""
        size = 0
        for afile in self:
            size += op.getsize(op.join(config.DefaultRepository, afile))
        return size

    def save(self, filename=None):
        """
        Save the list of selected files

        @param selected_list: list of filename selected
        """
        if filename is None:
            selected_fn = op.join(config.DefaultRepository, config.Selected_save)
        else:
            selected_fn = str(filename)
        logger.debug("Saving selection into file %s" % selected_fn)
        os.remove(selected_fn)
        with open(selected_fn, "w") as select_file:
            select_file.write(os.linesep.join(self))
        os.chmod(selected_fn, config.DefaultFileMode)

    @classmethod
    def load(cls, filename=None):
        """
        Load the list of selected filenames

        @return: the list of selected images (filenames)
        """
        self = cls()
        if filename is None:
            selected_fn = op.join(config.DefaultRepository, config.Selected_save)
        else:
            selected_fn = str(filename)
        if op.exists(selected_fn):
            logger.debug("Loading selection from file %s" % selected_fn)
        else:
            logger.warning("No such selection file %s" % selected_fn)
            return self

        try:
            for line in open(selected_fn, "r"):
                line_stripped = line.strip()
                if op.isfile(op.join(config.DefaultRepository, line_stripped)):
                    self.append(line_stripped)
        except Exception as exc:
            logger.warning("Failed (%s) to load selection from file %s" % (exc, selected_fn))
            return  self
        self.sort()
        return self

