# Copyright (c) 2014 Hugo Osvaldo Barrera
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

import os
from os import makedirs
from os.path import abspath, dirname, exists, join, pardir

from xdg.BaseDirectory import xdg_config_home

PACKAGE_PATH = os.path.dirname(os.path.abspath(__file__))
LOCALE_PATH = join(PACKAGE_PATH, 'locale')
GLADE_PATH = join(PACKAGE_PATH, 'assets/glade')
IMAGE_PATH = join(PACKAGE_PATH, 'assets/images')


def get_base_path():
    c = abspath(dirname(__file__))
    # FIXME: This may recurse all the way up to "/" and end up in an infinite
    # loop
    while True:
        if exists(join(c, "share/caffeine")):
            return c

        c = join(c, pardir)
        if not exists(c):
            raise Exception("Can't determine get_base_path()")


def get_glade_file(filename):
    return join(GLADE_PATH, filename)


def get_config_dir():
    return __config_dir


def get_whitelist_file():
    return join(__config_dir, "whitelist.txt")


def get_icon_path():
    return __icon_path


__config_dir = join(xdg_config_home, "caffeine")
__icon_path = join(get_base_path(), 'share', 'icons')


if not exists(__config_dir):
    makedirs(__config_dir)

if not exists(get_whitelist_file()):
    open(get_whitelist_file(), "a").close()
