# @[copyright_header]@
"""
common usage facilities
"""

from hashlib import sha256
from typing import Iterable

import logging
import os
from logging.handlers import TimedRotatingFileHandler


LOGGER = None


def init_logger(log_file):
    """
    Init logger to print to *log_file*.

    log file is read from the config file 'log-file' key, and defaults
    to '/var/log/gerrit-mmpack-build.log'

    Should be called after loading the CONFIG

    Files rotate every day, and are kept for a month
    """
    global LOGGER  # pylint: disable=global-statement

    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    log_handler = TimedRotatingFileHandler(log_file, when='D', backupCount=30)

    formatter = logging.Formatter("%(asctime)s: %(levelname)s: %(message)s",
                                  "%Y-%m-%d %H:%M:%S")
    log_handler.setFormatter(formatter)

    LOGGER = logging.getLogger('mmpack-ci-server')
    LOGGER.addHandler(log_handler)
    LOGGER.setLevel(logging.INFO)


def log_error(msg: str):
    """
    Log message with error level
    """
    LOGGER.error(msg)


def log_info(msg: str):
    """
    Log message with info level
    """
    LOGGER.info(msg)


def subdict(adict: dict, keys: Iterable) -> dict:
    """
    Return a subset of adict dictionary containing only keys passed in argument
    """
    return {k: v for k, v in adict.items() if k in keys}


def str2bool(value: str) -> bool:
    """
    interpret value and convert to bool
    """
    if not value:
        return False

    return value.lower() in ['true', 'yes', 'y', '1']


def sha256sum(filename: str) -> str:
    """
    compute the SHA-256 hash of a file

    Returns:
        a string containing hexadecimal value of hash
    """
    sha = sha256()
    with open(filename, 'rb') as fileobj:
        sha.update(fileobj.read())
    return sha.hexdigest()
