#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
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


import os
from os.path import join, abspath, dirname, pardir
from gi.repository import Gtk, Gio

from xdg.BaseDirectory import xdg_config_home

VERSION = "2.4.1"

def getBasePath():
    c = abspath(dirname(__file__))
    while True:
        if os.path.exists(os.path.join(c, "bin")) and \
           os.path.exists(os.path.join(c, "share/caffeine")) :
            return c

        c = join(c, pardir)
        if not os.path.exists(c):
            raise Exception("Can't determine BASE_PATH")

BASE_PATH = getBasePath()
BASE_KEY = "net.launchpad.caffeine"

_config_dir = os.path.join(xdg_config_home, "caffeine")

if not os.path.exists(_config_dir):
    os.makedirs(_config_dir)

CONFIG_DIR = _config_dir
## file with a list of programs that caffeine should 
## activate when they are running

## Log file.
LOG = os.path.join(CONFIG_DIR, "log")
WHITELIST = os.path.join(CONFIG_DIR, "whitelist.txt")
## create file if it doesn't exist
if not os.path.isfile(WHITELIST):
    file = open(WHITELIST, "w")
    file.close()


from caffeine import procmanager
_ProcMan = procmanager.ProcManager()

def get_ProcManager():
    return _ProcMan


IMAGE_PATH = join(BASE_PATH, 'share', 'caffeine', 'images')
GLADE_PATH = join(BASE_PATH, 'share', 'caffeine', 'glade')
ICON_PATH  = join(BASE_PATH, 'share', 'icons')

_desktop_file  = join(BASE_PATH, 'share', 'applications',
        'caffeine.desktop')

FULL_ICON_PATH = join(IMAGE_PATH, "Full_Cup.svg")
EMPTY_ICON_PATH = join(IMAGE_PATH, "Empty_Cup.svg")

GENERIC_PROCESS_ICON_PATH = join(IMAGE_PATH, "application-x-executable.png")

ICON_NAME = 'caffeine'
icon_theme = Gtk.IconTheme.get_default()

def get_icon_pixbuf(size):
    global icon_theme
    global ICON_NAME
    
    iconInfo = icon_theme.lookup_icon(ICON_NAME, size,
        Gtk.IconLookupFlags.NO_SVG)
    
    if iconInfo:
        # icon is found
        base_size = iconInfo.get_base_size()
        if base_size != size:
            ## No sizexsize icon in the users theme so use the default
            icon_theme = Gtk.IconTheme()
            icon_theme.set_search_path((ICON_PATH,))
    else:
        icon_theme.append_search_path(ICON_PATH)
        iconInfo = icon_theme.lookup_icon(ICON_NAME, size,
            Gtk.IconLookupFlags.NO_SVG)

    pixbuf = icon_theme.load_icon(ICON_NAME, size,
                Gtk.IconLookupFlags.NO_SVG)

    return pixbuf

### Setup translations
###
GETTEXT_DOMAIN = "caffeine"
LOCALE_PATH = os.path.join(BASE_PATH, "share", "locale")

import gettext
import locale

locale.setlocale(locale.LC_ALL, '')

for module in locale, gettext:
    module.bindtextdomain(GETTEXT_DOMAIN, LOCALE_PATH)
    module.textdomain(GETTEXT_DOMAIN)

# register the gettext function for the whole interpreter as "_"
import __builtin__
__builtin__._ = gettext.gettext


from caffeine.main import main
