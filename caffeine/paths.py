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
from os.path import exists
from os.path import join

try:
    from xdg.BaseDirectory import xdg_config_home
except ModuleNotFoundError:
    from xdg import xdg_config_home

    xdg_config_home = str(xdg_config_home())

PACKAGE_PATH = os.path.dirname(__file__)
LOCALE_PATH = join(PACKAGE_PATH, "locale")
GLADE_PATH = join(PACKAGE_PATH, "assets/glade")
IMAGE_PATH = join(PACKAGE_PATH, "assets/images")
ICON_PATH = join(PACKAGE_PATH, "assets/icons")


def get_glade_file(filename):
    return join(GLADE_PATH, filename)


def get_config_dir():
    return __config_dir


def get_whitelist_file():
    return join(__config_dir, "whitelist.txt")


def get_blacklist_file_audio():
    return join(__config_dir, "audio_blacklist.txt")


__config_dir = join(xdg_config_home, "caffeine")


if not exists(__config_dir):
    makedirs(__config_dir)

if not exists(get_whitelist_file()):
    open(get_whitelist_file(), "a").close()

if not exists(get_blacklist_file_audio()):
    open(get_blacklist_file_audio(), "a").close()
