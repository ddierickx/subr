#!/usr/bin/env python

import os, sys, inspect
import logging
import settings

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