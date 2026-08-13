#!/usr/bin/env python
# coding: utf-8
"""Run the imagizer test suite: ``python3 -m imagizer.test``."""
import os
import sys
import unittest


def suite():
    here = os.path.dirname(os.path.abspath(__file__))
    return unittest.TestLoader().discover(here, pattern="test_*.py")


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(suite())
    sys.exit(0 if result.wasSuccessful() else 1)
