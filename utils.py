#!/usr/bin/env python

import logging
import settings

def load_libraries():
    """
        add all libraries in the 'lib' folder to the python path
        > http://stackoverflow.com/questions/279237/python-import-a-module-from-a-folder
    """
    import os, sys, inspect
    library_folder = "lib"
    cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0],library_folder)))
    if cmd_subfolder not in sys.path:
        sys.path.insert(0, cmd_subfolder)

load_libraries()

"""
    log to syso and file
"""
logger = logging.getLogger("subr-log")
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler(settings.LOG_FILENAME)
console_handler = logging.StreamHandler()
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)
