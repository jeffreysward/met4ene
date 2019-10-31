"""
Overview:

- This module provides methods which support simplify running in a
  linux environment.

_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
Known Issues:



"""

from shutil import rmtree


def remove_dir(directory):
    try:
        rmtree(directory)
    except OSError as e:
        print("OSError in remove_dir: %s - %s." % (e.filename, e.strerror))
