# -*- coding: utf-8 -*-
#
# Copyright © 2009-2014 The Caffeine Developers
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
from gi.repository import Gtk

VERSION = "2.6.1"

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
GLADE_PATH = join(BASE_PATH, 'share', 'caffeine', 'glade')

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
