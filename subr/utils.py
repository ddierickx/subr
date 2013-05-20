#!/usr/bin/env python

import os
import logging
import settings

from difflib import SequenceMatcher

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
logger.setLevel(logging.INFO)

def ratio(a, b):
    """
        do a fuzzy string match between strings a and b, returns a value [0, 1]
    """
    return round(SequenceMatcher(a=a.lower(), b=b.lower()).ratio(), 2)