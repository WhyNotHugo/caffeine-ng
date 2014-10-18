# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Hugo Osvaldo Barrera
# Copyright © 2009 The Caffeine Developers
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

# This is a simple logging module for Caffeine. Currently, for simplicity,
# it only provides 'info', 'warn' and 'error' procedures. The logging
# messages are colorized to enhance readability. Info and warning messages
# have their level name colored green and yellow, respectively, while
# error messages are colored red in their entirety.
#
# Example of use:
# from caffeinelogging import info, warn, error
# error("Caffeine has hit an exception")

import sys
import logging
import logging.handlers

import caffeine

SWITCH_TO_GREEN = "\033[1;32m"
SWITCH_TO_YELLOW = "\033[1;33m"
SWITCH_TO_RED = "\033[1;31m"
RESET_TO_NORMAL = "\033[0m"

FORMAT_STRING = '%(asctime)s %(levelname)s %(message)s'
DATE_FORMAT_STRING = '%d%b%Y %H:%M:%S'

# == write logs to a file:
file_info_handler = \
    logging.handlers.RotatingFileHandler(caffeine.LOG, maxBytes=1*1024*1024,
                                         backupCount=5)

file_info_formatter = logging.Formatter('%(asctime)s INFO: %(message)s',
                                        '(%d %b %Y) %H:%M:%S')
file_info_handler.setFormatter(file_info_formatter)
# ==


info_handler = logging.StreamHandler(sys.stdout)

info_formatter = logging.Formatter('%(asctime)s ' + SWITCH_TO_GREEN + 'INFO: '
                                   + RESET_TO_NORMAL + ' %(message)s',
                                   '(%d %b %Y) %H:%M:%S')
info_handler = logging.StreamHandler(sys.stdout)
info_handler.setFormatter(info_formatter)

info_logger = logging.getLogger("InfoLogger")
info_logger.setLevel(logging.INFO)
info_logger.addHandler(info_handler)
info_logger.addHandler(file_info_handler)

####

# == write logs to a file:

file_warn_handler = \
    logging.handlers.RotatingFileHandler(caffeine.LOG, maxBytes=1*1024*1024,
                                         backupCount=5)

file_warn_formatter = \
    logging.Formatter('%(asctime)s WARNING: %(message)s',
                      '(%d %b %Y) %H:%M:%S')
file_warn_handler.setFormatter(file_warn_formatter)
# ==

warn_formatter = logging.Formatter('%(asctime)s ' + SWITCH_TO_YELLOW +
                                   'WARNING: ' + RESET_TO_NORMAL +
                                   ' %(message)s', '(%d %b %Y) %H:%M:%S')
warn_handler = logging.StreamHandler(sys.stdout)
warn_handler.setFormatter(warn_formatter)

warn_logger = logging.getLogger("WarnLogger")
warn_logger.setLevel(logging.WARN)
warn_logger.addHandler(warn_handler)
warn_logger.addHandler(file_warn_handler)

####

# == write logs to a file:

file_error_handler = \
    logging.handlers.RotatingFileHandler(caffeine.LOG, maxBytes=1*1024*1024,
                                         backupCount=5)

file_error_formatter = logging.Formatter('%(asctime)s ERROR: %(message)s',
                                         '(%d %b %Y) %H:%M:%S')
file_error_handler.setFormatter(file_error_formatter)
# ==


error_formatter = \
    logging.Formatter(SWITCH_TO_RED + '%(asctime)s ERROR: %(message)s' +
                      RESET_TO_NORMAL, '(%d %b %Y) %H:%M:%S')
error_handler = logging.StreamHandler(sys.stderr)
error_handler.setFormatter(error_formatter)

error_logger = logging.getLogger("ErrorLogger")
error_logger.setLevel(logging.ERROR)
error_logger.addHandler(error_handler)
error_logger.addHandler(file_error_handler)


def info(msg):
    info_logger = logging.getLogger("InfoLogger")
    info_logger.info(msg)


def warn(msg):
    warn_logger = logging.getLogger("WarnLogger")
    warn_logger.warn(msg)


def error(msg):
    error_logger = logging.getLogger("ErrorLogger")
    error_logger.error(msg)
