"""
Functions that simplify running in a linux environment.
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
Known Issues/Wishlist:

"""

from shutil import rmtree


def remove_dir(directory):
    """
    This function utilized an exception clause to delete a directory.

    Parameters
    ----------
    directory : string
        complete path to the directory to be removed.

    """

    try:
        rmtree(directory)
    except OSError as e:
        print("OSError in remove_dir: %s - %s." % (e.filename, e.strerror))
